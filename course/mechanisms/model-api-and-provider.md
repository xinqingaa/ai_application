# Model API、调用生命周期与 Provider 抽象

> 机制篇：观察一次真实模型调用如何从业务配置进入 Provider、返回统一响应并暴露供应商差异。
>
> 课程位置：[标准学习路径](../learning-path.md)。必要前置是 [模型输入输出契约](../concepts/model-input-output-contracts.md)；本文交付可运行、可切换、可观察的真实模型调用入口。

---

## 为什么业务逻辑不能直接绑定模型 SDK

如果业务层直接依赖某个供应商的请求对象、异常类型和返回形状，切换模型、记录调用身份或统一失败处理都会扩散到各处。应用需要一层稳定边界，把业务意图转换为供应商请求，再把供应商结果还原为统一响应。

## 一次模型调用的完整生命周期

### 一次 Chat 调用是什么

**输入**：`messages`（`system` / `user` / `assistant` 角色文本）+ 模型参数（`temperature`、`max_tokens` 等）+ 选哪条模型配置（`config_ref`）。  
**输出**：`LLMResponse`——至少包含 `content`、`usage`、`latency_ms`、`model`、`config_ref`；`raw_response` 仅供调试。

与 SDK 直调的区别是：直调只证明「能通」；Provider 调用层还要证明「能换、能记录、能统一」。

这里要先建立一个很重要的心智模型：**模型 API 调用不是业务逻辑本身，而是业务逻辑依赖的一层外部能力**。需求评审助手真正关心的是「这份 PRD 有哪些研发风险」「依据是什么」「能不能进入前端卡片和后续评估」，而不是某个页面、某个 Agent、某个 RAG 链路各自知道 OpenAI SDK 的初始化方式。

如果每个业务模块都直接写 `OpenAI(api_key=...)`，短期看很快，长期会把模型供应商、模型名、参数、错误处理和日志格式散落到各处。散落的后果不是「代码丑」这么简单，而是后续任何质量问题都难以归因：是 Prompt 变了、模型变了、温度变了、供应商变了，还是只是某个模块忘记记录 `usage`？

所以本节的 Provider 抽象不是为了把简单事情复杂化，而是为了明确一条边界：**业务层声明任务需要的模型配置，LLM 调用层负责把配置翻译成具体供应商请求，并统一返回可观测结果**。

### 从直调到抽象：机制递进

下面这条链是本章认知主线。每一步解决上一步的遗留问题；**不能跳过**理解最终为什么要 `config_ref`。

**第 1 步 · SDK 直调**

业务直接创建供应商客户端、传入模型名和消息，再从 SDK 对象中取文本。它能跑通，但 model、base_url、默认参数散落在脚本里；换供应商要改代码；返回值是 SDK 对象，上层难以统一记日志。

**第 2 步 · 环境变量（`.env`）**

密钥和 endpoint 不进仓库。`api_key`、`OPENAI_BASE_URL` 等由 `.env` 注入。  
**遗留**：model 名、默认 `temperature` 仍在 Python 字符串里；多环境（开发 / 演示）仍要改代码。

**第 3 步 · `models.yaml`（配置真源）**

把 `model`、`base_url`、`default_params`、`api_key_env` 收到 YAML；支持 `${OPENAI_MODEL:-gpt-4o-mini}` 占位符，由 `ConfigRegistry` 解析环境变量。  
**遗留**：业务若仍写 YAML 里的具体 model 字符串，换配置条目时调用方还要改。

**第 4 步 · `config_ref`（稳定别名）**

业务只写 `config_ref="chat.dev_chat"`，不碰具体 model 名。换模型改 YAML 或 `.env`，业务无感。  
**遗留**：仍需要一层客户端统一返回结构与错误类型。

**第 5 步 · `LLMClient` + `LLMResponse`**

`LLMClient.chat(messages, config_ref)` 完成：查配置 → 选 Provider → 发请求 → 包装 `LLMResponse`；可选 `debug=True` 向全仓共享 `app_log` 发出调用详情事件，只有启用 DEBUG / verbose 时才显示完整内容。
RAG、Agent、结构化输出（结构化输出）都通过同一入口扩展，而不是再 copy 一份 `OpenAI()`。

```text
first_chat 直调 → .env 密钥 → models.yaml → config_ref → LLMClient / LLMResponse
```

这条递进链也可以反过来帮助你排查问题：

- 如果 Key 泄露或不同环境不一致，先看 `.env`。
- 如果模型名、base_url、默认参数不对，先看 `models.yaml`。
- 如果业务传错用途，先看 `config_ref`。
- 如果返回字段缺失或日志没法统计，先看 `LLMResponse` 是否被绕过。
- 如果不同供应商行为不一致，先看 Provider 层是否正确吸收了差异。

学习这一节时，不要把 `config_ref` 理解成一个字符串技巧。它是业务层和模型供应商之间的「用途契约」。业务说“我要开发聊天模型”，配置层决定当前开发聊天模型具体是谁；调用层负责把这件事稳定执行并记录结果。

### 从前端 / 客户端视角理解这层抽象

如果你来自前端或 Flutter，Provider 抽象可以类比为「数据源适配层」。页面组件不应该知道这个数据来自 REST、GraphQL、WebSocket 还是本地缓存；页面只关心拿到稳定的 view model。同样，需求评审助手的业务模块不应该知道当前模型来自 OpenAI、DeepSeek 还是另一个 OpenAI-compatible 平台；业务只关心拿到稳定的 `LLMResponse`。

这种分层对 AI Native 前端尤其重要。前端以后要展示的不只是最终文本，还包括：

- 当前任务用了哪个模型配置。
- 这次调用花了多少 token。
- 哪一步失败，是鉴权、限流、能力不支持，还是模型输出不可用。
- 用户等待时，系统到底是在调模型、检索、解析，还是重试。

如果后端没有统一的调用层，前端很难得到一致的状态字段。于是用户看到的就只剩一个转圈，研发也很难解释“为什么这次评审结果慢、贵、或失败”。

### 一个完整小场景：从开发模型切到演示模型

假设你正在做需求评审助手的风险审查。开发阶段，为了节省成本，你希望默认使用一个便宜模型；作品展示阶段，你希望换成效果更好的模型；结构化输出阶段，你又希望使用更稳定支持 JSON 的模型。

如果业务代码里到处写具体模型名，这三个阶段会变成三轮全局搜索和手工修改。更糟的是，某个模块漏改也不一定立刻报错，只会在评审结果里表现成“为什么这个任务风格和别的任务不一样”。这类问题非常难查，因为它不是语法错误，而是配置漂移。

使用 `config_ref` 后，业务代码不需要知道“现在 dev_chat 背后是谁”。开发阶段改 `.env` 或 `models.yaml`，演示阶段再改配置，业务调用仍然是 `chat.dev_chat`。这就像前端路由名不等于真实页面文件路径：路由名稳定，底层实现可以演进。

这个场景也说明为什么 `config_ref` 不应随意命名。`chat.dev_chat`、`chat.structured_chat`、`chat.fallback_chat` 这些名字表达的是用途，而不是供应商。好的配置名应该让读者一眼知道“这条配置在业务里承担什么角色”。

### 如何读一次 `LLMResponse`

当 demo 打出一行结果时，不要只看 `content`。本节真正训练的是读懂一次调用的几个信号：

- `content`：模型生成的文本，只是结果本身。
- `model`：实际命中的模型，用来确认配置是否生效。
- `config_ref`：业务请求的是哪类用途，用来追踪调用来源。
- `usage`：token 消耗，用来判断 Prompt 变长、上下文膨胀或成本异常。
- `latency_ms`：耗时，用来判断供应商、模型大小或网络状态的影响。

如果你只看 `content`，就会把模型调用当成一次聊天；如果你同时看这些字段，就开始把它当成一个可观测的应用系统。后续 Prompt 对比、结构化输出、RAG 生成和 Agent trajectory 都会依赖这种观察习惯。

### 本节的设计取舍

本节没有把 `LLMClient` 做成一个大而全的服务层。它暂时不负责完整重试、限流、缓存、成本统计、harness 落盘，也不直接处理 streaming、tool calling 或 embedding 请求。这样设计是刻意的。

如果 Provider 调用层 一开始就搭完整 LLM service，学习者会被大量工程设施淹没，反而看不清最核心的三件事：配置如何集中、调用如何统一、响应如何可观测。后续每个能力进入课程时，再把对应职责加厚到同一个 `llm_core`，比一开始预建所有模块更符合项目式学习节奏。

因此本节完成后，你不需要觉得“LLM 调用层已经生产级完整”。更准确的说法是：你已经建立了一个能被后续课程继续加厚的调用底座。

### 什么时候不用做复杂抽象

抽象不是越早越好。若你只是写一个一次性脚本，目标是验证某个模型是否能回答一个问题，SDK 最小调用 的 SDK 直调就够了。把一次性脚本也拆 Provider、Registry、Response，只会增加阅读负担。

但本仓库的主线不是一次性脚本，而是需求评审助手会持续演进：Prompt 工程 做 Prompt，结构化输出 做结构化输出，后续 RAG 要调用 Chat 和 Embedding，Agent 要调用模型和工具，Eval 要记录每次调用。只要同一套模型调用会被多个能力复用，抽象层就开始有价值。

因此本节的判断标准是：**这个抽象是否吸收了真实变化点**。模型供应商会变、模型角色会变、默认参数会变、能力支持会变、日志字段需要统一，这些都是已知变化点，所以 `LLMClient + config_ref + LLMResponse` 是合理的最小抽象。

### 数据流

```text
业务 / demo
    │  messages + config_ref + 可选 temperature / max_tokens
    ▼
LLMClient.chat()
    │  ConfigRegistry.get_config(config_ref)
    ▼
OpenAICompatProvider.chat()
    │  OpenAI SDK → HTTP POST /v1/chat/completions
    ▼
LLMResponse（content, usage, latency_ms, model, config_ref, …）
```

### messages：system / user / assistant

| role | 谁写的 | 用途 |
| --- | --- | --- |
| `system` | 开发者 | 全局约束：「你是需求评审助手，只基于材料…」 |
| `user` | 用户或程序 | PRD 片段、问题 |
| `assistant` | 模型（历史轮） | 多轮对话中上一轮的模型回复 |

多轮时**历史存在应用的 `messages` 列表里**，API 没有 `session_id`。流式与对话机制 会讲对话状态管理；当节只需知道：多轮 = 每次请求把历史 messages 一并传入。

```json
[
  {"role": "system", "content": "你是需求评审助手。"},
  {"role": "user", "content": "【PRD】… 列出风险。"},
  {"role": "assistant", "content": "1. 接口 v2 兼容性…"},
  {"role": "user", "content": "第 1 条依据是哪一段？"}
]
```

### 常用请求参数

| 参数 | 作用 | 观察方式 |
| --- | --- | --- |
| `temperature` | 随机性：越低越稳定 | `provider_switching.py --temperature 0` vs `0.7` |
| `max_tokens` | 限制**生成**的最大 token 数 | 输出变短时检查是否触顶 |
| `model` | 供应商侧模型 id | 由 `models.yaml` 配置，业务用 `config_ref` |

默认值在 [`config/models.yaml`](../../source/packages/llm_core/config/models.yaml) 的 `default_params`；调用时可覆盖。

### Provider、ModelConfig、config_ref

- **Provider**：适配某一类 API（Provider 调用层 实现 `openai_compat`）。
- **ModelConfig**：一条具体配置（model、base_url、默认参数、能力标签 `capabilities`）。
- **config_ref**：点分别名，如 `chat.dev_chat`；由 YAML 的 section + name 自动生成。

三者的关系可以这样理解：

- `Provider` 回答「怎么和某类接口说话」。
- `ModelConfig` 回答「这一次用哪台模型、哪个 endpoint、哪些默认参数」。
- `config_ref` 回答「业务代码如何稳定地指向这类用途」。

这三个概念必须分开。若业务直接写模型名，模型名就同时承担了「用途」「供应商」「成本层级」「能力假设」四件事。后续想把开发模型从 `gpt-4o-mini` 换成 DeepSeek，或者把结构化任务换成更强模型，就会变成全仓库搜索字符串。`config_ref` 的价值在于让业务写「我要日常开发模型」或「我要结构化模型」，而不是写「我要某个供应商某个具体型号」。

### 三类模型角色（配置分离）

| 角色 | 输入 | 输出 | Provider 调用层 是否调用 |
| --- | --- | --- | --- |
| Chat | messages | 文本 | 是（`LLMClient.chat`） |
| Embedding | 文本 | 向量 | 是（`LLMClient.embed`；详见 Embedding 机制篇） |
| Rerank | query + 文档 | 分数 | 否（后续可选） |

对 `embedding.default_embed` 调 `chat`，或对 chat 配置调 `embed`，都会触发 `LLMErrorCode.CAPABILITY_MISMATCH`——这是刻意的角色守卫，避免 Chat 与 Embedding 混用。

这也是抽象层应该承担的责任：它不只帮你发请求，还要尽早阻止明显错误。若把 embedding 配置误传给 chat，最糟糕的做法是等供应商返回一个难懂的 HTTP 错误；更好的做法是在本地看到 `role` 不匹配时就失败，并给出 `config_ref`。这类「早失败」会让后续 RAG 和 Agent 调试简单很多。

### OpenAI-compatible 的边界

OpenAI-compatible 的意思是：很多平台愿意用近似 OpenAI Chat Completions 的请求/响应格式，让你可以复用 SDK 或 HTTP 结构。它解决的是接入成本，不等于能力完全一致。

本节只要求普通 chat 调用可切换。后续 Structured Outputs、Tool Calling、Streaming、Context length、计费字段、错误码细节，都可能因供应商不同而不同。因此 `models.yaml` 中的 `capabilities` 更像一份能力说明，而不是魔法开关。看到某平台普通 chat 正常，不要自动推断它支持 `json_schema`、tool call 或流式事件。

这个边界意识很重要。否则后续遇到 `json_schema` 报错时，你可能会先怀疑 Prompt 或 Pydantic；但真正原因可能只是当前供应商不支持这个 `response_format`。Provider 调用层 先建立这个心智模型，结构化输出 才能正确判断结构化输出失败属于哪一层。

---

## 收敛为唯一模型调用边界

调用层至少要统一接收消息、模型角色、配置引用和必要参数，并统一返回内容、实际模型、用量、耗时和调用身份。Provider 适配器负责 SDK 差异；配置解析负责选择真实模型；业务层不判断供应商细节。配置身份必须随结果保留，否则两次模型输出无法被公平比较。

## 框架封装了什么、没有解决什么

| 方式 | 与本项目 |
| --- | --- |
| **OpenAI SDK** | `OpenAICompatProvider` 内部使用；`base_url` 对接兼容平台 |
| **本项目 LLMClient** | 业务与 demo 通过 `config_ref` 调用；日志与切换集中 |
| **LangChain ChatModel** | 后续 RAG 拼链时可从同一 `models.yaml` 读 model，避免两套配置 |

原则：**配置真源在 `models.yaml` + `.env`**；框架是消费方，不在业务里再写一份 model 名。

---

## 沿调用链定位 Provider 问题

### 排查路径（表现 → 原因 → 怎么验证）

**1. `auth`：一调用就失败，提示环境变量未配置**

- **表现**：`LLMError` code 为 `auth`，消息含 `OPENAI_API_KEY 未配置` 或 401。
- **原因**：`.env` 未复制、Key 名与 `api_key_env` 不一致、`base_url` 与 Key 不匹配。
- **验证**：检查仓库根 `.env`；`provider_switching.py --verbose` 看请求是否发出；换 Key 后是否立即恢复。

**2. `rate_limit`：偶发 429**

- **表现**：`rate_limit`，有时重试又好。
- **原因**：供应商 QPS / 配额；开发环境多人共用一个 Key。
- **验证**：换 `chat.fallback_chat` 对比；记录 `latency_ms` 与发生时段；完整重试策略在可靠调用机制，**当节**会换 config_ref 即可。

**3. `capability_mismatch`：配置条目用错角色**

- **表现**：对 `embedding.default_embed` 调 `chat` 立刻报错。
- **原因**：Chat 与 Embedding API 路径不同，不能混用 `config_ref`。
- **验证**：`models.yaml` 看 `role` 字段；业务是否误把 embed 配置传给 `LLMClient.chat`。

**4. 兼容平台「能 chat 但不能 structured / tool」**

- **表现**：普通 `chat` 正常，结构化输出 的 `json_schema` 报 `API_ERROR`。
- **原因**：OpenAI 兼容 ≠ 全功能兼容；`capabilities.structured_output` 仅为文档性标签，不自动降级。
- **验证**：对比 `chat.dev_chat` 与 `chat.structured_chat`；结构化细节在结构化输出机制。

### 常见误区

| 误区 | 纠正 |
| --- | --- |
| 「有 `base_url` 就等于 OpenAI」 | 参数支持与限额因平台而异 |
| 「`config_ref` 可以随意命名」 | 必须与 YAML section.name 一致，否则 `KeyError` |
| 「多轮对话 API 会记住」 | 历史由应用拼进 `messages` |
| 「`usage` 可省略」 | 成本与上下文问题靠 usage 发现；成本治理 专讲成本 |

### 本节不做（defer）

| 能力 | 目标节 | 当节最小判断 |
| --- | --- | --- |
| 流式输出 | 流式机制 | 知道非流式一次返回 `content` 即可 |
| 完整重试 / 熔断 | 可靠调用 | 会用 `LLMErrorCode` 分类，遇 429 知换 `fallback` |
| Structured Outputs | 结构化输出 | 知 `chat.structured_chat` 预留给结构化任务 |
| 实际调用 embedding | Embedding 机制篇 | 本节建立 role 守卫；`LLMClient.embed` 在后续步骤进入 |
| harness 落盘 | 调用 Harness | demo 对比 + 笔记记录 token/latency |
| 多轮会话持久化 | 流式机制 | 知历史在 `messages`，不由 API 保存 |

---

## 通过真实对照验证边界

配套实验使用相同输入切换两个真实模型配置，观察业务调用方式是否保持不变、配置身份是否随结果返回，以及供应商错误是否被统一暴露。环境准备、运行命令、输出字段和读码路径见[配套实验](../labs/model-api-and-provider.md)。

## 怎样判断调用边界已经可复用

业务调用不因供应商切换而改写；结果带有实际模型与配置身份；鉴权、超时、限流和能力不支持能够被区分；配置变化可以独立对照；真实失败不会静默变成假成功。达到这些条件，调用层才具备进入后续 Prompt、Structured Output 和可靠性机制的基础。

## 交给项目的调用契约

- 新增 `llm_core` 调用层（`LLMClient`、`models.yaml`、`ConfigRegistry`、`LLMResponse`、`LLMError`）与 `llm_invoke_lab` demo。
- 需求评审助手具备：**按任务切换模型配置、统一响应结构与可观测日志**；SDK 最小调用 的 `llm_invoke_lab`（`first_chat.py`） 保留作 SDK 直调对照。
- 后续 Prompt、Structured Output、Reliability 和按需 Streaming 都复用同一个 `LLMClient`，但进入顺序只由标准学习路径规定。

完成实验后回到 [标准学习路径](../learning-path.md)。需要查完整知识关系时再使用 [知识地图](../knowledge-map.md)。
