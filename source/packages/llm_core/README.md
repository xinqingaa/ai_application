# llm_core

需求评审助手的 **LLM 模型交互底座**。它不是完整 LLM 平台，而是 `02_llm` 阶段沉淀出来的共享 package，供后续 RAG、Agent、Workflow、评估观测和 AI Native 工作台继续复用。

课程正文负责解释为什么这样设计；本 README 负责帮助你读代码、跑 demo、定位模块。

## 当前能力

```text
01 Provider 抽象
messages + config_ref
→ LLMClient.chat
→ Provider
→ LLMResponse

02 Prompt 工程化
prompt_id@version + variables
→ render_prompt
→ messages
→ LLMClient.chat

03 Structured Outputs
messages + structured_mode
→ chat_structured
→ response_format + parse_risk_list
→ StructuredLLMResponse

04 Streaming + Conversation
messages + config_ref
→ LLMClient.stream_chat
→ LLMStreamEvent
→ FastAPI SSE

05 Context Engineering
requirement + candidate sources + policy
→ build_review_context
→ prompt variables + context report

06 Reliability + Degradation
messages + primary config_ref
→ ReliableLLMService
→ retry / fallback / parse validation
→ ReliableCallResult + ReliableCallReport

07 Calling Harness
case set + run config
→ LLMCallingHarness
→ HarnessRunRecord + HarnessSummary
```

## 模块职责

| 模块 | 职责 | 先读什么 |
| --- | --- | --- |
| `client/` | 统一调用入口：`chat` / `stream_chat` / `chat_structured` | `client/service.py` |
| `config/` | `ModelConfig`、`LLMResponse`、`models.yaml` | `config/models.yaml` |
| `providers/` | OpenAI-compatible 请求适配与错误映射 | `providers/openai_compat.py` |
| `prompts/` | YAML Prompt 加载、版本化与渲染 | `prompts/registry.py` |
| `schemas/` | 需求评审结构化 schema 与解析结果 | `schemas/review.py` / `schemas/parse.py` |
| `structured/` | `response_format` 构造与结构化响应包装 | `structured/response.py` |
| `streaming/` | 流式事件模型与 SSE 编码 | `streaming/events.py` |
| `conversation/` | 最小会话历史缓存 | `conversation/buffer.py` |
| `context/` | 上下文候选、策略、预算、压缩和引用候选 | `context/builder.py` |
| `errors/` | 全局 LLM 错误分类 | `errors/types.py` |
| `reliability/` | 重试、降级、attempt report、可靠调用服务 | `reliability/service.py` |
| `harness/` | 批量 case 调用记录与汇总 | `harness/runner.py` |
| `observability/` | demo 日志格式与调用详情输出 | `observability/demo_log.py` |

## 读代码顺序

### 01 Provider

1. [`config/models.yaml`](config/models.yaml)：理解 `chat.dev_chat`、`chat.structured_chat`、`chat.fallback_chat`。
2. [`config/types.py`](config/types.py)：理解 `ModelConfig` 和 `LLMResponse`。
3. [`client/service.py`](client/service.py)：`LLMClient.chat` 如何查配置、校验 role、调用 provider。
4. [`providers/openai_compat.py`](providers/openai_compat.py)：真实 SDK 调用和错误映射。

### 02 Prompt

1. [`prompts/review/risk_review_v1.yaml`](prompts/review/risk_review_v1.yaml) 到 `v4`：Prompt 版本如何演进。
2. [`prompts/registry.py`](prompts/registry.py)：`get_prompt` / `render_prompt`。
3. demo [`02_model_contracts/prompt_compare.py`](../../demos/02_model_contracts/prompt_compare.py)：同一样例比较 Prompt 版本。

### 03 Structured Outputs

1. [`schemas/review.py`](schemas/review.py)：应用认可的风险数据结构。
2. [`structured/response.py`](structured/response.py)：`none` / `json_object` / `json_schema` 如何影响请求。
3. [`schemas/parse.py`](schemas/parse.py)：`empty`、`json`、`schema` 失败如何判层。
4. [`client/service.py`](client/service.py)：`chat_structured` 调用后立刻 parse。

### 04 Streaming + Conversation

1. [`streaming/events.py`](streaming/events.py)：`LLMStreamEvent` 与 `encode_sse`。
2. [`providers/openai_compat.py`](providers/openai_compat.py)：供应商 chunk 如何翻译成事件。
3. [`conversation/buffer.py`](conversation/buffer.py)：只有稳定消息进入 history。
4. app [`02_llm_streaming_api`](../../apps/02_llm_streaming_api/)：SSE 如何暴露给前端。

### 05 Context

1. [`context/types.py`](context/types.py)：`ContextSource`、`ContextBuildPolicy`、`ContextBuildReport`。
2. [`context/policies.py`](context/policies.py)：`minimal` / `balanced` / `evidence_first` / `tight_budget`。
3. [`context/builder.py`](context/builder.py)：去重、排序、预算、压缩、引用候选。
4. demo [`02_context_lab/context_compare.py`](../../demos/02_context_lab/context_compare.py)：观察 context report。

### 06 Reliability

1. [`errors/types.py`](errors/types.py)：统一错误码。
2. [`reliability/policies.py`](reliability/policies.py)：`RetryPolicy` / `DegradationPolicy`。
3. [`reliability/report.py`](reliability/report.py)：attempt、report、result。
4. [`reliability/service.py`](reliability/service.py)：如何包住 `LLMClient`。
5. demo [`02_call_ops_lab/reliability_compare.py`](../../demos/02_call_ops_lab/reliability_compare.py)：观察 retry / fallback。

### 07 Harness

1. [`harness/cases.py`](harness/cases.py)：`HarnessCase` 与 `HarnessRunConfig`。
2. [`harness/records.py`](harness/records.py)：`HarnessRunRecord` 与 `HarnessSummary`。
3. [`harness/runner.py`](harness/runner.py)：批量运行如何复用 `ReliableLLMService`。
4. [`harness/formatting.py`](harness/formatting.py)：demo 的记录表和汇总输出。
5. demo [`02_call_ops_lab/harness_compare.py`](../../demos/02_call_ops_lab/harness_compare.py)：观察 case 批量运行。

## 快速使用

安装：

```bash
uv sync
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

可靠调用：

```python
from llm_core import LLMClient, ReliableLLMService, RetryPolicy

service = ReliableLLMService(LLMClient.from_default_config())
result = service.chat(
    [{"role": "user", "content": "列出这个需求的研发风险"}],
    "chat.dev_chat",
    retry_policy=RetryPolicy(max_attempts=2),
    temperature=0,
)
print(result.ok, result.report.attempt_count, result.report.degraded)
```

批量 harness：

```python
from llm_core import HarnessCase, HarnessRunConfig, LLMCallingHarness, LLMClient, ReliableLLMService

cases = [
    HarnessCase.from_user_input(
        case_id="S1",
        title="售后入口",
        user_input="订单详情页新增申请售后入口。",
    )
]
service = ReliableLLMService(LLMClient.from_default_config())
records, summary = LLMCallingHarness(service).run_cases(
    cases,
    HarnessRunConfig(run_name="risk_review_smoke"),
)
print(summary.success_count, records[0].attempt_count)
```

## 对应入口

- 00 SDK 最小调用：[../../demos/02_llm_basics/](../../demos/02_llm_basics/)
- 01–03 模型契约 lab：[../../demos/02_model_contracts/](../../demos/02_model_contracts/)
- 04 Streaming SSE：[../../apps/02_llm_streaming_api/](../../apps/02_llm_streaming_api/)
- 05 Context lab：[../../demos/02_context_lab/](../../demos/02_context_lab/)
- 06–08 Call ops lab：[../../demos/02_call_ops_lab/](../../demos/02_call_ops_lab/)

## 常见定位

| 现象 | 先看哪里 |
| --- | --- |
| Key 未配置、401 | 根目录 `.env` 与 `models.yaml` 的 `api_key_env` |
| 换模型不生效 | `config_ref` 是否指向预期配置；`.env` 占位符是否正确 |
| Prompt 版本找不到 | YAML 内 `prompt_id` / `version`，不是文件名 |
| `json_schema` API 失败 | 供应商是否支持该 `response_format` |
| `error_stage=json` | assistant 原文是否为合法 JSON、是否有围栏或截断 |
| 模型没有引用证据 | `context.included_source_ids` 是否为空；`evidence_block` 是否含 source id |
| 关键证据没进 Prompt | `dropped_source_ids` 与 `token_budget` |
| 模型调用偶发失败 | `ReliableCallReport.attempts` 里每次 attempt 的错误码 |
| 不知道是否发生降级 | `ReliableCallReport.degraded` 与 `final_config_ref` |
| 不知道一批 case 是否退化 | `HarnessSummary` 的成功率、解析成功率、错误分布 |

## 对应课程正文

- [01 Model API 与 Provider 抽象](../../../course/02_llm/01_model_api_and_provider_abstraction.md)
- [02 面向应用的 Prompt Engineering](../../../course/02_llm/02_prompt_engineering_for_apps.md)
- [03 Structured Outputs](../../../course/02_llm/03_structured_outputs.md)
- [04 Streaming 与 Conversation](../../../course/02_llm/04_streaming_and_conversation.md)
- [05 Context Engineering](../../../course/02_llm/05_context_engineering.md)
- [06 Reliability、Errors 与 Degradation](../../../course/02_llm/06_reliability_errors_and_degradation.md)
- [07 LLM Calling Harness](../../../course/02_llm/07_llm_calling_harness.md)
