# 2.1 更多字符串方法

# 大小写转换
print("hello world".title())
print("hello world".capitalize())
print("Hello World".swapcase())

# 去除空白（单侧）
print("  hello  ".lstrip())
print("  hello  ".rstrip())

# 查找
print("hello hello".rfind("hello"))
print("hello".index("l"))
print("hello hello".count("hello"))

# 分割进阶
print("a,b,c".split(",", 1))
print("a.b.c.d".rsplit(".", 1))
print("a\nb\nc".splitlines())

# 判断方法
print("123".isdigit())
print("abc".isalpha())
print("abc123".isalnum())
print("   ".isspace())

# 对齐与填充
print("Hello".center(10, "-"))
print("Hello".ljust(10, "-"))
print("Hello".rjust(10, "-"))
print("5".zfill(3))

# 2.2 f-string 进阶格式化

name = "张三"
print(f"{name:>10}")   # 右对齐
print(f"{name:<10}")   # 左对齐
print(f"{name:^10}")   # 居中

count = 1234567
print(f"{count:,}")    # 千分位
print(f"{count:_}")    # 下划线分隔
print(f"{count:e}")    # 科学计数法
print(f"{count:#x}")   # 十六进制
print(f"{count:#b}")   # 二进制

ratio = 0.856
print(f"{ratio:.2%}")  # 百分比

# 2.3 format() 方法

print("{}今年{}岁".format("张三", 25))
print("{0}今年{0}岁".format("张三"))
print("{name}今年{age}岁".format(name="张三", age=25))
print("{0}今年{age}岁".format("张三", age=25))
print("第一：{0[0]}，第二：{0[1]}".format(["a", "b"]))

# 2.4 多行字符串

# 三引号字符串
text = """
这是第一行
这是第二行
这是第三行
"""
print(repr(text))  # 用 repr 查看实际内容（包含 \n）

# 反斜杠去除首行换行
text = """\
Hello
World
"""
print(repr(text))

# strip() 去除首尾空白
text = """
Hello
World
""".strip()
print(repr(text))

# textwrap.dedent
import textwrap
prompt = textwrap.dedent("""
    你是一个 AI 助手。
    请回答用户问题。
""").strip()
print(repr(prompt))