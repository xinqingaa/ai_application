"""
01_basics 练习参考答案

运行方式：
python source/01_python/01_basics/reference.py
"""


def exercise_2_message() -> str:
    name: str = "张三"
    age: int = 18
    score: float = 95.5
    is_student: bool = True
    return f"{name}今年{age}岁，分数{score}，是学生吗？{is_student}"


def exercise_3_get_grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def exercise_4_even_sum(limit: int) -> int:
    total = 0
    for number in range(1, limit + 1):
        if number % 2 == 0:
            total += number
    return total


def exercise_5_multiplication_table() -> list[str]:
    lines: list[str] = []

    for row in range(1, 10):
        parts: list[str] = []
        for column in range(1, row + 1):
            parts.append(f"{row}x{column}={row * column}")
        lines.append(" ".join(parts))

    return lines


def main() -> None:
    print("练习 2：")
    print(exercise_2_message())

    print("\n练习 3：")
    for score in [95, 83, 72, 60, 45]:
        print(f"score = {score}, grade = {exercise_3_get_grade(score)}")

    print("\n练习 4：")
    print(f"1 到 100 的偶数和: {exercise_4_even_sum(100)}")

    print("\n练习 5：")
    for line in exercise_5_multiplication_table():
        print(line)


if __name__ == "__main__":
    main()
