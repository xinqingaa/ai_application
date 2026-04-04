# 03. 字符串与文件基础 - 实践指南

> 本文档说明如何跟着 [学习文档](../../../docs/01_python/03_string_file.md) 一步步动手操作

---

## 核心原则

```
读文档 → 新建文件 → 照着文档敲代码 → 运行看结果
```

- 所有操作在项目根目录 `/Users/linruiqiang/work/ai_application` 下进行
- 本目录下的代码文件用来**练习文档中的每个示例**，不是写 exercises
- 每个文档章节对应一个 `.py` 文件，跟着文档内容逐步填充

---

## 最终目录结构

完成所有练习后，本目录结构如下：

```
source/01_python/03_string_file/
├── README.md            ← 你正在读的这个文件
├── exercises.py         ← （已存在，暂不管）
├── string_advanced.py   ← 第 2 步创建：练习文档第 2 章「字符串进阶」
├── file_io.py           ← 第 3 步创建：练习文档第 3 章「文件读写」
├── pathlib_basics.py    ← 第 4 步创建：练习文档第 4 章「路径处理」
├── json_basics.py       ← 第 5 步创建：练习文档第 5 章「JSON 处理」
└── data/                ← 运行代码时自动生成的数据目录
    ├── example.txt
    ├── output.txt
    ├── log.txt
    ├── config.txt
    └── user.json
```

---

## 第 1 步：字符串进阶（文档第 2 章）

**新建文件**：`string_advanced.py`

**不需要提前准备任何文件**，这一章全部是字符串操作，直接写 Python 代码。

### 操作流程

1. 打开文档第 2 章，从 2.1 开始读

2. 新建 `string_advanced.py`，照着文档把代码敲进去。建议按以下结构组织：

```python
# ========================================
# 2.1 更多字符串方法
# ========================================

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
```

3. 读到 2.2 节 f-string 进阶格式化，继续往下加：

```python
# ========================================
# 2.2 f-string 进阶格式化
# ========================================

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
```

4. 读到 2.3 节 format()，继续加：

```python
# ========================================
# 2.3 format() 方法
# ========================================

print("{}今年{}岁".format("张三", 25))
print("{0}今年{0}岁".format("张三"))
print("{name}今年{age}岁".format(name="张三", age=25))
print("{0}今年{age}岁".format("张三", age=25))
print("第一：{0[0]}，第二：{0[1]}".format(["a", "b"]))
```

5. 读到 2.4 节多行字符串，继续加：

```python
# ========================================
# 2.4 多行字符串
# ========================================

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
```

6. 读到 2.4 原始字符串部分，继续加：

```python
# ========================================
# 2.4 原始字符串
# ========================================

# 文件路径
path1 = "C:\\Users\\zhangsan\\Documents"  # 普通字符串，需要转义
path2 = r"C:\Users\zhangsan\Documents"    # 原始字符串，不需要转义
print(path1 == path2)  # True

# 正则表达式
import re
text = "abc123def"
result = re.search(r"\d+", text)
print(result.group())  # "123"
```

7. 运行验证：

```bash
python source/01_python/03_string_file/string_advanced.py
```

---

## 第 2 步：文件读写（文档第 3 章）

**新建文件**：`file_io.py`

这一章开始涉及文件操作。文档中的示例代码需要一个 `example.txt` 文件来读取。

### 操作流程

1. 先创建测试用的数据文件。在项目根目录下运行：

```bash
mkdir -p source/01_python/03_string_file/data
```

然后手动创建 `source/01_python/03_string_file/data/example.txt`，内容随意写几行，例如：

```
这是第一行
这是第二行
这是第三行
Hello World
```

2. 新建 `file_io.py`，照着文档第 3 章开始敲代码。

3. **文档 3.1 节 — open() 基础**。注意：文档中的路径 `"example.txt"` 要改成相对项目根目录的正确路径：

```python
# ========================================
# 3.1 open() 函数基础 - 读取文件
# ========================================

# 方式 1：读取全部内容
file = open("source/01_python/03_string_file/data/example.txt", "r", encoding="utf-8")
content = file.read()
print(content)
file.close()

# 方式 2：逐行读取
file = open("source/01_python/03_string_file/data/example.txt", "r", encoding="utf-8")
for line in file:
    print(line.strip())
file.close()

# 方式 3：读取所有行为列表
file = open("source/01_python/03_string_file/data/example.txt", "r", encoding="utf-8")
lines = file.readlines()
print(lines)
file.close()
```

4. 继续写文档 3.1 的**写入文件**部分：

```python
# ========================================
# 3.1 open() 函数基础 - 写入文件
# ========================================

# 覆盖写入
file = open("source/01_python/03_string_file/data/output.txt", "w", encoding="utf-8")
file.write("Hello World\n")
file.write("第二行")
file.close()

# 追加写入
file = open("source/01_python/03_string_file/data/output.txt", "a", encoding="utf-8")
file.write("\n这是追加的内容")
file.close()

# 验证：读取看看写入是否成功
file = open("source/01_python/03_string_file/data/output.txt", "r", encoding="utf-8")
print(file.read())
file.close()
```

5. 读到 **3.2 节 with 语句**，这是重点，继续往下加：

```python
# ========================================
# 3.2 with 语句（推荐方式）
# ========================================

# 语法：
# with open(...) as file:
#     使用 file
#
# 你可以先把它理解成：
# file = open(...)
# try:
#     ...
# finally:
#     file.close()

base = "source/01_python/03_string_file/data"

# with 自动关闭文件
with open(f"{base}/example.txt", "r", encoding="utf-8") as file:
    content = file.read()
    print("with 读取:", content)

# 读取指定字节数
with open(f"{base}/example.txt", "r", encoding="utf-8") as file:
    chunk = file.read(10)
    print("前10个字符:", chunk)

# 逐行迭代（推荐）
with open(f"{base}/example.txt", "r", encoding="utf-8") as file:
    print("逐行读取:")
    for line in file:
        print(f"  {line.strip()}")

# with 写入
with open(f"{base}/output.txt", "w", encoding="utf-8") as file:
    file.write("用 with 写入\n")
    file.write("第二行")

# 和 with 等价的手写版：自己负责 close()
file = open(f"{base}/example.txt", "r", encoding="utf-8")
try:
    print("try/finally 读取:")
    print(file.read())
finally:
    file.close()
```

这一节要重点记：

- `with ... as file:` 里的 `as file`，就是把资源绑定给变量 `file`
- `with` 最核心的价值不是“少写一行代码”，而是“自动做清理”
- 文件只是最常见例子，后面你还会遇到 `async with httpx.AsyncClient() as client`

6. 读到 **3.3 节文件指针**：

```python
# ========================================
# 3.3 文件指针
# ========================================

with open(f"{base}/example.txt", "r", encoding="utf-8") as file:
    print("当前位置:", file.tell())  # 0

    content = file.read(5)
    print("读取5个字符:", content)
    print("当前位置:", file.tell())  # 5

    file.seek(0)  # 回到开头
    print("seek后位置:", file.tell())  # 0
```

7. 读到 **3.5 节实际应用示例**，需要准备额外文件。

先手动创建 `source/01_python/03_string_file/data/log.txt`，内容如下：

```
2024-01-15 10:30:15 INFO User logged in
2024-01-15 10:31:20 ERROR Database connection failed
2024-01-15 10:32:00 INFO Request completed
```

再手动创建 `source/01_python/03_string_file/data/config.txt`，内容如下：

```
# 应用配置
API_KEY=your_api_key
MODEL=gpt-4
MAX_TOKENS=1000
```

然后在代码中照着文档实现这三个示例函数：

```python
# ========================================
# 3.5 实际应用示例
# ========================================

# 读取配置文件
def load_config(filepath: str) -> dict:
    config = {}
    with open(filepath, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()
    return config

config = load_config(f"{base}/config.txt")
print("配置:", config)

# 日志解析
def parse_log(filepath: str, level: str = "ERROR") -> list:
    logs = []
    with open(filepath, "r", encoding="utf-8") as file:
        for line in file:
            if f" {level} " in line:
                logs.append(line.strip())
    return logs

errors = parse_log(f"{base}/log.txt", "ERROR")
print("ERROR日志:", errors)

# 统计文件信息
def file_stats(filepath: str) -> dict:
    lines = 0
    words = 0
    chars = 0
    with open(filepath, "r", encoding="utf-8") as file:
        for line in file:
            lines += 1
            words += len(line.split())
            chars += len(line)
    return {"lines": lines, "words": words, "chars": chars}

stats = file_stats(f"{base}/example.txt")
print("文件统计:", stats)
```

8. 运行验证：

```bash
python source/01_python/03_string_file/file_io.py
```

9. 检查 `data/` 目录下是否生成了 `output.txt`，内容是否正确。

---

## 第 3 步：路径处理 pathlib（文档第 4 章）

**新建文件**：`pathlib_basics.py`

这一章不需要提前准备文件，代码会自己创建和删除文件。

### 操作流程

1. 打开文档第 4 章，从 4.1 开始

2. 新建 `pathlib_basics.py`，照着文档敲代码：

```python
from pathlib import Path

# ========================================
# 4.1 pathlib 基础
# ========================================

# 当前目录
current = Path.cwd()
print("当前目录:", current)

# 用户目录
home = Path.home()
print("用户目录:", home)

# 路径拼接（推荐用 / 运算符）
path = Path("folder") / "file.txt"
print("拼接路径:", path)

path = Path("data") / "2024" / "log.txt"
print("多层拼接:", path)
```

3. 读到 **4.2 路径属性**：

```python
# ========================================
# 4.2 路径属性
# ========================================

path = Path("/Users/xxx/project/data/file.txt")

print("文件名:", path.name)       # file.txt
print("不含扩展名:", path.stem)   # file
print("扩展名:", path.suffix)     # .txt
print("父目录:", path.parent)     # /Users/xxx/project/data
print("根目录:", path.anchor)     # /

# 多扩展名示例
path2 = Path("archive.tar.gz")
print("多扩展名:", path2.suffixes)  # ['.tar', '.gz']
```

4. 读到 **4.4 文件操作**，这段会实际创建和删除文件：

```python
# ========================================
# 4.4 文件操作 - 创建和删除
# ========================================

base = Path("source/01_python/03_string_file/data")

# 创建目录
(base / "logs").mkdir(parents=True, exist_ok=True)
print("logs目录已创建")

# 创建空文件
test_file = base / "test_file.txt"
test_file.touch()
print("文件是否存在:", test_file.exists())

# 删除文件
test_file.unlink()
print("删除后是否存在:", test_file.exists())
```

5. 继续写 pathlib 的**读写文件**和**遍历目录**：

```python
# ========================================
# 4.4 文件操作 - 读写
# ========================================

rw_file = base / "pathlib_test.txt"
rw_file.write_text("用 pathlib 写入的内容\n", encoding="utf-8")
content = rw_file.read_text(encoding="utf-8")
print("读取内容:", content)

# ========================================
# 4.4 文件操作 - 遍历目录
# ========================================

print("\ndata 目录下的文件:")
for item in base.iterdir():
    print(f"  {item.name} ({'文件' if item.is_file() else '目录'})")

print("\n所有 .txt 文件:")
for txt_file in base.rglob("*.txt"):
    print(f"  {txt_file}")
```

6. 读到 **4.5 pathlib vs os.path**，照着敲一遍对比：

```python
# ========================================
# 4.5 pathlib vs os.path 对比
# ========================================

import os

# 拼接路径
print(os.path.join("data", "logs", "app.log"))
print(Path("data") / "logs" / "app.log")

# 获取文件名
print(os.path.basename("/path/to/file.txt"))
print(Path("/path/to/file.txt").name)

# 获取扩展名
print(os.path.splitext("file.txt")[1])
print(Path("file.txt").suffix)
```

7. 读到 **4.6 实际应用示例**，照着文档把 `read_json_file` 和 `ProjectPaths` 两个示例敲进去。

8. 运行验证：

```bash
python source/01_python/03_string_file/pathlib_basics.py
```

---

## 第 4 步：JSON 文件处理（文档第 5 章）

**新建文件**：`json_basics.py`

### 操作流程

1. 打开文档第 5 章

2. 新建 `json_basics.py`，照着文档敲代码：

```python
import json
from pathlib import Path
from datetime import datetime

# ========================================
# 5.1 基本操作
# ========================================

# Python 对象 -> JSON 字符串
data = {"name": "张三", "age": 25, "hobbies": ["阅读", "编程"]}
json_str = json.dumps(data, ensure_ascii=False, indent=2)
print(json_str)

# JSON 字符串 -> Python 对象
parsed = json.loads(json_str)
print(parsed["name"])
```

3. 读到 **5.2 文件读写**：

```python
# ========================================
# 5.2 JSON 文件读写
# ========================================

base = Path("source/01_python/03_string_file/data")
base.mkdir(parents=True, exist_ok=True)

# 写入 JSON 文件
user_data = {"name": "张三", "age": 25}
json_path = base / "user.json"

with json_path.open("w", encoding="utf-8") as file:
    json.dump(user_data, file, ensure_ascii=False, indent=2)

# 读取 JSON 文件
with json_path.open("r", encoding="utf-8") as file:
    loaded = json.load(file)
    print("读取 JSON:", loaded)
```

4. 读到 **5.3 常用参数**，逐个试一遍：

```python
# ========================================
# 5.3 常用参数
# ========================================

data = {"name": "张三", "score": 95.5}

# 中文处理
print(json.dumps(data))                       # unicode 转义
print(json.dumps(data, ensure_ascii=False))   # 保留中文

# 格式化
print(json.dumps(data, indent=2))
print(json.dumps(data, sort_keys=True))
print(json.dumps(data, separators=(",", ":")))  # 紧凑
```

5. 读到 **5.4 处理复杂类型**：

```python
# ========================================
# 5.4 处理复杂类型
# ========================================

data = {
    "name": "张三",
    "created_at": datetime.now(),
    "path": Path("/Users/test")
}

# 方法 1：预先转换
data["created_at"] = data["created_at"].isoformat()
data["path"] = str(data["path"])
print(json.dumps(data, ensure_ascii=False, indent=2))

# 方法 2：自定义编码器
class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Path):
            return str(obj)
        return super().default(obj)

data2 = {
    "name": "李四",
    "created_at": datetime.now(),
    "path": Path("/Users/demo")
}
print(json.dumps(data2, cls=CustomEncoder, ensure_ascii=False, indent=2))
```

6. 运行验证：

```bash
python source/01_python/03_string_file/json_basics.py
```

7. 检查 `data/user.json` 文件是否正确生成。

---

## 需要手动创建的文件清单

在跟着文档操作之前，先创建好以下文件：

| 文件 | 什么时候需要 | 内容 |
|-----|------------|------|
| `data/example.txt` | 第 2 步（文档 3.1 节） | 随意写几行文字 |
| `data/log.txt` | 第 2 步（文档 3.5 节） | 见下方内容 |
| `data/config.txt` | 第 2 步（文档 3.5 节） | 见下方内容 |

**log.txt 内容**：
```
2024-01-15 10:30:15 INFO User logged in
2024-01-15 10:31:20 ERROR Database connection failed
2024-01-15 10:32:00 INFO Request completed
```

**config.txt 内容**：
```
# 应用配置
API_KEY=your_api_key
MODEL=gpt-4
MAX_TOKENS=1000
```

其余文件（`output.txt`、`user.json`、`pathlib_test.txt` 等）由代码自动生成，不需要手动创建。

---

## 一次性创建所有必要文件

如果想先把环境和文件都准备好再开始学，在项目根目录下执行：

```bash
# 创建数据目录
mkdir -p source/01_python/03_string_file/data

# 创建 example.txt
cat > source/01_python/03_string_file/data/example.txt << 'EOF'
这是第一行
这是第二行
这是第三行
Hello World
EOF

# 创建 log.txt
cat > source/01_python/03_string_file/data/log.txt << 'EOF'
2024-01-15 10:30:15 INFO User logged in
2024-01-15 10:31:20 ERROR Database connection failed
2024-01-15 10:32:00 INFO Request completed
EOF

# 创建 config.txt
cat > source/01_python/03_string_file/data/config.txt << 'EOF'
# 应用配置
API_KEY=your_api_key
MODEL=gpt-4
MAX_TOKENS=1000
EOF

# 创建 4 个练习用的 .py 文件
touch source/01_python/03_string_file/string_advanced.py
touch source/01_python/03_string_file/file_io.py
touch source/01_python/03_string_file/pathlib_basics.py
touch source/01_python/03_string_file/json_basics.py
```

然后就可以打开文档，从第 2 章开始，照着往 `string_advanced.py` 里敲代码了。

---

## 学习顺序总结

| 顺序 | 文档章节 | 练习文件 | 需要提前准备 |
|-----|---------|---------|------------|
| 1 | 第 2 章：字符串进阶 | `string_advanced.py` | 无 |
| 2 | 第 3 章：文件读写 | `file_io.py` | `data/example.txt`、`data/log.txt`、`data/config.txt` |
| 3 | 第 4 章：路径处理 | `pathlib_basics.py` | 无 |
| 4 | 第 5 章：JSON 处理 | `json_basics.py` | 无 |
