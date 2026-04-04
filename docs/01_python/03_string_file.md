# 03. 字符串与文件基础

> 本节目标：掌握字符串进阶操作、文件读写和路径处理

---

## 1. 概述

### 学习目标

- 掌握字符串常用方法和格式化技巧
- 理解多行字符串和原始字符串的使用场景
- 掌握文件的读写操作和 with 语句
- 学会使用 pathlib 处理路径
- 能够处理日志文件和配置文件

### 预计学习时间

- 字符串进阶：1 小时
- 文件读写：1 小时
- 路径处理：30 分钟
- 练习：1-2 小时

### 本节在 AI 应用中的重要性

| 场景 | 相关知识 |
|-----|---------|
| 读取配置文件 | 文件操作、JSON |
| 处理 API 响应 | 字符串解析 |
| 日志记录 | 文件写入、格式化 |
| Prompt 模板管理 | 多行字符串、文件读取 |
| 知识库文档处理 | 文件读取、字符串处理 |

---

## 2. 字符串进阶

> 本节在第一节"字符串操作"基础上，补充更多进阶内容

### 2.1 更多字符串方法

第一节已介绍：`strip`, `lower`, `upper`, `find`, `replace`, `split`, `join`, `startswith`, `endswith`

**补充方法**

```python
# 大小写转换
"hello world".title()        # "Hello World"（标题格式）
"hello world".capitalize()   # "Hello world"（首字母大写）
"Hello World".swapcase()     # "hELLO wORLD"（大小写互换）

# 去除空白（单侧）
"  hello  ".lstrip()         # "hello  "（只去除左侧）
"  hello  ".rstrip()         # "  hello"（只去除右侧）

# 查找
"hello hello".rfind("hello") # 6（从右侧查找）
"hello".index("l")           # 2（找不到会报错，find 返回 -1）
"hello hello".count("hello") # 2（统计出现次数）

# 分割进阶
"a,b,c".split(",", 1)        # ["a", "b,c"]（最多分割 1 次）
"a.b.c.d".rsplit(".", 1)     # ["a.b.c", "d"]（从右侧分割）
"a\nb\nc".splitlines()       # ["a", "b", "c"]（按行分割）

# 判断方法
"123".isdigit()              # True（只包含数字）
"abc".isalpha()              # True（只包含字母）
"abc123".isalnum()           # True（只包含字母和数字）
"   ".isspace()              # True（只包含空白）

# 对齐与填充
"Hello".center(10, "-")      # "--Hello---"（居中填充）
"Hello".ljust(10, "-")       # "Hello-----"（左对齐填充）
"Hello".rjust(10, "-")       # "-----Hello"（右对齐填充）
"5".zfill(3)                 # "005"（用 0 填充到指定宽度）
```

### 2.2 f-string 进阶格式化

第一节已介绍 f-string 基本用法，这里补充进阶格式化。

```python
# 宽度和对齐
name = "张三"
f"{name:>10}"                # "        张三"（右对齐，宽度 10）
f"{name:<10}"                # "张三        "（左对齐）
f"{name:^10}"                # "    张三    "（居中）

# 数字格式化
count = 1234567
f"{count:,}"                 # "1,234,567"（千分位）
f"{count:_}"                 # "1_234_567"（下划线分隔）
f"{count:e}"                 # "1.234567e+06"（科学计数法）
f"{count:#x}"                # "0x12d687"（十六进制）
f"{count:#b}"                # "0b100101101011010000111"（二进制）

# 百分比
ratio = 0.856
f"{ratio:.2%}"               # "85.60%"

# 组合格式化
price = 99.99
quantity = 10
f"{'单价':<6}{price:>8.2f}"
f"{'数量':<6}{quantity:>8d}"
```

### 2.3 format() 方法

format() 是 Python 2.6+ 的格式化方式，兼容性更好，某些场景更灵活。

```python
# 位置参数
"{}今年{}岁".format("张三", 25)           # "张三今年25岁"
"{0}今年{0}岁".format("张三")             # "张三今年张三岁"

# 关键字参数
"{name}今年{age}岁".format(name="张三", age=25)

# 混合使用
"{0}今年{age}岁".format("张三", age=25)

# 通过索引访问列表
"第一：{0[0]}，第二：{0[1]}".format(["a", "b"])
```

**格式化方式对比**

| 方式 | 版本要求 | 可读性 | 性能 | 适用场景 |
|-----|---------|-------|------|---------|
| f-string | 3.6+ | ⭐⭐⭐ | ⭐⭐⭐ | 大多数场景 |
| format() | 2.6+ | ⭐⭐ | ⭐⭐ | 模板分离、延迟格式化 |
| % 格式化 | 全部 | ⭐ | ⭐ | 旧代码兼容 |

### 2.4 多行字符串

**三引号字符串**

```python
# 多行字符串
text = """
这是第一行
这是第二行
这是第三行
"""

# 保留格式的多行文本
prompt = """
你是一个 AI 助手，请根据用户的问题给出回答。

规则：
1. 回答要简洁
2. 语气要友好
3. 不确定时诚实说明
"""
```

**去除多余的换行**

```python
# 问题：三引号会包含首尾换行
text = """
Hello
World
"""
# 实际是 "\nHello\nWorld\n"

# 解决方法 1：使用 \ 反斜杠
text = """\
Hello
World
"""
# 实际是 "Hello\nWorld\n"

# 解决方法 2：使用 strip()
text = """
Hello
World
""".strip()
# 实际是 "Hello\nWorld"

# 解决方法 3：使用 textwrap.dedent（推荐用于缩进的文本）
import textwrap

prompt = textwrap.dedent("""
    你是一个 AI 助手。
    请回答用户问题。
""").strip()
```

**AI 应用示例：Prompt 模板**

```python
system_prompt = """\
你是一个专业的 Python 编程助手。

你的职责是：
1. 回答 Python 相关问题
2. 提供代码示例
3. 解释代码原理

回答格式：
- 先给出简洁回答
- 再提供代码示例
- 最后解释关键点
"""

user_prompt = f"""
用户问题：{question}

请按照规定格式回答。
"""
```

### 2.4 原始字符串

原始字符串（raw string）不处理转义字符，以 `r` 开头。

**文件路径**

```python
# 普通字符串：\ 需要转义
path = "C:\\Users\\zhangsan\\Documents"

# 原始字符串：不需要转义
path = r"C:\Users\zhangsan\Documents"

# 更推荐：使用 pathlib（后续讲解）
from pathlib import Path
path = Path("C:/Users/zhangsan/Documents")
```

**正则表达式**

```python
import re

# 普通字符串：\\ 匹配 \
pattern = "\\\\d+"      # 需要双重转义

# 原始字符串：更清晰
pattern = r"\\d+"       # 直接写正则

# 示例：匹配数字
text = "abc123def"
result = re.search(r"\d+", text)
print(result.group())   # "123"
```

**何时使用原始字符串**

| 场景 | 是否使用 r"" |
|-----|-------------|
| Windows 文件路径 | ✅ 推荐 |
| 正则表达式 | ✅ 必须 |
| 普通文本 | ❌ 不需要 |
| JSON 字符串 | ❌ 不需要 |

---

## 3. 文件读写

### 3.1 open() 函数基础

**基本语法**

```python
open(file, mode='r', encoding=None)
```

**模式说明**

| 模式 | 说明 | 文件不存在时 |
|-----|------|------------|
| `r` | 只读（默认） | 报错 |
| `w` | 只写（覆盖） | 创建新文件 |
| `a` | 追加 | 创建新文件 |
| `x` | 只写（新建） | 报错（文件存在时） |
| `r+` | 读写 | 报错 |
| `rb` | 二进制读 | 报错 |
| `wb` | 二进制写 | 创建新文件 |

**读取文件**

```python
# 方式 1：读取全部内容
file = open("example.txt", "r", encoding="utf-8")
content = file.read()
file.close()  # 必须手动关闭！

# 方式 2：逐行读取
file = open("example.txt", "r", encoding="utf-8")
for line in file:
    print(line.strip())
file.close()

# 方式 3：读取所有行为列表
file = open("example.txt", "r", encoding="utf-8")
lines = file.readlines()  # ["第一行\n", "第二行\n", ...]
file.close()
```

**写入文件**

```python
# 覆盖写入
file = open("output.txt", "w", encoding="utf-8")
file.write("Hello World\n")
file.write("第二行")
file.close()

# 追加写入
file = open("output.txt", "a", encoding="utf-8")
file.write("\n这是追加的内容")
file.close()

# 写入多行
lines = ["第一行\n", "第二行\n", "第三行\n"]
file = open("output.txt", "w", encoding="utf-8")
file.writelines(lines)
file.close()
```

### 3.2 with 语句（上下文管理器）

使用 `with` 语句可以自动管理文件关闭，**强烈推荐**。

先看语法骨架：

```python
with 表达式 as 变量:
    代码块
```

放到文件里就是：

```python
with open("example.txt", "r", encoding="utf-8") as file:
    content = file.read()
```

你可以先这样理解这 3 个部分：

- `open("example.txt", "r", encoding="utf-8")`：打开文件
- `as file`：把打开后的文件对象绑定给变量 `file`
- 缩进代码块：在这个资源的有效期内使用它

代码块结束后，Python 会自动帮你清理资源。对文件来说，就是自动执行 `close()`。

所以 `with` 本质上很像：

```python
file = open("example.txt", "r", encoding="utf-8")
try:
    content = file.read()
finally:
    file.close()
```

也就是说，`with` 可以先粗略理解成“更安全的 `try/finally` 语法糖”。

**基本用法**

```python
# with 语句会自动关闭文件
with open("example.txt", "r", encoding="utf-8") as file:
    content = file.read()
# 文件在这里自动关闭

# 即使发生异常，文件也会正确关闭
with open("example.txt", "r", encoding="utf-8") as file:
    content = file.read()
    raise Exception("出错了")  # 文件仍然会被正确关闭
```

> 这也是为什么 `with` 不只用于文件。后面你会在锁、数据库连接、HTTP 客户端里看到同样的模式，因为它的本质是“进入时获取资源，退出时自动释放资源”。

**读取文件的几种方式**

```python
# 1. 读取全部内容
with open("example.txt", "r", encoding="utf-8") as file:
    content = file.read()
    print(content)

# 2. 读取指定字节数
with open("example.txt", "r", encoding="utf-8") as file:
    chunk = file.read(10)  # 读取前 10 个字符
    print(chunk)

# 3. 读取一行
with open("example.txt", "r", encoding="utf-8") as file:
    first_line = file.readline()
    print(first_line)

# 4. 逐行迭代（推荐，内存友好）
with open("example.txt", "r", encoding="utf-8") as file:
    for line in file:
        print(line.strip())

# 5. 读取所有行为列表
with open("example.txt", "r", encoding="utf-8") as file:
    lines = file.readlines()
    print(lines)
```

**写入文件**

```python
# 覆盖写入
with open("output.txt", "w", encoding="utf-8") as file:
    file.write("Hello World\n")
    file.write("第二行")

# 追加写入
with open("output.txt", "a", encoding="utf-8") as file:
    file.write("\n追加的内容")

# 同时读写
with open("example.txt", "r+", encoding="utf-8") as file:
    content = file.read()
    file.write("\n新内容")
```

### 3.3 文件指针

文件读写位置由文件指针控制。

```python
with open("example.txt", "r", encoding="utf-8") as file:
    # 当前位置
    print(file.tell())  # 0

    # 读取 5 个字符
    content = file.read(5)
    print(file.tell())  # 5

    # 移动指针到开头
    file.seek(0)
    print(file.tell())  # 0

    # 移动指针到指定位置
    file.seek(10)  # 移动到第 10 个字节
```

### 3.4 二进制文件

```python
# 读取二进制文件（如图片）
with open("image.png", "rb") as file:
    data = file.read()
    print(type(data))  # <class 'bytes'>

# 写入二进制文件
with open("copy.png", "wb") as file:
    file.write(data)

# 复制文件
with open("source.png", "rb") as src, open("dest.png", "wb") as dst:
    dst.write(src.read())
```

### 3.5 实际应用示例

**读取配置文件**

```python
# config.txt 内容：
# API_KEY=your_api_key
# MODEL=gpt-4
# MAX_TOKENS=1000

def load_config(filepath: str) -> dict:
    """加载简单配置文件"""
    config = {}
    with open(filepath, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith("#"):  # 跳过空行和注释
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()
    return config

config = load_config("config.txt")
print(config)  # {"API_KEY": "your_api_key", "MODEL": "gpt-4", ...}
```

**日志解析**

```python
# log.txt 内容：
# 2024-01-15 10:30:15 INFO User logged in
# 2024-01-15 10:31:20 ERROR Database connection failed
# 2024-01-15 10:32:00 INFO Request completed

def parse_log(filepath: str, level: str = "ERROR") -> list:
    """提取指定级别的日志"""
    logs = []
    with open(filepath, "r", encoding="utf-8") as file:
        for line in file:
            if f" {level} " in line:
                logs.append(line.strip())
    return logs

errors = parse_log("log.txt", "ERROR")
print(errors)  # ["2024-01-15 10:31:20 ERROR Database connection failed"]
```

**统计文件信息**

```python
def file_stats(filepath: str) -> dict:
    """统计文件信息"""
    lines = 0
    words = 0
    chars = 0

    with open(filepath, "r", encoding="utf-8") as file:
        for line in file:
            lines += 1
            words += len(line.split())
            chars += len(line)

    return {
        "lines": lines,
        "words": words,
        "chars": chars
    }
```

---

## 4. 路径处理（pathlib）

### 4.1 pathlib 基础

`pathlib` 是 Python 3.4+ 引入的路径处理库，比 `os.path` 更面向对象、更易用。

**创建 Path 对象**

```python
from pathlib import Path

# 当前目录
current = Path.cwd()
print(current)  # /Users/xxx/project

# 用户目录
home = Path.home()
print(home)  # /Users/xxx

# 创建路径
path = Path("folder/file.txt")
path = Path("folder") / "file.txt"  # 使用 / 拼接路径（推荐）
path = Path("folder") / "subfolder" / "file.txt"
```

**路径拼接**

```python
from pathlib import Path

# 使用 / 运算符（推荐）
path = Path("data") / "2024" / "log.txt"
print(path)  # data/2024/log.txt

# 与字符串拼接
path = Path("data") / "file_" + ".txt"  # ❌ 错误！
path = Path("data") / ("file_" + ".txt")  # ✅ 正确

# 绝对路径
base = Path("/Users/xxx/project")
file = base / "data" / "file.txt"
```

### 4.2 路径属性

```python
from pathlib import Path

path = Path("/Users/xxx/project/data/file.txt")

# 路径各部分
path.name       # "file.txt"（文件名）
path.stem       # "file"（不含扩展名）
path.suffix     # ".txt"（扩展名）
path.suffixes   # [".txt"]（多个扩展名，如 .tar.gz）
path.parent     # /Users/xxx/project/data（父目录）
path.parents    # 所有父目录的序列
path.anchor     # "/"（根目录，Windows 是 "C:\"）

# 示例
path = Path("archive.tar.gz")
path.stem       # "archive.tar"
path.suffix     # ".gz"
path.suffixes   # [".tar", ".gz"]
```

### 4.3 路径检查

```python
from pathlib import Path

path = Path("data/file.txt")

# 检查是否存在
path.exists()        # True/False

# 检查类型
path.is_file()       # 是否是文件
path.is_dir()        # 是否是目录

# 检查权限
path.is_readable()   # 是否可读（Python 3.12+）
path.is_writable()   # 是否可写（Python 3.12+）

# 兼容写法
import os
os.access(path, os.R_OK)  # 是否可读
os.access(path, os.W_OK)  # 是否可写
```

### 4.4 文件操作

**创建和删除**

```python
from pathlib import Path

# 创建目录
Path("data/logs").mkdir(parents=True, exist_ok=True)
# parents=True：创建中间目录
# exist_ok=True：目录存在时不报错

# 创建空文件
Path("data/file.txt").touch()

# 删除文件
Path("data/file.txt").unlink()

# 删除空目录
Path("data/empty").rmdir()

# 删除目录及其内容（需要 shutil）
import shutil
shutil.rmtree("data")
```

**读写文件**

```python
from pathlib import Path

path = Path("data/file.txt")

# 读取文件
content = path.read_text(encoding="utf-8")
lines = path.read_text(encoding="utf-8").splitlines()

# 写入文件
path.write_text("Hello World\n", encoding="utf-8")

# 追加内容
with path.open("a", encoding="utf-8") as file:
    file.write("追加内容\n")
```

**遍历目录**

```python
from pathlib import Path

data_dir = Path("data")

# 遍历直接子项
for item in data_dir.iterdir():
    print(item.name, item.is_file())

# 递归遍历所有文件
for file in data_dir.rglob("*"):
    if file.is_file():
        print(file)

# 按模式查找
for py_file in data_dir.glob("**/*.py"):  # 所有 .py 文件
    print(py_file)

for txt_file in data_dir.rglob("*.txt"):  # 递归查找 .txt 文件
    print(txt_file)
```

### 4.5 pathlib vs os.path

```python
import os
from pathlib import Path

# 拼接路径
# os.path
path = os.path.join("data", "logs", "app.log")
# pathlib
path = Path("data") / "logs" / "app.log"

# 获取文件名
# os.path
name = os.path.basename("/path/to/file.txt")
# pathlib
name = Path("/path/to/file.txt").name

# 获取扩展名
# os.path
ext = os.path.splitext("file.txt")[1]
# pathlib
ext = Path("file.txt").suffix

# 检查是否存在
# os.path
exists = os.path.exists("file.txt")
# pathlib
exists = Path("file.txt").exists()

# 获取父目录
# os.path
parent = os.path.dirname("/path/to/file.txt")
# pathlib
parent = Path("/path/to/file.txt").parent
```

**推荐**：新项目优先使用 `pathlib`，更直观、更 Pythonic。

### 4.6 实际应用示例

**安全的文件路径处理**

```python
from pathlib import Path

def read_json_file(filepath: str) -> dict:
    """安全读取 JSON 文件"""
    import json

    path = Path(filepath)

    # 检查文件存在
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {filepath}")

    # 检查是否是文件
    if not path.is_file():
        raise ValueError(f"不是文件: {filepath}")

    # 读取内容
    try:
        content = path.read_text(encoding="utf-8")
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON 解析失败: {e}")
```

**管理项目目录结构**

```python
from pathlib import Path

class ProjectPaths:
    """项目路径管理"""

    def __init__(self, base_dir: str = "."):
        self.base = Path(base_dir).resolve()
        self.data = self.base / "data"
        self.logs = self.base / "logs"
        self.config = self.base / "config"
        self.output = self.base / "output"

    def ensure_dirs(self):
        """确保所有目录存在"""
        for path in [self.data, self.logs, self.config, self.output]:
            path.mkdir(parents=True, exist_ok=True)

    def get_log_file(self, name: str) -> Path:
        """获取日志文件路径"""
        return self.logs / f"{name}.log"

    def get_data_file(self, name: str) -> Path:
        """获取数据文件路径"""
        return self.data / name

# 使用
paths = ProjectPaths()
paths.ensure_dirs()
log_file = paths.get_log_file("app")
```

---

## 5. JSON 文件处理

JSON 是 AI 应用中最常用的数据格式，Python 内置 `json` 模块。

### 5.1 基本操作

```python
import json

# Python 对象 -> JSON 字符串
data = {"name": "张三", "age": 25, "hobbies": ["阅读", "编程"]}
json_str = json.dumps(data, ensure_ascii=False, indent=2)
print(json_str)
# {
#   "name": "张三",
#   "age": 25,
#   "hobbies": ["阅读", "编程"]
# }

# JSON 字符串 -> Python 对象
parsed = json.loads(json_str)
print(parsed["name"])  # "张三"
```

### 5.2 文件读写

```python
import json
from pathlib import Path

# 写入 JSON 文件
data = {"name": "张三", "age": 25}
path = Path("data/user.json")
path.parent.mkdir(parents=True, exist_ok=True)

with path.open("w", encoding="utf-8") as file:
    json.dump(data, file, ensure_ascii=False, indent=2)

# 读取 JSON 文件
with path.open("r", encoding="utf-8") as file:
    loaded = json.load(file)
    print(loaded)
```

### 5.3 常用参数

```python
import json

data = {"name": "张三", "score": 95.5}

# ensure_ascii：处理中文
json.dumps(data)                      # {"name": "\u5f20\u4e09", ...}
json.dumps(data, ensure_ascii=False)  # {"name": "张三", ...}

# indent：格式化输出
json.dumps(data, indent=2)    # 缩进 2 空格
json.dumps(data, indent=4)    # 缩进 4 空格

# sort_keys：按键排序
json.dumps(data, sort_keys=True)

# separators：紧凑输出
json.dumps(data, separators=(",", ":"))  # 无空格，最紧凑
```

### 5.4 处理复杂类型

```python
import json
from datetime import datetime
from pathlib import Path

# JSON 不支持 datetime，需要自定义处理
data = {
    "name": "张三",
    "created_at": datetime.now(),
    "path": Path("/Users/test")
}

# 方法 1：预先转换
data["created_at"] = data["created_at"].isoformat()
data["path"] = str(data["path"])

# 方法 2：自定义编码器
class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Path):
            return str(obj)
        return super().default(obj)

json_str = json.dumps(data, cls=CustomEncoder, ensure_ascii=False)
```

---

## 6. 练习题

请在 `source/01_python/03_string_file/exercises.py` 中完成以下练习：

### 练习 1：字符串处理

```python
# 给定字符串 "  Hello, World! Welcome to Python!  "

# 1. 去除首尾空格
# 2. 转换为小写
# 3. 按空格分割成列表
# 4. 用 "-" 连接列表
# 5. 统计 "o" 出现的次数
# 6. 将所有 "o" 替换为 "O"
```

### 练习 2：格式化输出

```python
# 使用 f-string 实现以下格式化：

# 1. 商品列表
# 商品名        单价    数量    小计
# iPhone       5999    2       11998
# MacBook      9999    1       9999
# ------------------------------------
# 合计：       21997

# 2. 百分比显示
# 进度：85.6%
# 完成：████████░░ 85.6%

# 3. 数字格式化
# 1234567 -> 1,234,567
# 0.856 -> 85.60%
# 3.14159 -> 3.14
```

### 练习 3：文件读写

```python
# 1. 创建文件 "data/numbers.txt"，写入 1-100（每行一个数字）
# 2. 读取文件，计算所有数字的和
# 3. 追加一行 "总和: xxx"
# 4. 读取文件，找出所有偶数
```

### 练习 4：日志解析

```python
# 有日志文件 log.txt，格式如下：
# 2024-01-15 10:30:15 INFO User logged in
# 2024-01-15 10:31:20 ERROR Database connection failed
# 2024-01-15 10:32:00 WARN Memory usage high
# 2024-01-15 10:33:10 ERROR API timeout
# 2024-01-15 10:34:00 INFO Request completed

# 实现函数：
# 1. parse_log(filepath) -> 返回所有日志的列表（每条日志为字典）
# 2. filter_by_level(logs, level) -> 按级别过滤
# 3. count_by_level(logs) -> 统计各级别数量
# 4. extract_timestamps(logs) -> 提取所有时间戳
```

### 练习 5：路径操作

```python
# 使用 pathlib 实现：

# 1. 创建目录结构 data/2024/01
# 2. 在该目录下创建文件 summary.txt
# 3. 检查文件是否存在
# 4. 获取文件的父目录、文件名、扩展名
# 5. 列出 data 目录下的所有 .txt 文件
# 6. 计算文件大小（字节）
```

### 练习 6：配置文件处理

```python
# 实现一个简单的配置文件管理器：

# 配置文件格式（config.txt）：
# # 这是注释
# API_KEY=sk-xxx
# MODEL=gpt-4
# MAX_TOKENS=1000
# DEBUG=true

# 实现以下功能：
# 1. load_config(filepath) -> 读取配置，返回字典
# 2. save_config(filepath, config) -> 保存配置
# 3. get_config(key, default=None) -> 获取配置项
# 4. set_config(key, value) -> 设置配置项
# 5. 支持类型转换（true/false -> bool，数字 -> int）
```

---

## 7. 小结

### 本节要点

1. **字符串进阶**
   - 掌握常用方法：strip, split, join, replace, find
   - f-string 是首选的格式化方式
   - 多行字符串用于 Prompt 模板
   - 原始字符串用于路径和正则

2. **文件读写**
   - 使用 with 语句自动管理资源
   - 注意 encoding="utf-8" 处理中文
   - 逐行读取适合大文件

3. **路径处理**
   - pathlib 比 os.path 更直观
   - 使用 / 运算符拼接路径
   - Path 对象有丰富的属性和方法

4. **JSON 处理**
   - dumps/loads 处理字符串
   - dump/load 处理文件
   - ensure_ascii=False 处理中文

### 与 JavaScript 对照表

| 特性 | Python | JavaScript |
|-----|--------|------------|
| 字符串格式化 | f"{name}" | `${name}` |
| 多行字符串 | """...""" | `...` |
| 去除空白 | strip() | trim() |
| 分割 | split(",") | split(",") |
| 连接 | "-".join(list) | list.join("-") |
| 路径拼接 | Path("a") / "b" | path.join("a", "b") |
| JSON 序列化 | json.dumps() | JSON.stringify() |
| JSON 解析 | json.loads() | JSON.parse() |

### 下一节预告

下一节将进行 **综合练习：通讯录管理**：
- 结合列表、字典、文件操作
- 实现完整的命令行程序
- 数据持久化存储

---

## 8. 常见问题

### Q: 读写文件时为什么需要指定 encoding？

不同系统默认编码不同：
- Windows：可能使用 GBK
- macOS/Linux：通常使用 UTF-8

不指定编码可能导致中文乱码。**始终推荐**指定 `encoding="utf-8"`。

### Q: with 语句有什么优势？

1. **自动关闭文件**：即使发生异常也能正确关闭
2. **代码更简洁**：不需要手动 close()
3. **资源管理更安全**：防止资源泄露

```python
# 推荐
with open("file.txt") as f:
    content = f.read()

# 不推荐
f = open("file.txt")
content = f.read()
f.close()  # 如果 read() 出错，close() 不会执行
```

### Q: Path("file.txt").read_text() 和 open() 有什么区别？

`read_text()` 是便捷方法，适合小文件：

```python
# 等价写法
content = Path("file.txt").read_text(encoding="utf-8")

with open("file.txt", encoding="utf-8") as f:
    content = f.read()
```

大文件建议使用 `open()` 逐行读取，避免内存问题。

### Q: 如何处理大文件？

逐行读取，不要一次性读取全部内容：

```python
# ❌ 大文件不要这样做
with open("huge.log") as f:
    content = f.read()  # 可能耗尽内存

# ✅ 逐行处理
with open("huge.log") as f:
    for line in f:
        process(line)  # 每次只处理一行
```

### Q: pathlib 如何获取文件大小？

```python
from pathlib import Path

path = Path("file.txt")
size = path.stat().st_size  # 字节数

# 人类可读格式
def human_size(size: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}TB"

print(human_size(size))
```

### Q: 如何处理文件路径中的特殊字符？

```python
from pathlib import Path

# 路径包含空格或中文
path = Path("data/我的文件/2024-01 report.txt")

# pathlib 会自动处理，无需特殊处理
content = path.read_text(encoding="utf-8")

# 避免的做法
# path = "data/我的文件/2024-01 report.txt".replace(" ", "\\ ")  # 不需要
```
