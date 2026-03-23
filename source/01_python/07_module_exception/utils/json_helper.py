# utils/json_helper.py
# JSON 读写工具模块
#
# 跨包导入：使用 config.exceptions.AppError 处理文件操作异常

import json
import os
from typing import Any

from config.exceptions import AppError


def save_json(data: Any, filepath: str, indent: int = 2) -> None:
    """
    将数据保存为 JSON 文件

    Args:
        data: 要保存的数据（dict / list / 基本类型）
        filepath: 文件路径
        indent: 缩进空格数

    Raises:
        AppError: 写入失败时
    """
    try:
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        print(f"✅ 已保存到 {filepath}")
    except (OSError, TypeError) as e:
        raise AppError(f"保存 JSON 失败: {e}") from e


def load_json(filepath: str) -> Any:
    """
    从 JSON 文件读取数据

    Args:
        filepath: 文件路径

    Returns:
        解析后的 Python 对象

    Raises:
        AppError: 文件不存在或格式错误时
    """
    if not os.path.exists(filepath):
        raise AppError(f"文件不存在: {filepath}", code=404)

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise AppError(f"JSON 格式错误 ({filepath}): {e}", code=400) from e


def pretty_print(data: Any) -> None:
    """格式化打印 JSON 数据"""
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    print("=== JSON 工具测试 ===\n")

    test_data = {
        "name": "AI 助手",
        "version": "1.0",
        "models": ["gpt-4o-mini", "claude-sonnet", "deepseek-chat"],
        "settings": {
            "temperature": 0.7,
            "max_tokens": 1000,
        }
    }

    test_file = "data/test_output.json"

    # 保存
    save_json(test_data, test_file)

    # 读取
    loaded = load_json(test_file)
    print(f"\n读取到的数据:")
    pretty_print(loaded)

    # 测试文件不存在
    print("\n=== 测试文件不存在 ===")
    try:
        load_json("data/不存在.json")
    except AppError as e:
        print(f"✅ 捕获异常: {e}")

    # 清理测试文件
    if os.path.exists(test_file):
        os.remove(test_file)
        print(f"\n🧹 已清理测试文件: {test_file}")
    data_dir = "data"
    if os.path.exists(data_dir) and not os.listdir(data_dir):
        os.rmdir(data_dir)
