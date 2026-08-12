# Top-k、阈值、Metadata Filter 与 Retrieval 诊断

> 这是一篇机制篇。你已经让 lexical 和 dense 各自找候选，并用 RRF 合并排名；现在要把这些零散步骤收成一个固定 Retriever。读完后，你应该能回答：一个正确 Chunk 没进最终结果，究竟消失在哪一步？本文不讨论 Reranker，也不把某组阈值包装成永久最佳参数。

## 先追踪一个“消失的正确答案”

假设知识库确实有这条规则：

> 创建售后单时，`source_channel` 为必填字段。

用户问“逆向服务从哪个渠道发起？”，你最后却没看到这条规则。刚开始做 RAG 时，很容易直接说“检索效果不好”。但候选从数据库到模型之前，至少可能经过五次变化：

1. Metadata Filter 先决定这条资料对当前请求是否可见。
2. lexical 和 dense 各取有限数量的候选。
3. 每一路用自己的原生分数阈值删除过弱候选。
4. RRF 把两路剩余候选融合并重新排名。
5. `final_top_k` 只保留最终要交给下游的前几条。

所以“最终没看到”不是一个足够精确的诊断。我们需要的不是再猜一个参数，而是一份能回答以下问题的报告：

- 过滤前有多少已索引 Chunk，过滤后还有多少可见 Chunk？
- 两路分别取了多少候选？
- 哪条候选因哪一个原生阈值被删除？
- RRF 合并后有多少不同候选？
- 哪条候选只是没进入最终 `top_k`？
- 某一路是真的空，还是执行失败？

这就是 Retriever 契约：它不仅返回候选，还要公开候选形成过程。

## 一条固定且可解释的控制顺序

本项目 V0 使用以下顺序：

```text
pre-filter
→ lexical / dense candidate_k
→ route threshold
→ RRF
→ final_top_k
→ RetrievalResult + RetrievalReport
```

顺序不是排版偏好，而是结果的一部分。例如先做 Metadata Filter，意思是 lexical 和 dense 只能在当前业务范围内竞争；若先从全库取前 5 条再过滤，某个小范围里本来相关的 Chunk 可能永远进不了候选集。

同样，`candidate_k` 和 `final_top_k` 虽然都带 `k`，职责却不同：

| 控制项 | 作用位置 | 它回答的问题 |
| --- | --- | --- |
| Metadata Filter | 每路召回前 | 当前请求允许搜索哪些资料？ |
| `lexical_candidate_k` | lexical 排名后 | lexical 最多给融合层多少候选？ |
| `dense_candidate_k` | dense 排名后 | dense 最多给融合层多少候选？ |
| route threshold | 每路候选形成后 | 该路原生分数是否达到当前准入线？ |
| RRF | 两路阈值之后 | 两个不同分数空间的排名怎样合并？ |
| `final_top_k` | 融合排名后 | 最终交给 Context Builder 几条？ |

如果把两路 `candidate_k` 都设为 1，RRF 最多只看见两条候选。事后把 `final_top_k` 从 3 调到 10，并不能找回从未进入融合层的第 2、3 名。

## Metadata Filter 是检索范围，不是检索分数

需求评审助手目前用三类字段限制可见范围：

- `knowledge_scope`：例如只搜索 `after_sale` 业务域。
- `source_roles`：例如只允许 `reference_knowledge` 进入当前路线。
- `evidence_eligibilities`：例如只把 `current_evidence` 当作当前证据。

这些字段回答“能不能参与本轮检索”，不回答“内容有多相关”。因此它们必须在 lexical 和 dense 搜索之前生效，而且两路收到相同的范围。否则会出现 lexical 搜售后资料、dense 却搜全库的隐蔽错误。

当前 PostgreSQL FTS 实现先构造 `visible` 集合，再执行 `@@` 匹配和排名；pgvector 路线也先限定同一 Embedding 空间与 Metadata，再算近邻。两路诊断都保留：

```text
indexed_chunk_count
→ visible_chunk_count
→ returned/candidate count
```

若 `indexed=40, visible=0`，先检查 scope、来源角色和证据资格。此时继续调 RRF 没有意义，因为融合层根本收不到候选。

## 阈值必须留在各自的原生分数空间

第 13 步已经避免把 lexical 的 `fts_rank` 和 dense 的 cosine distance 直接相加。第 14 步的阈值也要保持同样纪律：

- lexical 使用 `postgresql_ts_rank`，当前约定为越大越好，所以是 `rank >= lexical_min_rank`。
- dense 使用 `pgvector_cosine_distance`，越小越近，所以是 `distance <= dense_max_distance`。

“都设成 0.7”没有共同含义。一个是 PostgreSQL 排名函数的值，一个是距离；它们没有统一刻度，甚至方向相反。

所以每条阈值决策要一起记录：

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

只记录 `score=0.2, dropped=true` 不够。缺少分数名称和方向后，我们连“0.2 是太高还是太低”都无法判断。

阈值为 `None` 也不是遗漏配置。它明确表示这一轮不做该路分数淘汰，报告会记录 `no_route_threshold`。这样可以先建立无阈值基线，再一次只改变一个变量。

## 从两路结果到统一返回对象

公共入口位于 `rag_core.retrieval.hybrid.FixedHybridRetriever`：

```python
config = HybridRetrieverConfig(
    lexical_candidate_k=5,
    dense_candidate_k=5,
    lexical_min_rank=None,
    dense_max_distance=None,
    rrf_k=60,
    final_top_k=3,
    knowledge_scope="after_sale",
    source_roles=(SourceRole.REFERENCE_KNOWLEDGE,),
    evidence_eligibilities=(EvidenceEligibility.CURRENT_EVIDENCE,),
)

result = retriever.retrieve(query, query_embedding, config=config)
```

这里有两个输出层次：

- `RetrievalResult.candidates`：最终交给下游的融合候选。
- `RetrievalResult.report`：本轮范围、两路状态、阈值决策、融合诊断和最终截断。

`HybridRetrieverConfig.config_ref` 会把所有会改变结果的控制项计算成一个稳定引用。比较两次实验时，如果配置引用不同，就不应把结果变化笼统归因于“模型波动”。

核心调用链与前几步直接相连：

```text
第 8–9 步：KnowledgeDocument → Chunk
→ 第 11 步：PostgresFTSRetriever.search
→ 第 12 步：PostgresDenseRetriever.search
→ 第 13 步：reciprocal_rank_fusion
→ 第 14 步：RetrievalResult + RetrievalReport
```

`FixedHybridRetriever` 没有重新实现词法分析、向量存储或 RRF；它负责固定调用顺序和收集诊断。这样同一能力只有一个实现真源。

## 空结果不能只返回一个空列表

最终候选为空时，当前协议给出结构化原因：

| `no_result_reason` | 看到的事实 | 优先排查 |
| --- | --- | --- |
| `visible_scope_empty` | 当前 Metadata 范围内没有可见 Chunk | scope、角色、证据资格、入库 Metadata |
| `no_route_match` | 有可见 Chunk，但两路都没形成候选 | query 表示、词项、Embedding 空间、`candidate_k` 前的匹配 |
| `all_below_threshold` | 路由曾返回候选，但全部被各自阈值删除 | 原生值、方向、阈值是否过严 |
| `route_failure` | 至少一路失败，剩余路线也没给出最终候选 | 对应 route 的 error code 和 message |
| `all_routes_failed` | lexical 与 dense 都执行失败 | 数据库、migration、真实依赖与配置 |

注意：这里没有 `knowledge_has_no_answer`。Retriever 为空只能证明“按本轮范围、表示、参数和路线没有找到”，不能证明知识库客观上没有答案。要判断证据是否充分，还需要后续 Citation、Refusal 与评估机制。

`EMPTY` 与 `FAILED` 也必须分开：

- `EMPTY`：查询成功执行，只是候选为空。
- `FAILED`：数据库连接、权限、migration 或查询执行失败。

如果把失败捕获后返回 `[]`，界面会误导用户去改问题，运维也看不到真正故障。本实现会保留失败路线；即使另一条路线还有候选，报告也会标记 `partial_failure=true`，真实实验进程返回非零状态。

## 按报告定位，而不是盲调参数

回到开头那条消失的 `source_channel` 规则，可以按数据流逆向检查：

1. 看 `visible_chunk_count`。若为 0，问题发生在预过滤或入库 Metadata。
2. 看两路 `candidate_count`。可见但为 0，检查词项、query embedding、Embedding 空间和路线查询。
3. 看 `threshold_decisions`。若候选出现后被删，核对原生分数名称、方向和阈值。
4. 看 RRF 的 `distinct_candidate_count`、贡献路线与融合排名。
5. 看 `final_selection`。若理由是 `dropped_by_final_top_k`，说明检索和融合都见过它，只是最终预算没选中。

这套顺序还能避免一种常见误判：看到正确候选没进最终三条，就立刻降低 dense 阈值。若报告显示它已经通过 dense 阈值，只是在 RRF 后排第 4，那么改 dense 阈值并没有针对真正原因。

## 用同一批资料做单变量实验

真实实验入口是 `source/demos/rag_retrieval_lab/inspect_retrieval_contract.py`。它继续使用第 11–13 步相同的售后规则、查询集、真实 PostgreSQL 和真实 Embedding，不通过更换样例制造结果差异。

先运行默认的“无 route threshold”基线，再分别尝试：

- 只降低某一路 `candidate_k`，观察融合层从未见到哪些候选。
- 只增加 `lexical_min_rank`，观察词法候选的原生值和淘汰原因。
- 只降低 `dense_max_distance`，观察语义近邻被保留到什么位置。
- 只减小 `final_top_k`，确认变化只发生在融合之后。
- 改成一个不存在的 `knowledge_scope`，观察 `visible_scope_empty`。

每次记录命令、`retriever_config_ref` 和目标观察，再比较报告。不要同时改四个参数，否则即使结果变好，也无法知道是哪一个控制项起作用。

`--verbose` 会展开每条阈值和最终选择决策；JSON Lines 模式适合保存实验记录。完整命令与配置准备见 [rag_retrieval_lab README](../../source/demos/rag_retrieval_lab/README.md)。

离线测试使用构造好的 route result，只验证控制顺序、阈值方向、状态分类和 Metadata 传递等确定性契约。它不能证明真实 Embedding 质量或某组阈值适合业务；这些判断必须来自真实运行和后续固定评估集。

## 这一层解决了什么，还没解决什么

完成本步后，我们终于有一个可被下游稳定调用的 Retriever：它返回最终候选，也能解释候选在哪里发生变化。它解决的是检索控制与可观察性。

它仍然没有决定：

- 最终候选怎样在 token 预算内装进 Prompt。
- 两条重复或冲突的候选怎样选择。
- 模型生成的风险是否真的被某条来源支持。
- 当前阈值、`top_k` 和 RRF 参数是否在固定数据集上更好。
- 是否要增加 Reranker。

前两项属于 Context Construction，引用支持性和证据不足闭环在 V1，系统评估与 Reranker 准入在 V2。现在不要把 `rrf_score` 或检索排名直接当成事实权威性。

## 亲手完成一次小改动

给 `NoResultReason` 的展示层增加一组面向用户的中文说明，但不要改枚举值和诊断判断。例如把 `visible_scope_empty` 展示成“当前资料范围为空，请检查知识范围”，并保留原始机器值供日志使用。

完成后至少验证：

1. 五种原因都有稳定展示文案。
2. 未知值不会被静默显示成“知识中没有答案”。
3. 单元测试仍只证明展示映射，不声称检索质量提高。

## 学完后的自检

不看正文，尝试回答：

- 为什么 Metadata Filter 应在每路候选排名前执行？
- `candidate_k=3` 与 `final_top_k=3` 为什么不是同一个控制？
- lexical 和 dense 为什么不能共用一个“0.7 相关度阈值”？
- `visible=20, candidate=4, passed=0` 应先查哪一层？
- 为什么 Retriever 空结果不能证明知识中没有答案？
- 一路 `FAILED`、一路有候选时，为什么仍要暴露部分失败？

如果你还能运行真实实验，让一条候选分别在 route threshold 和 `final_top_k` 两处消失，并从报告准确指出原因，就完成了本节的学习目标。请回到 [标准学习路径](../learning-path.md) 继续按主线学习。
