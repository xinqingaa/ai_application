# Top-k、阈值、Metadata Filter 与 Retrieval 诊断

> [Lexical Retrieval](lexical-retrieval.md)、[Dense Retrieval](vector-store-and-pgvector.md)和[RRF 融合](multi-retrieval-and-rrf.md)已经让同一份“售后入口与订单状态”资料形成两路候选和一份融合排名。本节继续使用同一份资料和同一个问题“申请售后”，回答：一条候选从可检索资料走到最终结果时，会在哪个控制点被保留或淘汰，应用怎样解释它的去向？
>
> 读完后，你应该能沿 `Metadata pre-filter → route candidate_k → route threshold → RRF → final_top_k` 跟踪两个真实 Chunk，并区分正常空结果、路线失败和实验准备失败。本文不讨论 Context token 预算、Reranker，也不把示例阈值包装成产品最佳参数。完整命令、真实输出和修改任务见[配套实验](../labs/retriever-contract.md)。

## RRF 已经融合，为什么还不能直接交给 Context

前面的三节已经分别交付：

```text
第 11 节
同一个 query → PostgreSQL FTS → LexicalSearchResult

第 12 节
同一个 query → Query Embedding + pgvector → DenseSearchResult

第 13 节
两份有序候选 → 稳定 chunk_id 合并 → RRFResult
```

`RRFResult` 能解释一个候选在 lexical 和 dense 中分别排第几、贡献了多少倒数排名分数，却还没有回答完整应用中的控制问题：

- 本轮允许搜索哪些资料？
- 每条路线最多让多少候选进入融合？
- 两路原生分数方向不同，各自在哪里应用准入阈值？
- 融合后最终交给下游多少条？
- 空列表来自范围为空、路线无匹配、阈值过严，还是依赖失败？
- 这次结果使用了哪组 Retriever 配置，执行花了多久？

如果应用只返回最终 `Chunk[]`，下游只能看到“剩下什么”，无法知道“为什么剩下”。第 14 节不新增第三条检索路线，而是把第 11–13 节已经出现的过滤、候选深度、原生分数和 RRF 收束成一个固定 Retriever 契约。

## 同一份资料和同一个问题贯穿本节

本节继续使用真实 fixture [`order_rules.md`](../../source/apps/review_assistant/fixtures/rag/ingestion/order_rules.md)：

```text
# 售后入口与订单状态

## 当前订单状态规则
- 仅已支付且已完成的订单可申请售后。
- 虚拟商品不进入售后流程。

## 接口与客户端约束
- 售后接口 v2 必须提供 source_channel。
- Flutter 客户端必须使用相同的入口可见性规则。
```

当前 structure-aware Chunker 会把本轮 fixture 组织成两个真实 Chunk：

| 代号 | 真实 Chunk 内容 | 当前业务范围 |
| --- | --- | --- |
| A：订单状态规则 | “仅已支付且已完成……”和“虚拟商品不进入……” | `after_sale` |
| B：接口与客户端约束 | “售后接口 v2……”和“Flutter 客户端……” | `after_sale` |

固定问题来自 [`retrieval_queries.json`](../../source/apps/review_assistant/fixtures/rag/retrieval/retrieval_queries.json)：

```text
query_id = surface_match
query = 申请售后
dataset_version = rag-retrieval-exploration-1.0.0
```

“本轮生成两个 Chunk”不自动等于“复用数据库中只有两行”。如果旧 Chunking 身份或其他同范围资料仍留在兼容索引中，lexical 和 dense 可能看到不同数量；真实 demo 会显示本轮两个 `chunk_id` 并警告意外候选。完成单变量对照前必须先解决数据准备差异，不能把旧身份带来的变化归因于 Retriever 参数。

为什么必须固定这些输入？因为本节要观察的是控制顺序。若一边改变 Query 和资料，一边修改阈值或 top-k，就无法判断候选变化究竟来自检索输入还是控制参数。

## 先分清真实事实、机制假设和真实运行

两个真实 Chunk 足以运行当前代码，但真实 Embedding distance 会随 Provider、模型和空间身份变化，不能在课程正文中写成永久常量。下面使用三种不同证据，它们不能互相冒充：

| 层级 | 本节怎样使用 | 能证明什么 | 不能证明什么 |
| --- | --- | --- | --- |
| 真实业务事实 | `order_rules.md`、两个真实 Chunk、`surface_match` | 本节一直处理同一份资料和问题 | 某个 Provider 一定返回哪个分数 |
| 确定性机制假设 | 暂时固定两路排名、原生分数和阈值 | 控制顺序、方向和候选去向 | 真实检索质量、最佳阈值 |
| 真实运行 | PostgreSQL、真实 Embedding、pgvector 和同一 Query | 当前环境的候选、分数、状态、耗时与错误 | 所有模型和数据上的普遍结论 |

接下来的数值都属于第二层。它们只用于手算，并在确定性测试中守住同一份控制契约。真实 demo 会重新调用 Provider，输出可能与这些数值不同。

## 让两个真实 Chunk 走完五层控制

继续查询“申请售后”。为了让每一层都能手算，暂时固定下面这组机制输入：

```text
knowledge_scope = after_sale
source_roles = [reference_knowledge]
evidence_eligibilities = [current_evidence]

lexical_candidate_k = 2
dense_candidate_k = 2
lexical_min_rank = 0.20
dense_max_distance = 0.30
rrf_k = 60
final_top_k = 1
```

两路暂时假设为：

| Lexical route rank | 候选 | 假设的 `postgresql_ts_rank` |
| ---: | --- | ---: |
| 1 | A：订单状态规则 | 0.82 |
| 2 | B：接口与客户端约束 | 0.31 |

| Dense route rank | 候选 | 假设的 `pgvector_cosine_distance` |
| ---: | --- | ---: |
| 1 | A：订单状态规则 | 0.12 |
| 2 | B：接口与客户端约束 | 0.44 |

这里没有增加新资料：A、B 就是 fixture 产生的两个 Chunk。只有排名和数值是为了讲清机制而暂时固定的输入。

### 第一层：Metadata Filter 先决定谁有资格竞争

在只包含当前 fixture 身份的干净实验库中，两个 Chunk 都满足：

```text
knowledge_scope = after_sale
source_role = reference_knowledge
evidence_eligibility = current_evidence
```

所以两路都得到：

```text
indexed_chunk_count = 2
visible_chunk_count = 2
```

这一步不判断谁与“申请售后”更相关，只回答“本轮允许搜索谁”。如果同一个 Query 把 `knowledge_scope` 改为 `missing_scope`，数据库和索引仍然存在，但两个 Chunk 都不再可见：

```text
indexed = 2
visible = 0
```

这是真实 demo 能稳定观察的自然边界。当前 fixture 没有“一条可见、一条不可见”的混合 Metadata；若确定性测试临时改变其中一条的证据资格，那只是为了验证选择性过滤，不代表真实 fixture 已经这样标注。

### 第二层：每条路线只取自己的前 `candidate_k`

当前两路 `candidate_k=2`，所以 A、B 都能进入各自路线的候选池。若只把 lexical 的 `candidate_k` 改为 1：

```text
Lexical：只剩 A
Dense：仍然是 A、B
```

B 不是被 lexical 阈值删除，也不是 RRF 排低；它从未进入 lexical 交给后续处理的候选列表。之后把 `final_top_k` 调得再大，也无法恢复 B 的 lexical 路线贡献。

第 11、12 节已经使用过 `candidate_k`，本节新增的不是这个参数本身，而是明确它在统一控制链中的位置和诊断含义。

### 第三层：两路阈值在各自原生空间判断

Lexical 的 rank 越大越好，因此：

```text
postgresql_ts_rank >= lexical_min_rank
```

| 候选 | 判断 | 结果 |
| --- | --- | --- |
| A | `0.82 >= 0.20` | passed |
| B | `0.31 >= 0.20` | passed |

Dense 保存 cosine distance，越小越近，因此：

```text
pgvector_cosine_distance <= dense_max_distance
```

| 候选 | 判断 | 结果 |
| --- | --- | --- |
| A | `0.12 <= 0.30` | passed |
| B | `0.44 <= 0.30` | dropped |

阈值之后：

```text
Lexical：A(1), B(2)
Dense：  A(1)
```

B 仍然有 lexical 贡献，但它的 dense 记录不会进入 RRF。这里不能使用一个含义模糊的 `min_relevance=0.7` 同时过滤两路：第 11 节的 rank 越大越好，第 12 节的 distance 越小越好，而且二者属于不同数值空间。

如果阈值为 `None`，含义不是“忘记配置”，而是本轮明确采用无路线阈值基线。报告仍要为每条候选记录 `no_route_threshold`，使运行者知道它为什么通过。

### 第四层：RRF 只融合通过阈值的路线记录

第 13 节已经学过：RRF 只读取 `route_rank`，不直接相加 rank 和 distance。`rrf_k=60` 时：

| 候选 | 路线贡献 | RRF 分数 | fusion rank |
| --- | --- | ---: | ---: |
| A | lexical `1/61` + dense `1/61` | 0.032787 | 1 |
| B | lexical `1/62` | 0.016129 | 2 |

RRF 的输入已经不再包含 B 的 dense 记录，因此不能在融合之后才补做 dense 阈值判断。RRF 分数只表达多路名次贡献，也不是一个经过标定的统一相关度。

### 第五层：`final_top_k` 在融合后统一截断

当前 `final_top_k=1`：

| fusion rank | 候选 | 最终决定 |
| ---: | --- | --- |
| 1 | A | `selected_by_final_top_k` |
| 2 | B | `dropped_by_final_top_k` |

B 已经通过 lexical 阈值、进入 RRF 并获得 fusion rank 2，只是在最终交付时被截断。此时调整 dense 阈值不是针对真正原因；如果要让 B 进入下游，应先判断是否增加 `final_top_k`，再评估它对 Context 预算和噪声的影响。

整条链可以压缩成：

```text
同一份资料 + “申请售后”
→ visible 2
→ route candidates lexical 2 / dense 2
→ threshold passed lexical 2 / dense 1
→ fused distinct 2
→ final selected 1
```

## 五层顺序是契约，不是日志排版

### Filter 必须在排序和 `candidate_k` 之前

正确语义是：

```text
从 after_sale 的当前证据中找前 k 条
```

而不是：

```text
先从全库找前 k 条
→ 再删除不属于 after_sale 的结果
```

后过滤会让其他业务域或历史资料占据候选名额，真正可见的售后规则甚至没有进入 top-k 的机会。当前实现把相同的业务范围传给 lexical 和 dense，两路 SQL 都在排序与 `LIMIT` 前建立可见集合。

### `candidate_k` 与 `final_top_k` 控制不同池子

```text
candidate_k
→ 每条路线最多交给阈值和 RRF 多少候选

final_top_k
→ 融合后最多交给 Context Builder 多少候选
```

前者改变融合输入，后者不改变两路候选和 RRF 排名。两者都不是越大越好：太小可能漏掉有用 Chunk，太大则会增加融合和 Context 竞争；具体值需要固定 development 数据验证。

### Route threshold 必须先于 RRF

阈值读的是每路原生数值和方向，RRF 读的是阈值之后的名次列表。把阈值放到融合后，会丢失“哪一路以什么数值淘汰了候选”的含义，也容易把 RRF 分数误当统一相关度。

### `final_top_k` 必须发生在融合之后

若先从每路各选最终一条再拼接，得到的是两个局部 top 1，不是全局融合 top 1。当前配置还要求 `final_top_k > 0`，因此只要 RRF 非空，最终结果至少有一条；`fused > 0, final = 0` 只能表示实现违反契约，不能当作正常空结果。

## Metadata Filter 不是相关度，也不是权限系统

当前第一阶段使用：

| 字段 | 当前作用 | 本节值 |
| --- | --- | --- |
| `knowledge_scope` | 业务知识范围 | `after_sale` |
| `source_roles` | 资料在系统中的角色 | `reference_knowledge` |
| `evidence_eligibilities` | 当前是否允许成为证据候选 | `current_evidence` |

它们决定资料能否参加本轮搜索，不判断它与 Query 有多相关。Dense 路线还必须保证 Query 与 Chunk 向量属于同一 Embedding 空间；空间兼容性和业务可见性是两个不同约束。

第一阶段当前是固定项目，这些字段不等于租户权限或文档 ACL。未来即使增加权限，权限过滤也必须在召回前生效，但不能假装现有 `knowledge_scope` 已经实现企业权限系统。

## Retriever 必须同时返回结果与过程

最终候选供下游使用，诊断报告解释候选如何产生。当前公共契约可以理解为：

```text
RetrievalResult
├── candidates：最终选中的融合候选
└── report：同一次运行的控制过程与失败事实
```

### 路线数量不能都叫“结果数”

每条路线需要区分：

```text
indexed_chunk_count
→ 当前词法配置或 Embedding 空间中有多少已索引 Chunk

visible_chunk_count
→ Metadata 与空间约束后有多少 Chunk 可见

matched_chunk_count
→ lexical 中有多少可见 Chunk 满足 FTS 匹配

candidate_count
→ candidate_k 后返回多少路线候选

passed_threshold_count / dropped_threshold_count
→ 路线候选经过阈值后的去向
```

Lexical 有明确的 `@@` 匹配，因此能区分 matched 与 candidate。Dense exact search 会对所有兼容且可见的向量计算距离，没有同义的 FTS matched 集合，所以它的 `matched_chunk_count` 为 `None`，不能伪造一个相同字段含义。

### 每条阈值决定必须保留原始事实

只记录“B 被阈值删除”仍然不够。`ThresholdDecision` 需要保存：

```text
route_name
chunk_id
route_rank
native_score_name / native_score
higher_is_better
threshold_name / threshold_value
status / reason
```

这样才能区分“没有进入路线候选”和“进入候选后低于准入线”，也能防止用 lexical 的方向解释 dense distance。

### 路线执行状态和阈值后状态是两件事

```text
execution_status
→ 路线查询是否成功，查询后是否有候选

post_threshold_status
→ 查询成功后，阈值处理还剩不剩候选
```

一条路线可能是：

```text
execution_status = success
post_threshold_status = empty
```

它表示数据库查询成功且曾返回候选，只是候选全部被当前阈值淘汰；这不是数据库失败，也不是原始召回为 0。

## 空结果必须说明在哪种条件下为空

`candidates == ()` 只能证明本轮没有最终候选，不能证明知识库客观上没有答案。当前契约区分：

| `NoResultReason` | 已知事实 | 优先检查 |
| --- | --- | --- |
| `visible_scope_empty` | 已诊断路线在当前范围都无可见 Chunk | scope、资料角色、证据资格、空间与入库 Metadata |
| `no_route_match` | 有可见资料，但没有路线形成候选 | lexical 词项、Query Embedding、候选输入 |
| `all_below_threshold` | 路线曾返回候选，但阈值后全部为空 | 原生数值、方向和阈值 |
| `route_failure` | 至少一路失败，且没有剩余最终候选 | 失败路线及另一条路线为何无候选 |
| `all_routes_failed` | 所有路线执行失败 | PostgreSQL、migration、连接与权限 |

只要仍有最终候选，`no_result_reason` 就是 `None`。但如果某一路失败，报告还必须保留：

```text
partial_failure = true
```

“有候选”和“所有依赖完整成功”不是同一事实。调用者可以决定展示部分结果、要求重试或整次失败，但不能把部分失败隐藏成完整成功。

## 配置身份和耗时回答不同问题

`retriever_config_ref` 由候选深度、两路阈值、`rrf_k`、`final_top_k` 和 Metadata Filter 等控制配置生成。任一控制变化，配置身份都应变化。它能回答“这次使用了哪组 Retriever 控制”，但不能单独证明：

- 使用了哪一版数据集。
- 当前 Embedding Provider、模型和空间是什么。
- 结果是否命中正确来源。
- 当前参数是否优于另一组参数。

因此真实实验还要同时显示 `dataset_version`、Embedding 空间身份和 Query 身份。

路线 `latency_ms` 与总 `latency_ms` 说明时间花在哪一层，是性能诊断，不是相关度判断。一个候选排名第一不代表检索很快；一次运行很快也不代表候选正确。质量和性能需要分别记录。

## 三类失败发生在不同边界

### 输入契约错误

空 Query、`candidate_k <= 0`、`final_top_k <= 0`、dense distance 阈值超出 `[0, 2]`，或 Query 文本与 Query Embedding 文本不一致，都属于调用方违反契约。它们应直接失败，不应伪装成路线空结果。

### 路线执行失败

Lexical 或 dense 搜索中的 PostgreSQL 错误会映射成结构化 `RetrievalError`。固定 Retriever 保留失败路线的 code、message 和状态，再判断另一条路线是否仍有候选。

### Query Embedding 准备失败

Retriever 接收已经生成好的 Query Embedding。如果真实 Provider 在这之前鉴权失败、限流或超时，Retriever 尚未开始，因此不会产生 `RetrievalReport`。真实 demo 会明确退出，不会创建假向量继续运行。

确定性测试可以用受控路线结果稳定复现“全部低于阈值”和“单路失败”，证明状态分类和错误契约；它不能证明真实 PostgreSQL、Embedding 或检索质量。真实依赖失败也不能被 Mock 成功替换。

## 当前实现怎样承载这条机制

第一阶段没有引入检索编排框架。本地 `rag_core` 使用显式 `FixedHybridRetriever` 组合 PostgreSQL FTS、pgvector Dense Retrieval 和应用侧 RRF：

```text
query + query_embedding + HybridRetrieverConfig
→ 两路真实查询
→ 两路原生阈值
→ RRF
→ final_top_k
→ RetrievalResult + RetrievalReport
```

选择显式实现不是宣称框架无用，而是先让第一阶段的固定顺序、状态和诊断成为稳定公共契约。以后更换底层实现时，业务范围、空结果原因、部分失败和配置身份仍不能丢失。

它也不是 Agent：路线、顺序和停止条件都由应用预先固定，模型没有选择检索路线、改写 Query 或决定再次检索。

## 本节向 Context Engineering 交付什么

完成本节后，第 11–13 节的候选能力已经收束为：

```text
同一份售后资料 + “申请售后”
→ 固定可见范围
→ 可诊断的两路候选与阈值
→ RRF 融合
→ 最终候选 + 同次运行报告
```

这一步解决候选控制和失败定位，但最终候选仍不是模型真正看到的 Context，更不是已验证证据。它没有决定：

- 多条候选怎样分配 token 预算。
- 去重、分区和压缩怎样改变模型输入。
- 排名是否代表来源权威性。
- 候选是否支持模型生成的具体结论。
- 当前参数是否在固定评估集上更优。
- 是否值得增加 Reranker。

这些责任由后续 Context、可信生成、Citation 支持性和评估机制继续承担。

## 学完后的自检

不看正文，尝试回答：

1. 第 11–13 节分别向固定 Retriever 提供了什么？
2. 为什么第 14 节没有新增检索路线，却仍需要独立的 Retriever 契约？
3. `candidate_k` 与 `final_top_k` 为什么不能互相补救？
4. 为什么 lexical 和 dense 不能共用一个“0.7 相关度阈值”？
5. `execution_status=success, post_threshold_status=empty` 表示什么？
6. 同一个 `surface_match` 在 `missing_scope` 下得到空结果，为什么不是数据库失败？
7. 一路失败、一路仍有候选时，`partial_failure` 与 `no_result_reason` 分别是什么？
8. `retriever_config_ref` 能证明什么，不能证明什么？
9. 为什么耗时属于诊断事实，却不能证明候选质量？
10. 正文假设的分数、确定性测试和真实 Provider 输出分别能证明什么？

如果你能使用同一份资料和“申请售后”问题，在运行前写出两个 Chunk 的预期去向，再从真实报告指出候选消失在哪一层，就完成了本节目标。

## 参考

- [PostgreSQL `SELECT` 官方文档](https://www.postgresql.org/docs/current/sql-select.html)
- [pgvector 官方 Filtering 说明](https://github.com/pgvector/pgvector#filtering)
