# config/enums.py
# 枚举定义：TaskStatus / ModelProvider
#
# Python 3.11+ 使用 StrEnum，值可以直接当字符串使用
# 注意：旧写法 class X(str, Enum) 在 Python 3.11+ 中 str() 行为已变更，
#       str(X.A) 会返回 "X.A" 而非值本身，所以推荐用 StrEnum

from enum import StrEnum


class TaskStatus(StrEnum):
    """任务状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

    @classmethod
    def active_statuses(cls) -> list["TaskStatus"]:
        """返回所有'进行中'的状态"""
        return [cls.PENDING, cls.IN_PROGRESS]


class ModelProvider(StrEnum):
    """模型供应商枚举"""
    OPENAI = "openai"
    CLAUDE = "claude"
    DEEPSEEK = "deepseek"
    TONGYI = "tongyi"

    def get_api_base_url(self) -> str:
        """返回对应平台的 API 地址"""
        urls = {
            ModelProvider.OPENAI: "https://api.openai.com/v1",
            ModelProvider.CLAUDE: "https://api.anthropic.com",
            ModelProvider.DEEPSEEK: "https://api.deepseek.com",
            ModelProvider.TONGYI: "https://dashscope.aliyuncs.com/api/v1",
        }
        return urls[self]


if __name__ == "__main__":
    print("=== TaskStatus 枚举 ===")

    # 基础使用
    status = TaskStatus.PENDING
    print(f"name: {status.name}")    # PENDING
    print(f"value: {status.value}")  # pending
    print(f"str: {status}")          # pending（StrEnum 直接输出值）

    # 比较
    print(f"\n与字符串比较: {status == 'pending'}")  # True
    print(f"与枚举比较: {status == TaskStatus.PENDING}")  # True

    # 从字符串创建
    from_str = TaskStatus("completed")
    print(f"\n从字符串创建: {from_str}")

    # 遍历
    print("\n所有状态:")
    for s in TaskStatus:
        print(f"  {s.name:15s} → {s.value}")

    # 类方法
    print(f"\n进行中的状态: {TaskStatus.active_statuses()}")

    print("\n=== ModelProvider 枚举 ===")

    for provider in ModelProvider:
        print(f"  {provider.value:10s} → {provider.get_api_base_url()}")

    # --- 练习 ---
    # TODO: 添加 LogLevel 枚举
    #   - DEBUG, INFO, WARNING, ERROR, CRITICAL
    #   - 添加一个方法 should_log(min_level) 判断是否应该输出
