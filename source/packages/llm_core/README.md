# llm_core

需求评审助手的 **LLM 模型交互底座**，供 RAG、Agent、Workflow 与评估观测复用。

## 当前进度（02_llm/03）

```text
llm_core/
├── client.py              # chat + chat_structured
├── structured.py            # build_response_format, StructuredLLMResponse
├── schemas/
│   ├── review.py          # ReviewRisk, ReviewRiskList — Schema 真源
│   └── parse.py           # parse_risk_list, StructuredParseResult
├── prompts/review/        # v1–v4 risk_review
└── providers/
```

- 00：[../../demos/02_first_chat/](../../demos/02_first_chat/)
- 01：[provider_switching.py](../../demos/02_provider_switching/provider_switching.py)
- 02：[prompt_compare.py](../../demos/02_provider_switching/prompt_compare.py)
- 03：[structured_risk.py](../../demos/02_provider_switching/structured_risk.py)

## 03 结构化输出：三层模型

```text
Prompt（软描述）→ response_format（API 约束）→ Pydantic（应用契约，始终执行）
```

日志与 demo 输出统一经 `llm_core.observability.DemoLog`（`[tag]` 块）。

| 层 | 模块 | 作用 |
| --- | --- | --- |
| Schema 真源 | `schemas/review.py` | `ReviewRisk`, `ReviewRiskList`, 枚举 |
| Pydantic → API | `structured.build_response_format` | `none` / `json_object` / `json_schema` |
| 统一调用 | `client.chat_structured` | 调 API + `parse_risk_list` |
| 解析 | `schemas/parse.py` | `error_stage`: `empty` / `json` / `schema` |

## 快速使用

```python
from llm_core import LLMClient, demo_log, parse_risk_list, ReviewRiskList
from llm_core.prompts import get_prompt, render_prompt

# 本地解析（不调用 API）
result = parse_risk_list('{"risks":[{"title":"…","category":"api","level":"high","rationale":"…"}]}')
assert result.ok

# 端到端
client = LLMClient.from_default_config()
tpl = get_prompt("review.risk_review", version="4.0.0")
messages = render_prompt(tpl, {"requirement_text": "…", "evidence_block": "…"})
out = client.chat_structured(
    messages,
    "chat.dev_chat",
    structured_mode="json_object",  # none | json_object | json_schema
)
if out.parse.ok:
    for risk in out.parse.risks:  # list[ReviewRisk]
        print(risk.category, risk.level, risk.title)
```

`json_schema` 模式使用 `ReviewRiskList.model_json_schema()` 构造 API 的 `response_format`。

## 安装

```bash
pip install -e .   # 仓库根目录
```

详见 [course/02_llm/03_structured_outputs.md](../../../course/02_llm/03_structured_outputs.md)。
