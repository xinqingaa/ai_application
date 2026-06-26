
# ========================================
# 2.1 基础定义
# ========================================
print("==================2.1 基础定义=================")

# 基础函数
def greet(name: str) -> str:
    return f"你好，{name}！"

result = greet("张三")
print(result)  # "你好，张三！"


# 多返回值（实际返回元组）
def divide(a: float, b: float) -> tuple[float, int]:
    quotient = a // b
    remainder = a % b
    return quotient, remainder

q, r = divide(10, 3)
print(q, r)  # 3.0 1.0


# 无返回值
def log_message(message: str) -> None:
    print(f"[LOG] {message}")

log_message("测试日志")

# ========================================
# 2.2 文档字符串（docstring）
# ========================================

print("==================2.2 文档字符串=================")

def calculate_bmi(weight: float, height: float) -> float:
    """
    计算 BMI 指数。

    Args:
        weight: 体重（公斤）
        height: 身高（米）

    Returns:
        BMI 值

    Raises:
        ValueError: 体重或身高为非正数时
    """
    if weight <= 0 or height <= 0:
        raise ValueError("体重和身高必须为正数")
    return weight / (height ** 2)

print(calculate_bmi(70, 1.75))

# 查看文档
# help(calculate_bmi) # 终端出现黑框
"""
  ┌───────────────────┬──────────────────────────────────┐                                                                                                                                                       
  │       按键        │               作用               │  
  ├───────────────────┼──────────────────────────────────┤
  │ q                 │ 退出（最常用），退出帮助回到代码 │
  ├───────────────────┼──────────────────────────────────┤
  │ h                 │ 显示所有快捷键帮助               │                                                                                                                                                       
  ├───────────────────┼──────────────────────────────────┤
  │ 空格键 / PageDown │ 下一页                           │                                                                                                                                                       
  ├───────────────────┼──────────────────────────────────┤                                                                                                                                                       
  │ b / PageUp        │ 上一页                           │
  ├───────────────────┼──────────────────────────────────┤                                                                                                                                                       
  │ 上/下箭头         │ 上一行 / 下一行                  │  
  ├───────────────────┼──────────────────────────────────┤                                                                                                                                                       
  │ /                 │ 搜索（输入关键词后回车）         │
  ├───────────────────┼──────────────────────────────────┤                                                                                                                                                       
  │ n                 │ 搜索结果下一个匹配               │  
  └───────────────────┴──────────────────────────────────┘ 
"""
print(calculate_bmi.__doc__)

# ========================================
# 3.1 位置参数与关键字参数
# ========================================
print("==================3.1 位置参数与关键字参数=================")
def create_user(name: str, age: int, city: str) -> dict:
    return {"name": name, "age": age, "city": city}

print(create_user("张三", 25, "北京"))               # 位置参数
print(create_user(city="上海", name="李四", age=30))  # 关键字参数
print(create_user("王五", age=28, city="广州"))       # 混用

# ========================================
# 3.2 默认参数
# ========================================

print("==================3.2 默认参数=================")

def chat(message: str, model: str = "gpt-4o-mini", temperature: float = 0.7) -> str:
    return f"{model}, temp={temperature} 回复：收到 '{message}'"

print(chat("你好"))                                    # 用默认值
print(chat("你好", temperature=0))                     # 只覆盖一个
print(chat("你好", model="claude-sonnet", temperature=0.5))  # 全部覆盖


# ❌ 错误示范：可变默认参数
def add_item_wrong(item: str, items: list = []) -> list:
    items.append(item)
    return items

print(add_item_wrong("a"))  # ["a"]
print(add_item_wrong("b"))  # ["a", "b"] ← 不是 ["b"]！共享了同一个列表


# ✅ 正确写法：用 None
def add_item(item: str, items: list | None = None) -> list:
    if items is None:
        items = []
    items.append(item)
    return items

print(add_item("a"))  # ["a"]
print(add_item("b"))  # ["b"] ← 正确


# ========================================
# 3.3 *args 和 **kwargs
# ========================================
print("==================3.3 *args 和 **kwargs=================")
# - * 的作用：收集多余的位置参数（打包成元组）                                                                                                                                                                   
# - ** 的作用：收集多余的关键字参数（打包成字典）
# - args / kwargs 只是名字，不是关键字，换成什么都行，真正起作用的是 * 和 **  
# *args：任意数量位置参数（不带名字的参数）
def sum_all(*args: float) -> float:
    print(f"args 类型: {type(args)}")  # tuple
    print(f"args 内容: {args}")
    return sum(args)

print(sum_all(1, 2, 3))        # 6
print(sum_all(1, 2, 3, 4, 5))  # 15


# **kwargs：任意数量关键字参数（带名字的参数）
def print_info(**kwargs: str) -> None:
    print(f"kwargs 类型: {type(kwargs)}")  # dict
    print(f"kwargs 内容: {kwargs}")
    for key, value in kwargs.items():
        print(f"  {key}: {value}")

print_info(name="张三", age="25", city="北京")


# 组合使用：完整演示参数分配规则
def api_call(endpoint: str, *path_parts: str, **params: str) -> str:
    # endpoint: 第一个具名参数
    # path_parts: 剩余位置参数（不带名字）→ 元组
    # params: 剩余关键字参数（带名字）→ 字典
    print(f"endpoint = {endpoint}")
    print(f"path_parts = {path_parts}  (类型: {type(path_parts)})")
    print(f"params = {params}  (类型: {type(params)})")
    path = "/".join(path_parts)
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{endpoint}/{path}?{query}"

# 调用时传入 5 个参数，但 endpoint 只有 1 个
# Python 分配规则：
#   1. "https://api.example.com" → endpoint
#   2. "v1", "users" → *path_parts（位置参数）
#   3. limit="10", offset="0", userId="20" → **params（关键字参数）
print(api_call(
    "https://api.example.com",  # → endpoint
    "v1",                        # → *path_parts
    "users",                     # → *path_parts
    limit="10",                  # → **params
    offset="0",                  # → **params
    userId="20"                  # → **params
))


# ========================================
# 4.1 LEGB 规则
# ========================================
print("==================4.1 LEGB 规则=================")
x = "global"

def outer():
    x = "enclosing"

    def inner():
        x = "local"
        print("inner:", x)  # "local"

    inner()
    print("outer:", x)      # "enclosing"

outer()
print("global:", x)         # "global"


# ========================================
# 4.2 global 和 nonlocal
# ========================================
print("==================4.2 global 和 nonlocal=================")
count = 0

def increment():
    global count # 声明使用全局变量
    count += 1

increment()
increment()
print("global count:", count)  # 2


# nonlocal
def make_counter():
    count = 0

    def increment():
        nonlocal count # nonlocal：修改外层函数的变量
        count += 1
        return count

    return increment

counter = make_counter()
print(counter())  # 1
print(counter())  # 2
print(counter())  # 3