# Python 学习大纲

> 目标：零基础达到中等深度，为 AI 应用开发做准备

---

## 一、基础语法

### 1. 环境搭建与基础语法

#### 知识点

1. **环境配置**
   - Python 版本选择（3.11+）
   - 虚拟环境：`uv` 或 `venv`
   - 包管理：`pip` / `uv pip`
   - IDE 配置：VS Code + Python 插件

2. **基础语法**
   - 变量与命名规范（snake_case）
   - 数据类型：int, float, str, bool, None
   - 类型注解：`name: str = "hello"`
   - 字符串操作：f-string, 方法

3. **控制流**
   - if / elif / else
   - for / while 循环
   - range() 函数
   - break / continue / pass

#### 练习题

```python
# 1. 环境配置练习
# - 创建虚拟环境
# - 安装 requests 库
# - 验证安装成功

# 2. 变量与类型
# 编写代码：声明 name(str), age(int), score(float), is_student(bool)
# 使用 f-string 输出："张三今年18岁，分数95.5，是学生吗？True"

# 3. 控制流练习
# 输入一个分数(0-100)，输出等级：
# 90-100: A, 80-89: B, 70-79: C, 60-69: D, <60: F

# 4. 循环练习
# 打印 1-100 中所有偶数的和
# 使用 for 循环打印九九乘法表
```

---

### 2. 数据结构

#### 知识点

1. **列表 (List)**
   - 创建与索引
   - 常用方法：append, insert, remove, pop, sort
   - 列表推导式：`[x*2 for x in range(10)]`
   - 切片：`lst[1:3]`, `lst[::-1]`

2. **字典 (Dict)**
   - 创建与访问
   - 常用方法：get, keys, values, items, update
   - 字典推导式
   - 嵌套字典

3. **元组 (Tuple)**
   - 不可变性
   - 解包：`a, b = (1, 2)`

4. **集合 (Set)**
   - 去重
   - 集合运算：交集、并集、差集

#### 练习题

```python
# 1. 列表操作
# 给定列表 [3, 1, 4, 1, 5, 9, 2, 6]
# - 排序
# - 去重
# - 找出所有偶数
# - 计算平均值

# 2. 字典操作
# 创建学生成绩字典：{"张三": 85, "李四": 92, "王五": 78}
# - 找出最高分的学生
# - 计算平均分
# - 添加新学生

# 3. 列表推导式
# 生成 1-50 中所有能被 3 整除的数的平方列表

# 4. 综合练习
# 有两个列表 names = ["a", "b", "c"] 和 scores = [90, 85, 92]
# 将它们合并成一个字典
```

---

### 3. 字符串与文件基础

#### 知识点

1. **字符串进阶**
   - 常用方法：split, join, strip, replace, find
   - 格式化：f-string, format()
   - 多行字符串
   - 原始字符串：`r"path"`

2. **文件读写**
   - open() 函数
   - with 语句（上下文管理器）
   - 读写模式：r, w, a, rb, wb
   - 逐行读取

3. **路径处理**
   - `pathlib.Path`
   - 路径拼接与检查

#### 练习题

```python
# 1. 字符串处理
# 给定字符串 "  Hello, World!  "
# - 去除首尾空格
# - 转换为小写
# - 按逗号分割
# - 用 "-" 连接

# 2. 文件读写
# - 创建一个文本文件，写入 10 行数据
# - 读取文件，统计行数
# - 追加一行 "这是追加的内容"

# 3. 日志解析
# 有日志文件 log.txt，格式如下：
# 2024-01-15 10:30:15 INFO User logged in
# 2024-01-15 10:31:20 ERROR Database connection failed
# 提取所有 ERROR 级别的日志行

# 4. 路径操作
# 使用 pathlib 实现：
# - 检查文件是否存在
# - 获取文件扩展名
# - 创建目录
```

---

### 4. 综合练习：通讯录管理

```python
# 实现一个命令行通讯录程序，功能包括：
# 1. 添加联系人（姓名、电话、邮箱）
# 2. 查找联系人（按姓名）
# 3. 删除联系人
# 4. 显示所有联系人
# 5. 保存到文件 / 从文件加载
#
# 要求：
# - 使用字典存储联系人
# - 使用 JSON 格式保存文件
# - 使用循环实现交互式菜单
```

---

## 二、函数与类

### 5. 函数

#### 知识点

1. **函数定义**
   - def 语句
   - 参数与返回值
   - 类型注解：`def add(a: int, b: int) -> int:`

2. **参数类型**
   - 位置参数
   - 默认参数
   - 关键字参数
   - *args 和 **kwargs

3. **作用域**
   - 局部变量 vs 全局变量
   - global 关键字（少用）

4. **高阶函数**
   - 函数作为参数
   - lambda 表达式
   - map, filter, reduce

5. **装饰器基础**
   - @decorator 语法
   - 简单装饰器实现

#### 练习题

```python
# 1. 基础函数
# 编写函数：
# - calculate_bmi(weight, height) -> 返回 BMI 值和等级
# - is_prime(n) -> 判断是否为质数

# 2. 参数练习
# 编写函数 greet(name, greeting="你好", times=1)
# 调用方式：
# greet("张三")
# greet("李四", greeting="早上好")
# greet("王五", times=3)

# 3. *args 和 **kwargs
# 编写函数 sum_all(*args) 计算所有参数的和
# 编写函数 print_info(**kwargs) 打印所有键值对

# 4. 高阶函数
# 使用 map 将列表 [1,2,3,4,5] 中每个元素平方
# 使用 filter 筛选出 [1,2,3,4,5,6,7,8,9,10] 中的奇数
# 使用 reduce 计算 1! + 2! + 3! + 4! + 5!

# 5. 简单装饰器
# 编写计时装饰器，打印函数执行时间
```

---

### 6. 类与面向对象

#### 知识点

1. **类基础**
   - class 定义
   - __init__ 构造函数
   - self 参数
   - 实例属性 vs 类属性

2. **方法**
   - 实例方法
   - @classmethod
   - @staticmethod

3. **封装**
   - 私有属性（_name, __name）
   - @property 装饰器

4. **继承**
   - 单继承
   - super() 调用父类方法
   - 方法重写

5. **特殊方法**
   - __str__, __repr__
   - __len__, __eq__

#### 练习题

```python
# 1. 基础类
# 创建 Student 类：
# - 属性：name, age, scores (列表)
# - 方法：add_score(score), get_average()
# - __str__ 方法返回学生信息

# 2. 类方法和静态方法
# 扩展 Student 类：
# - 类属性 student_count
# - 类方法 get_count() 返回学生总数
# - 静态方法 is_adult(age) 判断是否成年

# 3. 继承
# 创建 GraduateStudent 继承 Student：
# - 新增属性：thesis_title
# - 重写 __str__ 方法

# 4. 私有属性和 property
# 创建 BankAccount 类：
# - 私有属性 __balance
# - property balance (只读)
# - 方法 deposit(amount), withdraw(amount)

# 5. 综合练习
# 实现一个简单的购物车系统：
# - Product 类：name, price
# - Cart 类：add_product(), remove_product(), get_total()
```

---

### 7. 模块、包与异常处理

#### 知识点

1. **模块**
   - import 语句
   - from ... import ...
   - __name__ == "__main__"

2. **包**
   - 目录结构
   - __init__.py
   - 相对导入 vs 绝对导入

3. **常用标准库**
   - os, sys
   - json
   - datetime
   - random
   - collections (Counter, defaultdict)

4. **异常处理**
   - try / except / finally
   - 常见异常类型
   - raise 抛出异常
   - 自定义异常

#### 练习题

```python
# 1. 模块练习
# 创建模块 calculator.py，包含 add, subtract, multiply, divide 函数
# 在 main.py 中导入并使用

# 2. JSON 处理
# - 将字典保存为 JSON 文件
# - 从 JSON 文件读取为字典
# - 格式化输出（indent=2）

# 3. datetime 练习
# - 获取当前时间
# - 计算两个日期相差多少天
# - 格式化日期输出

# 4. 异常处理
# 编写安全除法函数 safe_divide(a, b)：
# - 处理除零异常
# - 处理类型异常
# - 返回 None 或结果

# 5. 自定义异常
# 创建 AgeError 异常类
# 编写函数 set_age(age)，年龄不在 0-150 时抛出异常
```

---

### 8. 综合练习：任务管理器

```python
# 实现一个任务管理器，要求：
#
# 1. Task 类
#    - 属性：id, title, description, status, created_at
#    - 状态：pending, in_progress, completed
#
# 2. TaskManager 类
#    - 添加任务
#    - 删除任务
#    - 更新任务状态
#    - 按状态筛选任务
#    - 保存到 JSON / 从 JSON 加载
#
# 3. 异常处理
#    - TaskNotFoundError
#    - InvalidStatusError
#
# 4. 命令行交互界面
```

---

## 三、AI 应用开发核心

### 9. JSON 与 HTTP 请求

#### 知识点

1. **JSON 深入**
   - json.dumps() / json.loads()
   - 处理复杂嵌套结构
   - 自定义序列化（datetime 等）

2. **HTTP 基础**
   - 请求方法：GET, POST, PUT, DELETE
   - 请求头、请求体
   - 状态码
   - JSON API 交互

3. **requests 库**
   - 基本请求
   - 传递参数
   - 处理响应
   - 超时与重试

4. **httpx 库**（推荐）
   - 同步请求
   - 异步请求预览

#### 练习题

```python
# 1. JSON 处理
# 处理嵌套 JSON 数据：
data = {
    "users": [
        {"name": "张三", "age": 25, "hobbies": ["reading", "coding"]},
        {"name": "李四", "age": 30, "hobbies": ["music"]}
    ]
}
# - 提取所有用户名
# - 统计所有爱好
# - 找出年龄最大的用户

# 2. requests 练习
# 使用 httpbin.org 测试：
# - GET 请求带参数
# - POST 请求发送 JSON
# - 获取响应头信息

# 3. API 调用练习
# 调用公开 API（如天气 API、随机名言 API）：
# - 发送请求
# - 解析响应
# - 处理错误

# 4. 封装 HTTP 客户端
# 创建简单的 HTTP 客户端类：
# - get_json(url)
# - post_json(url, data)
# - 统一错误处理
```

---

### 10. 异步编程

#### 知识点

1. **异步概念**
   - 同步 vs 异步
   - 阻塞 vs 非阻塞
   - 为什么 AI 应用需要异步

2. **asyncio 基础**
   - async def 定义协程
   - await 等待协程
   - asyncio.run()
   - 并发执行：gather, create_task

3. **异步 HTTP**
   - httpx.AsyncClient
   - 异步请求示例

4. **异步文件操作**
   - aiofiles 库

#### 练习题

```python
# 1. 基础异步
# 编写异步函数：
async def say_hello(name, delay):
    # 延迟后打印问候
    pass

# 并发调用 3 次，观察执行顺序

# 2. 异步 HTTP
# 使用 httpx.AsyncClient：
# - 并发请求 5 个 URL
# - 统计总耗时

# 3. 异步文件操作
# 使用 aiofiles：
# - 异步读取文件
# - 异步写入文件

# 4. 实战：并发 API 调用
# 模拟调用 3 个不同的 LLM API
# 并发请求，返回最快的结果
```

---

### 11. FastAPI 基础

#### 知识点

1. **FastAPI 入门**
   - 安装与运行
   - 路由与请求处理
   - 路径参数与查询参数

2. **请求与响应**
   - Pydantic 模型
   - 请求体验证
   - 响应模型

3. **高级特性**
   - 依赖注入
   - 错误处理
   - 静态文件与模板（可选）

4. **部署基础**
   - uvicorn 运行
   - 热重载

#### 练习题

```python
# 1. 基础 API
# 创建 FastAPI 应用：
# - GET / 返回 "Hello World"
# - GET /items/{item_id} 返回物品信息
# - GET /users?limit=10&offset=0 返回用户列表

# 2. Pydantic 模型
# 定义请求模型：
class UserCreate(BaseModel):
    name: str
    email: str
    age: int

# 实现 POST /users 创建用户

# 3. 完整 CRUD
# 实现书籍管理 API：
# - GET /books 获取列表
# - POST /books 创建
# - GET /books/{id} 获取详情
# - PUT /books/{id} 更新
# - DELETE /books/{id} 删除

# 4. 错误处理
# 实现自定义错误处理：
# - 404 资源不存在
# - 400 请求参数错误
```

---

### 12. 综合练习：AI 聊天 API

```python
# 实现一个简单的 AI 聊天后端 API
#
# 1. 数据模型
#    - Message: role, content, timestamp
#    - Conversation: id, messages, created_at
#
# 2. API 接口
#    - POST /chat: 发送消息，返回模拟回复
#    - GET /conversations: 获取对话列表
#    - GET /conversations/{id}: 获取对话详情
#
# 3. 功能要求
#    - 使用 Pydantic 验证
#    - 内存存储（字典）
#    - 支持流式响应（可选）
#
# 4. 进阶（可选）
#    - 接入真实 LLM API（OpenAI / Claude）
#    - 添加 API Key 验证
#    - 添加日志记录
```

---

## 学习资源推荐

### 官方文档
- [Python 官方文档](https://docs.python.org/zh-cn/3/)
- [FastAPI 官方文档](https://fastapi.tiangolo.com/zh/)

### 推荐教程
- [Python 入门教程 - 廖雪峰](https://www.liaoxuefeng.com/wiki/1016959663602400)
- [Real Python](https://realpython.com/)

### 练习平台
- [LeetCode](https://leetcode.cn/) - 简单题目
- [HackerRank](https://www.hackerrank.com/domains/python)

---

## 学习建议

1. **先理解再记忆**，不要死记语法
2. **遇到问题先搜索**，培养独立解决能力
3. **记录笔记**，整理到 docs 目录
4. **代码放 source 目录**，方便复习
