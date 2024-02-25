import glob
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from config import (
    DB_PARAMS,
    LOGS_PATH,
    SKIP_EVENT_BY_DATE,
    SKIP_FILE_METHOD,
    get_logger,
    skip_file_method_mapper,
)
from database import Database
from models import LogEntry

logger = get_logger()


class LogParser:
    def __init__(self, logs_path: str):
        self.db_url: str = self.build_db_url()
        self.logs_path: str = logs_path
        self.run_number: int = 0
        self.compared_time: Optional[datetime] = None

    def run_parser(self) -> None:
        logger.info("Starting Auditd log parser")

        database = Database(self.db_url)
        Session = database.get_session()

        with Session() as session:
            with session.begin():
                self.set_run_number(session)
                self.set_compared_time(session)
                self.parse_auditd_logs(session)

        logger.info("Finished Auditd log parser")

    @staticmethod
    def build_db_url() -> str:
        return f"{DB_PARAMS['db_engine']}:///{DB_PARAMS['db_path']}"

    def get_files_to_parse(self) -> List[str]:
        """
        Find the auditd log files.
        logs_path may be a path to a directory or a single log file

        :return: List containing the auditd log files
        """

        if os.path.isdir(self.logs_path):
            log_files = glob.glob(os.path.join(self.logs_path, "*"))
        elif os.path.isfile(self.logs_path):
            log_files = [self.logs_path]
        else:
            logger.error(f"Invalid audit log files path: {self.logs_path!r}")
            raise FileNotFoundError

        return sorted(log_files, key=lambda x: os.path.getmtime(x))

    def set_run_number(self, session) -> None:
        """
        Return the number of the current code run.
        """
        try:
            prev_run = self.get_max_value(session, "run_num") or 0
            self.run_number = prev_run + 1

        except SQLAlchemyError as e:
            logger.error(f"{type(e).__name__}: {e}")
            raise

    def set_compared_time(self, session) -> None:
        try:
            field_name = skip_file_method_mapper.get(SKIP_FILE_METHOD)
            self.compared_time = self.get_max_value(session, field_name)
        except SQLAlchemyError as e:
            logger.error(f"{type(e).__name__}: {e}")
            raise

    def parse_auditd_logs(self, session) -> None:
        """
        This function parse the audit log files
        And add the logs to the database
        """

        log_files = self.get_files_to_parse()

        # Loop on the log files
        for i, log_file in enumerate(log_files, 1):
            file_name = log_file.split("/")[-1]
            logger.info(f"Parsing file {file_name} ({i}/{len(log_files)})")

            if self.skip_file_by_date(log_file):
                logger.info(f"No new events in {file_name}, skipping...")
                continue

            with open(log_file, "r") as f:
                records_added = 0

                try:
                    # Loops on custom events
                    while event_dict := self.get_event(f):
                        new_record = self.build_log_record(event_dict)

                        # Check whether to skip current event
                        if self.skip_event(session, new_record):
                            continue

                        self.add_record(session, new_record)
                        self.compared_time = new_record["event_timestamp"]
                        records_added += 1

                except Exception as e:
                    logger.warning(
                        f"Failed parsing {log_file}. {type(e).__name__}: {e}",
                        exc_info=True,
                    )
                    continue

            logger.info(
                f"Finished parsing file {file_name}, Records added: {records_added}"
            )

    def build_log_record(self, event_dict: Dict[str, str]) -> Dict[str, Any]:
        new_log_record: Dict[str, Any] = {
            key: event_dict[key]
            for key in LogEntry.__table__.columns.keys()
            if key in event_dict
        }

        # log_id is taken from msg=audit(<timestamp>:<event_id>):
        log_id = event_dict["msg"][6:-2]

        time_stamp = log_id.split(":")[0]
        date_time = datetime.fromtimestamp(float(time_stamp))

        new_log_record["log_id"] = log_id
        new_log_record["event_timestamp"] = date_time
        new_log_record["run_num"] = self.run_number

        return new_log_record

    @staticmethod
    def get_max_value(session, field_name):
        if not field_name:
            return None

        return session.query(func.max(getattr(LogEntry, field_name))).scalar()

    @staticmethod
    def add_record(session, event):
        session.add(LogEntry(**event))

    def skip_file_by_date(self, file_path: str) -> bool:
        compared_time = self.compared_time

        if not compared_time:
            return False

        modify_time = os.path.getmtime(file_path)
        modify_date = datetime.fromtimestamp(modify_time)

        return compared_time > modify_date

    def skip_event(self, session, event: Dict[str, Any]):
        if SKIP_EVENT_BY_DATE:
            return self.skip_event_by_date(event)

        return self.skip_event_by_existence_in_db(session, event)

    def skip_event_by_date(self, event: Dict[str, Any]) -> bool:
        compared_time = self.compared_time

        if not compared_time:
            return False

        return compared_time >= event["event_timestamp"]

    @staticmethod
    def skip_event_by_existence_in_db(session, event: Dict[str, Any]):
        log_id = event["log_id"]

        log_entry = (
            session.query(LogEntry).filter(LogEntry.log_id == log_id).one_or_none()
        )

        return log_entry is not None

    @staticmethod
    def get_event(f) -> Dict[str, str]:
        """
        Returns a log event as a dict.

        The function assume that all the relevant data is between a SYSCALL-PROCTITLE block
        The function assume that SYSCALL with key=(null) are irrelevant since it probably was created by a system event
        """

        event: Dict[str, str] = {}
        line: str = ""
        pattern = re.compile(r"(\S+)=(\S+)")

        # TODO: add an option to not skip null values
        # TODO: add event id verification
        # read lines until a custom event is found
        while not line.startswith("type=SYSCALL") or line.endswith("key=(null)\n"):
            line = f.readline()

            if not line:
                return {}

        # read lines until the user's event is finished
        while not line.startswith("type=PROCTITLE"):
            # Collect the event entry data
            matches = pattern.findall(line)
            event.update(dict(matches))

            # read the next line
            line = f.readline()

        # Collect the event entry data
        matches = pattern.findall(line)
        event.update(dict(matches))

        return event


def main():
    LogParser(LOGS_PATH).run_parser()


if __name__ == "__main__":
    main()
