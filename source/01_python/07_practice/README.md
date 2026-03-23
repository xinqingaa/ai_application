# 第 7 节练习（手动实现版）

> 这是你自己动手实现的文件夹。参考答案在旁边的 `07_module_exception/` 中，**先自己写，卡住了再去看**。

## 你的目标

从零创建两个 Python 包（`config` 和 `utils`），让它们互相引用，并通过 `main.py` 统一调用。

## 需要创建的目录结构

```
07_module_exception_practice/
├── main.py                     # 入口文件：导入两个包，运行演示
├── .env                        # 环境变量（从 .env.example 复制）
├── .env.example                # 环境变量模板
│
├── config/                     # 配置包（先建这个，它是基础）
│   ├── __init__.py
│   ├── exceptions.py           # 步骤1：自定义异常
│   ├── enums.py                # 步骤2：枚举定义
│   └── env_manager.py          # 步骤3：环境变量管理
│
└── utils/                      # 工具包（依赖 config 包）
    ├── __init__.py
    ├── calculator.py           # 步骤4：四则运算
    ├── json_helper.py          # 步骤5：JSON 读写
    └── datetime_helper.py      # 步骤6：日期时间工具
```

## 如何创建 Python 包

**方法一：VS Code Python 扩展（推荐）**

1. 在左侧资源管理器中，右键点击 `07_module_exception_practice/` 文件夹
2. 选择 **"New Python Package"**（需要安装 `ms-python.python` 扩展）
3. 输入包名 `config`，VS Code 自动创建 `config/` 目录和 `config/__init__.py`
4. 同样操作创建 `utils` 包

**方法二：手动创建**

1. 新建文件夹 `config/`
2. 在 `config/` 中创建空文件 `__init__.py`
3. 同样操作创建 `utils/`

## 实现步骤（建议按顺序）

### 步骤 1：config/exceptions.py — 自定义异常

创建异常继承层次：

```
Exception
└── AppError(message, code=500)        # 基础异常，带错误码
    ├── ConfigError(key)               # 配置缺失，code=400
    └── CalculationError(message)      # 计算错误，code=422
```

要求：
- `AppError` 接收 `message` 和 `code` 参数
- `ConfigError` 接收 `key` 参数，自动拼消息 `"缺少必要配置：{key}"`
- 添加 `if __name__ == "__main__"` 测试代码

### 步骤 2：config/enums.py — 枚举

创建两个枚举：

- `TaskStatus(StrEnum)`：PENDING / IN_PROGRESS / COMPLETED / FAILED
- `ModelProvider(StrEnum)`：OPENAI / CLAUDE / DEEPSEEK / TONGYI
  - 给 `ModelProvider` 加一个 `get_api_base_url()` 方法

提示：`from enum import StrEnum`（Python 3.11+）

### 步骤 3：config/env_manager.py — 环境变量管理

要求：
- 从**同包**导入 `ConfigError` 和 `ModelProvider`（包内导入）
- 实现 `load_env()` 函数：加载 `.env` 文件
- 实现 `get_config()` 函数：返回配置字典，`API_KEY` 缺失时抛 `ConfigError`

依赖：`pip install python-dotenv`

### 步骤 4：utils/calculator.py — 四则运算（跨包导入）

要求：
- 从 **config 包**导入 `CalculationError`（**跨包导入，核心知识点**）
- 实现 `add / subtract / multiply / divide` 四个函数
- `divide` 除零时抛出 `CalculationError`

### 步骤 5：utils/json_helper.py — JSON 读写

要求：
- 实现 `save_json(data, filepath)` 和 `load_json(filepath)`
- 文件不存在或格式错误时抛出 `AppError`

### 步骤 6：utils/datetime_helper.py — 日期时间工具

要求：
- 实现 `format_datetime()` — 格式化当前时间
- 实现 `time_ago(dt)` — 返回 "X 分钟前" 这样的描述
- 实现 `get_timestamp()` — 返回 UTC ISO 格式时间戳

### 步骤 7：__init__.py — 统一导出

在两个包的 `__init__.py` 中统一导出，让外部可以直接：

```python
from config import AppError, ConfigError, TaskStatus, ModelProvider
from utils import add, divide, save_json, format_datetime
```

### 步骤 8：main.py — 入口文件

从两个包导入并演示使用，验证所有导入关系正常。

## 导入关系速查（写代码时参考）

```
config/exceptions.py    → 无依赖（最先写）
config/enums.py         → 无依赖
config/env_manager.py   → 包内导入 config.exceptions + config.enums
utils/calculator.py     → 跨包导入 config.exceptions  ⬅️ 重点
utils/json_helper.py    → 跨包导入 config.exceptions
utils/datetime_helper.py → 无依赖（纯标准库）
main.py                 → 导入 config + utils
```

## 运行方式

```bash
# 必须在 07_module_exception_practice/ 目录下运行
cd source/01_python/07_module_exception_practice

python main.py

# 单独测试某个模块（用 -m 方式）
python -m config.exceptions
python -m utils.calculator
```

```bash
# ❌ 错误方式（跨包导入会失败）
python config/exceptions.py
python utils/calculator.py
```

## 卡住了？

1. 先看文档 `docs/01_python/07_module_exception.md` 对应章节
2. 再看参考实现 `07_module_exception/` 中对应的文件
3. 重点关注 `import` 语句怎么写
