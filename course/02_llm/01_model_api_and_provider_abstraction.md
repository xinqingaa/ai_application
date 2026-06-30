# 01. Model API 与 Provider 抽象

> 在 00 跑通「一次最小 chat」之后，学会用 **统一客户端 + 配置文件** 接模型、切换供应商、读懂请求/响应，并为后续 RAG / Agent 复用同一套调用方式。

---

## 真实问题

专题 00 建立了问题空间：需求评审助手需要稳定的 LLM 层。本篇回答：**具体怎么接模型，业务代码才不写死** `model="gpt-4o"`，以及一次 Chat 调用在工程上到底经过哪些环节。

### 学习者真实问题

- **调 API 到底在调什么？** 是你的 Python 程序向云端发一次 HTTP 请求，云端模型根据 `messages` 生成文本；不是在本机跑模型文件。
- **Token 是什么？** 文本切成词元后的计数单位；`usage.prompt_tokens` / `completion_tokens` 决定成本，也反映上下文有多长。
- **OpenAI 兼容是什么意思？** 很多平台（含 DeepSeek）提供与 OpenAI Chat API **相同 JSON 格式**的接口；换 `base_url` + Key 即可，不必重写业务逻辑。
- **Embedding 和 Chat 不都是「模型」吗？** API 路径、输入输出完全不同；Chat 生成文本，Embedding 生成向量；配置必须分开（RAG 课再用 embedding）。

### 产品真实问题

继续小周团队的售后 PRD 场景。00 用 `first_chat.py` 直连 OpenAI SDK 已经能打出风险预览，团队很高兴。两周后要做三件事：

1. **开发用便宜模型、演示用强模型**——若 `model="gpt-4o"` 写死在业务里，每个脚本都要改。
2. **接入 DeepSeek 降本**——若 Key、`base_url` 散落在五个文件里，换一次供应商要全库搜索。
3. **前端要展示每次调用的 model、耗时、token**——若有的模块返回 SDK 原始对象、有的只返回字符串，日志和 eval 无法汇总。

某次上线前，后端在风险审查、摘要、追问三个模块里各写了一份 `OpenAI(api_key=...)`，模型名还不一致。运维把 `.env` 里的 `OPENAI_MODEL` 改成 `deepseek-chat` 后，只有两个模块生效，第三个仍打旧 endpoint，评审会上出现「同一 PRD、两份结论、模型还不同」的尴尬。

产品需要的是：**业务只声明「用哪类任务配置」**（如 `chat.dev_chat`），模型名、供应商、默认参数集中在仓库里的配置真源；每次调用返回统一结构，便于对比和记账。

### 工程真实问题

| 问题 | 典型表现 | 本节方向 |
| --- | --- | --- |
| 直接依赖 SDK 原始对象 | 日志字段不一致，eval 难汇总 | 统一 `LLMResponse` |
| 写死 model 字符串 | 换阶段 / 换供应商改多处 | `config_ref` + `models.yaml` |
| 假设「兼容 OpenAI = 所有参数都能用」 | structured / tool call 在部分平台失败 | `capabilities` 认知；03 起实测 |
| 错误全部 `except Exception` | 429 与 Key 错误混在一起 | `LLMError` + `LLMErrorCode` 分类 |

本篇在 `llm_core` 建立 **`LLMClient` + `models.yaml` + `LLMResponse`**，把调用与可观测收敛到一层。00 的 `02_first_chat` 保留作 SDK 直调对照，本篇是项目内的标准入口。

---

## 基础原理

### 一次 Chat 调用是什么

**输入**：`messages`（`system` / `user` / `assistant` 角色文本）+ 模型参数（`temperature`、`max_tokens` 等）+ 选哪条模型配置（`config_ref`）。  
**输出**：`LLMResponse`——至少包含 `content`、`usage`、`latency_ms`、`model`、`config_ref`；`raw_response` 仅供调试。

与 00 SDK 直调的区别：00 证明「能通」；01 证明「能换、能记、能统一」。

这里要先建立一个很重要的心智模型：**模型 API 调用不是业务逻辑本身，而是业务逻辑依赖的一层外部能力**。需求评审助手真正关心的是「这份 PRD 有哪些研发风险」「依据是什么」「能不能进入前端卡片和后续评估」，而不是某个页面、某个 Agent、某个 RAG 链路各自知道 OpenAI SDK 的初始化方式。

如果每个业务模块都直接写 `OpenAI(api_key=...)`，短期看很快，长期会把模型供应商、模型名、参数、错误处理和日志格式散落到各处。散落的后果不是「代码丑」这么简单，而是后续任何质量问题都难以归因：是 Prompt 变了、模型变了、温度变了、供应商变了，还是只是某个模块忘记记录 `usage`？

所以本节的 Provider 抽象不是为了把简单事情复杂化，而是为了明确一条边界：**业务层声明任务需要的模型配置，LLM 调用层负责把配置翻译成具体供应商请求，并统一返回可观测结果**。

### 从直调到抽象：机制递进

下面这条链是本章认知主线。每一步解决上一步的遗留问题；**不能跳过**理解最终为什么要 `config_ref`。

**第 1 步 · SDK 直调（00 `first_chat`）**

```python
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
resp = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
text = resp.choices[0].message.content
```

能跑通，但 model、base_url、默认参数散落在脚本里；换供应商要改代码；返回值是 SDK 对象，上层难以统一记日志。

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

`LLMClient.chat(messages, config_ref)` 完成：查配置 → 选 Provider → 发请求 → 包装 `LLMResponse`；可选 `debug=True` 打印完整日志。  
RAG、Agent、结构化输出（03）都通过同一入口扩展，而不是再 copy 一份 `OpenAI()`。

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

如果 01 一开始就搭完整 LLM service，学习者会被大量工程设施淹没，反而看不清最核心的三件事：配置如何集中、调用如何统一、响应如何可观测。后续每个能力进入课程时，再把对应职责加厚到同一个 `llm_core`，比一开始预建所有模块更符合项目式学习节奏。

因此本节完成后，你不需要觉得“LLM 调用层已经生产级完整”。更准确的说法是：你已经建立了一个能被后续课程继续加厚的调用底座。

### 什么时候不用做复杂抽象

抽象不是越早越好。若你只是写一个一次性脚本，目标是验证某个模型是否能回答一个问题，00 的 SDK 直调就够了。把一次性脚本也拆 Provider、Registry、Response，只会增加阅读负担。

但本仓库的主线不是一次性脚本，而是需求评审助手会持续演进：02 做 Prompt，03 做结构化输出，后续 RAG 要调用 Chat 和 Embedding，Agent 要调用模型和工具，Eval 要记录每次调用。只要同一套模型调用会被多个能力复用，抽象层就开始有价值。

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

多轮时**历史存在应用的 `messages` 列表里**，API 没有 `session_id`。专题 04 会讲对话状态管理；当节只需知道：多轮 = 每次请求把历史 messages 一并传入。

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

- **Provider**：适配某一类 API（01 实现 `openai_compat`）。
- **ModelConfig**：一条具体配置（model、base_url、默认参数、能力标签 `capabilities`）。
- **config_ref**：点分别名，如 `chat.dev_chat`；由 YAML 的 section + name 自动生成。

三者的关系可以这样理解：

- `Provider` 回答「怎么和某类接口说话」。
- `ModelConfig` 回答「这一次用哪台模型、哪个 endpoint、哪些默认参数」。
- `config_ref` 回答「业务代码如何稳定地指向这类用途」。

这三个概念必须分开。若业务直接写模型名，模型名就同时承担了「用途」「供应商」「成本层级」「能力假设」四件事。后续想把开发模型从 `gpt-4o-mini` 换成 DeepSeek，或者把结构化任务换成更强模型，就会变成全仓库搜索字符串。`config_ref` 的价值在于让业务写「我要日常开发模型」或「我要结构化模型」，而不是写「我要某个供应商某个具体型号」。

### 三类模型角色（配置分离）

| 角色 | 输入 | 输出 | 01 是否调用 |
| --- | --- | --- | --- |
| Chat | messages | 文本 | 是（`LLMClient.chat`） |
| Embedding | 文本 | 向量 | 否（YAML 预置，`03_rag` 用） |
| Rerank | query + 文档 | 分数 | 否（后续可选） |

对 `embedding.default_embed` 调 `chat` 会触发 `LLMErrorCode.CAPABILITY_MISMATCH`——这是刻意的角色守卫，避免 Chat 与 Embedding 混用。

这也是抽象层应该承担的责任：它不只帮你发请求，还要尽早阻止明显错误。若把 embedding 配置误传给 chat，最糟糕的做法是等供应商返回一个难懂的 HTTP 错误；更好的做法是在本地看到 `role` 不匹配时就失败，并给出 `config_ref`。这类「早失败」会让后续 RAG 和 Agent 调试简单很多。

### OpenAI-compatible 的边界

OpenAI-compatible 的意思是：很多平台愿意用近似 OpenAI Chat Completions 的请求/响应格式，让你可以复用 SDK 或 HTTP 结构。它解决的是接入成本，不等于能力完全一致。

本节只要求普通 chat 调用可切换。后续 Structured Outputs、Tool Calling、Streaming、Context length、计费字段、错误码细节，都可能因供应商不同而不同。因此 `models.yaml` 中的 `capabilities` 更像一份能力说明，而不是魔法开关。看到某平台普通 chat 正常，不要自动推断它支持 `json_schema`、tool call 或流式事件。

这个边界意识很重要。否则后续遇到 `json_schema` 报错时，你可能会先怀疑 Prompt 或 Pydantic；但真正原因可能只是当前供应商不支持这个 `response_format`。01 先建立这个心智模型，03 才能正确判断结构化输出失败属于哪一层。

---

## 最小实现

本节最小实现要验证的不是「能否把 SDK 包一层」，而是这条链路是否成立：

```text
业务只传 messages + config_ref
→ 调用层查到 ModelConfig
→ Provider 发起真实请求
→ 统一返回 LLMResponse
```

这条链路成立后，上层的 Prompt、Structured Outputs、RAG generation、Agent tool reasoning 都可以复用同一入口。后续课程不需要重新学习「怎么初始化供应商 SDK」，而是专注在各自能力的输入、输出和失败边界上。

### 1. `LLMClient.chat`：业务层唯一入口

[`client.py`](../../source/packages/llm_core/client.py)：

```python
config = self._registry.get_config(config_ref)
if config.role != "chat":
    raise LLMError(
        code=LLMErrorCode.CAPABILITY_MISMATCH,
        message=f"{config_ref} 的 role 是 {config.role}，不能用于 chat",
        config_ref=config_ref,
    )
provider = self._registry.get_provider(config.provider)
response = provider.chat(messages, config, **params)
return response
```

这个片段里有三个关键点。

第一，`config_ref` 先被解析成 `ModelConfig`，业务不直接接触模型名和 endpoint。第二，`config.role != "chat"` 时立刻失败，说明调用层不是透明转发器，而是会保护模型角色边界。第三，真正发请求的对象是 `provider`，所以未来如果有非 OpenAI-compatible 供应商，只需要新增 Provider，而不是让业务模块到处判断供应商差异。

### 2. `LLMResponse`：统一业务可读的输出

Provider 发回来的 SDK 原始对象不应该直接扩散到业务层。业务层需要的是稳定字段：文本、token、耗时、模型、配置引用。[`config.py`](../../source/packages/llm_core/config.py) 中的 `LLMResponse` 就是这层统一形状：

```python
@dataclass(frozen=True)
class LLMResponse:
    content: str
    raw_response: Any
    usage: Optional[TokenUsage]
    latency_ms: float
    provider: str
    model: str
    config_ref: str
```

这不是为了「好看」，而是为了让后续所有质量工程有同一份记录口径。比如：

- 改 Prompt 后，要比较 `prompt_tokens` 和 `completion_tokens`。
- 切供应商后，要比较 `latency_ms` 和输出稳定性。
- 做 harness 时，要把 `config_ref`、`model`、`usage` 和结果一起落盘。
- 前端展示运行状态时，要能说明这次调用用了哪个配置、耗时多久。

因此 `LLMResponse` 是后续观测和评估的基础接口。没有它，RAG 和 Agent 的每次模型调用都会变成难以对齐的散点日志。

### 3. YAML 配置只保留为真源，不进入业务判断

`models.yaml` 里保存模型名、默认参数、供应商和能力标签。正文不需要逐字段背诵配置格式，但需要理解它解决的工程问题：**配置变化不应要求修改业务代码**。

在需求评审助手里，`chat.dev_chat` 可以先指向便宜模型；`chat.structured_chat` 可以指向更适合结构化输出的模型；`chat.fallback_chat` 可以在限流时临时切换。业务层只看 `config_ref`，而不是关心每个 ref 背后的具体型号。这样后续换模型时，学习者能把注意力放在“效果有没有变好、成本有没有下降、错误类型有没有变化”，而不是到处改字符串。

### 判断这层设计是否过度

一个抽象是否合理，要看它有没有承担真实变化点。Provider 抽象在本项目里是必要的，因为后续会发生这些变化：

- 开发、演示、结构化输出、兜底调用需要不同模型配置。
- OpenAI-compatible 平台多数能复用请求格式，但能力支持并不完全一致。
- RAG / Agent / eval 都需要统一记录 token、耗时、模型版本和错误类型。
- Chat、Embedding、Rerank 角色不同，必须避免混用。

如果只是一次性脚本，直接 SDK 调用完全可以；但需求评审助手是持续演进项目，后续课程会不断复用 LLM 层，所以本节开始就把边界立住。

---

## 主流框架实现

| 方式 | 与本项目 |
| --- | --- |
| **OpenAI SDK** | `OpenAICompatProvider` 内部使用；`base_url` 对接兼容平台 |
| **本项目 LLMClient** | 业务与 demo 通过 `config_ref` 调用；日志与切换集中 |
| **LangChain ChatModel** | 后续 RAG 拼链时可从同一 `models.yaml` 读 model，避免两套配置 |

原则：**配置真源在 `models.yaml` + `.env`**；框架是消费方，不在业务里再写一份 model 名。

---

## 失败分析与能力边界

### 排查路径（表现 → 原因 → 怎么验证）

**1. `auth`：一调用就失败，提示环境变量未配置**

- **表现**：`LLMError` code 为 `auth`，消息含 `OPENAI_API_KEY 未配置` 或 401。
- **原因**：`.env` 未复制、Key 名与 `api_key_env` 不一致、`base_url` 与 Key 不匹配。
- **验证**：检查仓库根 `.env`；`provider_switching.py --verbose` 看请求是否发出；换 Key 后是否立即恢复。

**2. `rate_limit`：偶发 429**

- **表现**：`rate_limit`，有时重试又好。
- **原因**：供应商 QPS / 配额；开发环境多人共用一个 Key。
- **验证**：换 `chat.fallback_chat` 对比；记录 `latency_ms` 与发生时段；完整重试策略在专题 06，**当节**会换 config_ref 即可。

**3. `capability_mismatch`：配置条目用错角色**

- **表现**：对 `embedding.default_embed` 调 `chat` 立刻报错。
- **原因**：Chat 与 Embedding API 路径不同，不能混用 `config_ref`。
- **验证**：`models.yaml` 看 `role` 字段；业务是否误把 embed 配置传给 `LLMClient.chat`。

**4. 兼容平台「能 chat 但不能 structured / tool」**

- **表现**：普通 `chat` 正常，03 的 `json_schema` 报 `API_ERROR`。
- **原因**：OpenAI 兼容 ≠ 全功能兼容；`capabilities.structured_output` 仅为文档性标签，不自动降级。
- **验证**：对比 `chat.dev_chat` 与 `chat.structured_chat`；结构化细节在专题 03。

### 常见误区

| 误区 | 纠正 |
| --- | --- |
| 「有 `base_url` 就等于 OpenAI」 | 参数支持与限额因平台而异 |
| 「`config_ref` 可以随意命名」 | 必须与 YAML section.name 一致，否则 `KeyError` |
| 「多轮对话 API 会记住」 | 历史由应用拼进 `messages` |
| 「`usage` 可省略」 | 成本与上下文问题靠 usage 发现；08 专讲成本 |

### 本节不做（defer）

| 能力 | 目标节 | 当节最小判断 |
| --- | --- | --- |
| 流式输出 | 04 | 知道非流式一次返回 `content` 即可 |
| 完整重试 / 熔断 | 06 | 会用 `LLMErrorCode` 分类，遇 429 知换 `fallback` |
| Structured Outputs | 03 | 知 `chat.structured_chat` 预留给结构化任务 |
| 实际调用 embedding | 03_rag | 知 YAML 里已有 `embedding.default_embed`，01 不调 |
| harness 落盘 | 07 | demo 对比 + 笔记记录 token/latency |
| 多轮会话持久化 | 04 | 知历史在 `messages`，不由 API 保存 |

---

## 本节实战

### 目标

业务通过 `config_ref` 调用模型；所有调用返回统一 `LLMResponse`；`--verbose` 时可看清 system/user、参数与完整回复；能在 S2 样例上对比至少两个 `config_ref`。

### 涉及文件

关键路径：

- [`source/packages/llm_core/client.py`](../../source/packages/llm_core/client.py)：统一调用入口。
- [`source/packages/llm_core/config.py`](../../source/packages/llm_core/config.py)：`ModelConfig`、`LLMResponse` 等数据结构。
- [`source/packages/llm_core/config/models.yaml`](../../source/packages/llm_core/config/models.yaml)：模型配置真源。
- [`source/demos/02_provider_switching/provider_switching.py`](../../source/demos/02_provider_switching/provider_switching.py)：本节观察入口。

完整文件说明和命令变体放在 [demo README](../../source/demos/02_provider_switching/README.md)。

### 实现步骤（与最小实现对照）

1. 从根目录 `.env` 读取 Key、base_url 和模型名。
2. 从 `models.yaml` 通过 `config_ref` 找到模型配置。
3. 用 `LLMClient.chat()` 发起调用并返回 `LLMResponse`。
4. 在 demo 表格中观察：不同 `config_ref` 对应的 model、latency、usage 与输出差异。

### 步骤 1：配置环境（OpenAI 默认）

```bash
cd <仓库根>
cp .env.example .env
# 编辑 .env，填写 OPENAI_API_KEY
pip install -e .
```

DeepSeek 等 OpenAI-compatible 平台可通过 `.env` 切换 `OPENAI_BASE_URL` / `OPENAI_MODEL`，具体配置细节见 demo README。

### 步骤 2：运行对比 demo

```bash
cd source/demos/02_provider_switching
python provider_switching.py
```

### 建议观察清单

- [ ] 两个 `config_ref` 的 `model` 字段是否如 YAML 预期
- [ ] `temperature=0` vs `0.7` 下 `content` 稳定性差异
- [ ] `usage` 是否随 Prompt 长度变化（体会 token 与成本）
- [ ] `--verbose` 能否看清完整 `messages` 传给云端的内容（命令见 README）

本节不是要证明哪个模型最好，而是训练一种观察方法：固定样例，只变一个配置点，再看 `LLMResponse` 中的 model、usage、latency 和输出内容如何变化。系统化落盘会在专题 07 进入 harness。

---

## 完成标准

- **能解释**：一次 Chat 的输入（messages、config_ref、参数）与输出（`LLMResponse` 各字段）。
- **能说明**：`temperature` / `max_tokens` 对输出的影响。
- **能画出**：从直调 SDK 到 `config_ref` 的五步递进，各步遗留什么问题。
- **能配置**：OpenAI 或 DeepSeek（`.env` + `models.yaml`）。
- **能运行**：`provider_switching` 默认对比与 `--verbose`。
- **能说明**：为何业务写 `config_ref` 而不是写死 model 字符串。

### 运行与观察

```bash
cd source/demos/02_provider_switching
python provider_switching.py
python provider_switching.py --verbose
```

应看到至少 2 行对比；verbose 下可见 system/user 与完整 assistant 回复。详见 [demo README](../../source/demos/02_provider_switching/README.md)。

### 自检题

1. 多轮对话的历史存在哪里？通过 API 的哪个字段带给模型？
2. 为什么业务代码应写 `config_ref="chat.dev_chat"` 而不是 `model="gpt-4o"`？
3. 把 Chat 模型名填进 embedding 接口会导致什么问题？
4. `.env` 与 `models.yaml` 各解决什么，为什么不能只用其中一个？
5. 收到 `LLMErrorCode.RATE_LIMIT` 时，当节可以先做哪一步，完整重试策略在哪一节？
6. `LLMResponse` 相比 SDK 原始响应，多解决了哪两个工程问题？

---

## 本节沉淀

- 新增 `llm_core` 调用层（`LLMClient`、`models.yaml`、`ConfigRegistry`、`LLMResponse`、`LLMError`）与 `02_provider_switching` demo。
- 需求评审助手具备：**按任务切换模型配置、统一响应结构与可观测日志**；00 的 `02_first_chat` 保留作 SDK 直调对照。
- 下一节 [02_prompt_engineering_for_apps.md](02_prompt_engineering_for_apps.md) 在同一 `LLMClient` 上叠加 Prompt 模板。

---

## 相关专题

- 上一篇：[00_llm_problem_space.md](00_llm_problem_space.md)
- 下一篇：[02_prompt_engineering_for_apps.md](02_prompt_engineering_for_apps.md)
- 课程大纲：[outline.md](outline.md)
