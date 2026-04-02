# 05. 函数

> 本节目标：掌握函数定义、参数类型、生成器、类型注解进阶、高阶函数和装饰器

---

## 1. 概述

### 学习目标

- 掌握函数定义和多种参数类型
- 理解作用域规则
- 掌握生成器（yield）的使用和原理
- 掌握 typing 模块的进阶类型注解
- 了解高阶函数和 lambda 表达式
- 了解装饰器的基本用法

### 预计学习时间

- 函数定义与参数：1 小时
- 生成器：1 小时
- 类型注解进阶：1-1.5 小时
- 高阶函数与装饰器：1 小时
- 练习：1-2 小时

### 本节在 AI 应用中的重要性

| 场景 | 相关知识 |
|-----|---------|
| LLM 流式输出 | 生成器（yield）是流式响应的基础 |
| Pydantic 模型定义 | 类型注解进阶（Optional, Literal, Annotated） |
| LangGraph 状态定义 | TypedDict |
| Function Calling Schema | 类型注解 → 自动生成参数描述 |
| FastAPI 路由函数 | 函数参数、类型注解、装饰器 |
| LangChain Tool 定义 | @tool 装饰器、参数 Schema |

---

## 2. 函数定义 📌

> `def` 是 **define（定义）** 的缩写，是 Python 中声明函数的关键字。相当于 JavaScript 中的 `function` 关键字。Python 中所有函数都用 `def` 开头，没有其他声明方式（匿名函数用 `lambda`，但那不是完整的函数定义）。

### 2.1 基础定义

```python
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
```

### 2.2 文档字符串（docstring）

```python
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
```

### 2.3 查看文档：`help()` 和 `__doc__`

Python 提供了两种方式查看函数（或其他对象）的文档：

```python
# 在代码中直接使用
help(calculate_bmi)            # 输出：格式化后的完整帮助文档
print(calculate_bmi.__doc__)  # 输出：原始文档字符串

# 也可以在终端直接查询（不用写代码文件）
python3 -c "help(list.append)"
python3 -c "print(list.__doc__)"
```

**两者的区别**

| | `help()` | `__doc__` |
|--|---------|-----------|
| 输出 | 格式化后的完整帮助文档 | 原始文档字符串 |
| 能查什么 | 函数、类、模块、变量都行 | 任何有 `__doc__` 属性的对象 |
| 实际用途 | 交互式探索 API | 代码中读取文档（如自动生成文档） |

**进入交互式解释器查看**

在终端输入 `python3` 进入交互模式：

```bash
$ python3
Python 3.13.3 (main, ...)
[GCC ...] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> def calculate_bmi(weight: float, height: float) -> float:
...     """计算 BMI 指数。"""
...     return weight / (height ** 2)
...
>>> help(calculate_bmi)
Help on function calculate_bmi in module __main__:

calculate_bmi(weight: float, height: float) -> float
    计算 BMI 指数。

>>> print(calculate_bmi.__doc__)
计算 BMI 指数。
>>> exit()
```

**AI 应用开发中的实际用途**

- 调试时快速查某个函数怎么用：`help(requests.get)`
- `__doc__` 用于构建 Prompt 模板（动态注入文档）
- 养成写 docstring 的习惯，AI 工具（如 Cursor）能识别并给出更好的代码补全

> **AI 应用关联**：LangChain 的 `@tool` 装饰器会读取 docstring 作为工具描述传递给 LLM，描述质量直接影响 LLM 能否正确选择和调用工具。

### 2.4 与 JavaScript 对比

| 概念 | JavaScript | Python |
|-----|-----------|--------|
| 定义 | `function add(a, b) {}` | `def add(a, b):` |
| 箭头函数 | `const add = (a, b) => a + b` | `add = lambda a, b: a + b` |
| 默认参数 | `function f(x = 1) {}` | `def f(x=1):` |
| 剩余参数 | `function f(...args) {}` | `def f(*args):` |
| 返回值 | `return` | `return`（无 return 则返回 None） |
| 多返回值 | 返回对象/数组 | 直接 `return a, b`（元组解包） |

---

## 3. 参数类型 📌

### 3.1 位置参数与关键字参数

```python
def create_user(name: str, age: int, city: str) -> dict:
    return {"name": name, "age": age, "city": city}


# 位置参数：按顺序传
create_user("张三", 25, "北京")

# 关键字参数：按名称传（顺序无关）
create_user(city="上海", name="李四", age=30)

# 混用：位置参数必须在关键字参数前面
create_user("王五", age=28, city="广州")
```

### 3.2 默认参数

```python
def chat(message: str, model: str = "gpt-4o-mini", temperature: float = 0.7) -> str:
    """模拟 LLM API 调用"""
    return f"[{model}, temp={temperature}] 回复：收到 '{message}'"


# 使用默认值
chat("你好")

# 覆盖部分默认值
chat("你好", temperature=0)

# 覆盖全部默认值
chat("你好", model="claude-sonnet", temperature=0.5)
```

> **注意**：默认参数不要用可变对象（list、dict），这是 Python 常见的坑。

```python
# ❌ 错误：默认值是可变对象，所有调用共享同一个列表
def add_item(item: str, items: list = []) -> list:
    items.append(item)
    return items

print(add_item("a"))  # ["a"]
print(add_item("b"))  # ["a", "b"] — 不是 ["b"]！

# ✅ 正确：用 None 作为默认值
def add_item(item: str, items: list | None = None) -> list:
    if items is None:
        items = []
    items.append(item)
    return items
```

### 3.3 *args 和 **kwargs

`*args` 和 `**kwargs` 是 Python 用来**接收任意数量参数**的语法。

**关键理解**：区分的不是"数据类型"，而是**传参方式**。

| 语法 | 收集什么 | 传参时的样子 |
|------|---------|------------|
| `*args` | **位置参数**（不带名字的参数） | `func(1, 2, 3)` → args = `(1, 2, 3)` |
| `**kwargs` | **关键字参数**（带名字的参数） | `func(a=1, b=2)` → kwargs = `{"a": 1, "b": 2}` |

#### *args：接收任意数量的位置参数

```python
def sum_all(*args: float) -> float:
    """args 是一个元组"""
    print(type(args))  # <class 'tuple'>
    print(args)        # (1, 2, 3)
    return sum(args)

sum_all(1, 2, 3)       # 6
sum_all(1, 2, 3, 4, 5) # 15
```

#### **kwargs：接收任意数量的关键字参数

```python
def print_info(**kwargs: str) -> None:
    """kwargs 是一个字典"""
    print(type(kwargs))  # <class 'dict'>
    print(kwargs)        # {'name': '张三', 'age': '25'}
    for key, value in kwargs.items():
        print(f"{key}: {value}")

print_info(name="张三", age="25", city="北京")
```

#### 组合使用：完整图解

这是你选中的代码，逐参数拆解：

```python
def api_call(endpoint: str, *path_parts: str, **params: str) -> str:
    print(path_parts)  # ('v1', 'users')
    print(params)       # {'limit': '10', 'offset': '0', 'userId': '20'}
    path = "/".join(path_parts)
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{endpoint}/{path}?{query}"
```

调用：

```python
api_call(
    "https://api.example.com",  # 位置参数 → endpoint
    "v1",                        # 位置参数 → *path_parts
    "users",                     # 位置参数 → *path_parts
    limit="10",                  # 关键字参数 → **params
    offset="0",                  # 关键字参数 → **params
    userId="20"                  # 关键字参数 → **params
)
```

**Python 的分配规则**：

1. 先按名字匹配**具名参数**（`endpoint`）
2. 剩下的**不带名字的参数**全部归 `*path_parts`
3. 剩下的**带名字的参数**全部归 `**params`

```
传入的参数：
  "https://api.example.com" (位置) → endpoint
  "v1" (位置) → *path_parts
  "users" (位置) → *path_parts
  limit="10" (关键字) → **params
  offset="0" (关键字) → **params
  userId="20" (关键字) → **params
```

所以 `endpoint="https://api.example.com"`，`path_parts=("v1", "users")`，`params={"limit": "10", "offset": "0", "userId": "20"}`，最终返回：

```
https://api.example.com/v1/users?limit=10&offset=0&userId=20
```

> **注意**：类型注解 `*args: str` 只是提示，不强制限制。`"v1"` 是字符串所以没问题，但如果传 `1`（整数），Python 不会报错，只是类型检查器会提示。

#### AI 应用场景

很多 LLM SDK 的方法都用 `**kwargs` 传递可选参数：

```python
# OpenAI SDK 内部大量使用 **kwargs
response = client.chat.completions.create(
    model="gpt-4o-mini",      # 具名参数
    messages=[...],            # 具名参数
    temperature=0.7,           # → **params
    max_tokens=1000,           # → **params
    stream=True,               # → **params
)
```

> 理解了这个，你再看 SDK 源码就明白：那些不在函数签名里显式列出来的参数，都是通过 `**kwargs` 接收的。

### 3.4 仅位置参数和仅关键字参数

```python
# / 前面的参数只能按位置传
# * 后面的参数只能按关键字传
def strict_func(pos_only: int, /, normal: int, *, kw_only: int) -> None:
    print(f"{pos_only}, {normal}, {kw_only}")

strict_func(1, 2, kw_only=3)       # ✅
strict_func(1, normal=2, kw_only=3) # ✅
# strict_func(pos_only=1, normal=2, kw_only=3)  # ❌ pos_only 是仅位置参数
# strict_func(1, 2, 3)                           # ❌ kw_only 是仅关键字参数
```

> 日常开发中不常自己写，但阅读 SDK 源码时会遇到。了解即可。

---

## 4. 作用域 ⚡

### 4.1 LEGB 规则

Python 查找变量的顺序：Local → Enclosing → Global → Built-in

```python
x = "global"

def outer():
    x = "enclosing"

    def inner():
        x = "local"
        print(x)  # "local"

    inner()
    print(x)      # "enclosing"

outer()
print(x)          # "global"
```

### 4.2 global 和 nonlocal

```python
count = 0

def increment():
    global count  # 声明使用全局变量
    count += 1

increment()
print(count)  # 1


# nonlocal：修改外层函数的变量
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
```

> **实际开发中**：尽量避免使用 `global`，通过参数传递和返回值来传递数据更清晰。`nonlocal` 偶尔在闭包中使用。

---

## 5. 生成器 📌 🔗

> 这是本节最重要的新概念之一，直接关联 AI 应用中的流式输出。

### 5.1 什么是生成器

生成器是一种特殊的函数，使用 `yield` 而不是 `return` 返回值。它不会一次性计算所有结果，而是**按需逐个产出**。

```python
# 普通函数：一次性返回所有结果
def get_numbers_list(n: int) -> list[int]:
    result = []
    for i in range(n):
        result.append(i)
    return result  # 一次性返回全部

# 生成器函数：逐个产出结果
def get_numbers_gen(n: int):
    for i in range(n):
        yield i  # 每次产出一个值，暂停执行，下次从这里继续
```

### 5.2 生成器的执行流程

```python
def countdown(n: int):
    print(f"开始倒计时：{n}")
    while n > 0:
        yield n          # 产出值，暂停
        n -= 1
        print(f"继续：{n}")
    print("倒计时结束")


gen = countdown(3)
print(type(gen))  # <class 'generator'>

# 每次 next() 执行到下一个 yield
print(next(gen))  # 打印"开始倒计时：3"，产出 3
print(next(gen))  # 打印"继续：2"，产出 2
print(next(gen))  # 打印"继续：1"，产出 1
# next(gen)       # 打印"继续：0"和"倒计时结束"，然后 StopIteration


# 通常用 for 循环遍历（自动处理 StopIteration）
for n in countdown(3):
    print(f"  {n}")
```

### 5.3 生成器 vs 列表：内存优势

```python
import sys

# 列表：全部在内存中
numbers_list = [i for i in range(1_000_000)]
print(sys.getsizeof(numbers_list))  # 约 8 MB

# 生成器：几乎不占内存
numbers_gen = (i for i in range(1_000_000))
print(sys.getsizeof(numbers_gen))   # 约 200 字节
```

### 5.4 实际应用：模拟流式输出

这是生成器在 AI 应用中最核心的用法——**流式输出**：

```python
import time


def stream_response(text: str, delay: float = 0.05):
    """模拟 LLM 流式输出，逐字产出"""
    for char in text:
        yield char
        time.sleep(delay)


# 使用：逐字打印（类似 ChatGPT 的效果）
for char in stream_response("你好，我是 AI 助手。"):
    print(char, end="", flush=True)
print()  # 换行


# 进阶：模拟 OpenAI 流式 API 的 chunk 格式
def stream_chat_response(text: str, chunk_size: int = 2):
    """模拟流式 API，按块产出"""
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i + chunk_size]
        yield {"type": "token", "content": chunk}
    yield {"type": "done", "content": ""}


for chunk in stream_chat_response("生成器是流式输出的基础。"):
    if chunk["type"] == "token":
        print(chunk["content"], end="", flush=True)
    elif chunk["type"] == "done":
        print("\n[完成]")
```

### 5.5 yield from（委托生成器）

`yield from` 是语法糖，让代码更简洁。

**基础语法**

```python
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
# yield from gen_a() 等价于 for item in gen_a(): yield item
def combined():
    yield from gen_a()
    yield from gen_b()

list(combined())  # [1, 2, 3, 4]
```

**`yield from` 的执行流程（图解）**

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
    for char in "我是 AI 助手。":
        yield char

def stream_chunk_3():
    """第三段：结束语"""
    for char in "有什么可以帮你的吗？":
        yield char

# 用 yield from 合并多个流
def full_stream():
    yield from stream_chunk_1()
    yield from stream_chunk_2()
    yield from stream_chunk_3()

# 使用
for char in full_stream():
    print(char, end="", flush=True)
# 输出：你好，我是 AI 助手。有什么可以帮你的吗？
```

**实际场景二：分段读取文件（无需一次性加载到内存）**

```python
import os

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
files = ["file1.txt", "file2.txt"]
for line in read_multiple_files(files):
    print(line)  # 逐行输出两个文件的所有内容
```

> **为什么 `yield from` 重要？**
> - 代码更简洁（少写 for 循环）
> - 性能更好（避免中间列表）
> - 语义更清晰（"委托"给另一个生成器）
> - AI 应用场景：合并多个 LLM 流、分段处理文档、链式工具调用

### 5.6 异步生成器（预览）

后续在异步编程和 FastAPI 流式响应中会深入使用：

```python
import asyncio


async def async_stream(text: str, delay: float = 0.05):
    """异步生成器：AI 应用流式输出的实际形式"""
    for char in text:
        yield char
        await asyncio.sleep(delay)


# 使用 async for 遍历
async def main():
    async for char in async_stream("异步流式输出"):
        print(char, end="", flush=True)
    print()

# asyncio.run(main())
```

> **记住**：后续学习中，OpenAI SDK 的 `stream=True`、FastAPI 的 `StreamingResponse`、LangChain 的 `.stream()` 底层都依赖生成器机制。

### 5.7 与 JavaScript 对比

| 概念 | JavaScript | Python |
|-----|-----------|--------|
| 生成器函数 | `function* gen() {}` | `def gen():` |
| 产出值 | `yield value` | `yield value` |
| 委托 | `yield* other()` | `yield from other()` |
| 异步生成器 | `async function* gen() {}` | `async def gen():` + `yield` |
| 遍历 | `for (const x of gen())` | `for x in gen():` |

---

## 6. 类型注解进阶 📌 🔗

> 这部分在 AI 应用开发中非常高频，Pydantic、LangGraph、FastAPI 都重度依赖。

### 6.1 Optional 和 Union

```python
from typing import Optional, Union


# Optional[X] 等价于 X | None
def find_user(user_id: int) -> Optional[dict]:
    """查找用户，不存在返回 None"""
    users = {1: {"name": "张三"}, 2: {"name": "李四"}}
    return users.get(user_id)

result = find_user(1)   # {"name": "张三"}
result = find_user(99)  # None


# Union[X, Y]：可以是 X 或 Y
def process_input(data: Union[str, list[str]]) -> list[str]:
    """接受字符串或字符串列表"""
    if isinstance(data, str):
        return [data]
    return data


# Python 3.10+ 简写
def process_input_modern(data: str | list[str]) -> list[str]:
    if isinstance(data, str):
        return [data]
    return data
```

### 6.2 Literal

```python
from typing import Literal


# 限定参数只能是特定的几个值
def set_log_level(level: Literal["debug", "info", "warning", "error"]) -> None:
    print(f"日志级别设置为：{level}")

set_log_level("info")     # ✅
set_log_level("debug")    # ✅
# set_log_level("verbose") # IDE 会提示类型错误


# AI 应用场景：限定模型名称
def chat(
    message: str,
    model: Literal["gpt-4o", "gpt-4o-mini", "claude-sonnet"] = "gpt-4o-mini"
) -> str:
    return f"[{model}] {message}"


# AI 应用场景：限定角色类型
Role = Literal["system", "user", "assistant"]

def create_message(role: Role, content: str) -> dict:
    return {"role": role, "content": content}
```

### 6.3 TypedDict

```python
from typing import TypedDict


# 定义类型化字典（和 TypeScript 的 interface 类似）
class ChatMessage(TypedDict):
    role: str
    content: str


class ChatRequest(TypedDict):
    messages: list[ChatMessage]
    model: str
    temperature: float


# 使用
message: ChatMessage = {"role": "user", "content": "你好"}
request: ChatRequest = {
    "messages": [message],
    "model": "gpt-4o-mini",
    "temperature": 0.7,
}
```

> **核心应用**：LangGraph 的状态就是用 TypedDict 定义的：
> ```python
> from typing import TypedDict, Annotated
> from langgraph.graph import add_messages
>
> class AgentState(TypedDict):
>     messages: Annotated[list, add_messages]
>     next_action: str
> ```

### 6.4 Annotated

```python
from typing import Annotated


# Annotated 给类型附加额外信息
# Annotated[类型, 附加信息1, 附加信息2, ...]

# 基础用法：添加描述
UserId = Annotated[int, "用户唯一标识"]
Username = Annotated[str, "用户名，2-20个字符"]


# 结合 Pydantic（最常见的用法）
from pydantic import BaseModel, Field

class User(BaseModel):
    name: Annotated[str, Field(min_length=2, max_length=20, description="用户名")]
    age: Annotated[int, Field(ge=0, le=150, description="年龄")]
    email: Annotated[str | None, Field(default=None, description="邮箱地址")]
```

> **为什么 Annotated 重要？**
> - Pydantic v2 推荐用 `Annotated[type, Field(...)]` 的写法
> - FastAPI 用它来声明路径参数、查询参数的验证规则
> - LangGraph 用它来定义状态字段的更新方式

### 6.5 其他常用类型

```python
from typing import Any, Callable, TypeVar

# Any：任意类型（尽量少用）
def log(data: Any) -> None:
    print(data)


# Callable：函数类型
# Callable[[参数类型列表], 返回值类型]
def apply_func(func: Callable[[int, int], int], a: int, b: int) -> int:
    return func(a, b)

apply_func(lambda a, b: a + b, 3, 5)  # 8


# TypeVar：泛型（了解即可）
T = TypeVar("T")

def first(items: list[T]) -> T | None:
    return items[0] if items else None

first([1, 2, 3])       # 返回 int
first(["a", "b", "c"]) # 返回 str
```

### 6.6 类型注解总结

| 类型 | 用途 | 使用频率 |
|------|------|---------|
| `str`, `int`, `float`, `bool` | 基础类型 | 极高 |
| `list[X]`, `dict[K, V]` | 容器类型 | 极高 |
| `Optional[X]` / `X \| None` | 可选值 | 极高 |
| `Literal["a", "b"]` | 限定值范围 | 高 |
| `TypedDict` | 类型化字典 | 高（LangGraph） |
| `Annotated[X, ...]` | 附加约束信息 | 高（Pydantic/FastAPI） |
| `Union[X, Y]` / `X \| Y` | 联合类型 | 中 |
| `Callable` | 函数类型 | 中 |
| `Any` | 任意类型 | 低（尽量少用） |
| `TypeVar` | 泛型 | 低（库开发时用） |

---

## 7. 高阶函数 ⚡

### 7.1 函数作为参数

```python
def apply_to_list(func: Callable[[int], int], numbers: list[int]) -> list[int]:
    return [func(n) for n in numbers]

def double(x: int) -> int:
    return x * 2

apply_to_list(double, [1, 2, 3])  # [2, 4, 6]
```

### 7.2 lambda 表达式

```python
# lambda 是匿名函数（JS 的箭头函数）
square = lambda x: x ** 2
square(5)  # 25

# 常见搭配排序
users = [
    {"name": "张三", "age": 25},
    {"name": "李四", "age": 30},
    {"name": "王五", "age": 20},
]

# 按 age 排序
sorted_users = sorted(users, key=lambda u: u["age"])

# 按 name 长度排序
sorted_users = sorted(users, key=lambda u: len(u["name"]))
```

### 7.3 map / filter / reduce

```python
from functools import reduce

numbers = [1, 2, 3, 4, 5]

# map：对每个元素应用函数
squares = list(map(lambda x: x ** 2, numbers))  # [1, 4, 9, 16, 25]

# filter：筛选元素
evens = list(filter(lambda x: x % 2 == 0, numbers))  # [2, 4]

# reduce：累积计算
total = reduce(lambda acc, x: acc + x, numbers)  # 15
```

> **实际开发**：Python 更推荐用列表推导式代替 map/filter，代码更清晰：
> ```python
> # 推荐
> squares = [x ** 2 for x in numbers]
> evens = [x for x in numbers if x % 2 == 0]
>
> # 而不是
> squares = list(map(lambda x: x ** 2, numbers))
> ```

---

## 8. 装饰器基础 ⚡

### 8.1 什么是装饰器

装饰器是一个"包装"函数的函数，在**不修改原函数代码**的情况下给它添加额外功能。

```python
import time


def timer(func):
    """计时装饰器：打印函数执行时间"""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"{func.__name__} 执行耗时：{elapsed:.4f}s")
        return result
    return wrapper


# 使用装饰器
@timer
def slow_function():
    time.sleep(1)
    return "完成"

slow_function()
# 输出：slow_function 执行耗时：1.0012s
```

### 8.2 带参数的装饰器

```python
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
```

### 8.3 functools.wraps

```python
from functools import wraps


def timer(func):
    @wraps(func)  # 保留原函数的 __name__、__doc__ 等信息
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"{func.__name__} 耗时：{time.time() - start:.4f}s")
        return result
    return wrapper


@timer
def my_func():
    """我的函数文档"""
    pass

print(my_func.__name__)  # "my_func"（而不是 "wrapper"）
print(my_func.__doc__)   # "我的函数文档"
```

### 8.4 AI 应用中的装饰器

后续学习中会大量遇到装饰器：

```python
# FastAPI 路由装饰器
# @app.post("/chat")
# async def chat(request: ChatRequest):
#     ...

# LangChain 工具装饰器
# @tool
# def get_weather(city: str) -> str:
#     """获取城市天气"""
#     ...

# Pydantic 验证器装饰器
# @field_validator("age")
# def validate_age(cls, v):
#     ...
```

> 现在只需理解装饰器的机制（函数包装函数），后续遇到具体场景时会更容易理解。

---

## 9. 小结

### 核心知识

| 知识点 | 优先级 | 一句话总结 |
|--------|-------|-----------|
| 函数定义与参数 | 📌 | 掌握位置参数、默认参数、*args/**kwargs |
| 生成器（yield） | 📌🔗 | 流式输出的基础，AI 应用必备 |
| 类型注解进阶 | 📌🔗 | Optional/Literal/TypedDict/Annotated，贯穿 Pydantic/LangGraph/FastAPI |
| 高阶函数 | ⚡ | 了解 lambda 和 sorted 的 key 参数即可 |
| 装饰器 | ⚡ | 理解"函数包装函数"的机制，后续 FastAPI/@tool 会用到 |

### 与 JavaScript 关键差异

| 差异点 | JavaScript | Python |
|--------|-----------|--------|
| 默认参数的可变性 | 每次调用独立 | **共享同一对象**（大坑） |
| 剩余参数 | `...args`（数组） | `*args`（元组）、`**kwargs`（字典） |
| 生成器语法 | `function*` + `yield` | `def` + `yield`（无特殊标记） |
| 类型系统 | TypeScript（编译期） | typing（仅提示，运行时不强制） |
| 箭头函数 | `=>` 保留 this | `lambda` 无 self 问题 |

### 下一节预告

下一节将学习 **类与面向对象**：
- class 定义与 __init__
- 实例方法、类方法、静态方法
- dataclass（新增）
- 继承与特殊方法

---

## 10. 常见问题

### Q: 生成器只能遍历一次？

是的。生成器是"一次性"的，遍历完就耗尽了：

```python
gen = (x for x in range(3))
list(gen)  # [0, 1, 2]
list(gen)  # [] — 已经耗尽

# 如果需要多次遍历，要么用列表，要么重新创建生成器
```

### Q: yield 和 return 能同时用吗？

可以。`return` 在生成器中表示终止迭代（不返回值）：

```python
def gen_with_return():
    yield 1
    yield 2
    return  # 终止，等同于 StopIteration
    yield 3  # 永远不会执行

list(gen_with_return())  # [1, 2]
```

### Q: Optional[str] 和 str | None 有什么区别？

功能完全相同。`str | None` 是 Python 3.10+ 的简写语法：

```python
from typing import Optional

# 以下三种写法等价
def f(x: Optional[str] = None): ...
def f(x: str | None = None): ...
def f(x: Union[str, None] = None): ...

# 3.10+ 推荐用 str | None，更简洁
```

### Q: 什么时候用生成器，什么时候用列表？

- **数据量大或未知大小**：用生成器（如读取大文件、流式 API 响应）
- **需要多次访问**：用列表
- **需要索引访问**：用列表（生成器不支持 `gen[0]`）
- **只需遍历一次**：优先生成器，省内存

### Q: 装饰器的执行顺序是什么？

多个装饰器从下到上包装，从上到下执行：

```python
@decorator_a
@decorator_b
def func():
    pass

# 等价于：func = decorator_a(decorator_b(func))
# 执行时：先进入 a 的逻辑 → 再进入 b 的逻辑 → 执行 func → b 返回 → a 返回
```

### Q: TypedDict 和 Pydantic BaseModel 有什么区别？

| 维度 | TypedDict | BaseModel |
|------|-----------|-----------|
| 运行时验证 | 无 | 有（自动验证类型） |
| 性质 | 普通字典 + 类型提示 | 独立的类实例 |
| 性能 | 更快（就是字典） | 稍慢（有验证开销） |
| 使用场景 | LangGraph 状态、轻量结构 | API 请求/响应模型、数据验证 |
| 访问方式 | `state["key"]` | `model.key` |
