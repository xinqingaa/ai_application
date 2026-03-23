# utils/calculator.py
# 四则运算工具模块
#
# 跨包导入演示：从 config 包导入 CalculationError
# 这是本节的核心学习点之一

from config.exceptions import CalculationError


def add(a: float, b: float) -> float:
    """加法"""
    return a + b


def subtract(a: float, b: float) -> float:
    """减法"""
    return a - b


def multiply(a: float, b: float) -> float:
    """乘法"""
    return a * b


def divide(a: float, b: float) -> float:
    """
    除法

    Raises:
        CalculationError: 当除数为零时
    """
    if b == 0:
        raise CalculationError("除数不能为零")
    return a / b


def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    """安全除法：除零时返回默认值而非抛异常"""
    try:
        return divide(a, b)
    except CalculationError:
        return default


if __name__ == "__main__":
    print("=== 四则运算测试 ===\n")

    print(f"3 + 5 = {add(3, 5)}")
    print(f"10 - 4 = {subtract(10, 4)}")
    print(f"6 * 7 = {multiply(6, 7)}")
    print(f"15 / 3 = {divide(15, 3)}")

    # 测试除零异常
    print("\n=== 除零错误测试 ===")
    try:
        result = divide(10, 0)
    except CalculationError as e:
        print(f"✅ 捕获异常: {e}")

    # 安全除法
    print(f"\n安全除法 10/0 = {safe_divide(10, 0)}")
    print(f"安全除法 10/0 (default=-1) = {safe_divide(10, 0, default=-1)}")
