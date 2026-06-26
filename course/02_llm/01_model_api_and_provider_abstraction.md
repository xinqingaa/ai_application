# 01. Model API 与 Provider 抽象

> 建立统一 `LLMClient` 与多模型配置，让需求评审助手不被单一供应商绑定，并为 Chat / Embedding / Rerank 划分清晰角色。

---

## 真实问题

需求评审助手在不同阶段会使用不同模型：

- 日常开发：便宜、响应快。
- V1 结构化评审：structured output 稳定。
- V3+ 单 Agent：tool calling 可靠。
- 批量 eval：低成本跑 golden set。
- 生产兜底：主模型限流或超时时的备用。

如果只写死一个 `model="gpt-4o"`：

- 换平台要改遍业务代码。
- 「OpenAI 兼容」接口不代表支持 JSON Schema、tool call、stream 格式一致。
- Embedding 与 Chat 混用配置会导致向量空间错乱（RAG 灾难性失效）。

---

## 基础原理

### 一次调用的对象关系

```text
Provider（供应商适配）
  └── ModelConfig（model / base_url / api_key / default_params / capabilities）
        └── LLMClient.chat(messages, config_ref=...)
              └── LLMResponse（content / usage / latency / provider / model / raw）
```

### 三类模型角色（配置必须分离）

| 角色 | 用途 | 在本课程 | 实现阶段 |
| --- | --- | --- | --- |
| **Chat Model** | 生成、摘要、风险、结构化输出 | 01 本篇 | `02_llm` |
| **Embedding Model** | 文档 chunk 向量化 | 01 只讲配置 | `03_rag/07` |
| **Rerank Model** | 检索结果重排 | 01 只讲配置 | `03_rag/08` |

原则：**Embedding 模型与知识库绑定**；切换 embedding 必须重建向量，不能与 Chat 模型共用同一条 `ModelConfig`。

### 能力标签（Capability Tags）

每个 Chat 模型配置应显式记录（并在实测后修正）：

| 标签 | 含义 |
| --- | --- |
| `context_length` | 最大上下文 token |
| `streaming` | 是否支持流式 |
| `tool_calling` | 是否可靠支持 function calling |
| `structured_output` | 是否支持 JSON Schema / Structured Outputs |
| `cost_tier` | `low` / `medium` / `high`（相对分级即可） |

标签是**配置声明**，需与 harness 实测对照；不一致时更新配置而非假设「兼容即相同」。

### 消息与 Token（最小必要概念）

- Chat 请求体核心是 `messages: [{role, content}, ...]`，角色通常为 `system` / `user` / `assistant`。
- **多轮对话**由应用侧维护 history，不是模型自动记住会话。
- `usage.prompt_tokens` + `usage.completion_tokens` 决定成本；上下文越长，prompt_tokens 越高。

---

## 最小实现

### 统一返回结构

```python
from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class TokenUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

@dataclass
class LLMResponse:
    content: str
    raw_response: Any
    usage: Optional[TokenUsage]
    latency_ms: float
    provider: str
    model: str
```

所有 Chat 调用经 `LLMClient` 返回 `LLMResponse`，业务层禁止直接解析各 SDK 差异结构。

### 模型配置示例（YAML）

```yaml
# config/models.yaml — 密钥走环境变量，不写进文件
chat:
  dev_chat:
    provider: openai_compat
    model: gpt-4o-mini
    base_url: ${OPENAI_BASE_URL}
    api_key_env: OPENAI_API_KEY
    default_params:
      temperature: 0.2
      max_tokens: 2048
    capabilities:
      context_length: 128000
      streaming: true
      tool_calling: true
      structured_output: true
      cost_tier: low

  structured_chat:
    provider: openai_compat
    model: gpt-4o
    base_url: ${OPENAI_BASE_URL}
    api_key_env: OPENAI_API_KEY
    default_params:
      temperature: 0
    capabilities:
      structured_output: true
      cost_tier: medium

embedding:
  default_embed:
    provider: openai_compat
    model: text-embedding-3-small
    api_key_env: OPENAI_API_KEY
    # 仅用于 rag_core，不经 LLMClient.chat
```

### 切换调用

```python
# 伪代码：同一 messages，换 config_ref
resp_a = client.chat(messages, config_ref="chat.dev_chat")
resp_b = client.chat(messages, config_ref="chat.structured_chat")
# 对比 content / usage / latency_ms
```

### 入口与观察

- 后续 demo：`source/02_llm/demos/provider_switching/`
- 观察：切换 model 后 schema 成功率（03）、latency P50、单次评审预估成本。

---

## 主流框架实现

| 方式 | 说明 |
| --- | --- |
| OpenAI SDK | `llm_core` 默认实现；兼容 `base_url` 对接国内平台 |
| OpenAI 兼容 REST | 无 SDK 时同一抽象可换 HTTP 客户端 |
| LangChain `ChatOpenAI` | 在 `03_rag` 组合链时，应包装同一 `ModelConfig`，避免双份配置 |

LangChain 是组件组合层，**模型配置真源**应在 `llm_core.providers`，不在业务 scattered 硬编码。

---

## 失败分析与能力边界

### 常见失败

| 类型 | 典型原因 | 本篇处理 |
| --- | --- | --- |
| `rate_limit` | 429 | 记录；降级策略见专题 06 |
| `timeout` | 网络 / 模型慢 | 记录 latency；可换 fallback |
| `auth_error` | key / base_url 错误 | 快速失败，明确日志 |
| `capability_mismatch` | 配置声明 structured_output 但 API 不支持 | 更新能力标签或换模型 |
| `stream_format_diff` | 兼容平台 chunk 结构不同 | 专题 04 统一事件层 |

### 边界

- **OpenAI 兼容 ≠ 能力一致**：tool call 字段名、stream delta、schema 约束各平台可能不同。
- Embedding / Rerank **不经过** `LLMClient.chat`；由 `rag_core` 在 `03_rag` 读取同一配置文件的不同 section。
- 完整重试、熔断、兜底切换在专题 06；本篇只定义 `LLMResponse` 与错误类型枚举。

### 错误类型枚举（建议）

```python
class LLMErrorCode(str, Enum):
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    AUTH = "auth"
    CAPABILITY_MISMATCH = "capability_mismatch"
    PROVIDER_ERROR = "provider_error"
    UNKNOWN = "unknown"
```

---

## 评估观测

对同一批 prompt（5–10 条需求评审问题）：

| 指标 | 用途 |
| --- | --- |
| `latency_ms` P50 / P95 | 选型与超时设置 |
| `usage.total_tokens` | 成本基线 |
| 输出长度 / 是否遵守格式 | 能力标签验证 |
| structured 任务 schema 成功率 | `structured_chat` vs `dev_chat` 对比（配合 03） |

记录表字段：`config_ref`, `model`, `prompt_id`, `latency_ms`, `usage`, `success`, `error_code`。

能力标签与实测不符时：**更新 YAML 声明**，并在 harness 中标注 `capability_verified_at`。

---

## 小项目实战

为需求评审助手定义五类 Chat 配置（名称可调整，职责固定）：

| 配置名 | 用途 | 典型要求 |
| --- | --- | --- |
| `dev_chat` | 日常开发、调试 Prompt | 便宜、快 |
| `structured_chat` | V1 结构化评审、报告 | structured_output 稳定 |
| `tool_chat` | V3 单 Agent 工具调用 | tool_calling 可靠 |
| `batch_chat` | harness / eval 批量跑样例 | 低成本 |
| `fallback_chat` | 主模型限流或失败 | 可用性优先 |

Embedding / Rerank 在同一文件独立 section，供 `03_rag` 读取，例如 `embedding.default_embed`、`rerank.default_rerank`（rerank 可选）。

---

## 项目收敛

写入 `llm_core`：

```text
llm_core/
├── providers/
│   ├── base.py          # Provider 协议
│   ├── openai_compat.py # 默认实现
│   └── registry.py      # config_ref → ModelConfig
├── client.py            # LLMClient.chat / chat_stream（stream 04 完善）
├── config.py            # ModelConfig / CapabilityTags Pydantic 模型
└── errors.py            # LLMErrorCode / LLMError 异常
```

### `ModelConfig` 核心字段

| 字段 | 说明 |
| --- | --- |
| `provider` | 适配器名 |
| `model` | 模型 id |
| `base_url` | 可选，兼容平台 |
| `api_key_env` | 环境变量名 |
| `default_params` | temperature、max_tokens 等 |
| `capabilities` | 能力标签对象 |
| `role` | `chat` / `embedding` / `rerank` |

---

## 完成标准

- 能解释：Provider、ModelConfig、LLMClient、LLMResponse 各自职责。
- 能说明：为何 Embedding 配置不能与 Chat 混用、必须与知识库绑定。
- 能设计：一份含至少 3 个 Chat 配置 + 1 个 Embedding 配置的 YAML，并说明如何用 `config_ref` 切换。
- 能列举：OpenAI 兼容平台常见的 3 类能力差异（structured / tool / stream）。
- 能定义：`LLMErrorCode` 枚举及何时记录 `capability_mismatch`。

---

## 相关专题

- 上一篇：[00_llm_problem_space.md](00_llm_problem_space.md)
- 下一篇：[02_prompt_engineering_for_apps.md](02_prompt_engineering_for_apps.md)
- 结构化输出对模型能力的要求：[03_structured_outputs.md](03_structured_outputs.md)
- Embedding 实现：[03_rag/outline.md](../03_rag/outline.md) 专题 07
