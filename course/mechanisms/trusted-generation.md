# 可信生成：从 Citation Candidate 到可检查的来源声明

> 这是一篇机制篇。第 15 步已经构造出带 Citation Candidate 的 `BuiltContext`；本节让真实模型基于它生成结构化评审，并在应用侧检查模型声明的 source ID 是否属于本轮候选。读完后，你应该能准确说明 V0 检查了什么、还没有验证什么。本文不提前实现 Citation 支持性、证据充分性或 Refusal 闭环。

## 模型写出一个来源编号，不代表引用可信

假设模型返回：

```json
{
  "title": "售后接口缺少来源渠道",
  "category": "api",
  "level": "high",
  "rationale": "新入口需要传递 source_channel。",
  "citations": [{"source_id": "API-AFTER-SALE-V2"}]
}
```

这个 JSON 通过 Schema，只能证明字段和枚举合法。至少还有三个问题：

1. `API-AFTER-SALE-V2` 是否真的出现在本轮模型 Context 中？
2. 这个 source 是否允许作为当前证据，而不是历史材料或被评审的 PRD？
3. source 的内容是否真的支持“缺少来源渠道”这条结论？

V0 只解决前两个问题形成的最小边界：模型声明的 `source_id` 必须来自本轮 `Citation Candidate`。第 3 个问题需要检查引用内容与结论的支持关系，进入 V1。

因此本节所说的“可信”不是“答案已经为真”，而是生成过程的输入、结构和来源声明开始可检查、可拒绝、可追踪。

## 五个对象不能混成一个 Citation

从资料到已验证引用，要经过一条逐步收紧的链：

```text
Source
→ Retrieved Candidate
→ Citation Candidate
→ Claimed Citation
→ Validated Citation（V1）
```

| 对象 | 当前含义 | 它还不能证明什么 |
| --- | --- | --- |
| Source | 系统中的一条资料 | 本轮是否相关、是否可见 |
| Retrieved Candidate | Retriever 找到并排名的 Chunk | 是否进入模型 Context |
| Citation Candidate | 本轮 included Evidence 中允许引用的 source | 是否真正支持某条结论 |
| Claimed Citation | 模型输出中声明的 source ID | ID 是否真实、内容是否支持 |
| Validated Citation | 已检查 ID、位置和支持关系的引用 | V0 尚未实现 |

最容易犯的错误，是把 Claimed Citation 直接展示成“已验证依据”。模型能生成任何字符串；即使开启 Structured Output，`source_id` 仍然只是一个字符串字段。

## 这一节怎样接上前面的完整数据流

前面每一步都保留的数据，在这里终于进入一次真实生成：

```text
第 8–9 步：资料 → 带 locator 的 Chunk
→ 第 11–14 步：lexical + dense + RRF → RetrievalResult
→ 第 15 步：ContextSource → BuiltContext + Citation Candidate
→ 第 16 步：Prompt v5 + Structured Output → ReviewRisk[]
→ 本地 Citation Candidate membership check
→ TrustedGenerationResult + TrustedGenerationReport
```

第 16 步没有再写一套 Provider、Prompt renderer 或 Schema parser：

- `llm_core.LLMClient.chat_structured` 负责真实模型调用。
- `review.risk_review@5.0.0` 负责生成任务协议。
- `ReviewRiskList` 负责输出结构。
- `BuiltContext` 提供 Requirement、Evidence、History 与候选 source ID。
- `rag_core.generate_trusted_review` 负责编排并检查声明边界。

这仍是一条固定 RAG Pipeline，不是 Agent。模型没有自主决定是否调用 Retriever，也没有工具循环。

## Prompt 必须明确告诉模型哪些 ID 可以使用

第 15 步的 Evidence block 已经带 source ID，但只靠模型“自己看懂”不够。Prompt v5 额外列出：

```text
## Allowed Citation Source IDs
- chunk-a
- chunk-b
```

并规定：

- citation 的 `source_id` 只能逐字选自该列表。
- Requirement 是被评审对象，不能成为 citation。
- History 只用于提醒检查方向，不能成为 citation。
- 列表为空时，所有 citations 必须为空。
- Requirement 内部缺失或矛盾仍可形成无 citation 的风险，但不能伪装成外部资料事实。

最后一条很重要。风险没有 citation 不一定就是错误：例如 Requirement 同一句话前后矛盾，模型可以直接指出需求内部问题。反过来，如果模型声称“接口规定必须传 `source_channel`”，这属于外部规则，就应声明对应 Evidence source。

Prompt 约束只是第一道防线。模型仍可能忽略，所以应用必须在返回后再做本地检查。

## Structured Output 负责形状，业务检查负责边界

真实调用使用 `ReviewRiskList`：

```text
risks[]
  title
  category
  level
  rationale
  citations[]
    source_id
    excerpt?
```

`json_schema` 模式在供应商支持时能更强地约束字段形状；`json_object` 也仍需应用侧解析。无论使用哪种模式，Schema 都无法知道某次调用的动态候选列表。

原因很简单：Pydantic Schema 在调用前定义 `source_id: str`，而 `chunk-a`、`chunk-b` 是 Retriever 在本轮运行时才产生的。把每轮 ID 动态编进 JSON Schema 并不是这里的通用契约；当前实现选择在解析后做集合成员检查：

```python
claimed.source_id in context.report.citation_source_ids
```

两层校验各自负责：

| 层 | 检查 | 失败表现 |
| --- | --- | --- |
| Structured parse | JSON、字段、枚举、根结构 | `structured_output_invalid` |
| Citation Candidate check | 每个 claimed source ID 是否在本轮 allowlist | `unknown_citation_source` |

解析失败时没有可用 `ReviewRisk[]`，不能继续把原始字符串当成成功结果。出现未知 source ID 时，结构虽然合法，整个生成结果仍不是成功状态。

## 本地检查具体留下什么报告

公共入口：

```python
result = generate_trusted_review(
    built_context,
    config_ref="chat.structured_chat",
    structured_mode="json_schema",
)
```

`TrustedGenerationResult` 同时保留结构化 risks、真实模型响应和报告。`TrustedGenerationReport` 记录：

- Prompt、模型配置和 structured mode。
- 本轮 `citation_candidate_ids`。
- 当前是否存在 Citation Candidate。
- 结构化解析是否成功及失败阶段。
- risk 数量与未声明 citation 的 risk 数量。
- claimed citation 总数。
- 属于候选的声明数与未知来源数。
- 每个 risk、每个 citation 的逐项检查结果。
- 明确的检查边界：`candidate_membership_only_not_support_validation`。

最后这个字段不是多余说明。它阻止调用者看到 `candidate_claim_count=3` 就误写成“3 条引用已验证”。正确表述只能是“3 个声明的 source ID 来自本轮 Citation Candidate”。

## 三种生成状态怎样理解

| `GenerationStatus` | 已知事实 | 应用能否当成功结果 |
| --- | --- | --- |
| `succeeded` | 结构合法，所有 claimed source ID 都在候选列表 | 可以进入 V0 展示，但必须标明仍是 Citation Candidate 边界 |
| `structured_output_invalid` | 模型输出没有通过 JSON/Schema 解析 | 不可以；查看 parse stage/message |
| `unknown_citation_source` | 结构合法，但至少一个 source ID 不属于本轮候选 | 不可以；不能展示成可点击可信来源 |

真实 HTTP 调用还可能因 key、限流、超时或模型不支持 structured mode 抛出 `LLMError`。这些是依赖失败，不应转成空 risks 或 requirement-only 假成功。

## 空证据不等于模型必须沉默，也不等于已有事实依据

`EvidenceState.NO_CITATION_CANDIDATES` 表示本轮 Context 没有可引用外部证据。它可能来自：

- Retriever 最终无候选。
- 候选全部因 Context budget 或策略被丢弃。
- 只有 History，没有当前 Evidence。

V0 会把这一状态传进 Prompt，并要求 citations 为空。模型仍可指出 Requirement 自身明确存在的缺失或矛盾，但不能把常识或历史经验写成“当前接口规定”。

例如 Requirement 写了“失败时区分网络错误和业务拒绝”，却没有定义 UI 映射。模型可以说“需求未定义两类失败的交互表现”；这依据来自 Requirement 自身，不需要外部 citation。

但模型不能在空 Evidence 时说“接口错误码是 `CLIENT_PARAM_INVALID`”，因为该事实不在 Requirement 中。

完整的“证据不足时应该拒绝、追问什么、哪些风险允许输出”需要更细的业务策略与 Schema，属于 V1。V0 只让空证据和无引用风险保持可见，不假装已经完成 Refusal。

## 为什么还要观察正常无关证据

只比较“有正确证据”和“完全没证据”，很难看出模型是否单纯因为看到任意 Evidence 就变得更肯定。真实实验增加一份正常但业务无关的营销入口规则：

```text
同一个售后 Requirement
├─ rag_evidence：真实 Retriever 找到的售后规则
├─ normal_noise：合法格式但只描述营销活动入口的证据
└─ empty_evidence：没有 Citation Candidate
```

三组都调用真实模型，没有 mock 输出。观察重点不是哪组 risk 数量最多，而是：

- `rag_evidence` 是否更常声明真实候选 ID。
- `normal_noise` 是否错误把营销规则引用到售后风险。
- `empty_evidence` 是否保持 citations 为空。
- 模型是否声明了 allowlist 之外的 source ID。
- 相同 Requirement 下，外部事实是否随 Evidence 内容合理变化。

正常噪声是生成边界探针，不是检索质量结论。它由 fixture 明确标记为不同业务域；真实 RAG 主路径仍使用第 14 步的 Metadata Filter，不会故意把它作为售后候选。

## 真实实验的运行链

入口是 `source/demos/rag_retrieval_lab/inspect_trusted_generation.py`。它首先运行真实 PostgreSQL、真实 Embedding 和固定 Retriever，构造 `rag_evidence`；随后为同一 Requirement 构造 noise 与 empty 对照，最后逐组调用真实 chat 模型。

默认使用 `json_schema`。若所选真实 Provider 只支持 JSON object，可以显式切换并记录 structured mode；不能在失败后静默换模式，因为这会改变实验条件。

输出首先列出每组：

```text
evidence state
risk count
risk without citation count
candidate claim count
unknown source count
generation status
```

verbose 模式再展开每条风险与声明检查。JSON Lines 适合保存本轮真实观察。完整命令、配置和输出解释见 [rag_retrieval_lab README](../../source/demos/rag_retrieval_lab/README.md)。

离线测试使用构造好的模型响应，只验证 Schema 解析后的集合检查与状态分类。它不能证明模型会遵守 Prompt，也不能证明 source 内容支持结论；这些必须从真实模型实验和 V1/V2 评估中获得。

## 一个完整 bad case 应该怎样定位

表现：模型输出一条接口风险，引用 `API-V2`，界面却找不到该来源。

按顺序检查：

1. `RetrievalReport`：对应 Chunk 是否进入最终候选？
2. `ContextBuildReport`：它是否 included，是否成为 Citation Candidate？
3. 最终 Prompt：Allowed Citation Source IDs 是否真的含 `API-V2`？
4. Structured parse：`source_id` 是否被正确解析？
5. `TrustedGenerationReport.claim_checks`：它是 `candidate` 还是 `unknown_source`？

如果第 2 步的真实 ID 是一个稳定 Chunk hash，而模型写了自己概括的 `API-V2`，这就是未知来源声明。修复可以是增强 Prompt 的 ID 复制约束、改善 Evidence 格式或更换模型，但应用侧仍必须保持拒绝状态，不能用相似标题自动猜中某条来源。

若 source ID 合法，但 excerpt 根本不在 source 内容里，V0 membership check 仍会通过。这正是本节明确留下的失败边界，不应在报告里伪装成已解决。

## V0 到这里到底完成了什么

完成本节后，固定 RAG 的核心运行链已经贯通：

```text
外部资料
→ 可追踪 Chunk
→ lexical + dense + RRF
→ 固定 RetrievalResult
→ 受预算控制的 BuiltContext
→ 真实结构化生成
→ Citation Candidate membership report
```

你可以解释资料怎样进入模型、候选在哪里消失、模型声明了哪些来源，以及声明是否来自本轮候选。这是固定 RAG 核心机制入门的重要完成点。

但还不能说“RAG 都学完了”或“已经掌握生产级 RAG”，因为还缺：

- V1：Citation 内容支持性、证据充分性、Refusal、追问和知识版本治理。
- V2：固定数据集、Retrieval/Generation/Citation Eval、bad case 闭环和 Reranker 准入。
- V0 项目：真实 API、Web 工作台、完整异常流和版本验收。

学习路径中“读完第 16 步”与“完成 V0 固定 RAG 项目掌握”是两个不同门槛。

## 亲手完成一次小改动

给 `TrustedGenerationReport` 的展示层增加“候选声明率”：

```text
candidate_claim_count / claimed_citation_count
```

要求：

1. 没有 citation claim 时显示 `not_applicable`，不要除以零，也不要显示虚假的 100%。
2. 有未知 source 时同时保留原始数量和逐项检查。
3. 文案使用“候选声明率”，不能叫“引用正确率”或“证据支持率”。
4. 单元测试只证明计算和命名，不声称模型质量提高。

## 学完后的自检

不看正文，尝试回答：

- 为什么通过 `ReviewRiskList` Schema 仍可能出现假 source ID？
- Citation Candidate 与 Claimed Citation 有什么区别？
- source ID 属于候选列表后，为什么还不能称为 Validated Citation？
- 一条 Requirement 内部缺失风险没有 citation，为什么不一定是错误？
- 空 Evidence 时模型和应用分别应该保持哪些边界？
- `unknown_citation_source` 为什么不能自动按标题猜一个最相似来源？

如果你还能运行三组真实对照，指出每个 source claim 是否属于本轮候选，并明确说出实验没有验证内容支持关系，就完成了第 16 节目标。请回到 [标准学习路径](../learning-path.md) 查看固定 RAG 入门之后的产品与评估路线。
