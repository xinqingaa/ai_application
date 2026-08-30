# Context Engineering：输入装配、预算与证据边界

> 这是一篇机制篇。固定 Retriever 已经把过滤、每路候选、阈值、RRF 和最终截断收进 `RetrievalResult` 与 `RetrievalReport`。本文只向前推进一步：同一批最终候选怎样变成模型本轮真正可见、可定位、可声明来源的 `BuiltContext`。
>
> 学完后，你应该能从一条 `RetrievalResult.candidates` 候选追踪到 mapping、预算决定和 Citation Candidate，解释它为什么被保留、压缩或丢弃。本文不调用生成模型，也不判断某条结论是否真的获得证据支持。

## Retriever 找到了，为什么还可能看不到

继续固定同一份业务材料和同一个问题：

```text
资料：order_rules.md
dataset_version：rag-retrieval-exploration-1.0.0
query_id：surface_match
问题：申请售后
范围：after_sale + reference_knowledge + current_evidence
```

当前资料经同一 Chunk 策略形成两个候选单元：

| Chunk | 真实业务内容 |
| --- | --- |
| A：当前订单状态规则 | 仅已支付且已完成的订单可申请售后；虚拟商品不进入售后流程 |
| B：接口与客户端约束 | 售后接口 v2 必须提供 `source_channel`；Flutter 客户端使用相同入口可见性规则 |

在干净课程数据库和本节当前真实运行中，两路检索都成功，A、B 都进入了 `RetrievalResult.candidates`。这只证明 Retriever 把它们交给了下游，还不证明模型一定能看到两条。

假设 Context 的 Evidence 分区只能容纳 A。装配结果会变成：

```text
RetrievalResult.candidates = [A, B]
→ A included
→ B dropped: token_budget_exceeded
→ BuiltContext 只包含 A
→ Citation Candidate 也只包含 A
```

此时如果后续模型没有谈到 `source_channel`，不能回到数据库盲调 Embedding。B 已经被检索到，只是在 Context 装配阶段离开了模型输入。

这就是本节的核心区别：

```text
Retriever 找到什么
≠
模型这一轮看到什么
```

## 从 RetrievalResult 到 BuiltContext

本节只追踪一条输入装配链：

```text
RetrievalResult.candidates
        ↓ 保留身份、位置和路线诊断
Retrieval → Context mapping
        ↓
ContextSource 候选池
        ↓ 类型过滤、去重、排序
分区候选
        ↓ 总预算、分区预算、单来源上限、可选压缩
BuiltContext
        ├── ContextBuildReport
        └── Citation Candidate[]
```

`RetrievalReport` 仍解释候选怎样通过检索链；`ContextBuildReport` 解释候选怎样通过输入装配链。二者相邻，但不能合并成一个含义模糊的 `debug_info`。

## 四个对象不能混成一个“上下文”

### Retrieval Candidate

`RetrievalResult.candidates` 是固定 Retriever 最终选中的 Chunk。它携带稳定 `chunk_id`、文档版本、原文位置、RRF 排名、路线贡献和证据资格。

候选已经越过固定 Retriever 的 `final_top_k`，但尚未经过 Context 的类型、去重和预算控制。

### ContextSource

`ContextSource` 是 Context Builder 能够处理的统一材料单元。它不仅保存正文，还保存来源身份、类型、优先级和 metadata。

RAG 适配器把每个 Retrieval Candidate 映射成 `ContextSource`。这个适配层只转换契约，不重新检索，也不重新实现预算算法。

### BuiltContext

`BuiltContext` 是应用允许模型本轮看到的最终材料。它包含 Requirement、最终 Evidence block、其他已允许分区、included/dropped 结果和构建报告。

知识库有某条规则、Retriever 找到某条规则，都不能替代检查 `BuiltContext` 中是否真的存在该规则。

### Prompt

Prompt 规定模型应该怎样使用输入，例如“只能声明本轮允许的 source ID”。Context 决定模型拿到了哪些材料。

```text
Prompt：怎样做
Context：拿什么做
```

Prompt 写得再严格，也补不回 Builder 已经丢掉的 B。后续可信生成才会把 `BuiltContext` 交给真实生成模型。

## Mapping 的第一条不变量：身份不能重编

### `source_id` 继续使用 `chunk_id`

从资料进入固定 RAG 后，同一条内容一直使用同一个稳定身份：

```text
数据库 Chunk
↔ Lexical / Dense candidate
↔ RRF candidate
↔ RetrievalResult candidate
↔ ContextSource
↔ Citation Candidate
```

若适配时临时改成 `SOURCE-1`、`SOURCE-2`，同一 Chunk 在不同运行中可能获得不同编号。检索日志、Context 报告和后续来源声明将无法稳定关联。

因此当前适配器直接令：

```text
ContextSource.source_id = RetrievalCandidate.chunk_id
```

额外材料也不能占用某个检索 Chunk 的 `source_id`。发生冲突时必须明确失败，不能让后加入的文字静默覆盖真实候选。

### locator 缺失时不能伪装可追踪

`source_id` 只能回答“是哪条材料”，locator 才能回答“原文在哪里”。当前适配器要求每个检索候选至少携带一个 `source_span`：

```text
candidate 有 chunk_id，但没有 source_span
→ mapping 失败
→ 不构造“位置未知”的 Evidence
```

这条约束继承自文档解析和 Chunking。否则后续即使模型声明了 source ID，用户也无法回到原文核对。

### 哪些诊断保留在 Source，哪些仍属于 Report

映射后的 `ContextSource.metadata` 保留与该候选直接相关的信息：

- `document_id`、`document_version`；
- 来源角色和证据资格；
- 原文 locators；
- `fusion_rank`、`rrf_score`；
- 各路线名次、原生分数名称、数值和方向；
- `retriever_config_ref`。

每路 indexed、visible、threshold 状态和部分失败等运行级事实仍留在 `RetrievalReport`。适配器不会把整份检索报告复制进每条 Source；应用通过同一运行记录和配置身份把二者关联起来。

## RRF 排名不是证据权威性

RAG 适配器会用融合名次保持候选的预算选择顺序，但不会把 RRF 分数写成通用可信度：

```text
PostgreSQL ts_rank  → 词面排序信号
cosine distance     → 向量距离
RRF score           → 多路名次融合信号
证据资格             → 当前材料能否作为外部依据
```

前三项回答“为何排在这里”，最后一项回答“允许怎样使用”。排序靠前不等于事实更权威，也不等于内容已经支持某条结论。

## 证据资格先决定进入哪个边界

适配器根据 Retrieval Candidate 的 `evidence_eligibility` 做显式映射：

| 检索资格 | Context 类型 | 后续能否成为 Citation Candidate |
| --- | --- | --- |
| `current_evidence` | `evidence` | included 后可以 |
| `historical_context` | `history_review` | 不可以 |
| `ineligible` | 明确排除 | 不可以 |

本节真实主路径的 A、B 都是 `current_evidence`。历史材料和不可用材料只用于确定性契约测试；它们不是 `order_rules.md` 中的新增业务事实。

Requirement 是被评审对象，也不能用来证明自身正确。于是“模型可以看到”和“模型允许声明为来源”始终是两层判断。

## Builder 收到的是候选池，不是最终输入

映射成功的 Source 进入唯一的 Context Builder。构建前先执行：

```text
ContextSource 候选池
  ↓ policy 允许的 source_type
类型过滤
  ↓ 相同 source_id 去重
身份唯一
  ↓ 规范化内容去重
内容唯一
  ↓ 类型权重、priority、score、source_id
稳定排序
```

每个被排除的来源都留下 reason，例如：

- `source_type_excluded`；
- `duplicate_source_id`；
- `duplicate_content`。

相同 ID 表示身份冲突或重复输入；不同 ID 但文本相同表示内容重复。内容去重可以节省预算，却不能替代文档版本治理：两份文字暂时相同，不代表有效期和来源责任相同。

对于本节真实 A、B，二者身份和内容都不同。干净基线不应依靠 `duplicate_content` 让其中一条消失。若真实运行出现非当前 fixture 的旧身份，应该先处理数据准备差异，再研究 Context 策略。

## 为什么要同时有总预算和分区预算

Context 不只有 Evidence。通用 Builder 还支持 Requirement、History 等分区。当前固定 RAG 主路径只使用 Requirement 和 Evidence，但分区规则仍然重要：低优先级材料不能因为总预算有空就挤占当前证据的责任边界。

一次选择同时受三类空间限制：

```text
总剩余预算
当前分区剩余预算
单来源上限（若配置）
```

对一条 Source，可用空间近似为：

```text
available = min(总剩余预算, 当前分区剩余预算, 单来源上限)
```

### 用同一 A、B 做确定性预算推演

下面是机制推演，不是新的业务资料，也不是 Provider 计费结果。假设本地格式化后：

```text
Requirement “申请售后”      约 3 tokens
A                           约 302 tokens
B                           约 293 tokens
总预算                      2200
Evidence 分区预算            350
```

Builder 按融合顺序处理：

1. Requirement 完整进入；
2. A 需要约 302，没有超过 Evidence 的 350，因此 included；
3. Evidence 只剩约 48，B 需要约 293；
4. 当前 `full_context` 不允许压缩，因此 B 被标记为 `token_budget_exceeded`。

注意，总预算仍有大量空间，但 B 依然被丢弃。原因是 Evidence 分区空间不足，不是 Retriever 漏召回，也不是总窗口已经耗尽。

真实 token 数应以实验当前 tokenizer、metadata 和格式化结果为准；这里的数字只用于把控制顺序说清楚。

## 压缩不是“来源还在就没问题”

当 policy 允许压缩且单条 Source 超过可用空间时，当前 Builder 使用确定性的抽取式压缩：

```text
Requirement 提取关键词
→ Source 按行和句子切分
→ 按关键词重合排序
→ 在目标预算内选择原文片段
→ 恢复原始顺序
```

它不调用另一个模型改写事实，同样输入会产生稳定结果，`source_id` 和 metadata 继续保留。

但是 source ID 被保留，不等于业务条件被完整保留。若一个较长版本的接口 Chunk 同时包含 `source_channel`、入口规则和否定条件，抽取式压缩可能只留下与“申请售后”词面更接近的句子。

这里的“较长版本”是确定性机制假设：当前 `order_rules.md` 只有两个短 Chunk，真实主实验不靠伪造长资料制造压缩成功。压缩契约由同主题的受控测试稳定验证；真实主路径仍显示 A、B 的原始内容。

## Citation Candidate 只能来自最终 included Evidence

Builder 完成选择后，从最终 included 的 Evidence 产生 Citation Candidate：

```text
current evidence
  ├── included              → Citation Candidate
  ├── compressed + included → Citation Candidate
  └── dropped               → 不是 Citation Candidate

history / ineligible
  └── 即使模型可见，也不能成为当前证据候选
```

Citation Candidate 只表达两件事：

1. 这条 Evidence 在本轮 `BuiltContext` 中真实存在；
2. 后续模型可以声明它的 `source_id`。

它不证明模型一定会声明、不证明内容支持某条结论，也不证明证据已经充分。后续可信生成只会先检查模型声明的 ID 是否属于候选集合；更强的支持性和充分性仍由后续机制完成。

## BuiltContext 与 ContextBuildReport 各回答什么

| 对象 | 回答的问题 |
| --- | --- |
| `BuiltContext` | 模型这一轮实际能看到什么 |
| `ContextBuildReport` | 为什么形成这些材料 |

构建报告至少应解释：

- 使用了哪份有效 policy；
- 总预算和分区预算；
- 每个分区的实际估算用量；
- included、dropped、compressed 来源；
- dropped 或 compressed reason；
- Citation Candidate 集合；
- Requirement 超分区、Evidence 为空等 warning。

应用既不能只保存报告而丢掉真实输入，也不能只保存输入而丢掉决策过程。

## 当前 token budget 不是 Provider 硬上限

当前 token 数是本地估算。实现优先使用适配的 tokenizer 编码，不可用时会使用约定的回退估算。它控制的是 Context 选择，不是 Provider 对最终 messages 的计费结果。

还有两个边界必须保留：

### Requirement 当前不会被静默截断

Requirement 超过自己的分区预算时，Builder 产生 `requirement_over_section_budget` warning，但仍保留完整 Requirement。若 Requirement 本身超过总预算，最终估算甚至可能大于配置值。

### 最终 messages 还有额外开销

真实请求还会加入 system message、任务说明、结构化输出 Schema 和 Provider 特殊 token：

```text
ContextBuildReport.estimated_tokens
≠
Provider 最终 input_tokens
```

要提供严格窗口保证，必须在最终 messages 形成后再次按目标 Provider 计数，并定义超限时的拒绝、压缩或删减策略。当前第一阶段 Context Builder 还没有伪装成完成了这层生产保证。

## 按候选第一次消失的位置诊断

仍以 B 的 `source_channel` 规则为例：

### 第一层：Retrieval

检查 `RetrievalResult.candidates` 是否有 B，并用 `RetrievalReport` 回看过滤、候选、阈值、RRF 和 `final_top_k`。

B 不在这里，问题仍属于固定 Retriever 或更早的资料链；调 Context budget 无效。

### 第二层：Mapping

检查 B 是否保持相同 `source_id`、locator、文档版本和证据资格。

若缺少 locator 或资格为 `ineligible`，问题发生在 Retrieval → Context 契约；加预算不能修复身份错误。

### 第三层：Context Builder

检查 B 是 included、compressed 还是 dropped，并读取 reason、分区用量和最终 Evidence block。

若 reason 是 `token_budget_exceeded`，应检查 Evidence 分区、前序来源和压缩策略，而不是重新训练 Embedding。

### 第四层：Prompt 与模型

只有 B 已 included，且 `source_channel` 真的出现在最终 Evidence block 中，才把问题交给 Prompt、真实模型和生成 Eval。本文到第三层为止。

## 正常边界与失败边界

| 现象 | 性质 | 应怎样解释 |
| --- | --- | --- |
| A、B 都 included | 正常路径 | 两条当前证据都对模型可见 |
| B 因 Evidence budget 被 dropped | 正常配置边界 | Retriever 成功，Context 做了明确取舍 |
| Evidence budget 为 0 | 自然边界 | Requirement 保留，无 Citation Candidate，并产生 warning |
| Source 被压缩 | 受控取舍 | 身份保留，但必须检查关键条件是否仍在 |
| 候选缺少 locator | 契约失败 | 明确停止，不伪造位置 |
| 额外来源与 chunk ID 冲突 | 契约失败 | 明确停止，不静默覆盖 |
| PostgreSQL 或 Embedding 失败 | 上游真实依赖失败 | Context Builder 尚未获得可信 RetrievalResult |
| Retriever 部分失败 | 上游不完整结果 | 可以保留诊断，但不能当作完整成功基线 |
| 出现非当前 fixture Chunk | 数据准备失败 | 先处理旧身份，不把去重误当策略效果 |

## 当前能力由谁承载

本节没有引入 Agent 框架。职责分为两层：

```text
rag_core Context adapter
→ 把 RetrievalResult 映射成可追踪 ContextSource

llm_core Context Builder
→ 负责过滤、去重、排序、分区、预算、压缩和报告
```

当前 Builder 是本地确定性实现，适合把输入边界和失败原因完整暴露出来。成熟框架可以提供文档压缩器、Prompt 模板或 token 计数器，但不能替应用决定：哪些材料是当前证据、历史是否可引用、locator 如何贯穿、分区预算如何分配，以及证据为空时产品应该怎样处理。

需求评审助手负责提供领域材料、证据资格和 policy；通用 package 不写死某一个售后问题，也不维护第二套 Retriever。

## 向可信生成交付什么

本节最终交付：

```text
BuiltContext
+ ContextBuildReport
+ Citation Candidate IDs
```

下一步可以确认模型真实输入、列出允许声明的 source ID，并检查模型是否生成未知 ID。但“ID 合法”仍不等于“内容支持结论”。

## 学完后的自检

- 为什么 `RetrievalResult.candidates` 有 B，不代表模型一定看到 B？
- `RetrievalReport` 与 `ContextBuildReport` 分别解释哪段链路？
- 为什么 `source_id` 要继续使用稳定 `chunk_id`？
- locator 缺失时为什么不能填“未知位置”继续？
- RRF 排名为什么不能作为来源权威性？
- 总预算还有空间时，B 为什么仍可能因 Evidence 分区被丢弃？
- `compressed=true` 时为什么仍要检查最终 Evidence block？
- 为什么 dropped Evidence 不能成为 Citation Candidate？
- 当前 token budget 为什么不是 Provider 的硬窗口保证？
- B 在哪个层次第一次消失，就应该修改哪个层次？

最后沿同一个 `surface_match=申请售后` 追踪 A、B：确认 Retrieval Candidate、mapping decision、included/dropped、最终 Evidence block 和 Citation Candidate 中的身份是否一致。能够完成这条追踪，才算真正理解模型这一轮拿到了什么。
