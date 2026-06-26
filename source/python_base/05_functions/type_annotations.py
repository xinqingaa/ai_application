from typing import Optional, Union, Literal, TypedDict, Annotated, Any, Callable, TypeVar

# ========================================
# 6.1 Optional 和 Union
# ========================================

# Optional[X] 等价于 X | None
def find_user(user_id: int) -> Optional[dict]:
    users = {1: {"name": "张三"}, 2: {"name": "李四"}}
    return users.get(user_id)

print(find_user(1))    # {"name": "张三"}
print(find_user(99))   # None


# Union[X, Y] 可以是 X 或 Y
def process_input(data: Union[str, list[str]]) -> list[str]:
    if isinstance(data, str):
        return [data]
    return data

print(process_input("hello"))         # ["hello"]
print(process_input(["a", "b"]))      # ["a", "b"]


# Python 3.10+ 简写
def process_input_modern(data: str | list[str]) -> list[str]:
    if isinstance(data, str):
        return [data]
    return data

print(process_input_modern("python"))         # ["python"]
print(process_input_modern(["z", "x" , "y"]))      # ["z", "x", "y"]


# ========================================
# 6.2 Literal
# ========================================

# 限定参数只能是特定的几个值
def set_log_level(level: Literal["debug", "info", "warning", "error"]) -> None:
    print(f"日志级别设置为：{level}")

set_log_level("info")     # ✅
set_log_level("debug")    # ✅
# set_log_level("verbose") # IDE 会提示类型错误


# AI 应用场景：限定模型名称
def chat(
    message: str,
    model: Literal["gpt-4o", "gpt-4o-mini", "claude-sonnet"] = "gpt-4o-mini"
) -> str:
    return f"[{model}] {message}"


print(chat("你好"))
print(chat("你好", model="claude-sonnet"))

# AI 应用场景：限定角色类型
Role = Literal["system", "user", "assistant"]

def create_message(role: Role, content: str) -> dict:
    return {"role": role, "content": content}

print(create_message("system", "你是助手"))
print(create_message("user", "你好"))


# ========================================
# 6.3 TypedDict（类似 TypeScript 的 interface）
# ========================================

class ChatMessage(TypedDict):
    role: str
    content: str

class ChatRequest(TypedDict):
    messages: list[ChatMessage]
    model: str
    temperature: float

message: ChatMessage = {"role": "user", "content": "你好"}
request: ChatRequest = {
    "messages": [message],
    "model": "gpt-4o-mini",
    "temperature": 0.7,
}
print("ChatRequest:", request)

# ========================================
# 6.4 Annotated
# ========================================

# 基础用法：添加描述
UserId = Annotated[int, "用户唯一标识"]
Username = Annotated[str, "用户名，2-20个字符"]

# 结合 Pydantic（需要安装 pydantic，如果没有安装先跳过运行）
# pip install pydantic
try:
    from pydantic import BaseModel, Field

    class User(BaseModel):
        name: Annotated[str, Field(min_length=2, max_length=20, description="用户名")]
        age: Annotated[int, Field(ge=0, le=150, description="年龄")]
        email: Annotated[str | None, Field(default=None, description="邮箱地址")]

    user = User(name="张三", age=25)
    print(f"Pydantic User: {user}")
except ImportError:
    print("pydantic 未安装，跳过 Pydantic 示例（后续安装后再试）")


# ========================================
# 6.5 其他常用类型
# ========================================

# Any
def log(data: Any) -> None:
    print(data)

log("字符串")
log(123)
log([1, 2, 3])


# Callable
def apply_func(func: Callable[[int, int], int], a: int, b: int) -> int:
    return func(a, b)

print(apply_func(lambda a, b: a + b, 3, 5))  # 8


# TypeVar
T = TypeVar("T")

def first(items: list[T]) -> T | None:
    return items[0] if items else None

print(first([1, 2, 3]))        # 1
print(first(["a", "b", "c"]))  # "a"
print(first([]))                # None 
