"""Application-wide structured logging and terminal presentation."""

from app_log.cli import add_log_arguments, configure_from_args
from app_log.console import AppConsole, console
from app_log.events import LogEvent
from app_log.logger import AppLogger, configure_logging, get_logger

__all__ = [
    "AppConsole",
    "AppLogger",
    "LogEvent",
    "add_log_arguments",
    "configure_from_args",
    "configure_logging",
    "console",
    "get_logger",
]
