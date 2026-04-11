"""
定义 foundation_lab 的最小日志初始化逻辑。

当前只做控制台输出，目的是让 API 和脚本层都能复用同一套 logger 创建方式。
"""

from __future__ import annotations

import logging


def setup_logger(name: str = "foundation_lab") -> logging.Logger:
    """创建或复用一个带基础格式化器的 logger。"""

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s | %(name)s | %(levelname)s | %(message)s"))
    logger.addHandler(handler)
    return logger
