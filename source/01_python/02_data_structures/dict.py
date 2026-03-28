# 字典 类似对象和Map

# 1. 创建和访问

# 1.1 创建
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

# 1.2 访问
person = {"name": "张三", "age": 25}

# 通过键访问
person["name"]      # "张三"

# 键不存在会报错
# person["email"]   # KeyError: 'email'

# 使用 get 方法（推荐）
person.get("name")       # "张三"
person.get("email")      # None（不存在返回 None）
person.get("email", "无") # "无"（指定默认值）

# 1.3 修改和添加
person = {"name": "张三", "age": 25}

# 修改
person["age"] = 26

# 添加新键值对
person["email"] = "zhangsan@example.com"

# update：批量更新
person.update({"city": "北京", "age": 27})

# 2. 常用方法

# 2.1 遍历字典

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

person.items() # dict_items([('name', '张三'), ('age', 25), ('city', '北京')]) 可以放在list() 中转成list
# 遍历键值对（最常用）
for key, value in person.items():
    print(f"{key}: {value}")

# 2.2 删除元素

person = {"name": "张三", "age": 25, "city": "北京"}

# del：删除指定键 (为什么不能用 del person.get('city') )
del person["city"]

# pop：删除并返回值
age = person.pop("age")    # 25

# popitem：删除并返回最后一个键值对（Python 3.7+）
item = person.popitem()    # ("name", "张三")

# clear：清空
person.clear()             # {}

# 2.3 setdefault：获取或设置默认值

person = {"name": "张三"}

# 如果键存在，返回值
person.setdefault("name", "默认")  # "张三"

# 如果键不存在，设置默认值并返回
person.setdefault("age", 18)       # 18
print(person)  # {"name": "张三", "age": 18}

# 3. 字典推导
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

# 4. 嵌套字典
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

# 访问嵌套值
users["张三"]["city"]           # "北京"
users["张三"]["hobbies"][0]     # "阅读"

# 安全访问（避免 KeyError）
users.get("张三", {}).get("city")       # "北京"
users.get("王五", {}).get("city", "未知") # "未知"