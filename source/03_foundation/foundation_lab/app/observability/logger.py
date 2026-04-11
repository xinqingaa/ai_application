"""
Minimal logger setup for foundation_lab.
"""

from __future__ import annotations

import logging


def setup_logger(name: str = "foundation_lab") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s | %(name)s | %(levelname)s | %(message)s"))
    logger.addHandler(handler)
    return logger
