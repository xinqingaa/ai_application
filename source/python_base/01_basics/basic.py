# 1. 声明变量

# 方式1 不声明类型 直接赋值
age = 25
weight = 60.4
# 方式2 类型注解 
name:str = "xiaoming";
msg1 = f"我的名字是 {name} 年龄{age} 体重{weight}" 
print(msg1);

# 2. 数据类型

# - int  整数
# - float  浮点数
# - str  字符串
# - bool  布尔值
# - None  空
type(42)        # <class 'int'>
type(3.14)      # <class 'float'>
type("hello")   # <class 'str'>
type(True)      # <class 'bool'>
type(None)      # <class 'NoneType'>
msg2 = f"name是 {type(name)} age是 {type(age)} weiget是{type(weight)}" 
print(msg2);

# 3. 类型转换

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

# 4. 字符串操作

# - f-string 格式化（前两个日志输出）
# - 格式化数字
print(f"明年{age + 1}岁")  # 明年26岁
score = 95.5678
print(f"分数：{score:.2f}")  # 分数：95.57

# 5. 字符串方法

# - strip  去除首尾空格
# - lower / upper  转换大小写
# - find / replace  查找和替换
# - split / join  分割和连接
# - startswith / endswith  判断开头/结尾
# - leb 字符串长度
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
"hello.py".endswith("py")      # True
name = "张三"
len(name)  # 2（Python 3 中中文按字符计数）

# 6. 控制流

# if / elif / else
# 作用域无{} 通过锁进表示代码块
print(f"第一个 score {score} 类型 {type(score)}")
score = 85 # 重复声明时会直接覆盖之前的变量
print(f"第二个 score {score} 类型 {type(score)}")
if score >= 90:
    print("优秀")
elif score >= 85:
    print("良好")
elif score >= 60:
    print("及格")
else:
    print("不及格")

# 7. 逻辑运算符

# and  与 （类似 &&）
# or  或  （类似 ||）
# not  非  (类似 !)
# ==  等于
# !=  不等于
# >   大于
# <   小于
# >=  大于等于
# <=  小于等于
# is  是否为同一对象（身份比较）

has_id = False
age = 88

if age >= 18 and has_id:
    print("可以进入")

# 或（or）
if age < 12 or age > 65:
    print("票价优惠")

# 非（not）
if not has_id:
    print("请出示证件")

# 8. 遍历语句
# for 循环 可以遍历列表和字符串
# range() 可以指定范围、步长
# enumerate()：同时获取索引和值
# while 循环
# break  跳出循环
# continue 跳出本次
# pass 占位

#  for循环
fruits = ["苹果", "香蕉", "橙子"]

# 遍历列表
for fruit in fruits:
    print(f"{fruit}")
# 输出：
# 苹果
# 香蕉
# 橙子

# 遍历字符串
for char in "Hello":
    print(char)
# 输出：H e l l o（每行一个）

# range()
# range(n)：0 到 n-1
for i in range(2):
    print(i)  # 0, 1

# range(start, end)：start 到 end-1
for i in range(0, 3):
    print(i)  # 0, 1, 2

# range(start, end, step)：指定步长
for i in range(0, 10, 3):
    print(i)  # 0, 3, 6, 9

# enumerate 获取索引
for index, fruit in enumerate(fruits):
    print(f"{index}: {fruit}")

# while循环
count = 0

while count < 2:
    print(count)
    count += 1  # 注意：Python 没有 count++
# 输出：0, 1


# break 跳出循环
for i in range(10):
    if i == 1:
        break
    print(i)
# 输出：0

# continue 跳出本次
for i in range(3):
    if i == 1:
        continue
    print(i)
# 输出：0, 2（跳过了 1）


if score >= 60:
    pass  # TODO: 后续实现
else:
    print("不及格")