from llm_core import ConversationBuffer


def test_conversation_buffer_exports_chat_messages():
    history = ConversationBuffer(system_prompt="你是需求评审助手")
    history.add_user("分析这个需求")
    history.add_assistant("需要关注接口兼容")

    assert history.to_messages() == [
        {"role": "system", "content": "你是需求评审助手"},
        {"role": "user", "content": "分析这个需求"},
        {"role": "assistant", "content": "需要关注接口兼容"},
    ]


def test_conversation_buffer_keeps_system_and_latest_messages():
    history = ConversationBuffer(system_prompt="system", max_messages=3)
    history.add_user("u1")
    history.add_assistant("a1")
    history.add_user("u2")
    history.add_assistant("a2")

    assert history.to_messages() == [
        {"role": "system", "content": "system"},
        {"role": "user", "content": "u2"},
        {"role": "assistant", "content": "a2"},
    ]
