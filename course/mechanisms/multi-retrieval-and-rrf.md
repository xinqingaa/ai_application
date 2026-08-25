# 多路召回与 RRF 融合

> [第 11 步](lexical-retrieval.md)和[第 12 步](vector-store-and-pgvector.md)已经让同一批 Chunk 分别经过 PostgreSQL FTS 和 pgvector，得到 lexical 与 dense 两份排名。本节继续回答：同一个候选可能出现在两份列表里，而且顺序不同，应用怎样把它们合并成一份可解释、可追踪的候选列表？
>
> 读完后，你应该能手算一个最小融合例子，运行真实实验，并判断问题来自上游召回还是排名融合。完整命令、输出字段和排障步骤见[第 13 步操作文档](../../source/demos/rag_retrieval_lab/docs/13-rrf.md)。

## 两条路线都正常，应用却还没有最终候选

先沿用前面的“售后入口与订单状态”资料。为了只观察融合问题，下面暂时把四条业务规则抽象成 A、B、C、D 四个候选单元：

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

这两份排名只是为了建立心智模型，不是第 11、12 步固定实验的真实输出。真实 fixture 经过当前 Chunk 策略会得到两个 Chunk，而不是这里的四个候选单元；本例暂时拆细，是为了同时展示“多路重合”和“只在单路出现”两种融合输入。换一个真实模型、Chunk 策略或查询，候选数量和 dense 顺序都可能变化。

现在应用还必须回答：

1. 同时出现在两路的 Chunk B、A 是否只保留一次？
2. 只在 lexical 出现的 Chunk C 和只在 dense 出现的 Chunk D 谁排在前面？
3. 最终顺序为什么这样产生，之后还能不能回到每一路的原始结果？

这就是**排名融合**要解决的问题：它接收多条检索路线已经排好序的候选列表，再生成一份统一排名。第一阶段使用其中一种简单方法——**RRF**，全称 Reciprocal Rank Fusion，中文可理解为“倒数排名融合”。

本节只解决“已有候选怎样合并和排序”。哪些资料有资格进入每条路线、融合后最终保留几条、哪些候选进入模型，以及候选能否支持最终结论，分别由上游过滤和后续 Retriever、Context、可信生成机制负责。先不要记公式，下面先看几个更直觉的方案为什么不够。

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

一种补救思路是先把每路分数映射到可比较范围，再加权相加，这类方案叫 **Score Fusion**。例如 min-max normalization 会用当前列表的最大值和最小值把分数缩放到 `0～1`；但在很小的候选集里，新增一条极高或极低的噪声候选，就会让其他候选的缩放结果一起变化。

更可靠的 Score Fusion 需要用固定数据判断“某一路的某个分数通常代表多强的相关性”，这个过程叫分数标定；还要决定每路权重，并验证数据分布变化后是否仍然成立。这些都不是本节要新增的变量。

第一阶段先采用更简单的约束：

> 不比较两路原始分数，只比较候选在各自路线中的名次。

## Rank Fusion 到底接收什么

让同一个 query 分别进入多个检索器、得到多份候选列表，就是**多路召回**。多路召回、排名融合和重排经常被混在一起，先把它们放回数据流：

```text
同一个 query
├─→ Lexical Retriever → 一份有序候选
└─→ Dense Retriever   → 另一份有序候选

两份候选排名
→ Rank Fusion
→ 一份融合排名
```

| 动作 | 读取的信息 | 是否重新阅读候选内容 | 当前进入第一阶段主线 |
| --- | --- | --- | --- |
| Multi-retrieval | query、各检索器和知识库 | 各检索器按自己的机制读取 | lexical + dense 已进入 |
| Score Fusion | 多路已经变得可比较的原始分数 | 通常不需要 | 未进入 |
| Rank Fusion | 候选身份和每路名次 | 不需要 | 使用 RRF |
| Reranker | query 与候选内容 | 需要重新阅读二者并计算新的相关性 | 扩展实验，证明收益后再准入 |

Reranker 是召回后的二次排序器：它重新阅读 query 和候选内容，再给候选排序。RRF 不做这次内容理解，它只是 Rank Fusion 的一种，只知道：

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

因此，进入融合前的每条候选同时保留四项诊断事实：来自哪条路线、在该路线排第几、原生数值叫什么，以及这个数值应该按越大越好还是越小越好阅读。例如 lexical 可以记录“第 2 名、`postgresql_ts_rank=0.31`、越大越靠前”，dense 可以记录“第 1 名、`pgvector_cosine_distance=0.08`、越小越靠前”。

RRF 只读取 `route_rank` 做计算；原生分数用于回查上游排序。保留与参与计算是两件不同的事。

不要把这两个字段重新包装成一个含义模糊的 `score`。否则调试时很容易把“0.08”误读成很差的相似度，或者把不同配置下的数值直接比较。

## 融合前先统一候选契约

Lexical 和 dense 的原始结果结构不同，但 RRF 只需要一份最小的共同输入。每条候选必须能回答：

- 它来自哪条检索路线。
- 它指向哪个稳定 Chunk 及哪个文档版本。
- 它在本路线排第几。
- 它的原生分数或距离叫什么、方向是什么。
- 它携带的原文、来源位置、资料角色和业务范围是什么。

统一的是融合所需的这些事实，不是把两种检索器伪装成同一种算法。Lexical 仍然按词排序，dense 仍然按向量距离排序；RRF 只在它们已经各自排好序之后工作。

### `route_rank` 必须从 1 开始且连续

RRF 公式把名次直接放进分母。如果一条路线返回 `1, 2, 5`，我们无法判断 3、4 是真的存在但被隐藏，还是调用者错误地跳过了名次。

因此，交给 RRF 的每条路线都应该满足：

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

如果 lexical 和 dense 都返回 Chunk A，融合后只产生一个候选，同时保存 lexical 和 dense 两份排名贡献。

### 相同 ID 还必须是相同内容

只比较 ID 仍不够。假设 lexical 表里保存 Chunk A 的旧版本，dense 表里却把同一个 ID 指向新文本。此时继续融合会生成一个无法回答“到底引用了哪一版”的候选。

当前实现会继续核对文档及版本、原文与来源位置、资料角色与证据资格、业务 Metadata。稳定 ID 相同而这些来源事实不同，说明两路索引对“这个 Chunk 是什么”没有达成一致。

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

融合输入契约用下面三条规则守住这个区别：

| 状态 | candidates | error |
| --- | --- | --- |
| `SUCCESS` | 至少 1 条 | 不允许 |
| `EMPTY` | 必须为空 | 不允许 |
| `FAILED` | 必须为空 | 必须有 code 和 message |

RRF 可以继续融合其他成功路线，并把失败路线写入 `failed_routes`。但“算法还能产生候选”不等于“产品可以宣称完整成功”。当前真实 demo 发现任一路失败时会保留诊断并返回非零退出码，不会用单路结果冒充完整的两路融合。

## 从机制到真实实现只需要一座小桥

真实公共入口是 [`fusion.py`](../../source/packages/rag_core/retrieval/fusion.py) 中的 `reciprocal_rank_fusion`。它接收至少两条已经排好序且名称不重复的路线，以及本次 `rrf_k`，返回融合候选和诊断。

实现内部仍然只是刚才的手算过程：先校验路线和名次，再为每条候选计算倒数排名贡献；随后按稳定 Chunk 身份聚合、核对来源一致性、累加贡献、稳定排序，最后组装诊断。应用代码负责把这些不变量变成强制校验，而不是依赖调用者记住规则。

理解机制时不需要先背类名和内部字段。完整对象结构、源码调用和测试修改任务放在[第 13 步操作文档](../../source/demos/rag_retrieval_lab/docs/13-rrf.md)中。

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

融合结果不能只有一个最终列表。诊断至少要回答：本次使用哪个 `rrf_k`，每条路线是成功、空结果还是失败，每路带来了多少候选，去重后剩多少候选，其中多少候选被多路共同命中，以及哪些路线失败。

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

当前实现还会用算法版本、路由名称和 `rrf_k` 形成融合配置身份。修改 `rrf_k` 或新增路线后，即使代码入口相同，也不能把结果当作同一个融合配置。

不过它还不是完整的 Retrieval 诊断。每路 Metadata Filter、阈值淘汰、最终截断和统一无结果原因会在下一步由 `RetrievalReport` 继续承接。

## 运行真实实验前先做预测

实验复用第 11、12 步的相同资料和 `retrieval_queries.json`，调用真实 PostgreSQL、真实 Embedding 服务和 pgvector。两路还必须使用相同的 `knowledge_scope`、来源角色和证据资格，保证变化来自检索路线，而不是候选可见范围不同：

```text
order_rules.md
→ Loader + Chunker
→ 同一批可见 Chunk 写入 PostgreSQL FTS 与 pgvector
→ 同一 query、同一可见范围分别进入 lexical / dense
→ 两份各自排好序的候选列表
→ 按稳定身份合并并累加排名贡献
→ 一份融合候选与诊断
```

默认基线固定 `candidate_k=5`、`rrf_k=60` 和 exact dense，先减少近似索引带来的额外变量。运行前不要猜具体 distance 或最终名次，因为真实 Embedding 空间可能变化；先写下可以由机制推出的预测：

| Query | 先预测什么 | 重点观察什么 |
| --- | --- | --- |
| `source_channel` | lexical 应体现精确标识优势 | 强词法候选是否在融合后仍可见 |
| `发起逆向服务` | lexical 可能为空，dense 有机会补回“申请售后” | `EMPTY` 是否与 `FAILED` 分开，dense-only 候选如何获得贡献 |
| `申请售后` | 两路都有机会命中同一规则 | 重合候选是否只出现一次并获得两份贡献 |
| `售前活动入口` | dense 可能返回主题接近的售后噪声 | RRF 是否会如实保留单路或共同噪声 |

真实运行时不要只看 `RRF top`。一条结果至少要能证明五件事：

1. lexical 和 dense 是 `SUCCESS`、`EMPTY` 还是 `FAILED`。
2. 融合前每个候选在各路的 `route_rank` 是多少。
3. 每份 `reciprocal_rank` 是否符合公式，总和是否等于 `rrf_score`。
4. `postgresql_ts_rank` 和 `pgvector_cosine_distance` 是否只保留作诊断，没有参与相加。
5. 相同 `chunk_id` 是否只保留一条融合候选，同时记录两路贡献。

本节的主要对照只修改 `rrf_k`。从 60 改为 20 时，应预期：

- lexical 和 dense 的原始候选、原生分数及 `route_rank` 不变。
- `reciprocal_rank` 和 `rrf_score` 改变。
- `fusion_config_ref` 改变。
- 某些候选的融合顺序可能改变，也可能完全不变。

如果两路候选本身变了，就不能把差异只归因于 `rrf_k`。先检查是否同时更换了 Embedding 模型、query、Chunk、`candidate_k` 或 dense mode。

完整运行顺序、verbose 字段解读、手算核对、JSON 输出和排障见[第 13 步操作文档](../../source/demos/rag_retrieval_lab/docs/13-rrf.md)。切换 HNSW 或 `candidate_k` 也可以观察融合，但它们会改变上游候选，不能与“只修改 `rrf_k`”混为同一个对照。

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

先检查它是否存在于任一路的输入列表。如果两路都没有，问题发生在上游召回，不是 RRF 删除了它。

本节的 RRF 会保留所有输入候选；它不执行 threshold 或 `final_top_k`。

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

使用人工构造的排名，可以稳定验证公式只读取路线名次、重合候选得到多份贡献、空结果与失败不会混淆、重复身份和来源不一致会被拒绝。这类测试适合证明确定性算法和输入契约，却不能证明：

- 真实 lexical 找到了正确 Chunk。
- 真实 Embedding 表示了业务同义关系。
- RRF 比任一单路更好。
- 融合候选足以支持模型结论。

后四项必须分别通过真实检索实验、固定数据集和后续生成/Citation 评估获得。具体测试入口和修改任务见[第 13 步操作文档](../../source/demos/rag_retrieval_lab/docs/13-rrf.md)。

## 框架可以隐藏调用，但不能替你决定边界

一些检索框架或搜索服务可以直接组合多个 Retriever，也可能内置 RRF。它们能减少编排代码，但不会自动解决：

- 两路是否搜索同一个可见知识范围。
- 不同索引中的 `chunk_id` 是否稳定一致。
- 原生分数名称和方向是否保留。
- 空结果与路由失败是否分开。
- 新增一条高度相关的路线是否重复放大同一种信号。
- RRF 是否真的提高当前业务数据的质量。

当前项目在 `rag_core` 中显式实现应用侧 RRF，是为了先看清输入、贡献、身份和状态，而不是把某个框架写成唯一标准。以后更换实现时，这些契约和评估问题仍然存在。

## 用增加第三条路线检验理解

假设以后增加一条只匹配标题和精确标识的 `title_exact` 路线。RRF 公式不需要改写，但你必须重新判断：

1. 新路线与 lexical 是否高度相关，会不会重复放大同一种词面信号？
2. 三条路线是否仍搜索同一个可见知识范围？
3. 同一个 Chunk 在三路出现时，应该保存几份贡献？
4. 哪些诊断和融合配置身份必须变化？
5. 怎样用固定问题集证明新路线带来的收益大于噪声？

这道题检查的是机制能否扩展，不要求现在把第三条路线接入第一阶段产品。对应的代码修改题位于实验文档。

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

如果你能画出“lexical / dense 排名 → 按稳定身份聚合 → 计算每路贡献 → 形成融合候选”的数据流，手算一条真实输出中的候选，运行单变量对照，并能把“没有召回”“路线失败”和“融合排序不符合预期”分别定位，就完成了本节目标。

## 本节真正交付到哪里

完成本节后，你已经建立：

- lexical 与 dense 两路候选的统一排名契约。
- `SUCCESS`、`EMPTY`、`FAILED` 三种路线状态。
- 基于稳定 `chunk_id` 的候选合并。
- 只使用 route rank 的 RRF 计算。
- 每路贡献、原生值和方向的诊断保留。
- 可复现的融合排序和 `fusion_config_ref`。
- 使用真实 PostgreSQL、Embedding 和 pgvector 的两路融合实验。

但这份融合输出仍然只是候选，不是最终模型证据。它还没有决定：

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
