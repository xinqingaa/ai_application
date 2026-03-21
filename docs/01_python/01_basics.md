# 01. 环境搭建与基础语法

> 本节目标：搭建 Python 开发环境，掌握变量、数据类型和控制流基础

---

## 1. 概述

### 学习目标

- 完成虚拟环境配置
- 理解 Python 变量与命名规范
- 掌握五种基本数据类型
- 学会使用类型注解
- 掌握 f-string 字符串格式化
- 掌握条件判断和循环控制

### 预计学习时间

- 环境配置：30 分钟
- 基础语法：1 小时
- 控制流：1 小时
- 练习：1-2 小时

---

## 2. 环境配置

### 2.1 Python 版本确认

你已经安装了 Python 3.13，这是一个非常新的版本。在终端中确认：

```bash
python --version
# 或
python3 --version
```

> **为什么选择 3.11+？**
> - 3.11 版本性能提升约 25%
> - 更好的错误提示信息
> - 支持 typing.Self、ParamSpec 等新特性
> - 你的 3.13 版本完全满足要求

### 2.2 虚拟环境 - venv（基础方案）

**什么是虚拟环境？**

如果你熟悉 Node.js，虚拟环境类似于每个项目独立的 `node_modules` 目录。它可以让不同项目使用不同版本的依赖包，互不干扰。

**创建虚拟环境**

```bash
# 进入你的项目目录
cd /Users/linruiqiang/work/ai_application

# 创建虚拟环境（命名为 .venv）
python3 -m venv .venv
```

**激活虚拟环境**

```bash
# macOS / Linux
source .venv/bin/activate

# 激活成功后，终端前面会显示 (.venv)
```

**退出虚拟环境**

```bash
deactivate
```

### 2.3 虚拟环境 - uv（进阶方案）

**什么是 uv？**

uv 是一个用 Rust 编写的现代 Python 包管理工具，速度比 pip 快 10-100 倍。类似于 Node.js 生态中的 pnpm。

**安装 uv**

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**使用 uv 创建虚拟环境**

```bash
# 创建虚拟环境
uv venv

# 激活虚拟环境（与 venv 相同）
source .venv/bin/activate
```

**uv 的优势**

- 创建虚拟环境更快
- 安装依赖更快
- 支持锁定依赖版本

> **建议**：初学阶段可以先用 venv 熟悉概念，等依赖管理复杂后再切换到 uv

### 2.4 包管理 - pip 基础命令

pip 是 Python 的包管理工具，类似于 npm。

```bash
# 安装包
pip install requests

# 安装指定版本
pip install requests==2.28.0

# 查看已安装的包
pip list

# 导出依赖列表
pip freeze > requirements.txt

# 从 requirements.txt 安装
pip install -r requirements.txt

# 卸载包
pip uninstall requests
```

**使用 uv 管理包（可选）**

```bash
# uv 可以直接使用 pip 命令
uv pip install requests

# 从 requirements.txt 安装（更快）
uv pip install -r requirements.txt
```

### 2.5 VS Code 配置确认

你已经配置好了 VS Code，确保以下几点：

1. **安装 Python 插件**（Microsoft 官方）
2. **选择解释器**：
   - `Cmd + Shift + P` 打开命令面板
   - 输入 `Python: Select Interpreter`
   - 选择 `.venv` 中的 Python 解释器

3. **验证配置**：
   - 新建 `test.py` 文件
   - 输入 `print("Hello")`
   - 右上角点击运行按钮

---

## 3. 基础语法

> 本节知识点需要你在 `source/01_python/01_basics/exercises.py` 中动手实践

### 3.1 变量与命名规范

**变量定义**

Python 不需要声明变量类型，直接赋值即可：

```python
name = "张三"
age = 25
score = 95.5
```

**命名规范（snake_case）**

| Python 风格 | JavaScript 风格 | 说明 |
|------------|----------------|------|
| `user_name` | `userName` | 变量、函数用下划线 |
| `MAX_SIZE` | `MAX_SIZE` | 常量用全大写下划线 |
| `UserName` | `UserName` | 类名用驼峰（后续学习） |

**命名规则**

- 只能包含字母、数字、下划线
- 不能以数字开头
- 区分大小写
- 不能使用关键字（如 `if`, `for`, `class` 等）

```python
# ✅ 正确
user_name = "张三"
_age = 18
score1 = 95.5

# ❌ 错误
1name = "张三"      # 不能以数字开头
user-name = "张三"  # 不能用连字符
class = "一班"      # 不能用关键字
```

### 3.2 数据类型

Python 有五种基本数据类型：

| 类型 | Python | JavaScript 对应 | 示例 |
|-----|--------|----------------|------|
| 整数 | `int` | `number` | `42`, `-10` |
| 浮点数 | `float` | `number` | `3.14`, `-0.5` |
| 字符串 | `str` | `string` | `"hello"`, `'world'` |
| 布尔值 | `bool` | `boolean` | `True`, `False` |
| 空值 | `None` | `null` / `undefined` | `None` |

**查看类型**

```python
type(42)        # <class 'int'>
type(3.14)      # <class 'float'>
type("hello")   # <class 'str'>
type(True)      # <class 'bool'>
type(None)      # <class 'NoneType'>
```

**类型转换**

```python
# 字符串转数字
int("42")       # 42
float("3.14")   # 3.14

# 数字转字符串
str(42)         # "42"

# 布尔转换
bool(1)         # True
bool(0)         # False
bool("")        # False（空字符串为 False）
bool("hello")   # True（非空字符串为 True）
```

> **注意**：Python 的布尔值是 `True` / `False`，首字母大写，不同于 JavaScript 的 `true` / `false`

### 3.3 类型注解

Python 3.5+ 支持类型注解（Type Hints），类似于 TypeScript 的类型标注。

**基本语法**

```python
# 变量类型注解
name: str = "张三"
age: int = 25
score: float = 95.5
is_student: bool = True

# 类型注解是可选的，不会影响运行
# 但可以让 IDE 提供更好的提示和检查
```

**对比 TypeScript**

```python
# Python
name: str = "张三"

# TypeScript
let name: string = "张三";
```

**为什么使用类型注解？**

1. IDE 可以提供更好的代码补全
2. 提高代码可读性
3. 静态检查工具可以提前发现类型错误
4. AI 应用开发中，API 调用和数据处理更清晰

### 3.4 字符串操作

**f-string 格式化（推荐）**

f-string 是 Python 3.6+ 引入的格式化方式，简洁高效：

```python
name = "张三"
age = 25

# f-string（推荐）
message = f"{name}今年{age}岁"
print(message)  # 张三今年25岁

# 可以在 {} 中写表达式
print(f"明年{age + 1}岁")  # 明年26岁

# 格式化数字
score = 95.5678
print(f"分数：{score:.2f}")  # 分数：95.57
```

**对比 JavaScript 模板字符串**

```python
# Python f-string
f"{name}今年{age}岁"

# JavaScript 模板字符串
`${name}今年${age}岁`
```

**常用字符串方法**

```python
text = "  Hello, World!  "

# 去除首尾空格
text.strip()           # "Hello, World!"

# 转换大小写
text.lower()           # "  hello, world!  "
text.upper()           # "  HELLO, WORLD!  "

# 查找和替换
text.find("World")     # 9（返回索引，找不到返回 -1）
text.replace("World", "Python")  # "  Hello, Python!  "

# 分割和连接
"a,b,c".split(",")     # ["a", "b", "c"]
"-".join(["a", "b", "c"])  # "a-b-c"

# 判断开头/结尾
"hello.py".startswith("hello")  # True
"hello.py".endswith(".py")      # True
```

**字符串长度**

```python
name = "张三"
len(name)  # 2（Python 3 中中文按字符计数）
```

---

## 4. 控制流

> 本节知识点需要你在 `source/01_python/01_basics/exercises.py` 中动手实践

### 4.1 条件判断 if / elif / else

**基本语法**

```python
score = 85

if score >= 90:
    print("优秀")
elif score >= 80:
    print("良好")
elif score >= 60:
    print("及格")
else:
    print("不及格")
```

**与 JavaScript 的区别**

```python
# Python：使用缩进表示代码块，elif 关键字
if score >= 90:
    print("优秀")
elif score >= 60:
    print("及格")

# JavaScript：使用花括号，else if
if (score >= 90) {
    console.log("优秀");
} else if (score >= 60) {
    console.log("及格");
}
```

**重要规则**

1. **缩进必须一致**：使用 4 个空格（推荐）或 1 个 Tab
2. **冒号不能省略**：`if`、`elif`、`else` 行末必须有冒号
3. **条件表达式不需要括号**（但可以加）

**逻辑运算符**

```python
age = 25
has_id = True

# 与（and）
if age >= 18 and has_id:
    print("可以进入")

# 或（or）
if age < 12 or age > 65:
    print("票价优惠")

# 非（not）
if not has_id:
    print("请出示证件")
```

| Python | JavaScript | 含义 |
|--------|-----------|------|
| `and` | `&&` | 与 |
| `or` | `\|\|` | 或 |
| `not` | `!` | 非 |

**比较运算符**

```python
==   # 等于
!=   # 不等于
>    # 大于
<    # 小于
>=   # 大于等于
<=   # 小于等于
is   # 是否为同一对象（身份比较）
```

### 4.2 for 循环

**遍历列表**

```python
fruits = ["苹果", "香蕉", "橙子"]

for fruit in fruits:
    print(fruit)
# 输出：
# 苹果
# 香蕉
# 橙子
```

**遍历字符串**

```python
for char in "Hello":
    print(char)
# 输出：H e l l o（每行一个）
```

**使用 range()**

```python
# range(n)：0 到 n-1
for i in range(5):
    print(i)  # 0, 1, 2, 3, 4

# range(start, end)：start 到 end-1
for i in range(2, 6):
    print(i)  # 2, 3, 4, 5

# range(start, end, step)：指定步长
for i in range(0, 10, 2):
    print(i)  # 0, 2, 4, 6, 8
```

**enumerate()：同时获取索引和值**

```python
fruits = ["苹果", "香蕉", "橙子"]

for index, fruit in enumerate(fruits):
    print(f"{index}: {fruit}")
# 输出：
# 0: 苹果
# 1: 香蕉
# 2: 橙子
```

### 4.3 while 循环

```python
count = 0

while count < 5:
    print(count)
    count += 1  # 注意：Python 没有 count++
# 输出：0, 1, 2, 3, 4
```

> **注意**：Python 不支持 `++` 和 `--` 运算符，使用 `+= 1` 和 `-= 1`

### 4.4 break / continue / pass

**break：跳出整个循环**

```python
for i in range(10):
    if i == 5:
        break
    print(i)
# 输出：0, 1, 2, 3, 4
```

**continue：跳过本次迭代**

```python
for i in range(5):
    if i == 2:
        continue
    print(i)
# 输出：0, 1, 3, 4（跳过了 2）
```

**pass：占位符，什么都不做**

```python
if score >= 60:
    pass  # TODO: 后续实现
else:
    print("不及格")
```

`pass` 常用于：
- 先搭建代码结构，后续再实现
- 定义空类或空函数时占位

---

## 5. 练习题

请在 `source/01_python/01_basics/exercises.py` 中完成以下练习：

### 练习 1：环境配置

```python
# 1. 创建虚拟环境（在终端完成）
# 2. 激活虚拟环境
# 3. 安装 requests 库
# 4. 验证安装：pip list | grep requests
```

### 练习 2：变量与类型

```python
# 声明以下变量（使用类型注解）：
# - name: str = "张三"
# - age: int = 18
# - score: float = 95.5
# - is_student: bool = True

# 使用 f-string 输出：
# "张三今年18岁，分数95.5，是学生吗？True"
```

### 练习 3：控制流

```python
# 输入一个分数(0-100)，输出等级：
# 90-100: A
# 80-89: B
# 70-79: C
# 60-69: D
# <60: F

# 提示：使用 input() 获取用户输入，需要转换为 int
```

### 练习 4：循环

```python
# 1. 打印 1-100 中所有偶数的和

# 2. 使用 for 循环打印九九乘法表
# 格式：
# 1x1=1
# 2x1=2 2x2=4
# 3x1=3 3x2=6 3x3=9
# ...
```

---

## 6. 小结

### 本节要点

1. **环境配置**
   - 虚拟环境隔离项目依赖
   - venv 是内置方案，uv 是更快的选择
   - pip 是标准包管理工具

2. **基础语法**
   - 变量命名使用 snake_case
   - 五种基本类型：int, float, str, bool, None
   - 类型注解提高代码可读性
   - f-string 是推荐的字符串格式化方式

3. **控制流**
   - Python 用缩进表示代码块
   - elif 而不是 else if
   - range() 生成数字序列
   - 没有 ++ 和 -- 运算符

### 与 JavaScript 对照表

| 特性 | Python | JavaScript |
|-----|--------|------------|
| 变量命名 | snake_case | camelCase |
| 布尔值 | True / False | true / false |
| 空值 | None | null / undefined |
| 逻辑与 | and | && |
| 逻辑或 | or | \|\| |
| 逻辑非 | not | ! |
| 字符串格式化 | f"{name}" | `${name}` |
| 代码块 | 缩进 | {} |
| 自增 | i += 1 | i++ |

### 下一节预告

下一节将学习 **数据结构**：
- 列表（List）
- 字典（Dict）
- 元组（Tuple）
- 集合（Set）

---

## 7. 常见问题

### Q: venv 和 uv 选哪个？

初学阶段用 venv 即可，它是 Python 内置的，无需额外安装。等项目复杂、依赖多了再考虑切换到 uv。

### Q: 为什么 Python 用缩进而不是花括号？

这是 Python 的设计哲学——强制统一的代码风格。虽然一开始可能不习惯，但好处是不同人写的代码风格一致，阅读起来更容易。

### Q: 类型注解是必须的吗？

不是必须的，Python 仍然是动态类型语言。但在 AI 应用开发中，建议使用类型注解，因为：
- API 响应、配置文件等数据结构复杂
- 有助于 IDE 提供更好的提示
- 方便团队协作和代码维护

### Q: input() 返回的是什么类型？

`input()` 始终返回字符串，如果需要数字，必须手动转换：

```python
age_str = input("请输入年龄：")
age = int(age_str)  # 转换为整数
```
