
# ========================================
# 2.1 什么是类
# ========================================

# 对照 JavaScript 理解：Python 的 class 和 JS 的 class 概念一样
# JS: constructor(name, age) { this.name = name; }
# Python: def __init__(self, name, age): self.name = name


# ========================================
# 2.2 __init__ 和 self
# ========================================
# - `__init__` 是构造函数（JS 中的 `constructor`）
# - `self` 是对当前实例的引用（JS 中的 `this`），**必须作为第一个参数显式写出**
# **关键区别**：JS 的 `this` 是隐式的，Python 的 `self` 是显式的。每个实例方法的第一个参数都必须是 `self`，调用时不需要手动传。

class User:
    def __init__(self, name: str, email: str, age: int = 0):
        self.name = name      # 实例属性
        self.email = email
        self.age = age

    def greet(self) -> str:
        return f"你好，我是 {self.name}，邮箱是 {self.email}"

    def is_adult(self) -> bool:
        return self.age >= 18


user1 = User("张三", "zhangsan@example.com", 25)
user2 = User("李四", "lisi@example.com")

print(user1.greet())     # "你好，我是 张三，邮箱是 zhangsan@example.com"
print(user1.is_adult())  # True
print(user2.age)         # 0（使用了默认值）


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

print(dog1.species)   # "犬科"（通过实例访问类属性）
print(Dog.species)    # "犬科"（通过类名访问类属性）
print(dog1.name)      # "旺财"（实例属性，每个对象不同）
print(Dog.count)      # 2（类属性，所有实例共享的计数器）



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

# ========================================
# 3.2 类方法（@classmethod）
# ========================================

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

print(user1.name, user1.email)
print(user2.name, user2.email)
print(user3.name, user3.email)


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