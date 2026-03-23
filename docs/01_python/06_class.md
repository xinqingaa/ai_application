# 06. 类与面向对象

> 本节目标：掌握类的定义、方法类型、dataclass、封装与继承

---

## 1. 概述

### 学习目标

- 掌握类的定义、`__init__`、`self` 的含义
- 区分实例属性和类属性
- 掌握实例方法、类方法、静态方法的使用场景
- 掌握 dataclass 的用法及与普通 class 的区别
- 了解封装（私有属性、property）和继承
- 了解常用特殊方法

### 预计学习时间

- 类基础与方法：1.5 小时
- dataclass：1 小时
- 封装与继承：1 小时
- 特殊方法：30 分钟
- 练习：1-2 小时

### 本节在 AI 应用中的重要性

| 场景 | 相关知识 |
|-----|---------|
| Pydantic BaseModel | 类定义、继承、属性 |
| LLM 客户端封装 | 类、实例方法、__init__ 配置 |
| 配置对象、指标收集 | dataclass |
| LangChain Tool / Agent | 类继承、方法重写 |
| FastAPI 依赖注入 | 类实例作为依赖 |
| 错误类型定义 | 继承 Exception |

---

## 2. 类基础 📌

### 2.1 什么是类

类是创建对象的"模板"。如果你熟悉 JavaScript/TypeScript 的 class，Python 的 class 概念完全一样，只是语法略有不同。

```python
# JavaScript
# class Person {
#     constructor(name, age) {
#         this.name = name;
#         this.age = age;
#     }
# }

# Python
class Person:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age
```

### 2.2 `__init__` 和 `self`

- `__init__` 是构造函数（JS 中的 `constructor`）
- `self` 是对当前实例的引用（JS 中的 `this`），**必须作为第一个参数显式写出**

```python
class User:
    def __init__(self, name: str, email: str, age: int = 0):
        self.name = name      # 实例属性
        self.email = email
        self.age = age

    def greet(self) -> str:
        return f"你好，我是 {self.name}，邮箱是 {self.email}"

    def is_adult(self) -> bool:
        return self.age >= 18


# 创建实例
user1 = User("张三", "zhangsan@example.com", 25)
user2 = User("李四", "lisi@example.com")

print(user1.greet())     # "你好，我是 张三，邮箱是 zhangsan@example.com"
print(user1.is_adult())  # True
print(user2.age)         # 0（使用了默认值）
```

> **关键区别**：JS 的 `this` 是隐式的，Python 的 `self` 是显式的。每个实例方法的第一个参数都必须是 `self`，调用时不需要手动传。

### 2.3 实例属性 vs 类属性

```python
class Dog:
    # 类属性：所有实例共享
    species = "犬科"
    count = 0

    def __init__(self, name: str, breed: str):
        # 实例属性：每个实例独立
        self.name = name
        self.breed = breed
        Dog.count += 1  # 通过类名访问类属性


dog1 = Dog("旺财", "柴犬")
dog2 = Dog("小黑", "拉布拉多")

print(dog1.species)   # "犬科"（通过实例访问类属性）
print(Dog.species)    # "犬科"（通过类名访问类属性）
print(dog1.name)      # "旺财"（实例属性）
print(Dog.count)      # 2
```

| 维度 | 类属性 | 实例属性 |
|------|--------|---------|
| 定义位置 | class 内部、方法外部 | `__init__` 中通过 `self.xxx` |
| 归属 | 属于类本身 | 属于每个实例 |
| 共享性 | 所有实例共享 | 每个实例独立 |
| 访问方式 | `类名.属性` 或 `实例.属性` | `实例.属性` |
| 典型用途 | 计数器、默认配置、常量 | 对象的具体数据 |

---

## 3. 方法类型 📌

### 3.1 实例方法

最常见的方法类型，通过 `self` 访问实例属性和其他方法：

```python
class Calculator:
    def __init__(self):
        self.history: list[str] = []

    def add(self, a: float, b: float) -> float:
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result

    def get_history(self) -> list[str]:
        return self.history


calc = Calculator()
calc.add(3, 5)
calc.add(10, 20)
print(calc.get_history())  # ["3 + 5 = 8", "10 + 20 = 30"]
```

### 3.2 类方法（@classmethod）

用 `@classmethod` 装饰，第一个参数是 `cls`（类本身），常用于"替代构造函数"：

```python
class User:
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """从字典创建 User（替代构造函数）"""
        return cls(data["name"], data["email"])

    @classmethod
    def from_string(cls, info: str) -> "User":
        """从字符串创建 User，格式：'name,email'"""
        name, email = info.split(",")
        return cls(name.strip(), email.strip())


# 多种创建方式
user1 = User("张三", "zhangsan@example.com")
user2 = User.from_dict({"name": "李四", "email": "lisi@example.com"})
user3 = User.from_string("王五, wangwu@example.com")
```

> **AI 应用场景**：Pydantic 的 `model_validate()` 本质上就是类方法——从 dict/JSON 创建模型实例。

### 3.3 静态方法（@staticmethod）

不需要访问实例（self）或类（cls），只是逻辑上归属于这个类的工具函数：

```python
class MathUtils:
    @staticmethod
    def is_even(n: int) -> bool:
        return n % 2 == 0

    @staticmethod
    def clamp(value: float, min_val: float, max_val: float) -> float:
        """将值限制在范围内"""
        return max(min_val, min(max_val, value))


MathUtils.is_even(4)       # True
MathUtils.clamp(1.5, 0, 1) # 1.0
```

### 3.4 三种方法对比

```python
class Demo:
    class_var = "我是类属性"

    def __init__(self, value: str):
        self.value = value

    def instance_method(self):
        """实例方法：能访问 self 和 cls"""
        return f"实例方法 → self.value={self.value}, cls={Demo.class_var}"

    @classmethod
    def class_method(cls):
        """类方法：能访问 cls，不能访问 self"""
        return f"类方法 → cls.class_var={cls.class_var}"

    @staticmethod
    def static_method():
        """静态方法：不能访问 self 和 cls"""
        return "静态方法 → 独立的工具函数"
```

| 方法类型 | 装饰器 | 第一个参数 | 能访问 | 典型用途 |
|---------|--------|-----------|--------|---------|
| 实例方法 | 无 | `self` | 实例属性、类属性 | 操作对象数据 |
| 类方法 | `@classmethod` | `cls` | 类属性 | 替代构造函数 |
| 静态方法 | `@staticmethod` | 无 | 都不能 | 工具函数 |

---

## 4. 封装 ⚡

### 4.1 私有属性

Python 没有真正的私有（不像 Java/TS 的 `private`），而是用命名约定：

```python
class Account:
    def __init__(self, owner: str, balance: float):
        self.owner = owner        # 公开属性
        self._id = id(self)       # 约定私有（单下划线）：外部能访问但不应该
        self.__balance = balance   # 名称改写（双下划线）：外部难以直接访问

    def get_balance(self) -> float:
        return self.__balance


acc = Account("张三", 1000)
print(acc.owner)        # ✅ "张三"
print(acc._id)          # ✅ 能访问（但约定不应该）
# print(acc.__balance)  # ❌ AttributeError
print(acc.get_balance()) # ✅ 1000

# 实际上双下划线只是被改写了名字
print(acc._Account__balance)  # 1000（能访问，但强烈不推荐）
```

| 命名 | 含义 | 能否外部访问 |
|------|------|------------|
| `name` | 公开 | ✅ |
| `_name` | 约定私有（"请不要直接用"） | ✅ 但不建议 |
| `__name` | 名称改写（强私有） | 技术上可以但不应该 |

### 4.2 @property 装饰器

`@property` 让方法像属性一样访问，常用于只读属性或需要验证的属性：

```python
class Temperature:
    def __init__(self, celsius: float):
        self._celsius = celsius

    @property
    def celsius(self) -> float:
        """只读属性"""
        return self._celsius

    @celsius.setter
    def celsius(self, value: float) -> None:
        """写入时验证"""
        if value < -273.15:
            raise ValueError("温度不能低于绝对零度")
        self._celsius = value

    @property
    def fahrenheit(self) -> float:
        """计算属性（只读）"""
        return self._celsius * 9 / 5 + 32


temp = Temperature(100)
print(temp.celsius)     # 100（像属性一样访问，实际调用了方法）
print(temp.fahrenheit)  # 212.0
temp.celsius = 37       # 调用了 setter
# temp.celsius = -300   # ValueError: 温度不能低于绝对零度
```

> **AI 应用场景**：Pydantic 的 `@computed_field` 和 `@field_validator` 本质上就是 property + 验证的思路。

---

## 5. 继承 ⚡

### 5.1 基础继承

```python
class Animal:
    def __init__(self, name: str, sound: str):
        self.name = name
        self.sound = sound

    def speak(self) -> str:
        return f"{self.name} 说：{self.sound}"

    def info(self) -> str:
        return f"动物：{self.name}"


class Dog(Animal):
    def __init__(self, name: str, breed: str):
        super().__init__(name, "汪汪")  # 调用父类构造函数
        self.breed = breed

    # 方法重写
    def info(self) -> str:
        return f"狗：{self.name}（{self.breed}）"

    # 新增方法
    def fetch(self) -> str:
        return f"{self.name} 去捡球了"


dog = Dog("旺财", "柴犬")
print(dog.speak())  # "旺财 说：汪汪"（继承的方法）
print(dog.info())   # "狗：旺财（柴犬）"（重写的方法）
print(dog.fetch())  # "旺财 去捡球了"（新方法）
```

### 5.2 实际应用：自定义异常

继承最常见的实际用途之一是自定义异常类：

```python
class AppError(Exception):
    """应用基础异常"""
    def __init__(self, message: str, code: int = 500):
        super().__init__(message)
        self.code = code


class NotFoundError(AppError):
    """资源不存在"""
    def __init__(self, resource: str):
        super().__init__(f"{resource} 不存在", code=404)


class AuthError(AppError):
    """认证失败"""
    def __init__(self, message: str = "认证失败"):
        super().__init__(message, code=401)


# 使用
try:
    raise NotFoundError("用户 #123")
except AppError as e:
    print(f"错误 [{e.code}]: {e}")
    # 错误 [404]: 用户 #123 不存在
```

### 5.3 实际应用：LLM 客户端抽象

```python
class BaseLLMClient:
    """LLM 客户端基类"""
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model

    def chat(self, messages: list[dict]) -> str:
        raise NotImplementedError("子类必须实现 chat 方法")


class OpenAIClient(BaseLLMClient):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        super().__init__(api_key, model)

    def chat(self, messages: list[dict]) -> str:
        # 实际会调用 OpenAI API
        return f"[OpenAI/{self.model}] 模拟响应"


class ClaudeClient(BaseLLMClient):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        super().__init__(api_key, model)

    def chat(self, messages: list[dict]) -> str:
        # 实际会调用 Anthropic API
        return f"[Claude/{self.model}] 模拟响应"


# 统一接口使用
def get_response(client: BaseLLMClient, question: str) -> str:
    messages = [{"role": "user", "content": question}]
    return client.chat(messages)

openai_client = OpenAIClient("sk-xxx")
claude_client = ClaudeClient("sk-xxx")

print(get_response(openai_client, "你好"))  # [OpenAI/gpt-4o-mini] 模拟响应
print(get_response(claude_client, "你好"))  # [Claude/claude-sonnet-4-20250514] 模拟响应
```

> 这就是面向对象的多态——不同子类实现同一个接口，调用方不需要关心具体是哪个类。后续学到 LLM 阶段封装统一客户端时会用到这个模式。

---

## 6. dataclass 📌 🔗

> dataclass 是 Python 3.7+ 的内置功能，专门用于创建"主要用来存数据"的类，大幅减少样板代码。

### 6.1 基础用法

```python
from dataclasses import dataclass


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


# dataclass 写法（一行搞定）
@dataclass
class User:
    name: str
    age: int
    email: str


# 自动生成了 __init__、__repr__、__eq__
user = User("张三", 25, "zhangsan@example.com")
print(user)        # User(name='张三', age=25, email='zhangsan@example.com')
print(user.name)   # "张三"

user2 = User("张三", 25, "zhangsan@example.com")
print(user == user2)  # True（自动比较所有字段）
```

### 6.2 默认值与 field()

```python
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ChatMessage:
    role: str
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict = field(default_factory=dict)  # 可变默认值用 field()


msg = ChatMessage(role="user", content="你好")
print(msg)
# ChatMessage(role='user', content='你好', timestamp='2026-03-23T...', metadata={})


@dataclass
class LLMConfig:
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 1000
    stream: bool = False


# 使用默认值
config = LLMConfig()
print(config)  # LLMConfig(model='gpt-4o-mini', temperature=0.7, max_tokens=1000, stream=False)

# 覆盖部分默认值
config = LLMConfig(model="claude-sonnet", temperature=0)
print(config)
```

> **注意**：和函数默认参数一样，可变对象（list、dict）必须用 `field(default_factory=...)` 而不是直接赋值。

### 6.3 不可变 dataclass

```python
@dataclass(frozen=True)
class Point:
    x: float
    y: float


p = Point(3.0, 4.0)
# p.x = 5.0  # ❌ FrozenInstanceError: cannot assign to field 'x'

# frozen dataclass 可以用作字典的 key 或放入 set
points = {Point(0, 0), Point(1, 1), Point(0, 0)}
print(len(points))  # 2（去重了）
```

### 6.4 dataclass vs 普通 class vs Pydantic BaseModel

| 维度 | 普通 class | dataclass | Pydantic BaseModel |
|------|-----------|-----------|-------------------|
| 样板代码 | 多（手写 __init__ 等） | 少（自动生成） | 少（自动生成） |
| 运行时验证 | 无 | 无 | **有**（自动验证类型） |
| 性能 | 最快 | 快 | 稍慢（有验证开销） |
| 序列化 | 需手写 | 需手写或用 asdict() | 内置 `.model_dump()` |
| 适用场景 | 复杂业务逻辑 | 内部数据结构、配置 | API 请求/响应、数据验证 |

```python
from dataclasses import dataclass, asdict
from pydantic import BaseModel, Field


# dataclass：轻量、无验证
@dataclass
class ConfigDC:
    model: str = "gpt-4o-mini"
    temperature: float = 0.7


# Pydantic：有验证
class ConfigPD(BaseModel):
    model: str = "gpt-4o-mini"
    temperature: float = Field(default=0.7, ge=0, le=2)


# dataclass 不会验证
dc = ConfigDC(temperature=999)  # ✅ 不报错（但值不合理）

# Pydantic 会验证
# pd = ConfigPD(temperature=999)  # ❌ ValidationError
```

> **选择建议**：
> - 内部数据传递、配置对象、指标收集 → **dataclass**
> - API 输入输出、用户数据、需要验证 → **Pydantic BaseModel**
> - 复杂业务逻辑、需要很多自定义方法 → **普通 class**

---

## 7. 特殊方法 ⚡

Python 的特殊方法（也叫 dunder methods，双下划线方法）让你的类能和 Python 内置操作配合。

### 7.1 常用特殊方法

```python
class TokenCounter:
    """Token 计数器"""
    def __init__(self, model: str):
        self.model = model
        self._counts: list[int] = []

    def add(self, count: int) -> None:
        self._counts.append(count)

    def __str__(self) -> str:
        """print() 时调用，面向用户的可读字符串"""
        return f"TokenCounter({self.model}): 共 {sum(self._counts)} tokens"

    def __repr__(self) -> str:
        """调试时显示，面向开发者，能重新创建对象"""
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

print(counter)               # TokenCounter(gpt-4o-mini): 共 350 tokens
print(repr(counter))         # TokenCounter(model='gpt-4o-mini')
print(len(counter))          # 2
print(100 in counter)        # True
```

### 7.2 常见特殊方法速查

| 方法 | 触发方式 | 用途 |
|------|---------|------|
| `__init__` | `Class()` | 构造函数 |
| `__str__` | `print(obj)`, `str(obj)` | 可读字符串 |
| `__repr__` | 调试显示, `repr(obj)` | 开发者字符串 |
| `__len__` | `len(obj)` | 长度 |
| `__eq__` | `obj == other` | 相等比较 |
| `__lt__` | `obj < other` | 小于比较（支持排序） |
| `__contains__` | `x in obj` | 包含检查 |
| `__getitem__` | `obj[key]` | 索引访问 |
| `__iter__` | `for x in obj` | 迭代 |

> 日常开发中最常用的是 `__init__`、`__str__`、`__repr__`。dataclass 会自动生成其中大部分。

---

## 8. 小结

### 核心知识

| 知识点 | 优先级 | 一句话总结 |
|--------|-------|-----------|
| class / __init__ / self | 📌 | 定义类的基本语法，self 等同于 JS 的 this |
| 实例方法 / classmethod / staticmethod | 📌 | 实例方法最常用，classmethod 常做替代构造函数 |
| dataclass | 📌🔗 | 数据类的首选写法，AI 应用中配置和中间结构常用 |
| 封装（_、__、property） | ⚡ | 了解命名约定，property 后续 Pydantic 会用到 |
| 继承 | ⚡ | 理解 super() 和方法重写，自定义异常和抽象基类会用到 |
| 特殊方法 | ⚡ | 了解 __str__/__repr__，dataclass 会自动生成 |

### 与 JavaScript 关键差异

| 差异点 | JavaScript | Python |
|--------|-----------|--------|
| 构造函数 | `constructor()` | `__init__(self)` |
| this/self | `this`（隐式） | `self`（显式，必须写） |
| 私有属性 | `#name`（真私有） | `__name`（名称改写，非真私有） |
| 静态方法 | `static method()` | `@staticmethod` |
| getter/setter | `get name()` / `set name()` | `@property` / `@xxx.setter` |
| 继承 | `extends` | `class Child(Parent):` |
| 调用父类 | `super.method()` | `super().method()` |

### 下一节预告

下一节将学习 **模块、包与异常处理**：
- import 与模块系统
- 常用标准库（os、json、datetime）
- 环境变量管理（新增）
- 枚举 Enum（新增）
- try/except 异常处理
- 自定义异常

---

## 9. 常见问题

### Q: self 能用别的名字吗？

技术上可以，但**绝对不要这么做**。`self` 是 Python 社区的强制约定，换名字会让所有人困惑：

```python
# ❌ 能运行但不要这么写
class Bad:
    def method(this):  # 别这样
        return this

# ✅ 永远用 self
class Good:
    def method(self):
        return self
```

### Q: 什么时候用 class，什么时候用 dict？

- **只是传递数据**（几个字段，不需要方法）→ dict 或 dataclass
- **需要方法和行为** → class
- **需要数据验证** → Pydantic BaseModel
- **来自 JSON/API 的数据** → dict → Pydantic 验证 → 内部使用

```python
# 简单场景用 dict 就够了
config = {"model": "gpt-4o-mini", "temperature": 0.7}

# 复杂场景或需要类型提示时用 dataclass
@dataclass
class LLMConfig:
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
```

### Q: dataclass 和 NamedTuple 有什么区别？

- `dataclass` 是可变的（默认），可以修改属性
- `NamedTuple` 是不可变的（和 tuple 一样）
- 推荐用 `dataclass`，需要不可变时加 `frozen=True`

### Q: 为什么 Python 没有接口（interface）？

Python 用"鸭子类型"——如果一个对象有 `chat()` 方法，它就可以当作 LLM 客户端用，不需要显式声明"我实现了某个接口"。

如果需要强制约束，可以用抽象基类（ABC）：

```python
from abc import ABC, abstractmethod

class BaseLLM(ABC):
    @abstractmethod
    def chat(self, messages: list) -> str:
        """子类必须实现此方法"""
        pass

# class MyLLM(BaseLLM):
#     pass
# MyLLM()  # ❌ TypeError: 没有实现抽象方法 chat

class MyLLM(BaseLLM):
    def chat(self, messages: list) -> str:
        return "实现了"
# MyLLM()  # ✅
```

### Q: __str__ 和 __repr__ 都要写吗？

- 只写一个的话，优先写 `__repr__`（print 找不到 `__str__` 时会退回使用 `__repr__`）
- 用 `dataclass` 会自动生成 `__repr__`，一般够用
- 只有需要用户可读输出时才单独写 `__str__`
