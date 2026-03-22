# 03. 字符串与文件基础 - 练习题
# 请在下方完成练习

import json
from pathlib import Path
from datetime import datetime
from typing import Optional


# ============================================
# 练习 1：字符串处理
# ============================================

def exercise_1():
    """字符串处理练习"""
    text = "  Hello, World! Welcome to Python!  "

    # 1. 去除首尾空格
    stripped = None  # TODO: 你的代码

    # 2. 转换为小写
    lower = None  # TODO: 你的代码

    # 3. 按空格分割成列表
    words = None  # TODO: 你的代码

    # 4. 用 "-" 连接列表
    joined = None  # TODO: 你的代码

    # 5. 统计 "o" 出现的次数
    count_o = None  # TODO: 你的代码

    # 6. 将所有 "o" 替换为 "O"
    replaced = None  # TODO: 你的代码

    print(f"去除空格: '{stripped}'")
    print(f"小写: '{lower}'")
    print(f"分割: {words}")
    print(f"连接: '{joined}'")
    print(f"'o' 出现次数: {count_o}")
    print(f"替换后: '{replaced}'")


# ============================================
# 练习 2：格式化输出
# ============================================

def exercise_2():
    """格式化输出练习"""

    # 1. 商品列表格式化
    products = [
        {"name": "iPhone", "price": 5999, "quantity": 2},
        {"name": "MacBook", "price": 9999, "quantity": 1},
        {"name": "AirPods", "price": 1299, "quantity": 3},
    ]

    print("商品列表：")
    print("-" * 50)
    # TODO: 使用 f-string 实现格式化输出
    # 商品名        单价    数量    小计
    # iPhone       5999    2       11998
    # ...

    # 2. 百分比和进度条
    progress = 0.856
    # TODO: 输出 "进度：85.60%"
    # TODO: 输出进度条 "完成：████████░░ 85.6%"

    # 3. 数字格式化
    numbers = [1234567, 0.856, 3.14159, 255]
    # TODO: 分别格式化为：
    # 1,234,567
    # 85.60%
    # 3.14
    # 0xff


# ============================================
# 练习 3：文件读写
# ============================================

def exercise_3():
    """文件读写练习"""
    data_dir = Path("source/01_python/03_string_file/data")
    data_dir.mkdir(parents=True, exist_ok=True)

    file_path = data_dir / "numbers.txt"

    # 1. 创建文件，写入 1-100（每行一个数字）
    # TODO: 你的代码

    # 2. 读取文件，计算所有数字的和
    total = 0  # TODO: 你的代码

    # 3. 追加一行 "总和: xxx"
    # TODO: 你的代码

    # 4. 读取文件，找出所有偶数
    even_numbers = []  # TODO: 你的代码

    print(f"总和: {total}")
    print(f"偶数: {even_numbers[:10]}...")  # 只显示前10个


# ============================================
# 练习 4：日志解析
# ============================================

def parse_log(filepath: str) -> list:
    """
    解析日志文件，返回日志列表

    每条日志格式：
    {
        "timestamp": "2024-01-15 10:30:15",
        "level": "INFO",
        "message": "User logged in"
    }
    """
    logs = []
    # TODO: 你的代码
    return logs


def filter_by_level(logs: list, level: str) -> list:
    """按级别过滤日志"""
    # TODO: 你的代码
    return []


def count_by_level(logs: list) -> dict:
    """统计各级别数量"""
    # TODO: 你的代码
    return {}


def extract_timestamps(logs: list) -> list:
    """提取所有时间戳"""
    # TODO: 你的代码
    return []


def exercise_4():
    """日志解析练习"""
    data_dir = Path("source/01_python/03_string_file/data")
    log_file = data_dir / "log.txt"

    # 创建测试日志文件
    log_content = """2024-01-15 10:30:15 INFO User logged in
2024-01-15 10:31:20 ERROR Database connection failed
2024-01-15 10:32:00 WARN Memory usage high
2024-01-15 10:33:10 ERROR API timeout
2024-01-15 10:34:00 INFO Request completed
2024-01-15 10:35:00 DEBUG Processing data
2024-01-15 10:36:00 ERROR Network error"""

    log_file.write_text(log_content, encoding="utf-8")

    # 1. 解析日志
    logs = parse_log(str(log_file))
    print(f"解析日志: {len(logs)} 条")

    # 2. 过滤 ERROR
    errors = filter_by_level(logs, "ERROR")
    print(f"ERROR 日志: {len(errors)} 条")

    # 3. 统计各级别
    counts = count_by_level(logs)
    print(f"各级别统计: {counts}")

    # 4. 提取时间戳
    timestamps = extract_timestamps(logs)
    print(f"时间戳: {timestamps[:3]}...")


# ============================================
# 练习 5：路径操作
# ============================================

def exercise_5():
    """路径操作练习"""
    base_dir = Path("source/01_python/03_string_file/data")

    # 1. 创建目录结构 data/2024/01
    # TODO: 你的代码

    # 2. 在该目录下创建文件 summary.txt
    # TODO: 你的代码

    # 3. 检查文件是否存在
    # TODO: 你的代码

    # 4. 获取文件的父目录、文件名、扩展名
    file_path = base_dir / "2024" / "01" / "summary.txt"
    # TODO: 你的代码

    # 5. 列出 data 目录下的所有 .txt 文件
    # TODO: 你的代码

    # 6. 计算文件大小（字节）
    # TODO: 你的代码

    print(f"文件存在: {file_path.exists()}")
    print(f"父目录: {file_path.parent}")
    print(f"文件名: {file_path.name}")
    print(f"扩展名: {file_path.suffix}")


# ============================================
# 练习 6：配置文件处理
# ============================================

class ConfigManager:
    """配置文件管理器"""

    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.config = {}
        self._load()

    def _load(self):
        """读取配置文件"""
        # TODO: 实现
        # 格式：
        # # 这是注释
        # API_KEY=sk-xxx
        # MODEL=gpt-4
        # MAX_TOKENS=1000
        # DEBUG=true
        pass

    def _parse_value(self, value: str):
        """
        解析配置值，支持类型转换：
        - true/false -> bool
        - 数字 -> int/float
        - 其他 -> str
        """
        # TODO: 实现
        return value

    def save(self):
        """保存配置到文件"""
        # TODO: 实现
        pass

    def get(self, key: str, default=None):
        """获取配置项"""
        # TODO: 实现
        return default

    def set(self, key: str, value):
        """设置配置项"""
        # TODO: 实现
        pass

    def __str__(self):
        return str(self.config)


def exercise_6():
    """配置文件处理练习"""
    data_dir = Path("source/01_python/03_string_file/data")
    config_file = data_dir / "config.txt"

    # 创建测试配置文件
    config_content = """# 应用配置
API_KEY=sk-test-12345
MODEL=gpt-4
MAX_TOKENS=1000
DEBUG=true
TIMEOUT=30.5"""

    config_file.write_text(config_content, encoding="utf-8")

    # 测试 ConfigManager
    config = ConfigManager(str(config_file))

    print(f"配置内容: {config}")
    print(f"API_KEY: {config.get('API_KEY')}")
    print(f"DEBUG: {config.get('DEBUG')} (类型: {type(config.get('DEBUG'))})")
    print(f"MAX_TOKENS: {config.get('MAX_TOKENS')} (类型: {type(config.get('MAX_TOKENS'))})")
    print(f"不存在的配置: {config.get('NOT_EXIST', '默认值')}")

    # 修改配置
    config.set("NEW_KEY", "new_value")
    config.save()
    print(f"修改后: {config}")


# ============================================
# 运行所有练习
# ============================================

if __name__ == "__main__":
    print("=" * 50)
    print("练习 1：字符串处理")
    print("=" * 50)
    exercise_1()

    print("\n" + "=" * 50)
    print("练习 2：格式化输出")
    print("=" * 50)
    exercise_2()

    print("\n" + "=" * 50)
    print("练习 3：文件读写")
    print("=" * 50)
    exercise_3()

    print("\n" + "=" * 50)
    print("练习 4：日志解析")
    print("=" * 50)
    exercise_4()

    print("\n" + "=" * 50)
    print("练习 5：路径操作")
    print("=" * 50)
    exercise_5()

    print("\n" + "=" * 50)
    print("练习 6：配置文件处理")
    print("=" * 50)
    exercise_6()
