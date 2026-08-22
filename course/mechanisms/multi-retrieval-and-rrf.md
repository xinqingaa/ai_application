# 多路召回与 RRF 融合

> 这是一篇机制篇。[第 11 步](lexical-retrieval.md)和[第 12 步](vector-store-and-pgvector.md)已经让同一批 Chunk 分别经过 PostgreSQL FTS 和 pgvector，得到 lexical 与 dense 两份排名；本节继续回答：两份排名怎样合并成一份可解释、可追踪的候选列表？读完后，你应该能手算一个最小 RRF 例子，运行真实实验，并判断问题来自上游召回还是排名融合。本文只形成 `RRFResult`，不决定每路阈值、最终 `top_k`、Context 预算或证据是否足以支持结论。

## 两条路线都正常，应用却还没有最终候选

先沿用前面的“售后入口与订单状态”资料。知识库里有四个可检索 Chunk：

```text
Chunk A：售后接口 v2 必须提供 source_channel。
Chunk B：仅已支付且已完成的订单可申请售后。
Chunk C：虚拟商品不进入售后流程。
Chunk D：Flutter 客户端必须使用相同的入口可见性规则。
```

现在输入问题：

```text
申请售后入口需要满足什么条件？
```

Lexical Retrieval 和 Dense Retrieval 可能返回不同顺序：

| Lexical 排名 | 候选 | 原因 |
| ---: | --- | --- |
| 1 | Chunk B | “申请售后”词面直接命中 |
| 2 | Chunk A | 命中“售后”“接口”等词项 |
| 3 | Chunk C | 命中“售后”，但它描述的是排除条件 |

| Dense 排名 | 候选 | 原因 |
| ---: | --- | --- |
| 1 | Chunk D | “入口可见性”与问题中的“入口”语义接近 |
| 2 | Chunk B | “申请售后”与问题整体语义接近 |
| 3 | Chunk A | 接口约束与“入口需要什么条件”相关 |

这两份排名只是为了建立心智模型，不是对真实 Embedding 输出的承诺。换一个真实模型、Chunk 策略或查询，dense 顺序都可能变化。

现在应用还必须回答：

1. 同时出现在两路的 Chunk B、A 是否只保留一次？
2. 只在 lexical 出现的 Chunk C 和只在 dense 出现的 Chunk D 谁排在前面？
3. 最终顺序为什么这样产生，之后还能不能回到每一路的原始结果？

这就是排名融合要解决的问题。

## 先尝试三个直觉方案

在引入 RRF 之前，先看三个更容易想到的方案为什么不够。

### 只使用一条路线

只用 lexical，精确字段名、状态码和相同措辞通常更稳定，但“发起逆向服务”可能无法命中资料中的“申请售后”。

只用 dense，同义改写更容易被找回，但“售前活动入口”和“售后入口”也可能因为主题接近而距离很近。

这不是哪一路坏了，而是两条路线观察文本的方式不同。只选一条，就会主动放弃另一条路线的强项。

### 把两份列表首尾拼起来

如果直接执行：

```text
Lexical top 3 + Dense top 3
```

会得到：

```text
B, A, C, D, B, A
```

同一个 Chunk 重复进入 Context，不但浪费 token，也会让模型误以为重复出现代表更可靠。即使再做一次去重，结果通常仍取决于“哪条列表先拼接”，而不是两条路线共同提供的排序信号。

### 把两路原始分数相加

假设真实结果中保存：

```text
Lexical
Chunk B：fts_rank = 0.82
Chunk A：fts_rank = 0.31

Dense
Chunk D：cosine_distance = 0.08
Chunk B：cosine_distance = 0.14
```

直接相加首先没有统一方向：

```text
fts_rank             越大越靠前
cosine_distance      越小越靠前
```

即使把 distance 改写成 similarity，两个数值也不在同一尺度：

- PostgreSQL `ts_rank` 受词项、位置、查询形式和 Chunk 文本影响。
- cosine distance 属于当前 Embedding 模型和预处理形成的向量空间。
- 任一侧更换配置，原始数值的分布都可能变化。

也可以先做 min-max normalization 再相加，但小候选集的最大值和最小值很不稳定。增加一条噪声候选，就可能让其他候选的归一化分数一起变化。若要使用 Score Fusion，需要为分数标定、权重和数据分布建立额外评估证据。

V0 先采用更简单的约束：

> 不比较两路原始分数，只比较候选在各自路线中的名次。

## Rank Fusion 到底接收什么

多路召回、排名融合和重排经常被混在一起。先把它们放回数据流：

```text
同一个 query
├─→ Lexical Retriever → 一份有序候选
└─→ Dense Retriever   → 另一份有序候选

两份候选排名
→ Rank Fusion
→ 一份融合排名
```

| 动作 | 读取的信息 | 是否重新阅读候选内容 | 当前进入 V0 |
| --- | --- | --- | --- |
| Multi-retrieval | query、各检索器和知识库 | 各检索器按自己的机制读取 | lexical + dense 已进入 |
| Score Fusion | 多路经过标定的原始分数 | 通常不需要 | 未进入 |
| Rank Fusion | 候选身份和每路名次 | 不需要 | 使用 RRF |
| Reranker | query 与候选内容 | 需要重新计算相关性 | V2 先实验再准入 |

RRF 是 Rank Fusion 的一种。它不知道 Chunk B 写了什么，只知道：

```text
Chunk B 在 lexical 排第 1
Chunk B 在 dense 排第 2
```

因此，RRF 能组合排名信号，却不能修正候选文本里的事实，也不能判断某条资料是否足以支持最终结论。

## 先手算一遍 RRF

Reciprocal Rank Fusion 为候选在每条路线中的名次计算一份倒数贡献：

```text
单路贡献 = 1 / (rrf_k + route_rank)
```

同一个候选出现在多条路线时，将贡献相加：

```text
rrf_score(candidate)
= 每条命中路线的 1 / (rrf_k + route_rank)
```

为了把计算写完整，使用下面这组缩小后的候选。它仍然是手算示例，不是 demo 的固定真实输出：

```text
Lexical                       Dense
rank 1：Chunk A               rank 1：Chunk B
rank 2：Chunk B               rank 2：Chunk C
rank 3：Chunk D               rank 3：Chunk A
```

设置 `rrf_k = 60`，先算每个名次的贡献：

```text
rank 1 → 1 / 61 ≈ 0.016393
rank 2 → 1 / 62 ≈ 0.016129
rank 3 → 1 / 63 ≈ 0.015873
```

再按 `chunk_id` 汇总：

| Chunk | Lexical 贡献 | Dense 贡献 | RRF 总分 |
| --- | ---: | ---: | ---: |
| A | `1/61` | `1/63` | `0.032266` |
| B | `1/62` | `1/61` | `0.032522` |
| C | — | `1/62` | `0.016129` |
| D | `1/63` | — | `0.015873` |

最后按 RRF 分数从高到低排序：

```text
fusion rank 1：Chunk B  0.032522
fusion rank 2：Chunk A  0.032266
fusion rank 3：Chunk C  0.016129
fusion rank 4：Chunk D  0.015873
```

这个结果揭示了 RRF 的两个基本偏好：

1. 在多条路线共同出现的候选，会累积多份贡献。
2. 同样命中多路时，各路排名更靠前的候选贡献更大。

Chunk B 没有在 lexical 排第一，却因为两路都把它放在前面，最终超过了 Chunk A。Chunk C 虽然在 dense 排第二，但只获得一份贡献，所以仍排在两路共同命中的候选之后。

这里的“共同命中”只能理解为多个检索器都认为它相关，不能改写成“多个证据证明它正确”。

## `rrf_k` 不是候选数量

公式中的 `rrf_k` 是平滑常数。它与下面两个参数不是一回事：

| 参数 | 作用位置 | 决定什么 |
| --- | --- | --- |
| `candidate_k` | 每条检索路线 | 每路最多带多少候选进入后续处理 |
| `rrf_k` | RRF 公式 | 不同名次之间的贡献差距 |
| `final_top_k` | 融合之后 | 最终从融合列表中保留多少条 |

比较 rank 1 和 rank 5：

```text
rrf_k = 10
rank 1 → 1/11 ≈ 0.090909
rank 5 → 1/15 ≈ 0.066667

rrf_k = 60
rank 1 → 1/61 ≈ 0.016393
rank 5 → 1/65 ≈ 0.015385
```

`rrf_k` 较小时，名次差异更明显；较大时，前几名的单次贡献更接近，多路重合产生的累计贡献相对突出。

这仍然不能推出“越大越好”或“越小越好”。改变 `rrf_k` 只改变融合偏好，不会让 RRF 突然理解候选内容。当前 demo 默认使用 60，目的是建立可比较基线，而不是宣布 60 是所有知识库的最优值。

## 原生分数不参加公式，为什么还要保留

如果 RRF 只使用名次，似乎可以在进入融合时删除 `fts_rank` 和 cosine distance。这样做会破坏诊断链。

假设融合后 Chunk B 排第一。我们仍然需要回答：

```text
Lexical 为什么把它排第 2？
Dense 为什么把它排第 1？
它们的原生数值和方向分别是什么？
```

因此，进入融合前的统一候选同时保存：

```text
route_rank = 2
native_score_name = postgresql_ts_rank
native_score = 0.31
higher_is_better = true
```

或：

```text
route_rank = 1
native_score_name = pgvector_cosine_distance
native_score = 0.08
higher_is_better = false
```

RRF 只读取 `route_rank` 做计算；原生分数用于回查上游排序。保留与参与计算是两件不同的事。

不要把这两个字段重新包装成一个含义模糊的 `score`。否则调试时很容易把“0.08”误读成很差的相似度，或者把不同配置下的数值直接比较。

## 两路结果怎样变成同一种输入

真实代码不会直接把 `LexicalHit` 和 `DenseHit` 塞进公式。两种对象先分别经过适配：

```text
LexicalSearchResult
→ lexical_ranked_route
→ RankedRoute("lexical")

DenseSearchResult
→ dense_ranked_route
→ RankedRoute("dense")
```

它们最终都包含 `RankedCandidate`：

```text
RankedCandidate
├── chunk_id
├── document_id / document_version
├── content / source_spans
├── source_role / evidence_eligibility
├── business_metadata
├── route_rank
├── native_score_name / native_score
└── higher_is_better
```

这一步不是为了把两种检索器伪装成完全相同。统一的是融合所需的候选契约；每条路线的原生名称、数值和方向仍然保留。

### `route_rank` 必须从 1 开始且连续

RRF 公式把名次直接放进分母。如果一条路线返回 `1, 2, 5`，我们无法判断 3、4 是真的存在但被隐藏，还是调用者错误地跳过了名次。

当前 `RankedRoute` 因此要求：

```text
1, 2, 3, ..., n
```

同一路线也不能重复出现相同 `chunk_id`，否则一个检索器可以因为重复行给同一 Chunk 投两次票。

### `chunk_id` 是两路汇合的主键

两路搜索的是第 9 步建立的同一批 Chunk。应用使用稳定 `chunk_id` 判断两条命中是否指向同一个候选。

不能改用：

- 数据库行号：重建表或换存储后可能变化。
- 当前列表位置：它只是某一路的 rank。
- 文件名：一份文件包含多个 Chunk。
- 当前文本：不同 Chunk 可能恰好内容相同，文本也可能经过清洗或截断。

如果 lexical 和 dense 都返回 Chunk A，融合后只产生一个 `RRFCandidate`，其中保存两份 `RRFContribution`。

### 相同 ID 还必须是相同内容

只比较 ID 仍不够。假设 lexical 表里保存 Chunk A 的旧版本，dense 表里却把同一个 ID 指向新文本。此时继续融合会生成一个无法回答“到底引用了哪一版”的候选。

当前实现会检查同一 `chunk_id` 的：

- `document_id` 和 `document_version`。
- `content` 和 `source_spans`。
- `source_role` 和 `evidence_eligibility`。
- `business_metadata`。

任一身份事实不一致都会明确失败。这里的失败不是 RRF 质量不好，而是上游索引没有遵守稳定身份契约。

## `SUCCESS`、`EMPTY` 和 `FAILED` 是三种运行事实

从候选数量看，`EMPTY` 和 `FAILED` 都是 0 条；但它们对使用者的含义完全不同。

```text
SUCCESS
→ 查询成功完成
→ 至少有 1 条候选

EMPTY
→ 查询成功完成
→ 当前查询和范围下返回 0 条

FAILED
→ 查询没有成功完成
→ 保存 error_code 和 error_message
```

例如查询“发起逆向服务”时，资料没有相同词面，lexical 可能正常返回 `EMPTY`。这属于词法检索的自然边界。

如果数据库连接失败，lexical 也会有 0 条候选，但这时不能推断“资料中没有答案”。它必须是 `FAILED`。

`RankedRoute` 用对象约束守住这个区别：

| 状态 | candidates | error |
| --- | --- | --- |
| `SUCCESS` | 至少 1 条 | 不允许 |
| `EMPTY` | 必须为空 | 不允许 |
| `FAILED` | 必须为空 | 必须有 code 和 message |

RRF 可以继续融合其他成功路线，并把失败路线写入 `failed_routes`。但“算法还能产生候选”不等于“产品可以宣称完整成功”。当前真实 demo 发现任一路失败时会保留诊断并返回非零退出码，不会用单路结果冒充完整的两路融合。

## 把手算过程映射到真实代码

公共入口位于 `source/packages/rag_core/retrieval/fusion.py`：

```python
fused = reciprocal_rank_fusion(
    (
        lexical_ranked_route(lexical_result),
        dense_ranked_route(dense_result),
    ),
    rrf_k=60,
)
```

它接收至少两条名称不重复的 `RankedRoute`，返回 `RRFResult`：

```text
RRFResult
├── candidates: RRFCandidate[]
└── diagnostics: RRFDiagnostics
```

核心调用链可以按刚才的手算过程理解，而不需要先背源码：

```text
1. 检查 route 数量、名称和 rrf_k
2. 遍历每条路线的每个候选
3. 计算 1 / (rrf_k + route_rank)
4. 按 chunk_id 放入聚合表
5. 相同 chunk_id 先检查来源身份是否一致
6. 汇总每个候选的 contributions 和 rrf_score
7. 使用稳定规则排序并写入 fusion_rank
8. 组装候选与 diagnostics
```

聚合表可以想象成：

```text
aggregated = {
  "chunk-a": {
    candidate: Chunk A 的来源事实,
    contributions: [lexical rank 1, dense rank 3]
  },
  "chunk-b": {
    candidate: Chunk B 的来源事实,
    contributions: [lexical rank 2, dense rank 1]
  }
}
```

最终 `RRFCandidate` 不只保存总分：

```text
RRFCandidate
├── chunk_id / document identity / content / source_spans
├── contributions[]
│   ├── route_name
│   ├── route_rank
│   ├── reciprocal_rank
│   ├── native_score_name / native_score
│   └── higher_is_better
├── rrf_score
└── fusion_rank
```

所以看到融合第一名时，可以给出可检查的解释：

```text
Chunk B 融合后排第 1。
它在 lexical 排第 2，贡献 1/62；
在 dense 排第 1，贡献 1/61；
总分约为 0.032522。
fts_rank 和 cosine distance 被保留用于回查，但没有互相相加。
```

## 分数相同时为什么还要规定顺序

如果 Chunk C 只在 dense 排第 1，Chunk D 只在 lexical 排第 1，它们都会得到：

```text
1 / (rrf_k + 1)
```

没有稳定规则时，数据库返回顺序或容器遍历顺序可能让两条候选在不同运行中交换位置。这样会导致：

- 测试偶尔失败。
- 相同配置的实验结果难以比较。
- 后续 `top_k` 恰好切在同分位置时，进入 Context 的候选不稳定。

当前实现依次使用：

1. `rrf_score` 降序。
2. 命中路线数量降序。
3. 最佳 `route_rank` 升序。
4. `chunk_id` 升序。

前三项优先使用现有融合信息；最后用稳定 ID 结束并列。`chunk_id` 较小不代表内容更相关，它只负责让同分结果可以复现。

## 诊断信息怎样说明一次融合发生了什么

`RRFDiagnostics` 保存：

```text
rrf_k
fusion_config_ref
route_statuses
route_candidate_counts
distinct_candidate_count
overlap_candidate_count
failed_routes
```

假设两路各返回 3 条，其中 2 个 `chunk_id` 重合：

```text
route_candidate_counts = {lexical: 3, dense: 3}
distinct_candidate_count = 4
overlap_candidate_count = 2
```

这里的关系是：

```text
两路候选总数 6
- 重复身份带来的 2 条重复记录
= 融合后的 4 个不同候选
```

`fusion_config_ref` 由算法版本、路由名称和 `rrf_k` 共同形成。修改 `rrf_k` 或新增路线后，即使代码入口相同，也不能把结果当作同一个融合配置。

不过它还不是完整的 Retrieval 诊断。每路 Metadata Filter、阈值淘汰、最终截断和统一无结果原因会在下一步由 `RetrievalReport` 继续承接。

## 运行真实实验前先做预测

真实入口是：

```text
source/demos/rag_retrieval_lab/inspect_rrf_retrieval.py
```

实验复用第 11、12 步的相同资料和 `retrieval_queries.json`，调用真实 PostgreSQL、真实 Embedding 服务和 pgvector：

```text
order_rules.md
→ Loader + Chunker
→ 同一批 Chunk 写入 PostgreSQL FTS 与 pgvector
→ 同一 query 分别进入 lexical / dense
→ LexicalSearchResult + DenseSearchResult
→ RankedRoute("lexical") + RankedRoute("dense")
→ reciprocal_rank_fusion
→ RRFResult
```

默认使用 exact dense，目的是先减少近似索引带来的额外变量。运行命令和完整参数由 [retrieval lab 步骤 13](../../source/demos/rag_retrieval_lab/docs/13-rrf.md) 维护；最小运行方式是：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_rrf_retrieval.py --verbose
```

运行前，不要先猜具体 distance 或融合名次。真实 Embedding 空间可能变化。先写下可以由机制推出的预测：

| Query | 先预测什么 | 重点观察什么 |
| --- | --- | --- |
| `source_channel` | lexical 应体现精确标识优势 | 强词法候选是否在融合后仍可见 |
| `发起逆向服务` | lexical 可能为空，dense 有机会补回“申请售后” | `EMPTY` 是否与 `FAILED` 分开，dense-only 候选如何获得贡献 |
| `申请售后` | 两路都有机会命中同一规则 | 重合候选是否只出现一次并获得两份贡献 |
| `售前活动入口` | dense 可能返回主题接近的售后噪声 | RRF 是否会如实保留单路或共同噪声 |

## 怎样读 verbose 输出

不要只看 `RRF top`。按下面的顺序检查一条 query。

### 第一步：看两路是否真的成功

```text
routes = lexical=success:3 · dense=success:3
```

如果出现 `empty`，说明查询成功但没有候选；如果出现 `failed`，先处理错误，不能继续把候选差异解释成检索能力差异。

### 第二步：看融合前各路名次

例如一条融合记录可能显示：

```text
Route ranks = lexical:2 / dense:1
```

先回到两路原始结果确认这两个名次，而不是从 RRF 总分反推原始相关性。

### 第三步：手算一条候选

若 `rrf_k=60`：

```text
1/62 + 1/61 ≈ 0.032522
```

输出中的 `RRF` 应与贡献和一致。这一步能发现公式、route rank 或输出解释是否错位。

### 第四步：核对原生值只用于诊断

```text
postgresql_ts_rank=...
pgvector_cosine_distance=...
```

确认两种名称和方向没有被抹成通用 score，也不要尝试从它们相加得到当前 RRF 值。

### 第五步：检查身份合并

同一 `chunk_id` 在两路命中时，融合结果应只有一行，但 `Routes` 中同时出现 `lexical + dense`。若出现两行相同内容，先核对它们是否真的是同一个稳定 Chunk，而不是只凭文本外观判断。

## 做一次只改变 `rrf_k` 的对照

先保存默认运行，再执行：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_rrf_retrieval.py --rrf-k 20 --verbose
```

这次只改变 `rrf_k`，应预期：

- lexical 和 dense 的原始候选、原生分数及 `route_rank` 不变。
- `reciprocal_rank` 和 `rrf_score` 改变。
- `fusion_config_ref` 改变。
- 某些候选的融合顺序可能改变，也可能完全不变。

如果两路候选本身变了，就不能把差异只归因于 `rrf_k`。先检查是否同时更换了 Embedding 模型、query、Chunk、`candidate_k` 或 dense mode。

切换 `--dense-mode hnsw` 也有价值，但它改变了 dense 候选产生方式，研究的是“近似检索输入变化后融合怎样变化”，不再是纯粹的 RRF 参数对照。

## 一个正常 bad case：两路共同放大了噪声

假设查询是：

```text
售前活动入口
```

而候选 Chunk 描述：

```text
售后入口与订单状态
```

它们共享“入口”，主题也相邻。lexical 可能因共同词产生弱命中，dense 也可能因为“售前/售后入口”语义接近而把它排在前面。

如果这个噪声在两路都靠前，RRF 会给它两份贡献，并且可能稳定地排到融合第一。这是 RRF 忠实执行输入排名，不是公式损坏。

遇到这种现象，按数据流从前往后检查：

1. 打开完整 Chunk 和 locator，确认它是否真的与 query 无关。
2. 查看 lexical 的 query lexeme、匹配词、operator 和原生 rank。
3. 查看 dense 的 Embedding 空间、cosine distance 和 route rank。
4. 确认两路是否真的都把噪声排在前面。
5. 手算 RRF，确认融合只是累加已有排名信号。
6. 再判断应该修改 Chunk、词法分析、Metadata 范围、Embedding，还是在下一步加入各路阈值。

不要先反复调整 `rrf_k`，直到这个单一 Case 看起来正确。若根因是两路都召回了主题噪声，改变平滑常数只是在重新排列症状。

另一个自然边界是：真正相关的 Chunk 只在一条路线排得较后，而噪声 Chunk 在两路都靠前。RRF 的“重合偏好”仍可能压低正确候选。因此，RRF 是否提升整体质量必须在后续固定数据集上比较 lexical、dense 和 RRF，不能用一两个漂亮例子证明。

## 三种相似表现要分开定位

### 融合结果没有某个 Chunk

先检查它是否存在于任一路的 `RankedRoute`。如果两路都没有，问题发生在上游召回，不是 RRF 删除了它。

本节的 `reciprocal_rank_fusion` 会保留所有输入候选；它不执行 threshold 或 `final_top_k`。

### 融合结果顺序出乎预期

依次检查：

1. 每路 `route_rank`。
2. `rrf_k`。
3. 每条 `reciprocal_rank`。
4. 总和 `rrf_score`。
5. 是否触发稳定 tie-break。

不要拿 FTS rank 和 cosine distance 直接解释 RRF 总分。

### 某一路显示 0 条

先看状态：

- `EMPTY`：回查查询词、Embedding 表示、Metadata 范围和候选深度。
- `FAILED`：回查数据库、Embedding 服务、migration、配置和结构化错误。

二者都显示 0 条，但排查路径完全不同。

## 确定性测试能证明什么

`source/packages/rag_core/tests/test_rrf.py` 使用人工构造的排名验证：

- 公式只使用 `route_rank`。
- 两路重合候选得到两份贡献。
- `EMPTY` 与 `FAILED` 不会混成同一个状态。
- 同一路线不能重复出现一个 `chunk_id`。
- 同一 ID 指向不同来源内容时拒绝融合。

这些测试适合证明确定性算法和对象契约。它们不能证明：

- 真实 lexical 找到了正确 Chunk。
- 真实 Embedding 表示了业务同义关系。
- RRF 比任一单路更好。
- 融合候选足以支持模型结论。

后四项必须分别通过真实检索实验、固定数据集和后续生成/Citation 评估获得。

## 框架可以隐藏调用，但不能替你决定边界

一些检索框架或搜索服务可以直接组合多个 Retriever，也可能内置 RRF。它们能减少编排代码，但不会自动解决：

- 两路是否搜索同一个可见知识范围。
- 不同索引中的 `chunk_id` 是否稳定一致。
- 原生分数名称和方向是否保留。
- 空结果与路由失败是否分开。
- 新增一条高度相关的路线是否重复放大同一种信号。
- RRF 是否真的提高当前业务数据的质量。

当前项目在 `rag_core` 中显式实现应用侧 RRF，是为了先看清输入、贡献、身份和状态，而不是把某个框架写成唯一标准。以后更换实现时，这些契约和评估问题仍然存在。

## 亲手完成一次小改动

先不要急着增加第三条检索路线。为 `test_rrf.py` 增加一个四候选测试，使用本文的手算排名：

```text
Lexical：A(1), B(2), D(3)
Dense：  B(1), C(2), A(3)
rrf_k：  60
```

完成下面四件事：

1. 写测试前先手算 A、B、C、D 的 RRF 分数和最终顺序。
2. 断言 B 排在 A 前面，并检查 B 的两份 contribution。
3. 断言 distinct candidate 是 4、overlap candidate 是 2。
4. 把 `rrf_k` 改为 20，说明哪些值一定改变、哪些输入事实必须不变。

这项修改验证你是否真的理解“按身份聚合、按名次贡献、保留原生诊断”，而不只是会运行 demo。

完成后再考虑扩展题：增加一条 `title_exact` 路线时，RRF 公式不需要改写，但必须回答新路线是否与 lexical 高度相关、是否会重复放大词面信号，以及 `fusion_config_ref` 和固定评估集为什么必须更新。

## 学完后的自检

不看正文，尝试回答：

1. 为什么 lexical 和 dense 的原始分数不能直接相加？
2. Multi-retrieval、Rank Fusion 和 Reranker 分别读取什么？
3. 给定两份三候选排名，你能否手算每个候选的 RRF 分数？
4. `candidate_k`、`rrf_k` 与 `final_top_k` 分别在哪一层生效？
5. 原生分数不参与 RRF，为什么仍必须保留名称、值和方向？
6. 为什么必须按稳定 `chunk_id` 合并，而不能按文本或列表位置？
7. 同一 ID 在两路指向不同版本内容时，为什么应该失败？
8. `EMPTY` 与 `FAILED` 都是 0 条，为什么不能合并？
9. 两路共同命中为什么不等于证据已经正确？
10. RRF 为什么可能把两路共同的噪声排得更高？
11. 分数相同时，稳定 tie-break 解决了什么，又没有证明什么？
12. 修改 `rrf_k` 后，怎样确认实验没有同时改变上游候选？

如果你能画出 `LexicalHit / DenseHit → RankedRoute → RRFContribution → RRFCandidate` 的数据流，手算一条真实输出中的候选，运行单变量对照，并能把“没有召回”“路线失败”和“融合排序不符合预期”分别定位，就完成了本节目标。

## 本节真正交付到哪里

完成本节后，你已经建立：

- lexical 与 dense 两路候选的统一排名契约。
- `SUCCESS`、`EMPTY`、`FAILED` 三种路线状态。
- 基于稳定 `chunk_id` 的候选合并。
- 只使用 route rank 的 RRF 计算。
- 每路贡献、原生值和方向的诊断保留。
- 可复现的融合排序和 `fusion_config_ref`。
- 使用真实 PostgreSQL、Embedding 和 pgvector 的两路融合实验。

但 `RRFResult` 仍然只是融合候选，不是最终模型证据。它还没有决定：

- 哪些 Metadata 对当前请求可见。
- 每路最多召回多少候选。
- 原生阈值淘汰了谁。
- 融合后最终保留多少条。
- 空结果属于哪个原因。
- 哪些候选最终进入 Context。
- 候选内容是否支持模型结论。

这些边界不会通过继续修改 RRF 公式自动消失。完成学习动作后，回到 [标准学习路径](../learning-path.md)，由唯一课表进入后续 Retriever、Context 和可信生成机制。

## 参考

- [RRF 原始论文：Reciprocal Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods](https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf)
- [pgvector 官方 Hybrid Search 说明](https://github.com/pgvector/pgvector#hybrid-search)
- [pgvector-python 官方 RRF 示例](https://github.com/pgvector/pgvector-python/blob/master/examples/hybrid_search/rrf.py)
