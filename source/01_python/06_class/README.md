# 06. 类与面向对象 - 实践指南

> 本文档说明如何跟着 [学习文档](../../../docs/01_python/06_class.md) 一步步动手操作

---

## 核心原则

```
读文档 → 新建文件 → 照着文档敲代码 → 运行看结果
```

- 所有操作在项目根目录 `/Users/linruiqiang/work/ai_application` 下进行
- 每个文档章节对应一个 `.py` 文件，跟着文档内容逐步填充
- 本章**不需要提前准备任何数据文件**，全部是纯 Python 代码

---

## 最终目录结构

完成所有练习后，本目录结构如下：

```
source/01_python/06_class/
├── README.md                        ← 你正在读的这个文件
├── exercises.py                     ← （已存在，暂不管）
├── class_basics.py                  ← 第 1 步创建：文档第 2-3 章（类基础、方法类型）
├── encapsulation_inheritance.py     ← 第 2 步创建：文档第 4-5 章（封装、继承）
└── dataclass_special.py             ← 第 3 步创建：文档第 6-7 章（dataclass、特殊方法）
```

---

## 一次性创建所有文件

```bash
touch source/01_python/06_class/class_basics.py
touch source/01_python/06_class/encapsulation_inheritance.py
touch source/01_python/06_class/dataclass_special.py
```

---

## 第 1 步：类基础与方法类型（文档第 2-3 章）

**新建文件**：`class_basics.py`

### 操作流程

1. 打开文档第 2 章，从 2.1 开始读

2. 新建 `class_basics.py`，照着文档敲代码。建议按以下结构：

```python
# ========================================
# 2.1 什么是类
# ========================================

# 对照 JavaScript / Dart 理解：
# - `__init__` 对应 constructor
# - `self` 对应 this


# ========================================
# 2.2 __init__ 和 self
# ========================================

class UserProfile:
    def __init__(self, name: str, email: str, age: int = 0):
        self.name = name      # 实例属性
        self.email = email
        self.age = age

    def greet(self) -> str:
        return f"你好，我是 {self.name}，邮箱是 {self.email}"

    def is_adult(self) -> bool:
        return self.age >= 18


user1 = UserProfile("张三", "zhangsan@example.com", 25)
user2 = UserProfile("李四", "lisi@example.com")

print(user1.greet())     # "你好，我是 张三，邮箱是 zhangsan@example.com"
print(user1.is_adult())  # True
print(user2.age)         # 0（使用了默认值）
```

3. 读到 **2.3 实例属性 vs 类属性**：

先记住一句话：

- Python 通常只有 2 种属性：实例属性、类属性
- 你在 JS / Dart 里说的"静态属性"，在 Python 里基本就对应"类属性"

```python
# ========================================
# 2.3 实例属性 vs 类属性
# ========================================

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

print(dog1.species)   # "犬科"
print(Dog.species)    # "犬科"
print(dog1.name)      # "旺财"（实例属性，每个对象不同）
print(Dog.count)      # 2（类属性，所有实例共享的计数器）

Dog.species = "犬科动物"
print(dog1.species)   # "犬科动物"
print(dog2.species)   # "犬科动物"

dog1.species = "家庭宠物"
print(dog1.species)   # "家庭宠物"
print(dog2.species)   # "犬科动物"
print(Dog.species)    # "犬科动物"
```

4. 读到 **第 3 章 方法类型**，从 3.1 实例方法开始：

```python
# ========================================
# 3.1 实例方法
# ========================================

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

5. 读到 **3.2 类方法 @classmethod**：

这一节要特别注意：`@classmethod` 不是简单等于 JS / Dart 的 `static`，它会自动拿到当前类 `cls`。

```python
# ========================================
# 3.2 类方法（@classmethod）
# ========================================

class Member:
    role = "member"

    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

    @classmethod
    def from_dict(cls, data: dict) -> "Member":
        return cls(data["name"], data["email"])


class Admin(Member):
    role = "admin"

member = Member.from_dict({"name": "李四", "email": "lisi@example.com"})
admin = Admin.from_dict({"name": "王五", "email": "wangwu@example.com"})

print(type(member).__name__, member.role)  # Member member
print(type(admin).__name__, admin.role)    # Admin admin
```

6. 读到 **3.3 静态方法 @staticmethod**：

这一节才最接近你熟悉的 `static method`。

```python
# ========================================
# 3.3 静态方法（@staticmethod）
# ========================================

class MathUtils:
    @staticmethod
    def is_even(n: int) -> bool:
        return n % 2 == 0

    @staticmethod
    def clamp(value: float, min_val: float, max_val: float) -> float:
        """将值限制在范围内"""
        return max(min_val, min(max_val, value))


print(MathUtils.is_even(4))        # True
print(MathUtils.clamp(1.5, 0, 1))  # 1.0
```

7. 读到 **3.4 三种方法对比**，照着敲一遍，加深理解：

```python
# ========================================
# 3.4 三种方法对比
# ========================================

class Demo:
    class_var = "我是类属性"

    def __init__(self, value: str):
        self.value = value

    def instance_method(self):
        """实例方法：主要处理实例自己的数据"""
        return f"实例方法 → self.value={self.value}, class_var={self.class_var}"

    @classmethod
    def class_method(cls):
        """类方法：能访问 cls，不能访问 self"""
        return f"类方法 → cls.class_var={cls.class_var}"

    @staticmethod
    def static_method():
        """静态方法：不能直接访问 self 和 cls"""
        return "静态方法 → 独立的工具函数"


d = Demo("测试")
print(d.instance_method())
print(Demo.class_method())
print(Demo.static_method())
```

8. 运行验证：

```bash
python source/01_python/06_class/class_basics.py
```

9. 跑完后用这句话复盘：

- 属性：2 种，实例属性 + 类属性
- 方法：3 种，实例方法 + 类方法 + 静态方法
- JS / Dart 里的静态属性/静态方法，在 Python 里通常对应类属性 / `@staticmethod`
- Python 多了一个常用的 `@classmethod`

---

## 第 2 步：封装与继承（文档第 4-5 章）

**新建文件**：`encapsulation_inheritance.py`

### 操作流程

1. 打开文档第 4 章，从 4.1 私有属性开始读

2. 新建 `encapsulation_inheritance.py`，照着文档敲：

```python
# ========================================
# 4.1 私有属性
# ========================================

class Account:
    def __init__(self, owner: str, balance: float):
        self.owner = owner          # 公开属性
        self._id = id(self)         # 约定私有（单下划线）
        self.__balance = balance    # 名称改写（双下划线）

    def get_balance(self) -> float:
        return self.__balance


acc = Account("张三", 1000)
print(acc.owner)          # ✅ "张三"
print(acc._id)            # ✅ 能访问（但约定不应该）
# print(acc.__balance)   # ❌ AttributeError，取消注释试试
print(acc.get_balance())  # ✅ 1000

# 双下划线只是被改写了名字（知道就行，不要这么用）
print(acc._Account__balance)  # 1000
```

3. 读到 **4.2 @property 装饰器**：

```python
# ========================================
# 4.2 @property 装饰器
# ========================================

# 先看你更熟悉的普通 getter / setter 写法
class TemperatureWithMethods:
    def __init__(self, celsius: float):
        self._celsius = celsius

    def get_celsius(self) -> float:
        return self._celsius

    def set_celsius(self, value: float) -> None:
        if value < -273.15:
            raise ValueError("温度不能低于绝对零度")
        self._celsius = value


temp_methods = TemperatureWithMethods(100)
print(temp_methods.get_celsius())  # 100
temp_methods.set_celsius(37)
print(temp_methods.get_celsius())  # 37

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
print(temp.celsius)      # 100（像属性一样访问）
print(temp.fahrenheit)   # 212.0
temp.celsius = 37        # 调用了 setter
print(temp.celsius)      # 37
# temp.celsius(1000)     # TypeError: 'int' object is not callable
# temp.celsius = -300    # ValueError，取消注释试试
```

这一节要特别注意，你现在的困惑点很正常：

- 这里不是"属性和方法随便同名"
- 而是 `@property` 把 `celsius()` 这个函数包装成了一个属性对象
- 后面的 `@celsius.setter` 是继续给这个属性对象补上 setter

你可以把它理解成 JS / Dart 的 getter / setter：

```javascript
class Temperature {
  get celsius() {
    return this._celsius;
  }

  set celsius(value) {
    this._celsius = value;
  }
}
```

所以 Python 里：

- `print(temp.celsius)` 看起来像读属性，实际上底层会调用 getter
- `temp.celsius = 37` 看起来像赋值，实际上底层会调用 setter

也就是说，**使用方式是属性，底层逻辑是方法**。

如果你更习惯传统 getter/setter，可以先把它近似理解成：

```python
class Temperature:
    def get_celsius(self):
        return self._celsius

    def set_celsius(self, value):
        if value < -273.15:
            raise ValueError("温度不能低于绝对零度")
        self._celsius = value

    celsius = property(get_celsius)
    celsius = celsius.setter(set_celsius)
```

两种方式直接对比：

- 普通方法风格读取：`temp_methods.get_celsius()`
- 普通方法风格写入：`temp_methods.set_celsius(37)`
- `@property` 风格读取：`temp.celsius`
- `@property` 风格写入：`temp.celsius = 37`
- `temp.celsius(1000)` 不成立，因为 `temp.celsius` 先返回的是数值，不是函数

记忆重点：

- `@property` 定义"读"的逻辑
- `@xxx.setter` 定义"写"的逻辑
- 两个函数名字必须一样，因为它们描述的是同一个属性 `celsius`

4. 读到 **第 5 章 继承**，从 5.1 基础继承开始：

```python
# ========================================
# 5.1 基础继承
# ========================================

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

    def info(self) -> str:              # 方法重写
        return f"狗：{self.name}（{self.breed}）"

    def fetch(self) -> str:             # 新增方法
        return f"{self.name} 去捡球了"


dog = Dog("旺财", "柴犬")
print(dog.speak())  # "旺财 说：汪汪"（继承的方法）
print(dog.info())   # "狗：旺财（柴犬）"（重写的方法）
print(dog.fetch())  # "旺财 去捡球了"（新方法）
```

5. 读到 **5.2 实际应用：自定义异常**：

```python
# ========================================
# 5.2 自定义异常
# ========================================
# 继承关系：
# NotFoundError -> AppError -> Exception
# AuthError     -> AppError -> Exception

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
    # 调用链：
    # NotFoundError.__init__
    # -> AppError.__init__
    # -> Exception.__init__
    raise NotFoundError("用户 #123")
except AppError as e:
    # 为什么能被 except AppError 接住？
    # 因为 NotFoundError 是 AppError 的子类
    print(f"错误 [{e.code}]: {e}")

try:
    raise AuthError()
except AppError as e:
    print(f"错误 [{e.code}]: {e}")
```

这里建议你顺着这个图理解：

```text
raise NotFoundError("用户 #123")
        |
        v
NotFoundError.__init__
        |
        v
AppError.__init__
        |
        v
Exception.__init__
        |
        v
异常对象被抛出
        |
        v
except AppError as e 负责捕获
        |
        v
e.code -> 404
str(e) -> "用户 #123 不存在"
```

记忆重点：

- `raise XxxError(...)` 会先创建异常对象
- 子类 `__init__` 里通常会 `super()` 调父类
- `except 父类异常` 可以捕获子类异常
- `e.code` 是你自己加的属性，`e` 的文本来自异常 message

6. 读到 **5.3 实际应用：LLM 客户端抽象**，这是一个很好的 AI 应用示例：

```python
# ========================================
# 5.3 LLM 客户端抽象（多态示例）
# ========================================

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
        return f"[OpenAI/{self.model}] 模拟响应"


class ClaudeClient(BaseLLMClient):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        super().__init__(api_key, model)

    def chat(self, messages: list[dict]) -> str:
        return f"[Claude/{self.model}] 模拟响应"


# 统一接口，不关心具体是哪个客户端
def get_response(client: BaseLLMClient, question: str) -> str:
    messages = [{"role": "user", "content": question}]
    return client.chat(messages)


openai_client = OpenAIClient("sk-xxx")
claude_client = ClaudeClient("sk-xxx")

print(get_response(openai_client, "你好"))
print(get_response(claude_client, "你好"))
```

7. 运行验证：

```bash
python source/01_python/06_class/encapsulation_inheritance.py
```

---

## 第 3 步：dataclass 与特殊方法（文档第 6-7 章）

**新建文件**：`dataclass_special.py`

> dataclass 在 AI 应用中非常常用（配置对象、中间数据结构等）。

### 操作流程

1. 打开文档第 6 章，从 6.1 开始读

2. 新建 `dataclass_special.py`，照着文档敲：

```python
from dataclasses import dataclass, field, asdict
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
```

3. 读到 **6.2 默认值与 field()**：

这一节先记住一句话：

- `str`、`int`、`float`、`bool` 这类简单默认值可以直接写
- `list`、`dict`、`set` 这类可变对象不要直接写默认值，要用 `field(default_factory=...)`

```python
# ========================================
# 6.2 默认值与 field()
# ========================================

# 和函数默认参数一样，可变默认值会出问题
def append_tag_bad(tag: str, tags: list[str] = []):
    tags.append(tag)
    return tags


print("函数默认参数第一次:", append_tag_bad("python"))   # ['python']
print("函数默认参数第二次:", append_tag_bad("dataclass"))  # ['python', 'dataclass']

# 上面就说明：默认 list 会被复用，所以第二次不是一个“全新的空列表”

@dataclass
class ChatMessage:
    role: str
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict = field(default_factory=dict)  # 可变默认值必须用 field()


msg = ChatMessage(role="user", content="你好")
print(msg)

msg1 = ChatMessage(role="user", content="第一条")
msg2 = ChatMessage(role="assistant", content="第二条")
msg1.metadata["source"] = "chat"

print(msg1.metadata)  # {'source': 'chat'}
print(msg2.metadata)  # {}
print(id(msg1.metadata) == id(msg2.metadata))  # False


@dataclass
class LLMConfig:
    # 这些是简单类型默认值，可以直接写
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 1000
    stream: bool = False


# 使用默认值
config1 = LLMConfig()
print("默认配置:", config1)

# 覆盖部分默认值
config2 = LLMConfig(model="claude-sonnet", temperature=0)
print("自定义配置:", config2)
```

为什么简单类型通常可以直接写，而 `list` / `dict` 不行？

- `model = "gpt-4o-mini"`、`temperature = 0.7` 这种值不会在原地被修改
- 但 `metadata = {}`、`items = []` 这种对象可以被 `append`、`update`、赋值修改
- 一旦默认对象被多个实例共享，就会出现“我改了自己的，别人也变了”的问题

所以：

- 简单默认值：直接写
- 可变默认值：`field(default_factory=list)` / `field(default_factory=dict)`

4. 读到 **6.3 不可变 dataclass**：

```python
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
```

5. 读到 **6.4 dataclass vs 普通 class vs Pydantic**，这节有 Pydantic 的示例。如果没安装 Pydantic 可以先跳过运行，只看代码理解区别：

```python
# ========================================
# 6.4 dataclass vs Pydantic 对比
# ========================================

# asdict() 是 dataclasses 模块提供的函数
# 它会把 dataclass 实例转成普通 dict
# 常见场景：打印配置、转 JSON、传给需要 dict 的函数
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
        # ge=0 表示必须 >= 0
        # le=2 表示必须 <= 2
        temperature: float = Field(default=0.7, ge=0, le=2)

    # Pydantic 会验证
    pd_ok = ConfigPD(temperature=0.5)
    print(f"Pydantic 验证通过: {pd_ok}")

    # pd_err = ConfigPD(temperature=999)  # ❌ ValidationError，取消注释试试
except ImportError:
    print("pydantic 未安装，跳过对比示例（后续安装后再试）")
```

这里要补两个理解点：

1. `asdict(config)` 是什么？

- 它不是 `config.asdict()`
- 它是 `dataclasses` 模块里的函数
- 输入一个 dataclass 实例，输出一个普通 `dict`

你可以把它理解成：

- dataclass 适合在 Python 代码里当对象用
- `asdict()` 适合在你要打印、序列化、传参时把它转回字典

2. Pydantic 是怎么验证的？

- `ConfigPD(temperature=0.5)` 创建对象时，Pydantic 会先读取字段定义
- 看到 `temperature: float = Field(default=0.7, ge=0, le=2)`
- 就知道这个字段必须满足：`>= 0` 且 `<= 2`
- `0.5` 合法，所以对象创建成功
- 如果传 `999`，就不满足 `le=2`，Pydantic 会直接抛 `ValidationError`

可以把调用链理解成：

```text
ConfigPD(temperature=0.5)
        |
        v
读取字段定义
        |
        v
读取 Field(ge=0, le=2) 规则
        |
        v
检查 0.5 是否在 [0, 2] 范围内
        |
        v
合法 -> 创建成功
```

6. 读到 **第 7 章 特殊方法**：

```python
# ========================================
# 7.1 常用特殊方法
# ========================================

# 这是完整手写版，目的是演示每个特殊方法分别怎么工作

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
print(repr(counter))         # __repr__ → TokenCounter(model='gpt-4o-mini')
print(len(counter))          # __len__ → 2
print(100 in counter)        # __contains__ → True


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

print(counter_dc)           # __str__：自己写
print(repr(counter_dc))     # __repr__：dataclass 自动生成
print(len(counter_dc))      # __len__：自己写
print(250 in counter_dc)    # __contains__：自己写
```

这里要补两个理解点：

1. dataclass 能不能把这些都自动生成？

- 不能全部生成
- dataclass 常帮你省掉的是：`__init__`、`__repr__`、`__eq__`
- 但 `__len__`、`__contains__`、业务方法 `add()` 这类行为逻辑，还是要自己写

所以这段 `TokenCounter` 的手写版更像“教学版完整样板代码”，目的是让你看到每个特殊方法分别对应什么行为。

2. 为什么方法名叫 `__repr__`，但调用写成 `repr(counter)`？

- 因为 `repr` 是 Python 内置函数
- 它内部会去调用对象的 `__repr__()`

你可以这样记：

- `print(counter)` -> `str(counter)` -> `counter.__str__()`
- `repr(counter)` -> `counter.__repr__()`
- `len(counter)` -> `counter.__len__()`
- `100 in counter` -> `counter.__contains__(100)`

7. 文档 9 章常见问题中还有一个 **抽象基类 ABC** 的示例，也值得敲一遍：

```python
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
```

8. 运行验证：

```bash
python source/01_python/06_class/dataclass_special.py
```

---

## 需要手动创建的文件清单

本章**不需要提前准备任何数据文件**。只需要创建 3 个 `.py` 文件：

| 文件 | 对应文档章节 |
|-----|------------|
| `class_basics.py` | 第 2、3 章 |
| `encapsulation_inheritance.py` | 第 4、5 章 |
| `dataclass_special.py` | 第 6、7 章 |

---

## 学习顺序总结

| 顺序 | 文档章节 | 练习文件 | 核心内容 | 重要性 |
|-----|---------|---------|---------|-------|
| 1 | 第 2-3 章 | `class_basics.py` | __init__/self、实例/类属性、三种方法类型 | 基础必会 |
| 2 | 第 4-5 章 | `encapsulation_inheritance.py` | 私有属性、@property、继承、自定义异常、多态 | 基础必会 |
| 3 | 第 6-7 章 | `dataclass_special.py` | dataclass、field()、frozen、特殊方法 | AI 应用核心 |

---

## 注意事项

- **6.4 节 Pydantic 对比**需要安装 pydantic（`pip install pydantic`），代码中已用 `try/except` 包裹，未安装也不会报错
- **4.1 节私有属性**中的 `__balance` 访问报错是正常的，取消注释体会一下区别
- **4.2 节 @property setter** 的温度验证，取消注释 `temp.celsius = -300` 看看报错效果
- **5.3 节 LLM 客户端**是多态的典型应用，后续封装统一 LLM 客户端时会用到这个模式
