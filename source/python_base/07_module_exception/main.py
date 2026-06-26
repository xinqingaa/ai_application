# main.py
# 第 7 节练习入口：模块、包与异常处理
#
# 演示内容：
# 1. 从 utils 包导入（跨包导入 config.exceptions）
# 2. 从 config 包导入（包内导入）
# 3. 异常处理实战
# 4. 环境变量管理
#
# 运行方式：在 07_module_exception/ 目录下执行
#   python main.py

# 换行使用 括号
from config import (
    AppError,
    ConfigError,
    CalculationError,
    TaskStatus,
    ModelProvider,
)
from config.env_manager import get_config, get_env, load_env, print_config

from utils import add, subtract, multiply, divide
from utils.calculator import safe_divide
from utils.json_helper import save_json, load_json, pretty_print
from utils.datetime_helper import format_datetime, time_ago, get_timestamp

import os
from datetime import datetime, timedelta


def demo_calculator():
    """演示1：四则运算（跨包导入异常类）"""
    print("=" * 50)
    print("📐 演示1：四则运算")
    print("=" * 50)

    print(f"  3 + 5   = {add(3, 5)}")
    print(f"  10 - 4  = {subtract(10, 4)}")
    print(f"  6 × 7   = {multiply(6, 7)}")
    print(f"  15 ÷ 3  = {divide(15, 3)}")

    print("\n  测试除零异常（CalculationError 来自 config 包）:")
    try:
        divide(10, 0)
    except CalculationError as e:
        print(f"  ✅ 捕获: {e}")

    print(f"  安全除法 10/0 = {safe_divide(10, 0, default=-1)}")


def demo_enums():
    """演示2：枚举使用"""
    print("\n" + "=" * 50)
    print("🏷️  演示2：枚举")
    print("=" * 50)

    # TaskStatus
    status = TaskStatus.IN_PROGRESS
    print(f"  当前状态: {status} (name={status.name})")
    print(f"  与字符串比较: {status == 'in_progress'}")

    print(f"  活跃状态: {TaskStatus.active_statuses()}")

    # ModelProvider
    print(f"\n  模型列表:")
    for p in ModelProvider:
        print(f"    {p.value:10s} → {p.get_api_base_url()}")


def demo_json():
    """演示3：JSON 读写"""
    print("\n" + "=" * 50)
    print("📄 演示3：JSON 读写")
    print("=" * 50)

    data = {
        "task": "学习 Python 模块与包",
        "status": TaskStatus.IN_PROGRESS.value,
        "created_at": get_timestamp(),
        "tags": ["python", "模块", "异常处理"],
        "config": {
            "model": ModelProvider.OPENAI.value,
            "temperature": 0.7,
        }
    }

    test_file = "data/demo_output.json"

    # 保存
    save_json(data, test_file)

    # 读取
    loaded = load_json(test_file)
    print("  读取内容:")
    pretty_print(loaded)

    # 清理
    os.remove(test_file)
    data_dir = "data"
    if os.path.exists(data_dir) and not os.listdir(data_dir):
        os.rmdir(data_dir)
    print("  🧹 已清理测试文件")


def demo_datetime():
    """演示4：日期时间工具"""
    print("\n" + "=" * 50)
    print("🕐 演示4：日期时间工具")
    print("=" * 50)

    print(f"  当前时间: {format_datetime()}")
    print(f"  UTC 时间戳: {get_timestamp()}")

    # 相对时间
    now = datetime.now()
    points = [
        ("刚才", now - timedelta(seconds=10)),
        ("半小时前", now - timedelta(minutes=30)),
        ("昨天", now - timedelta(days=1)),
        ("一周前", now - timedelta(weeks=1)),
    ]
    print("\n  相对时间:")
    for label, dt in points:
        print(f"    {label:8s} → {time_ago(dt)}")


def demo_env_config():
    """演示5：环境变量管理"""
    print("\n" + "=" * 50)
    print("⚙️  演示5：环境变量管理")
    print("=" * 50)

    # 加载环境变量
    load_env()

    # 读取非必要变量
    debug = get_env("DEBUG", default="false")
    print(f"  DEBUG = {debug}")

    # 读取必要变量（可能报错）
    try:
        config = get_config()
        print_config(config)
    except ConfigError as e:
        print(f"  ⚠️  配置未完成: {e}")
        print("  💡 提示: 复制 .env.example 为 .env 并填入 API Key")


def demo_exception_chain():
    """演示6：异常层次与捕获顺序"""
    print("\n" + "=" * 50)
    print("🛡️  演示6：异常层次")
    print("=" * 50)

    errors = [
        ConfigError("API_KEY"),
        CalculationError("溢出"),
        AppError("未知问题"),
    ]

    for error in errors:
        try:
            raise error
        except ConfigError as e:
            print(f"  ConfigError      → {e}")
        except CalculationError as e:
            print(f"  CalculationError → {e}")
        except AppError as e:
            print(f"  AppError         → {e}")

    # 用父类统一捕获
    print("\n  用 AppError 统一捕获:")
    for error in errors:
        try:
            raise error
        except AppError as e:
            print(f"    {type(e).__name__:20s} → {e}")


def main():
    """主函数：运行所有演示"""
    print("\n🐍 第 7 节：模块、包与异常处理 — 综合演示\n")

    demos = [
        ("1", "四则运算（跨包导入）", demo_calculator),
        ("2", "枚举", demo_enums),
        ("3", "JSON 读写", demo_json),
        ("4", "日期时间", demo_datetime),
        ("5", "环境变量管理", demo_env_config),
        ("6", "异常层次", demo_exception_chain),
    ]

    print("请选择要运行的演示（输入编号，或 'a' 运行全部，'q' 退出）:\n")
    for num, name, _ in demos:
        print(f"  [{num}] {name}")
    print(f"  [a] 运行全部")
    print(f"  [q] 退出")

    while True:
        choice = input("\n👉 请输入: ").strip().lower()

        if choice == "q":
            print("\n👋 再见！")
            break
        elif choice == "a":
            for _, _, func in demos:
                func()
            print("\n✅ 所有演示运行完毕！")
            break
        elif choice in [num for num, _, _ in demos]:
            idx = int(choice) - 1
            demos[idx][2]()
        else:
            print(f"  无效输入: '{choice}'，请输入 1-6、a 或 q")


if __name__ == "__main__":
    main()
