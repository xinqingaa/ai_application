# 元组 不可变的有序序列，类似list 但是不能修改

# 1. 创建与访问
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


# 访问元素
point = (3, 4)

# 索引（与列表相同）
point[0]            # 3
point[-1]           # 4

# 切片
point[0:1]          # (3,)

# 元组不可修改
# point[0] = 5      # TypeError: 'tuple' object does not support item assignment

# 2. 元组解包 同时给多个变量赋值
# 2.1 基础解包
point = (3, 4)
x, y = point
print(x)  # 3
print(y)  # 4

# 交换变量（经典用法）
a, b = 1, 2
a, b = b, a
print(a, b)  # 2 1

# 2.2 扩展解包
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

# 使用应用
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

# 元组作为字典键
# 用坐标作为键
locations = {
    (0, 0): "原点",
    (1, 0): "x轴正方向",
    (0, 1): "y轴正方向"
}
print(locations[(0, 0)])  # "原点"

# 列表不能作为键
# locations[[0, 0]] = "原点"  # TypeError

