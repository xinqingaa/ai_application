# Top-k、阈值、Metadata Filter 与 Retrieval 诊断

> 这是一篇机制篇。[RRF 融合](multi-retrieval-and-rrf.md)已经把 lexical 与 dense 排名融合成 `RRFResult`；本节继续回答：一条候选从“数据库中存在”到“最终交给 Context Builder”，会在哪些控制点被保留或淘汰？读完后，你应该能跟踪一条 Chunk 穿过 `pre-filter → candidate_k → route threshold → RRF → final_top_k`，并从 `RetrievalReport` 判断它消失在哪一层。本文不讨论 Context token 预算、Reranker，也不把示例阈值包装成产品最佳参数。

## “数据库里有”为什么仍然不等于“Retriever 会返回”

知识库里有这样一条接口规则：

```text
创建售后单时，source_channel 为必填字段。
```

用户询问：

```text
创建逆向服务时需要哪些字段？
```

最后的检索结果里却没有这条规则。刚开始学习 RAG 时，很容易把它概括成“数据库没搜到”或者“Embedding 不准”。但在固定 RAG 中，这条 Chunk 至少要穿过五层控制：

```text
已索引 Chunk
→ Metadata pre-filter
→ lexical / dense candidate_k
→ 每路原生分数 threshold
→ RRF
→ final_top_k
→ RetrievalResult.candidates
```

它可能根本不在当前业务范围，也可能进入了某一路候选后被阈值删除，还可能完成融合却恰好排在最终截断线之外。

所以只返回一个 `Chunk[]` 不够。下游除了需要最终候选，还需要知道：

- 本轮允许搜索哪些资料。
- 两路分别看到了多少候选。
- 哪条候选在哪个阈值被删除。
- RRF 合并后有多少不同候选。
- 哪条候选只因最终 `top_k` 没被选中。
- 某一路是真的没有结果，还是执行失败。

Retriever 契约的核心不是“参数比较多”，而是让每次候选变化都有明确位置和可检查原因。

## 先让五条候选走完整条链

下面先做一个确定性手算。它使用与 `test_hybrid_retriever.py` 相同的排名和数值结构，但把候选改成更容易理解的业务名称。它用于学习控制顺序，不代表真实 Embedding 服务一定返回这些数值。

当前配置是：

```text
knowledge_scope = after_sale
source_roles = [reference_knowledge]
evidence_eligibilities = [current_evidence]

lexical_candidate_k = 3
dense_candidate_k = 3
lexical_min_rank = 0.50
dense_max_distance = 0.25
rrf_k = 60
final_top_k = 2
```

我们重点跟踪五条候选：

| 代号 | 简化内容 | 后面会出现在哪里 |
| --- | --- | --- |
| A `shared` | 创建售后单时必须传 `source_channel` | lexical 与 dense |
| B `exact-only` | `source_channel` 的字段枚举说明 | lexical |
| C `lexical-low` | 一条只有弱词面重合的售后说明 | lexical，但原生分数低 |
| D `semantic-only` | 发起逆向服务前需要校验订单状态 | dense |
| E `dense-far` | 主题相邻但业务无关的入口说明 | dense，但距离远 |

### 第一层：Metadata Filter 把 10 条缩小到 6 条可见资料

假设当前兼容索引中有 10 条 Chunk。只有 6 条同时满足：

```text
knowledge_scope = after_sale
source_role = reference_knowledge
evidence_eligibility = current_evidence
```

另外 4 条可能属于营销业务域、历史评审，或者不允许作为当前证据。它们不会先参与全库排名再被删掉，而是在 lexical 匹配和 dense 距离排序之前就不进入当前可见集合。

此时报告中的数量关系是：

```text
indexed_chunk_count = 10
visible_chunk_count = 6
```

这一步还没有判断 A–E 谁更相关，只是在回答“本轮允许搜索谁”。

### 第二层：每条路线各自只取前 3 名

在 6 条可见资料中，两路分别排序并应用自己的 `candidate_k`：

| Lexical route rank | 候选 | `postgresql_ts_rank` |
| ---: | --- | ---: |
| 1 | A `shared` | 0.90 |
| 2 | B `exact-only` | 0.70 |
| 3 | C `lexical-low` | 0.20 |

| Dense route rank | 候选 | `pgvector_cosine_distance` |
| ---: | --- | ---: |
| 1 | D `semantic-only` | 0.10 |
| 2 | A `shared` | 0.20 |
| 3 | E `dense-far` | 0.80 |

两路现在各有 3 条，但不能把它理解成“总共有 6 个不同 Chunk”：A 同时出现在两路，之后会按稳定 `chunk_id` 合并。

`candidate_k` 控制的是“每路最多带多少候选进入后续处理”。如果两路都设为 1，RRF 最多只看见两个路由位置；事后把 `final_top_k` 从 2 改成 10，也找不回从未进入融合输入的路线第 2、3 名。

### 第三层：阈值在各自的原生空间中做决定

Lexical 的分数越大越好，因此执行：

```text
fts_rank >= 0.50
```

| 候选 | 判断 | 结果 |
| --- | --- | --- |
| A | `0.90 >= 0.50` | passed |
| B | `0.70 >= 0.50` | passed |
| C | `0.20 >= 0.50` | dropped |

Dense 保存的是 cosine distance，越小越近，因此执行：

```text
cosine_distance <= 0.25
```

| 候选 | 判断 | 结果 |
| --- | --- | --- |
| D | `0.10 <= 0.25` | passed |
| A | `0.20 <= 0.25` | passed |
| E | `0.80 <= 0.25` | dropped |

经过阈值后：

```text
Lexical：A(1), B(2)
Dense：  D(1), A(2)
```

C 和 E 没有进入 RRF。它们不是被 RRF 排低，而是在融合之前已经被各自路线的准入线删除。

### 第四层：RRF 看到 4 条记录，合成 3 个不同候选

使用RRF 融合已经学过的公式：

```text
contribution = 1 / (rrf_k + route_rank)
```

`rrf_k=60` 时：

| 候选 | 路线贡献 | RRF 分数 | fusion rank |
| --- | --- | ---: | ---: |
| A | lexical `1/61` + dense `1/62` | 0.032522 | 1 |
| D | dense `1/61` | 0.016393 | 2 |
| B | lexical `1/62` | 0.016129 | 3 |

A 的两条记录按 `chunk_id` 合并，因此：

```text
route candidates after threshold = 2 + 2
distinct fused candidates = 3
overlap candidates = 1
```

### 第五层：`final_top_k=2` 只选择融合前两名

最终选择是：

| fusion rank | 候选 | 最终决定 |
| ---: | --- | --- |
| 1 | A | `selected_by_final_top_k` |
| 2 | D | `selected_by_final_top_k` |
| 3 | B | `dropped_by_final_top_k` |

B 已经通过 lexical 阈值，也进入了 RRF，只是融合后排第 3。此时降低 dense 阈值并不针对真正原因，因为 B 根本不是在 dense 阈值处消失的。

整条链可以压缩成一行：

```text
indexed 10
→ visible 6
→ route candidates lexical 3 / dense 3
→ threshold passed lexical 2 / dense 2
→ fused distinct 3
→ final selected 2
```

如果你能指出 A–E 最后分别停在哪一层，就已经建立了本节最重要的诊断视角。

## 五层顺序为什么不能随便交换

刚才的顺序不是为了让日志整齐，而是会直接改变结果。

### Metadata Filter 必须先限定竞争范围

正确语义是：

```text
从售后现行规则中找最相关的前 3 条
```

而不是：

```text
先从全库找前 3 条
→ 再删除不属于售后的结果
```

如果全库前三名都被营销资料占据，后过滤可能得到 0 条；售后范围内本来应该排第一的规则甚至没有机会进入候选。

当前实现不会在 Python 中先搜全库再过滤。`FixedHybridRetriever` 把相同的 `knowledge_scope`、`source_roles` 和 `evidence_eligibilities` 传给 lexical、dense 两路，各自的 SQL 在排序与 `LIMIT` 前建立可见集合。

### `candidate_k` 与 `final_top_k` 控制不同池子

```text
candidate_k
→ 限制每条路线交给融合层的深度

final_top_k
→ 限制融合之后交给下游的数量
```

增大 `final_top_k` 只会从已经融合的候选中多选几条，无法扩大上游路线曾经观察的范围。增大 `candidate_k` 则可能增加单路候选、路线重合和融合竞争，同时带来更多后续处理量。

两者都不是“越大越好”：候选太浅可能漏召回，候选太深则可能把大量弱相关结果带进融合与 Context 预算竞争。最佳值需要固定数据集验证。

### Route threshold 必须在原生分数空间中判断

当前两路分别使用：

```text
lexical_min_rank：postgresql_ts_rank >= threshold
dense_max_distance：pgvector_cosine_distance <= threshold
```

不能给两路共用一个名为 `min_relevance=0.7` 的模糊字段。一个数越大越好，另一个数越小越好；模型、词法配置和数据变化也会改变数值分布。

阈值先于 RRF，是因为 RRF 分数只表达多路名次贡献，并不是标定后的统一相关度。先让每条路线根据自己的原生尺度决定准入，再融合剩余排名，诊断含义更清楚。

### `final_top_k` 发生在融合之后

如果先从每路选最终两条再拼接，得到的仍是两个局部 top 2，不是一个全局融合 top 2。当前顺序先计算所有通过阈值候选的 RRF 排名，再统一截断。

由于配置要求 `final_top_k > 0`，只要 RRF 有候选，最终结果至少会有一条。`final_top_k` 可以让某个正确候选消失，但不会把非空融合列表截成空列表。

## Metadata Filter 不是相关度，也不是完整权限系统

当前第一阶段实现使用三类字段表达检索范围：

| 字段 | 当前作用 | 示例 |
| --- | --- | --- |
| `knowledge_scope` | 业务知识范围 | `after_sale` |
| `source_roles` | 资料在系统中的角色 | `reference_knowledge` |
| `evidence_eligibilities` | 当前是否允许作为证据候选 | `current_evidence` |

它们回答“这条资料能不能参与本轮搜索”，不回答“它与 query 有多相关”。一个 Chunk 即使完全匹配 `source_channel`，只要属于历史材料或另一个业务 scope，也不应该偷偷进入当前证据路线。

Dense 路线还有一个额外硬约束：query 与存储向量必须属于兼容的 Embedding 空间。Embedding space filter 解决表示兼容性，业务 Metadata 解决可见范围；二者不能互相替代。

第一阶段当前是单用户固定项目，这些字段也不等于完整的租户权限或文档 ACL。未来若有用户权限，权限过滤仍必须在召回前生效，但不能假装现有 `knowledge_scope` 已经实现了企业权限系统。

## 数量看起来相似，含义却不同

`RouteControlReport` 会同时记录多种数量。初学时最容易把它们都看成“结果数”。

```text
indexed_chunk_count
→ 当前路线兼容索引里有多少 Chunk

visible_chunk_count
→ 经过空间与 Metadata 范围后还有多少 Chunk

matched_chunk_count
→ lexical 中有多少可见 Chunk 满足 FTS 匹配

candidate_count
→ candidate_k 后真正返回了多少路线候选

passed_threshold_count / dropped_threshold_count
→ 路线候选经过阈值后的去向
```

Lexical 有明确的 `@@` 匹配，所以可以区分：

```text
visible 20 → matched 8 → candidate 5
```

Dense exact search 对每个兼容且可见的向量都能计算距离，因此当前统一报告中的 `matched_chunk_count` 为 `None`，不能伪造一个与 FTS 相同的“匹配数”。它直接记录 visible 与 returned candidate 数量。

两路的 `indexed_chunk_count` 也不一定相同：lexical 统计兼容词法配置的 Chunk，dense 统计当前 Embedding 空间中的向量。如果两者相差很大，先检查索引生产和空间版本，不要急着调融合参数。

## 阈值决策必须留下每条候选的原始事实

只记录下面这句话无法诊断：

```text
Chunk C 被阈值删除。
```

我们还需要知道它来自哪一路、使用什么数值和方向。`ThresholdDecision` 因此保存：

```text
route_name
chunk_id
route_rank
native_score_name
native_score
higher_is_better
threshold_name / threshold_value
status / reason
```

手算例中的 C 会形成类似记录：

```text
route_name = lexical
chunk_id = lexical-low
native_score_name = postgresql_ts_rank
native_score = 0.20
higher_is_better = true
threshold_name = lexical_min_fts_rank
threshold_value = 0.50
status = dropped
reason = dropped_by_route_threshold
```

如果阈值配置为 `None`，所有现有路线候选都会通过，但报告仍写明：

```text
threshold_name = None
threshold_value = None
reason = no_route_threshold
```

这不是“忘记记录阈值”，而是本轮明确采用无阈值基线。

还有两个状态不能混在一起：

```text
execution_status
→ 这条路线的查询是否成功，是否产生候选

post_threshold_status
→ 查询成功后，经过阈值还剩不剩候选
```

一条路线可以是：

```text
execution_status = success
post_threshold_status = empty
```

它表示查询正常返回过候选，但候选全部低于当前准入线，不是数据库失败，也不是原始召回为 0。

## Retriever 为什么要同时返回结果与过程

最终候选给 Context Builder 使用，诊断报告解释它们怎样经过可见范围、各路候选深度、原生阈值、RRF 和最终截断。两者必须属于同一次运行，并带有能够识别控制条件的配置身份；否则应用只能看到“剩下什么”，无法解释“为什么剩下”。

## 空结果必须说明“在哪一种条件下为空”

`RetrievalResult.candidates == ()` 只能证明本轮没有最终候选，不能证明知识库客观上没有答案。

当前实现按运行事实给出五种 `NoResultReason`：

| 原因 | 这轮已经知道什么 | 优先检查什么 |
| --- | --- | --- |
| `visible_scope_empty` | 已有诊断的路线在当前范围都没有可见 Chunk | scope、角色、证据资格、索引空间、入库 Metadata |
| `no_route_match` | 有可见资料，但没有路线形成候选 | lexical 词项与 query、dense 兼容向量和召回输入 |
| `all_below_threshold` | 路线曾返回候选，但阈值后全部为空 | 原生数值、方向、阈值是否过严 |
| `route_failure` | 至少一路失败，且没有剩余最终候选 | 失败路线的 code/message，以及另一条路线为何无候选 |
| `all_routes_failed` | 所有路线都执行失败 | 数据库、migration、连接与真实依赖 |

分类顺序也很重要：

```text
只要有最终 candidates
→ no_result_reason = None

没有 candidates
→ 先判断是否全部失败
→ 再判断是否部分路线失败
→ 再看 visible scope
→ 再看原始 candidate count
→ 再看 threshold pass count
```

因此，一路失败、另一路仍返回候选时：

```text
no_result_reason = None
partial_failure = true
```

业务上有候选，不代表依赖完整成功。调用者可以决定是否展示部分结果、要求重试或整次失败，但不能丢掉 `partial_failure`。

反过来，如果 lexical 与 dense 都正常执行但全部被阈值删除，应该是 `all_below_threshold`，不能变成 `route_failure`，也不能显示成“知识中没有答案”。

## 输入错误、路线失败和实验准备失败不在同一层

调试时还要区分报告之外的失败。

### 输入契约错误

例如空 query、`candidate_k <= 0`、`final_top_k <= 0`、dense distance 阈值超出 `[0, 2]`，或者 query 与 query embedding 文本不一致。这些是调用方违反明确契约，直接抛出 `ValueError`，不应该伪装成某条路线的空结果。

### 路线执行失败

Lexical 或 dense 搜索中的 PostgreSQL 错误会映射为 `RetrievalError`。`FixedHybridRetriever` 将它转成带 `error_code`、`error_message` 的 `FAILED` route，并继续组装可诊断报告。

### Query Embedding 还没生成成功

`FixedHybridRetriever` 接收的是已经生成好的 `EmbeddingRecord`。如果真实 Embedding Provider 在这之前鉴权失败、限流或超时，Retriever 根本没有开始执行，因此不会产生 `RetrievalReport`。真实 demo 会把这种 `LLMError` 作为实验准备失败明确暴露，不会创建假向量继续运行。

这三个层次对应不同修复位置：调用参数、Retriever 路线、Embedding Provider，不能都归类为“RAG 没结果”。

## 观察报告时按控制顺序阅读

先确认数据、Query、Embedding 空间和控制配置，再依次查看 `visible → candidate → passed → fused → final` 的数量变化。候选在哪一层消失，就从那一层的输入和决策开始定位。命令、单变量对照、完整字段和调试方式见[配套实验](../labs/retriever-contract.md)。

## 一个正确候选消失时，按什么顺序定位

回到开头的 `source_channel` 规则。不要从最熟悉的参数开始调，按数据流检查。

### 1. 它属于当前可见范围吗

看两路的 `indexed_chunk_count` 与 `visible_chunk_count`，再核对该 Chunk 的 `knowledge_scope`、`source_role`、`evidence_eligibility` 和 Embedding 空间。

如果 visible 为 0，RRF 和 `final_top_k` 还没有机会处理它。

### 2. 它成为某一路 candidate 了吗

Lexical 路线检查 query terms、`tsquery`、matched count 和 `candidate_k`；dense 路线检查 query embedding、distance 排名、兼容空间和 `candidate_k`。

如果两路都没有它，问题在召回或候选深度，不在融合。

### 3. 它通过 route threshold 了吗

在 `threshold_decisions` 中按 `chunk_id` 查找。看到 `dropped_by_route_threshold` 时，先核对分数名称、方向和阈值，不要拿另一条路线的尺度解释它。

### 4. 它进入 RRF 后排第几

查看 `fusion_diagnostics` 和该候选的路线贡献。候选若只在一路较后位置出现，可能被两路共同命中的其他候选超过。

### 5. 它是否只被 `final_top_k` 截断

查看 `final_selection`。若原因是 `dropped_by_final_top_k`，增大 final 数量可能让它进入下游，但也会增加 Context 竞争；是否值得仍需评估，而不是看到正确候选就无限增大。

只有走完这五步，才能把“检索没效果”改写成一个可行动结论，例如：

```text
该 Chunk 在 after_sale 范围可见，
进入 lexical candidate rank 2，
通过 lexical 阈值，
RRF 后排第 3，
因 final_top_k=2 被截断。
```

## 一个自然边界：范围正确执行，却配置错了 scope

`missing_scope` 实验会稳定得到空可见范围。这不是为了故意损坏数据库，而是在观察一个正常配置取舍：系统忠实搜索了调用者指定的业务范围，只是该范围没有资料。

表现：

```text
indexed > 0
visible = 0
candidates = 0
no_result_reason = visible_scope_empty
```

可能原因包括：

- 调用者传错 `knowledge_scope`。
- 入库时漏写或写错业务 Metadata。
- 资料角色或证据资格与本轮过滤不一致。

验证顺序：

1. 先查看实际 config 和 `retriever_config_ref`。
2. 查询目标 Chunk 保存的 Metadata 与索引空间。
3. 分别检查 lexical、dense 的 indexed/visible 数量。
4. 使用业务上正确的 scope 做单变量对照。
5. visible 恢复后再观察 candidate、threshold 和 RRF。

不要把过滤条件直接删除来“修复”空结果。那可能让历史资料、其他业务域或不具备当前证据资格的内容进入候选，只是把范围错误变成证据边界错误。

## 确定性验证守住哪些不变量

确定性验证应守住控制顺序、两路阈值方向、各层数量、最终截断原因、空结果分类、部分失败和配置身份。它不能证明某组阈值或候选数量提高了真实检索质量；这些结论仍需要固定数据和真实依赖上的对照。

## 框架封装不了你的参数语义和诊断责任

检索框架可以把多个 Retriever、过滤、融合和 top-k 包装成一个调用。但框架不会自动知道：

- `source_role` 与 `evidence_eligibility` 的业务含义。
- lexical 和 dense 阈值为什么方向相反。
- 一路失败时产品是否允许展示部分结果。
- 空结果应该归类为范围为空、无匹配还是阈值过严。
- 哪组参数在需求评审数据上真正更好。

当前使用显式 `FixedHybridRetriever`，不是宣称手写编排永远优于框架，而是让第一阶段的固定顺序、状态和报告先成为稳定契约。以后替换底层实现时，仍需要保留这些可观察事实。

它也不是 Agent：查询流程由应用预先固定，模型没有选择检索路线、改写 query 或决定是否再次检索。

## 学完后的自检

不看正文，尝试回答：

1. 为什么 Metadata Filter 必须在每路排序和 `candidate_k` 之前执行？
2. `candidate_k=3` 与 `final_top_k=3` 为什么不是同一个控制？
3. lexical 和 dense 为什么不能共用一个“0.7 相关度阈值”？
4. `execution_status=success`、`post_threshold_status=empty` 表示什么？
5. `indexed=10, visible=6, candidate=3, passed=0` 应先检查哪一层？
6. 为什么 dense 没有照搬 lexical 的 `matched_chunk_count`？
7. 一条候选在 `final_selection` 中显示 dropped，说明前面哪些步骤已经成功见过它？
8. 为什么 Retriever 空结果不能证明知识库没有答案？
9. 一路失败、一路仍有最终候选时，`partial_failure` 与 `no_result_reason` 分别是什么？
10. Embedding Provider 在 query 向量生成阶段失败，为什么不会得到 `RetrievalReport`？
11. `retriever_config_ref` 能证明什么，不能证明什么？
12. 怎样用报告把“正确 Chunk 没找到”改写成精确的阶段结论？

如果你能根据一组 candidate、阈值和 top-k 在运行前写出每条 Chunk 的去向，运行真实单变量对照，并从报告区分范围为空、路线无匹配、全部低于阈值、路线失败和最终截断，就完成了本节目标。

## 本节真正交付到哪里

完成本节后，你已经把前面的单路检索与 RRF 组合成一个固定、可诊断的 Retriever：

```text
query + query_embedding + retriever config
→ 相同范围下的 lexical / dense candidates
→ 各路原生阈值
→ RRF
→ final_top_k
→ RetrievalResult + RetrievalReport
```

这一步交付了候选控制和失败定位，但最终候选还不是模型真正看到的 Context，更不是已经验证的证据。它没有解决：

- 多条候选怎样分配 token 预算。
- 去重、压缩和分区怎样改变最终模型输入。
- 检索排名是否代表来源权威性。
- 候选是否支持模型生成的某条风险。
- 当前参数是否在固定评估集上优于其他配置。
- 是否值得增加 Reranker。

这些问题不能靠继续增加 `RetrievalReport` 字段自动解决。完成学习动作后，回到 [标准学习路径](../learning-path.md)，由唯一课表继续组合 Context、生成和评估能力。

## 参考

- [PostgreSQL `SELECT` 官方文档](https://www.postgresql.org/docs/current/sql-select.html)
- [pgvector 官方 Filtering 说明](https://github.com/pgvector/pgvector#filtering)
