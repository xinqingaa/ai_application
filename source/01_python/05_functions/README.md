# 05. 函数 - 实践指南

> 本文档说明如何跟着 [学习文档](../../../docs/01_python/05_functions.md) 一步步动手操作

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
source/01_python/05_functions/
├── README.md                 ← 你正在读的这个文件
├── exercises.py              ← （已存在，暂不管）
├── function_basics.py        ← 第 1 步创建：文档第 2-4 章（函数定义、参数、作用域）
├── generators.py             ← 第 2 步创建：文档第 5 章（生成器）
├── type_annotations.py       ← 第 3 步创建：文档第 6 章（类型注解进阶）
└── higher_order.py           ← 第 4 步创建：文档第 7-8 章（高阶函数与装饰器）
```

---

## 一次性创建所有文件

如果想先把文件准备好再开始学：

```bash
touch source/01_python/05_functions/function_basics.py
touch source/01_python/05_functions/generators.py
touch source/01_python/05_functions/type_annotations.py
touch source/01_python/05_functions/higher_order.py
```

然后打开文档，从第 2 章开始。

---

## 第 1 步：函数定义、参数、作用域（文档第 2-4 章）

**新建文件**：`function_basics.py`

这三个章节是函数的基础知识，放在一起练习。

### 操作流程

1. 打开文档第 2 章，从 2.1 开始读

2. 新建 `function_basics.py`，照着文档把代码敲进去。建议按以下结构：

```python
# ========================================
# 2.1 基础定义
# ========================================

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
```

3. 读到 **2.2 文档字符串**，继续加：

```python
# ========================================
# 2.2 文档字符串（docstring）
# ========================================

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
```

> **交互提示**：运行 `help(calculate_bmi)` 时会进入**分页器**，底部显示 `(press h for help or q to quit)`，按 `q` 退出。按 `q` 后代码会继续执行 `print(calculate_bmi.__doc__)`。

如果想直接跳过交互，用 `print(calculate_bmi.__doc__)` 代替 `help()`。

也可以在终端直接查询（不需要写代码文件）：

```bash
python -c "help(list.append)"
python -c "print(list.__doc__)"
```

4. 读到 **第 3 章 参数类型**，从 3.1 开始，继续往下加：

```python
# ========================================
# 3.1 位置参数与关键字参数
# ========================================

def create_user(name: str, age: int, city: str) -> dict:
    return {"name": name, "age": age, "city": city}

print(create_user("张三", 25, "北京"))               # 位置参数
print(create_user(city="上海", name="李四", age=30))  # 关键字参数
print(create_user("王五", age=28, city="广州"))       # 混用
```

5. 读到 **3.2 默认参数**，注意文档里提到的"可变默认参数"陷阱：

```python
# ========================================
# 3.2 默认参数
# ========================================

def chat(message: str, model: str = "gpt-4o-mini", temperature: float = 0.7) -> str:
    return f"[{model}, temp={temperature}] 回复：收到 '{message}'"

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
```

6. 读到 **3.3 \*args 和 \*\*kwargs**，这是本节重点，参数分配规则要理解清楚：

```python
# ========================================
# 3.3 *args 和 **kwargs
# ========================================

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
```

**参数分配过程的可视化**：

```
传入的参数：
  "https://api.example.com" (位置) ──→ endpoint（匹配具名参数）
  "v1"                        (位置) ──→ *path_parts（不带名字的位置参数）
  "users"                     (位置) ──→ *path_parts
  limit="10"                  (关键字) ──→ **params（带名字的关键字参数）
  offset="0"                  (关键字) ──→ **params
  userId="20"                 (关键字) ──→ **params

最终结果：
  endpoint = "https://api.example.com"
  path_parts = ('v1', 'users')
  params = {'limit': '10', 'offset': '0', 'userId': '20'}
  返回: "https://api.example.com/v1/users?limit=10&offset=0&userId=20"
```

7. 读到 **3.4 仅位置参数和仅关键字参数**，了解即可：

```python
# ========================================
# 3.4 仅位置参数 / 仅关键字参数
# ========================================

def strict_func(pos_only: int, /, normal: int, *, kw_only: int) -> None:
    print(f"{pos_only}, {normal}, {kw_only}")

strict_func(1, 2, kw_only=3)        # ✅
strict_func(1, normal=2, kw_only=3) # ✅
# strict_func(pos_only=1, 2, 3)     # ❌ 试试看会报什么错
# strict_func(1, 2, 3)              # ❌ 试试看会报什么错
```

8. 读到 **第 4 章 作用域**：

```python
# ========================================
# 4.1 LEGB 规则
# ========================================

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

count = 0

def increment():
    global count
    count += 1

increment()
increment()
print("global count:", count)  # 2


# nonlocal
def make_counter():
    count = 0

    def increment():
        nonlocal count
        count += 1
        return count

    return increment

counter = make_counter()
print(counter())  # 1
print(counter())  # 2
print(counter())  # 3
```

9. 运行验证：

```bash
python source/01_python/05_functions/function_basics.py
```

---

## 第 2 步：生成器（文档第 5 章）

**新建文件**：`generators.py`

> 这章是 AI 应用最重要的前置知识之一，LLM 流式输出就基于生成器。

### 操作流程

1. 打开文档第 5 章，从 5.1 开始读

2. 新建 `generators.py`，照着文档敲代码：

```python
import time
import sys

# ========================================
# 5.1 什么是生成器
# ========================================

# 普通函数 vs 生成器函数
def get_numbers_list(n: int) -> list[int]:
    result = []
    for i in range(n):
        result.append(i)
    return result  # 一次性返回全部

def get_numbers_gen(n: int):
    for i in range(n):
        yield i  # 每次产出一个值

print("列表:", get_numbers_list(5))
print("生成器:", get_numbers_gen(5))       # 生成器对象
print("生成器转列表:", list(get_numbers_gen(5)))
```

3. 读到 **5.2 生成器的执行流程**，这节要重点理解 yield 的暂停/恢复机制：

```python
# ========================================
# 5.2 生成器的执行流程
# ========================================

def countdown(n: int):
    print(f"开始倒计时：{n}")
    while n > 0:
        yield n
        n -= 1
        print(f"继续：{n}")
    print("倒计时结束")

gen = countdown(3)
print(type(gen))  # <class 'generator'>

# 手动 next() 调用，理解暂停和恢复
print("--- 手动调用 next() ---")
print("产出:", next(gen))  # 开始倒计时：3 → 产出 3
print("产出:", next(gen))  # 继续：2 → 产出 2
print("产出:", next(gen))  # 继续：1 → 产出 1
# print(next(gen))         # 继续：0 + 倒计时结束 → StopIteration

# 用 for 循环（自动处理 StopIteration）
print("--- for 循环 ---")
for n in countdown(3):
    print(f"  {n}")
```

4. 读到 **5.3 生成器 vs 列表：内存优势**：

```python
# ========================================
# 5.3 生成器 vs 列表：内存优势
# ========================================

numbers_list = [i for i in range(1_000_000)]
print(f"列表占用内存: {sys.getsizeof(numbers_list)} 字节")

numbers_gen = (i for i in range(1_000_000))
print(f"生成器占用内存: {sys.getsizeof(numbers_gen)} 字节")
```

5. 读到 **5.4 模拟流式输出**，这是最核心的应用：

```python
# ========================================
# 5.4 模拟流式输出
# ========================================

def stream_response(text: str, delay: float = 0.05):
    """模拟 LLM 流式输出，逐字产出"""
    for char in text:
        yield char
        time.sleep(delay)

# 逐字打印（类似 ChatGPT 的效果）
print("--- 逐字流式输出 ---")
for char in stream_response("你好，我是 AI 助手。"):
    print(char, end="", flush=True)
print()


# 模拟 OpenAI 流式 API 的 chunk 格式
def stream_chat_response(text: str, chunk_size: int = 2):
    """模拟流式 API，按块产出"""
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i + chunk_size]
        yield {"type": "token", "content": chunk}
    yield {"type": "done", "content": ""}

print("--- 按 chunk 流式输出 ---")
for chunk in stream_chat_response("生成器是流式输出的基础。"):
    if chunk["type"] == "token":
        print(chunk["content"], end="", flush=True)
    elif chunk["type"] == "done":
        print("\n[完成]")
```

6. 读到 **5.5 yield from（委托生成器）**：

**`yield from` 是什么？**

简单说，`yield from X` 等价于 `for item in X: yield item`，但更简洁。

```python
# ========================================
# 5.5 yield from（委托生成器）
# ========================================

# 基础示例：合并多个生成器
def gen_a():
    yield 1
    yield 2

def gen_b():
    yield 3
    yield 4

# 方法 1：手动合并（需要写 for 循环）
def combined_manual():
    for item in gen_a():
        yield item
    for item in gen_b():
        yield item

# 方法 2：使用 yield from 简化（推荐）
def combined():
    yield from gen_a()
    yield from gen_b()

print("手动合并:", list(combined_manual()))  # [1, 2, 3, 4]
print("yield from:", list(combined()))       # [1, 2, 3, 4]

# 本质理解：yield from 是语法糖
# yield from gen_a() 等价于 for item in gen_a(): yield item
```

**`yield from` 的执行流程（图解）**：

```
调用 combined()
    ↓
执行 yield from gen_a()
    ↓
进入 gen_a()，开始迭代
    ↓
yield 1 ← 暂停，返回值 1 给 combined() 的调用者
    ↓ (调用者请求下一个值)
继续 gen_a()
    ↓
yield 2 ← 暂停，返回值 2 给 combined() 的调用者
    ↓ (调用者请求下一个值)
gen_a() 耗尽，返回到 combined()
    ↓
执行 yield from gen_b()
    ↓
进入 gen_b()，开始迭代
    ↓
yield 3 ← 暂停，返回值 3
    ↓ (调用者请求下一个值)
yield 4 ← 暂停，返回值 4
    ↓ (调用者请求下一个值)
gen_b() 耗尽，返回到 combined()
    ↓
combined() 结束
```

**实际场景一：模拟 LLM 多段流式输出**

```python
# 模拟 LLM API 返回多个 chunk
def stream_chunk_1():
    """第一段：问候语"""
    for char in "你好，":
        yield char

def stream_chunk_2():
    """第二段：正文"""
    for char in "我是 AI 助手。"
        yield char

def stream_chunk_3():
    """第三段：结束语"""
    for char in "有什么可以帮你的吗？"
        yield char

# 用 yield from 合并多个流
def full_stream():
    yield from stream_chunk_1()
    yield from stream_chunk_2()
    yield from stream_chunk_3()

# 使用
print("--- 多段流式输出 ---")
for char in full_stream():
    print(char, end="", flush=True)
print()
```

**实际场景二：分段读取文件（无需一次性加载到内存）**

```python
import os

# 创建测试文件
os.makedirs("temp_files", exist_ok=True)
with open("temp_files/file1.txt", "w") as f:
    f.write("文件 1 第一行\n文件 1 第二行\n")
with open("temp_files/file2.txt", "w") as f:
    f.write("文件 2 第一行\n文件 2 第二行\n")

def read_file_lines(file_path: str):
    """读取单个文件的每一行"""
    with open(file_path) as f:
        for line in f:
            yield line.strip()

def read_multiple_files(file_paths: list[str]):
    """读取多个文件，流式产出所有行"""
    for path in file_paths:
        yield from read_file_lines(path)

# 使用
print("--- 分段读取多个文件 ---")
files = ["temp_files/file1.txt", "temp_files/file2.txt"]
for line in read_multiple_files(files):
    print(f"  {line}")

# 清理测试文件
import shutil
shutil.rmtree("temp_files")
```

> **为什么 `yield from` 重要？**
> - 代码更简洁（少写 for 循环）
> - 性能更好（避免中间列表）
> - 语义更清晰（"委托"给另一个生成器）
> - AI 应用场景：合并多个 LLM 流、分段处理文档、链式工具调用

7. 读到 **5.6 异步生成器**，这节先了解，不用深究（后续异步章节会详细学）：

```python
# ========================================
# 5.6 异步生成器（预览，先了解）
# ========================================

import asyncio

async def async_stream(text: str, delay: float = 0.05):
    """异步生成器"""
    for char in text:
        yield char
        await asyncio.sleep(delay)

async def demo_async():
    async for char in async_stream("异步流式输出"):
        print(char, end="", flush=True)
    print()

# 运行异步生成器（取消注释即可运行）
# asyncio.run(demo_async())
print("异步生成器：先了解概念，后续异步章节会深入")
```

8. 运行验证：

```bash
python source/01_python/05_functions/generators.py
```

---

## 第 3 步：类型注解进阶（文档第 6 章）

**新建文件**：`type_annotations.py`

> 这章和 Pydantic、LangGraph、FastAPI 直接相关，在 AI 应用中极高频率使用。

### 操作流程

1. 打开文档第 6 章，从 6.1 开始读

2. 新建 `type_annotations.py`，照着文档敲代码：

```python
from typing import Optional, Union, Literal, TypedDict, Annotated, Any, Callable, TypeVar

# ========================================
# 6.1 Optional 和 Union
# ========================================

# Optional[X] 等价于 X | None
def find_user(user_id: int) -> Optional[dict]:
    users = {1: {"name": "张三"}, 2: {"name": "李四"}}
    return users.get(user_id)

print(find_user(1))    # {"name": "张三"}
print(find_user(99))   # None


# Union[X, Y]
def process_input(data: Union[str, list[str]]) -> list[str]:
    if isinstance(data, str):
        return [data]
    return data

print(process_input("hello"))         # ["hello"]
print(process_input(["a", "b"]))      # ["a", "b"]


# Python 3.10+ 简写
def process_input_modern(data: str | list[str]) -> list[str]:
    if isinstance(data, str):
        return [data]
    return data
```

3. 读到 **6.2 Literal**：

```python
# ========================================
# 6.2 Literal
# ========================================

def set_log_level(level: Literal["debug", "info", "warning", "error"]) -> None:
    print(f"日志级别设置为：{level}")

set_log_level("info")
set_log_level("debug")
# set_log_level("verbose")  # IDE 会提示类型错误，试试看


# AI 应用场景：限定模型名称
def chat(
    message: str,
    model: Literal["gpt-4o", "gpt-4o-mini", "claude-sonnet"] = "gpt-4o-mini"
) -> str:
    return f"[{model}] {message}"

print(chat("你好"))
print(chat("你好", model="claude-sonnet"))


# 限定角色类型
Role = Literal["system", "user", "assistant"]

def create_message(role: Role, content: str) -> dict:
    return {"role": role, "content": content}

print(create_message("system", "你是助手"))
print(create_message("user", "你好"))
```

4. 读到 **6.3 TypedDict**：

```python
# ========================================
# 6.3 TypedDict（类似 TypeScript 的 interface）
# ========================================

class ChatMessage(TypedDict):
    role: str
    content: str

class ChatRequest(TypedDict):
    messages: list[ChatMessage]
    model: str
    temperature: float

message: ChatMessage = {"role": "user", "content": "你好"}
request: ChatRequest = {
    "messages": [message],
    "model": "gpt-4o-mini",
    "temperature": 0.7,
}
print("ChatRequest:", request)
```

5. 读到 **6.4 Annotated**：

```python
# ========================================
# 6.4 Annotated
# ========================================

# 基础用法：添加描述
UserId = Annotated[int, "用户唯一标识"]
Username = Annotated[str, "用户名，2-20个字符"]

# 结合 Pydantic（需要安装 pydantic，如果没有安装先跳过运行）
# pip install pydantic
try:
    from pydantic import BaseModel, Field

    class User(BaseModel):
        name: Annotated[str, Field(min_length=2, max_length=20, description="用户名")]
        age: Annotated[int, Field(ge=0, le=150, description="年龄")]
        email: Annotated[str | None, Field(default=None, description="邮箱地址")]

    user = User(name="张三", age=25)
    print(f"Pydantic User: {user}")
except ImportError:
    print("pydantic 未安装，跳过 Pydantic 示例（后续安装后再试）")
```

6. 读到 **6.5 其他常用类型**：

```python
# ========================================
# 6.5 其他常用类型
# ========================================

# Any
def log(data: Any) -> None:
    print(data)

log("字符串")
log(123)
log([1, 2, 3])


# Callable
def apply_func(func: Callable[[int, int], int], a: int, b: int) -> int:
    return func(a, b)

print(apply_func(lambda a, b: a + b, 3, 5))  # 8


# TypeVar
T = TypeVar("T")

def first(items: list[T]) -> T | None:
    return items[0] if items else None

print(first([1, 2, 3]))        # 1
print(first(["a", "b", "c"]))  # "a"
print(first([]))                # None
```

7. 运行验证：

```bash
python source/01_python/05_functions/type_annotations.py
```

---

## 第 4 步：高阶函数与装饰器（文档第 7-8 章）

**新建文件**：`higher_order.py`

### 操作流程

1. 打开文档第 7 章，从 7.1 开始读

2. 新建 `higher_order.py`，照着文档敲代码：

```python
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
```

3. 读到 **7.2 lambda 表达式**：

```python
# ========================================
# 7.2 lambda 表达式
# ========================================

square = lambda x: x ** 2
print(square(5))  # 25

# 搭配排序
users = [
    {"name": "张三", "age": 25},
    {"name": "李四", "age": 30},
    {"name": "王五", "age": 20},
]

sorted_by_age = sorted(users, key=lambda u: u["age"])
print("按年龄排序:", sorted_by_age)

sorted_by_name_len = sorted(users, key=lambda u: len(u["name"]))
print("按名字长度排序:", sorted_by_name_len)
```

4. 读到 **7.3 map / filter / reduce**：

```python
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
squares_v2 = [x ** 2 for x in numbers]
evens_v2 = [x for x in numbers if x % 2 == 0]
print("列表推导式:", squares_v2, evens_v2)
```

5. 读到 **第 8 章 装饰器**，从 8.1 开始：

```python
# ========================================
# 8.1 什么是装饰器
# ========================================

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

print(slow_function())
```

6. 读到 **8.2 带参数的装饰器**：

```python
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
    import random
    if random.random() < 0.7:
        raise ConnectionError("连接失败")
    return "成功"

try:
    print(unreliable_api_call())
except ConnectionError:
    print("所有重试都失败了")
```

7. 读到 **8.3 functools.wraps**：

```python
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
```

8. 运行验证：

```bash
python source/01_python/05_functions/higher_order.py
```

---

## 需要手动创建的文件清单

本章**不需要提前准备任何数据文件**。只需要创建 4 个 `.py` 文件：

| 文件 | 对应文档章节 |
|-----|------------|
| `function_basics.py` | 第 2、3、4 章 |
| `generators.py` | 第 5 章 |
| `type_annotations.py` | 第 6 章 |
| `higher_order.py` | 第 7、8 章 |

---

## 学习顺序总结

| 顺序 | 文档章节 | 练习文件 | 核心内容 | 重要性 |
|-----|---------|---------|---------|-------|
| 1 | 第 2-4 章 | `function_basics.py` | 函数定义、参数类型、作用域 | 基础必会 |
| 2 | 第 5 章 | `generators.py` | yield、流式输出 | AI 应用核心 |
| 3 | 第 6 章 | `type_annotations.py` | Optional/Literal/TypedDict/Annotated | AI 应用核心 |
| 4 | 第 7-8 章 | `higher_order.py` | lambda、map/filter、装饰器 | 了解即可 |

---

## 注意事项

- **6.4 节 Pydantic 示例**需要安装 pydantic，如果没有安装，代码中已用 `try/except` 包裹，不会报错
- **5.6 节异步生成器**是预览内容，`asyncio.run()` 已注释掉，后续异步章节会深入学习
- **2.3 节 help() 分页器**：运行 `help(calculate_bmi)` 后会进入分页器，按 `q` 退出。也可以直接用 `print(calculate_bmi.__doc__)` 跳过交互
- **3.2 节可变默认参数**是个常见坑，一定要运行看看错误示范的输出
- **8.3 节 functools.wraps** 对比了用和不用 wraps 的区别，一定要运行看输出差异
