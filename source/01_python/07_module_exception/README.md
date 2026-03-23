# 第 7 节练习：模块、包与异常处理（参考实现）

> 这是**参考答案**，完整可运行。建议先在旁边的 `07_module_exception_practice/` 中自己动手实现，卡住了再来这里对照。

## 目录结构

```
07_module_exception/
├── main.py                     # 入口文件（交互式菜单，运行所有演示）
├── .env.example                # 环境变量模板
├── README.md
│
├── config/                     # 配置包
│   ├── __init__.py             # 统一导出
│   ├── exceptions.py           # 自定义异常层次
│   ├── enums.py                # 枚举（TaskStatus / ModelProvider）
│   └── env_manager.py          # 环境变量管理
│
└── utils/                      # 工具包
    ├── __init__.py             # 统一导出
    ├── calculator.py           # 四则运算（跨包导入 config.exceptions）
    ├── json_helper.py          # JSON 读写工具
    └── datetime_helper.py      # 日期时间工具
```

## 包间引用关系

```
main.py
  ├── 导入 config 包（枚举、异常、配置管理）
  └── 导入 utils 包（计算器、JSON、日期时间）

utils/calculator.py  ──跨包导入──→  config/exceptions.py
utils/json_helper.py ──跨包导入──→  config/exceptions.py

config/env_manager.py ──包内导入──→  config/exceptions.py
config/env_manager.py ──包内导入──→  config/enums.py
```

## 运行方式

### 1. 准备环境

```bash
# 进入练习目录
cd source/01_python/07_module_exception

# 安装依赖（python-dotenv）
pip install python-dotenv

# 复制环境变量模板
cp .env.example .env
# 编辑 .env，填入真实的 API Key（可选，演示5需要）
```

### 2. 运行入口文件

```bash
# 必须在 07_module_exception/ 目录下运行
python main.py
```

运行后会显示交互式菜单，可选择运行单个演示或全部运行。

### 3. 单独运行某个模块

每个模块都有 `if __name__ == "__main__"` 保护，可以单独测试。

但因为跨包导入的原因，**必须在 `07_module_exception/` 目录下**用 `-m` 运行：

```bash
# 正确方式
python -m config.exceptions    # 测试异常
python -m config.enums         # 测试枚举
python -m config.env_manager   # 测试环境变量管理
python -m utils.calculator     # 测试计算器
python -m utils.json_helper    # 测试 JSON 工具
python -m utils.datetime_helper # 测试日期时间工具
```

```bash
# ❌ 错误方式（跨包导入会失败）
python config/exceptions.py
python utils/calculator.py
```

## 学习要点

### 核心知识点

1. **包内导入**：`env_manager.py` 导入同包的 `exceptions.py` 和 `enums.py`
2. **跨包导入**：`calculator.py`（utils 包）导入 `config.exceptions` 的异常类
3. **顶层导入**：`main.py` 从两个包导入并使用
4. **`__init__.py` 的作用**：统一导出，简化外部导入路径

### 关键对比

| 导入方式 | 示例 | 场景 |
|---------|------|------|
| 绝对导入 | `from config.exceptions import AppError` | 跨包、入口文件 |
| 包内导入 | `from config.enums import ModelProvider` | 同包内模块互引 |
| 通过 `__init__.py` | `from config import AppError` | 外部简化导入 |

## 如何在 VS Code 中创建 Python 包

**方法一：Python 扩展（推荐）**

1. 在资源管理器中右键点击目标目录
2. 选择 **"New Python Package"**（需要安装 `ms-python.python` 扩展）
3. 输入包名（如 `utils`）
4. VS Code 自动创建目录 + `__init__.py`

**方法二：手动创建**

1. 新建文件夹（如 `utils/`）
2. 在其中创建空的 `__init__.py` 文件

## 自己动手

旁边的 `07_module_exception_practice/` 是空的练习目录，有详细的分步指引，建议先自己实现一遍。

## 扩展练习

完成代码中标注了 `TODO` 的扩展练习：

- `config/exceptions.py`：添加 `AuthError` 和 `RateLimitError`
- `config/enums.py`：添加 `LogLevel` 枚举
