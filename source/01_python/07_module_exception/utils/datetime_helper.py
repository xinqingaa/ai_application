# utils/datetime_helper.py
# 日期时间工具模块
#
# 无跨包依赖，仅使用标准库

from datetime import datetime, timedelta, timezone


def get_timestamp() -> str:
    """获取当前时间的 ISO 格式字符串（UTC）"""
    return datetime.now(timezone.utc).isoformat()


def format_datetime(
    dt: datetime | None = None,
    fmt: str = "%Y-%m-%d %H:%M:%S"
) -> str:
    """
    格式化日期时间

    Args:
        dt: datetime 对象，默认为当前时间
        fmt: 格式化模板

    Returns:
        格式化后的字符串
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime(fmt)


def time_ago(dt: datetime) -> str:
    """
    计算距今多久，返回人类友好的描述

    Args:
        dt: 过去的时间点

    Returns:
        如 "3 分钟前"、"2 小时前"、"1 天前"
    """
    now = datetime.now(dt.tzinfo)
    diff = now - dt

    seconds = int(diff.total_seconds())
    if seconds < 0:
        return "未来"
    if seconds < 60:
        return f"{seconds} 秒前"
    if seconds < 3600:
        return f"{seconds // 60} 分钟前"
    if seconds < 86400:
        return f"{seconds // 3600} 小时前"
    if seconds < 2592000:
        return f"{seconds // 86400} 天前"
    return f"{seconds // 2592000} 个月前"


def parse_datetime(text: str, fmt: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """
    从字符串解析日期时间

    Args:
        text: 日期时间字符串
        fmt: 格式模板

    Returns:
        datetime 对象

    Raises:
        ValueError: 格式不匹配时
    """
    return datetime.strptime(text, fmt)


if __name__ == "__main__":
    print("=== 日期时间工具测试 ===\n")

    # 当前时间戳
    print(f"UTC 时间戳: {get_timestamp()}")
    print(f"格式化当前时间: {format_datetime()}")
    print(f"自定义格式: {format_datetime(fmt='%Y年%m月%d日')}")

    # time_ago
    print("\n=== 相对时间 ===")
    now = datetime.now()
    examples = [
        ("30秒前", now - timedelta(seconds=30)),
        ("5分钟前", now - timedelta(minutes=5)),
        ("3小时前", now - timedelta(hours=3)),
        ("2天前", now - timedelta(days=2)),
    ]
    for label, dt in examples:
        print(f"  {label} → {time_ago(dt)}")

    # 解析字符串
    print("\n=== 字符串解析 ===")
    dt = parse_datetime("2026-01-15 10:30:00")
    print(f"解析结果: {dt}")
    print(f"距今: {time_ago(dt)}")
