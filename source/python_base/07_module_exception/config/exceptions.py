# config/exceptions.py
# 自定义异常层次
#
# 异常继承关系：
#   Exception
#   └── AppError           （应用基础异常）
#       ├── ConfigError    （配置错误：缺少 API Key 等）
#       └── CalculationError（计算错误：除零等）


class AppError(Exception):
    """应用基础异常，所有自定义异常的父类"""

    def __init__(self, message: str, code: int = 500):
        super().__init__(message)
        self.code = code
        self.message = message

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


class ConfigError(AppError):
    """配置错误：缺少必要的配置项"""

    def __init__(self, key: str, message: str = ""):
        self.key = key
        msg = message or f"缺少必要配置：{key}"
        super().__init__(msg, code=400)


class CalculationError(AppError):
    """计算错误：除零、数值越界等"""

    def __init__(self, message: str):
        super().__init__(message, code=422)


# --- 以下为练习区域 ---
# TODO: 自行添加更多异常类
#
# 1. AuthError：认证错误（code=401）
#    - 属性：provider（哪个平台认证失败）
#
# 2. RateLimitError：速率限制错误（code=429）
#    - 属性：retry_after（建议等待秒数）


if __name__ == "__main__":
    # 直接运行此文件可以测试异常
    print("=== 异常测试 ===")

    try:
        raise AppError("通用错误")
    except AppError as e:
        print(f"捕获 AppError: {e}")

    try:
        raise ConfigError("OPENAI_API_KEY")
    except ConfigError as e:
        print(f"捕获 ConfigError: {e}（key={e.key}）")

    try:
        raise CalculationError("除数不能为零")
    except CalculationError as e:
        print(f"捕获 CalculationError: {e}")

    # 演示异常层次：子类异常可以被父类捕获
    print("\n=== 异常层次演示 ===")
    errors = [
        ConfigError("API_KEY"),
        CalculationError("溢出"),
        AppError("未知错误"),
    ]
    for error in errors:
        try:
            raise error
        except ConfigError as e:
            print(f"  ConfigError → {e}")
        except AppError as e:
            print(f"  AppError → {e}")
