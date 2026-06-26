from dataclasses import asdict, dataclass, field
from datetime import datetime

# ========================================
# 6.1 基础用法
# ========================================

# 普通 class 写法（样板代码多）
class UserOld:
    def __init__(self, name: str, age: int, email: str):
        self.name = name
        self.age = age
        self.email = email

    def __repr__(self):
        return f"UserOld(name='{self.name}', age={self.age}, email='{self.email}')"

    def __eq__(self, other):
        return self.name == other.name and self.age == other.age and self.email == other.email


# dataclass 写法（自动生成 __init__、__repr__、__eq__）
@dataclass
class User:
    name: str
    age: int
    email: str


user = User("张三", 25, "zhangsan@example.com")
print(user)        # User(name='张三', age=25, email='zhangsan@example.com')
print(user.name)   # "张三"

user2 = User("张三", 25, "zhangsan@example.com")
print(user == user2)  # True（自动比较所有字段）


# ========================================
# 6.2 默认值与 field()
# ========================================

# 先记结论：
# - 简单类型（int、float、str、bool、None）可以直接写默认值
# - 可变对象（list、dict、set）不要直接写默认值，要用 field(default_factory=...)
#
# 为什么？
# 因为可变对象可以被修改。
# 如果多个实例共享同一个默认 list / dict，一个实例改了，其他实例也会被影响。
#
# 和函数默认参数是同一个坑：
def append_tag_bad(tag: str, tags: list[str] = []):
    tags.append(tag)
    return tags


print("函数默认参数第一次:", append_tag_bad("python"))   # ['python']
print("函数默认参数第二次:", append_tag_bad("dataclass"))  # ['python', 'dataclass']
# 上面第二次调用复用了第一次的同一个默认 list，这就是“可变默认值”的问题。


# dataclass 也一样：
# 下面这种写法会报错，dataclass 明确禁止你这样写
#
# @dataclass
# class BadBag:
#     items: list[str] = []
#
# ValueError: mutable default <class 'list'> for field items is not allowed: use default_factory

@dataclass
class ChatMessage:
    role: str
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict = field(default_factory=dict)  # 可变默认值必须用 field()


msg = ChatMessage(role="user", content="你好")
print(msg)
# ChatMessage(role='user', content='你好', timestamp='2026-03-23T...', metadata={})


msg1 = ChatMessage(role="user", content="第一条")
msg2 = ChatMessage(role="assistant", content="第二条")
msg1.metadata["source"] = "chat"

print("msg1.metadata:", msg1.metadata)  # {'source': 'chat'}
print("msg2.metadata:", msg2.metadata)  # {}
print("是不是同一个 dict:", id(msg1.metadata) == id(msg2.metadata))  # False


@dataclass
class LLMConfig:
    # 这些是不可变默认值，可以直接写
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 1000
    stream: bool = False


# 使用默认值
config1 = LLMConfig()
print("默认配置:", config1)

# 覆盖部分默认值
config2 = LLMConfig(model="claude-sonnet", temperature=0 , stream=True)
print("自定义配置:", config2)


# ========================================
# 6.3 不可变 dataclass（frozen=True）
# ========================================

@dataclass(frozen=True)
class Point:
    x: float
    y: float


p = Point(3.0, 4.0)
print(p)
# p.x = 5.0  # ❌ FrozenInstanceError，取消注释试试

# frozen dataclass 可以放入 set（因为不可变 + 可哈希）
points = {Point(0, 0), Point(1, 1), Point(0, 0)}
print(f"去重后: {len(points)} 个点")  # 2

# ========================================
# 6.4 dataclass vs Pydantic 对比
# ========================================

# asdict() 是 dataclasses 提供的函数，不是实例方法
# 作用：把 dataclass 实例递归转成普通 dict
# 常见场景：
# 1. 打印配置
# 2. 转成 JSON 前先变成 dict
# 3. 传给需要 dict 参数的函数
config = LLMConfig()
print(asdict(config))  # {'model': 'gpt-4o-mini', 'temperature': 0.7, ...}

# dataclass 不验证值
dc = LLMConfig(temperature=999)
print(f"dataclass 不验证: temperature={dc.temperature}")  # 999，不报错


# Pydantic 对比（需要安装：pip install pydantic）
try:
    from pydantic import BaseModel, Field

    class ConfigPD(BaseModel):
        model: str = "gpt-4o-mini"
        # Field(...) 用来补充字段规则
        # ge=0: greater than or equal，必须 >= 0
        # le=2: less than or equal，必须 <= 2
        temperature: float = Field(default=0.7, ge=0, le=2)

    # Pydantic 会验证
    pd_ok = ConfigPD(temperature=0.5)
    print(f"Pydantic 验证通过: {pd_ok}")

    # 调用链：
    # 1. 创建 ConfigPD(...)
    # 2. Pydantic 读取字段定义和 Field 规则
    # 3. 检查 temperature 是否满足 >= 0 且 <= 2
    # 4. 0.5 合法，所以创建成功

    # 下面这一行如果取消注释：
    # 1. Pydantic 会发现 999 不满足 <= 2
    # 2. 因此抛出 ValidationError，而不是默默接收
    # pd_err = ConfigPD(temperature=999)  # ❌ ValidationError，取消注释试试
except ImportError:
    print("pydantic 未安装，跳过对比示例（后续安装后再试）")


# ========================================
# 7.1 常用特殊方法
# ========================================

# 些双下划线方法，本质上是在实现“协议”。平时不是直接调用 counter.__repr__()，而是通过内置函数或运算符触发它。

class TokenCounter:
    """Token 计数器"""
    def __init__(self, model: str):
        self.model = model
        self._counts: list[int] = []

    def add(self, count: int) -> None:
        self._counts.append(count)

    def __str__(self) -> str:
        """print() 时调用"""
        return f"TokenCounter({self.model}): 共 {sum(self._counts)} tokens"

    def __repr__(self) -> str:
        """调试时调用"""
        return f"TokenCounter(model='{self.model}')"

    def __len__(self) -> int:
        """len() 时调用"""
        return len(self._counts)

    def __eq__(self, other) -> bool:
        """== 比较时调用"""
        if not isinstance(other, TokenCounter):
            return False
        return self.model == other.model and self._counts == other._counts

    def __contains__(self, value: int) -> bool:
        """in 操作时调用"""
        return value in self._counts


counter = TokenCounter("gpt-4o-mini")
counter.add(100)
counter.add(250)

print(counter)               # __str__ → TokenCounter(gpt-4o-mini): 共 350 tokens
# repr(counter) 之所以这样写，是因为 repr 是内置函数，它内部再去调用 counter.__repr__()
print(repr(counter))         # __repr__ → TokenCounter(model='gpt-4o-mini')
print(len(counter))          # __len__ → 2
print(100 in counter)        # __contains__ → True


# 内置函数 / 运算符 和特殊方法的对应关系：
# print(counter)  -> str(counter)      -> counter.__str__()
# repr(counter)   -> repr(counter)     -> counter.__repr__()
# len(counter)    -> len(counter)      -> counter.__len__()
# 100 in counter  -> 100 in counter    -> counter.__contains__(100)


# 如果只想减少样板代码，可以改成 dataclass 版本：
@dataclass
class TokenCounterDC:
    model: str
    _counts: list[int] = field(default_factory=list)

    def add(self, count: int) -> None:
        self._counts.append(count)

    def __str__(self) -> str:
        return f"TokenCounterDC({self.model}): 共 {sum(self._counts)} tokens"

    def __len__(self) -> int:
        return len(self._counts)

    def __contains__(self, value: int) -> bool:
        return value in self._counts


counter_dc = TokenCounterDC("gpt-4o-mini")
counter_dc.add(100)
counter_dc.add(250)

print(counter_dc)            # 自己写的 __str__
print(repr(counter_dc))      # dataclass 自动生成的 __repr__
print(len(counter_dc))       # 自己写的 __len__
print(250 in counter_dc)     # 自己写的 __contains__


# ========================================
# 补充：抽象基类（ABC）
# ========================================
from abc import ABC, abstractmethod

class BaseLLM(ABC):
    @abstractmethod
    def chat(self, messages: list) -> str:
        pass

# 没有实现抽象方法会报错
# class MyLLM(BaseLLM):
#     pass
# MyLLM()  # ❌ TypeError

class MyLLM(BaseLLM):
    def chat(self, messages: list) -> str:
        return "实现了"

llm = MyLLM()
print(llm.chat([]))  # "实现了"