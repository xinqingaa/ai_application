# 07. 模块、包与异常处理 - 实践指南

> 本文档说明如何跟着 [学习文档](../../../docs/01_python/07_module_exception.md) 一步步动手操作

---

## 核心原则

```
读文档 → 看对应代码 → 运行验证 → 理解原理
```

- 所有操作在 `source/01_python/07_module_exception/` 目录下进行
- 本章代码已经写好，是一个完整的多包项目，重点在于**理解文档概念如何落地到代码结构**
- 每个文档章节对应项目中的具体文件，按顺序阅读和运行

---

## 项目结构

```
07_module_exception/
├── README.md                ← 你正在读的这个文件
├── main.py                  ← 入口文件：交互式菜单，运行所有演示
├── .env.example             ← 环境变量模板
│
├── config/                  ← 配置包
│   ├── __init__.py          ← 统一导出（文档 3.2 节）
│   ├── exceptions.py        ← 自定义异常（文档 7.5 节）
│   ├── enums.py             ← 枚举定义（文档第 6 章）
│   └── env_manager.py       ← 环境变量管理（文档第 5 章）
│
└── utils/                   ← 工具包
    ├── __init__.py          ← 统一导出（文档 3.2 节）
    ├── calculator.py        ← 四则运算，跨包导入异常（文档 3.5 节）
    ├── json_helper.py       ← JSON 读写（文档 4.2 节）
    └── datetime_helper.py   ← 日期时间（文档 4.3 节）
```

---

## 前置准备

### 1. 安装依赖

```bash
pip install python-dotenv
```

### 2. 准备环境变量文件

```bash
cd source/01_python/07_module_exception
cp .env.example .env
```

编辑 `.env`，填入你的 API Key（测试用，随便填一个就行）。

### 3. 运行方式

**所有命令都必须在 `07_module_exception/` 目录下执行。**

```bash
cd source/01_python/07_module_exception

# 方式一：运行入口文件（交互式菜单）
python main.py

# 方式二：单独测试某个模块
python -m config.exceptions     # 测试异常
python -m config.enums          # 测试枚举
python -m config.env_manager    # 测试环境变量
python -m utils.calculator      # 测试计算器
python -m utils.json_helper     # 测试 JSON 工具
python -m utils.datetime_helper # 测试日期时间
```

> 注意：不能用 `python config/exceptions.py` 这种方式运行，跨包导入会失败。必须用 `python -m` 或通过 `main.py` 入口运行。

---

## 第 1 步：模块与 import（文档第 2 章）

### 对应文档

文档第 2 章「模块（import）」讲了三种导入形式和 `__name__ == "__main__"`。

### 操作流程

1. 读文档 2.1 节「三种导入形式」

2. 打开 `main.py` 第 13-25 行，看顶部的导入部分：

```python
# 这是「形式二：从模块导入特定内容」+ __init__.py 统一导出的效果
from config import AppError, ConfigError, CalculationError, TaskStatus, ModelProvider
from utils import add, subtract, multiply, divide
```

3. 读文档 2.2 节「`__name__ == "__main__"`」

4. 打开任意一个模块文件（如 `utils/calculator.py`），看底部：

```python
if __name__ == "__main__":
    # 直接运行此文件时才执行
    print("=== 四则运算测试 ===")
    ...
```

5. 读文档 2.3 节「模块搜索路径」

6. 运行查看搜索路径：

```bash
python -c "import sys; [print(p) for p in sys.path]"
```

---

## 第 2 步：包与 `__init__.py`（文档第 3 章）

### 对应文档

文档第 3 章「包（Package）」讲包结构、`__init__.py`、跨包导入。

### 操作流程

1. 读文档 3.1-3.2 节「包的目录结构和 `__init__.py`」

2. 打开 `config/__init__.py`，理解它做了什么：

```python
# 把子模块的内容统一导出，外部可以直接 from config import AppError
from config.exceptions import AppError, ConfigError, CalculationError
from config.enums import TaskStatus, ModelProvider
```

对比 `utils/__init__.py` 做了同样的事情。

3. 读文档 3.3-3.4 节「导入包中的模块」和「相对导入 vs 绝对导入」

4. 打开 `config/env_manager.py`，看它的导入方式（包内导入）：

```python
from config.exceptions import ConfigError   # 绝对导入
from config.enums import ModelProvider       # 绝对导入
```

5. 读文档 3.5 节「跨包导入」

6. 打开 `utils/calculator.py`，看跨包导入：

```python
from config.exceptions import CalculationError  # utils 包导入 config 包的异常类
```

同样 `utils/json_helper.py` 也跨包导入了 `config.exceptions.AppError`。

7. 打开 `main.py`，看顶层导入——从两个包导入并使用。

**包间引用关系图**：

```
main.py
  ├── from config import ...        ← 通过 __init__.py 统一导出
  └── from utils import ...         ← 通过 __init__.py 统一导出

utils/calculator.py  ──跨包──→  config/exceptions.py
utils/json_helper.py ──跨包──→  config/exceptions.py

config/env_manager.py ──包内──→  config/exceptions.py
config/env_manager.py ──包内──→  config/enums.py
```

---

## 第 3 步：常用标准库（文档第 4 章）

### 对应文档

文档第 4 章讲了 os、json、datetime、random、collections。

### 操作流程

1. 读文档 4.1 节「os 模块」，打开 `config/env_manager.py` 看 `os.getenv` 的实际使用

2. 读文档 4.2 节「json 模块」，打开 `utils/json_helper.py` 看完整的 JSON 读写封装：

```python
# save_json: json.dump() 写入文件，ensure_ascii=False 处理中文
# load_json: json.load() 读取文件，带异常处理
```

3. 运行 JSON 工具测试：

```bash
python -m utils.json_helper
```

4. 读文档 4.3 节「datetime 模块」，打开 `utils/datetime_helper.py` 看实际使用：

```python
# get_timestamp(): datetime.now(timezone.utc).isoformat()
# time_ago(): timedelta 计算相对时间
# format_datetime(): strftime 格式化输出
```

5. 运行日期时间测试：

```bash
python -m utils.datetime_helper
```

6. 读文档 4.5 节「collections 模块」（Counter、defaultdict），这部分文档中的示例可以直接在 Python 交互模式中敲：

```bash
python
>>> from collections import Counter, defaultdict
>>> Counter(["apple", "banana", "apple"])
Counter({'apple': 2, 'banana': 1})
>>> exit()
```

---

## 第 4 步：环境变量与配置管理（文档第 5 章）

### 对应文档

文档第 5 章「环境变量与配置管理」，这是 AI 应用中管理 API Key 的核心方式。

### 操作流程

1. 读文档 5.1 节「为什么需要环境变量」

2. 查看 `.env.example` 文件内容（模板，可以提交 git）

3. 查看你刚创建的 `.env` 文件（真实配置，不提交 git）

4. 读文档 5.2 节「python-dotenv」，打开 `config/env_manager.py` 看：

```python
from dotenv import load_dotenv
load_dotenv()                    # 加载 .env 文件
api_key = os.getenv("API_KEY")   # 读取环境变量
```

5. 读文档 5.3 节「配置管理最佳实践」，对比 `env_manager.py` 中的 `get_config()` 函数

6. 运行环境变量测试（确保 `.env` 文件存在）：

```bash
python -m config.env_manager
```

7. 读文档 5.4 节「.gitignore 中忽略 .env」

**关键理解**：
- `.env` = 真实密钥，**绝不提交 git**
- `.env.example` = 配置模板，**应该提交 git**
- `os.getenv()` 返回的都是字符串，数字和布尔值需要手动转换

---

## 第 5 步：枚举 Enum（文档第 6 章）

### 对应文档

文档第 6 章「枚举 Enum」。

### 操作流程

1. 读文档 6.1 节「基础 Enum」

2. 打开 `config/enums.py`，看 `TaskStatus` 的定义和使用

3. 读文档 6.2 节「字符串枚举 StrEnum」，对比 `enums.py` 中的写法：

```python
from enum import StrEnum

class TaskStatus(StrEnum):
    PENDING = "pending"
    # StrEnum 的好处：可以直接和字符串比较
    # status == "pending" → True
```

4. 读文档 6.3 节「AI 应用场景」，看 `ModelProvider` 的 `get_api_base_url()` 方法

5. 运行枚举测试：

```bash
python -m config.enums
```

---

## 第 6 步：异常处理（文档第 7 章）

### 对应文档

文档第 7 章「异常处理」。

### 操作流程

1. 读文档 7.1-7.2 节「try/except 基础」和「else 和 finally」

2. 读文档 7.4 节「raise 主动抛出异常」

3. 读文档 7.5 节「自定义异常」，打开 `config/exceptions.py` 看异常层次：

```
Exception
└── AppError           （应用基础异常）
    ├── ConfigError    （配置错误，code=400）
    └── CalculationError（计算错误，code=422）
```

4. 运行异常测试：

```bash
python -m config.exceptions
```

5. 看异常在项目中的实际使用：
   - `utils/calculator.py` 第 32-33 行：`raise CalculationError("除数不能为零")`
   - `utils/calculator.py` 第 40-42 行：`except CalculationError` 捕获
   - `utils/json_helper.py` 第 31 行：`raise AppError(...) from e` 异常链
   - `config/env_manager.py` 第 50 行：`raise ConfigError(key)` 配置缺失

6. 运行完整项目，看所有演示：

```bash
python main.py
# 输入 a 运行全部演示
```

---

## 文档章节与项目文件对应表

| 文档章节 | 核心内容 | 对应项目文件 |
|---------|---------|------------|
| 第 2 章：模块 | import 三种形式、`__name__` | 所有文件的顶部 import 和底部 `if __name__` |
| 第 3 章：包 | `__init__.py`、跨包导入 | `config/__init__.py`、`utils/__init__.py`、`utils/calculator.py`（跨包导入） |
| 第 4 章：标准库 | json、datetime、os | `utils/json_helper.py`、`utils/datetime_helper.py`、`config/env_manager.py` |
| 第 5 章：环境变量 | dotenv、.env | `config/env_manager.py`、`.env.example` |
| 第 6 章：枚举 | Enum、StrEnum | `config/enums.py` |
| 第 7 章：异常处理 | try/except、自定义异常 | `config/exceptions.py`、`utils/calculator.py` |

---

## 学习顺序总结

| 顺序 | 文档章节 | 重点理解 | 运行命令 |
|-----|---------|---------|---------|
| 1 | 第 2-3 章 | import、包、`__init__.py`、跨包导入 | `python -m utils.calculator` |
| 2 | 第 4 章 | json 读写、datetime 格式化 | `python -m utils.json_helper` / `python -m utils.datetime_helper` |
| 3 | 第 5 章 | .env 文件、python-dotenv | `python -m config.env_manager` |
| 4 | 第 6 章 | StrEnum 定义和使用 | `python -m config.enums` |
| 5 | 第 7 章 | 自定义异常层次、异常捕获顺序 | `python -m config.exceptions` |
| 6 | 综合 | 所有知识点串联 | `python main.py`（输入 a 运行全部） |

---

## 注意事项

- **运行目录**：必须在 `07_module_exception/` 目录下运行，否则跨包导入会失败
- **python-dotenv**：必须安装（`pip install python-dotenv`），否则 `env_manager.py` 会跳过
- **`.env` 文件**：需要从 `.env.example` 复制创建，否则演示 5 会提示配置未完成
- **`__pycache__/`**：运行后会自动生成，是 Python 的编译缓存，不用管，不用提交 git
