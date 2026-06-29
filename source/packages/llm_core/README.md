# llm_core

需求评审助手的 **LLM 模型交互底座**，供 RAG、Agent、Workflow 与评估观测复用。

## 当前进度（02_llm/02）

```text
llm_core/
├── client.py
├── config.py / config/models.yaml
├── errors.py
├── observability.py
├── prompts/                 # 02：YAML 模板 + render
│   └── review/
│       ├── risk_review_v1.yaml
│       ├── risk_review_v2.yaml
│       └── risk_review_v3.yaml
└── providers/
```

每个 yaml 含 `prompt_id` 与 `version` 字段；`get_prompt(id, version)` **按字段匹配**，文件名 `risk_review_v1.yaml` 等仅为可读性。与 demo 配置对照见 02 正文。

- 00 demo：[../../demos/02_first_chat/](../../demos/02_first_chat/)
- 01 demo：[../../demos/02_provider_switching/provider_switching.py](../../demos/02_provider_switching/provider_switching.py)
- 02 demo：[../../demos/02_provider_switching/prompt_compare.py](../../demos/02_provider_switching/prompt_compare.py)

## 快速使用（01 调用）

```python
from llm_core import LLMClient

client = LLMClient.from_default_config()
messages = [
    {"role": "system", "content": "你是需求评审助手。"},
    {"role": "user", "content": "请列出 2 条风险。"},
]
resp = client.chat(messages, "chat.dev_chat", debug=True)
```

## 快速使用（02 Prompt）

```python
from llm_core import LLMClient
from llm_core.prompts import get_prompt, render_prompt

tpl = get_prompt("review.risk_review", version="2.0.0")
messages = render_prompt(tpl, {
    "requirement_text": "【PRD 片段】…",
    "evidence_block": "（检索证据或静态 fixture）",
})
resp = client.chat(messages, tpl.model_config_ref, temperature=0)
```

## 安装

```bash
pip install -e .   # 仓库根目录
```

详见 [course/02_llm/02_prompt_engineering_for_apps.md](../../../course/02_llm/02_prompt_engineering_for_apps.md)。
