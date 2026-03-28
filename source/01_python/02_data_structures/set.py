# set 是无序的不重复元素集合 类似数学概念中的集合

# 1. 创建

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

# 2. 添加和删除
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

# 3. 判断
fruits = {"苹果", "香蕉", "橙子"}

"苹果" in fruits      # True
"西瓜" in fruits      # False

# 4. 集合运算
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

# 5. 子集和超集
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

# 6.set推导
# 基本语法
# {表达式 for 变量 in 可迭代对象}

# 示例
squares = {x**2 for x in range(5)}
# {0, 1, 4, 9, 16}

# 去重并转换
numbers = [1, 2, 2, 3, 3, 3, 4]
unique_squares = {x**2 for x in numbers}
# {1, 4, 9, 16}

# 7. 去重

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