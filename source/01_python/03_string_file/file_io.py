# ========================================
# 3.1 open() 函数基础 - 读取文件 r
# ========================================

# 方式 1：读取全部内容
file = open("source/01_python/03_string_file/data/example.txt", "r", encoding="utf-8")
content = file.read()
print(content)
file.close()

# 方式 2：逐行读取
file = open("source/01_python/03_string_file/data/example.txt", "r", encoding="utf-8")
for line in file:
    print(line.strip())
file.close()

# 方式 3：读取所有行为列表
file = open("source/01_python/03_string_file/data/example.txt", "r", encoding="utf-8")
lines = file.readlines()
print(lines)
file.close()


# ========================================
# 3.1 open() 函数基础 - 写入文件 w a r
# ========================================

# 覆盖写入
file = open("source/01_python/03_string_file/data/output.txt", "w", encoding="utf-8")
file.write("Hello World\n")
file.write("第二行")
file.close()

# 追加写入
file = open("source/01_python/03_string_file/data/output.txt", "a", encoding="utf-8")
file.write("\n这是追加的内容")
file.close()

# 验证：读取看看写入是否成功
file = open("source/01_python/03_string_file/data/output.txt", "r", encoding="utf-8")
print(file.read())
file.close()