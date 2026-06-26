# 05. 函数 - 练习题
# 请在下方完成练习

import time
import sys
from typing import Optional, Literal, TypedDict, Annotated, Union, Callable
from functools import reduce


# ============================================
# 练习 1：基础函数
# ============================================

def exercise_1():
    """基础函数练习"""

    # 1.1 实现 calculate_bmi 函数
    # 参数：weight(体重，公斤), height(身高，米)
    # 返回：(bmi值, 等级字符串)
    # 等级：<18.5 偏瘦, 18.5-24 正常, 24-28 偏胖, >=28 肥胖
    def calculate_bmi(weight: float, height: float) -> tuple[float, str]:
        pass  # TODO: 你的代码

    # 测试
    bmi, level = calculate_bmi(70, 1.75)
    print(f"BMI: {bmi:.1f}, 等级: {level}")
    # 预期：BMI: 22.9, 等级: 正常

    bmi, level = calculate_bmi(90, 1.70)
    print(f"BMI: {bmi:.1f}, 等级: {level}")
    # 预期：BMI: 31.1, 等级: 肥胖

    # 1.2 实现 is_prime 函数
    # 参数：n(正整数)
    # 返回：是否为质数
    def is_prime(n: int) -> bool:
        pass  # TODO: 你的代码

    # 测试
    test_numbers = [1, 2, 3, 4, 5, 17, 20, 97]
    for n in test_numbers:
        print(f"{n} {'是' if is_prime(n) else '不是'}质数")
    # 预期：1不是, 2是, 3是, 4不是, 5是, 17是, 20不是, 97是


# ============================================
# 练习 2：参数类型
# ============================================

def exercise_2():
    """参数类型练习"""

    # 2.1 实现 greet 函数
    # 支持自定义问候语和重复次数
    def greet(name: str, greeting: str = "你好", times: int = 1) -> None:
        pass  # TODO: 你的代码

    # 测试
    greet("张三")                          # 预期：你好，张三！
    greet("李四", greeting="早上好")       # 预期：早上好，李四！
    greet("王五", times=3)                 # 预期：打印 3 次"你好，王五！"

    print("---")

    # 2.2 实现 sum_all 函数（使用 *args）
    def sum_all(*args: float) -> float:
        pass  # TODO: 你的代码

    # 测试
    print(f"sum_all(1, 2, 3) = {sum_all(1, 2, 3)}")          # 预期：6
    print(f"sum_all(10, 20, 30, 40) = {sum_all(10, 20, 30, 40)}")  # 预期：100

    print("---")

    # 2.3 实现 build_profile 函数（使用 **kwargs）
    # 接收 name(必填) 和任意数量的额外信息
    # 返回包含所有信息的字典
    def build_profile(name: str, **kwargs) -> dict:
        pass  # TODO: 你的代码

    # 测试
    profile = build_profile("张三", age=25, city="北京", job="工程师")
    print(profile)
    # 预期：{"name": "张三", "age": 25, "city": "北京", "job": "工程师"}


# ============================================
# 练习 3：生成器
# ============================================

def exercise_3():
    """生成器练习"""

    # 3.1 实现 fibonacci 生成器
    # 逐个产出前 n 个斐波那契数：0, 1, 1, 2, 3, 5, 8, ...
    def fibonacci(n: int):
        pass  # TODO: 你的代码（使用 yield）

    # 测试
    print("斐波那契数列（前10个）：")
    print(list(fibonacci(10)))
    # 预期：[0, 1, 1, 2, 3, 5, 8, 13, 21, 34]

    print("---")

    # 3.2 实现 stream_text 生成器
    # 逐字产出文本，模拟流式输出
    def stream_text(text: str):
        pass  # TODO: 你的代码（使用 yield，每次产出一个字符）

    # 测试
    print("流式输出：", end="")
    for char in stream_text("Hello, AI!"):
        print(char, end="", flush=True)
        time.sleep(0.05)
    print()

    print("---")

    # 3.3 实现 chunk_list 生成器
    # 将列表按指定大小分块产出
    # chunk_list([1,2,3,4,5,6,7], 3) → [1,2,3], [4,5,6], [7]
    def chunk_list(items: list, chunk_size: int):
        pass  # TODO: 你的代码（使用 yield）

    # 测试
    data = list(range(1, 11))
    print(f"原始数据：{data}")
    print("按 3 个一组分块：")
    for chunk in chunk_list(data, 3):
        print(f"  {chunk}")
    # 预期：[1,2,3], [4,5,6], [7,8,9], [10]

    print("---")

    # 3.4 对比内存占用
    # 分别用列表和生成器创建 100 万个数的平方
    list_squares = [x ** 2 for x in range(1_000_000)]
    gen_squares = (x ** 2 for x in range(1_000_000))

    print(f"列表占用内存：{sys.getsizeof(list_squares):,} bytes")
    print(f"生成器占用内存：{sys.getsizeof(gen_squares):,} bytes")


# ============================================
# 练习 4：类型注解进阶
# ============================================

def exercise_4():
    """类型注解进阶练习"""

    # 4.1 使用 Optional 和 Literal
    # 实现 search 函数：在列表中搜索，返回匹配项或 None
    def search(
        items: list[str],
        keyword: str,
        mode: Literal["exact", "contains"] = "contains"
    ) -> Optional[list[str]]:
        """
        搜索函数
        - mode="exact"：精确匹配
        - mode="contains"：包含匹配
        - 无结果时返回 None
        """
        pass  # TODO: 你的代码

    # 测试
    fruits = ["apple", "banana", "cherry", "apricot", "blueberry"]
    print(f"contains 'ap': {search(fruits, 'ap', 'contains')}")
    # 预期：["apple", "apricot"]
    print(f"exact 'banana': {search(fruits, 'banana', 'exact')}")
    # 预期：["banana"]
    print(f"contains 'xyz': {search(fruits, 'xyz', 'contains')}")
    # 预期：None

    print("---")

    # 4.2 使用 TypedDict
    # 定义 ChatMessage 和 ChatRequest 类型
    class ChatMessage(TypedDict):
        role: Literal["system", "user", "assistant"]
        content: str

    class ChatRequest(TypedDict):
        messages: list[ChatMessage]
        model: str
        temperature: float

    # 创建一个符合类型的请求对象
    request: ChatRequest = None  # TODO: 创建一个包含 system 和 user 消息的请求

    # 测试
    if request:
        print(f"模型：{request['model']}")
        print(f"消息数量：{len(request['messages'])}")
        for msg in request["messages"]:
            print(f"  [{msg['role']}] {msg['content']}")

    print("---")

    # 4.3 使用 Callable 类型
    # 实现 apply_transform 函数
    # 接收一个转换函数和一个字符串列表，对每个字符串应用转换
    def apply_transform(
        transform: Callable[[str], str],
        items: list[str]
    ) -> list[str]:
        pass  # TODO: 你的代码

    # 测试
    words = ["hello", "world", "python"]
    print(f"大写：{apply_transform(str.upper, words)}")
    # 预期：["HELLO", "WORLD", "PYTHON"]
    print(f"首字母大写：{apply_transform(str.capitalize, words)}")
    # 预期：["Hello", "World", "Python"]
    print(f"加前缀：{apply_transform(lambda s: f'[AI] {s}', words)}")
    # 预期：["[AI] hello", "[AI] world", "[AI] python"]


# ============================================
# 练习 5：高阶函数
# ============================================

def exercise_5():
    """高阶函数练习"""
    numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    # 5.1 使用 map：将每个数平方
    squares = None  # TODO: 使用 map + lambda

    # 5.2 使用 filter：筛选奇数
    odds = None  # TODO: 使用 filter + lambda

    # 5.3 使用 reduce：计算所有数的乘积
    product = None  # TODO: 使用 reduce + lambda

    # 5.4 使用列表推导式重新实现 5.1 和 5.2（推荐写法）
    squares_v2 = None  # TODO: 列表推导式
    odds_v2 = None     # TODO: 列表推导式

    print(f"平方（map）：{squares}")
    print(f"奇数（filter）：{odds}")
    print(f"乘积（reduce）：{product}")
    print(f"平方（推导式）：{squares_v2}")
    print(f"奇数（推导式）：{odds_v2}")

    print("---")

    # 5.5 排序练习
    students = [
        {"name": "张三", "score": 85, "age": 20},
        {"name": "李四", "score": 92, "age": 22},
        {"name": "王五", "score": 78, "age": 19},
        {"name": "赵六", "score": 92, "age": 21},
    ]

    # 按分数降序排列
    by_score = None  # TODO: sorted + lambda

    # 按分数降序，分数相同按年龄升序
    by_score_age = None  # TODO: sorted + lambda (提示：key 可返回元组)

    print("按分数降序：")
    if by_score:
        for s in by_score:
            print(f"  {s['name']}: {s['score']}")

    print("按分数降序 + 年龄升序：")
    if by_score_age:
        for s in by_score_age:
            print(f"  {s['name']}: 分数={s['score']}, 年龄={s['age']}")


# ============================================
# 练习 6：装饰器
# ============================================

def exercise_6():
    """装饰器练习"""

    # 6.1 实现计时装饰器 timer
    # 打印函数名和执行时间
    def timer(func):
        pass  # TODO: 你的代码

    # 测试
    @timer
    def slow_add(a: int, b: int) -> int:
        time.sleep(0.1)
        return a + b

    result = slow_add(3, 5)
    print(f"结果：{result}")
    # 预期：slow_add 执行耗时：0.10xxs
    #       结果：8

    print("---")

    # 6.2 实现日志装饰器 log_call
    # 在函数调用前打印参数，调用后打印返回值
    def log_call(func):
        pass  # TODO: 你的代码

    @log_call
    def add(a: int, b: int) -> int:
        return a + b

    @log_call
    def greet(name: str) -> str:
        return f"你好，{name}"

    add(3, 5)
    # 预期：调用 add(args=(3, 5), kwargs={})
    #       add 返回：8

    greet(name="张三")
    # 预期：调用 greet(args=(), kwargs={'name': '张三'})
    #       greet 返回：你好，张三


# ============================================
# 练习 7：综合练习 - 模拟流式 LLM 响应
# ============================================

def exercise_7():
    """
    综合练习：模拟一个简单的流式 LLM 响应系统

    要求：
    1. 实现 stream_llm_response 生成器，逐块产出响应
    2. 每个 chunk 是一个字典：{"type": "token"|"done", "content": str}
    3. 实现 collect_stream 函数，收集流式输出的完整文本
    4. 实现 timer 装饰器，统计流式输出总耗时
    """

    # 实现 stream_llm_response 生成器
    def stream_llm_response(
        prompt: str,
        model: Literal["fast", "slow"] = "fast"
    ):
        """
        模拟 LLM 流式响应

        - model="fast"：每 0.02s 产出一个字符
        - model="slow"：每 0.05s 产出一个字符
        - 响应内容：f"收到问题：{prompt}。这是模拟回答。"
        - 最后产出 {"type": "done", "content": ""} 表示完成
        """
        pass  # TODO: 你的代码

    # 实现 collect_stream 函数
    def collect_stream(stream) -> str:
        """收集流式输出的全部 token，拼接为完整字符串"""
        pass  # TODO: 你的代码

    # 测试流式输出
    print("=== 流式输出测试 ===")
    print("输出：", end="")
    for chunk in stream_llm_response("什么是生成器？", model="fast"):
        if chunk["type"] == "token":
            print(chunk["content"], end="", flush=True)
    print()

    # 测试收集完整响应
    print("\n=== 收集完整响应 ===")
    full_text = collect_stream(stream_llm_response("什么是生成器？"))
    print(f"完整响应：{full_text}")
    print(f"响应长度：{len(full_text)} 字符")


# ============================================
# 主程序
# ============================================

if __name__ == "__main__":
    exercises = {
        "1": ("基础函数", exercise_1),
        "2": ("参数类型", exercise_2),
        "3": ("生成器", exercise_3),
        "4": ("类型注解进阶", exercise_4),
        "5": ("高阶函数", exercise_5),
        "6": ("装饰器", exercise_6),
        "7": ("综合练习：流式 LLM 响应", exercise_7),
    }

    print("=" * 50)
    print("第 5 节：函数 - 练习题")
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
