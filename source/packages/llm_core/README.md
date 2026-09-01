# llm_core

需求评审助手的 **LLM 模型交互底座**。它不是完整 LLM 平台，而是供 RAG、Agent、Workflow、评估观测和 AI Native 工作台共同复用的共享 package。

课程正文负责解释为什么这样设计；本 README 负责帮助你读代码、跑 demo、定位模块。

日志、颜色、终端表格与 JSON Lines 由全仓共享的 [`app_log`](../app_log/) 负责。`llm_core` 只产生统一响应、诊断和结构化日志事件，不维护自己的终端输出子模块。

## 已实现能力不等于当前学习顺序

`llm_core` 已经包含多个可复用模块，但模块存在不会自动启用功能，也不会自动发起模型请求。真正参与一次运行的能力由 demo、app 或产品代码显式调用。

学习时先由 [标准学习路径](../../../course/learning-path.md) 确定当前机制，再按本 README 阅读对应代码。不要按照下面的模块排列推断课程顺序。

```text
Provider 抽象
messages + config_ref
→ LLMClient.chat
→ Provider
→ LLMResponse

Embedding
texts + embedding config_ref
→ LLMClient.embed
→ Provider
→ EmbeddingResponse

Prompt 工程化
prompt_id@version + variables
→ render_prompt
→ messages
→ LLMClient.chat

结构化输出
messages + structured_mode
→ chat_structured
→ response_format + parse_risk_list
→ StructuredLLMResponse

Reliability + Degradation
messages + primary config_ref
→ ReliableLLMService
→ retry / fallback / parse validation
→ ReliableCallResult + ReliableCallReport

Context Engineering
requirement + candidate sources + policy
→ build_review_context
→ prompt variables + context report

Calling Harness
case set + run config
→ LLMCallingHarness
→ HarnessRunRecord + HarnessSummary

按需 Streaming + Conversation
messages + config_ref
→ LLMClient.stream_chat
→ LLMStreamEvent
→ FastAPI SSE

Cost / Latency / Cache
harness records + learning price table + cache key
→ cost estimate + cache diagnostics
→ cost / latency baseline
```

不使用 `COURSE_STAGE`、`ENABLE_CONTEXT` 一类环境变量隐藏尚未学习的模块。`.env` 只管理密钥、endpoint 和模型选择；项目功能是否启用，应由真实业务 Pipeline 显式组合，而不是由课程进度控制。

## 模块职责

| 模块 | 职责 | 先读什么 |
| --- | --- | --- |
| `client/` | 统一调用入口：`chat` / `embed` / `stream_chat` / `chat_structured` | `client/service.py` |
| `config/` | `ModelConfig`、`LLMResponse`、`EmbeddingResponse`、`models.yaml` | `config/models.yaml` |
| `providers/` | OpenAI-compatible chat / embedding 请求适配与错误映射 | `providers/openai_compat.py` |
| `prompts/` | YAML Prompt 加载、版本化与渲染 | `prompts/registry.py` |
| `schemas/` | 需求评审结构化 schema 与解析结果 | `schemas/review.py` / `schemas/parse.py` |
| `structured/` | `response_format` 构造与结构化响应包装 | `structured/response.py` |
| `streaming/` | 流式事件模型与 SSE 编码 | `streaming/events.py` |
| `conversation/` | 最小会话历史缓存 | `conversation/buffer.py` |
| `context/` | 上下文候选、策略、预算、压缩和引用候选 | `context/builder.py` |
| `errors/` | 全局 LLM 错误分类 | `errors/types.py` |
| `reliability/` | 重试、降级、attempt report、可靠调用服务 | `reliability/service.py` |
| `harness/` | 批量 case 调用记录与汇总 | `harness/runner.py` |
| `costing/` | 学习用价格表、token 成本估算 | `costing/estimate.py` |
| `cache/` | 本地 exact-match cache key 与命中统计 | `cache/keys.py` |

## 按标准学习路径读代码

下面只规定每项能力内部如何读，不建立第二套课程顺序。

### Provider 抽象

1. [`config/models.yaml`](config/models.yaml)：理解 chat 配置与独立的 `embedding.default_embed`。
2. [`config/types.py`](config/types.py)：理解 `ModelConfig` 和 `LLMResponse`。
3. [`client/service.py`](client/service.py)：`LLMClient.chat` 如何查配置、校验 role、调用 provider。
4. [`providers/openai_compat.py`](providers/openai_compat.py)：真实 SDK 调用和错误映射。

### Embedding

1. [`config/models.yaml`](config/models.yaml)：确认 Embedding 使用独立 key、base URL 和模型配置。
2. [`config/types.py`](config/types.py)：理解 `EmbeddingResponse` 的向量顺序、维度、usage 和模型信息。
3. [`client/service.py`](client/service.py)：理解 `LLMClient.embed` 的 role 与输入校验。
4. [`providers/openai_compat.py`](providers/openai_compat.py)：理解真实 `embeddings.create`、返回顺序校验和错误映射。
5. demo [`rag_retrieval_lab`](../../demos/rag_retrieval_lab/)：观察真实向量与成对相似度。

### Prompt 工程

1. [`prompts/review/risk_review_v1.yaml`](prompts/review/risk_review_v1.yaml) 到 `v5`：Prompt 怎样从直接调用演进到动态 Citation Candidate 边界。
2. [`prompts/registry.py`](prompts/registry.py)：`get_prompt` / `render_prompt`。
3. demo [`llm_invoke_lab/prompt_compare.py`](../../demos/llm_invoke_lab/prompt_compare.py)：同一样例比较 Prompt 版本。

### Structured Outputs

1. [`schemas/review.py`](schemas/review.py)：应用认可的风险数据结构。
2. [`structured/response.py`](structured/response.py)：`none` / `json_object` / `json_schema` 如何影响请求。
3. [`schemas/parse.py`](schemas/parse.py)：`empty`、`json`、`schema` 失败如何判层。
4. [`client/service.py`](client/service.py)：`chat_structured` 调用后立刻 parse。

### Reliability

1. [`errors/types.py`](errors/types.py)：统一错误码。
2. [`reliability/policies.py`](reliability/policies.py)：`RetryPolicy` / `DegradationPolicy`。
3. [`reliability/report.py`](reliability/report.py)：attempt、report、result。
4. [`reliability/service.py`](reliability/service.py)：如何包住 `LLMClient`。
5. demo [`llm_reliability_lab/reliability_compare.py`](../../demos/llm_reliability_lab/reliability_compare.py)：观察 retry / fallback。

### Context Engineering

标准学习路径完成文档、Chunk 和 Retriever 前置后，从 RAG 适配进入：

1. [`context/types.py`](context/types.py)：`ContextSource`、`ContextBuildPolicy`、`ContextBuildReport`。
2. [`context/policies.py`](context/policies.py)：`minimal` / `balanced` / `evidence_first` / `tight_budget`。
3. [`context/builder.py`](context/builder.py)：去重、排序、预算、压缩、引用候选。
4. [`rag_core/context/adapter.py`](../rag_core/context/adapter.py)：把 RetrievalResult 的身份、locator 和诊断接入 ContextSource。
5. demo [`rag_retrieval_lab/inspect_rag_context.py`](../../demos/rag_retrieval_lab/inspect_rag_context.py)：观察真实候选的 Context Report。
6. demo [`llm_context_lab/context_compare.py`](../../demos/llm_context_lab/context_compare.py)：用静态材料离线观察 Builder 策略。

### Calling Harness

1. [`harness/cases.py`](harness/cases.py)：`HarnessCase` 与 `HarnessRunConfig`。
2. [`harness/records.py`](harness/records.py)：`HarnessRunRecord` 与 `HarnessSummary`。
3. [`harness/runner.py`](harness/runner.py)：批量运行如何复用 `ReliableLLMService`。
4. [`harness/formatting.py`](harness/formatting.py)：demo 的记录表和汇总输出。
5. demo [`llm_regression_lab/harness_compare.py`](../../demos/llm_regression_lab/harness_compare.py)：观察 case 批量运行。

### Streaming + Conversation

Agent 产品需要用这些能力表达增量输出、结构化事件和会话状态：

1. [`streaming/events.py`](streaming/events.py)：`LLMStreamEvent` 与 `encode_sse`。
2. [`providers/openai_compat.py`](providers/openai_compat.py)：供应商 chunk 如何翻译成事件。
3. [`conversation/buffer.py`](conversation/buffer.py)：只有稳定消息进入 history。
4. demo [`llm_streaming_lab`](../../demos/llm_streaming_lab/)：SSE 如何暴露给前端。

### Cost / Latency / Cache

1. [`costing/pricing.py`](costing/pricing.py)：学习用价格表，真实项目应改为配置。
2. [`costing/estimate.py`](costing/estimate.py)：从 `TokenUsage` 估算输入、输出和总成本。
3. [`cache/keys.py`](cache/keys.py)：cache key 如何包含模型、Prompt、schema、messages 和 context 指纹。
4. [`cache/records.py`](cache/records.py)：cache hit / miss 与节省 token、成本、延迟。
5. demo [`llm_regression_lab/cost_latency_cache.py`](../../demos/llm_regression_lab/cost_latency_cache.py)：观察冷启动、重复命中和上下文变化 miss。

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

Embedding：

```python
from llm_core import LLMClient

response = LLMClient.from_default_config().embed(
    ["申请售后", "发起逆向服务"],
    "embedding.default_embed",
)
print(response.model, response.dimensions, response.usage)
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

按 [标准学习路径](../../../course/learning-path.md) 进入，不要按目录字母序通关：

- 模型调用与输入输出契约：[../../demos/llm_invoke_lab/](../../demos/llm_invoke_lab/)（含 `first_chat.py` SDK 对照）
- Embedding 表示与真实调用：[../../demos/rag_retrieval_lab/](../../demos/rag_retrieval_lab/)
- Reliability 与可见降级：[../../demos/llm_reliability_lab/](../../demos/llm_reliability_lab/)
- Context Engineering（已接 RAG）：[../../demos/rag_retrieval_lab/](../../demos/rag_retrieval_lab/)；静态策略对照见 [../../demos/llm_context_lab/](../../demos/llm_context_lab/)
- Calling Harness、成本、延迟与缓存：[../../demos/llm_regression_lab/](../../demos/llm_regression_lab/)
- Streaming SSE：[../../demos/llm_streaming_lab/](../../demos/llm_streaming_lab/)

## 常见定位

| 现象 | 先看哪里 |
| --- | --- |
| Key 未配置、401 | 根目录 `.env` 与 `models.yaml` 的 `api_key_env`；Embedding 不自动复用 chat key |
| 换模型不生效 | `config_ref` 是否指向预期配置；`.env` 占位符是否正确 |
| Prompt 版本找不到 | YAML 内 `prompt_id` / `version`，不是文件名 |
| `json_schema` API 失败 | 供应商是否支持该 `response_format` |
| `error_stage=json` | assistant 原文是否为合法 JSON、是否有围栏或截断 |
| 模型没有引用证据 | `context.included_source_ids` 是否为空；`evidence_block` 是否含 source id |
| 关键证据没进 Prompt | `dropped_source_ids` 与 `token_budget` |
| 模型调用偶发失败 | `ReliableCallReport.attempts` 里每次 attempt 的错误码 |
| 不知道是否发生降级 | `ReliableCallReport.degraded` 与 `final_config_ref` |
| 不知道一批 case 是否退化 | `HarnessSummary` 的成功率、解析成功率、错误分布 |
| 成本估算为空 | `LLMResponse.usage` 是否为空，或当前模型是否没有学习用价格配置 |
| 缓存没有命中 | `CacheKeyParts` 中 model / prompt_version / schema_version / context_fingerprint 是否变化 |

## 对应课程正文

- [模型 API 与 Provider 抽象](../../../course/mechanisms/model-api-and-provider.md)
- [Embedding 表示与向量相似度](../../../course/mechanisms/embedding-and-similarity.md)
- [面向应用的 Prompt Engineering](../../../course/mechanisms/prompt-engineering.md)
- [Structured Outputs](../../../course/mechanisms/structured-output.md)
- [Streaming 与 Conversation 组合机制参考](../../../course/mechanisms/streaming-and-conversation.md)
- [检索名单怎样变成模型本轮 Context](../../../course/mechanisms/context-engineering.md)
- [Reliability、Errors 与 Degradation](../../../course/mechanisms/reliability-and-errors.md)
- [LLM Calling Harness](../../../course/mechanisms/calling-harness-and-regression.md)
- [Cost、Latency 与 Caching](../../../course/mechanisms/cost-latency-and-caching.md)
