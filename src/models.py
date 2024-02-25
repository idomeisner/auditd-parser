from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class LogEntry(Base):
    __tablename__ = "logs"

    # Custom fields
    log_id = Column(String, primary_key=True, unique=True)
    event_timestamp = Column(DateTime, nullable=False)
    processed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    run_num = Column(Integer)

    arch = Column(String)
    syscall = Column(Integer)
    ppid = Column(Integer)
    pid = Column(Integer)
    auid = Column(Integer)
    uid = Column(Integer)
    gid = Column(Integer)
    euid = Column(Integer)
    suid = Column(Integer)
    fsuid = Column(Integer)
    egid = Column(Integer)
    sgid = Column(Integer)
    fsgid = Column(Integer)
    tty = Column(String)
    ses = Column(Integer)
    comm = Column(String)
    exe = Column(String)
    cwd = Column(String)
    mode = Column(String)
    key = Column(String)
