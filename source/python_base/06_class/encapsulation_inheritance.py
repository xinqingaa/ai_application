# ========================================
# 4.1 私有属性（没有真正的私有属性 private ）
# ========================================

class Account:
    def __init__(self, owner: str, balance: float):
        self.owner = owner          # 公开属性
        self._id = id(self)         # 约定私有（单下划线）
        self.__balance = balance    # 名称改写，但不是真正的私有属性（双下划线）

    def get_balance(self) -> float:
        return self.__balance


acc = Account("张三", 1000)
print(acc.owner)          # ✅ "张三"
print(acc._id)            # ✅ 能访问（但约定不应该）
# print(acc.__balance)   # ❌ AttributeError，取消注释试试
print(acc.get_balance())  # ✅ 1000

# 双下划线只是被改写了名字（知道就行，不要这么用，__真正的作用是内部修改了名字）
print(acc._Account__balance)  # 1000 （能访问，但强烈不推荐）


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

# `@property` 让方法像属性一样访问，常用于只读属性或需要验证的属性：
# 这里不是"属性和方法随便同名"
# 而是 @property 把 celsius() 这个函数包装成了一个属性对象
# 后面的 @celsius.setter 是继续给这个属性对象补上 setter
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

# 对比：
# - 普通方法风格：temp_methods.set_celsius(37)
# - @property 风格：temp.celsius = 37
# - 读取时也是一样：
#   temp_methods.get_celsius()
#   temp.celsius


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

# ========================================
# 5.2 自定义异常
# ========================================
# 继承关系：
# NotFoundError -> AppError -> Exception
# AuthError     -> AppError -> Exception

# raise XxxError(...) 会先创建异常对象
# 子类 __init__ 里通常会 super() 调父类
# except 父类异常 可以捕获子类异常
# e.code 是你自己加的属性，e 的文本来自异常 message

# 调用链路（以 raise NotFoundError("用户 #123") 为例）：
# 1. 先创建异常对象，进入 NotFoundError.__init__
# 2. NotFoundError.__init__ 里调用 super()，进入 AppError.__init__
# 3. AppError.__init__ 再调用 Exception.__init__ 保存错误消息
# 4. raise 把这个异常对象抛出去
# 5. except AppError as e 能接住它，因为 NotFoundError 是 AppError 的子类
# 6. e.code 读取自定义错误码，str(e) 读取异常消息

class AppError(Exception):
    """应用基础异常"""
    def __init__(self, message: str, code: int = 500):
        # 交给内置异常类保存 message，这样 str(e) 才能拿到错误文本
        super().__init__(message)
        # 再额外挂上业务错误码
        self.code = code


class NotFoundError(AppError):
    """资源不存在"""
    def __init__(self, resource: str):
        # 继续调用父类初始化逻辑，统一设置 message 和 code
        super().__init__(f"{resource} 不存在", code=404)


class AuthError(AppError):
    """认证失败"""
    def __init__(self, message: str = "认证失败"):
        super().__init__(message, code=401)


# 使用
try:
    # raise NotFoundError(...) 相当于：
    # NotFoundError.__init__ -> AppError.__init__ -> Exception.__init__
    raise NotFoundError("用户 #123")
except AppError as e:
    # except AppError 能接住子类异常
    # e.code 来自 AppError.__init__
    # e 的文本来自 Exception.__init__ 里保存的 message
    print(f"错误 [{e.code}]: {e}")

try:
    raise AuthError()
except AppError as e:
    print(f"错误 [{e.code}]: {e}")


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


openai_client = OpenAIClient("sk-xxx" , model="gpt-5.4")
claude_client = ClaudeClient("sk-xxx" , model="ops-4.6")

print(get_response(openai_client, "你好"))
print(get_response(claude_client, "你好"))

