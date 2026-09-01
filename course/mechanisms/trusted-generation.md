# 可信生成：模型写了来源编号，为什么还不能直接相信

> Context 装入已经把检索名单变成模型真正能看到的 `BuiltContext`，并产生本轮允许声明的来源 `Citation Candidate`。本文继续解释固定 RAG 的生成核心机制：调用真实模型生成结构化风险，并由应用检查模型声明的 `source_id` 是否来自本轮候选。
>
> 学完后，你应该能区分“JSON 合法”“来源编号属于本轮候选”和“证据真的支持结论”这三个完全不同的判断。本文只解释前两个层次；Citation 支持性、证据充分性和 Refusal 需要后续机制继续完成。

## 先看一个很像成功的结果

模型返回：

```json
{
  "risks": [
    {
      "title": "售后接口缺少来源渠道",
      "category": "api",
      "level": "high",
      "rationale": "新入口需要传递 source_channel。",
      "citations": [
        {"source_id": "API-AFTER-SALE-V2"}
      ]
    }
  ]
}
```

这个结果看起来很完整：JSON 能解析、字段齐全、风险合理，还有来源编号。

但程序至少还要问三个问题：

1. 这些字段和枚举是否符合 `ReviewRiskList`？
2. `API-AFTER-SALE-V2` 是否真的属于本轮允许引用的来源？
3. 这条来源的内容是否真的支持“缺少来源渠道”这个结论？

它们对应三层不同的可信边界：

```text
结构合法
  ↓
来源声明属于本轮候选
  ↓
来源内容支持当前结论
```

当前机制完成前两层：

- 使用 Structured Output 和本地解析检查结构；
- 使用 Citation Candidate allowlist 检查来源声明。

第三层需要读取声明对应的证据，并判断它与具体风险之间的支持关系。这是后续 Citation 支持性的 Citation 校验，不在本节伪装成已经完成。

因此，本节标题里的“可信生成”应理解为：

> 生成输入、输出结构和来源声明开始受到应用约束并可被检查，而不是模型的每条结论已经被证明为真。

## 先把五个对象拆开

初学时最容易把 Source、Citation Candidate 和 Citation 都叫“引用”。但从资料进入系统到成为经过验证的引用，中间要逐层收紧：

```text
Source
  ↓ Retriever 选择
Retrieved Candidate
  ↓ Context Builder 选择
Citation Candidate
  ↓ 模型在输出中声明
Claimed Citation
  ↓ 应用检查内容支持关系
Validated Citation（后续 Citation 支持性）
```

### Source

系统中存在的一条资料或 Chunk。它只表示“系统拥有这份资料”，还不知道本轮是否相关。

### Retrieved Candidate

Retriever 为当前问题找到的候选。它可能通过 Lexical、Dense 或两路 RRF 进入最终检索结果，但仍可能在 Context Builder 中被去重、压缩或丢弃。

### Citation Candidate

Context Engineering最终 included 的 Evidence 来源。它满足两项事实：

- 模型在本轮输入中真的看到了它；
- 应用允许模型使用它的 `source_id` 作为来源声明。

它还没有和某条具体风险建立支持关系。

### Claimed Citation

模型输出中的：

```json
{"source_id": "chunk-api"}
```

这只是模型的一次声明。模型能够生成任何字符串，即使 Structured Output 已经限制 `source_id` 必须是字符串，也不能保证这个字符串来自本轮候选。

### Validated Citation

应用已经确认：来源存在、可定位、版本有效，而且它的内容确实支持当前结论。本节还没有交付这一层。

所以必须避免下面这个跳跃：

```text
模型写了 source_id
        ✗
界面立即显示“已验证依据”
```

本节最多能显示“模型声明的来源候选”，并保留当前检查边界。

## 本节怎样接上前面的数据

前面每一步保留下来的信息，在这里进入一次真实生成：

```text
文档解析与 Chunking
资料 → 带稳定 chunk_id 和 locator 的 Chunk
        ↓
检索链
Lexical + Dense + RRF → RetrievalResult
        ↓
Context Engineering
ContextSource → BuiltContext + Citation Candidate
        ↓
本节
Prompt v5 + Structured Output → ReviewRisk[]
        ↓
Citation Candidate membership check
        ↓
TrustedGenerationResult + TrustedGenerationReport
```

本节没有重新实现前面已有的能力：

- `BuiltContext` 提供 Requirement、Evidence、History 和候选 ID；
- `review.risk_review@5.0.0` 负责生成任务协议；
- `LLMClient.chat_structured` 负责真实模型调用和结构化解析；
- `ReviewRiskList` 定义结果形状；
- `rag_core.generate_trusted_review` 负责组合这些对象并检查来源声明。

这依然是固定 Pipeline。执行顺序由应用预先写好，模型没有决定是否调用 Retriever，也没有 Tool 或 Agent Loop。

## 生成边界接收什么，返回什么

可信生成只接收已经构建完成、带构建报告的 BuiltContext。它返回结构化风险、真实模型响应、实际模型输入、生成状态和来源声明报告。缺少构建报告时不能猜测哪些已保留来源具有引用资格，应直接暴露契约错误。

这一步仍是固定 Pipeline：顺序由应用预先确定，模型还没有选择 Retriever、Tool 或循环行动的权力。

## 第一道约束：Prompt 把候选 ID 明确列出来

Context Engineering的 Evidence block 已经带有 source ID，但只让模型“自己从文本里找编号”不够明确。Prompt v5 会额外生成：

```text
## Allowed Citation Source IDs
- chunk-order-rule
- chunk-after-sale-api
```

如果本轮没有 Citation Candidate，则是：

```text
## Allowed Citation Source IDs
（无）
```

Prompt 同时规定：

- 只有依据 Current Evidence 的结论才添加 citation；
- `source_id` 必须逐字选自 Allowed Citation Source IDs；
- Requirement 是被评审对象，不能成为 citation；
- Historical Context 只能提醒检查方向，不能成为 citation；
- allowlist 为空时，所有 citations 必须为空；
- 不确定时减少结论，不要生成未知 ID。

这些规则解决的是“模型应该怎样做”。它们不能保证模型一定照做，所以 Prompt 是第一道防线，不是最终校验。

### 为什么 Requirement 风险可以没有 citation

假设 Requirement 自己写着：

```text
失败时区分网络错误和业务拒绝。
```

却没有说明两种失败分别如何展示。模型可以指出：

```text
需求未定义网络错误与业务拒绝的交互反馈。
```

这是一条针对 Requirement 内部缺失的评审判断，不需要伪造一个外部来源。

但如果模型声称：

```text
售后接口规定必须传 source_channel。
```

这已经是在陈述外部规则，应当声明对应的 Current Evidence。

因此，“风险没有 citation”不自动等于错误；应用必须先区分它是在评审 Requirement 自身，还是在引用外部事实。当前本节只统计 `risk_without_citation_count`，还没有自动完成这种语义分类。

## 第二道约束：Schema 检查输出形状

真实调用使用 `ReviewRiskList`：

```text
ReviewRiskList
└── risks[]
    ├── title: string
    ├── category: interaction | state_flow | api | ...
    ├── level: high | medium | low
    ├── rationale: string
    └── citations[]
        ├── source_id: string
        └── excerpt?: string
```

当 Provider 支持时，`json_schema` 会把 Pydantic 生成的 Schema 作为严格 response format 发给模型。若 Provider 只支持 JSON object，可以显式选择 `json_object`，然后仍由本地解析器校验字段和枚举。

无论使用哪种模式，本地都会经历：

```text
模型文本
  ↓ JSON 解析
Python 对象
  ↓ ReviewRiskList / ReviewRisk 校验
ReviewRisk[] 或 parse failure
```

解析错误会保留发生阶段：

| `parse_error_stage` | 含义 |
| --- | --- |
| `empty` | 模型没有返回内容 |
| `json` | 内容不是支持的 JSON 根结构或 JSON 语法错误 |
| `schema` | JSON 可解析，但字段、枚举或类型不符合业务 Schema |

解析失败时，`result.risks` 为空，状态是 `structured_output_invalid`。应用不能把原始字符串继续当成成功评审结果。

### 为什么 Schema 不能顺便校验本轮 source ID

业务 Schema 只能规定 `source_id` 是字符串，但 `chunk-order-rule` 和 `chunk-after-sale-api` 是本轮检索与 Context 构建后才产生的动态集合。Schema 知道 `source_id` 必须是字符串，却不知道这一次只允许哪几个字符串。

理论上可以为每次调用动态生成枚举 Schema，但当前项目没有采用这种设计。当前实现保持稳定业务 Schema，并在解析后执行动态集合检查。这两个职责因此分开：

```text
Schema                 → 这个字段是不是合法字符串
Candidate membership  → 这个字符串是不是本轮允许的 ID
```

## 第三道约束：应用逐项检查来源声明

结构解析成功后，应用逐条遍历风险和 Citation，判断声明的 `source_id` 是否属于本轮 Citation Candidate 集合。每次检查都要保留风险位置、Citation 位置、原始 ID 和判断状态，使未知来源能够定位到具体声明。集合成员检查只确认 ID 合法，不判断内容是否支持结论。

### 为什么不能按标题自动猜来源

假设真正候选 ID 是：

```text
chunk_f34162ec83acabe4
```

模型却输出：

```text
API-AFTER-SALE-V2
```

它看起来可能像接口文档标题，但应用不能自动找“最相似”的来源并替换。否则会把模型的无效声明篡改成看似合法的 Citation，用户再也分不清原始输出和应用猜测。

正确做法是：

- 保留模型原始 `source_id`；
- 标记为 `unknown_source`；
- 将整次结果置为非成功状态；
- 再从 Prompt、Evidence 格式或模型能力层定位原因。

## 三种状态是怎样得到的

当前 `GenerationStatus` 只有三种：

```text
parse ok?
├── no  → structured_output_invalid
└── yes
    ├── 存在 unknown source → unknown_citation_source
    └── 不存在 unknown      → succeeded
```

| 状态 | 确定知道什么 | 本节应怎样处理 |
| --- | --- | --- |
| `succeeded` | 结构合法；所有已声明的 source ID 都属于候选 | 可以作为本节生成结果，但不能标成已验证 Citation |
| `structured_output_invalid` | 模型结果未通过 JSON / Schema 解析 | 生成失败，不进入业务成功结果 |
| `unknown_citation_source` | 结构合法，但至少一个声明不在 allowlist | 生成失败，不能把未知 ID 做成可信链接 |

### 一个容易忽略的逻辑：没有 citation 也可能 `succeeded`

集合检查只检查“已经声明的 citation”。如果一条或多条风险完全没有 citation：

```text
claimed_citation_count = 0
unknown_source_count = 0
```

只要结构解析成功，当前状态仍是 `succeeded`。

这不表示系统已证明“这些风险不需要证据”，也不表示模型正确执行了 Prompt。它只表示：没有出现未知来源声明。

因此下面两个判断不能混淆：

```text
所有 claimed IDs 都合法
≠
所有需要外部证据的结论都提供了 citation
```

后一个判断需要理解风险内容和证据需求，属于证据充分性与生成评估边界。

## `TrustedGenerationReport` 怎样避免过度宣称

报告会记录：

- `prompt_ref`、`config_ref` 与 `structured_mode`；
- `citation_candidate_ids`；
- 当前 `evidence_state`；
- parse 是否成功及错误阶段；
- risk 总数和无 citation 的 risk 数量；
- claimed citation 总数；
- candidate / unknown 数量；
- 每个声明的逐项检查；
- `citation_boundary`。

当前 `citation_boundary` 固定为：

```text
candidate_membership_only_not_support_validation
```

它的中文含义是：

> 只检查来源声明是否属于本轮 Citation Candidate，不检查来源内容是否支持该风险。

这个字段不是注释，而是报告语义的一部分。看到 `candidate_claim_count = 3` 时，只能说“3 个声明来自本轮候选”，不能改写成“3 条引用正确”或“3 条风险有证据支持”。

## 空 Evidence 时，系统实际完成了什么

当 `citation_candidate_ids` 为空时，报告的：

```text
evidence_state = no_citation_candidates
```

它可能由不同上游原因造成：

- Retriever 没有最终候选；
- 候选在 Context Builder 中全部被去重、策略排除或预算丢弃；
- 本轮只有 History，没有可引用的 Current Evidence。

生成层不会重新猜测原因，只把空 allowlist 和 Context 一起交给 Prompt，并要求 citations 为空。

模型仍然可以针对 Requirement 本身指出明确缺失或矛盾。例如 Requirement 要求区分错误类型，却没有定义 UI 行为；这是评审输入本身可见的问题。

模型不可以在空 Evidence 时声称：

```text
接口错误码是 CLIENT_PARAM_INVALID。
```

因为这个事实既不在 Requirement，也没有外部 Evidence 支持。

当前实现会检查空 allowlist 下模型是否编造了 source ID：任何 citation 都会成为 `unknown_source`。但如果模型写了一条无 citation 的外部事实，本节的集合检查看不出来。

这正是为什么：

```text
NO_CITATION_CANDIDATES
≠ 自动 Refusal
≠ 没有任何风险可输出
≠ 所有无 citation 结论都合理
```

完整 Refusal、补充问题和证据充分性策略在后续 Citation 支持性建立。

## 一个合法 ID 仍可能引用错误内容

假设候选 `chunk-api` 的真实内容是：

```text
售后接口需要 order_id。
```

模型却输出：

```json
{
  "title": "必须传 source_channel",
  "rationale": "接口要求来源渠道",
  "citations": [
    {
      "source_id": "chunk-api",
      "excerpt": "必须传 source_channel"
    }
  ]
}
```

`chunk-api` 确实属于本轮 allowlist，所以当前状态会是 `succeeded`。但这条 excerpt 并不存在，来源内容也不支持该结论。

本节没有检查：

- excerpt 是否出现在来源原文；
- 引用定位是否仍对应正确版本；
- 证据是否蕴含、支持或反驳风险；
- 一条风险的证据是否充分；
- 多条证据之间是否冲突。

这个例子不是代码 bug，而是当前机制刻意保留的能力边界。若正文把 `candidate` 翻译成“引用正确”，就会把尚未实现的后续 Citation 支持性能力写成成功事实。

## 为什么真实实验要比较三种 Context

只运行“正确 RAG Evidence”很难判断模型究竟是在使用证据，还是看见任意 Evidence 后就变得更肯定。

当前实验对同一个 Requirement 构造三组 Context：

```text
同一个售后 Requirement
├── rag_evidence
│   └── 真实 Retriever 找到的售后规则
├── normal_noise
│   └── 合法格式但只描述营销活动入口的 Evidence
└── empty_evidence
    └── 没有 Citation Candidate
```

三组都调用真实模型，不使用预写的模型答案。

### `rag_evidence` 观察什么

它经过真实 Loader、Chunker、PostgreSQL FTS、pgvector、RRF 和 Context Builder。观察模型是否使用真正属于本轮售后证据的 ID。

### `normal_noise` 观察什么

这条材料的身份和格式都合法，也被明确放进 Evidence，但内容只描述营销活动入口。它用于观察模型会不会把“任意合法 Evidence”错误当成当前需求依据。

注意：noise 是生成层的对照探针，不是 Retriever 自然召回结果。它不会写入售后知识范围，也不能用来证明 Metadata Filter 失效。

### `empty_evidence` 观察什么

它用于观察 allowlist 为空时模型是否保持 citations 为空，以及模型会不会仍然编造外部资料事实。

三组对照的重点不是比较 risk 数量谁最多，而是观察：

- 外部事实是否随着 Evidence 内容合理变化；
- claimed IDs 是否都属于各自 Context 的 allowlist；
- normal noise 是否被错误引用来支持售后结论；
- empty evidence 是否出现未知 ID；
- 无 citation 风险究竟是在评审 Requirement，还是在陈述无依据外部事实。

最后两项仍需要学习者阅读输出或后续 Eval，不能只靠 membership 数量自动判断。

## 真实生成对照应该验证什么

同一生成入口应分别接收真实 RAG Evidence、正常但无关的噪声和空 Evidence。对照时观察结构化结果、声明的来源 ID、membership 校验和最终状态，不能只看语言是否流畅。运行、日志、单 variant、Provider 兼容与排障见[配套实验](../labs/trusted-generation.md)。

## 一个完整 bad case 怎样从后往前定位

表现如下：模型返回一条接口风险，声明 `API-V2`，但界面无法打开这个来源，生成状态是 `unknown_citation_source`。

不要只改 Prompt。按链路检查：

### 1. 先看模型究竟输出了什么

从 `TrustedGenerationReport.claim_checks` 找到：

```text
risk 1, citation 1
API-V2 → unknown_source
```

确认不是 UI 丢字段，也不是显示层拼错 ID。

### 2. 看本轮 allowlist

检查本轮报告保存的 Citation Candidate ID 集合

若真实候选是稳定 Chunk ID `chunk_f34162ec83acabe4`，而模型写了文档简称 `API-V2`，membership check 的失败是正确的。

### 3. 看最终 Prompt

检查 `result.messages` 中的 Allowed Citation Source IDs 是否真的包含稳定 ID。若候选报告里有、Prompt 里没有，问题在变量装配或模板渲染；若 Prompt 里有但模型仍改写了 ID，问题更接近 Prompt 遵循或模型能力。

### 4. 再回查 Context Builder

如果你原本期待 `API-V2` 对应的来源进入，却根本不在 allowlist，回到Context Engineering看它是否：

- 被映射成 History；
- 因预算 dropped；
- 因重复内容被去重；
- 不是 current evidence。

### 5. 必要时才回查 Retriever

如果 Context 候选池里从未出现这条来源，再查 RetrievalReport。不要因为模型声明了一个听起来合理的名字，就反向假定 Retriever 曾经找到它。

这条定位链可以写成：

```text
claim check
→ allowlist
→ rendered messages
→ ContextBuildReport
→ RetrievalReport
```

它与前面“从 Retriever 向模型追踪来源”方向相反，但检查的是同一条可追踪链。

## 真实依赖失败和结果失败不是一回事

`generate_trusted_review` 返回的三种 `GenerationStatus` 都发生在 Provider 已经返回响应之后。

下面这些失败则可能直接抛出 `LLMError`：

- API key 缺失或鉴权失败；
- 限流或网络超时；
- endpoint / model 不存在；
- 配置角色不是 chat；
- Provider 不支持所选 structured response format。

因此运行层至少要区分：

```text
模型调用没有成功
  → LLMError / dependency failure

模型调用成功但内容无法进入程序
  → structured_output_invalid

内容结构合法但来源声明越界
  → unknown_citation_source

结构与已声明 ID 都通过本节边界
  → succeeded
```

把鉴权失败转换成 `risks=[]` 会制造“模型认为没有风险”的假象；把 parse failure 的原文直接展示成正式报告，则绕过了应用 Schema。两种做法都会破坏可观察边界。

## 确定性验证能证明什么

确定性验证可以证明状态推导、结构契约、逐项来源 membership 和诊断报告符合规则；它不能证明引用内容真正支持结论，也不能证明 Evidence 已经充分。后两项需要独立的 Citation 支持性和证据充分性机制。

## SDK 和框架封装不了哪些业务判断

模型 SDK、Pydantic 和各种 RAG 框架可以帮助我们：

- 发送 messages；
- 请求 JSON object 或 JSON Schema；
- 解析业务对象；
- 组织 Retriever 与 Context；
- 保存 token、latency 和原始响应。

但它们不会自动知道：

- Requirement 为什么不能成为 Citation；
- History 为什么只能辅助而不能证明当前规则；
- 本轮哪些 included source 具备引用资格；
- 未知 ID 是否应该让整次业务结果失败；
- 一条无 citation 风险是否只基于 Requirement；
- 某条证据是否真正支持当前风险；
- 空证据时应该继续评审、拒答还是追问。

这些是需求评审助手的证据责任和阶段边界，必须由应用契约、代码与后续 Eval 共同建立。

## 到本节，固定 RAG 学到了什么程度

完成固定 RAG 核心链，并亲自运行实验、解释报告、定位边界和完成修改题后，可以称为：

> 完成固定 RAG 核心机制入门。

此时你已经能解释：

```text
外部资料
→ 可追踪 Chunk
→ Lexical + Dense + RRF
→ 可诊断 RetrievalResult
→ 受预算控制的 BuiltContext
→ 真实结构化生成
→ Citation Candidate membership report
```

但“本节读完”不等于“RAG 全部掌握”。还需要：

- 第一阶段后续：Citation 内容支持性、来源定位、证据充分性、Refusal、补充问题、API、Web 工作台、固定对照、最小评估和阶段验收；
- 第二阶段：需要动态决策时，再进入 Query Rewrite、Source Routing、Retriever as Tool 和单 Agent RAG；完整 Trace、回归、bad case 与反馈在第二阶段后部收束。

判断自己是否“掌握”，不看读了多少篇，而看能否解释、验证、修改、调试和取舍这条链。

## 学完后的自检

先不看正文，回答：

- 为什么 JSON Schema 通过后，`source_id` 仍可能是模型编造的？
- Source、Retrieved Candidate、Citation Candidate、Claimed Citation 和 Validated Citation 分别是什么？
- `candidate` 状态具体证明了什么，又没有证明什么？
- 为什么 Requirement 内部缺失风险可以没有 citation？
- 为什么无 citation 风险仍可能让当前本节状态成为 `succeeded`？
- 空 Evidence 时，为什么不能简单理解成“模型必须什么都不说”？
- 合法 source ID 搭配虚假 excerpt 时，当前机制为什么仍可能通过？
- `unknown_citation_source` 为什么不能自动按标题匹配一个来源？
- `LLMError`、`structured_output_invalid` 和 `unknown_citation_source` 分别发生在哪一层？
- normal noise 对照能观察什么，不能证明什么？

再做一次完整追踪：从一条 `Citation Candidate` 开始，在渲染后的 allowlist 中找到它，运行真实模型，找到对应 Claimed Citation 和 `CitationClaimCheck`，最后说出它距离 Validated Citation 还缺哪一步。

如果你能完成这条追踪，并且不会把 `succeeded` 解释成“引用内容已验证”，就完成了本节的核心目标。

后续还需要完成 Citation 支持性和证据充分性，再把这条固定 RAG 核心链交付为 API、Web 工作台和可比较的第一阶段产品基线。阅读顺序仍以[标准学习路径](../learning-path.md)为准。
