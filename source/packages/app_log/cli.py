"""Reusable argparse options for workspace entry points."""

from __future__ import annotations

import argparse

from app_log.logger import configure_logging


def add_log_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--log-format",
        choices=("compact", "verbose", "json", "quiet"),
        default="compact",
        help="终端日志格式",
    )
    parser.add_argument(
        "--log-level",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        default="INFO",
        help="最低日志级别",
    )
    parser.add_argument("--verbose", action="store_true", help="显示完整实验诊断")
    parser.add_argument("--no-color", action="store_true", help="关闭终端颜色")


def configure_from_args(args: argparse.Namespace) -> None:
    log_format = "verbose" if getattr(args, "verbose", False) else args.log_format
    configure_logging(
        log_format=log_format,
        level=args.log_level,
        color="never" if args.no_color else "auto",
    )
