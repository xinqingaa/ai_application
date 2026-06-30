# llm_core

需求评审助手的 **LLM 模型交互底座**。它不是一个完整 LLM 平台，而是 `02_llm` 阶段沉淀出来的共享 package，供后续 RAG、Agent、Workflow 和评估观测继续复用。

课程正文负责解释为什么这样设计；本 README 负责帮助你读代码、跑 demo、定位模块。

## 当前能力

```text
01 Provider 抽象
业务 messages + config_ref
→ LLMClient.chat
→ Provider
→ LLMResponse

02 Prompt 工程化
prompt_id@version + variables
→ get_prompt / render_prompt
→ messages
→ LLMClient.chat

03 Structured Outputs
messages + response_model + structured_mode
→ chat_structured
→ response_format
→ parse_risk_list
→ StructuredLLMResponse
```

## 模块职责

| 模块 | 职责 | 先读什么 |
| --- | --- | --- |
| `client.py` | 统一调用入口：`chat` / `chat_structured` | `LLMClient.chat` |
| `config.py` | 调用层数据结构：`ModelConfig`、`LLMResponse`、`TokenUsage` | `LLMResponse` |
| `config/models.yaml` | 模型配置真源：`config_ref`、model、base_url、默认参数、能力标签 | `chat.dev_chat` |
| `providers/registry.py` | 读取 YAML，注册 provider，按 `config_ref` 找配置 | `ConfigRegistry.default` |
| `providers/openai_compat.py` | OpenAI-compatible 请求适配与错误映射 | `OpenAICompatProvider.chat` |
| `prompts/registry.py` | 加载 YAML Prompt，按 `prompt_id@version` 渲染 messages | `get_prompt` / `render_prompt` |
| `prompts/review/*.yaml` | 需求评审风险审查 Prompt 版本 | `risk_review_v1`–`v4` |
| `schemas/review.py` | 结构化风险列表 Schema 真源 | `ReviewRisk` / `ReviewRiskList` |
| `schemas/parse.py` | JSON 提取、Pydantic 校验、`error_stage` 判层 | `parse_risk_list` |
| `structured.py` | 构造 `response_format`，封装结构化响应 | `build_response_format` |
| `observability.py` | demo 日志格式与调用详情输出 | `render_call_log` |

## 读代码顺序

### 01：Provider 抽象

1. 先看 [`config/models.yaml`](config/models.yaml)，理解 `chat.dev_chat`、`chat.structured_chat`、`chat.fallback_chat` 的用途。
2. 再看 [`config.py`](config.py) 里的 `ModelConfig` 和 `LLMResponse`。
3. 再看 [`client.py`](client.py) 的 `LLMClient.chat`：查配置、校验 role、找 provider、返回统一响应。
4. 最后看 [`providers/openai_compat.py`](providers/openai_compat.py)：真实 SDK 调用和错误分类。

核心判断：业务层不写具体 model 字符串，而是写 `config_ref`；业务层不读 SDK 原始对象，而是读 `LLMResponse`。

### 02：Prompt 工程化

1. 先看 [`prompts/review/risk_review_v1.yaml`](prompts/review/risk_review_v1.yaml)、`v2`、`v3` 的差异。
2. 再看 [`prompts/registry.py`](prompts/registry.py)：`get_prompt` 如何按 `prompt_id@version` 找模板，`render_prompt` 如何替换变量。
3. 最后看 demo [`prompt_compare.py`](../../demos/02_provider_switching/prompt_compare.py)：同一样例、同一温度下比较三版 Prompt。

核心判断：YAML + `prompt_id@version` 是本项目的实践方案，不是 Prompt 工程唯一标准。通用原则是任务边界清楚、变量来源清楚、改动可回归。

### 03：Structured Outputs

1. 先看 [`schemas/review.py`](schemas/review.py)：应用认可的风险数据结构是什么。
2. 再看 [`structured.py`](structured.py)：`none` / `json_object` / `json_schema` 如何影响 API 请求。
3. 再看 [`schemas/parse.py`](schemas/parse.py)：如何区分 `empty`、`json`、`schema` 失败。
4. 最后看 [`client.py`](client.py) 的 `chat_structured`：调用后立刻 parse，返回 `StructuredLLMResponse`。

核心判断：Pydantic 本地校验是通用原则；`ReviewRiskList` 字段是需求评审助手当前阶段的项目取舍。

## 快速使用

安装：

```bash
pip install -e .   # 仓库根目录
```

普通 chat：

```python
from llm_core import LLMClient

client = LLMClient.from_default_config()
response = client.chat(
    [{"role": "user", "content": "列出这个需求的研发风险"}],
    "chat.dev_chat",
    temperature=0,
)
print(response.model, response.usage, response.content)
```

Prompt 渲染：

```python
from llm_core import LLMClient
from llm_core.prompts import get_prompt, render_prompt

client = LLMClient.from_default_config()
tpl = get_prompt("review.risk_review", version="2.0.0")
messages = render_prompt(tpl, {
    "requirement_text": "订单详情页新增申请售后按钮...",
    "evidence_block": "【Evidence】售后接口 v2...",
})
response = client.chat(messages, tpl.model_config_ref, temperature=0)
```

结构化输出：

```python
from llm_core import LLMClient
from llm_core.prompts import get_prompt, render_prompt

client = LLMClient.from_default_config()
tpl = get_prompt("review.risk_review", version="4.0.0")
messages = render_prompt(tpl, {
    "requirement_text": "订单详情页新增申请售后按钮...",
    "evidence_block": "【Evidence】售后接口 v2...",
})
out = client.chat_structured(
    messages,
    "chat.dev_chat",
    structured_mode="json_object",  # none | json_object | json_schema
)
if out.parse.ok:
    for risk in out.parse.risks:
        print(risk.category, risk.level, risk.title)
else:
    print(out.parse.error_stage, out.parse.message)
```

## 常见定位

| 现象 | 先看哪里 |
| --- | --- |
| Key 未配置、401 | 根目录 `.env` 与 `models.yaml` 的 `api_key_env` |
| 换模型不生效 | `config_ref` 是否指向预期配置；`.env` 占位符是否正确 |
| Prompt 版本找不到 | YAML 内 `prompt_id` / `version`，不是文件名 |
| Evidence 没进 Prompt | `render_prompt` 的 variables 是否传了 `evidence_block` |
| `json_schema` 直接 API 失败 | 供应商是否支持该 `response_format` |
| `error_stage=json` | assistant 原文是否为合法 JSON、是否有围栏或截断 |
| `error_stage=schema` | 字段名、枚举、根形态是否符合 `ReviewRiskList` |

## 对应 demo

- 00 first chat：[../../demos/02_first_chat/](../../demos/02_first_chat/)
- 01 Provider：[../../demos/02_provider_switching/provider_switching.py](../../demos/02_provider_switching/provider_switching.py)
- 02 Prompt：[../../demos/02_provider_switching/prompt_compare.py](../../demos/02_provider_switching/prompt_compare.py)
- 03 Structured Outputs：[../../demos/02_provider_switching/structured_risk.py](../../demos/02_provider_switching/structured_risk.py)

对应课程正文：

- [01 Model API 与 Provider 抽象](../../../course/02_llm/01_model_api_and_provider_abstraction.md)
- [02 面向应用的 Prompt Engineering](../../../course/02_llm/02_prompt_engineering_for_apps.md)
- [03 Structured Outputs](../../../course/02_llm/03_structured_outputs.md)
