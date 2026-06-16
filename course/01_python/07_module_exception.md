# 07. 模块、包与异常处理

> 本节目标：掌握模块导入、包结构、常用标准库、环境变量管理、枚举和异常处理

---

## 1. 概述

### 学习目标

- 掌握 import 的三种导入形式
- 理解包（Package）的结构和 `__init__.py` 的作用
- 掌握常用标准库（os、json、datetime、collections）
- 掌握环境变量管理（python-dotenv）
- 掌握枚举 Enum 的定义和使用
- 掌握异常处理和自定义异常

### 预计学习时间

- 模块与包：1.5 小时
- 常用标准库：1-1.5 小时
- 环境变量管理：30 分钟
- 枚举：30 分钟
- 异常处理：1 小时
- 练习：1-2 小时

### 本节在 AI 应用中的重要性

| 场景 | 相关知识 |
|-----|---------|
| API Key 管理 | 环境变量、python-dotenv、.env 文件 |
| LLM API 响应解析 | json 模块 |
| 对话历史时间戳 | datetime 模块 |
| 统计 Token 使用 | collections.Counter |
| 模型/状态选择 | Enum 枚举 |
| API 调用错误处理 | try/except、自定义异常 |
| 项目代码组织 | 模块、包、__init__.py |

---

## 2. 模块（import） 📌

> 模块就是一个 `.py` 文件。Python 的模块系统类似 JavaScript 的 ESM（import/export），但语法和机制有差异。

### 2.1 三种导入形式

```python
# 形式一：导入整个模块
import json

data = json.dumps({"name": "张三"})


# 形式二：从模块导入特定内容
from json import dumps, loads

data = dumps({"name": "张三"})


# 形式三：导入并重命名（别名）
import datetime as dt
from collections import Counter as C

now = dt.datetime.now()
```

### 2.2 `__name__ == "__main__"`

每个 Python 文件都有一个 `__name__` 属性：
- 直接运行时：`__name__` 等于 `"__main__"`
- 被其他文件导入时：`__name__` 等于模块名

```python
# calculator.py

def add(a: float, b: float) -> float:
    return a + b

def subtract(a: float, b: float) -> float:
    return a - b

# 只有直接运行 calculator.py 时才执行
# 被 import 时不会执行
if __name__ == "__main__":
    print(add(3, 5))
    print(subtract(10, 4))
```

> **与 JS 对比**：JS 没有这个机制。Python 的 `if __name__ == "__main__"` 让同一个文件既能当模块被导入，又能直接运行测试。

### 2.3 模块搜索路径

Python 查找模块的顺序：

1. 当前目录
2. 环境变量 `PYTHONPATH` 指定的目录
3. 标准库目录
4. 第三方包目录（site-packages）

```python
import sys

# 查看搜索路径
for path in sys.path:
    print(path)
```

---

## 3. 包（Package） 📌

> 包是包含 `__init__.py` 的目录，用于组织多个模块。类似 JS 中一个文件夹 + `index.js` 的结构。

### 3.1 包的目录结构

```
my_project/
├── main.py
├── utils/                # 包
│   ├── __init__.py       # 包标识文件（类似 index.js）
│   ├── calculator.py     # 模块
│   └── json_helper.py    # 模块
└── config/               # 另一个包
    ├── __init__.py
    ├── enums.py
    └── exceptions.py
```

### 3.2 `__init__.py` 的作用

`__init__.py` 有两个作用：
1. **标识目录为包**（Python 3.3+ 不是严格必须，但强烈建议保留）
2. **控制包的导出内容**（类似 JS 的 `index.js` 统一导出）

```python
# utils/__init__.py

# 方式一：空文件（最简单）
# 使用时：from utils.calculator import add

# 方式二：统一导出（推荐）
from utils.calculator import add, subtract, multiply, divide
from utils.json_helper import save_json, load_json

# 使用时可以直接：from utils import add, save_json
```

> **如何在 VS Code 中创建 Python 包：**
>
> **方法一：VS Code Python 扩展（推荐）**
> 1. 在资源管理器中右键点击目标目录
> 2. 选择 **"New Python Package"**（需要安装 Python 扩展 `ms-python.python`）
> 3. 输入包名（如 `utils`）
> 4. VS Code 自动创建目录和 `__init__.py` 文件
>
> **方法二：手动创建**
> 1. 新建文件夹（如 `utils/`）
> 2. 在其中创建一个空的 `__init__.py` 文件

### 3.3 导入包中的模块

```python
# 假设目录结构：
# project/
# ├── main.py
# ├── utils/
# │   ├── __init__.py
# │   └── calculator.py
# └── config/
#     ├── __init__.py
#     └── exceptions.py

# --- main.py 中的导入方式 ---

# 绝对导入（推荐）
from utils.calculator import add
from config.exceptions import AppError

# 导入整个模块
from utils import calculator
result = calculator.add(3, 5)
```

### 3.4 相对导入 vs 绝对导入

```python
# config/env_manager.py

# 绝对导入：从项目根目录开始
from config.exceptions import ConfigError
from config.enums import ModelProvider

# 相对导入：用 . 表示当前包
from .exceptions import ConfigError      # . 表示当前包（config/）
from .enums import ModelProvider

# .. 表示上一级（不常用，容易出错）
# from ..utils.calculator import add
```

| 方式 | 语法 | 优点 | 缺点 |
|------|------|------|------|
| 绝对导入 | `from config.exceptions import X` | 清晰、不易出错 | 包名变了要全部改 |
| 相对导入 | `from .exceptions import X` | 包内重构方便 | 不能直接运行文件 |

> **建议**：优先用绝对导入，结构清晰。相对导入在包内部使用也可以。

### 3.5 跨包导入

不同包之间互相引用是实际项目中最常见的场景：

```python
# utils/calculator.py 导入 config 包的异常类

from config.exceptions import CalculationError

def divide(a: float, b: float) -> float:
    if b == 0:
        raise CalculationError("除数不能为零")
    return a / b
```

> **关键**：跨包导入时，Python 从**项目根目录**（即运行 `python` 命令的目录）开始查找。所以必须在正确的目录下运行代码。

---

## 4. 常用标准库 📌

### 4.1 os 模块

```python
import os

# 环境变量
api_key = os.getenv("OPENAI_API_KEY")         # 不存在返回 None
api_key = os.getenv("OPENAI_API_KEY", "默认值") # 不存在返回默认值
os.environ["MY_VAR"] = "value"                  # 设置环境变量

# 路径操作（简单场景用 os.path，复杂场景用 pathlib）
os.path.exists("file.txt")          # 文件是否存在
os.path.join("data", "output.json") # 拼接路径
os.getcwd()                          # 当前工作目录
os.listdir(".")                      # 列出目录内容

# 目录操作
os.makedirs("data/output", exist_ok=True)  # 递归创建目录
```

### 4.2 json 模块 📌

```python
import json

# Python 对象 → JSON 字符串
data = {"name": "张三", "age": 25, "scores": [85, 92, 78]}
json_str = json.dumps(data, ensure_ascii=False, indent=2)
print(json_str)
# {
#   "name": "张三",
#   "age": 25,
#   "scores": [85, 92, 78]
# }

# JSON 字符串 → Python 对象
parsed = json.loads(json_str)
print(parsed["name"])  # "张三"


# 读写 JSON 文件
# 写入
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# 读取
with open("data.json", "r", encoding="utf-8") as f:
    loaded = json.load(f)
```

> **`ensure_ascii=False`**：不加的话中文会被转义成 `\u5f20\u4e09`。AI 应用处理中文数据时务必加上。

| 函数 | 用途 | 输入/输出 |
|------|------|----------|
| `json.dumps()` | 序列化为字符串 | dict → str |
| `json.loads()` | 从字符串反序列化 | str → dict |
| `json.dump()` | 序列化并写入文件 | dict → file |
| `json.load()` | 从文件读取并反序列化 | file → dict |

### 4.3 datetime 模块

```python
from datetime import datetime, timedelta, date

# 当前时间
now = datetime.now()
print(now)                          # 2026-03-23 14:30:00.123456
print(now.isoformat())              # 2026-03-23T14:30:00.123456

# 格式化输出
print(now.strftime("%Y-%m-%d %H:%M:%S"))  # 2026-03-23 14:30:00
print(now.strftime("%Y年%m月%d日"))         # 2026年03月23日

# 从字符串解析
dt = datetime.strptime("2026-01-15 10:30:00", "%Y-%m-%d %H:%M:%S")

# 时间计算
tomorrow = now + timedelta(days=1)
one_hour_ago = now - timedelta(hours=1)

# 两个日期的差
d1 = date(2026, 1, 1)
d2 = date(2026, 3, 23)
diff = d2 - d1
print(f"相差 {diff.days} 天")  # 相差 81 天

# UTC 时间（推荐在 API 场景使用）
from datetime import timezone
utc_now = datetime.now(timezone.utc)
```

### 4.4 random 模块

```python
import random

random.random()              # 0-1 随机浮点数
random.randint(1, 100)       # 1-100 随机整数
random.choice(["a", "b"])    # 随机选一个
random.sample([1,2,3,4,5], 3) # 随机选 3 个（不重复）
random.shuffle([1,2,3,4,5])   # 原地打乱列表
```

### 4.5 collections 模块

```python
from collections import Counter, defaultdict

# Counter：计数器
words = ["apple", "banana", "apple", "cherry", "banana", "apple"]
counter = Counter(words)
print(counter)                    # Counter({'apple': 3, 'banana': 2, 'cherry': 1})
print(counter.most_common(2))     # [('apple', 3), ('banana', 2)]

# AI 场景：统计 Token 使用
token_usage = Counter()
token_usage["input"] += 500
token_usage["output"] += 300
token_usage["input"] += 200
print(token_usage)  # Counter({'input': 700, 'output': 300})
print(f"总 Token：{sum(token_usage.values())}")  # 1000


# defaultdict：带默认值的字典
# 普通 dict 访问不存在的 key 会报错，defaultdict 会自动创建
scores = defaultdict(list)
scores["张三"].append(85)  # 自动创建 key "张三"，值为空列表
scores["张三"].append(92)
scores["李四"].append(78)
print(dict(scores))  # {'张三': [85, 92], '李四': [78]}

# 计数
word_count = defaultdict(int)
for word in ["hello", "world", "hello"]:
    word_count[word] += 1
print(dict(word_count))  # {'hello': 2, 'world': 1}
```

---

## 5. 环境变量与配置管理 📌 🔗

### 5.1 为什么需要环境变量

API Key、数据库密码等敏感信息**不能硬编码在代码中**。正确做法是通过环境变量传入。

```python
# ❌ 硬编码（绝对不要这样做）
api_key = "sk-1234567890abcdef"

# ✅ 从环境变量读取
import os
api_key = os.getenv("OPENAI_API_KEY")
```

### 5.2 python-dotenv

`python-dotenv` 从 `.env` 文件加载环境变量，开发时不需要手动 `export`。

```bash
# 安装
pip install python-dotenv
```

**创建 `.env` 文件**（项目根目录）：

```
# .env — 这个文件不提交到 git！
OPENAI_API_KEY=sk-your-real-key-here
MODEL_NAME=gpt-4o-mini
TEMPERATURE=0.7
DEBUG=true
```

**创建 `.env.example` 文件**（提交到 git，作为模板）：

```
# .env.example — 配置模板，不含真实密钥
OPENAI_API_KEY=your-api-key-here
MODEL_NAME=gpt-4o-mini
TEMPERATURE=0.7
DEBUG=false
```

**在代码中加载**：

```python
from dotenv import load_dotenv
import os

# 加载 .env 文件中的变量到环境
load_dotenv()

# 读取
api_key = os.getenv("OPENAI_API_KEY")
model = os.getenv("MODEL_NAME", "gpt-4o-mini")  # 有默认值
temperature = float(os.getenv("TEMPERATURE", "0.7"))
debug = os.getenv("DEBUG", "false").lower() == "true"
```

### 5.3 配置管理最佳实践

```python
from dotenv import load_dotenv
import os


def get_config() -> dict:
    """加载并验证配置"""
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("缺少必要配置：OPENAI_API_KEY，请在 .env 文件中设置")

    return {
        "api_key": api_key,
        "model": os.getenv("MODEL_NAME", "gpt-4o-mini"),
        "temperature": float(os.getenv("TEMPERATURE", "0.7")),
    }
```

### 5.4 .gitignore 中忽略 .env

```
# .gitignore
.env
.env.local
.env.*.local
```

> **记住**：`.env` 包含真实密钥，绝不提交。`.env.example` 包含占位符，应该提交。

---

## 6. 枚举 Enum ⚡

### 6.1 基础 Enum

```python
from enum import Enum


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# 使用
status = TaskStatus.PENDING
print(status)        # TaskStatus.PENDING
print(status.value)  # "pending"
print(status.name)   # "PENDING"

# 比较
if status == TaskStatus.PENDING:
    print("任务待处理")

# 从值创建
status = TaskStatus("completed")
print(status)  # TaskStatus.COMPLETED

# 遍历
for s in TaskStatus:
    print(f"{s.name} = {s.value}")
```

### 6.2 字符串枚举（StrEnum）

```python
# Python 3.11+ 推荐使用 StrEnum
from enum import StrEnum


class ModelProvider(StrEnum):
    OPENAI = "openai"
    CLAUDE = "claude"
    DEEPSEEK = "deepseek"


# StrEnum 的好处：枚举值可以直接当字符串用
provider = ModelProvider.OPENAI
print(f"当前模型：{provider}")   # "当前模型：openai"
print(provider == "openai")      # True（可以和字符串比较）
```

> **注意版本差异**：
> - Python 3.11+：用 `StrEnum`（推荐）
> - Python 3.10 及以下：用 `class X(str, Enum)` 写法
> - 在 Python 3.11+ 中，旧写法 `str + Enum` 的 `str()` 行为已变更（`str(X.A)` 返回 `"X.A"` 而非值），所以推荐统一用 `StrEnum`

### 6.3 AI 应用场景

```python
from enum import StrEnum


class ModelProvider(StrEnum):
    OPENAI = "openai"
    CLAUDE = "claude"
    DEEPSEEK = "deepseek"


def get_api_base_url(provider: ModelProvider) -> str:
    urls = {
        ModelProvider.OPENAI: "https://api.openai.com/v1",
        ModelProvider.CLAUDE: "https://api.anthropic.com",
        ModelProvider.DEEPSEEK: "https://api.deepseek.com",
    }
    return urls[provider]


url = get_api_base_url(ModelProvider.DEEPSEEK)
print(url)  # "https://api.deepseek.com"
```

> **为什么用 Enum 而不是普通字符串？**
> - 防拼写错误（IDE 有自动补全）
> - 值受限（不会出现 `"opanai"` 这种 typo）
> - 代码可读性更好

---

## 7. 异常处理 📌

### 7.1 try / except 基础

```python
# 基础语法
try:
    result = 10 / 0
except ZeroDivisionError:
    print("不能除以零")


# 捕获异常信息
try:
    result = int("abc")
except ValueError as e:
    print(f"转换失败：{e}")  # "转换失败：invalid literal for int() with base 10: 'abc'"


# 捕获多种异常
try:
    data = {"key": "value"}
    print(data["missing"])
except KeyError:
    print("键不存在")
except TypeError:
    print("类型错误")
except Exception as e:
    print(f"未知错误：{e}")
```

### 7.2 else 和 finally

```python
try:
    result = 10 / 2
except ZeroDivisionError:
    print("除零错误")
else:
    # 没有异常时执行
    print(f"结果：{result}")
finally:
    # 无论是否异常都执行
    print("执行完毕")
```

> **与 JS 对比**：Python 多了 `else` 分支（JS 的 try/catch/finally 没有 else）。

### 7.3 常见异常类型

| 异常 | 触发场景 | 示例 |
|------|---------|------|
| `ValueError` | 值不合法 | `int("abc")` |
| `TypeError` | 类型不对 | `"hello" + 123` |
| `KeyError` | 字典键不存在 | `{}["missing"]` |
| `IndexError` | 索引越界 | `[1,2,3][10]` |
| `FileNotFoundError` | 文件不存在 | `open("不存在.txt")` |
| `ZeroDivisionError` | 除以零 | `1 / 0` |
| `AttributeError` | 属性不存在 | `None.method()` |
| `ImportError` | 导入失败 | `import 不存在的模块` |
| `ConnectionError` | 网络连接失败 | API 调用超时 |
| `TimeoutError` | 超时 | 请求超时 |

### 7.4 raise 主动抛出异常

```python
def set_temperature(value: float) -> None:
    if not 0 <= value <= 2:
        raise ValueError(f"temperature 必须在 0-2 之间，当前值：{value}")
    print(f"设置 temperature = {value}")


try:
    set_temperature(3.0)
except ValueError as e:
    print(f"参数错误：{e}")
```

### 7.5 自定义异常

```python
# 定义异常层次
class AppError(Exception):
    """应用基础异常"""
    def __init__(self, message: str, code: int = 500):
        super().__init__(message)
        self.code = code


class ConfigError(AppError):
    """配置错误"""
    def __init__(self, key: str):
        super().__init__(f"缺少必要配置：{key}", code=400)
        self.key = key


class CalculationError(AppError):
    """计算错误"""
    def __init__(self, message: str):
        super().__init__(message, code=422)


# 使用
def get_api_key() -> str:
    import os
    key = os.getenv("API_KEY")
    if not key:
        raise ConfigError("API_KEY")
    return key

try:
    key = get_api_key()
except ConfigError as e:
    print(f"[{e.code}] {e}（缺少 key: {e.key}）")
except AppError as e:
    print(f"[{e.code}] 应用错误：{e}")
```

> **异常层次设计原则**：
> - 定义一个基础异常（如 `AppError`），所有自定义异常继承它
> - 调用方可以 `except AppError` 捕获所有应用异常
> - 也可以 `except ConfigError` 只捕获特定异常

---

## 8. 小结

### 核心知识

| 知识点 | 优先级 | 一句话总结 |
|--------|-------|-----------|
| import 三种形式 | 📌 | `import X` / `from X import Y` / `import X as Z` |
| 包与 `__init__.py` | 📌 | 目录 + `__init__.py` = 包，`__init__.py` 控制导出 |
| json 模块 | 📌 | `dumps`/`loads`（字符串）、`dump`/`load`（文件），中文加 `ensure_ascii=False` |
| datetime 模块 | 📌 | `datetime.now()`、`strftime` 格式化、`timedelta` 时间计算 |
| 环境变量 / dotenv | 📌🔗 | `.env` 存密钥不提交 git，`.env.example` 做模板提交 |
| Enum 枚举 | ⚡ | 限定值范围，防拼写错误，`str + Enum` 可直接当字符串用 |
| try / except | 📌 | 捕获异常，`as e` 获取信息，`finally` 必定执行 |
| 自定义异常 | 📌 | 继承 Exception，设计异常层次，基类 + 子类 |

### 与 JavaScript 关键差异

| 差异点 | JavaScript | Python |
|--------|-----------|--------|
| 模块系统 | ESM: `import { add } from './calc.js'` | `from calc import add` |
| 默认导出 | `export default` | 无（用 `__init__.py` 控制） |
| 包标识 | `package.json` | `__init__.py` |
| 错误捕获 | `try { } catch(e) { }` | `try: ... except Exception as e:` |
| 错误类型 | `if (e instanceof TypeError)` | `except TypeError as e:` |
| else 分支 | 无 | `try → except → else → finally` |
| 枚举 | `const Status = { ... } as const` (TS) | `class Status(Enum)` |
| 环境变量 | `process.env.KEY` / `dotenv` | `os.getenv("KEY")` / `python-dotenv` |

### 下一节预告

下一节将进入 **综合练习：任务管理器**，把前面学到的所有知识整合：
- 类与 dataclass
- 模块与包
- JSON 文件持久化
- 异常处理
- 枚举状态管理

---

## 9. 常见问题

### Q: import 和 from...import 有什么区别？

```python
# import json — 导入模块，通过 json.xxx 访问
import json
json.dumps(...)

# from json import dumps — 直接导入函数，不需要前缀
from json import dumps
dumps(...)
```

一般原则：
- 标准库（json、os、datetime）习惯用 `import json`
- 第三方库中的特定类/函数习惯用 `from X import Y`
- 避免 `from X import *`（污染命名空间）

### Q: `__init__.py` 可以是空文件吗？

可以。空的 `__init__.py` 只起"标识这是一个包"的作用。但推荐在里面写导出语句，简化外部导入：

```python
# config/__init__.py
from config.exceptions import AppError, ConfigError
from config.enums import TaskStatus, ModelProvider

# 外部就可以：from config import AppError, TaskStatus
# 而不需要：from config.exceptions import AppError
```

### Q: 相对导入报错 "attempted relative import beyond top-level package"？

这通常是因为你直接运行了包内的文件。相对导入只能在**包的上下文中**使用：

```bash
# ❌ 直接运行包内文件（相对导入会失败）
python config/env_manager.py

# ✅ 从项目根目录运行入口文件
python main.py

# ✅ 或者用 -m 标志运行模块
python -m config.env_manager
```

### Q: .env 文件中的值都是字符串？

是的。`os.getenv()` 返回的都是字符串，数字和布尔值需要手动转换：

```python
# .env 中：TEMPERATURE=0.7, DEBUG=true

temperature = float(os.getenv("TEMPERATURE", "0.7"))
debug = os.getenv("DEBUG", "false").lower() == "true"
max_tokens = int(os.getenv("MAX_TOKENS", "1000"))
```

### Q: except Exception 和 except BaseException 有什么区别？

- `except Exception`：捕获所有常规异常（推荐）
- `except BaseException`：连 `KeyboardInterrupt`（Ctrl+C）和 `SystemExit` 也捕获（不推荐）

```python
# 推荐：用户 Ctrl+C 可以正常退出
try:
    ...
except Exception as e:
    print(f"错误：{e}")

# 不推荐：Ctrl+C 也被吞掉了
try:
    ...
except BaseException:
    pass
```

### Q: 什么时候该自定义异常，什么时候用内置异常？

- **参数验证失败**：用 `ValueError`（内置够用）
- **业务逻辑错误**（如余额不足、配置缺失）：自定义异常（更语义化）
- **需要附加信息**（如错误码、字段名）：自定义异常
