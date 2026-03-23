# 06. 类与面向对象 - 练习题
# 请在下方完成练习

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ============================================
# 练习 1：基础类 - Student
# ============================================

def exercise_1():
    """
    创建 Student 类：
    - 属性：name(str), age(int), scores(list[int])
    - 方法：
      - add_score(score): 添加成绩
      - get_average(): 返回平均分（没有成绩返回 0）
    - __str__ 方法：返回 "学生：张三，年龄：20，平均分：85.0"
    """

    class Student:
        pass  # TODO: 你的代码

    # 测试
    s = Student("张三", 20)
    print(s)  # 预期：学生：张三，年龄：20，平均分：0
    s.add_score(85)
    s.add_score(92)
    s.add_score(78)
    print(s)  # 预期：学生：张三，年龄：20，平均分：85.0
    print(f"平均分：{s.get_average()}")  # 预期：85.0


# ============================================
# 练习 2：类方法和静态方法
# ============================================

def exercise_2():
    """
    扩展 Student 类：
    - 类属性 student_count：记录创建了多少个学生
    - 类方法 get_count()：返回学生总数
    - 类方法 from_dict(data)：从字典创建学生 {"name": "张三", "age": 20}
    - 静态方法 is_adult(age)：判断是否成年（>=18）
    """

    class Student:
        student_count = 0

        def __init__(self, name: str, age: int):
            self.name = name
            self.age = age
            # TODO: 更新 student_count

        @classmethod
        def get_count(cls) -> int:
            pass  # TODO: 你的代码

        @classmethod
        def from_dict(cls, data: dict) -> "Student":
            pass  # TODO: 你的代码

        @staticmethod
        def is_adult(age: int) -> bool:
            pass  # TODO: 你的代码

    # 测试
    s1 = Student("张三", 20)
    s2 = Student("李四", 16)
    s3 = Student.from_dict({"name": "王五", "age": 25})

    print(f"学生总数：{Student.get_count()}")  # 预期：3
    print(f"张三成年？{Student.is_adult(s1.age)}")  # 预期：True
    print(f"李四成年？{Student.is_adult(s2.age)}")  # 预期：False
    print(f"从字典创建：{s3.name}, {s3.age}")  # 预期：王五, 25


# ============================================
# 练习 3：继承
# ============================================

def exercise_3():
    """
    1. 创建 Animal 基类：
       - 属性：name, sound
       - 方法：speak() → "name 说：sound"

    2. 创建 Dog(Animal)：
       - 新增属性：breed（品种）
       - sound 固定为 "汪汪"
       - 新增方法：fetch() → "name 去捡球了"

    3. 创建 Cat(Animal)：
       - sound 固定为 "喵喵"
       - 重写 speak() → "name 优雅地说：sound"
    """

    class Animal:
        pass  # TODO: 你的代码

    class Dog(Animal):
        pass  # TODO: 你的代码

    class Cat(Animal):
        pass  # TODO: 你的代码

    # 测试
    dog = Dog("旺财", "柴犬")
    cat = Cat("小咪")

    print(dog.speak())   # 预期：旺财 说：汪汪
    print(dog.fetch())   # 预期：旺财 去捡球了
    print(cat.speak())   # 预期：小咪 优雅地说：喵喵

    # 多态：统一调用 speak()
    animals = [dog, cat]
    for animal in animals:
        print(animal.speak())


# ============================================
# 练习 4：dataclass
# ============================================

def exercise_4():
    """
    1. 用 dataclass 创建 ChatMessage：
       - role: str（"system" / "user" / "assistant"）
       - content: str
       - timestamp: str（默认为当前时间 ISO 格式）

    2. 用 dataclass 创建 LLMConfig：
       - model: str = "gpt-4o-mini"
       - temperature: float = 0.7
       - max_tokens: int = 1000
       - stream: bool = False
       - extra_params: dict = {}（空字典）

    3. 用普通 class 实现同样的 LLMConfig，对比代码量
    """

    # TODO: 用 dataclass 实现 ChatMessage
    # @dataclass
    # class ChatMessage:
    #     ...

    # TODO: 用 dataclass 实现 LLMConfig
    # @dataclass
    # class LLMConfig:
    #     ...

    # TODO: 用普通 class 实现 LLMConfigOld（对比用）
    # class LLMConfigOld:
    #     def __init__(self, ...):
    #         ...
    #     def __repr__(self):
    #         ...
    #     def __eq__(self, other):
    #         ...

    # 测试 ChatMessage
    # msg = ChatMessage(role="user", content="你好")
    # print(msg)
    # print(f"timestamp 自动填充：{msg.timestamp}")

    # 测试 LLMConfig
    # config1 = LLMConfig()
    # print(f"默认配置：{config1}")
    #
    # config2 = LLMConfig(model="claude-sonnet", temperature=0)
    # print(f"自定义配置：{config2}")
    #
    # config3 = LLMConfig()
    # print(f"config1 == config3? {config1 == config3}")  # 预期：True

    print("请取消上方注释，完成 dataclass 实现后运行")


# ============================================
# 练习 5：私有属性和 property
# ============================================

def exercise_5():
    """
    创建 BankAccount 类：
    - 私有属性 __balance（初始余额）
    - property balance（只读）
    - 方法 deposit(amount)：存款（金额必须 > 0）
    - 方法 withdraw(amount)：取款（金额必须 > 0 且不超过余额）
    - 操作失败时打印错误信息而不是抛异常
    """

    class BankAccount:
        pass  # TODO: 你的代码

    # 测试
    acc = BankAccount("张三", 1000)
    print(f"户主：{acc.owner}")
    print(f"余额：{acc.balance}")       # 预期：1000

    acc.deposit(500)
    print(f"存款后余额：{acc.balance}")  # 预期：1500

    acc.withdraw(200)
    print(f"取款后余额：{acc.balance}")  # 预期：1300

    acc.withdraw(2000)                   # 预期：打印"余额不足"
    print(f"余额仍为：{acc.balance}")    # 预期：1300

    acc.deposit(-100)                    # 预期：打印"存款金额必须大于0"


# ============================================
# 练习 6：综合练习 - 购物车
# ============================================

def exercise_6():
    """
    实现购物车系统：

    1. Product 类（建议用 dataclass）：
       - name: str
       - price: float
       - __str__: "商品名 - ¥价格"

    2. Cart 类：
       - 属性：items（商品列表，每项包含商品和数量）
       - add(product, quantity=1)：添加商品
       - remove(product_name)：按名称删除商品
       - get_total()：计算总价
       - __str__：格式化输出购物车内容
       - __len__：返回商品种类数
    """

    # TODO: 实现 Product（建议 dataclass）

    # TODO: 实现 Cart

    # 测试
    # phone = Product("iPhone", 5999)
    # laptop = Product("MacBook", 9999)
    # earbuds = Product("AirPods", 1299)
    #
    # cart = Cart()
    # cart.add(phone, 1)
    # cart.add(laptop, 1)
    # cart.add(earbuds, 2)
    #
    # print(cart)
    # # 预期输出类似：
    # # 购物车（3 种商品）：
    # #   iPhone x1 = ¥5999.00
    # #   MacBook x1 = ¥9999.00
    # #   AirPods x2 = ¥2598.00
    # #   总计：¥18596.00
    #
    # print(f"商品种类：{len(cart)}")  # 预期：3
    # print(f"总价：¥{cart.get_total():.2f}")  # 预期：¥18596.00
    #
    # cart.remove("MacBook")
    # print(f"\n删除 MacBook 后：")
    # print(f"总价：¥{cart.get_total():.2f}")  # 预期：¥8597.00

    print("请取消上方注释，完成实现后运行")


# ============================================
# 练习 7：综合练习 - LLM 客户端抽象
# ============================================

def exercise_7():
    """
    实现一个简单的 LLM 客户端抽象：

    1. LLMConfig（dataclass）：
       - model: str
       - temperature: float = 0.7
       - max_tokens: int = 1000

    2. BaseLLMClient（基类）：
       - __init__(config: LLMConfig)
       - chat(message: str) -> str（抽象方法，raise NotImplementedError）
       - __str__：返回 "ClientName(model=xxx)"

    3. OpenAIClient(BaseLLMClient)：
       - chat()：返回 "[OpenAI/model] 回复：message"

    4. MockClient(BaseLLMClient)：
       - chat()：返回固定的 "这是模拟响应"
       - 用途：测试时不消耗 API 额度

    5. get_client(provider: str, config: LLMConfig) -> BaseLLMClient
       工厂函数：根据 provider 返回对应客户端
    """

    # TODO: 实现以上类和函数

    # 测试
    # config = LLMConfig(model="gpt-4o-mini")
    #
    # # 工厂模式
    # client = get_client("openai", config)
    # print(client)  # 预期：OpenAIClient(model=gpt-4o-mini)
    # print(client.chat("你好"))  # 预期：[OpenAI/gpt-4o-mini] 回复：你好
    #
    # mock = get_client("mock", config)
    # print(mock.chat("你好"))  # 预期：这是模拟响应
    #
    # # 多态
    # clients = [get_client("openai", config), get_client("mock", config)]
    # for c in clients:
    #     print(f"{c} → {c.chat('测试')}")

    print("请取消上方注释，完成实现后运行")


# ============================================
# 主程序
# ============================================

if __name__ == "__main__":
    exercises = {
        "1": ("基础类 - Student", exercise_1),
        "2": ("类方法和静态方法", exercise_2),
        "3": ("继承", exercise_3),
        "4": ("dataclass", exercise_4),
        "5": ("私有属性和 property", exercise_5),
        "6": ("综合：购物车", exercise_6),
        "7": ("综合：LLM 客户端抽象", exercise_7),
    }

    print("=" * 50)
    print("第 6 节：类与面向对象 - 练习题")
    print("=" * 50)

    while True:
        print("\n请选择练习（输入编号，q 退出）：")
        for num, (name, _) in exercises.items():
            print(f"  {num}. {name}")
        print(f"  a. 运行全部")

        choice = input("\n> ").strip().lower()

        if choice == "q":
            print("再见！")
            break
        elif choice == "a":
            for num, (name, func) in exercises.items():
                print(f"\n{'='*40}")
                print(f"练习 {num}：{name}")
                print(f"{'='*40}")
                func()
        elif choice in exercises:
            name, func = exercises[choice]
            print(f"\n{'='*40}")
            print(f"练习 {choice}：{name}")
            print(f"{'='*40}")
            func()
        else:
            print("无效输入，请重新选择")
