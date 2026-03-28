# 数据结构
# 列表、字典、元祖、集合

# 1. 列表 类似数组
# 1.1 直接创建
fruits = ["苹果", "香蕉", "橙子", "葡萄", "西瓜"]
numbers = [1, 2, 3, 4, 5]
mixed = [1, "hello", True, 3.14]  # 可以混合类型（但不推荐）

# 1.2 空列表
empty = []
empty = list() # 通过list方法

# 1.3 从其他序列创建
list_string = list("hello") # ['h', 'e', 'l', 'l', 'o']

# 1.4 正向索引（从 0 开始）
fruits[0]  # "苹果"
fruits[2]  # "橙子"

# 1.5 负向索引（从 -1 开始，-1 表示最后一个）
fruits[-1]  # "西瓜"
fruits[-2]  # "葡萄"

# 索引越界会报错
# fruits[10]  # IndexError: list index out of range

# 2. 切片
# 是 Python 的强大特性，可以轻松获取子列表。
# list[start:end:step]
# start：起始索引（包含，默认 0）
# end：结束索引（不包含，默认到末尾）
# step：步长（默认 1）

numbers = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

# 2.1 基本切片
numbers[2:5]    # [2, 3, 4]（索引 2、3、4）
numbers[:3]     # [0, 1, 2]（前三个）
numbers[7:]     # [7, 8, 9]（从索引 7 到末尾）
numbers[:]      # [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]（完整复制）

# 2.2 步长
numbers[::2]    # [0, 2, 4, 6, 8]（每隔一个取一个）
numbers[1::2]   # [1, 3, 5, 7, 9]（从索引 1 开始，每隔一个）

# 负步长（反转）
numbers[::-1]   # [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]（反转列表）

# 负索引切片
numbers[-3:]    # [7, 8, 9]（最后三个）
numbers[:-2]    # [0, 1, 2, 3, 4, 5, 6, 7]（排除最后两个）

# 2.3 切片是复制不是引用
a = [1, 2, 3]
b = a[:]     # 创建新列表
b[0] = 100
print(a)     # [1, 2, 3]（a 不受影响）

# 对比直接赋值
c = a        # c 和 a 指向同一个列表
c[0] = 100
print(a)     # [100, 2, 3]（a 被修改了）


# 3. 常用方法
# 3.1 添加元素
fruits = ["苹果", "香蕉"]

# append：末尾添加
fruits.append("橙子")  # ["苹果", "香蕉", "橙子"]

# insert：指定位置插入
fruits.insert(1, "葡萄")  # ["苹果", "葡萄", "香蕉", "橙子"]

# extend：添加多个元素（或用 +=）
fruits.extend(["西瓜", "草莓"])  # 末尾添加两个
fruits += ["芒果", "荔枝"]       # 同上

# 3.2 删除元素
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

# 3.3 查找与统计
numbers = [1, 2, 3, 2, 4, 2, 5]

# index：查找元素索引（第一个）
numbers.index(2)        # 1

# count：统计出现次数
numbers.count(2)        # 3

# in：判断是否存在
2 in numbers            # True
10 in numbers           # False

# 3.4 排序和反转
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


numbers = [3, 1, 4, 1, 5]

# 长度
len(numbers)            # 5

# 最大值、最小值、求和
max(numbers)            # 5
min(numbers)            # 1
sum(numbers)            # 14

# 复制
new_list = numbers.copy()

# 4. 列表推导

# 4.1 基本语法
# [表达式 for 变量 in 可迭代对象]
squares = [x**2 for x in range(5)]
# [0, 1, 4, 9, 16]

# 等价于：
squares = []
for x in range(5):
    squares.append(x**2)


# 4.2 带有条件推导
# [表达式 for 变量 in 可迭代对象 if 条件]
evens = [x for x in range(10) if x % 2 == 0]
# [0, 2, 4, 6, 8]

# 等价于：
evens = []
for x in range(10):
    if x % 2 == 0:
        evens.append(x)

# 4.3 if-else 推导
# [表达式1 if 条件 else 表达式2 for 变量 in 可迭代对象]
# 注意：if-else 写在 for 前面

labels = ["偶数" if x % 2 == 0 else "奇数" for x in range(5)]
# ["偶数", "奇数", "偶数", "奇数", "偶数"]
