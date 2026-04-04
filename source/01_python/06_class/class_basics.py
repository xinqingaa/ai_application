# ========================================
# 2.1 什么是类
# ========================================

# 对照 JavaScript / Dart 理解：
# - Python 的 class 也是对象模板
# - `__init__` 对应 JS 的 `constructor`
# - `self` 对应 JS / Dart 里的 `this`


# ========================================
# 2.2 __init__ 和 self
# ========================================
# - `__init__` 是初始化方法，实例创建后会自动调用
# - `self` 是当前实例本身，必须作为实例方法的第一个参数显式写出
# - JS / Dart 的 `this` 是隐式可用的，Python 的 `self` 需要手动写


class UserProfile:
    def __init__(self, name: str, email: str, age: int = 0):
        self.name = name  # 实例属性
        self.email = email
        self.age = age

    def greet(self) -> str:
        return f"你好，我是 {self.name}，邮箱是 {self.email}"

    def is_adult(self) -> bool:
        return self.age >= 18


user1 = UserProfile("张三", "zhangsan@example.com", 25)
user2 = UserProfile("李四", "lisi@example.com")

print(user1.greet())     # 你好，我是 张三，邮箱是 zhangsan@example.com
print(user1.is_adult())  # True
print(user2.age)         # 0（使用了默认值）


# ========================================
# 2.3 实例属性 vs 类属性
# ========================================
# 先记住一句话：
# - Python 里通常只有 2 种属性：实例属性、类属性
# - 你在 JS / Dart 里理解的“静态属性”，在 Python 里基本就对应“类属性”
# - Python 没有 `static name = ...` 这种关键字写法，而是直接写在 class 代码块里


class Dog:
    # 类属性：所有实例共享
    species = "犬科"
    count = 0

    def __init__(self, name: str, breed: str):
        # 实例属性：每个实例独立
        self.name = name
        self.breed = breed
        Dog.count += 1


dog1 = Dog("旺财", "柴犬")
dog2 = Dog("小黑", "拉布拉多")

print(dog1.species)  # 犬科
print(Dog.species)   # 犬科
print(dog1.name)     # 旺财
print(Dog.count)     # 2

# 修改类属性：所有没被覆盖的实例都会看到新值
Dog.species = "犬科动物"
print(dog1.species)  # 犬科动物
print(dog2.species)  # 犬科动物

# 通过实例赋值，不会修改类属性，而是给这个实例单独创建同名实例属性
dog1.species = "家庭宠物"
print(dog1.species)  # 家庭宠物（实例属性，屏蔽了类属性）
print(dog2.species)  # 犬科动物
print(Dog.species)   # 犬科动物


# ========================================
# 2.4 和 JS / Dart 的对应关系
# ========================================
# | JS / Dart 叫法 | Python 对应 | 常见写法 |
# | -------------- | ----------- | -------- |
# | 实例属性       | 实例属性    | `self.name = ...` |
# | 静态属性       | 类属性      | 直接写在 class 内 |
# | 实例方法       | 实例方法    | `def run(self): ...` |
# | 静态方法       | 静态方法    | `@staticmethod` |
# | 无明显同名概念 | 类方法      | `@classmethod` |


# ========================================
# 3.1 实例方法
# ========================================
# 默认定义的方法就是实例方法
# - 第一个参数是 `self`
# - 主要处理“某个对象自己的数据”


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
print(calc.get_history())  # ['3 + 5 = 8', '10 + 20 = 30']


# ========================================
# 3.2 类方法（@classmethod）
# ========================================
# `@classmethod` 更像“绑定到类本身的方法”
# - 第一个参数是 `cls`
# - 常用于替代构造函数
# - 和 JS / Dart 的 static 最像，但它比 static 更强，因为它能拿到当前类


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


# ========================================
# 3.3 静态方法（@staticmethod）
# ========================================
# `@staticmethod` 才最接近你在 JS / Dart 里理解的 static method
# - 不需要 `self`
# - 不需要 `cls`
# - 只是逻辑上放在类里面的工具函数


class MathUtils:
    @staticmethod
    def is_even(n: int) -> bool:
        return n % 2 == 0

    @staticmethod
    def clamp(value: float, min_val: float, max_val: float) -> float:
        return max(min_val, min(max_val, value))


print(MathUtils.is_even(4))        # True
print(MathUtils.clamp(1.5, 0, 1))  # 1


# ========================================
# 3.4 三种方法对比
# ========================================


class Demo:
    class_var = "我是类属性"

    def __init__(self, value: str):
        self.value = value

    def instance_method(self) -> str:
        return f"实例方法 → self.value={self.value}, class_var={self.class_var}"

    @classmethod
    def class_method(cls) -> str:
        return f"类方法 → cls.class_var={cls.class_var}"

    @staticmethod
    def static_method() -> str:
        return "静态方法 → 不依赖 self，也不依赖 cls"


d = Demo("测试")
print(d.instance_method())
print(Demo.class_method())
print(Demo.static_method())

# 速记：
# - 属性：2 种，实例属性 + 类属性
# - 方法：3 种，实例方法 + 类方法 + 静态方法
# - 你在 JS / Dart 里说的“静态属性/静态方法”
#   在 Python 里通常对应“类属性/@staticmethod”
# - Python 多出来一个很常用的 `@classmethod`
