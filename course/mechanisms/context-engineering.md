# Context Engineering：从检索候选到模型真正看到的证据

> 这是一篇机制篇。第 14 步已经返回可诊断的 `RetrievalResult`；本节继续回答：这些候选怎样在 token 预算内进入模型输入，而且仍能回到原文位置？读完后，你应该能区分“没检索到”和“检索到了但没进 Context”。本文不重新实现 Retriever，也不生成最终评审结果。

## 正确 Chunk 找到了，模型却仍然没提到它

假设第 14 步的报告明确显示：接口规则 `source_channel` 已经排进最终候选。你调用模型后，它却只谈订单状态，没有谈接口字段。

这时不能再说“检索没找到”。`RetrievalResult` 已经证明候选存在，接下来还发生了另一轮选择：

```text
RetrievalResult.candidates
→ 映射成带来源的 ContextSource
→ 去重与分区
→ 按 token budget 选择或压缩
→ BuiltContext
→ Prompt messages
```

接口规则可能在这条链路里因重复内容、证据预算不足或压缩而消失。修复方向也和 Retriever 完全不同。

所以先记住两个问题：

- `RetrievalReport` 回答“Retriever 找到了什么，候选在哪里被过滤或截断”。
- `ContextBuildReport` 回答“在这些最终候选中，模型这一轮实际看到了什么”。

它们不能合并成一个模糊的 `debug_info`。前者属于检索，后者属于模型输入装配。

## Context 不等于知识库，也不等于 Prompt 文案

初学时常把三个东西混在一起：

| 对象 | 它是什么 | 当前项目中的例子 |
| --- | --- | --- |
| 知识库 | 系统可能搜索到的外部资料全集 | 订单规则、售后接口文档 |
| Context | 本轮模型调用实际获得的任务、证据和辅助材料 | 当前 PRD + 被选中的 3 个 Chunk + 一条历史摘要 |
| Prompt | 告诉模型如何处理 Context 的任务协议 | “识别研发风险，只引用给出的 source id” |

知识库很大，不可能也不应该整库塞给模型。Prompt 写得再严格，也无法补回 Context Builder 已经丢掉的接口规则。

Context Engineering 就是应用在调用模型之前，对输入材料进行身份保留、分类、去重、预算和诊断的过程。它不是让模型“自己挑重要内容”，而是应用先明确本轮允许模型看什么。

## 先把第 9–14 步的来源链带过来

第 9 步的 Chunk 不只保存文本，还保存 `chunk_id`、文档版本和 `source_spans`。第 11、12 步分别给候选增加原生排名，第 13 步保留两路贡献，第 14 步输出最终融合候选。

如果第 15 步只执行：

```python
ContextSource(content=candidate.content)
```

前面积累的来源信息会在最后一米全部丢失。模型即使引用了这段文本，应用也不知道应该打开哪份文档的哪一页或哪几行。

本项目因此增加一个很薄的 RAG 适配层：

```text
RRFCandidate
  chunk_id
  document_id / version
  source_spans
  fusion_rank / rrf_score
  route ranks / native scores
  evidence_eligibility
        ↓
ContextSource
  source_id = chunk_id
  content
  source_type
  title + locator
  retrieval metadata
```

公共入口是 `rag_core.retrieval_result_to_context_sources`。它没有另写 Context Builder，只负责把两个已有契约接起来。

### 为什么 `source_id` 直接使用 `chunk_id`

`chunk_id` 是前面步骤形成的稳定候选身份。若适配时另造 `SOURCE-1`、`SOURCE-2`，同一 Chunk 在不同运行中可能换编号，日志、引用候选和来源定位就难以关联。

稳定 ID 不是为了让人容易背，而是让以下链条能使用同一个键：

```text
数据库 Chunk
↔ lexical / dense 候选
↔ RRF 候选
↔ ContextSource
↔ Citation Candidate
```

额外的历史材料也不能复用已有 Chunk ID。适配器会拒绝这种冲突，而不是靠优先级静默覆盖其中一条。

### 没有来源位置的候选不能悄悄进入

当前 RAG 适配器要求候选至少有一个 `source_span`。若缺失，它直接返回错误：这说明检索结果没有完整承接第 9 步的来源契约。

把 locator 设为“未知”后继续生成看起来更顺畅，但后续 Citation 点击、bad case 复盘和文档更新都会失去依据。V0 宁可让这类契约错误可见。

## 检索排名只决定装配顺序，不代表来源更权威

适配后的 `ContextSource.metadata` 保留：

- `fusion_rank` 与 `rrf_score`
- 每一路 `route_rank`
- 原生分数名称、数值和方向
- 文档 ID、版本、来源角色与证据资格
- 原文 locator
- `retriever_config_ref`

这些字段用于诊断“为什么先选了这条候选”。它们不证明候选内容是真的，也不表示排第 1 的资料在业务上比排第 2 的资料更权威。

适配器用融合排名保持候选的预算选择顺序，但把 `ContextSource.score` 留空，避免制造一个通用“可信度分数”。事实优先级要由来源治理、证据资格和后续校验决定，不能从 cosine distance 或 RRF 分数推导。

## 证据、历史和不可用材料要分开

Retriever 可以返回不同资格的材料；Context 不能把它们都格式化成 Evidence：

| `evidence_eligibility` | Context 处理 | 是否成为 Citation Candidate |
| --- | --- | --- |
| `current_evidence` | 映射为 `evidence` | 可以，前提是最终 included |
| `historical_context` | 映射为 `history_review` | 不可以，只能辅助发现风险方向 |
| `ineligible` | 明确排除 | 不可以，也不进入模型输入 |

历史评审“以前发生过重复提交”可以提醒我们检查重复申请，但它不能证明当前 v2 接口一定缺少拦截。若把历史材料也列成 Citation Candidate，用户会误以为当前结论已有现行规则支持。

这也是为什么当前 PRD 本身是 Requirement，而不是 Citation Candidate。它是被评审对象，不是证明自身正确的外部证据。

## 唯一 Context Builder 怎样工作

RAG 适配完成后，所有选择仍交给已有的 `llm_core.context.build_review_context`：

```python
result = build_rag_review_context(
    requirement_text=requirement,
    retrieval_result=retrieval_result,
    additional_sources=(history_source,),
    policy=get_context_policy("evidence_first"),
)
```

`build_rag_review_context` 内部只做两步：

1. 把检索候选映射成 `ContextSource`，检查身份和 locator。
2. 调用 `build_review_context` 完成已有的去重、分区、预算和压缩。

这样静态材料、RAG 候选和以后 Agent 产生的辅助摘要，都遵守同一套 Context 契约，不会为每种来源复制一个 Builder。

### 候选池不等于最终 Context

Builder 收到的 sources 只是候选池。它会把材料放进不同分区：

```text
Requirement      当前被评审的需求
Evidence         当前可引用证据
History Summary  历史辅助材料
Agent Summary    中间过程，不是事实来源
Other Context    兜底材料
```

然后根据 policy 依次做来源类型过滤、ID/内容去重、排序、分区预算和总预算控制。最终只有 `included_sources` 出现在 Prompt 中。

### 为什么既要总预算，又要分区预算

只有一个总预算时，某类长材料可能占满上下文。例如一份很长的历史评审先进入后，当前接口文档反而没有空间。

分区预算让应用可以表达：风险评审优先给 Evidence 空间，History 只保留少量。它不是唯一正确算法，但能让取舍变得可解释：

```text
token_budget = 整个 BuiltContext 上限
section_budgets["evidence"] = 证据分区上限
section_budgets["history"] = 历史分区上限
```

`evidence_first` 适合观察正常证据装配；`tight_budget` 则故意缩小预算，用来观察压缩和丢弃。策略数值是实验配置，不是永远适合产品的标准。

### 去重为什么也可能丢掉正确候选

Builder 会处理两种重复：

- 同一个 `source_id` 出现多次：保留排序更高的版本，报告 `duplicate_source_id`。
- 不同 ID 的规范化内容相同：保留排序更高的一条，报告 `duplicate_content`。

去重能节省预算，但也要保留原因。若两份内容看似相同、来源版本却不同，简单内容去重可能隐藏版本差异；这属于后续知识治理要进一步约束的边界。

### 压缩不是把末尾直接切掉

当前 `llm_core.context` 使用确定性的 extractive compression：从原文选择更贴近 Requirement 关键词的句子，并保留原 source ID。报告记录压缩前后的 token 估算。

这种方法容易复现，也不会让另一个模型重写事实，但它仍可能漏掉没有命中关键词的关键否定条件。因此压缩后要查看模型实际收到的文本，不能只看到 source ID 仍在就认为证据完整。

## 用两份报告定位同一个 bad case

假设模型仍然漏掉 `source_channel`，从前往后检查：

### 1. 看 RetrievalReport

- `visible_chunk_count` 是否大于 0？
- 接口规则是否成为 route candidate？
- 是否通过 route threshold？
- 是否进入 RRF 和 `final_top_k`？

如果没有进入 `RetrievalResult.candidates`，问题仍在第 14 步以前。

### 2. 看 Retrieval → ContextSource mapping

- `chunk_id` 是否成为相同的 `source_id`？
- 是否保留 document version 和 locator？
- `evidence_eligibility` 是否把它映射成当前 evidence？
- 是否因 `ineligible` 被明确排除？

这里出错说明两个 package 的契约没有接好。

### 3. 看 ContextBuildReport

- source 是否在 `included_source_ids`？
- 若不在，`dropped_sources.reason` 是预算、去重还是策略排除？
- 若被压缩，`compressed_sources` 显示了什么？
- 它是否出现在 `citation_source_ids`？

若检索已找到、mapping 正常，但 source 因 `token_budget_exceeded` 被丢弃，就应调整 Context 策略或候选数量，而不是重新调 Embedding。

### 4. 最后看 Prompt 和模型

source 已 included 且关键句确实在最终 Evidence block 中，模型仍忽略它，才进入 Prompt 约束、模型行为和生成评估层。

这个顺序能把一句“RAG 没效果”拆成可行动的问题。

## 真实实验怎样承接前面的功能

主实验入口是 `source/demos/rag_retrieval_lab/inspect_rag_context.py`。它不是从静态候选开始，而是复用前面的真实链路：

```text
order_rules.md
→ Loader + Chunker
→ PostgreSQL FTS + pgvector
→ FixedHybridRetriever
→ RetrievalResult
→ RAG Context adapter
→ llm_core Context Builder
→ BuiltContext + ContextBuildReport
```

它使用 `context_cases.json` 中同一个“订单详情页新增申请售后入口”作为 Requirement，也直接用该 Requirement 做检索 query；V0 此处不提前引入 Query Rewrite。

默认对同一个 `RetrievalResult` 分别运行 `evidence_first` 和 `tight_budget`。这样实验只改变 Context policy，Retriever 候选保持不变。你可以观察：

- 哪些候选已被检索并映射。
- 不同预算下哪些 source 被 included、compressed 或 dropped。
- 历史评审是否进入 History 而没有进入 Citation Candidate。
- 每条检索来源能否回到 Markdown 行号和标题路径。

再用 `--without-history` 做一次单变量对照，确认历史变化只影响 Context，不应改写同一轮 RetrievalReport。完整命令和输出解释见 [rag_retrieval_lab README](../../source/demos/rag_retrieval_lab/README.md)。

原有 [llm_context_lab](../../source/demos/llm_context_lab/README.md) 的静态材料实验仍有价值：它能在不调用数据库和 Embedding 时稳定观察各种 policy、去重和压缩。但静态实验只证明 Context Builder 的确定性行为，不证明 RAG 链路已经接通，也不证明真实检索质量。

## 代码中的关键不变量

这一步的确定性测试重点不是“模型回答更好”，而是守住数据边界：

1. 检索 `chunk_id` 与 Context `source_id` 不变。
2. 文档版本、locator、路由排名和原生分数没有在适配时丢失。
3. 原生检索分数只进入诊断 metadata，不伪装成来源权威分。
4. 缺少 `source_spans` 的候选不能进入可追踪 Context。
5. `historical_context` 可以辅助模型，但不能成为 Citation Candidate。
6. `ineligible` 候选明确排除。
7. additional source 不能用相同 ID 覆盖检索 Chunk。
8. 每条 mapped source 最终都能在 included 或 dropped 中找到去向。

这些测试可以离线运行。真实 PostgreSQL 和 Embedding 实验仍需真实配置；缺少 key 或数据库失败时不会回退到假候选。

## 这一层没有完成什么

现在模型输入已经可追踪、可预算，但不要把它误称为“可信 RAG 已完成”：

- Citation Candidate 只表示 source 在本轮 Evidence 中可被引用。
- 它不证明 source 真的支持某条模型结论。
- `no_evidence_included` 只是上下文状态，还没有形成完整 Refusal 策略。
- extractive compression 不保证保留全部事实。
- 当前 policy 尚未通过固定评估集证明最优。

下一阶段会把 `BuiltContext` 交给真实模型生成结构化结果，并检查模型声明的 source ID 是否属于本轮 Citation Candidate。Citation 支持性、证据充分性和 Refusal 闭环仍属于 V1。

## 亲手完成一次小改动

给真实实验增加一个 `--policies full_context,evidence_first` 对照，保持 Requirement、Retriever 配置和 `RetrievalResult` 完全不变。记录：

1. 两次 `mapped_source_ids` 是否相同。
2. 两次 included / dropped / compressed 有何差异。
3. History 是否错误进入 Citation Candidate。
4. 如果最终 Context 不同，能否只用 `ContextBuildReport` 解释原因。

若你改了 `candidate_k` 或检索阈值，这次对照就不再只研究 Context；请恢复相同 Retriever 配置再比较。

## 学完后的自检

不看正文，尝试回答：

- 为什么“Retriever 找到”不等于“模型看到”？
- `RetrievalReport` 与 `ContextBuildReport` 分别负责哪段链路？
- 为什么 Context `source_id` 应继续使用稳定 `chunk_id`？
- 为什么要保留 locator、route rank 和原生分数，却不能把它们当事实权威性？
- 历史评审为什么可以进入 Context，却不能成为 Citation Candidate？
- 正确候选因预算丢失时，为什么不该先调 Embedding？

如果你还能运行真实实验，从 `RetrievalResult` 追踪一条 Chunk 到 Evidence block，并解释另一条 Chunk 为什么只出现在 dropped report 中，就完成了本节目标。请回到 [标准学习路径](../learning-path.md) 继续按主线学习。
