# 02. 数据结构

> 本节目标：掌握 Python 四大核心数据结构——列表、字典、元组、集合

---

## 1. 概述

### 学习目标

- 掌握列表的创建、索引、切片和常用方法
- 理解并熟练使用列表推导式
- 掌握字典的创建、访问和常用操作
- 理解元组的不可变性和解包
- 掌握集合的去重和集合运算
- 理解各数据结构的适用场景

### 预计学习时间

- 列表：1.5 小时
- 字典：1.5 小时
- 元组与集合：1 小时
- 练习：1-2 小时

### 数据结构对比

| Python | JavaScript | 特点 | 适用场景 |
|--------|-----------|------|---------|
| List（列表） | Array | 有序、可变 | 存储有序数据集合 |
| Dict（字典） | Object / Map | 键值对、可变 | 存储映射关系 |
| Tuple（元组） | - | 有序、不可变 | 存储不变数据 |
| Set（集合） | Set | 无序、不重复 | 去重、集合运算 |

---

## 2. 列表（List）

列表是 Python 中最常用的数据结构，类似于 JavaScript 的数组。

### 2.1 创建与索引

**创建列表**

```python
# 直接创建
fruits = ["苹果", "香蕉", "橙子"]
numbers = [1, 2, 3, 4, 5]
mixed = [1, "hello", True, 3.14]  # 可以混合类型（但不推荐）

# 空列表
empty_list = []
empty_list = list()

# 从其他序列创建
list_from_string = list("hello")  # ['h', 'e', 'l', 'l', 'o']
list_from_range = list(range(5))  # [0, 1, 2, 3, 4]
```

**索引访问**

```python
fruits = ["苹果", "香蕉", "橙子", "葡萄", "西瓜"]

# 正向索引（从 0 开始）
fruits[0]  # "苹果"
fruits[2]  # "橙子"

# 负向索引（从 -1 开始，-1 表示最后一个）
fruits[-1]  # "西瓜"
fruits[-2]  # "葡萄"

# 索引越界会报错
# fruits[10]  # IndexError: list index out of range
```

**与 JavaScript 对比**

```python
# Python：支持负索引
fruits[-1]  # "西瓜"（最后一个元素）

# JavaScript：不支持负索引
// fruits[-1]  // undefined（不会报错，但不是你想要的）
// fruits.at(-1)  // "西瓜"（ES2022 新增）
```

### 2.2 切片（Slicing）

切片是 Python 的强大特性，可以轻松获取子列表。

**基本语法**

```python
# list[start:end:step]
# start：起始索引（包含，默认 0）
# end：结束索引（不包含，默认到末尾）
# step：步长（默认 1）

numbers = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

# 基本切片
numbers[2:5]    # [2, 3, 4]（索引 2、3、4）
numbers[:3]     # [0, 1, 2]（前三个）
numbers[7:]     # [7, 8, 9]（从索引 7 到末尾）
numbers[:]      # [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]（完整复制）

# 步长
numbers[::2]    # [0, 2, 4, 6, 8]（每隔一个取一个）
numbers[1::2]   # [1, 3, 5, 7, 9]（从索引 1 开始，每隔一个）

# 负步长（反转）
numbers[::-1]   # [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]（反转列表）

# 负索引切片
numbers[-3:]    # [7, 8, 9]（最后三个）
numbers[:-2]    # [0, 1, 2, 3, 4, 5, 6, 7]（排除最后两个）
```

**切片不会越界**

```python
numbers = [0, 1, 2]

# 切片超出范围不会报错，只返回有效部分
numbers[0:100]  # [0, 1, 2]
numbers[10:20]  # []（空列表）
```

**切片是复制，不是引用**

```python
a = [1, 2, 3]
b = a[:]     # 创建新列表
b[0] = 100
print(a)     # [1, 2, 3]（a 不受影响）

# 对比直接赋值
c = a        # c 和 a 指向同一个列表
c[0] = 100
print(a)     # [100, 2, 3]（a 被修改了）
```

### 2.3 常用方法

**添加元素**

```python
fruits = ["苹果", "香蕉"]

# append：末尾添加
fruits.append("橙子")  # ["苹果", "香蕉", "橙子"]

# insert：指定位置插入
fruits.insert(1, "葡萄")  # ["苹果", "葡萄", "香蕉", "橙子"]

# extend：添加多个元素（或用 +=）
fruits.extend(["西瓜", "草莓"])  # 末尾添加两个
fruits += ["芒果", "荔枝"]       # 同上
```

**删除元素**

```python
fruits = ["苹果", "香蕉", "橙子", "香蕉"]

# remove：删除第一个匹配的值
fruits.remove("香蕉")  # ["苹果", "橙子", "香蕉"]

# pop：删除指定索引（默认删除最后一个，返回被删除的值）
last = fruits.pop()     # "香蕉"（被删除的值）
first = fruits.pop(0)   # "苹果"

# del：删除指定索引或切片
del fruits[0]           # 删除第一个
del fruits[1:3]         # 删除切片

# clear：清空列表
fruits.clear()          # []
```

**查找与统计**

```python
numbers = [1, 2, 3, 2, 4, 2, 5]

# index：查找元素索引（第一个）
numbers.index(2)        # 1

# count：统计出现次数
numbers.count(2)        # 3

# in：判断是否存在
2 in numbers            # True
10 in numbers           # False
```

**排序与反转**

```python
numbers = [3, 1, 4, 1, 5, 9, 2, 6]

# sort：原地排序（修改原列表）
numbers.sort()          # [1, 1, 2, 3, 4, 5, 6, 9]
numbers.sort(reverse=True)  # 降序

# sorted：返回新列表（不修改原列表）
original = [3, 1, 4, 1, 5]
sorted_list = sorted(original)  # [1, 1, 3, 4, 5]
print(original)          # [3, 1, 4, 1, 5]（原列表不变）

# reverse：原地反转
numbers.reverse()

# 自定义排序（按字符串长度）
words = ["apple", "pie", "strawberry"]
words.sort(key=len)      # ["pie", "apple", "strawberry"]
```

**其他常用操作**

```python
numbers = [3, 1, 4, 1, 5]

# 长度
len(numbers)            # 5

# 最大值、最小值、求和
max(numbers)            # 5
min(numbers)            # 1
sum(numbers)            # 14

# 复制
new_list = numbers.copy()
```

### 2.4 列表推导式（List Comprehension）

列表推导式是 Python 的特色语法，可以简洁地创建列表。

**基本语法**

```python
# [表达式 for 变量 in 可迭代对象]
squares = [x**2 for x in range(5)]
# [0, 1, 4, 9, 16]

# 等价于：
squares = []
for x in range(5):
    squares.append(x**2)
```

**带条件的列表推导式**

```python
# [表达式 for 变量 in 可迭代对象 if 条件]
evens = [x for x in range(10) if x % 2 == 0]
# [0, 2, 4, 6, 8]

# 等价于：
evens = []
for x in range(10):
    if x % 2 == 0:
        evens.append(x)
```

**带 if-else 的列表推导式**

```python
# [表达式1 if 条件 else 表达式2 for 变量 in 可迭代对象]
# 注意：if-else 写在 for 前面

labels = ["偶数" if x % 2 == 0 else "奇数" for x in range(5)]
# ["偶数", "奇数", "偶数", "奇数", "偶数"]
```

**嵌套循环**

```python
# 生成笛卡尔积
pairs = [(x, y) for x in [1, 2] for y in ['a', 'b']]
# [(1, 'a'), (1, 'b'), (2, 'a'), (2, 'b')]

# 等价于：
pairs = []
for x in [1, 2]:
    for y in ['a', 'b']:
        pairs.append((x, y))
```

**实际应用示例**

```python
# 从字典列表中提取特定字段
users = [
    {"name": "张三", "age": 25},
    {"name": "李四", "age": 30},
    {"name": "王五", "age": 28}
]
names = [user["name"] for user in users]
# ["张三", "李四", "王五"]

# 过滤并转换
adults = [user["name"] for user in users if user["age"] >= 28]
# ["李四", "王五"]

# 字符串处理
words = ["  Hello  ", "  World  ", "  Python  "]
cleaned = [w.strip().lower() for w in words]
# ["hello", "world", "python"]
```

**与 JavaScript 对比**

```python
# Python 列表推导式
squares = [x**2 for x in range(5) if x % 2 == 0]

# JavaScript 数组方法
const squares = Array.from({length: 5}, (_, i) => i)
    .filter(x => x % 2 === 0)
    .map(x => x ** 2);
```

---

## 3. 字典（Dict）

字典是键值对的集合，类似于 JavaScript 的对象或 Map。

### 3.1 创建与访问

**创建字典**

```python
# 直接创建
person = {
    "name": "张三",
    "age": 25,
    "city": "北京"
}

# 空字典
empty_dict = {}
empty_dict = dict()

# 从列表创建
keys = ["a", "b", "c"]
values = [1, 2, 3]
d = dict(zip(keys, values))  # {"a": 1, "b": 2, "c": 3}

# 使用关键字参数
d = dict(name="张三", age=25)  # {"name": "张三", "age": 25}
```

**访问值**

```python
person = {"name": "张三", "age": 25}

# 通过键访问
person["name"]      # "张三"

# 键不存在会报错
# person["email"]   # KeyError: 'email'

# 使用 get 方法（推荐）
person.get("name")       # "张三"
person.get("email")      # None（不存在返回 None）
person.get("email", "无") # "无"（指定默认值）
```

**修改和添加**

```python
person = {"name": "张三", "age": 25}

# 修改
person["age"] = 26

# 添加新键值对
person["email"] = "zhangsan@example.com"

# update：批量更新
person.update({"city": "北京", "age": 27})
```

### 3.2 常用方法

**遍历字典**

```python
person = {"name": "张三", "age": 25, "city": "北京"}

# 遍历键（默认行为）
for key in person:
    print(key)

# 显式遍历键
for key in person.keys():
    print(key)

# 遍历值
for value in person.values():
    print(value)

# 遍历键值对（最常用）
for key, value in person.items():
    print(f"{key}: {value}")
```

**查找与判断**

```python
person = {"name": "张三", "age": 25}

# 判断键是否存在
"name" in person       # True
"email" in person      # False

# 获取所有键/值
person.keys()          # dict_keys(['name', 'age'])
person.values()        # dict_values(['张三', 25])
person.items()         # dict_items([('name', '张三'), ('age', 25)])

# 转换为列表
list(person.keys())    # ['name', 'age']
```

**删除元素**

```python
person = {"name": "张三", "age": 25, "city": "北京"}

# del：删除指定键
del person["city"]

# pop：删除并返回值
age = person.pop("age")    # 25

# popitem：删除并返回最后一个键值对（Python 3.7+）
item = person.popitem()    # ("name", "张三")

# clear：清空
person.clear()             # {}
```

**setdefault：获取或设置默认值**

```python
person = {"name": "张三"}

# 如果键存在，返回值
person.setdefault("name", "默认")  # "张三"

# 如果键不存在，设置默认值并返回
person.setdefault("age", 18)       # 18
print(person)  # {"name": "张三", "age": 18}
```

### 3.3 字典推导式

```python
# 基本语法
# {键表达式: 值表达式 for 变量 in 可迭代对象}

# 示例：创建平方数字典
squares = {x: x**2 for x in range(5)}
# {0: 0, 1: 1, 2: 4, 3: 9, 4: 16}

# 带条件
even_squares = {x: x**2 for x in range(10) if x % 2 == 0}
# {0: 0, 2: 4, 4: 16, 6: 36, 8: 64}

# 交换键值
original = {"a": 1, "b": 2, "c": 3}
swapped = {v: k for k, v in original.items()}
# {1: "a", 2: "b", 3: "c"}

# 从列表创建字典
words = ["apple", "banana", "cherry"]
word_lengths = {word: len(word) for word in words}
# {"apple": 5, "banana": 6, "cherry": 6}
```

### 3.4 嵌套字典

在 AI 应用开发中，经常需要处理嵌套的字典结构（如 API 响应）。

**创建嵌套字典**

```python
users = {
    "张三": {
        "age": 25,
        "city": "北京",
        "hobbies": ["阅读", "编程"]
    },
    "李四": {
        "age": 30,
        "city": "上海",
        "hobbies": ["音乐", "旅行"]
    }
}
```

**访问嵌套数据**

```python
# 访问嵌套值
users["张三"]["city"]           # "北京"
users["张三"]["hobbies"][0]     # "阅读"

# 安全访问（避免 KeyError）
users.get("张三", {}).get("city")       # "北京"
users.get("王五", {}).get("city", "未知") # "未知"
```

**处理嵌套数据示例**

```python
# API 响应数据
response = {
    "code": 200,
    "data": {
        "users": [
            {"id": 1, "name": "张三", "score": 85},
            {"id": 2, "name": "李四", "score": 92},
            {"id": 3, "name": "王五", "score": 78}
        ],
        "total": 3
    }
}

# 提取所有用户名
names = [user["name"] for user in response["data"]["users"]]
# ["张三", "李四", "王五"]

# 找出高分用户
high_scores = [
    user["name"] for user in response["data"]["users"]
    if user["score"] >= 90
]
# ["李四"]

# 计算平均分
scores = [user["score"] for user in response["data"]["users"]]
avg_score = sum(scores) / len(scores)  # 85.0
```

---

## 4. 元组（Tuple）

元组是不可变的有序序列，类似于列表但不能修改。

### 4.1 创建与访问

**创建元组**

```python
# 直接创建
point = (3, 4)
rgb = (255, 128, 0)
single = (1,)       # 单元素元组，注意逗号
empty = ()          # 空元组

# 省略括号（元组打包）
coordinates = 3, 4, 5
x, y, z = coordinates  # 元组解包

# 从其他序列创建
tuple_from_list = tuple([1, 2, 3])
tuple_from_string = tuple("hello")  # ('h', 'e', 'l', 'l', 'o')
```

**访问元素**

```python
point = (3, 4)

# 索引（与列表相同）
point[0]            # 3
point[-1]           # 4

# 切片
point[0:1]          # (3,)

# 元组不可修改
# point[0] = 5      # TypeError: 'tuple' object does not support item assignment
```

### 4.2 元组解包

元组解包是 Python 的强大特性，可以同时给多个变量赋值。

**基本解包**

```python
point = (3, 4)
x, y = point
print(x)  # 3
print(y)  # 4

# 交换变量（经典用法）
a, b = 1, 2
a, b = b, a
print(a, b)  # 2 1
```

**扩展解包（*运算符）**

```python
numbers = (1, 2, 3, 4, 5)

# * 收集剩余元素
first, *rest = numbers
print(first)  # 1
print(rest)   # [2, 3, 4, 5]（注意是列表）

*beginning, last = numbers
print(beginning)  # [1, 2, 3, 4]
print(last)       # 5

first, *middle, last = numbers
print(first)   # 1
print(middle)  # [2, 3, 4]
print(last)    # 5
```

**在函数返回值中的应用**

```python
# 函数返回多个值
def get_user_info():
    name = "张三"
    age = 25
    city = "北京"
    return name, age, city  # 实际返回的是元组

# 解包接收
name, age, city = get_user_info()

# 或者作为元组接收
info = get_user_info()
print(info)  # ("张三", 25, "北京")
```

### 4.3 元组 vs 列表

| 特性 | 列表 | 元组 |
|-----|------|------|
| 可变性 | 可变 | 不可变 |
| 语法 | `[1, 2, 3]` | `(1, 2, 3)` |
| 性能 | 稍慢 | 稍快 |
| 用途 | 数据需要修改时 | 数据固定不变时 |
| 字典键 | ❌ 不能作为键 | ✅ 可以作为键 |

**元组作为字典键**

```python
# 用坐标作为键
locations = {
    (0, 0): "原点",
    (1, 0): "x轴正方向",
    (0, 1): "y轴正方向"
}
print(locations[(0, 0)])  # "原点"

# 列表不能作为键
# locations[[0, 0]] = "原点"  # TypeError
```

---

## 5. 集合（Set）

集合是无序的不重复元素集合，类似于数学中的集合概念。

### 5.1 创建与基本操作

**创建集合**

```python
# 直接创建
fruits = {"苹果", "香蕉", "橙子"}
numbers = {1, 2, 3, 4, 5}

# 空集合（注意：{} 是空字典！）
empty_set = set()    # 正确
# empty = {}         # 这是空字典，不是集合！

# 从列表创建（自动去重）
unique = set([1, 2, 2, 3, 3, 3])  # {1, 2, 3}

# 从字符串创建
chars = set("hello")  # {'h', 'e', 'l', 'o'}
```

**添加和删除**

```python
fruits = {"苹果", "香蕉"}

# add：添加元素
fruits.add("橙子")

# remove：删除元素（不存在会报错）
fruits.remove("苹果")

# discard：删除元素（不存在不报错）
fruits.discard("西瓜")  # 安全删除

# pop：删除并返回任意一个元素
item = fruits.pop()

# clear：清空
fruits.clear()
```

**判断成员**

```python
fruits = {"苹果", "香蕉", "橙子"}

"苹果" in fruits      # True
"西瓜" in fruits      # False
```

### 5.2 集合运算

集合支持数学中的集合运算，这在数据处理中非常有用。

```python
a = {1, 2, 3, 4}
b = {3, 4, 5, 6}

# 交集（同时在两个集合中）
a & b              # {3, 4}
a.intersection(b)  # {3, 4}

# 并集（在任一集合中）
a | b           # {1, 2, 3, 4, 5, 6}
a.union(b)      # {1, 2, 3, 4, 5, 6}

# 差集（在 a 中但不在 b 中）
a - b               # {1, 2}
a.difference(b)     # {1, 2}

# 对称差集（在 a 或 b 中，但不同时在两者中）
a ^ b                       # {1, 2, 5, 6}
a.symmetric_difference(b)   # {1, 2, 5, 6}
```

**子集和超集判断**

```python
a = {1, 2}
b = {1, 2, 3, 4}

# 子集判断
a <= b              # True（a 是 b 的子集）
a.issubset(b)       # True

# 超集判断
b >= a              # True（b 是 a 的超集）
b.issuperset(a)     # True

# 是否没有共同元素
c = {5, 6}
a.isdisjoint(c)     # True（a 和 c 没有共同元素）
```

### 5.3 集合推导式

```python
# 基本语法
# {表达式 for 变量 in 可迭代对象}

# 示例
squares = {x**2 for x in range(5)}
# {0, 1, 4, 9, 16}

# 去重并转换
numbers = [1, 2, 2, 3, 3, 3, 4]
unique_squares = {x**2 for x in numbers}
# {1, 4, 9, 16}
```

### 5.4 去重应用

集合最常用的场景是去重。

```python
# 列表去重
numbers = [1, 2, 2, 3, 3, 3, 4, 4, 5]
unique = list(set(numbers))
# [1, 2, 3, 4, 5]（注意：顺序可能改变）

# 保持顺序的去重
def unique_ordered(lst):
    seen = set()
    result = []
    for item in lst:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result

unique_ordered(numbers)  # [1, 2, 3, 4, 5]（保持原顺序）

# 字符串去重
text = "hello world"
unique_chars = set(text)  # {'h', 'e', 'l', 'o', ' ', 'w', 'r', 'd'}
```

---

## 6. 数据结构选择指南

### 6.1 如何选择合适的数据结构

| 需求 | 推荐数据结构 | 示例 |
|-----|------------|------|
| 存储有序数据，需要频繁增删 | 列表 | 任务列表、消息队列 |
| 存储键值对，需要快速查找 | 字典 | 用户信息、配置项 |
| 存储不变数据 | 元组 | 坐标、配置常量 |
| 去重 | 集合 | 唯一 ID、标签 |
| 需要作为字典键 | 元组 | 坐标映射、缓存键 |

### 6.2 性能对比

```python
import time

# 列表查找（O(n)）
lst = list(range(100000))
start = time.time()
99999 in lst  # 较慢
print(f"列表查找: {time.time() - start}")

# 集合查找（O(1)）
s = set(range(100000))
start = time.time()
99999 in s    # 非常快
print(f"集合查找: {time.time() - start}")
```

### 6.3 AI 应用中的常见用法

**LLM API 响应处理**

```python
response = {
    "choices": [
        {
            "message": {
                "role": "assistant",
                "content": "Hello!"
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 10,
        "completion_tokens": 5,
        "total_tokens": 15
    }
}

# 提取回复内容
content = response["choices"][0]["message"]["content"]

# 计算总 token
total = response["usage"]["total_tokens"]
```

**消息列表管理**

```python
messages = [
    {"role": "system", "content": "你是一个助手"},
    {"role": "user", "content": "你好"}
]

# 添加用户消息
messages.append({"role": "user", "content": "今天天气怎么样"})

# 添加助手回复
messages.append({"role": "assistant", "content": "今天天气晴朗"})

# 提取所有用户消息
user_messages = [m["content"] for m in messages if m["role"] == "user"]
```

---

## 7. 字面量与构造函数 📌

### 7.1 概念区分

**字面量**是代码中直接写死的固定值，**构造函数**是用来从其他数据创建/转换数据的。

```python
# 字面量 —— 直接写值，代码里写死的数据
numbers = [1, 2, 3]
person = {"name": "张三"}
unique = {1, 2, 3}
point = (10, 20)

# 构造函数 —— 从其他数据转换得到
chars = list("hello")           # str → list
unique = set([1, 2, 2, 3])      # list → set（去重）
pairs = dict([("a", 1), ("b", 2)])  # list of tuples → dict
```

### 7.2 各类型的字面量 vs 构造函数

| 类型 | 字面量 | 构造函数 | 常见用法 |
|------|--------|----------|---------|
| 列表 | `[1, 2, 3]` | `list("hello")` → `['h', 'e', 'l', 'l', 'o']` | 从字符串/元组转列表 |
| 字典 | `{"a": 1}` | `dict([("a", 1)])` / `dict(name="张三")` | 从键值对列表/kwargs创建 |
| 集合 | `{1, 2}` | `set([1, 2, 2])` → `{1, 2}` | 从列表去重 |
| 元组 | `(1, 2, 3)` | `tuple([1, 2])` → `(1, 2)` | 从列表转元组 |

### 7.3 一个易错点：空集合

```python
# ❌ {} 是空字典，不是空集合！
empty_dict = {}

# ✅ 创建空集合必须用构造函数
empty_set = set()

# ✅ 验证
type({})    # <class 'dict'>
type(set()) # <class 'set'>
```

### 7.4 泛型语法（类型注解）

```python
# list[int] 是类型注解，不是数据！
# 表示"整数列表的类型"，给类型检查器看，运行时没意义

scores: list[int] = [90, 85, 78]   # 类型注解
scores = list[int]([90, 85, 78])  # 运行时创建列表（不常用）

# 运行时创建列表只有两种方式
scores = [90, 85, 78]             # 字面量（常用）
scores = list([90, 85, 78])       # 构造函数（通常用来转换）
```

---

## 8. 数据结构相互转换 📌

### 8.1 基础转换一览

```python
# 列表 ↔ 元组（互转）
tuple([1, 2, 3])    # [1, 2, 3] → (1, 2, 3)
list((1, 2, 3))     # (1, 2, 3) → [1, 2, 3]

# 列表 → 集合（去重）
set([1, 2, 2, 3])   # {1, 2, 3}

# 列表 → 字典（用 zip 组合键值）
keys = ["a", "b", "c"]
values = [1, 2, 3]
dict(zip(keys, values))  # {"a": 1, "b": 2, "c": 3}

# 字符串 → 列表/集合（逐字符拆分）
list("hello")  # ['h', 'e', 'l', 'l', 'o']
set("hello")   # {'h', 'e', 'l', 'o'}

# 字典 → 列表（键、值、键值对）
d = {"a": 1, "b": 2}
list(d.keys())        # ["a", "b"]
list(d.values())      # [1, 2]
list(d.items())       # [("a", 1), ("b", 2)]
```

### 8.2 实用场景一：API 响应去重（高频）

```python
# LLM 返回的工具列表可能有重复
tools = ["search", "calculator", "search", "weather"]

# 用集合快速去重
unique_tools = set(tools)   # {"search", "calculator", "weather"}

# 快速判断工具是否存在
if "search" in unique_tools:
    print("search 工具可用")

# 需要保持顺序时
unique_ordered = list(dict.fromkeys(tools))  # ["search", "calculator", "weather"]
```

### 8.3 实用场景二：保护数据不被修改

```python
# 函数返回多个值天然是元组
def get_user_stats():
    return ("张三", [85, 90, 78])

name, scores = get_user_stats()    # 解包

# 如果不希望 scores 被修改，转为元组
frozen_scores = tuple(scores)      # (85, 90, 78)
# frozen_scores[0] = 99  # TypeError: 'tuple' object does not support item assignment
```

### 8.4 实用场景三：字典键值对排序

```python
# 把字典转为 (key, value) 元组列表
config = {"model": "gpt-4o-mini", "temperature": 0.7, "max_tokens": 1000}

# 按键排序
items = list(config.items())
items.sort(key=lambda x: x[0])
print(items)
# [('max_tokens', 1000), ('model', 'gpt-4o-mini'), ('temperature', 0.7)]

# 按值排序
items_by_value = sorted(config.items(), key=lambda x: x[1])
print(items_by_value)
# [('max_tokens', 1000), ('temperature', 0.7), ('model', 'gpt-4o-mini')]
```

### 8.5 实用场景四：合并两个列表为字典

```python
names = ["Alice", "Bob", "Charlie"]
ages = [25, 30, 28]

# 方法1：用 zip
user_dict = dict(zip(names, ages))
# {"Alice": 25, "Bob": 30, "Charlie": 28}

# 方法2：用字典推导式
user_dict = {name: age for name, age in zip(names, ages)}
```

### 8.6 转换频率参考

| 转换 | 频率 | 典型场景 |
|------|------|---------|
| `tuple(list)` / `list(tuple)` | 高 | 数据结构适配、函数参数转换 |
| `set(list)` | 高 | API 响应去重、数据清洗 |
| `list(dict.keys())` / `.values()` / `.items()` | 高 | 遍历字典、字典排序 |
| `dict(zip(keys, values))` | 高 | 合并两个列表为字典 |
| `dict.fromkeys(list)` 保序去重 | 中 | 快速去重且保持原始顺序 |

---

## 9. 练习题

请在 `source/01_python/02_data_structures/exercises.py` 中完成以下练习：

### 练习 1：列表操作

```python
# 给定列表 numbers = [3, 1, 4, 1, 5, 9, 2, 6]
# 完成以下任务：

# 1. 排序（升序）
# 2. 去重（保持排序后的顺序）
# 3. 找出所有偶数
# 4. 计算平均值
# 5. 找出大于平均值的数字
```

### 练习 2：字典操作

```python
# 创建学生成绩字典
scores = {"张三": 85, "李四": 92, "王五": 78}

# 1. 找出最高分的学生
# 2. 计算平均分
# 3. 添加新学生 "赵六" 成绩 88
# 4. 删除成绩最低的学生
# 5. 将成绩转换为等级（90+为A，80+为B，70+为C，其他为D）
```

### 练习 3：列表推导式

```python
# 1. 生成 1-50 中所有能被 3 整除的数的平方列表
# 2. 将列表 ["  hello  ", "  WORLD  ", "  Python  "] 处理为小写且无空格
# 3. 从嵌套列表 [[1,2], [3,4], [5,6]] 中提取所有数字（扁平化）
```

### 练习 4：综合练习

```python
# 有两个列表
names = ["张三", "李四", "王五"]
scores = [85, 92, 78]

# 1. 将它们合并成一个字典
# 2. 添加新学生 "赵六" 成绩 88
# 3. 找出成绩最高的学生
# 4. 按成绩从高到低排序
```

### 练习 5：集合运算

```python
# 有两个团队
team_a = {"张三", "李四", "王五", "赵六"}
team_b = {"王五", "赵六", "钱七", "孙八"}

# 1. 找出同时在两个团队的人
# 2. 找出所有团队成员（去重）
# 3. 找出只在 team_a 的人
# 4. 找出只在一个团队的人
```

### 练习 6：嵌套数据处理

```python
# 模拟 API 返回的数据
data = {
    "users": [
        {"id": 1, "name": "张三", "scores": [85, 90, 88]},
        {"id": 2, "name": "李四", "scores": [92, 88, 95]},
        {"id": 3, "name": "王五", "scores": [78, 82, 80]}
    ]
}

# 1. 提取所有用户名
# 2. 计算每个用户的平均分
# 3. 找出平均分最高的用户
# 4. 找出所有分数大于 90 的记录（用户名 + 具体分数）
```

---

## 10. 小结

### 本节要点

1. **列表（List）**
   - 有序、可变
   - 支持索引、切片
   - 列表推导式是 Python 特色

2. **字典（Dict）**
   - 键值对、可变
   - 推荐使用 `get()` 访问避免 KeyError
   - 字典推导式简洁高效

3. **元组（Tuple）**
   - 有序、不可变
   - 解包特性强大
   - 可作为字典键

4. **集合（Set）**
   - 无序、不重复
   - 支持集合运算
   - 去重首选

### 与 JavaScript 对照表

| 特性 | Python | JavaScript |
|-----|--------|------------|
| 列表/数组 | `[1, 2, 3]` | `[1, 2, 3]` |
| 字典/对象 | `{"key": "value"}` | `{key: "value"}` |
| 负索引 | ✅ `arr[-1]` | ❌（需用 `.at(-1)`） |
| 切片 | ✅ `arr[1:3]` | ❌（需用 `.slice()`） |
| 解构赋值 | `a, b = (1, 2)` | `let [a, b] = [1, 2]` |
| 集合 | `set()` | `new Set()` |
| 推导式 | ✅ `[x*2 for x in arr]` | ❌（需用 `.map()`） |

### 下一节预告

下一节将学习 **字符串与文件基础**：
- 字符串进阶方法
- 文件读写操作
- pathlib 路径处理

---

## 11. 常见问题

### Q: 列表和元组该选哪个？

如果数据需要修改（添加、删除、更新元素），用列表。如果数据是固定的（如配置、常量、函数返回多个值），用元组。

元组的优势：
- 不可变性带来的安全性
- 可以作为字典键
- 性能稍好

### Q: 为什么集合遍历顺序不确定？

集合是基于哈希表实现的，不保证顺序。如果需要有序去重，使用列表 + 手动去重，或使用 `dict.fromkeys()`（Python 3.7+ 字典保持插入顺序）。

```python
# 有序去重
items = [3, 1, 2, 1, 3]
unique_ordered = list(dict.fromkeys(items))  # [3, 1, 2]
```

### Q: 字典的键可以是任意类型吗？

不是。键必须是**可哈希**的类型，即不可变类型：
- ✅ 字符串、数字、元组（元组内元素也必须不可变）
- ❌ 列表、字典、集合

```python
# 正确
d = {(1, 2): "坐标"}

# 错误
# d = {[1, 2]: "坐标"}  # TypeError
```

### Q: 列表推导式和 map/filter 哪个更好？

列表推导式通常更 Pythonic（更符合 Python 风格），可读性更好。map/filter 在函数式编程场景下可能更合适。

```python
# 推荐：列表推导式
evens = [x for x in range(10) if x % 2 == 0]

# 也可以：map/filter
evens = list(filter(lambda x: x % 2 == 0, range(10)))
```

### Q: 如何深拷贝嵌套的数据结构？

使用 `copy` 模块的 `deepcopy`：

```python
import copy

original = {"a": [1, 2, 3]}
shallow = original.copy()       # 浅拷贝
deep = copy.deepcopy(original)  # 深拷贝

shallow["a"].append(4)
print(original)  # {"a": [1, 2, 3, 4]}（受影响）

deep["a"].append(5)
print(original)  # {"a": [1, 2, 3]}（不受影响）
```

### Q: 如何判断变量是什么类型？

```python
# 使用 type()
type([1, 2, 3])          # <class 'list'>
type({"a": 1})           # <class 'dict'>

# 使用 isinstance()（推荐）
isinstance([1, 2, 3], list)      # True
isinstance({"a": 1}, dict)       # True
isinstance((1, 2), (list, tuple))  # True（可以是其中之一）
```

### Q: 为什么元组能作为字典键，而列表不能？

因为字典键必须是**可哈希**（hashable）的。可哈希意味着对象的值在创建后不会改变，这样它才能有一个稳定的哈希值来快速查找。

- **列表**：可变（可以 append、pop 等），值可能变化，所以不可哈希 ❌
- **元组**：不可变，创建后值固定，所以可哈希 ✅

```python
# 元组可以作为字典键
d = {(0, 0): "原点", (1, 0): "东"}
d[(0, 0)]  # "原点"

# 列表不能作为字典键
# d[[0, 0]] = "原点"  # TypeError: unhashable type: 'list'
```

> 这和第 8 节"数据结构相互转换"相关：虽然列表和元组可以相互转换，但**可哈希性**是它们的关键差异之一。

### Q: `list()` 和 `list[1, 2, 3]` 有什么区别？

- `list()` 是**空列表**（调用无参构造函数）
- `list[1, 2, 3]` 是**语法错误**（Python 不允许这样写）

注意区分：
```python
list()           # []（空列表）
list([1, 2, 3])  # [1, 2, 3]（从列表创建列表，实际就是拷贝）
list("abc")      # ['a', 'b', 'c']（从字符串转换）
list[1, 2, 3]    # ❌ 语法错误
list[int]        # ✅ 类型注解（泛型语法）
```

