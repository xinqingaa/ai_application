# 多路召回与 RRF 融合

> 机制篇：理解 lexical 与 dense 为什么会返回不同候选，以及应用怎样在不混加原始分数的前提下组合两份排名。
>
> 课程位置：[标准学习路径](../learning-path.md) V0 第十三步。必要前置是 [Lexical Retrieval](lexical-retrieval.md) 与 [pgvector、Dense Retrieval](vector-store-and-pgvector.md)。本文交付带每路贡献和状态的 `RRFCandidate[]`；不决定最终 `top_k`、每路阈值、统一无结果原因，也不把融合候选称为有效证据。

## 为什么已经有两条检索路线，还不能直接交给模型

第 11、12 步使用了同一组售后资料和问题。现在可能看到这样的结果：

```text
问题 A：source_channel 什么时候必填？
Lexical：接口规则排第 1
Dense：接口规则排第 2 或第 3

问题 B：哪些订单可以发起逆向服务？
Lexical：0 条，或只命中很弱的共同词
Dense：“申请售后”的状态规则排第 1
```

两条路线各自都在正常工作：

- Lexical 根据真实词项匹配，擅长字段名、状态码和相同措辞。
- Dense 根据 Embedding 距离排序，擅长同义改写，也可能把主题接近但约束相反的内容放得很近。

如果只选一条路线，就会主动放弃另一条路线的强项。如果把两份列表直接拼接，又会遇到新问题：

```text
Lexical top 5 + Dense top 5
→ 同一 Chunk 可能出现两次
→ 谁应该排前面没有规则
→ 模型上下文可能重复
→ 无法解释最终顺序来自哪一路
```

第十三步只解决：

> 怎样保留两路各自的原生排名，用稳定 `chunk_id` 合并重复候选，再形成一份可以解释来源贡献的融合排名？

完整链路先固定为：

```text
query
├→ PostgreSQL FTS → LexicalHit[]
└→ pgvector       → DenseHit[]

LexicalHit[] + DenseHit[]
→ 转为两条 RankedRoute
→ 按 chunk_id 合并
→ RRF 计算名次贡献
→ RRFCandidate[]
```

本文不会回答“最后给模型几条”“低质量候选是否淘汰”。这些属于下一步 Retriever 控制与诊断。

## 先看为什么不能直接相加原始分数

假设两路分别返回：

```text
Lexical
1. Chunk A   fts_rank = 0.82
2. Chunk B   fts_rank = 0.31

Dense
1. Chunk B   cosine_distance = 0.08
2. Chunk C   cosine_distance = 0.17
```

如果直接相加，会立即出现三个问题。

### 方向不同

```text
fts_rank：越大越靠前
cosine_distance：越小越靠前
```

`0.82 + 0.08` 没有明确的“更好”方向。

### 数值范围和分布不同

PostgreSQL `ts_rank` 的数值来自词项、位置和当前排序函数。cosine distance 来自 Embedding 空间。即使都改成“越大越好”，也不表示 `0.7` 在两条路线中具有相同强度。

### 配置变化会改变分数含义

- 词法分析、AND/OR、Chunk 长度会改变 FTS rank。
- Embedding 模型、预处理和距离函数会改变 dense distance。

如果先做 min-max normalization，再相加，小候选集中的最大值和最小值也会让归一化非常不稳定。增加一条噪声候选，其他候选的归一化分数都可能变化。

所以本项目在 V0 不做：

```text
normalize(fts_rank) + normalize(cosine_distance)
```

这不表示 Score Fusion 永远错误。它需要可靠的标定、权重和评估。V0 先选择只依赖排名位置的 RRF，减少分数空间不一致带来的混淆。

## Multi-retrieval、Fusion 和 Reranker 不是同一个动作

| 动作 | 输入 | 做什么 | V0 当前是否进入 |
| --- | --- | --- | --- |
| 多路召回 | 同一 query + 不同检索器 | 分别产生候选列表 | 是，lexical + dense |
| Score Fusion | 多路原始分数 | 标定或归一化后组合分数 | 否 |
| Rank Fusion | 多路排名 | 根据名次组合列表 | 是，RRF |
| Reranker | query + 一批候选内容 | 使用额外模型重新判断相关性 | 否，V2 先实验再准入 |

RRF 不会重新阅读 Chunk 内容。它只看到：

```text
某个 chunk_id 在 lexical 排第几
某个 chunk_id 在 dense 排第几
```

Reranker 则会再次使用 query 和候选文本计算新顺序，成本、延迟和失败面都不同。不能把 RRF 称为“重排模型”。

## RRF 的最小直觉：排名越靠前，贡献越大

Reciprocal Rank Fusion 的单路贡献是：

```text
contribution = 1 / (rrf_k + route_rank)
```

一个候选在多路出现时，把各路贡献相加：

```text
rrf_score(chunk)
= 1 / (rrf_k + lexical_rank)
+ 1 / (rrf_k + dense_rank)
```

例如使用 `rrf_k = 60`：

```text
Chunk A：lexical rank 1
score = 1 / 61 ≈ 0.016393

Chunk B：lexical rank 2 + dense rank 2
score = 1 / 62 + 1 / 62 ≈ 0.032258

Chunk C：dense rank 1
score = 1 / 61 ≈ 0.016393
```

Chunk B 虽然没有在任何一路排第一，但两路都认为它靠前，所以融合后可能排第一。

这就是 RRF 最核心的偏好：

> 多个检索器共同支持的靠前候选，通常比只在单路偶然靠前的候选更稳定。

但“共同支持”仍然只是共同认为相关，不等于事实正确或足以支撑结论。

## `rrf_k` 在控制什么

公式中的 `rrf_k` 是平滑常数，不是候选数量，也不是 `top_k`。

直观上：

- 较小的 `rrf_k`：更强调最前面的排名差异。
- 较大的 `rrf_k`：前几名之间的贡献更接近，多路重合的影响相对明显。

以 rank 1 和 rank 5 为例：

```text
rrf_k = 10
rank 1 → 1/11
rank 5 → 1/15

rrf_k = 60
rank 1 → 1/61
rank 5 → 1/65
```

不要从这个例子得出“越大越好”或“越小越好”。`rrf_k=60` 是常见基线，也是当前 demo 默认值，但它仍属于 Retriever 配置和实验变量，必须随运行记录保存。

当前 [`reciprocal_rank_fusion`](../../source/packages/rag_core/retrieval/fusion.py) 将算法版本、路由名称和 `rrf_k` 共同写入 `fusion_config_ref`。修改 `rrf_k` 后，结果不能继续冒充同一个配置版本。

## 两路先变成同一种候选契约

`LexicalHit` 与 `DenseHit` 的原生字段不同：

```text
LexicalHit.fts_rank
DenseHit.cosine_distance
```

进入融合前，它们分别通过：

```python
lexical_ranked_route(lexical_result)
dense_ranked_route(dense_result)
```

转换成 `RankedRoute`：

```text
RankedRoute
├── name
├── status
├── candidates[]
└── error（仅失败时）

RankedCandidate
├── chunk_id / document identity / content
├── source role / evidence eligibility / metadata
├── route_rank
├── native_score_name
├── native_score
└── higher_is_better
```

融合虽然不用原生分数计算 RRF，但仍保留它们用于诊断。这样学习者可以同时看到：

```text
lexical rank 2
postgresql_ts_rank = 0.31，越大越好

dense rank 1
pgvector_cosine_distance = 0.08，越小越好
```

保留不等于混加。它让最终排名可以追溯回两条原始路线。

## `chunk_id` 是两路汇合的主键

两路搜索的是同一批第 9 步 Chunk。它们必须使用稳定 `chunk_id` 判断“是不是同一个候选”。

不能使用：

- 数据库行号：不同表或重建后可能变化。
- 当前列表位置：位置只是某一路的 rank。
- 文本内容：不同 Chunk 可能内容相同，文本也可能被清洗或截断。
- 文件名：一个文件有多个 Chunk。

当前融合还会验证，同一 `chunk_id` 在不同路线中的这些内容必须一致：

- `document_id` / `document_version`。
- 原文。
- `source_role` / `evidence_eligibility`。
- `business_metadata`。

如果 lexical 看到的是旧版本内容，而 dense 看到同一 ID 下的新内容，继续融合会制造不可追踪的来源。系统应早失败，而不是选一份内容继续运行。

## 一路 0 条和一路失败必须分开

从界面上看，它们都可能表现为“这一路没有候选”，工程含义却完全不同。

### `EMPTY`

```text
查询成功
→ 数据库和检索器正常返回
→ 当前匹配条件下为 0 条
```

例如“发起逆向服务”没有足够共同词面，lexical 可能是 `EMPTY`。这是一项正常运行事实。

### `FAILED`

```text
查询没有成功完成
→ 连接、权限、migration、Embedding 或数据库执行错误
→ 不能根据 0 条推断知识中没有答案
```

当前 `RankedRoute.status` 明确区分：

```text
SUCCESS → 至少一条 candidate，没有 error
EMPTY   → 0 条 candidate，没有 error
FAILED  → 0 条 candidate，必须有 error_code 和 error_message
```

RRF 可以保留另一条成功路线的候选，同时把失败路线写入 `failed_routes`。这不表示产品应该把部分结果伪装成完整成功。第 13 步只保存事实；产品策略可以选择整次失败、显式降级或让用户重试，但失败状态不能丢失。

真实 demo 只要出现任一路失败，就会展示已有诊断并返回非零退出码，不会用单路结果宣称 RRF 成功。

## 核心调用链怎样推进

真实实验入口是 [`inspect_rrf_retrieval.py`](../../source/demos/rag_retrieval_lab/inspect_rrf_retrieval.py)：

```text
共享 Chunk + 共享 query
├→ PostgresFTSRetriever.search
│  → LexicalSearchResult
│  → lexical_ranked_route
│
└→ PostgresDenseRetriever.search
   → DenseSearchResult
   → dense_ranked_route

RankedRoute("lexical") + RankedRoute("dense")
→ reciprocal_rank_fusion
→ 按 chunk_id 聚合 contributions
→ 计算 rrf_score
→ 稳定排序
→ RRFResult
```

`RRFResult` 分为：

```text
candidates
→ 融合后的候选与每路贡献

diagnostics
→ rrf_k、配置身份、路线状态、每路数量、重合数量和失败路线
```

### 每个融合候选保留什么

```text
RRFCandidate
├── Chunk 来源与原文
├── contributions[]
│   ├── route_name
│   ├── route_rank
│   ├── reciprocal_rank
│   ├── native_score_name / value / direction
├── rrf_score
└── fusion_rank
```

读者可以解释：

```text
“这个 Chunk 融合后排第一，
因为 lexical 第 2、dense 第 2，
两路分别贡献 1/(60+2)；
不是因为把 0.31 和 0.14 相加。”
```

这就是本文要求的可解释性。

## 并列时为什么还需要稳定排序

只在单路 rank 1 出现的两个候选可能得到完全相同的 RRF score。若没有额外规则，数据库或 Python 容器顺序变化就可能让结果来回跳。

当前依次使用：

1. `rrf_score` 降序。
2. 命中路线数量降序。
3. 最佳 route rank 升序。
4. `chunk_id` 升序。

前两项表达融合偏好，最后的稳定 `chunk_id` 只负责确定性 tie-break，不表示 ID 小的内容更相关。

稳定顺序让测试、运行记录和后续评估可以复现。它不会把同分候选之间本来不存在的质量差异变成事实。

## 使用同一问题观察互补与噪声

运行方式由 [rag_retrieval_lab README](../../source/demos/rag_retrieval_lab/README.md) 维护。最小入口：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_rrf_retrieval.py
```

运行前先写下预测：

### 精确标识

```text
query：source_channel
```

观察：lexical 的强候选是否仍进入融合前列，而不是因 dense 路线存在就丢失。

### 同义改写

```text
query：发起逆向服务
```

观察：dense 是否补回“申请售后”规则；lexical `EMPTY` 是否被清晰记录，而不是标记为失败。

### 两路共同命中

```text
query：申请售后
```

观察：两路都靠前的 Chunk 是否因两份贡献在融合中上升。

### 主题噪声

```text
query：售前活动入口
```

观察：如果 dense 返回“售后入口”噪声，RRF 是否仍可能保留它。融合不是噪声过滤器。

默认实验选择 exact dense，使主要变化变量是“是否进行排名融合”。若切换 HNSW，需要把索引近似影响一起记录，不能将候选变化全部归因于 RRF。

## RRF 的真实边界：它会稳定地融合错误排名

假设 lexical 和 dense 都把一个无关 Chunk 排得很靠前：

```text
lexical rank 1：无关 Chunk X
dense rank 2：无关 Chunk X
```

RRF 会给它两路贡献，很可能把它排到融合第一。这不是公式实现错误，而是输入排名共同犯错。

排查顺序：

1. 查看 Chunk X 的完整原文和来源。
2. 查看 lexical 匹配词、operator 和原生 rank。
3. 查看 dense distance、空间和候选范围。
4. 确认两路是否真的都把 X 排前。
5. 再判断应修改词法策略、Embedding、Chunk、过滤还是后续阈值。

不应该直接把 `rrf_k` 调到某个数字，直到这个 Case 看起来正确。那会把上游召回错误伪装成融合参数问题。

另一个边界：相关 Chunk 只在一条路线排得较后，而噪声 Chunk 两路都靠前。RRF 的重合偏好可能继续压低相关 Chunk。因此第 23 步必须在固定数据集上比较 lexical、dense 与 RRF，不能用一两个漂亮例子证明融合必然提高质量。

## 确定性测试守住哪些不变量

[`test_rrf.py`](../../source/packages/rag_core/tests/test_rrf.py) 使用人工排名验证：

- RRF 只按 route rank 计算。
- 两路重合候选收到两份贡献。
- `EMPTY` 与 `FAILED` 保持不同状态。
- 单路不能重复出现同一个 `chunk_id`。
- 同一 `chunk_id` 的来源内容不一致时拒绝融合。
- 配置和稳定排序可以复现。

人工候选适合测试公式和契约，但不能证明真实检索质量。真实 lexical、真实 Embedding 与 pgvector 路线仍必须通过 demo 和后续评估运行。

## RRF 封装了什么，没有解决什么

RRF 封装：

- 把多份排名转换为倒数名次贡献。
- 按稳定身份合并重复候选。
- 产生可重复的融合顺序。

它没有解决：

- 每路查询和 Metadata 范围是否一致。
- `candidate_k` 是否足够。
- 原生阈值应该在哪里应用。
- 一路失败时产品是否允许部分结果。
- 融合后最终保留几条。
- 相关候选是否足以支持结论。
- 是否应该使用 Reranker。

因此 `RRFResult` 仍是候选层对象。下一步会把过滤、阈值、截断和无结果原因组织成完整 Retriever 契约。

## 修改题：增加第三条“标题精确匹配”路线

假设未来增加一条只检索标题和接口标识的路线：

```text
route name = title_exact
```

先回答：

1. 它输出的是原生分数还是稳定排名？
2. 是否继续使用相同 `chunk_id`？
3. 一条 Chunk 在该路由能否出现两次？
4. `fusion_config_ref` 为什么必须改变？
5. 三路共同命中是否一定应该获得三倍信任？
6. 新路线与 lexical 是否高度相关，从而重复放大同一种信号？
7. 哪些共享 Case 和评估门槛需要更新？

代码层可以增加第三个 `RankedRoute`，RRF 公式无需改写。但产品判断不能停在“代码兼容”：高度相似的两条词面路线可能重复投票，融合收益必须用固定数据证明。

## 判断是否已经掌握

不看正文，尝试回答：

1. 为什么 lexical 和 dense 的原始分数不能直接相加？
2. Multi-retrieval、Score Fusion、Rank Fusion 和 Reranker 有什么区别？
3. RRF 的输入是什么，公式使用了什么信息？
4. `rrf_k` 与 `candidate_k`、`final_top_k` 有什么区别？
5. 为什么两路都排第 2 的候选可能超过两个单路第 1？
6. 原生分数既然不参与公式，为什么仍要保留？
7. 为什么必须使用稳定 `chunk_id` 去重？
8. 同一 ID 在两路内容不一致时为什么不能继续融合？
9. `EMPTY` 与 `FAILED` 分别意味着什么？
10. RRF 为什么不会自动消除共同噪声？
11. 并列结果为什么需要稳定 tie-break？
12. 怎样证明一次改善来自 RRF，而不是换了 query、Chunk 或 dense 模式？

如果你能手算一个两路 RRF 小例子，解释每个融合候选的路线贡献，运行真实对照，并能区分融合问题和上游召回问题，就达到本节需要的掌握程度。

## 本节交付与边界

本节已经交付：

- lexical / dense 到统一 `RankedRoute` 的真实适配。
- `SUCCESS`、`EMPTY`、`FAILED` 路线状态契约。
- 基于稳定 `chunk_id` 的应用侧 RRF。
- 每路名次、倒数贡献、原生值与方向保留。
- 稳定融合排名和 `fusion_config_ref`。
- 同一 Chunk 跨路线一致性检查。
- 使用同一 Chunk、同一查询的真实 lexical / dense / RRF 实验。
- RRF 公式与不变量测试。

仍未交付：

- 每路 Metadata Filter 的统一记录。
- route threshold 和淘汰原因。
- `candidate_k` 与 `final_top_k` 的完整控制顺序。
- 统一 `RetrievalResult` / `RetrievalReport`。
- Context 适配和可信生成。
- RRF 质量提升的固定评估结论。

完成后回到 [标准学习路径](../learning-path.md)，由唯一课表决定后续内容。

## 参考

- [RRF 原始论文：Reciprocal Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods](https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf)
- [pgvector 官方 Hybrid Search 边界](https://github.com/pgvector/pgvector#hybrid-search)
- [pgvector-python 官方 RRF 示例](https://github.com/pgvector/pgvector-python/blob/master/examples/hybrid_search/rrf.py)
