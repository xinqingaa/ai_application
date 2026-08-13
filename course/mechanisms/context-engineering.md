# Context Engineering：Retriever 找到了，为什么模型仍然看不到

> 这是一篇机制篇。第 14 步已经把 Lexical、Dense、RRF、过滤和截断收进一个可诊断的 `RetrievalResult`。本节只向前推进一步：把检索候选变成这一轮模型真正能看到、能定位、能引用的 `BuiltContext`。
>
> 学完后，你应该能从一条检索候选一路追到最终 Evidence，解释它为什么被保留、压缩或丢弃。这里还不会生成最终评审结论；真实生成与引用检查留到第 16 步。

## 先从一个容易误判的问题开始

我们仍然评审同一个需求：

```text
订单详情页新增“申请售后”入口。
```

第 14 步的 `RetrievalReport` 已经告诉我们：订单状态规则和售后接口规则都进入了最终候选，接口规则还明确写着需要传 `source_channel`。可是模型的回答只谈了订单状态，完全没有提这个接口字段。

如果只看最终回答，我们很容易断言“检索没找到接口规则”。但检索之后还有一条输入装配链：

```text
RetrievalResult.candidates
        ↓ 映射并保留来源身份
ContextSource 候选池
        ↓ 类型过滤、去重、排序
分区候选
        ↓ 总预算、分区预算、压缩
BuiltContext
        ↓ 和 Prompt 模板组合
最终 messages
        ↓
模型
```

接口规则可能在 `ContextSource` 映射时被排除，也可能因 Evidence 分区预算不足被丢弃，还可能在压缩时丢失关键句。

所以从本节开始，需要把两个问题分开：

1. Retriever 找到了什么？
2. 模型这一轮实际看到了什么？

第一个问题看 `RetrievalReport`，第二个问题看 `BuiltContext` 与 `ContextBuildReport`。两份报告相互衔接，但不能混成一个模糊的 `debug_info`。

## 先区分四个容易混淆的对象

### 知识库：系统可能检索到的资料全集

知识库里可以有业务规则、接口文档、客户端说明和历史评审。它通常远大于单次模型调用能容纳的内容。

知识库里“有”一条规则，不表示本次检索找到了它。

### Retrieval Candidates：Retriever 为本次问题选出的候选

第 14 步输出的 `RetrievalResult.candidates` 是知识库的一个小子集。每个候选带着：

- 稳定 `chunk_id`；
- 文档 ID 与版本；
- `source_spans` 原文位置；
- Lexical / Dense 路由名次和原生分数；
- RRF 融合名次；
- 证据资格。

候选“被检索到”，仍不表示它一定进入模型输入。

### BuiltContext：应用允许模型在这一轮看到的材料

`BuiltContext` 不只包含检索证据。它还可以包含当前 Requirement、当前可引用 Evidence、历史辅助材料、Agent 中间摘要和其他上下文。

它已经经过类型过滤、去重、排序、分区预算和压缩，是一次确定的输入装配结果。

### Prompt：模型应该怎样处理这些材料

Prompt 会说明任务、输出格式和约束，例如：

```text
识别研发风险。
只能引用本轮给出的 source_id。
证据不足时不要编造确定结论。
```

Prompt 决定“怎样做”，Context 决定“拿什么做”。Prompt 写得再严格，也补不回 Builder 已经丢掉的接口规则。

> 知识库不是 Context，检索候选也不是 Context；`BuiltContext` 才是模型这一轮实际拿到的材料集合。

## 第 9–14 步积累的信息不能在最后一米丢失

第 9 步切 Chunk 时，我们没有只保存文本，还保留了 `chunk_id`、文档版本和 `source_spans`。第 11、12 步加入两路原生检索信息，第 13 步保留 RRF 贡献，第 14 步记录过滤、阈值和最终截断。

如果现在只写：

```python
ContextSource(content=candidate.content)
```

前面建立的可追踪链会在调用模型前断掉。模型即使引用了这段话，应用也无法知道它来自哪份文档、哪个版本、哪几行。

当前项目用一个很薄的适配层连接两个已有契约：

```text
rag_core.RRFCandidate
  chunk_id
  document_id / document_version
  source_spans
  fusion_rank / rrf_score
  route ranks / native scores
  evidence_eligibility
            ↓
rag_core.retrieval_result_to_context_sources
            ↓
llm_core.ContextSource
  source_id = chunk_id
  content
  source_type
  title
  priority
  metadata
```

公共入口是：

```python
from rag_core import retrieval_result_to_context_sources

mapping = retrieval_result_to_context_sources(retrieval_result)
```

它不重新实现 Context Builder，只负责把 RAG 候选转换成 `llm_core` 能理解的材料，并记录每条候选的映射决定。

## 适配器不是“复制一段文本”

### `source_id` 为什么继续使用 `chunk_id`

`chunk_id` 是从 Chunk、数据库、两路检索到 RRF 一直沿用的稳定身份。适配时若临时改成 `SOURCE-1`、`SOURCE-2`，同一个 Chunk 在不同运行中可能换编号，日志和引用也无法关联。

当前链条因此使用同一个键：

```text
数据库 Chunk
↔ Lexical / Dense candidate
↔ RRF candidate
↔ ContextSource
↔ Citation Candidate
```

额外加入的历史材料也不能复用检索 Chunk 的 ID。`build_rag_review_context` 会直接拒绝这种冲突，避免其中一条材料被静默覆盖。

### 没有 locator，为什么直接报错

当前适配器要求每条检索候选至少有一个 `source_span`。若候选只有文本却没有原文位置，它会抛出错误，而不是用“位置未知”继续运行。

这不是故意让流程变脆，而是在守住第 9 步建立的来源契约：

```text
source_id 只能回答“是哪条材料”
locator 才能回答“原文在哪里”
```

缺少 locator 时，后续点击 Citation、复盘 bad case、核对文档版本都会失去依据。V0 宁可暴露这类契约错误，也不伪装成可追踪证据。

### 检索信息保留在哪里

适配后的 `ContextSource.metadata` 会保留：

- `document_id`、`document_version`；
- 来源角色与证据资格；
- 原文 locator；
- `fusion_rank` 与 `rrf_score`；
- 每一路 `route_rank`；
- 原生分数名称、数值和方向；
- `retriever_config_ref`。

这些字段让我们能解释“这条候选为何排在前面”，但不能证明“这条内容一定正确”。

### 为什么没有把 RRF 分数塞进通用 `score`

`ContextSource` 有一个可选的 `score`，但 RAG 适配器不会把 RRF 分数冒充成统一可信度，而是把它留在诊断 metadata 中。

```text
PostgreSQL ts_rank       → 词面匹配强弱
cosine distance          → 向量空间距离
RRF score                → 多路名次融合后的排序信号
来源权威性                → 资料是否适合支持当前结论
```

前三者都不是最后一个。检索排名可以影响预算选择顺序，却不能自动决定事实权威性。

## 证据、历史和不可用材料必须分开

Retriever 返回的材料不一定都有相同资格。适配器会根据 `evidence_eligibility` 做明确决定：

| Retrieval 资格 | 映射结果 | 能否进入 Citation Candidate |
| --- | --- | --- |
| `current_evidence` | 映射为 `evidence` | 可以，但必须最终被 included |
| `historical_context` | 映射为 `history_review` | 不可以，只能辅助思考 |
| `ineligible` | 明确排除 | 不可以，也不会进入 Context |

例如，历史评审写着“以前出现过重复提交”，它可以提醒模型检查幂等性，却不能证明当前售后接口一定缺少幂等控制。

同样，当前 PRD 是 Requirement，是被评审对象；它不应该成为证明自身正确的 Citation Candidate。

这一步把“模型可以看到”与“模型可以把它当作外部依据引用”分开了。

## 唯一的 Context Builder

适配完成后，RAG 不会维护第二套装配算法。主入口仍然调用 `llm_core.context.build_review_context`：

```python
from llm_core import ContextSource, get_context_policy
from rag_core import build_rag_review_context

result = build_rag_review_context(
    requirement_text=requirement,
    retrieval_result=retrieval_result,
    additional_sources=(
        ContextSource(
            source_id="history-1",
            source_type="history_review",
            content="旧评审曾发现重复提交。",
        ),
    ),
    policy=get_context_policy("evidence_first"),
)

mapping = result.mapping
context = result.context
```

`build_rag_review_context` 内部只做两件事：

1. 把 `RetrievalResult` 映射为 `ContextSource`，检查 ID、locator 和证据资格；
2. 把映射结果和额外材料一起交给公共 Builder。

这样，静态资料、RAG 候选和以后的 Agent 摘要都遵守同一套 Context 契约，不会按课程章节复制平行实现。

## Builder 收到的是候选池，不是最终 Context

Builder 的输入 `sources` 只是材料候选池。真正构建前，它会先执行 `prepare_sources`：

```text
候选池
  ↓ 按 policy 过滤 source_type
允许进入的材料
  ↓ 相同 source_id 去重
身份唯一的材料
  ↓ 规范化 content 去重
内容唯一的材料
  ↓ 按类型权重、priority、score、source_id 排序
待分区材料
```

每个被排除的来源会留下原因，而不是凭空消失。

### 两种去重解决的问题不同

相同 `source_id` 表示同一个身份重复出现。Builder 保留排序更高的版本，并为另一条记录 `duplicate_source_id`。

不同 ID 的规范化内容相同，表示两个身份带来了重复文本。Builder 保留排序更高的一条，并记录 `duplicate_content`。

内容去重可以省预算，但它也有边界：两份文本暂时相同，不代表来源版本和有效期相同。如果版本差异本身有业务含义，不能只靠文本去重解决，仍需要上游知识治理。

## 为什么要分区，而不是把所有文字拼起来

准备好的来源会进入不同 section：

| Section | 常见 source type | 当前作用 |
| --- | --- | --- |
| `requirement` | 当前需求文本 | 被评审对象，始终保留 |
| `evidence` | `evidence`、`business_rule`、`api_doc`、`client_note` | 当前可引用依据 |
| `history` | `history`、`history_review` | 历史辅助信息 |
| `agent_summary` | `agent_summary`、`tool_result` | 中间结果，不等于事实来源 |
| `other` | 其他类型 | 兜底材料 |

Builder 按下面的顺序尝试填充：

```text
Evidence → History → Agent Summary → Other
```

Requirement 在这之前已经进入 Context。这个顺序表示当前风险评审优先保留现行证据，不表示所有 AI 应用都必须使用相同顺序。

## 总预算和分区预算怎样一起生效

只设一个总预算会有一个明显问题：一份很长的历史评审可能占满空间，真正需要引用的接口规则反而进不来。

所以 `ContextBuildPolicy` 同时有总预算和每个 section 的预算：

```python
ContextBuildPolicy(
    name="example",
    token_budget=500,
    section_budgets={
        "requirement": 120,
        "evidence": 250,
        "history": 70,
        "agent_summary": 50,
        "other": 10,
    },
    allow_compression=True,
    max_source_tokens=160,
    min_compression_tokens=36,
)
```

先用一组简化数字理解它：

```text
总预算                         500
Requirement 实际占用            120
Evidence 分区上限               250
History 分区上限                 70

Evidence A                       90
Evidence B                      180
History C                        80
```

构建过程是：

1. Requirement 先占用约 120，总剩余约 380；
2. Evidence A 需要 90，既没超过 Evidence 剩余 250，也没超过总剩余，因此进入；
3. Evidence B 需要 180，但 Evidence 只剩 160；即使总预算还够，它也只能尝试压到 160，否则丢弃；
4. History C 需要 80，但 History 分区只有 70；即使总预算仍有空间，它也不能借用 Evidence 的空位。

对单条来源来说，可用空间可以近似理解为：

```text
available = min(总剩余预算, 当前分区剩余预算)
```

因此，“总预算还有空间”不等于“任意材料都能进入”。分区预算就是为了防止某一类材料挤占其他类别。

### `max_source_tokens` 又限制了什么

若某条来源很长，即使当前 section 还有很多空间，`max_source_tokens` 也可以限制单条来源最多占多少。这样一篇超长接口文档不会吞掉整个 Evidence 分区。

最终单条来源的压缩目标还会受到它影响：

```text
target = min(available, max_source_tokens)
```

如果 policy 不允许压缩，或目标小于 `min_compression_tokens`，Builder 不会硬切出一小截不可读文本，而是把该来源标记为 dropped。

## 当前压缩算法具体做了什么

当前实现是确定性的 extractive compression，不会调用另一个模型改写证据。

```text
Requirement
  ↓ 提取关键词
来源内容
  ↓ 按行和句子切分
每个片段
  ↓ 计算与 Requirement 的关键词重合
按相关性选择能放进目标预算的片段
  ↓ 恢复原文顺序
压缩后的 ContextSource（source_id 不变）
```

这种做法有三个适合学习实验的特点：

- 同样输入会得到稳定结果；
- 原句被抽取，而不是由另一个模型重写事实；
- source ID 与 metadata 仍能保留。

但它不理解完整语义。例如原文是：

```text
只有 status=paid 且 sub_status!=closed 时才允许售后。
不满足条件时不得展示入口。
```

如果 Requirement 的关键词更多命中第一句，压缩可能保留条件，却漏掉第二句的否定约束。source ID 还在，不代表证据语义一定完整。

所以看到 `compressed=true` 时，不要只检查“这条来源有没有进入”，还要检查“关键条件和否定句有没有进入最终 Evidence block”。

## 用现有静态材料观察四种结果

主线实验需要真实 PostgreSQL 和 Embedding。为了先看清 Builder 本身，仓库还保留了离线的 [llm_context_lab](../../source/demos/llm_context_lab/README.md)。它使用固定材料池：

```text
BR-ORDER-STATE            订单状态规则
API-AFTER-SALE-V2         售后接口规则
CLIENT-DETAIL-API         客户端说明
HISTORY-2026-0412         历史评审
AGENT-RISK-SUMMARY        Agent 摘要
NOISE-OLD-V1              过期噪声
API-AFTER-SALE-V2-DUP     接口规则重复内容
```

不同 policy 会让同一候选池产生不同结果。

### `full_context`

预算较宽，通常能看到业务规则、接口说明、客户端说明、历史材料和 Agent 摘要。重复接口内容会因 `duplicate_content` 被排除；低优先级噪声仍可能因预算不足被丢弃。

它适合观察“尽量多放”带来的上下文形态，不表示材料越多效果越好。

### `evidence_first`

Evidence 获得主要预算，History 和 Agent Summary 的空间更小。当前样例中，业务规则、接口说明和客户端说明更容易保留，辅助材料可能因各自 section budget 被丢弃。

### `tight_budget`

总预算和单条来源预算都更小。高优先级 Evidence 先进入，较长的接口说明可能被压缩，其余材料被丢弃。

它不是“低成本生产配置”，而是用来稳定观察 compression 和 drop 的实验策略。

### `minimal`

只保留 Requirement，其他来源因 `source_type_excluded` 被排除。最终 Evidence 使用“无可用证据”占位，并产生 `no_evidence_included` warning。

它可以作为无证据对照，但“有 warning”还不等于系统已经实现拒答；拒答策略属于后续生成层。

## Citation Candidate 是怎样产生的

Builder 完成选择后，只从最终 included 的 Evidence 来源创建 `citation_candidates`：

```text
检索到的当前证据
  ├── included → Citation Candidate
  ├── compressed but included → Citation Candidate
  └── dropped → 不是 Citation Candidate

History / Agent Summary
  └── 即使 included，也不是 Citation Candidate
```

所以 Citation Candidate 只表达：

> 这条来源在本轮 Evidence 中真实存在，模型可以声明引用它。

它还没有证明模型真的引用了它、结论被它支持、当前证据已经充分，也没有证明来源内容没有过期。第 16 步会先检查模型声明的 source ID 是否属于这个候选集合；更强的“引用内容是否支持结论”仍是后续能力。

## `BuiltContext` 和 `ContextBuildReport` 分别看什么

构建完成后，实际对象在：

```python
context = result.context
report = context.report
```

### `BuiltContext`：实际材料

常用字段和方法包括：

```python
context.requirement_text
context.evidence_block
context.included_sources
context.dropped_sources
context.included_source_ids
context.dropped_source_ids
context.citation_candidates
context.context_block()
context.to_prompt_variables()
```

注意，`included_source_ids` 属于 `BuiltContext`，不是 `ContextBuildReport`。

### `ContextBuildReport`：构建解释

报告里可以看到：

```python
report.policy_name
report.token_budget
report.estimated_tokens
report.section_tokens
report.dropped_sources
report.compressed_source_ids
report.citation_source_ids
report.warnings
```

想知道“模型看到了什么”，先看 `BuiltContext`；想知道“为什么是这些材料”，再看 report。

## 一个必须说清的边界：当前 token budget 不是硬上限

这里很容易被一句“预算控制”误导。

当前 token 数来自本地估算：优先使用 `tiktoken` 的模型编码；找不到对应编码时回退到 `o200k_base`；tokenizer 不可用时还会使用字符数近似。它不是 Provider 对最终请求的计费结果。

而且当前 Builder 有两个明确边界。

### Requirement 会被完整保留

若 Requirement 本身超过 `requirement` 分区预算，Builder 会产生 `requirement_over_section_budget`，但不会截断被评审需求。若 Requirement 已经长于整个 `token_budget`，`estimated_tokens` 可能大于预算。

这是当前 V0 的选择：宁可暴露超预算，也不静默删掉需求正文。

### 最终 Prompt 还有额外开销

Builder 估算的是 Context section。真正请求还会加入 system message、任务说明、结构化输出约束和 Provider 特殊 token。因此：

```text
ContextBuildReport.estimated_tokens
≠ Provider 最终 input_tokens
```

所以本节里的 `token_budget` 应理解为：

> 本地的 Context 选择与分区预算目标，用于做可解释取舍；不是“最终请求永远不会超过模型窗口”的硬保证。

如果产品要提供硬保证，还需要在最终 messages 形成后再次按目标 Provider 计数，并定义超限时是拒绝、缩短 Requirement、继续压缩还是减少候选。当前代码尚未实现这层生产级闭环。

## 用四层检查定位 `source_channel` 为什么消失

现在回到开头的 bad case。不要从模型答案倒猜，从前往后查。

### 第一层：Retrieval

先看 `RetrievalReport`：

- 接口规则是否成为 Lexical 或 Dense 候选？
- 是否通过 route threshold？
- 是否进入 RRF？
- 是否被 `final_top_k` 保留？

如果它不在 `RetrievalResult.candidates`，问题仍在第 14 步及以前。

### 第二层：Retrieval → ContextSource mapping

再看 `mapping.decisions`：

- `chunk_id` 是否成为相同的 `source_id`？
- locator 与文档版本是否保留？
- 证据资格映射成了什么 `source_type`？
- 是否因 `ineligible` 被明确排除？

这里失败，说明两个 package 的契约没有正确接上。调 Context budget 不会修复缺失的 locator。

### 第三层：Context Builder

然后看：

```python
context.included_source_ids
context.dropped_sources
report.compressed_source_ids
report.citation_source_ids
```

若接口规则被检索并成功映射，却因 `token_budget_exceeded` 被 dropped，应该检查：

- Evidence 分区是不是太小；
- 前面是否有更高优先级材料占满预算；
- `max_source_tokens` 是否过小；
- 是否应该允许压缩；
- Retriever 是否返回了过多候选。

这时先调 Embedding 没有意义，因为正确候选已经检索到了。

### 第四层：Prompt 与模型

只有当接口规则已经 included，而且 `source_channel` 关键句确实出现在最终 `evidence_block` 中，才进入下一层：

- Prompt 是否明确要求逐条核对接口约束；
- 模型是否忽略了已有证据；
- 结构化输出是否容纳这个风险；
- 生成结果是否需要 Eval。

这四层把一句模糊的“RAG 没效果”拆成了四类可行动问题。

## 主实验：把前面整条真实链路接到 Context

本节主入口是 [inspect_rag_context.py](../../source/demos/rag_retrieval_lab/inspect_rag_context.py)。它不会伪造 RetrievalResult，而是复用前面的真实路径：

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

先按照 [rag_retrieval_lab README](../../source/demos/rag_retrieval_lab/README.md) 配置真实 PostgreSQL、migration 和 Embedding 服务，然后在仓库根目录运行：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_rag_context.py
```

默认会对同一个 `RetrievalResult` 运行 `evidence_first` 与 `tight_budget`。这里最重要的是“同一个 RetrievalResult”：检索候选不变，变化只来自 Context policy，因此 included、compressed、dropped 差异才能归因于 Context Builder。

### 展开真正需要观察的内容

```bash
uv run python source/demos/rag_retrieval_lab/inspect_rag_context.py --verbose
```

不要从第一行机械读到最后一行。按下面的顺序看：

1. `RetrievalReport · found candidates`：确认检索到了哪些 Chunk；
2. `Retrieval → ContextSource mapping`：确认身份、类型和 locator；
3. `included` / `dropped`：确认模型实际拿到哪些来源；
4. `citation candidates`：确认哪些 included 来源允许被引用；
5. `estimated / limit`：观察本地预算估算；
6. 最终 Context block：确认关键句是否真的存在。

### 只改变 Context policy

```bash
uv run python source/demos/rag_retrieval_lab/inspect_rag_context.py \
  --policies full_context,evidence_first --verbose
```

这次对照中，Requirement、Retriever 配置和 RetrievalResult 都不变。若结果不同，应能只用 `ContextBuildReport` 解释。

### 只移除历史辅助材料

先运行默认命令，再运行：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_rag_context.py \
  --without-history --verbose
```

预期关系是：

```text
RetrievalResult             不变
RAG mapped source IDs       不变
History section             变化
Citation Candidate          不应把 History 算进去
```

如果移除 History 后 RetrievalReport 也变了，说明实验同时改变了别的变量，不能再把差异归因于 Context。

### 真实依赖失败时会发生什么

主实验需要真实 `DATABASE_URL` 和 Embedding 配置。缺少数据库、鉴权失败或 Provider 异常会直接返回错误，不会静默切换到静态假候选。

这时可以用离线 `llm_context_lab` 学习 Builder，但必须准确表述结论：离线实验可以证明 Context Builder 的确定性行为；不能证明真实 RAG 链路已经接通，也不能证明检索质量。

## 一个自然 bad case：总预算有空，正确 History 仍被丢弃

假设总预算还剩 100 tokens，而 History 分区只剩 20；一条 60-token 的历史材料会被丢弃。

第一次看到时可能会觉得 Builder 出错了：“明明总空间够，为什么不放？”但这正是 section budget 在执行策略边界。

```text
候选池里有这条材料
→ 类型映射正常
→ History section 可用预算不足
→ dropped reason = token_budget_exceeded
```

如果业务确认这条 History 必须保留，改的是 `section_budgets["history"]`，而不是 Embedding、RRF 或 Prompt。

反过来，如果一条当前接口证据被 History 挤掉，则需要检查它是否被错误标成了 `history_review`。这时加预算只是掩盖类型映射错误。

## 常见失败与对应层次

| 现象 | 先看哪里 | 不要先做什么 |
| --- | --- | --- |
| 正确 Chunk 根本不在最终候选 | `RetrievalReport` | 不要先改 Prompt |
| 候选缺少 `source_spans` | RAG adapter 契约错误 | 不要填“未知位置”继续跑 |
| 当前证据被映射成 History | `mapping.decisions` 和证据资格 | 不要只加 Evidence 预算 |
| 不可用来源没有进入 Context | mapping reason | 不要误判成 Builder 随机丢失 |
| 不同 ID 的重复文本少了一条 | `duplicate_content` | 不要先调 Retriever top-k |
| 总预算有空间但某 section 仍丢材料 | `section_tokens` 与分区预算 | 不要把总预算当唯一限制 |
| source included 但关键否定句不见了 | 压缩后的 Evidence block | 不要只检查 source ID |
| History included 但不能引用 | Citation Candidate 规则 | 不要把辅助信息升级成现行证据 |
| `estimated_tokens` 超过 budget | Requirement warning 与本地估算边界 | 不要宣称已有硬上限 |
| Evidence 已包含关键句，模型仍漏答 | Prompt、模型行为与生成 Eval | 不要再反复调 Embedding |

## 测试守住了哪些不变量

本节相关确定性测试可以离线运行：

```bash
uv run pytest \
  source/packages/llm_core/tests/test_context.py \
  source/packages/rag_core/tests/test_rag_context.py -q
```

它们重点验证：

1. 检索 `chunk_id` 到 Context `source_id` 不变；
2. 文档版本、locator、路由排名和原生分数没有在适配时丢失；
3. 原生检索分数只作为诊断信息，不冒充事实权威性；
4. 缺少 `source_spans` 的检索候选不能进入可追踪 Context；
5. `historical_context` 可以辅助模型，但不能成为 Citation Candidate；
6. `ineligible` 候选会被明确排除；
7. additional source 不能用相同 ID 覆盖检索 Chunk；
8. 同 ID 和同内容去重都会留下原因；
9. 紧预算下可以压缩来源并保留稳定 ID；
10. 每条 mapped source 最终都能在 included 或 dropped 中找到去向。

这些测试证明的是确定性数据契约，不证明 PostgreSQL 与 Embedding 服务当前可用、检索效果足够好、某个 policy 是最优配置、模型一定使用 Evidence、Citation 一定支持结论，或最终 Provider 请求一定不会超出窗口。

这也是“测试通过”和“RAG 产品已经可信”之间的边界。

## 从 demo 进入核心代码

如果你第一次读这部分代码，建议沿着一次数据变化读，不要先打开整个 package：

1. [inspect_rag_context.py](../../source/demos/rag_retrieval_lab/inspect_rag_context.py)：看真实实验如何得到同一个 `RetrievalResult` 并比较 policy；
2. [adapter.py](../../source/packages/rag_core/context/adapter.py)：看候选身份、locator 和证据资格怎样进入 `ContextSource`；
3. [types.py](../../source/packages/llm_core/context/types.py)：看候选、policy、最终 Context 和报告分别保存什么；
4. [ranking.py](../../source/packages/llm_core/context/ranking.py)：看过滤、去重、排序和 section 映射；
5. [builder.py](../../source/packages/llm_core/context/builder.py)：看总预算与分区预算怎样共同选择来源；
6. [compression.py](../../source/packages/llm_core/context/compression.py)：看确定性抽取压缩与失败边界；
7. [formatting.py](../../source/packages/llm_core/context/formatting.py)：看 source ID 和 metadata 怎样进入最终文本；
8. [test_rag_context.py](../../source/packages/rag_core/tests/test_rag_context.py) 与 [test_context.py](../../source/packages/llm_core/tests/test_context.py)：用测试反查上述不变量。

读 `builder.py` 时可以画一条来源的轨迹：

```text
ContextSource
→ prepare_sources
→ section_for_source
→ available tokens
→ fit_source
→ included / compressed / dropped
→ section content
→ citation candidates
```

能沿这条轨迹解释一条来源，比记住所有类名更重要。

## 框架能替你做什么，不能替你决定什么

很多框架能提供文本切分、Prompt 模板、Retriever 接口、文档压缩器和 token 计数器。这些组件能减少样板代码，但不会自动决定：

- Requirement、Evidence、History 应该怎样分区；
- 哪些来源具备当前证据资格；
- 历史材料是否允许被引用；
- 来源身份和 locator 怎样贯穿检索与生成；
- 某个 section 应分到多少预算；
- 压缩丢失否定条件时如何发现；
- 无证据或超预算时产品应该继续、拒绝还是追问。

因此 Context Engineering 不是“选一个框架的 memory 类”。它是应用对模型输入边界和证据责任的显式设计。

## 亲手完成一个只改策略、不改检索的小实验

这次不需要再给 demo 增加 `--policies`，因为它已经支持这个参数。更有价值的练习是补一个确定性测试：

> 构造一个“总预算仍有空间，但 History 分区放不下”的来源，证明它会因 section budget 被 dropped；然后只增加 History 分区预算，证明同一来源能够 included。

约束如下：

1. Requirement 内容不变；
2. sources 内容、ID、类型和顺序不变；
3. 总 `token_budget` 不变；
4. 第一次只让 History section 太小；
5. 第二次只增大 `section_budgets["history"]`；
6. 断言第一次的 dropped reason；
7. 断言第二次 History included，但仍不进入 Citation Candidate。

完成后，你应该能用一句话解释结果：

```text
来源不是因为检索失败而消失，而是因为它所属分区没有预算。
```

如果你同时改了 Retriever top-k、来源内容或总预算，这个实验就不再是单变量对照。

## 学完后的自检

先不看正文，回答下面的问题：

- 为什么“知识库有”不等于“Retriever 找到”，而“Retriever 找到”又不等于“模型看到”？
- `RetrievalReport`、mapping decisions、`BuiltContext`、`ContextBuildReport` 分别解释哪段链路？
- 为什么 Context 的 `source_id` 要继续使用稳定 `chunk_id`？
- 为什么必须保留 locator，而不能只保留来源标题？
- RRF 分数为什么能影响装配顺序，却不能代表来源权威性？
- 为什么 History 可以 included，却不能成为 Citation Candidate？
- 总预算还有空间时，来源为什么仍可能因 section budget 被丢弃？
- `compressed=true` 时，为什么还要检查最终 Evidence block？
- 为什么当前 `token_budget` 是选择目标，而不是 Provider 请求的硬上限？
- 正确候选因 Context 预算丢失时，为什么不应该先调 Embedding？

最后完成一次真实追踪：从 `RetrievalResult` 中选一条 Chunk，找到相同的 `source_id`，检查它的 locator、mapping decision、included/dropped 去向和 Citation Candidate 状态。再解释另一条材料为什么没有进入。

做到这一步，你掌握的不是“把几段文字拼进 Prompt”，而是能解释模型这一轮究竟看到了什么，以及应用为什么做出这次取舍。

回到 [标准学习路径](../learning-path.md) 后，第 16 步会把 `BuiltContext` 交给真实模型，继续处理结构化生成、未知 source ID 和可信输出边界。

## 延伸参考

- [OpenAI Cookbook：How to count tokens with tiktoken](https://cookbook.openai.com/examples/how_to_count_tokens_with_tiktoken)：理解本地 token 计数为什么依赖模型编码，以及为什么最终 messages 仍有额外开销。
