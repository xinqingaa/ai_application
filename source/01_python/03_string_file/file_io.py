BASE = "source/01_python/03_string_file/data"
EXAMPLE_PATH = f"{BASE}/example.txt"
OUTPUT_PATH = f"{BASE}/output.txt"


# ========================================
# 3.1 open() 函数基础 - 读取文件 r
# ========================================

# 方式 1：读取全部内容
file = open(EXAMPLE_PATH, "r", encoding="utf-8")
content = file.read()
print(content)
file.close()

# 方式 2：逐行读取
file = open(EXAMPLE_PATH, "r", encoding="utf-8")
for line in file:
    print(line.strip())
file.close()

# 方式 3：读取所有行为列表
file = open(EXAMPLE_PATH, "r", encoding="utf-8")
lines = file.readlines()
print(lines)
file.close()


# ========================================
# 3.1 open() 函数基础 - 写入文件 w a
# ========================================

# 覆盖写入
file = open(OUTPUT_PATH, "w", encoding="utf-8")
file.write("Hello World\n")
file.write("第二行")
file.close()

# 追加写入
file = open(OUTPUT_PATH, "a", encoding="utf-8")
file.write("\n这是追加的内容")
file.close()

# 验证：读取看看写入是否成功
file = open(OUTPUT_PATH, "r", encoding="utf-8")
print(file.read())
file.close()


# ========================================
# 3.2 with 语句（上下文管理器）
# ========================================
# 语法：
# with open(...) as file:
#     使用 file
#
# 可以先把它理解成：
# 1. 打开资源
# 2. 把资源绑定给 as 后面的变量
# 3. 执行代码块
# 4. 代码块结束后自动清理资源
#
# 它和下面这种 try/finally 很像：
# file = open(...)
# try:
#     ...
# finally:
#     file.close()

# with 自动关闭文件
with open(EXAMPLE_PATH, "r", encoding="utf-8") as file:
    content = file.read()
    print("with 读取:")
    print(content)

# as file 的意思：把打开后的文件对象绑定给变量 file
with open(EXAMPLE_PATH, "r", encoding="utf-8") as file:
    print("file 变量类型:", type(file).__name__)
    print("前 10 个字符:", file.read(10))

# 逐行读取时，with + for 是最常见组合
with open(EXAMPLE_PATH, "r", encoding="utf-8") as file:
    print("逐行读取:")
    for line in file:
        print(f"  {line.strip()}")

# with 写入
with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
    file.write("用 with 写入\n")
    file.write("第二行")

# 和 with 等价的手写版：自己负责 close()
file = open(EXAMPLE_PATH, "r", encoding="utf-8")
try:
    print("try/finally 读取:")
    print(file.read())
finally:
    file.close()


# ========================================
# 3.3 文件指针
# ========================================

with open(EXAMPLE_PATH, "r", encoding="utf-8") as file:
    print("当前位置:", file.tell())  # 0

    content = file.read(5)
    print("读取 5 个字符:", content)
    print("当前位置:", file.tell())

    file.seek(0)
    print("seek 后位置:", file.tell())  # 0
