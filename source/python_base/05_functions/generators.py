import time
import sys

# ========================================
# 5.1 什么是生成器
# ========================================
# 生成器是一种特殊的函数，使用 `yield` 而不是 `return` 返回值。
# 它不会一次性计算所有结果，而是**按需逐个产出**。

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


# ========================================
# 5.2 生成器的执行流程
# ========================================

def countdown(n: int):
    print(f"开始倒计时：{n}")
    while n > 0:
        yield n   # 产出值 暂停
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

# # 用 for 循环（自动处理 StopIteration）
print("--- for 循环 ---")
for n in countdown(3):
    print(f"  {n}")


# ========================================
# 5.3 生成器 vs 列表：内存优势
# ========================================

# 列表：全部在内存中
numbers_list = [i for i in range(1_000_000)]
print(sys.getsizeof(numbers_list))  # 约 8 MB

# 生成器：几乎不占内存
numbers_gen = (i for i in range(1_000_000))
print(sys.getsizeof(numbers_gen))   # 约 200 字节


# ========================================
# 5.4 模拟流式输出
# ========================================

# 模拟流式输出
def stream_response(text: str, delay: float = 0.05):
    """模拟 LLM 流式输出，逐字产出"""
    for char in text:
        yield char
        time.sleep(delay)


# 使用：逐字打印（类似 ChatGPT 的效果）
print("--- 逐字流式输出 ---")
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

print("--- 按 chunk 流式输出 ---")
for chunk in stream_chat_response("生成器是流式输出的基础。"):
    if chunk["type"] == "token":
        print(chunk["content"], end="", flush=True)
    elif chunk["type"] == "done":
        print("\n[完成]")


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
# yield from gen_a() 等价于 for item in gen_a(): yield item
def combined():
    yield from gen_a()
    yield from gen_b()

print("手动合并:", list(combined_manual()))  # [1, 2, 3, 4]
print("yield from:", list(combined()))       # [1, 2, 3, 4]


# ========================================
# 实际场景一：模拟 LLM 多段流式输出
# ========================================

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
print("--- 多段流式输出 ---")
for char in full_stream():
    print(char, end="", flush=True)
print()


# ========================================
# 实际场景二：分段读取文件（无需一次性加载到内存）
# ========================================

import os
import shutil

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
shutil.rmtree("temp_files")

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

asyncio.run(main())