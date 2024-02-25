import logging
import sys

DB_PARAMS = {
    "db_engine": "sqlite",
    "db_path": "auditd_logs.db",
}

"""
# The path to the auditd log file/files
# LOGS_PATH can be a single file or a directory with log files
# Examples:
a. LOGS_PATH = "auditd_logs/"  # checking the directory 'auditd_logs' for logs files
b. LOGS_PATH = "auditd_logs/audit_2.log"  # parsing only the log file 'audit.log'
"""
LOGS_PATH = "auditd_logs/"


OUTPUT_LOG_PATH = "outlog.log"  # logger output log file path
SKIP_FILE_METHOD = "by_last_event"


skip_file_method_mapper = {
    "by_last_run": "processed_at",
    "by_last_event": "event_timestamp",
}

# If set to 'True' it will check the current parsed event again the date of last event found in database
# If set to 'False' it will check if current event is already in the database before adding it
SKIP_EVENT_BY_DATE = False


def get_logger() -> logging.Logger:
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
    logger = logging.getLogger()
    file_handler = logging.FileHandler(OUTPUT_LOG_PATH, mode="w")
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
