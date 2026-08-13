# 可信生成：模型写了来源编号，为什么还不能直接相信

> 这是一篇机制篇。第 15 步已经把检索候选装配成模型真正能看到的 `BuiltContext`，并产生本轮 `Citation Candidate`。本节继续完成 V0 固定 RAG 的最后一段核心机制：调用真实模型生成结构化风险，并由应用检查模型声明的 `source_id` 是否来自本轮候选。
>
> 学完后，你应该能区分“JSON 合法”“来源编号属于本轮候选”和“证据真的支持结论”这三个完全不同的判断。V0 只实现前两个层次，不提前宣称完成 Citation 支持性、证据充分性或 Refusal。

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

当前 V0 代码完成前两层：

- 使用 Structured Output 和本地解析检查结构；
- 使用 Citation Candidate allowlist 检查来源声明。

第三层需要读取声明对应的证据，并判断它与具体风险之间的支持关系。这是 V1 的 Citation 校验，不在本节伪装成已经完成。

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
Validated Citation（V1）
```

### Source

系统中存在的一条资料或 Chunk。它只表示“系统拥有这份资料”，还不知道本轮是否相关。

### Retrieved Candidate

Retriever 为当前问题找到的候选。它可能通过 Lexical、Dense 或两路 RRF 进入最终检索结果，但仍可能在 Context Builder 中被去重、压缩或丢弃。

### Citation Candidate

第 15 步最终 included 的 Evidence 来源。它满足两项事实：

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

应用已经确认：来源存在、可定位、版本有效，而且它的内容确实支持当前结论。V0 还没有交付这一层。

所以必须避免下面这个跳跃：

```text
模型写了 source_id
        ✗
界面立即显示“已验证依据”
```

V0 最多能显示“模型声明的来源候选”，并保留当前检查边界。

## 第 16 步怎样接上前面的数据

前面每一步保留下来的信息，在这里进入一次真实生成：

```text
第 8–9 步
资料 → 带稳定 chunk_id 和 locator 的 Chunk
        ↓
第 11–14 步
Lexical + Dense + RRF → RetrievalResult
        ↓
第 15 步
ContextSource → BuiltContext + Citation Candidate
        ↓
第 16 步
Prompt v5 + Structured Output → ReviewRisk[]
        ↓
Citation Candidate membership check
        ↓
TrustedGenerationResult + TrustedGenerationReport
```

第 16 步没有重新实现前面已有的能力：

- `BuiltContext` 提供 Requirement、Evidence、History 和候选 ID；
- `review.risk_review@5.0.0` 负责生成任务协议；
- `LLMClient.chat_structured` 负责真实模型调用和结构化解析；
- `ReviewRiskList` 定义结果形状；
- `rag_core.generate_trusted_review` 负责组合这些对象并检查来源声明。

这依然是固定 Pipeline。执行顺序由应用预先写好，模型没有决定是否调用 Retriever，也没有 Tool 或 Agent Loop。

## 公共入口接收什么，返回什么

当前公共入口位于 `rag_core.generation`：

```python
from rag_core import generate_trusted_review

result = generate_trusted_review(
    context,
    config_ref="chat.structured_chat",
    structured_mode="json_schema",
)
```

它的核心输入是一个已经构建完成的 `BuiltContext`。这里有一个重要前提：

```python
context.report is not None
```

因为 Citation Candidate IDs 来自 `ContextBuildReport`。如果调用者手工造了一个没有 report 的 `BuiltContext`，函数会直接拒绝，而不是猜测哪些 included source 可以引用。

输出 `TrustedGenerationResult` 包含四部分：

```text
status      本轮生成状态
risks       成功解析出的 ReviewRisk
messages    实际渲染出的模型输入
response    Provider 响应、usage、latency 与 parse 结果
report      来源声明和生成边界的诊断
```

这让我们既能使用业务结果，也能回看模型真正收到了什么、解析发生了什么，以及每个来源声明怎样被分类。

## 第一道约束：Prompt 把候选 ID 明确列出来

第 15 步的 Evidence block 已经带有 source ID，但只让模型“自己从文本里找编号”不够明确。Prompt v5 会额外生成：

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

因此，“风险没有 citation”不自动等于错误；应用必须先区分它是在评审 Requirement 自身，还是在引用外部事实。当前 V0 只统计 `risk_without_citation_count`，还没有自动完成这种语义分类。

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

`ReviewRiskList` 在代码加载时定义：

```python
class Citation(BaseModel):
    source_id: str
```

但 `chunk-order-rule` 和 `chunk-after-sale-api` 是本轮检索与 Context 构建后才产生的动态集合。Schema 知道 `source_id` 必须是字符串，却不知道这一次只允许哪几个字符串。

理论上可以为每次调用动态生成枚举 Schema，但当前项目没有采用这种设计。当前实现保持稳定业务 Schema，并在解析后执行动态集合检查。这两个职责因此分开：

```text
Schema                 → 这个字段是不是合法字符串
Candidate membership  → 这个字符串是不是本轮允许的 ID
```

## 第三道约束：应用逐项检查来源声明

结构解析成功后，`generate_trusted_review` 会遍历每条 risk 的每个 citation：

```text
for each risk
  for each claimed citation
    source_id ∈ citation_candidate_ids ?
      yes → candidate
      no  → unknown_source
```

对应的判断本质上只是集合成员检查：

```python
citation.source_id in citation_ids
```

每个声明都会形成一条 `CitationClaimCheck`：

```text
risk_index
risk_title
citation_index
source_id
status = candidate | unknown_source
```

为什么需要保留 risk 和 citation 的序号？因为只记录“出现一个未知来源”还不够排查。学习者必须能回答：是第几条风险的第几个 citation 出错，模型实际写了什么。

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

| 状态 | 确定知道什么 | V0 应怎样处理 |
| --- | --- | --- |
| `succeeded` | 结构合法；所有已声明的 source ID 都属于候选 | 可以作为 V0 生成结果，但不能标成已验证 Citation |
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

当前实现会检查空 allowlist 下模型是否编造了 source ID：任何 citation 都会成为 `unknown_source`。但如果模型写了一条无 citation 的外部事实，V0 的集合检查看不出来。

这正是为什么：

```text
NO_CITATION_CANDIDATES
≠ 自动 Refusal
≠ 没有任何风险可输出
≠ 所有无 citation 结论都合理
```

完整 Refusal、补充问题和证据充分性策略在 V1 建立。

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

V0 没有检查：

- excerpt 是否出现在来源原文；
- 引用定位是否仍对应正确版本；
- 证据是否蕴含、支持或反驳风险；
- 一条风险的证据是否充分；
- 多条证据之间是否冲突。

这个例子不是代码 bug，而是当前版本刻意保留的能力边界。若正文把 `candidate` 翻译成“引用正确”，就会把尚未实现的 V1 能力写成成功事实。

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

## 运行真实生成实验

主入口是 [inspect_trusted_generation.py](../../source/demos/rag_retrieval_lab/inspect_trusted_generation.py)。它先构建真实 RAG Context，再创建 noise 与 empty 对照，最后逐组调用真实 chat 模型。

在仓库根目录运行：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_trusted_generation.py
```

需要真实：

- `DATABASE_URL`；
- Embedding Provider、模型与 API key；
- chat Provider、模型与 API key；
- 已执行的 PostgreSQL / pgvector migration。

缺少配置、鉴权失败、限流、超时或 structured mode 不受支持时，实验会明确失败，不会切换到假检索、假模型或静态成功结果。

### 展开每条风险和声明检查

```bash
uv run python source/demos/rag_retrieval_lab/inspect_trusted_generation.py --verbose
```

先读汇总表：

| 输出 | 应怎样理解 |
| --- | --- |
| `Evidence` | 当前是否存在 Citation Candidate |
| `Risks` | 成功解析出的风险数量 |
| `No citation` | 没有声明来源的风险数量 |
| `Known` | 声明 ID 属于候选的数量 |
| `Unknown` | 声明 ID 不属于候选的数量 |
| `Status` | parse 与 membership 组合后的状态 |

然后再看 verbose 中每条 risk 的 `claims` 和逐项状态。不要从 `Known > 0` 直接得出“模型回答正确”。

### 只运行一个 variant

```bash
uv run python source/demos/rag_retrieval_lab/inspect_trusted_generation.py \
  --variants rag_evidence --verbose
```

只运行一组可以缩短排查范围，但也失去了三组对照，不能据此判断模型是否对任意 Evidence 都有同样反应。

### Provider 不支持 `json_schema` 时

如果你已经确认目标 Provider 只支持 JSON object，可以显式运行：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_trusted_generation.py \
  --structured-mode json_object
```

这是一次新的实验条件。应记录 structured mode，不能先让 `json_schema` 失败，再在代码里静默切换并把后者伪装成同一次成功。

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

检查：

```python
result.report.citation_candidate_ids
```

若真实候选是稳定 Chunk ID `chunk_f34162ec83acabe4`，而模型写了文档简称 `API-V2`，membership check 的失败是正确的。

### 3. 看最终 Prompt

检查 `result.messages` 中的 Allowed Citation Source IDs 是否真的包含稳定 ID。若候选报告里有、Prompt 里没有，问题在变量装配或模板渲染；若 Prompt 里有但模型仍改写了 ID，问题更接近 Prompt 遵循或模型能力。

### 4. 再回查 Context Builder

如果你原本期待 `API-V2` 对应的来源进入，却根本不在 allowlist，回到第 15 步看它是否：

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

结构与已声明 ID 都通过 V0 边界
  → succeeded
```

把鉴权失败转换成 `risks=[]` 会制造“模型认为没有风险”的假象；把 parse failure 的原文直接展示成正式报告，则绕过了应用 Schema。两种做法都会破坏可观察边界。

## 确定性测试能证明什么

本节测试可以离线运行：

```bash
uv run pytest \
  source/packages/rag_core/tests/test_trusted_generation.py \
  source/packages/llm_core/tests/test_client_structured.py -q
```

测试使用构造的模型响应，验证应用自己的确定性逻辑：

1. 已知 ID 被标记为 `candidate`；
2. 未知 ID 使结果成为 `unknown_citation_source`；
3. 无 citation 风险保持可见，不被误算成 unknown source；
4. 空 Evidence 会把 allowlist 渲染为“无”；
5. 非 JSON 输出成为 `structured_output_invalid`；
6. 没有 `ContextBuildReport` 的 Context 被拒绝；
7. `json_object` response format 和请求参数会传给调用层。

它们不能证明：

- 真实 Provider 支持当前 `json_schema`；
- 模型一定逐字复制候选 ID；
- 模型不会引用 normal noise；
- 无 citation 风险都有合理依据；
- excerpt 存在于原文；
- source 内容支持风险结论；
- RAG 质量达到产品验收标准。

Mock response 适合固定集合检查，不可以被当成真实模型效果证据。

## 从实验进入关键代码

第一次阅读时，沿着一条模型结果的变化顺序进入：

1. [inspect_trusted_generation.py](../../source/demos/rag_retrieval_lab/inspect_trusted_generation.py)：看三组 Context 怎样进入同一个真实生成入口；
2. [risk_review_v5.yaml](../../source/packages/llm_core/prompts/review/risk_review_v5.yaml)：看 Requirement、Evidence、History 和 allowlist 怎样被明确分开；
3. [review.py](../../source/packages/llm_core/schemas/review.py)：看 `ReviewRiskList`、risk 与 citation 的结构契约；
4. [service.py](../../source/packages/llm_core/client/service.py)：看 response format 怎样进入真实调用，返回后怎样解析；
5. [generation/service.py](../../source/packages/rag_core/generation/service.py)：看状态、逐项 membership check 与诊断报告；
6. [test_trusted_generation.py](../../source/packages/rag_core/tests/test_trusted_generation.py)：用测试反查每个不变量。

读 `generation/service.py` 时，可以用这条主线：

```text
BuiltContext
→ 提取 citation_source_ids
→ 渲染 Prompt v5
→ chat_structured
→ parse result
→ ReviewRisk[]
→ _check_claims
→ _generation_status
→ TrustedGenerationReport
```

其中 Prompt 和模型负责“尝试遵守”，应用代码负责“结构解析、集合检查和状态分类”。确定性边界不能只依赖模型自觉。

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

这些是需求评审助手的证据责任和版本边界，必须由应用契约、代码与后续 Eval 共同建立。

## 到第 16 步，固定 RAG 学到了什么程度

完成第 7–16 步，并亲自运行实验、解释报告、定位边界和完成修改题后，可以称为：

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

但“第 16 步读完”不等于“RAG 全部掌握”。还需要：

- V0 后续产品步骤：API、Web 工作台、固定对照、最小评估和项目验收；
- V1：Citation 内容支持性、来源定位、证据充分性、Refusal、补充问题和知识版本；
- V2：Retrieval / Generation / Citation Eval、回归、bad case 与反馈闭环；
- V3：需要动态决策时，再进入 Query Rewrite、Source Routing 和单 Agent RAG。

判断自己是否“掌握”，不看读了多少篇，而看能否解释、验证、修改、调试和取舍这条链。

## 亲手完成一个单变量修改

不要新增“候选声明率”，因为单个比率容易让初学者误读成引用质量。更适合本节机制的练习是增加一个确定性测试：

> 使用同一个合法候选 ID，故意让 `excerpt` 与来源内容不一致，观察当前状态仍为 `succeeded`，并用测试名称明确记录“V0 不验证 excerpt”。

约束如下：

1. `BuiltContext` 和 `citation_candidate_ids` 不变；
2. risk 的 `source_id` 使用真实候选 `chunk-api`；
3. `excerpt` 写成来源中不存在的文本；
4. 断言结构解析成功；
5. 断言 claim status 是 `candidate`；
6. 断言报告边界仍是 `candidate_membership_only_not_support_validation`；
7. 测试名称和注释不能称它为“引用正确”。

在动手前先预测：

```text
status = succeeded
candidate_claim_count = 1
unknown_source_count = 0
```

若结果符合预测，说明你已经理解当前代码检查的是 ID 集合，不是 excerpt 和支持关系。这不是要求你现在实现 V1，而是让未实现边界变成自己亲手验证过的事实。

如果你决定继续实现 excerpt 校验，任务范围已经从“学习 V0 边界”扩大到 V1 证据校验，不能顺手混进本节练习。

## 学完后的自检

先不看正文，回答：

- 为什么 JSON Schema 通过后，`source_id` 仍可能是模型编造的？
- Source、Retrieved Candidate、Citation Candidate、Claimed Citation 和 Validated Citation 分别是什么？
- `candidate` 状态具体证明了什么，又没有证明什么？
- 为什么 Requirement 内部缺失风险可以没有 citation？
- 为什么无 citation 风险仍可能让当前 V0 状态成为 `succeeded`？
- 空 Evidence 时，为什么不能简单理解成“模型必须什么都不说”？
- 合法 source ID 搭配虚假 excerpt 时，当前代码为什么仍可能通过？
- `unknown_citation_source` 为什么不能自动按标题匹配一个来源？
- `LLMError`、`structured_output_invalid` 和 `unknown_citation_source` 分别发生在哪一层？
- normal noise 对照能观察什么，不能证明什么？

再做一次完整追踪：从一条 `Citation Candidate` 开始，在渲染后的 allowlist 中找到它，运行真实模型，找到对应 Claimed Citation 和 `CitationClaimCheck`，最后说出它距离 Validated Citation 还缺哪一步。

如果你能完成这条追踪，并且不会把 `succeeded` 解释成“引用内容已验证”，就完成了第 16 步的核心目标。

回到 [标准学习路径](../learning-path.md)，继续把这条固定 RAG 核心机制交付为 API、Web 工作台和可比较的 V0 产品基线。
