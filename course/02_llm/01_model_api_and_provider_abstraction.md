# 01. Model API 与 Provider 抽象

> 在理解「LLM 是什么」之后，学会用统一方式调用模型、切换供应商、区分 Chat / Embedding 角色，并读懂一次 API 往返里每个字段的含义。

---

## 真实问题

专题 00 建立了全局视图：需求评审助手需要稳定的 **LLM 层**。本篇回答：**具体怎么「接模型」才不把自己锁死**。同样分三层。

### 学习者真实问题

- **「调 LLM API」到底在调什么？** 是一个函数、一个 URL，还是本地跑一个 `.bin` 文件？
- **`messages` 里 system / user / assistant 是什么？** 多轮对话是谁在记历史？
- **Token 是什么？** 为什么说上下文长了就贵、就慢？
- **OpenAI 兼容是什么意思？** 换国内平台要重写全部代码吗？
- **Embedding 和 Chat 用的不都是「模型」吗？** 为什么不能同一个配置搞定？

读完后你应能：**画一次请求的输入输出**、**用配置文件切换 model**、**说明为什么 Embedding 必须和 Chat 分开**。

### 产品真实问题：同一助手，不同阶段要不同「引擎」

继续小周的售后 PRD 场景。需求评审助手在生命周期里会多次调用模型，**任务不同，对模型的要求也不同**：

| 阶段 | 做什么 | 对模型的要求 |
| --- | --- | --- |
| 日常开发 | 调试 Prompt、试风险描述 | 便宜、快、够用即可 |
| V1 正式评审 | 输出 `ReviewReport` JSON | structured output 稳定、字段齐全 |
| V3 单 Agent | 模型决定是否查知识库 | tool calling 可靠 |
| 夜间 eval | 跑 30 条 golden set | 低成本、可批量 |
| 演示 / 兜底 | 对外 demo 或主模型 429 | 质量优先或可用性优先 |

如果代码里 everywhere 写死：

```python
client.chat.completions.create(model="gpt-4o", ...)
```

会出现：**开发调试烧贵模型**、**结构化任务用弱模型 JSON 总失败**、**换平台要改几十个文件**、**限流时没有备用模型**。  
产品需要的是：**按任务选 `config_ref`（如 `chat.structured_chat`）**，而不是在业务里散落 model 字符串。

### 工程真实问题

| 问题 | 典型触发 | 后果 |
| --- | --- | --- |
| 供应商锁定 | 业务直接依赖 OpenAI SDK 特有字段 | 迁移成本大 |
| 能力假设错误 | 平台标「OpenAI 兼容」但无 JSON Schema | V1 结构化全失败 |
| Embedding 混用 | 用 Chat 的 model 名做向量化 | RAG 检索错乱 |
| 响应结构不统一 | 有的返回 OpenAI 格式，有的多包一层 | 日志、eval 无法汇总 |
| 错误不可分类 | 全 catch Exception | 无法区分重试还是换模型 |

本篇建立 **`LLMClient` + `ModelConfig` + `LLMResponse`**，把上述问题收敛到 `llm_core` 一层处理。

---

## 基础原理

### 「调 API」在做什么：一次 Chat 调用的数据流

```text
你的 Python（llm_core）
    │
    │  ① 组装 messages + model + temperature ...
    ▼
HTTP POST  →  供应商 API（OpenAI 或兼容平台）
    │
    │  ② 模型推理（你看不见的内部计算）
    ▼
HTTP 响应  ←  JSON：choices[].message.content, usage, model, ...
    │
    │  ③ 解析为 LLMResponse
    ▼
业务层（RAG 生成 / Agent / 报告服务）
```

**输入（你控制的）：**

- `messages`：对话数组，见下节  
- `model`：模型 id 字符串  
- 参数：`temperature`、`max_tokens`、`response_format`（结构化时，专题 03）等  

**输出（你要统一消费的）：**

- `content`：模型生成的文本  
- `usage`：token 计数  
- `model`：实际执行的模型 id（有时与请求略有差异）  

应用开发者**不需要**部署模型权重；模型在供应商云端（或你另行部署的兼容服务）运行。你要做的是：**可靠地发请求、解析响应、记录元数据**。

### messages：system / user / assistant

Chat API 使用 **messages 数组** 表示对话上下文：

| role | 谁写的 | 典型用途 |
| --- | --- | --- |
| `system` | 开发者 | 全局人设与约束：「你是需求评审助手，只基于材料…」 |
| `user` | 最终用户或你的程序 | PRD 片段、问题：「请列出风险」 |
| `assistant` | 模型（历史轮次） | 多轮对话里**上一轮模型的回答** |

**多轮对话示例（第二轮）：**

```json
[
  {"role": "system", "content": "你是需求评审助手。"},
  {"role": "user", "content": "【PRD】... 列出风险。"},
  {"role": "assistant", "content": "1. 接口 v2 兼容性未说明..."},
  {"role": "user", "content": "第 1 条风险的依据是哪一段？"}
]
```

要点：**模型不会自动记住上次聊天**。会话历史由**你的服务**存入数据库或内存，下次请求时拼进 `messages`。需求评审助手后期用 `ChatRecord`（`07_projects`）持久化。

### Token 与成本（够用即可）

- 文本会先被 **tokenizer** 切成 token（不是严格的一字一词）。  
- **`usage.prompt_tokens`**：输入侧 token 数（system + user + 历史 + 长 PRD 都算）。  
- **`usage.completion_tokens`**：模型生成部分的 token 数。  
- 计费通常：`prompt 单价 × prompt_tokens + completion 单价 × completion_tokens`。

**和产品的关系：** 一次评审若调用 5 次模型、每次塞入 8000 token 的 PRD，成本会远高于「RAG 只塞 2000 token 相关片段」。这就是为什么后面要有 context 预算（专题 05）和 RAG（`03_rag`）。

**上下文窗口（context length）：** 模型一次能「看」的 token 上限。超过时，API 可能拒绝，或截断早期内容——**截断会导致模型「没看到」PRD 中间章节**。

### 三类「模型角色」—— 配置必须分离

都叫「模型」，在 AI 应用里职责不同：

| 角色 | 输入 | 输出 | 在需求评审助手中 |
| --- | --- | --- | --- |
| **Chat** | messages | 文本 / JSON | 摘要、风险、报告 |
| **Embedding** | 一段文本 | 向量（浮点数组） | 文档 chunk 向量化，供检索 |
| **Rerank** |  query + 候选文档 | 相关性分数 | 检索结果重排（可选） |

**为什么不能混用一条配置？**

- Embedding 模型和 Chat 模型的 **API 路径、参数、输出结构完全不同**。  
- 每个知识库绑定一种 embedding；**更换 embedding 模型必须重建全部向量**，否则语义空间不一致，检索失效。  
- Chat 的 `gpt-4o` 名字填进 embedding 接口会直接报错或产生无意义向量。

因此：`models.yaml` 分 `chat:`、`embedding:`、`rerank:` 三节；**Chat 走 `LLMClient.chat`**，Embedding 由 `03_rag` 的 `rag_core` 读取配置调用。

### Provider 抽象：为什么要多一层

```text
业务代码
    └── LLMClient.chat(messages, config_ref="chat.structured_chat")
            └── registry 加载 ModelConfig
                    └── OpenAICompatProvider.chat(...)
                            └── OpenAI SDK / HTTP
```

**Provider** = 适配某一类供应商 API 的模块。  
**ModelConfig** = 某一条具体模型配置（model 名、base_url、默认参数、能力标签）。  
**config_ref** = 配置别名，如 `chat.dev_chat`，业务只引用别名。

好处：

- 换平台：新增或切换 Provider，**不改**风险审查业务代码。  
- 换模型：改 YAML，**不改** Python（除非能力标签变化需改 Prompt）。  
- 统一日志：所有调用都经过 `LLMClient`，便于记录 `latency_ms`、`usage`。

### 能力标签（Capability Tags）

配置里声明「这个 model **应该** 能做什么」；上线后用 harness **验证**：

| 标签 | 含义 | 验错方式 |
| --- | --- | --- |
| `context_length` | 最大上下文 | 文档 / 实测超长输入 |
| `streaming` | 支持流式 | 专题 04 试 `stream=True` |
| `tool_calling` | 可靠 function call | 专题 09 / Agent 实测 |
| `structured_output` | JSON Schema 约束 | 专题 03 跑 ReviewReport |
| `cost_tier` | low / medium / high | 相对分级，便于选型 |

若 YAML 写 `structured_output: true`，实测却频繁 JSON 失败 → 更新标签或换 `structured_chat` 模型，**不要**假设「兼容 OpenAI 就一定行」。

### 与 LangChain 的关系（认知）

LangChain 的 `ChatOpenAI(model="...")` 本质也是包一层 Chat API。本项目约定：

- **配置真源**：`llm_core` 的 `models.yaml` + registry。  
- **LangChain**：在 `03_rag` 拼链时，从同一配置构造 ChatModel，避免项目里两个 model 名来源。

---

## 最小实现

### 统一响应：`LLMResponse` `[CODE-GATE: M1]`

> 设计草图；M1 实现见 `source/packages/llm_core/`。

业务层**只**消费以下结构，不直接摸 SDK 原始对象：

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
    content: str              # 模型生成的文本
    raw_response: Any         # 原始 SDK 响应，仅供调试
    usage: Optional[TokenUsage]
    latency_ms: float
    provider: str             # 如 openai_compat
    model: str                # 实际 model id
    config_ref: str           # 如 chat.dev_chat
```

**走读示例：** 小周 PRD 风险任务调用 `config_ref="chat.dev_chat"` 后，你可能得到：

```text
content: "1. 售后接口 v2 兼容性...\n2. 按钮点击后页面状态..."
usage: prompt_tokens=420, completion_tokens=180
latency_ms: 1340
model: gpt-4o-mini
```

业务层把 `content` 交给 Prompt 后处理或 Schema 解析（03）；**同时**把 `usage`、`latency_ms` 写入日志供 eval。

### 模型配置：`models.yaml` `[CODE-GATE: M1]`

密钥**只**放环境变量，不进 Git：

```yaml
# config/models.yaml（设计草图）

chat:
  dev_chat:
    role: chat
    provider: openai_compat
    model: gpt-4o-mini
    base_url: ${OPENAI_BASE_URL}      # 可选，默认 OpenAI 官方
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
    role: chat
    provider: openai_compat
    model: gpt-4o
    api_key_env: OPENAI_API_KEY
    default_params:
      temperature: 0
      max_tokens: 4096
    capabilities:
      structured_output: true
      cost_tier: medium

  fallback_chat:
    role: chat
    provider: openai_compat
    model: gpt-4o-mini
    api_key_env: OPENAI_API_KEY
    default_params:
      temperature: 0
    capabilities:
      cost_tier: low

embedding:
  default_embed:
    role: embedding
    provider: openai_compat
    model: text-embedding-3-small
    api_key_env: OPENAI_API_KEY
    # 由 rag_core 调用，不经 LLMClient.chat
```

### 调用方式对比实验

**同一 messages**，只换 `config_ref`：

```python
# 设计草图 [CODE-GATE: M1]

messages = [
    {"role": "system", "content": "你是需求评审助手。"},
    {"role": "user", "content": "【PRD 片段】售后按钮... 列出 2 条风险。"},
]

r1 = client.chat(messages, config_ref="chat.dev_chat")
r2 = client.chat(messages, config_ref="chat.structured_chat")

# 对比：latency_ms, usage.total_tokens, content 长度与稳定性
```

**观察笔记建议：**

- 强模型是否更贴材料、更少编造？  
- 延迟与 token 是否明显增加？  
- 若 user 里加「必须输出 JSON」，`dev_chat` 是否仍夹 Markdown？—— 为专题 03 选型提供依据。

### 完整请求-响应走读（概念）

**请求（简化）：**

```http
POST /v1/chat/completions
Authorization: Bearer sk-...
Content-Type: application/json

{
  "model": "gpt-4o-mini",
  "messages": [...],
  "temperature": 0.2
}
```

**响应（简化）：**

```json
{
  "id": "chatcmpl-...",
  "model": "gpt-4o-mini-2024-07-18",
  "choices": [{
    "message": { "role": "assistant", "content": "..." },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 420,
    "completion_tokens": 180,
    "total_tokens": 600
  }
}
```

`LLMClient` 的职责：发上述请求、计时、捕获异常、映射为 `LLMResponse` 或 `LLMError`。

### 入口与 demo

- M1 目标 demo：`source/demos/02_provider_switching/`  
- 运行方式（M1 完成后在 demo README 中维护）：切换 config_ref、打印对比表。

---

## 主流框架实现

| 方式 | 适用 | 本项目 |
| --- | --- | --- |
| OpenAI 官方 SDK | 官方或兼容 base_url | `OpenAICompatProvider` 默认实现 |
| 原生 HTTP + requests/httpx | 无 SDK 的平台 | 同一 Provider 接口下换实现 |
| LangChain `ChatOpenAI` | RAG LCEL 链 | 从 `ModelConfig` 构造，配置不重复 |
| 本地 Ollama 等 | 离线开发 | 可选 Provider；能力标签需实测 |

---

## 失败分析与能力边界

### 常见错误与应对（本篇只分类，降级详 06）

| LLMErrorCode | 典型原因 | 应用层第一反应 |
| --- | --- | --- |
| `auth` | key 错、base_url 错 |  fail fast，打明确日志 |
| `rate_limit` | 429 | 记录；换 fallback 或退避重试 |
| `timeout` | 网络 / 模型慢 | 记录 latency；可换 fallback |
| `capability_mismatch` | 要 Schema 但模型不支持 | 换 structured_chat 或改标签 |
| `provider_error` | 5xx、未知 body | 记录 raw；有限重试 |
| `unknown` | 未分类 | 记录现场，避免吞异常 |

```python
# 设计草图
class LLMErrorCode(str, Enum):
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    AUTH = "auth"
    CAPABILITY_MISMATCH = "capability_mismatch"
    PROVIDER_ERROR = "provider_error"
    UNKNOWN = "unknown"
```

### 常见误区

- **误区 1：**「OpenAI 兼容 = 所有 OpenAI 参数都能用」—— structured output、tool call 常不完整。  
- **误区 2：**「Embedding 随便选个便宜的就行，和 Chat 无关」—— embedding 与知识库生命周期绑定，换就要重建索引。  
- **误区 3：**「多轮对话靠 session_id 传给 API」—— 标准 Chat API 无 session；历史在 messages 里。  
- **误区 4：**「LLMClient 里顺便做 RAG」—— 检索属于 `rag_core`；Client 只负责生成调用。

### 边界

- 完整重试、熔断、降级策略 → 专题 06  
- Structured Outputs API 细节 → 专题 03  
- Embedding 写入 pgvector → `03_rag/07`  
- **本篇不实现** Tool Calling 执行，只保证 Chat 通道统一  

---

## 评估观测

### 跨模型对比表（与 00 样例集结合）

对样例 S2（售后 PRD 风险）等，固定 messages，切换 `config_ref`：

| config_ref | model | latency_ms | total_tokens | 人工 notes（1–5 可用性） |
| --- | --- | --- | --- | --- |
| chat.dev_chat | gpt-4o-mini | | | |
| chat.structured_chat | gpt-4o | | | |

### 能力标签验证记录

当实测与 YAML 不符时，更新配置并记录：

```text
structured_chat: structured_output 实测失败率 40% @ 2025-xx-xx → 换模型 / 改标签
```

字段：`config_ref`, `capability`, `expected`, `observed`, `verified_at`。

### 与 harness 的衔接

每次 `LLMClient.chat` 建议记录：`config_ref`, `model`, `usage`, `latency_ms`, `error_code`, `prompt_id`（02 起）。专题 07 将这些汇总为回归报告。

---

## 小项目实战

为需求评审助手定义 **五类 Chat 配置**（名称可调整，职责固定）：

| config_ref | 用途 | 典型场景 |
| --- | --- | --- |
| `chat.dev_chat` | 日常开发、Prompt 试验 | 本地调 risk_review 模板 |
| `chat.structured_chat` | V1 结构化报告 | 输出 ReviewReport |
| `chat.tool_chat` | V3 Agent | function calling |
| `chat.batch_chat` | 夜间 eval | 跑 golden set |
| `chat.fallback_chat` | 限流 / 超时 | 主模型失败时切换 |

**Embedding 配置（供 RAG 预置）：**

```yaml
embedding:
  default_embed:
    role: embedding
    model: text-embedding-3-small
    # 与知识库绑定；切换需 re-index
```

**练习：** 写出你的 `models.yaml` 草案（至少 3 个 chat + 1 个 embedding），并标注每个 config_ref 对应 V0–V3 哪条路径。

---

## 项目收敛

### 写入 `llm_core`（M1 范围）

```text
llm_core/
├── config.py            # ModelConfig, CapabilityTags, TokenUsage
├── errors.py            # LLMErrorCode, LLMError
├── providers/
│   ├── base.py          # Provider 协议
│   ├── openai_compat.py
│   └── registry.py      # 加载 YAML，config_ref → ModelConfig
└── client.py            # LLMClient.chat(..., config_ref)
```

### ModelConfig 字段说明

| 字段 | 说明 |
| --- | --- |
| `role` | `chat` / `embedding` / `rerank` |
| `provider` | 适配器名 |
| `model` | 供应商模型 id |
| `base_url` | 可选 |
| `api_key_env` | 环境变量名 |
| `default_params` | temperature、max_tokens 等 |
| `capabilities` | 能力标签对象 |

### 与项目版本 / 里程碑

| 里程碑 | 本篇交付 |
| --- | --- |
| **M1** | `LLMClient` + `models.yaml` + `provider_switching` demo 可跑 |
| **V0–V1** | 业务通过 config_ref 调模型，不硬编码 model 字符串 |
| **03_rag** | 读取同一 YAML 的 `embedding.default_embed` |

---

## 完成标准

- **能解释**：一次 Chat API 调用的输入（messages、model、参数）与输出（content、usage）。  
- **能解释**：system / user / assistant 在多轮对话中如何拼接。  
- **能说明**：Token、context window 与成本、截断风险的关系。  
- **能说明**：Chat / Embedding / Rerank 为何必须分配置；换 embedding 为何要 re-index。  
- **能设计**：含 ≥3 个 chat + 1 个 embedding 的 `models.yaml`，并用 `config_ref` 描述切换方式。  
- **能列举**：OpenAI 兼容平台常见的 3 类能力差异（structured / tool / stream）。  
- **能定义**：`LLMErrorCode` 各类何时使用。  

### 自检题（不看正文能否答）

1. 多轮对话的历史存在哪里？API 的哪个字段携带？  
2. 为什么业务代码不应写 `model="gpt-4o"` 而应写 `config_ref="chat.structured_chat"`？  
3. 把 Chat 模型名用于 embedding 接口会导致什么问题？  

---

## 相关专题

- 上一篇：[00_llm_problem_space.md](00_llm_problem_space.md)  
- 下一篇：[02_prompt_engineering_for_apps.md](02_prompt_engineering_for_apps.md)  
- Structured Output 对模型能力的要求：[03_structured_outputs.md](03_structured_outputs.md)  
- Embedding 实现与 pgvector：[03_rag/outline.md](../03_rag/outline.md) 专题 07  
- 代码里程碑 M1：[outline.md](outline.md)  
