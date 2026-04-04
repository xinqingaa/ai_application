# json_advanced.py
# 练习1：JSON 深入 — 嵌套处理 + 自定义序列化
#
# 运行方式：python json_advanced.py

import json
from datetime import datetime
from enum import StrEnum
from dataclasses import dataclass, asdict


# ============================================================
# 第一部分：复杂嵌套结构处理
# ============================================================

# 模拟 OpenAI API 的响应
MOCK_API_RESPONSE = {
    "id": "chatcmpl-abc123",
    "object": "chat.completion",
    "model": "gpt-4o-mini",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Python 是一门简洁优雅的编程语言。"
            },
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 15,
        "completion_tokens": 20,
        "total_tokens": 35
    }
}

# 模拟多用户数据
USERS_DATA = {
    "users": [
        {
            "name": "张三",
            "age": 25,
            "hobbies": ["reading", "coding", "gaming"],
            "scores": {"math": 85, "english": 92}
        },
        {
            "name": "李四",
            "age": 30,
            "hobbies": ["music", "coding"],
            "scores": {"math": 78, "english": 88}
        },
        {
            "name": "王五",
            "age": 22,
            "hobbies": ["reading", "sports", "cooking"],
            "scores": {"math": 95, "english": 76}
        }
    ]
}

#  安全取值方式：封装工具函数
def get_nested(data, *keys, default=None):
    """安全获取嵌套字典/列表中的值"""
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default)
        elif isinstance(current, list) and isinstance(key, int):
            current = current[key] if 0 <= key < len(current) else default
        else:
            return default
        if current is default:
            return default
    return current


def demo_nested_access():
    """演示嵌套 JSON 的访问方式"""
    print("=" * 50)
    print("📦 嵌套 JSON 访问")
    print("=" * 50)

    resp = MOCK_API_RESPONSE

    # 直接访问 不够安全
    content = resp["choices"][0]["message"]["content"]
    print(f"  回复内容: {content}")
    print(f"  Token 消耗: {resp['usage']['total_tokens']}")

    # 安全访问（用 get_nested 工具函数）
    content = get_nested(resp, "choices", 0, "message", "content", default="")
    model = get_nested(resp, "model", default="unknown")
    print(f"\n  安全取值 - 内容: {content}")
    print(f"  安全取值 - 模型: {model}")

    # 测试缺失路径
    missing = get_nested(resp, "choices", 5, "message", "content", default="未找到")
    print(f"  缺失路径: {missing}")


def demo_data_extraction():
    """演示从嵌套 JSON 提取和统计数据"""
    print("\n" + "=" * 50)
    print("🔍 数据提取与统计")
    print("=" * 50)

    users = USERS_DATA["users"]

    # 1. 提取所有用户名
    names = [u["name"] for u in users]
    print(f"  所有用户: {names}")

    # 2. 统计所有爱好（去重）
    all_hobbies = set()
    for u in users:
        all_hobbies.update(u["hobbies"])
    print(f"  所有爱好: {sorted(all_hobbies)}")

    # 3. 找出年龄最大的用户
    oldest = max(users, key=lambda u: u["age"])
    print(f"  年龄最大: {oldest['name']}（{oldest['age']}岁）")

    # 4. 找出数学最高分
    top_math = max(users, key=lambda u: u["scores"]["math"])
    print(f"  数学最高: {top_math['name']}（{top_math['scores']['math']}分）")

    # 5. 统计每个爱好的人数
    from collections import Counter
    hobby_counter = Counter()
    for u in users:
        hobby_counter.update(u["hobbies"])
    print(f"  爱好统计: {dict(hobby_counter.most_common())}")

    # 6. 筛选：找出喜欢 coding 的用户
    coders = [u["name"] for u in users if "coding" in u["hobbies"]]
    print(f"  喜欢编程: {coders}")


# ============================================================
# 第二部分：自定义序列化
# ============================================================

class ModelProvider(StrEnum):
    OPENAI = "openai"
    CLAUDE = "claude"
    DEEPSEEK = "deepseek"


@dataclass
class ChatMessage:
    role: str
    content: str
    timestamp: datetime
    provider: ModelProvider


def json_serializer(obj):
    """自定义序列化函数：处理 json.dumps 不认识的类型"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, StrEnum):
        return obj.value
    raise TypeError(f"类型 {type(obj)} 无法序列化")


class AppJSONEncoder(json.JSONEncoder):
    """自定义 JSON 编码器"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, StrEnum):
            return obj.value
        return super().default(obj)


def demo_custom_serialization():
    """演示自定义 JSON 序列化"""
    print("\n" + "=" * 50)
    print("🔧 自定义序列化")
    print("=" * 50)

    msg = ChatMessage(
        role="user",
        content="你好，请介绍一下 Python",
        timestamp=datetime(2026, 3, 23, 14, 30, 0),
        provider=ModelProvider.OPENAI,
    )

    # 方式一：asdict + default 参数
    print("\n  方式一：default 参数")
    result = json.dumps(
        asdict(msg),
        default=json_serializer,
        ensure_ascii=False,
        indent=2,
    )
    print(f"  {result}")

    # 方式二：JSONEncoder 子类
    print("\n  方式二：JSONEncoder 子类")
    result = json.dumps(
        asdict(msg),
        cls=AppJSONEncoder,
        ensure_ascii=False,
        indent=2,
    )
    print(f"  {result}")

    # 序列化列表
    messages = [
        asdict(ChatMessage("system", "你是助手", datetime(2026, 3, 23, 14, 0), ModelProvider.OPENAI)),
        asdict(ChatMessage("user", "你好", datetime(2026, 3, 23, 14, 30), ModelProvider.OPENAI)),
    ]
    print("\n  序列化消息列表:")
    print(json.dumps(messages, default=json_serializer, ensure_ascii=False, indent=2))


def demo_json_file_io():
    """演示 JSON 文件读写"""
    print("\n" + "=" * 50)
    print("📄 JSON 文件读写")
    print("=" * 50)

    import os

    data = {
        "app": "AI Chat",
        "version": "1.0",
        "conversations": [
            {
                "id": 1,
                "messages": [
                    {"role": "user", "content": "你好"},
                    {"role": "assistant", "content": "你好！有什么可以帮你的？"},
                ]
            }
        ]
    }

    filepath = "demo_output.json"

    # 写入
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  ✅ 写入: {filepath}")

    # 读取
    with open(filepath, "r", encoding="utf-8") as f:
        loaded = json.load(f)

    # 验证
    first_msg = loaded["conversations"][0]["messages"][0]
    print(f"  ✅ 读取验证: {first_msg['role']} → {first_msg['content']}")

    # 清理
    os.remove(filepath)
    print(f"  🧹 已清理: {filepath}")


if __name__ == "__main__":
    print("\n🐍 练习1：JSON 深入处理\n")
    demo_nested_access()
    demo_data_extraction()
    demo_custom_serialization()
    demo_json_file_io()
    print("\n✅ 全部完成！")
