# llm_core

需求评审助手的 **LLM 模型交互底座**，供 RAG、Agent、Workflow 与评估观测复用。

## 当前进度（02_llm/01）

```text
llm_core/
├── client.py              # LLMClient.chat(config_ref)
├── config.py              # ModelConfig, LLMResponse, TokenUsage
├── errors.py              # LLMError, LLMErrorCode
├── observability.py       # format_call_log / print_call_log
├── config/models.yaml     # 配置真源
└── providers/
    ├── openai_compat.py
    └── registry.py
```

- 00 demo（直调 SDK）：[../../demos/02_first_chat/](../../demos/02_first_chat/)
- 01 demo（`LLMClient`）：[../../demos/02_provider_switching/](../../demos/02_provider_switching/)

## 快速使用

```python
from llm_core import LLMClient

client = LLMClient.from_default_config()
messages = [
    {"role": "system", "content": "你是需求评审助手。"},
    {"role": "user", "content": "请列出 2 条风险。"},
]
resp = client.chat(messages, "chat.dev_chat", debug=True)
print(resp.content, resp.usage, resp.latency_ms)
```

## 安装

```bash
pip install -e .   # 仓库根目录
```

密钥通过环境变量配置，见根目录 `.env.example`。

详见 [course/02_llm/01_model_api_and_provider_abstraction.md](../../../course/02_llm/01_model_api_and_provider_abstraction.md)。
