import time
from functools import reduce, wraps
from typing import Callable

# ========================================
# 7.1 函数作为参数
# ========================================

def apply_to_list(func: Callable[[int], int], numbers: list[int]) -> list[int]:
    return [func(n) for n in numbers]

def double(x: int) -> int:
    return x * 2

print(apply_to_list(double, [1, 2, 3]))  # [2, 4, 6]


# ========================================
# 7.2 lambda 表达式
# ========================================

# lambda 是匿名函数（JS 的箭头函数）
square = lambda x: x ** 2
print(square(5))  # 25

# 搭配排序
users = [
    {"name": "张三", "age": 25},
    {"name": "李四", "age": 30},
    {"name": "王五", "age": 20},
]

# 按 age 排序
sorted_by_age = sorted(users, key=lambda u: u["age"])
print("按年龄排序:", sorted_by_age)

# 按 name 长度排序
sorted_by_name_len = sorted(users, key=lambda u: len(u["name"]))
print("按名字长度排序:", sorted_by_name_len)

# ========================================
# 7.3 map / filter / reduce
# ========================================

numbers = [1, 2, 3, 4, 5]

# map
squares = list(map(lambda x: x ** 2, numbers))
print("map:", squares)  # [1, 4, 9, 16, 25]

# filter
evens = list(filter(lambda x: x % 2 == 0, numbers))
print("filter:", evens)  # [2, 4]

# reduce
total = reduce(lambda acc, x: acc + x, numbers)
print("reduce:", total)  # 15

# 对比：Python 更推荐列表推导式
# 推荐
squares_v2 = [x ** 2 for x in numbers]
evens_v2 = [x for x in numbers if x % 2 == 0]
print("列表推导式:", f"实现map: {squares_v2}" ,f"实现filter: {evens_v2}" )


# ========================================
# 8.1 什么是装饰器
# ========================================

# 装饰器是一个"包装"函数的函数，在**不修改原函数代码**的情况下给它添加额外功能。

def timer(func):
    """计时装饰器"""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"{func.__name__} 执行耗时：{elapsed:.4f}s")
        return result
    return wrapper

@timer
def slow_function():
    time.sleep(1)
    return "完成"

print(slow_function()) # 输出：slow_function 执行耗时：1.0012s

# ========================================
# 8.2 带参数的装饰器
# ========================================

def retry(max_attempts: int = 3):
    """重试装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"第 {attempt} 次尝试失败：{e}")
                    if attempt == max_attempts:
                        raise
        return wrapper
    return decorator


@retry(max_attempts=3)
def unreliable_api_call():
    """模拟不稳定的 API 调用"""
    import random
    if random.random() < 0.7:
        raise ConnectionError("连接失败")
    return "成功"

try:
    print(unreliable_api_call())
except ConnectionError:
    print("所有重试都失败了")


# ========================================
# 8.3 functools.wraps
# ========================================

# 不用 @wraps
def timer_no_wrap(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"耗时：{time.time() - start:.4f}s")
        return result
    return wrapper

@timer_no_wrap
def func_a():
    """func_a 的文档"""
    pass

print("不使用 wraps:")
print(f"  __name__: {func_a.__name__}")  # "wrapper"（丢失了原函数名）
print(f"  __doc__: {func_a.__doc__}")     # None（丢失了文档）


# 使用 @wraps（推荐）
def timer_with_wrap(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"耗时：{time.time() - start:.4f}s")
        return result
    return wrapper

@timer_with_wrap
def func_b():
    """func_b 的文档"""
    pass

print("使用 wraps:")
print(f"  __name__: {func_b.__name__}")  # "func_b"（保留了原函数名）
print(f"  __doc__: {func_b.__doc__}")     # "func_b 的文档"（保留了文档）