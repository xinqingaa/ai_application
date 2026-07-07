# 05. Context Engineering

> 04 已经把流式 token、事件协议和 conversation history 分开。本篇回答：**模型调用前，应用如何把当前需求、证据、历史摘要和 Agent 中间结论装配成可追溯、可预算、可诊断的上下文**。

---

## 真实问题

到 04 为止，需求评审助手已经能完成模型调用、Prompt 版本化、结构化输出和流式展示。但这些能力都有一个共同前提：模型收到的 `messages` 质量足够好。真实项目里，`messages` 不再只是一个 user 字符串，而会混入 PRD、业务规则、接口文档、历史评审、上一轮对话、RAG 召回片段、Agent 中间结论、Workflow 状态和人工补充说明。

如果没有 Context Engineering，系统会自然滑向两个极端。一个极端是“能拿到什么就都塞进去”：Prompt 变长、成本上升、模型在旧材料和新材料之间摇摆，还可能把历史评审里的旧接口规则套到当前需求上。另一个极端是“只给当前用户问题”：模型看不到业务规则和接口约束，只能凭常识生成风险，最后输出看起来合理但无法溯源。

本节要解决的不是“如何检索材料”，而是更靠近 LLM 底座的一层问题：**候选材料已经来了，应用如何决定哪些进 Prompt、以什么顺序进、超过预算时怎么压缩或丢弃、哪些 source 可以被引用、诊断信息如何帮助定位 bad case**。

### 学习者真实问题

如果你有前端 / Flutter / 客户端背景，上下文很容易被理解成“聊天历史”或“Prompt 里的材料”。这个理解太窄。AI 应用里的 context 更像一次运行前的**输入装配层**：它决定哪些信息被模型看见，哪些信息只用于 UI 或 trace，哪些信息可以成为最终答案的依据，哪些信息即使存在也不能进入下一轮模型调用。

前端开发里也有类似经验。一个复杂页面不会把接口返回、缓存、埋点、错误栈、调试日志和临时 UI 状态全塞进一个组件 props；你会区分页面主数据、派生状态、临时状态、错误状态和调试信息。Context Engineering 做的是同类分层，只是对象变成了模型调用。模型没有真正的“背景知识管理器”，它只看本次输入窗口。窗口里放错材料，后面再强的 Schema、流式 UI 或 Agent loop 都会被污染。

所以，本节不是教你“把长文本塞进模型”。它训练的是工程判断：这条材料是当前任务、证据、历史摘要、Agent 中间结论，还是噪声？它能不能被引用？它超过预算时应该压缩还是丢弃？如果模型引用了不存在的 source id，是检索没命中、builder 丢了、Prompt 没约束，还是模型编造？

### 产品真实问题

产品同学小周继续评审 S2：订单详情页新增「申请售后」入口，对接售后接口 v2。前几节里，我们只把 PRD 和一段静态 `evidence_s2.json` 交给模型。现在评审负责人提出更真实的要求：一次评审不能只看 PRD，还要参考订单状态机、售后接口 v2 文档、三端客户端展示规则、历史售后入口评审摘要，以及上游 Agent 初步给出的风险分析。

第一次尝试时，后端把这些材料简单拼接：

```text
PRD + 业务规则 + 接口文档 + 客户端说明 + 历史评审 + Agent 输出 + 旧接口笔记
```

模型确实“知道得更多”，但风险列表反而变糊了。它引用了过期 v1 接口笔记，把历史评审里的旧问题当成当前必然问题，还把上游 Agent 的猜测当成证据。前端展示出的风险卡片带了 citation，但有些 citation 指向的 source 根本不应该作为证据。评审负责人追问“这条风险依据是哪份文档”，团队才发现：系统没有记录这次调用到底纳入了哪些材料，也没有区分 evidence、history 和 agent_summary。

这说明产品需要的不是更长 Prompt，而是一套上下文装配规则：当前需求永远是主任务；业务规则、接口文档、客户端说明是可引用证据；历史评审只能作为参考摘要；Agent 中间结论不能替代原始证据；过期材料即使出现，也应该低优先级或被丢弃；预算不足时要能解释为什么某条 source 没进 Prompt。

### 工程真实问题

工程上，Context Engineering 至少要拆成六层：

| 层 | 解决什么 | 本节落点 |
| --- | --- | --- |
| 候选材料池 | 输入材料来源不同，不能直接拼接 | `ContextSource` |
| 规范化与去重 | 同一 source 或重复内容不能反复进入 Prompt | source id / content dedupe |
| 排序与策略 | 不同任务需要不同优先级 | `ContextBuildPolicy` |
| 分区预算 | requirement、evidence、history、agent summary 不能抢同一个池子 | `ContextSection` |
| 压缩与丢弃 | 超预算时可解释地压缩或丢弃 | deterministic compression + dropped reason |
| 引用映射与诊断 | 最终输出 citation 必须能校验 | citation candidates + report warnings |

本节的代码会把这些层做成 `llm_core.context` 的核心能力；demo 只负责加载样例并调用它。

---

## 基础原理

### 本节方案性质

Context Engineering 没有唯一标准答案。不同产品可能使用 RAG、长上下文、摘要记忆、LangGraph state、向量检索、rerank、context compression 或人工标注结果。它们不是互斥方案，而是上下文装配链路中的不同环节。

本节要区分四层：

| 层级 | 本节怎么理解 |
| --- | --- |
| **通用原则** | 上下文必须分层；当前任务优先；证据可追溯；预算不足要可见；中间过程不能直接污染事实依据 |
| **工程实践** | 先把材料变成有身份的候选项，再按策略装配 Prompt，并输出诊断报告 |
| **项目取舍** | 本节用静态样例模拟材料池；压缩只做确定性片段抽取，不做 LLM 摘要 |
| **非目标** | 不把本节做成完整 RAG；不实现 embedding / vector store / rerank；不把 token 估算当真实计费 |

换句话说，本节不是提前实现 03_rag，而是给后续 RAG、Agent、Workflow 准备一个统一入口：无论材料来自静态 JSON、检索结果、工具调用还是 Agent 摘要，都先变成候选材料，再由 builder 决定是否进入模型输入。

### 先用一个小例子抓住主线

假设本轮评审只有三条材料：

```text
用户需求：订单详情页新增「申请售后」入口。
接口文档：售后接口 v2 必填 order_id、sku_list、apply_reason、source_channel、paid_at。
历史评审：上一次售后入口遗漏重复申请拦截，造成用户重复提交。
```

如果只把用户需求交给模型，模型可能凭常识说“注意接口异常”，但说不出 v2 必填参数，也不能给出来源。如果把三条材料原样拼进去，模型又可能把“历史评审里发生过的问题”当成当前需求已经确定存在的问题。更麻烦的是，模型最终输出 citation 时，应用不知道它引用的是接口文档、历史摘要，还是自己编出来的 source id。

Context Engineering 解决的就是这一步：**模型调用前，应用先整理本轮输入**。它不是让模型更聪明，而是让模型看到的材料更干净、边界更清楚、事后更好排查。

本节的最小数据流可以记成一句话：

```text
候选材料 ContextSource
→ 按 ContextBuildPolicy 取舍
→ 生成 Prompt 变量和 citation candidates
→ 用 ContextBuildReport 解释为什么这样装配
```

这四个动作对应四个问题：

| 问题 | 本节对象 | 白话解释 |
| --- | --- | --- |
| 我现在手上有哪些材料？ | `ContextSource` | 一条候选材料，还没决定放不放进 Prompt |
| 本轮按什么规则取舍？ | `ContextBuildPolicy` | 预算、优先级、哪些类型允许进入 |
| 模型最终能看到什么？ | `BuiltContext` | 已经组织好的 Requirement / Evidence / History / Agent Summary |
| 为什么是这个结果？ | `ContextBuildReport` | 哪些 source 进了、丢了、压缩了、能被引用 |

先抓住这条线，再看后面的 `source_type`、section budget、compression 和 citation，就不会觉得它们是突然冒出来的术语。

### 先把几个词说清楚

**Context**：本次模型调用能看到的全部输入，不只是聊天历史。它包括 system prompt、user prompt、当前需求、证据、历史摘要、Agent 摘要等。

**Context window**：模型一次调用最多能接收的 token 上限。窗口变大只是“装得下更多”，不代表材料相关、可信或可追溯。

**Context budget**：应用主动给本轮上下文设置的预算。即使模型窗口很大，也要控制成本、噪声和排查复杂度。

**Source**：一条带身份的材料。它不只是文本，还要有 `source_id`、`source_type`、标题、优先级和 metadata。

**Evidence**：可以支撑当前结论的证据材料。接口文档、业务规则、客户端接入说明通常可以作为 evidence；历史评审和 Agent 中间判断不默认作为当前事实依据。

**Citation**：模型输出里指向 evidence 的引用。03 的 Schema 只能保证 `citations` 字段长得对；05 的 `citation_candidates` 才告诉应用：本次 Prompt 中哪些 source id 是合法候选。

### 候选材料池不等于最终 Prompt

很多初学者会把 context 理解成最终 Prompt 里的那段文字。但工程上要先区分两个概念：

```text
候选材料池：应用当前能拿到的所有可能有用材料
最终 Prompt：本次模型调用实际能看到、且按规则组织后的材料
```

候选材料池可以很杂：PRD、接口文档、业务规则、历史评审、Agent 输出、工具日志、用户反馈、旧版本材料。最终 Prompt 必须更克制：它只包含当轮任务真正需要的内容，并且每个可引用证据都有 source id。

如果没有这个分层，系统无法回答一个关键问题：模型没提到接口 v2，是因为没有检索到接口文档，还是检索到了但被预算裁掉，还是进入 Prompt 后模型忽略了？这三个问题的修复方向完全不同。

这也解释了为什么 `ContextSource` 不是“多余包装”。如果材料只是一段字符串，builder 就不知道它来自接口文档还是历史摘要，不知道能不能被引用，也不知道重复内容应该保留哪一条。把材料变成 `ContextSource`，不是为了写更多类，而是为了让后面的取舍有依据。

### Source Type 决定能否作为证据

本节把候选材料封装成 `ContextSource`，其中最重要的不是 `content`，而是 `source_type`。

| source_type | 含义 | 是否可作为 citation |
| --- | --- | --- |
| `business_rule` | 业务规则、状态机、权限约束 | 可以 |
| `api_doc` | 接口文档、错误码、字段定义 | 可以 |
| `client_note` | 客户端接入说明、三端规则 | 可以 |
| `evidence` | 其他可引用证据 | 可以 |
| `history_review` | 历史评审摘要 | 不默认作为当前事实依据 |
| `agent_summary` | 上游 Agent 中间结论 | 不作为 citation，只作辅助 |
| `tool_result` | 工具调用结果 | 本节放入 agent summary 区，后续按工具类型细化 |
| `other` | 噪声或暂不分类材料 | 通常不作为 citation |

这个区分非常重要。历史评审和 Agent 输出可以帮助模型注意风险方向，但它们不能替代当前需求的原始证据。如果模型把 `agent_summary` 当成 citation，前端展示出来会给用户一种“这条风险有文档依据”的错觉。

可以这样判断：**能被用户点开追溯、并且确实描述当前规则或接口的材料，才适合做 citation**。历史评审可以提醒“重复申请以前出过问题”，但它不能证明当前接口 v2 的字段要求；Agent 摘要可以提醒“可能关注三端一致性”，但它不能证明三端 API 的真实规则。

### Context Builder 的工程流水线

本节的 builder 按下面顺序处理材料：

```text
requirement_text
  + candidate ContextSource[]
      ↓
source normalize / dedupe
      ↓
source_type + priority + score 排序
      ↓
按 policy 分 section budget
      ↓
必要时确定性压缩 source
      ↓
生成 sections / evidence_block / citation_candidates
      ↓
生成 ContextBuildReport
```

这里的“策略”不是为了炫技，而是因为不同任务上下文需求不同：

- 风险识别应优先业务规则和接口文档。
- 报告汇总可能需要更多 history 和 agent_summary。
- 追问任务可能应该在 evidence 不足时保留缺口诊断。
- 紧预算任务宁愿压缩历史，也要保留当前 PRD 与关键证据。

因此 `ContextBuildPolicy` 可以理解成“本轮装配规则”。它不是模型参数，也不是 Prompt 文案，而是应用在模型调用前做的一次工程取舍。例如 `evidence_first` 表示风险审查优先保留业务规则、接口文档和客户端说明；`tight_budget` 表示预算很小，允许压缩 source，并且会丢掉低优先级材料。

### 分区预算比一个总预算更可控

只给一个 `token_budget=1200` 会出现一个常见问题：某类材料独占预算。例如历史评审很长，排序又靠前，它可能挤掉当前接口文档。真实项目里更稳的做法是把预算分区：

```text
requirement: 当前任务
evidence: 可引用证据
history: 历史摘要
agent_summary: 中间结论
other: 兜底材料
```

分区预算不是绝对标准答案，但它让工程调试更清楚：如果 `evidence` 不够，就调整 evidence budget；如果 history 污染结果，就调低 history budget 或换策略，而不是盲目加大整个上下文窗口。

反例：如果只有总预算，历史评审摘要可能因为 priority 不低而挤掉客户端三端说明。模型最后没提 H5 / iOS / Android 一致性，你可能误以为模型漏看了，其实是 builder 根本没把这条材料放进去。分区预算让这类问题能从 report 中直接看到。

### 压缩不是简单截断字符串

上下文超预算时，最粗暴的办法是 `text[:N]`。这会导致两个问题：source id 还在，但关键句可能被截断；或者截断位置正好切掉错误码、状态约束、接口字段。用户看到 citation 时，以为模型依据完整文档，实际 Prompt 里只有半截。

本节先做确定性的 **extractive compression**。它的意思是：不让模型重写摘要，而是从原文里抽取更相关的行或句子。比如接口文档很长，当前需求包含“售后接口 v2、订单状态、重复申请”，压缩器会优先保留包含这些词的句子。

这不是完美摘要，也不保证保留所有关键事实。它的优点是可解释：保留下来的话仍来自原文，source id 不变，report 会记录哪条 source 从多少 token 压到了多少 token。它的风险也必须明确：如果关键词没覆盖真正关键的句子，压缩会丢事实。后续 RAG 或 LLM 摘要压缩会更强，但本节先用确定性方法帮助你看清“压缩会改变模型看见的事实”。

### Citation Candidates 是应用侧边界

03 的 `ReviewRisk.citations` 只是结构形状，不能保证 source id 真实存在。05 增加 `citation_candidates`，告诉下游：**本次 Prompt 中哪些 source id 是合法证据引用候选**。

这一步对后续评估和前端都重要：

- 前端可以把合法 citation 渲染成可点击来源。
- 评估可以判断模型是否引用了不存在 source。
- bad case 可以定位到“模型编造 citation”还是“builder 没放入关键 source”。

本节只生成 citation candidates，不做完整 citation 校验；真实校验会在 RAG 和 eval 阶段继续深化。

最小判断路径是：

```text
模型输出 citation=API-AFTER-SALE-V2
→ 先看 ContextBuildReport.citation_source_ids 是否包含它
→ 不包含：模型编造或 Prompt 约束不足
→ 包含：再看该 source 是否被压缩、内容是否真的支持这条风险
```

### 从弱到强的机制递进

**第 1 步 · 只放用户问题**

模型只看到“这个需求有什么风险”。实现最简单，但会依赖常识。反例：PRD 没写接口错误码，模型却编造 `SERVICE_TIMEOUT`。

**第 2 步 · 把所有材料拼进 Prompt**

模型能看到更多信息，但噪声和过期材料也进来了。反例：旧 v1 接口笔记被模型当作当前 v2 约束。

**第 3 步 · 用 Prompt 变量区分 Requirement / Evidence**

比纯拼接更清楚，但 evidence 仍然只是字符串。反例：模型输出 citation 时，应用不知道 source id 是否真实存在。

**第 4 步 · ContextSource + source_type**

材料有身份、类型、优先级、score 和 metadata。反例减少了，但如果只按总预算处理，history 仍可能挤掉 evidence。

**第 5 步 · Policy + Section Budget**

不同任务使用不同策略，requirement、evidence、history、agent_summary 各有预算。仍遗留：超预算 source 怎么处理？

**第 6 步 · Compression + Citation Map + Report**

source 可被压缩，合法引用候选可被列出，drop / warning 可被诊断。仍遗留：真实检索、rerank、LLM 摘要、引用质量评估在后续课程处理。

这条递进和前几节是连起来的：02 解决 Prompt 任务协议，03 解决输出能不能进程序，04 解决生成过程和 history 边界，05 解决模型调用前“本轮到底该看什么”。如果 05 没做好，Prompt 再清楚、Schema 再严格，也只是让模型稳定地处理一份被污染或缺证据的输入。

### 与 Prompt、Structured Output、Conversation 的分工

| 能力 | 负责什么 | 不负责什么 |
| --- | --- | --- |
| Prompt | 告诉模型任务、约束和输出要求 | 不决定材料来源与预算 |
| Context Builder | 决定哪些材料进入 Prompt，如何编号、压缩、诊断 | 不判断最终内容是否正确 |
| Structured Output | 校验输出字段、枚举和根形态 | 不保证 citation 真实 |
| Conversation | 保存稳定 user / assistant 历史 | 不保存 token、错误栈、工具日志 |
| RAG | 生产候选 evidence | 不应直接绕过 context builder |

---

## 最小实现

本节代码要验证的不是“模型回答更好了吗”，而是上下文装配链路能不能可解释地工作。最小实现不应该从 demo 开始，因为 demo 很容易把加载样例、排序、预算、压缩和打印结果混在一起。更稳的工程切分是：核心规则沉淀在 `llm_core.context`，demo 只调用 package API 做观察。

这一版最小实现守住五个不变量：

1. `requirement_text` 是当前任务输入，不作为 citation source。
2. 只有 `business_rule`、`api_doc`、`client_note`、`evidence` 这类当前证据可以成为 citation candidate。
3. `history_review`、`agent_summary` 可以进入上下文辅助判断，但不能替代当前证据。
4. 被压缩、被去重、被预算丢弃的 source 必须出现在 report 里。
5. demo 不能实现核心排序、压缩、引用映射逻辑，只能加载样例、选择策略、打印结果。

完整代码阅读顺序见 [llm_core README](../../source/packages/llm_core/README.md) 和 [context demo README](../../source/demos/02_context_lab/README.md)。

### 1. 候选材料与策略

[`context/types.py`](../../source/packages/llm_core/context/types.py) 定义材料契约和策略契约：

```python
@dataclass(frozen=True)
class ContextSource:
    source_id: str
    content: str
    source_type: ContextSourceType = "evidence"
    title: Optional[str] = None
    priority: int = 50
    score: Optional[float] = None
    metadata: dict[str, str] = field(default_factory=dict)

@dataclass(frozen=True)
class ContextBuildPolicy:
    name: str
    token_budget: int
    section_budgets: dict[ContextSectionName, int]
    allow_compression: bool = True
    max_source_tokens: Optional[int] = 180
```

这里的关键不是字段数量，而是职责边界。`ContextSource` 表示“应用拿到的一条候选材料”，它还没有资格直接进入 Prompt；`ContextBuildPolicy` 表示“一次装配实验的预算和过滤规则”，它让 `minimal`、`evidence_first`、`tight_budget` 等策略可以复用同一条 builder 流水线。

策略预设放在 [`context/policies.py`](../../source/packages/llm_core/context/policies.py)，而不是写在 demo 参数里。这样后续 RAG、Agent、Workflow 接入时，只要继续产出 `ContextSource`，就能沿用同一套上下文边界。

### 2. 构造结果与诊断报告

[`context/builder.py`](../../source/packages/llm_core/context/builder.py) 是主流水线，内部会调用 ranking、compression、formatting 和 tokenization；[`context/types.py`](../../source/packages/llm_core/context/types.py) 则定义最终诊断结构：

```python
@dataclass(frozen=True)
class ContextBuildReport:
    policy_name: str
    token_budget: int
    estimated_tokens: int
    section_tokens: dict[ContextSectionName, int]
    dropped_sources: list[DroppedContextSource]
    compressed_sources: list[CompressedContextSource]
    citation_candidates: list[CitationCandidate]
    warnings: list[ContextWarning]
```

这份 report 是 05 代码的重点。没有 report，上下文工程就只能靠“看最终答案猜原因”。有了 report，bad case 可以沿着上下文装配链路定位：source 是否进了？是否被压缩？是否可引用？是否因为策略被排除？

builder 的主流程可以简化理解为：

```text
ContextSource[]
→ normalize / dedupe
→ rank by source_type + priority + score
→ fill requirement / evidence / history / agent_summary sections
→ compress or drop when budget is tight
→ build citation candidates and ContextBuildReport
```

这也是为什么 05 的核心代码拆成子模块，而不是堆在单个文件中：

- `types.py` 只放数据契约。
- `policies.py` 只放策略预设。
- `ranking.py` 只处理归一化、去重、排序、分区。
- `compression.py` 只处理确定性压缩。
- `builder.py` 负责编排这些步骤并返回 `BuiltContext`。

### 3. Demo 只调用 package API

[`context_compare.py`](../../source/demos/02_context_lab/context_compare.py)：

```python
policy = get_context_policy(strategy)
context = build_review_context(
    requirement_text=str(case["requirement_text"]),
    sources=_load_sources(case),
    policy=policy,
)
print(context.included_source_ids)
print(context.report.citation_source_ids)
```

这段代码刻意很薄：demo 只加载样例、选择策略、打印结果。排序、压缩、预算、citation candidates 和 warnings 都在 `llm_core.context` 内部完成。这样新增 demo 不会变成另一套平行实现，也不会把 05 的核心能力耦合进某个脚本。

---

## 主流框架实现

LangChain 的 `Document(page_content, metadata)` 和本节的 `ContextSource` 很接近：二者都把文本和 metadata 绑在一起。区别在于，本节更早强调 `source_type`、section budget 和 citation candidates，因为需求评审助手后续要把证据展示给前端，而不仅是让模型“读到”一段文字。

Contextual Compression Retriever 的思路是：先检索，再根据 query 压缩 chunk。它和本节的 extractive compression 方向一致，但本节没有真实 retriever，也不调用模型做摘要，只做确定性的句/行级选择。这样更适合在 02_llm 阶段理解机制：压缩不是魔法，它会改变模型能看到的事实，因此必须记录在 report 里。

Conversation memory 处理的是多轮会话怎样保留。它不等于 context builder。Memory 可以生产 `history_summary`，但是否进入本轮 Prompt、占多少预算、能不能作为 citation，仍应由 context builder 决定。

LangGraph state 处理的是 workflow 节点之间的状态传递。它也不应直接塞进 Prompt。更稳的做法是：节点状态或工具结果先被整理成 `agent_summary` / `tool_result`，再由 policy 判断是否进入模型输入。

所以，框架能提供抽象，但本节要迁移的是工程边界：

```text
Document / Memory / State / Tool Result
→ ContextSource
→ ContextBuildPolicy
→ BuiltContext + ContextBuildReport
```

---

## 失败分析与能力边界

### 1. 模型引用了不存在的 source id

- **表现**：结构化输出里出现 `source_id=OLD-V1`，但前端找不到来源。
- **原因**：模型编造 citation，或 Prompt 中没有把合法候选约束清楚。
- **怎么验证**：先看 `ContextBuildReport.citation_source_ids`。如果不包含该 id，就是模型或 Prompt 问题；如果包含，再查 source 内容是否被压缩到失真。

### 2. 关键接口文档没进入 Prompt

- **表现**：模型没有提 `AFTER_SALE_DUPLICATED` 或 v2 必填参数。
- **原因**：接口文档未进入候选池、被重复去重、被预算丢弃，或被压缩时没保留关键句。
- **怎么验证**：看 `included_sources`、`dropped_sources.reason`、`compressed_sources` 和 `prompt_preview`。不要直接怪模型。

### 3. 历史评审污染当前需求

- **表现**：模型把历史售后入口的问题当成当前需求必然存在的问题。
- **原因**：history budget 过高，或历史材料被当成 evidence。
- **怎么验证**：比较 `full_context` 与 `evidence_first`。如果 `evidence_first` 输出更贴当前 PRD，说明历史材料噪声过强。

### 4. Agent 中间结论被当作事实依据

- **表现**：模型引用上游 Agent 的“初步判断”作为 citation。
- **原因**：没有区分 `agent_summary` 与 `evidence`。
- **怎么验证**：看 `citation_candidates` 是否包含 Agent source。按本节实现，Agent summary 不应成为 citation candidate。

### 5. 紧预算下 source 被压缩后丢失关键句

- **表现**：`tight_budget` 策略下 source 仍进入 Prompt，但关键字段没出现。
- **原因**：确定性压缩只保留部分相关句，不保证语义完整。
- **怎么验证**：看 `compressed_sources` 与 `prompt_preview`。若关键句丢失，应提高该 source 优先级、增大 evidence budget，或在 RAG 阶段改 chunk。

### 6. Token 估算和真实 usage 不一致

- **表现**：`estimated_tokens` 与 API 返回 `usage.prompt_tokens` 不一致。
- **原因**：本节估算只覆盖 context 材料；真实请求还包含 system prompt、任务描述、schema、消息包装和供应商 tokenizer 差异。
- **怎么验证**：把 `estimated_tokens` 当作上下文预算参考；真实成本统计放到 08。

### 常见误区

| 误区 | 纠正 |
| --- | --- |
| 「context window 很大，所以不用做 context builder」 | 大窗口只解决装得下，不解决相关性、可追溯和诊断 |
| 「RAG 检索到了就直接塞进 Prompt」 | 检索结果仍要经过排序、预算、压缩和引用映射 |
| 「history 和 evidence 都是上下文，所以可以混放」 | history 只能参考，不能默认作为当前事实依据 |
| 「压缩就是摘要，摘要一定更好」 | 压缩会丢事实，必须可观察、可回滚 |
| 「citation 字段通过 Schema 就可信」 | Schema 只管形状；source 是否真实要看 citation candidates |

### 本节不做（defer）

| 能力 | 目标节 | 当节最小判断 |
| --- | --- | --- |
| 文档 chunk、embedding、vector search、rerank | 03_rag | 本节只消费候选 source，不生产检索结果 |
| LLM 摘要压缩 | 03_rag / 后续项目 | 本节只做确定性 extractive compression |
| citation 真伪的批量评估 | 05_eval_observability | 本节只生成合法候选 |
| Agent scratchpad 管理和工具权限 | 04_agent | 本节只接收整理后的 `agent_summary` |
| 真实成本、延迟和缓存 | 08 | 本节只估算上下文材料 token |

---

## 本节实战

### 目标

为需求评审助手增加一个可复用 Context Builder：能把候选材料池按策略装配成 Prompt 变量，并输出 section tokens、included/dropped/compressed source、citation candidates 和 warnings。

### 涉及文件

关键路径：

- [`source/packages/llm_core/context/`](../../source/packages/llm_core/context/)：核心上下文工程子包，包含数据契约、策略、排序、压缩和 builder。
- [`source/packages/llm_core/context/types.py`](../../source/packages/llm_core/context/types.py)：`ContextSource`、`ContextBuildPolicy`、`BuiltContext`、`ContextBuildReport` 等数据结构。
- [`source/packages/llm_core/context/builder.py`](../../source/packages/llm_core/context/builder.py)：上下文装配主流程。
- [`source/packages/llm_core/context/policies.py`](../../source/packages/llm_core/context/policies.py)：`minimal`、`balanced`、`evidence_first`、`tight_budget` 等策略预设。
- [`source/packages/llm_core/tests/test_context.py`](../../source/packages/llm_core/tests/test_context.py)：策略、压缩、引用映射和诊断测试。
- [`source/demos/02_context_lab/context_compare.py`](../../source/demos/02_context_lab/context_compare.py)：05 context lab 观察入口，只调用 package API。
- [`source/demos/02_context_lab/context_cases.json`](../../source/demos/02_context_lab/context_cases.json)：需求评审材料池样例。
- [`source/demos/02_context_lab/README.md`](../../source/demos/02_context_lab/README.md)：demo 运行与输出说明。

### 实现步骤

1. 把 PRD、业务规则、接口文档、客户端说明、历史评审、Agent 摘要、过期材料都表示为 `ContextSource`。
2. 通过 `get_context_policy(...)` 选择上下文策略。
3. `build_review_context(...)` 执行去重、排序、分区预算、压缩、citation candidates 生成。
4. `context_compare.py` 打印每个策略的 report 和 prompt preview。
5. 可选打开 `COMPARE_WITH_MINIMAL`，把 `minimal` 与 `evidence_first` 交给真实模型，对比无证据和带证据时输出差异。

### 运行方式

离线测试：

```bash
uv run pytest source/packages/llm_core/tests/test_context.py
```

策略对比：

```bash
uv run python source/demos/02_context_lab/context_compare.py
```

`context_compare.py` 顶部提供学习期实验开关，改完后仍运行上面这一条短命令：

```python
DEFAULT_STRATEGY = "evidence_first"
CALL_LLM = True
COMPARE_WITH_MINIMAL = False
PRINT_MESSAGES = False
PRINT_FULL_CONTEXT = False
```

真实项目中，这类值通常来自配置、环境变量或后台开关；本节 demo 先放在文件顶部，避免每次靠一长串 CLI 参数控制行为。

常见改法：

| 想观察什么 | 推荐配置 |
| --- | --- |
| 默认真实模型结果 | `DEFAULT_STRATEGY = "evidence_first"`，`CALL_LLM = True` |
| 只看上下文构建诊断 | `DEFAULT_STRATEGY = "evidence_first"`，`CALL_LLM = False` |
| 紧预算压缩 + 真实模型 | `DEFAULT_STRATEGY = "tight_budget"`，`CALL_LLM = True` |
| 带/不带证据对比 | `DEFAULT_STRATEGY = "evidence_first"`，`COMPARE_WITH_MINIMAL = True`，`PRINT_MESSAGES = True` |

### 预期结果

默认运行会输出 `evidence_first` 策略。你应重点观察：

- `minimal`：只有 requirement，warning 提示没有 evidence。
- `full_context`：更多材料进入 Prompt，可能包含 history 和 old note。
- `evidence_first`：优先保留业务规则、接口文档、客户端说明。
- `tight_budget`：出现 compressed / dropped source。
- `agent_summary_only`：Agent 摘要可以进上下文，但 citation candidates 为空。

典型片段：

```text
[strategy] tight_budget
  [included_sources] BR-ORDER-STATE, API-AFTER-SALE-V2
  [citation_candidates] BR-ORDER-STATE, API-AFTER-SALE-V2
  [compressed_sources] API-AFTER-SALE-V2
  [dropped_sources]
    CLIENT-DETAIL-API reason=token_budget_exceeded
```

这说明模型可以引用业务规则和接口文档，但客户端说明因为预算不足没有进入 Prompt。如果最终答案缺少三端展示风险，应先查 context report，而不是直接改 Prompt。

真实模型对照时，你应观察两件事：

- `minimal` 只有 Requirement，`citation_candidates` 为空。模型即使能说出一些风险，也很难给出可靠来源。
- `evidence_first` 会把业务规则、接口文档和客户端说明放进 Evidence。模型更容易输出带 source id 的风险，但仍要检查 citation 是否在候选列表里。

默认运行会输出 `[context_build]`、`[built_context_preview]` 和 `[llm_result]`。前两段是上下文构建诊断，不是模型最终结果；`[llm_result] parse=ok` 才是模型输出的结构化评审结果。只有把 `CALL_LLM = False` 时，demo 才会进入离线诊断模式，不调用真实模型。

### 经典案例：读懂一次 minimal vs evidence_first 输出

当你把配置改成：

```python
DEFAULT_STRATEGY = "evidence_first"
COMPARE_WITH_MINIMAL = True
PRINT_MESSAGES = True
```

脚本会连续跑两组：第一组 `minimal`，第二组 `evidence_first`。这是一组很适合学习的对照，因为它让你看到“同一个 PRD，不带证据”和“带证据”到底差在哪里。

读这种大段输出时，不要从头到尾逐字看。按四步读：

```text
strategy
→ context_build
→ messages
→ llm_result
```

**第一步，看 `strategy`：这次在比较什么。**

`minimal` 表示只保留当前 Requirement，不带任何 Evidence。它是“无上下文 / 只靠 PRD”的基线。`evidence_first` 表示优先保留业务规则、接口文档和客户端说明，是本节推荐的风险审查策略。

**第二步，看 `context_build`：模型调用前，应用到底准备了什么。**

`minimal` 的关键片段通常是：

```text
[strategy] minimal
  [included_sources] —
  [citation_candidates] —
  [warnings]
    no_evidence_included
```

这说明 builder 没有放入任何证据，也没有任何合法 citation 候选。后面模型即使输出风险，也只能基于 Requirement 和常识判断。

`evidence_first` 的关键片段通常是：

```text
[strategy] evidence_first
  [included_sources] BR-ORDER-STATE, API-AFTER-SALE-V2, CLIENT-DETAIL-API
  [citation_candidates] BR-ORDER-STATE, API-AFTER-SALE-V2, CLIENT-DETAIL-API
```

这说明本次 Prompt 里放进了三条可引用证据：订单状态机、售后接口 v2、客户端接入说明。后面模型如果引用这三个 source id，至少说明引用对象来自本次上下文。

同时要看 `dropped_sources`。例如：

```text
API-AFTER-SALE-V2-DUP reason=duplicate_content
HISTORY-2026-0412 reason=token_budget_exceeded
AGENT-RISK-SUMMARY reason=token_budget_exceeded
NOISE-OLD-V1 reason=token_budget_exceeded
```

这里不是“丢了就坏”。重复接口摘录被去重，是好事；历史评审、Agent 摘要和过期 v1 笔记没有进入 evidence，也避免了旧信息和中间结论污染当前事实依据。

**第三步，看 `messages`：模型实际收到的输入。**

`PRINT_MESSAGES = True` 时，终端会打印 system / user messages。这里你要确认两件事：

- `minimal` 的 Evidence 段是“无可用证据”。
- `evidence_first` 的 Evidence 段里真的包含 `[BR-ORDER-STATE]`、`[API-AFTER-SALE-V2]`、`[CLIENT-DETAIL-API]`。

这一步回答的是：“我以为带了上下文，模型是否真的看到了？”如果这里没有出现某条 source，再去怪模型漏答就没有意义。

**第四步，看 `llm_result`：模型最后生成了什么。**

`minimal` 也可能返回 `parse=ok`，例如：

```text
[llm_result] parse=ok risks=7
  [1] interaction/medium ... cites=PRD片段
```

这说明结构化解析成功了，但不代表引用可信。因为 `minimal` 的 `citation_candidates` 是空的，`PRD片段` 并不是合法 source id。这个结果正好说明：**Schema 只能保证字段长得对，不能保证 citation 真实。**

`evidence_first` 的结果通常更像这样：

```text
[llm_result] parse=ok risks=6
  [1] interaction/high ... cites=BR-ORDER-STATE
  [2] api/high ... cites=API-AFTER-SALE-V2
  [4] exception/medium ... cites=CLIENT-DETAIL-API
```

这说明模型输出的风险开始绑定到合法证据上。比如 `apply_reason` 缺失只能从接口文档里稳定得出；弱网下跳转丢失上下文来自客户端说明；入口展示条件与状态机不一致来自业务规则和 PRD 的组合。

这组案例要沉淀的判断是：

| 对比点 | `minimal` | `evidence_first` |
| --- | --- | --- |
| 模型看到什么 | 只有 Requirement | Requirement + 三条 Evidence |
| citation candidates | 空 | 三个合法 source id |
| 输出风险 | 看起来也合理，但更像常识推断 | 更具体，能绑定接口字段、状态机、客户端规则 |
| 最大风险 | 模型会编造或自造 citation 名 | 仍需检查 citation 是否落在 candidates 中 |

因此，本节不是要证明“带上下文一定更聪明”，而是要证明：**带经过 builder 筛选和编号的上下文，模型输出才更容易被追溯、调试和评估。**

---

## 完成标准

- 能解释候选材料池与最终 Prompt 的区别。
- 能说明 `source_type` 为什么影响 citation candidates。
- 能解释 `minimal`、`full_context`、`balanced`、`evidence_first`、`tight_budget`、`agent_summary_only` 的取舍。
- 能运行 `context_compare.py`，读懂 included / dropped / compressed / warnings。
- 能根据一个 bad case 判断应该改 source、policy、budget、Prompt，还是后续 RAG。
- 能说明本节为什么不做真实检索、不做 LLM 摘要、不做 citation eval。

### 运行与观察

```bash
uv run pytest source/packages/llm_core/tests/test_context.py
uv run python source/demos/02_context_lab/context_compare.py
```

观察点：

- section token 是否符合策略预期。
- `API-AFTER-SALE-V2-DUP` 是否因为重复内容被 drop。
- `citation_candidates` 是否只包含 evidence 类 source。
- 若把 `DEFAULT_STRATEGY` 改为 `tight_budget`，是否出现 compressed source。
- 若把 `DEFAULT_STRATEGY` 改为 `agent_summary_only`，是否不会产生 citation candidates。

### 自检题

1. 为什么“检索到了材料”不等于“可以直接进入 Prompt”？
2. `history_review` 和 `business_rule` 都能帮助模型，为什么只有后者适合作为 citation？
3. 如果模型漏掉三端展示风险，你会如何沿 context report 排查？
4. `tight_budget` 下 source 被压缩，为什么仍要保留 source id 和 compression warning？
5. `full_context` 看起来信息最多，为什么不一定是最佳策略？
6. 后续 RAG 接入时，retriever 输出应如何转换为本节的 `ContextSource`？

---

## 本节沉淀

- `llm_core.context` 从简单 evidence formatter 升级为策略化 Context Builder，包含 source、policy、section、report、citation candidates 和确定性压缩。
- `02_context_lab` 作为 context 观察 lab，用独立入口比较不同 context 策略，避免和 Structured Outputs demo 耦合。
- 下一节 06 Reliability、Errors 与 Degradation 将处理模型调用失败、结构化失败、超时和降级；05 的 report 会成为后续 harness / eval 诊断的重要输入。

---

## 相关专题

- 上一篇：[04_streaming_and_conversation.md](04_streaming_and_conversation.md)
- 下一篇：[06_reliability_errors_and_degradation.md](06_reliability_errors_and_degradation.md)
- 课程大纲：[outline.md](outline.md)
