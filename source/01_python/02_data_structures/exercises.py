# 02. 数据结构 - 练习题
# 请在下方完成练习

# ============================================
# 练习 1：列表操作
# ============================================

def exercise_1():
    """列表操作练习"""
    numbers = [3, 1, 4, 1, 5, 9, 2, 6]

    # 1. 排序（升序）
    sorted_numbers = None  # TODO: 你的代码

    # 2. 去重（保持排序后的顺序）
    unique_numbers = None  # TODO: 你的代码

    # 3. 找出所有偶数
    even_numbers = None  # TODO: 你的代码

    # 4. 计算平均值
    average = None  # TODO: 你的代码

    # 5. 找出大于平均值的数字
    above_average = None  # TODO: 你的代码

    print(f"排序后: {sorted_numbers}")
    print(f"去重后: {unique_numbers}")
    print(f"偶数: {even_numbers}")
    print(f"平均值: {average}")
    print(f"大于平均值的数: {above_average}")


# ============================================
# 练习 2：字典操作
# ============================================

def exercise_2():
    """字典操作练习"""
    scores = {"张三": 85, "李四": 92, "王五": 78}

    # 1. 找出最高分的学生
    top_student = None  # TODO: 你的代码

    # 2. 计算平均分
    average_score = None  # TODO: 你的代码

    # 3. 添加新学生 "赵六" 成绩 88
    # TODO: 你的代码

    # 4. 删除成绩最低的学生
    # TODO: 你的代码

    # 5. 将成绩转换为等级（90+为A，80+为B，70+为C，其他为D）
    grade_dict = {}  # TODO: 你的代码

    print(f"最高分学生: {top_student}")
    print(f"平均分: {average_score}")
    print(f"添加后: {scores}")
    print(f"删除最低分后: {scores}")
    print(f"等级: {grade_dict}")


# ============================================
# 练习 3：列表推导式
# ============================================

def exercise_3():
    """列表推导式练习"""

    # 1. 生成 1-50 中所有能被 3 整除的数的平方列表
    squares_divisible_by_3 = None  # TODO: 你的代码

    # 2. 将列表处理为小写且无空格
    words = ["  hello  ", "  WORLD  ", "  Python  "]
    cleaned_words = None  # TODO: 你的代码

    # 3. 从嵌套列表中提取所有数字（扁平化）
    nested = [[1, 2], [3, 4], [5, 6]]
    flattened = None  # TODO: 你的代码

    print(f"能被3整除的平方数: {squares_divisible_by_3}")
    print(f"清理后的单词: {cleaned_words}")
    print(f"扁平化结果: {flattened}")


# ============================================
# 练习 4：综合练习
# ============================================

def exercise_4():
    """综合练习"""
    names = ["张三", "李四", "王五"]
    scores = [85, 92, 78]

    # 1. 将它们合并成一个字典
    student_dict = None  # TODO: 你的代码

    # 2. 添加新学生 "赵六" 成绩 88
    # TODO: 你的代码

    # 3. 找出成绩最高的学生
    top_student = None  # TODO: 你的代码

    # 4. 按成绩从高到低排序（返回列表）
    sorted_students = None  # TODO: 你的代码

    print(f"合并后: {student_dict}")
    print(f"添加后: {student_dict}")
    print(f"最高分学生: {top_student}")
    print(f"排序后: {sorted_students}")


# ============================================
# 练习 5：集合运算
# ============================================

def exercise_5():
    """集合运算练习"""
    team_a = {"张三", "李四", "王五", "赵六"}
    team_b = {"王五", "赵六", "钱七", "孙八"}

    # 1. 找出同时在两个团队的人（交集）
    both_teams = None  # TODO: 你的代码

    # 2. 找出所有团队成员（并集）
    all_members = None  # TODO: 你的代码

    # 3. 找出只在 team_a 的人（差集）
    only_a = None  # TODO: 你的代码

    # 4. 找出只在一个团队的人（对称差集）
    in_one_team = None  # TODO: 你的代码

    print(f"两个团队都有: {both_teams}")
    print(f"所有成员: {all_members}")
    print(f"只在 A 团队: {only_a}")
    print(f"只在一个团队: {in_one_team}")


# ============================================
# 练习 6：嵌套数据处理
# ============================================

def exercise_6():
    """嵌套数据处理练习"""
    data = {
        "users": [
            {"id": 1, "name": "张三", "scores": [85, 90, 88]},
            {"id": 2, "name": "李四", "scores": [92, 88, 95]},
            {"id": 3, "name": "王五", "scores": [78, 82, 80]}
        ]
    }

    # 1. 提取所有用户名
    names = None  # TODO: 你的代码

    # 2. 计算每个用户的平均分（返回字典 {name: average}）
    averages = None  # TODO: 你的代码

    # 3. 找出平均分最高的用户
    top_user = None  # TODO: 你的代码

    # 4. 找出所有分数大于 90 的记录（返回列表 [{name, score}, ...]）
    high_scores = None  # TODO: 你的代码

    print(f"所有用户名: {names}")
    print(f"平均分: {averages}")
    print(f"最高分用户: {top_user}")
    print(f"90分以上记录: {high_scores}")


# ============================================
# 运行所有练习
# ============================================

if __name__ == "__main__":
    print("=" * 50)
    print("练习 1：列表操作")
    print("=" * 50)
    exercise_1()

    print("\n" + "=" * 50)
    print("练习 2：字典操作")
    print("=" * 50)
    exercise_2()

    print("\n" + "=" * 50)
    print("练习 3：列表推导式")
    print("=" * 50)
    exercise_3()

    print("\n" + "=" * 50)
    print("练习 4：综合练习")
    print("=" * 50)
    exercise_4()

    print("\n" + "=" * 50)
    print("练习 5：集合运算")
    print("=" * 50)
    exercise_5()

    print("\n" + "=" * 50)
    print("练习 6：嵌套数据处理")
    print("=" * 50)
    exercise_6()
