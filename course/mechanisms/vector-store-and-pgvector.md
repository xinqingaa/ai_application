# pgvector、Dense Retrieval 与向量索引

> 机制篇：把Chunking 阶段的可回查 Chunk 与Embedding 阶段的真实 Embedding 连接起来，在 PostgreSQL 中完成可观察的向量检索。
>
> 课程位置：[标准学习路径](../learning-path.md)。Embedding 阶段提供 Embedding、向量和相似度的前置直觉；Lexical Retrieval提供同一批资料上的词面检索对照，但不是本节的知识前置。本文解释机制和边界，不承担实验准备、完整命令或运行排障；这些内容见[Dense Retrieval 实验篇](../labs/vector-store-and-pgvector.md)。

## 先分清两条检索路线

资料中有一句：

```text
仅已支付且已完成的订单可申请售后。
```

用户问：

```text
哪些订单可以发起逆向服务？
```

Lexical Retrieval学习的是 **Lexical Retrieval**：把资料和 Query 拆成词，按共同词项找候选。本节学习的是 **Dense Retrieval**：把资料和 Query 变成向量，按向量空间中的距离找候选。

```text
Lexical Retrieval：词项是否相同？
Dense Retrieval：表示在向量空间中是否接近？
```

Lexical Retrieval不是Dense Retrieval的知识前置；两者是两种不同的检索维度，后面的 RRF 才会把两路排名放到一起。实验可以复用Lexical Retrieval的 PostgreSQL、Chunk 和问题集，这是环境和数据的复用，不代表两节有相同的检索知识。

现在先看词面路线为什么可能返回 0 条。资料和 Query 进入检索的词可能是：

```text
资料词项：已支付 / 已完成 / 订单 / 申请 / 售后
查询词项：订单 / 发起 / 逆向 / 服务
```

“申请售后”和“发起逆向服务”表达接近的意思，但字面不同。词面检索只能使用实际出现的词，不能自己推断这两个说法相近。若同一次实验能够正常检索资料中原样出现的 `source_channel`，而同义改写没有词面命中，优先解释为 Lexical Retrieval 的能力边界，而不是数据库执行失败。

两步仍应复用同一批 Chunk 和同一组 Query。这样并排观察时，候选变化主要来自表示和匹配方式，而不是资料换了；本节不把两路原始分数放进同一个数轴。

## 成对比较还缺什么

Embedding 阶段已经可以把两段文字送进同一个 Embedding 空间，再观察它们的 cosine similarity。例如：

```text
“申请售后”       ↔ “发起逆向服务”
“申请售后”       ↔ “售前活动入口”
```

这能回答“这两对文字在表示空间中是否接近”，却还不能回答用户真正会问的问题：

```text
Query：哪些订单可以发起逆向服务？
```

资料里可能有很多 Chunk。系统不能提前知道应该比较哪一对，因此需要把 Query 和整批资料接起来：

```text
Query
→ 变成 query vector
→ 和一批 Chunk vectors 比较
→ 找出距离最近的候选
```

这就是本节新增的检索问题。它不是重新学习 Embedding，而是把Embedding 阶段的“成对观察”扩展成“对候选集合搜索”。

## 先看三件新增的事

从成对相似度到整库检索，至少多了三个动作：

1. **持久化**：Chunk 向量先生成并保存，查询时不必重新为每段资料调用模型。
2. **候选范围**：只比较当前允许检索的 Chunk，而不是随意把整张表或任意文本拿来比较。
3. **排名**：为 Query 与每个候选计算距离，按远近排序，再截取前 `candidate_k` 条。

因此最小数据流是：

```text
知识侧：Chunk.text
→ 生成 Chunk vector
→ 和 chunk_id、空间身份一起保存

查询侧：Query
→ 生成兼容的 query vector
→ 选出可见 Chunk
→ 计算 cosine distance
→ 从小到大排序
→ DenseHit[]
```

`DenseHit` 只是“这次检索返回的候选及其距离和来源身份”。它还不是最终证据，也不是答案。Dense Retrieval 不负责判断否定、版本有效性、证据充分性或最终生成。

## 先把 similarity 接到 distance

Embedding 阶段的成对实验使用 `cosine similarity`：

```text
越接近 1 → 方向越接近 → higher is closer
```

本节用 pgvector 做整库检索时，数据库使用 cosine distance 运算：

```text
cosine distance = 1 - cosine similarity
```

所以：

```text
similarity = 0.90 → distance = 0.10
similarity = 0.35 → distance = 0.65
```

在 distance 中，`0.10` 比 `0.65` 更近。当前结果刻意保留两个字段：

```text
cosine_distance   = 0.10  # lower is better
cosine_similarity = 0.90  # higher is better
```

它们只是同一个 cosine 关系的两种读法。检索按 distance 从小到大排名，诊断可以额外给出 similarity，帮助你承接Embedding 阶段的直觉。

不能把这些数与Lexical Retrieval的 `fts_rank` 相加：

```text
PostgreSQL FTS rank：词项匹配路线自己的排序值
pgvector distance：向量空间路线自己的距离值
```

两个数字来源、方向和分布都不同。后续融合会使用排名，而不是假装它们处于同一个分数空间。

## 术语沿着数据流逐个出现

先看知识侧的第一步。把 `Chunk.text` 变成固定长度的数字数组，需要调用真实的 **Embedding Provider**。它是提供 Embedding 能力的外部模型服务。Provider 只负责“文字变成向量”，不负责保存 `chunk_id`，也不决定哪些资料本轮可见。

向量生成后还要留下来，查询时才能复用。这一层叫 **Vector Store**：保存向量，并把它和 `chunk_id`、原文身份以及 Embedding 空间绑定。Store 解决“向量属于谁、属于哪个空间”，不负责判断 Query 最相关的 Chunk。

当用户 Query 到来，系统先用同一兼容空间生成 query vector，再从可见 Chunk 中计算距离、排序和截取候选。负责这段工作的对象叫 **Dense Retriever**。它返回 `DenseHit`，而不是最终答案或已验证证据。

如果 Chunk 数量变大，逐条比较全部向量会变慢。此时可以增加 **Vector Index**，让数据库更快找到可能接近的向量。当前使用 pgvector 的 HNSW 路线。索引只改变“怎样少走一些查询路径”，不会改变 Embedding 空间，也不会让模型理解“虚拟商品不进入售后”这种业务否定。

四个责任不能互相替代：Provider 失败、Store 没有向量、Retriever 过滤掉候选、Index 没有被采用，都会表现成不同的运行现象，排查位置也不同。

## pgvector：让 PostgreSQL 保存和计算向量

Lexical Retrieval已经让 PostgreSQL 保存 Chunk。Dense Retrieval增加 pgvector，让数据库能够保存向量，并在查询时计算向量之间的距离。这里的 **pgvector** 是 PostgreSQL 的扩展能力，不是 Embedding Provider，也不是另一种检索算法。

向量不只是一个浮点数组。它必须能回答“属于哪个 Chunk、来自哪个 Embedding 空间”。因此，向量存储需要同时保留 Chunk 的稳定身份和空间身份；同一个 Chunk 也可以在新空间中重新生成一份向量，而不会把旧空间悄悄覆盖成新含义。

这不是要求产品长期保留无限多旧空间。知识治理、重建和删除策略会继续演进；当前先把身份表达正确，避免新旧向量悄悄混用。

## 向量必须和 Chunk 身份绑定

向量写入时至少要守住这些不变量：

- Chunk 数量和向量记录数量一致。
- 每条向量记录都绑定正确的 `chunk_id`。
- 向量对应的文本与 Chunk 原文一致。
- 一批记录属于同一个 Embedding 空间。
- 向量真实长度与声明维度一致。
- cosine 路线不接受零向量。

任何一条不成立，都应该在入库前失败，而不是保存一批无法解释的浮点数。

尤其不能只依赖列表顺序：

```text
chunks  = [A, B]
vectors = [B 的向量, A 的向量]
```

数量完全一样，也能成功写入数据库，但以后 A 会召回 B 的语义。`text_id == chunk_id` 和原文一致性检查就是为了阻止这种“能运行但结果一直不对”的错误。

## Embedding 空间不只是维度

两组向量都是 1536 维，不代表它们可以比较。

当前最小空间身份是：

```text
provider
+ config_ref
+ model
+ dimensions
+ preprocessing_version
→ embedding_space_ref
```

应用会为这些字段生成稳定的空间身份。例如，下面任一变化都会形成新空间：

- 从模型 A 换到模型 B。
- Provider 不变，但 endpoint 背后的模型实现变化。
- 向量维度变化。
- 从“只嵌入 Chunk 原文”改成“标题 + Chunk 原文”。
- 文本清洗或截断策略升级。

query 也必须使用兼容空间：

```text
旧模型生成的 Chunk vectors
+ 新模型生成的 query vector
→ 维度可能相同
→ 数字可以计算
→ 结果没有可解释意义
```

数据库只知道浮点数组。应用必须阻止这种混用。

当前实验使用同一个 `retrieval-text-v1` 处理 Chunk 与 query，是第一阶段的明确取舍，不是所有检索系统的唯一做法。未来若 query 与 document 使用不同但经过模型明确支持的编码方式，也必须把这种关系建模成正式空间契约，不能靠调用者记忆。

## exact search：先建立正确性基线

假设当前可见范围只有四个 Chunk。最直接的方法是：

```text
query vector
→ 分别计算与 Chunk A / B / C / D 的距离
→ 对四个距离排序
→ 返回前 k 条
```

这叫 exact nearest-neighbor search。它会检查当前范围中的全部向量，因此结果是当前距离函数下的精确近邻。

如果有一百万个 Chunk，每次检查一百万条会越来越慢。但在学习和建立小型第一阶段基线时，exact 有一个非常重要的价值：

> 它是正确性基线。后面增加近似索引后，可以比较索引是否为了速度漏掉了 exact 本来能找到的候选。

(不要一开始就启用 ANN，然后看到结果不同却不知道是向量语义、过滤、索引参数还是近似召回造成的，后续会解析ANN机制)

exact 查询的机制可以概括为：先选出当前 Embedding 空间中的可见 Chunk，再计算 Query 与每个候选的 cosine distance，按距离从小到大排序，最后截取 `candidate_k` 条。数据库负责执行距离计算，应用负责决定空间身份、可见范围和返回契约。

## 先决定哪些 Chunk 有资格参加比较

需求评审助手中的 Chunk 有不同身份：

- 当前有效 Reference Knowledge。
- Historical Material。
- 不允许成为当前证据的资料。
- 不同 `knowledge_scope` 下的资料。

如果用户本轮只允许检索 `after_sale`，其他业务域不应因为向量接近就进入候选。

当前最小可见范围由 Embedding 空间、`knowledge_scope`、来源角色和证据资格共同决定：

```text
当前 Embedding 空间
+ 本轮允许的业务范围与资料身份
→ visible Chunk pool
→ distance ranking
```

这一步先回答“谁有资格参加本轮比较”，然后才谈谁更近。

实验把这三个数量缩写为 `indexed`、`visible` 和 `returned`：分别表示当前空间已有多少向量、其中有多少有资格参加比较，以及排序后实际返回多少候选。

因此，0 条结果不再只有一种解释：

```text
indexed = 0
→ 当前空间尚未入库，或 query 使用了不同空间

indexed > 0, visible = 0
→ Metadata / source role / evidence eligibility 排除了全部 Chunk

visible > 0, returned = 0
→ 继续检查查询执行或候选上限；本节没有静默阈值
```

完整 Metadata Filter、每路阈值、淘汰原因和统一无结果分类会在后续 Retriever 契约中深化。本文先让最小过滤发生在候选范围形成之前。

## 为什么 exact 以后还需要向量索引

从这里开始进入向量数据库的工程边界。先掌握 exact 作为正确性基线，再知道 HNSW 和其他近似索引解决什么问题；本节不要求你现在调完所有索引参数。

exact search 的成本会随可见向量数量增长。ANN 是 Approximate Nearest Neighbor，中文常译为“近似最近邻”。它尝试少检查一部分向量，更快找到“很可能接近”的候选。

代价是：

```text
更快
↔ 可能漏掉 exact 能找到的近邻
```

pgvector 当前常见两种 ANN 索引：

| 索引 | 直观特点 | 需要注意 |
| --- | --- | --- |
| HNSW | 建立近邻图，通常查询性能和 speed-recall 取舍较好 | 构建更慢、占用更多内存 |
| IVFFlat | 先把向量分组，查询只探测部分组 | 需要训练式分组和 `lists/probes` 调节，候选不足时召回下降 |

当前第一阶段机制实验选择 HNSW，不是宣布 HNSW 永远优于 IVFFlat，而是因为小型增量数据上可以先建立一条较少参数的索引观察路线。

## HNSW 也必须属于明确的空间

索引不能只按“向量都是 1536 维”来建立。不同模型或不同预处理方式可能使用同样的维度，却属于不同坐标系；它们不应该共享同一个近邻结构。

因此，向量索引也要和 Embedding 空间绑定。换模型或预处理后，应该形成新的空间和新的索引，而不是继续复用旧索引。维度上限等具体存储约束属于实现边界，遇到时应显式报错，不应偷偷截断向量。

## 索引存在，不等于本次查询一定使用

数据库会比较不同执行路径的成本。当前资料很少时，顺序读完几行可能比进入 HNSW 更便宜，所以实验中看到 `index_used=false` 不一定是故障。

这个现象只说明数据库这次选择了另一条更便宜的路径，不能说明 HNSW 改善了检索质量，也不能说明索引一定损坏。要证明索引有性能收益，需要更有代表性的数据量和独立的性能实验。

## ANN 与 Metadata Filter 的自然边界

在最终结果中，业务范围会限制哪些 Chunk 可见。但 ANN 索引内部可能先扫描有限的近邻，再应用这些条件。

假设 HNSW 初步检查 40 个近邻，而其中只有 10% 属于当前 `knowledge_scope`，最终可能只剩大约 4 条，即使 `candidate_k=10`。

数据库可以继续扩大扫描范围，但这仍是速度、召回、过滤比例和参数之间的取舍。

Dense Retrieval只需要建立两个判断：

- exact 是当前小数据的正确性基线。
- ANN + filter 可能少返回候选，不能看到少于 `candidate_k` 就直接认为知识中没有答案。

完整的过滤顺序、候选数量和无结果原因会在统一 Retriever 诊断中继续处理。

## 这条机制需要怎样的实现边界

当前实验把同一条机制链落在三个责任上：Chunk 继续由共享存储保存，向量由向量存储按空间写入，Dense Retriever 再用 Query vector 从可见 Chunk 中产生 `DenseHit`。真实实验入口和实现细节由Dense Retrieval 实验篇维护。

实现上还会返回诊断信息，让学习者区分“没有向量”“没有可见候选”“排名后没有返回”和“索引没有被采用”。这些字段是机制的可观察证据，不是本节需要逐个学习的接口细节。

## 用同一批问题对照两条路线

共享问题位于 [`retrieval_queries.json`](../../source/apps/review_assistant/fixtures/rag/retrieval/retrieval_queries.json)。Lexical 与 Dense 实验使用同一个文件和同一组 Chunk，不通过更换样例制造某条路线更强。

在实验中先预测，再观察同一组问题的两路结果：

| 问题 | Lexical 预测 | Dense 预测 |
| --- | --- | --- |
| `source_channel` | 精确标识强项 | 可能命中，但排名未必比 lexical 稳定 |
| `申请售后` | 词面直接命中 | 语义也应接近 |
| `发起逆向服务` | 可能因缺少共同词面而漏掉 | 有机会补回“申请售后”规则 |
| `虚拟商品 售后` | 能命中包含这些词的例外 | 也可能很近，但距离不解释否定 |
| `售前活动入口` | 可能空或出现弱词面噪声 | “售前/售后”主题接近，可能出现语义噪声 |

真实实验的准备、命令和依赖错误由[Dense Retrieval 实验篇](../labs/vector-store-and-pgvector.md)维护。正文只要求你确认主路径使用真实 Embedding 和真实 PostgreSQL；缺少 key、migration 或 extension 时，应让错误暴露，而不是用本地假结果替代。

观察时不要只看“有没有命中”，至少检查：

1. `embedding_space_ref` 是否与 Chunk 入库一致。
2. `indexed / visible / returned` 数量在哪里发生变化。
3. `cosine_distance` 的方向是否按越小越近阅读。
4. top Chunk 的原文是否真的与问题相关。
5. 精确字段、同义问题、否定问题和噪声问题分别表现怎样。
6. HNSW 是否真的被数据库采用。

## 三个结果很像，原因却完全不同

### `发起逆向服务` 在 lexical 为 0，dense 找回售后规则

这说明：

```text
两边字面不同
→ lexical 没有足够共同词项
→ Embedding 空间仍认为意思接近
→ dense 补回候选
```

它能证明两路有互补可能，不能证明 Dense 已经足够上线。还要检查其他问题、噪声、成本和延迟。

### `虚拟商品不进入售后` 距离很近

表现：例外 Chunk 可能排在前面。

这不一定是错误。用户确实在问虚拟商品和售后，它在主题上很相关。Dense Retriever 的任务是召回相关原文，不是独立完成否定推理。

后续 Context 与模型需要看到完整句子，可信生成和 Citation 校验还要继续约束结论。

### 过滤后返回 0 条

先查看：

```text
    indexed
    visible
```

如果 indexed 有值而 visible 为 0，优先检查 `knowledge_scope`、来源角色和证据资格。不要先重建向量，也不要先更换模型。

## 结果不符合预期时，沿数据流定位

不必先猜是模型问题。先沿着机制已发生的步骤排查：

```text
query 是否成功生成真实向量
→ 空间身份是否一致
→ Chunk vector 是否已入库
→ Metadata 后是否还有可见 Chunk
→ distance 和排序方向是否正确
→ ANN index 是否存在且可能被使用
→ 候选原文是否暴露语义边界
```

例如，维度不一致先查 Provider 或本地记录；`indexed=0` 先查空间和入库；`indexed>0` 但 `visible=0` 先查可见范围；`index_used=false` 先看数据规模，而不是直接重建索引。若候选语义接近却与业务约束相反，应回到完整原文判断，这是 Dense 的自然边界，不是数据库异常。

不要一看到结果差就直接调 Prompt。此时 Prompt 还没有进入链路。

## 修改题：给 Chunk 加标题再做 Embedding

需求变化：为了让短 Chunk 保留章节语义，准备把 Embedding 输入从：

```text
Chunk.text
```

改成：

```text
标题路径 + "\n" + Chunk.text
```

修改前先回答：

1. 原始 `Chunk.text` 是否应该一起改变？为什么？
2. `preprocessing_version` 是否必须升级？
3. 新向量能否继续写入旧 `embedding_space_ref`？
4. 哪些 Chunk 需要重新生成向量？
5. lexical index 是否也必须重建？
6. 共享问题集中的哪些 Case 可能改善，哪些可能因标题噪声退化？
7. 如何保留旧实验结果，避免看到新结果后才选择有利样例？

建议判断：

- 原始 Chunk 和来源定位不应为了 Embedding 前缀而被篡改。
- Embedding 输入预处理发生变化，必须升级版本并形成新空间。
- 当前资料需要重新生成向量。
- lexical 是否重建取决于 lexical_text 是否变化，不能因为 Dense 改动而机械重建全部索引。
- 是否更好必须使用相同问题集比较，不由单条同义问题决定。

这道修改题训练的是“需求变化后应该改哪一层”，不是只把字符串拼接进去让程序继续运行。

## 判断是否已经掌握

不看正文，尝试回答下面这些问题：

1. 成对 similarity 与整库 Dense Retrieval 的新增动作分别是什么？
2. Embedding Provider、Vector Store、Dense Retriever 和 Vector Index 为什么不能互相替代？
3. 为什么 Chunk 向量必须同时绑定 Chunk 身份和 Embedding 空间？
4. cosine similarity 与 cosine distance 的方向有什么不同？为什么不能和 FTS rank 直接相加？
5. exact search 为什么是近似索引的正确性基线？
6. HNSW 改善的是什么，不能改善什么？
7. 为什么同维度向量仍可能不能比较？
8. `indexed`、`visible`、`returned` 分别描述候选形成的哪一步？
9. 为什么语义接近的 Chunk 仍可能无法直接支持业务结论？
10. 哪些结论必须通过真实 Embedding 实验观察，不能由离线契约测试替代？

如果你能画出 `Chunk → Embedding → pgvector → DenseHit`，解释距离方向、空间身份、exact/HNSW 差异，并根据结果定位候选范围或空间问题，就达到本节需要的 Dense Retrieval 掌握程度。

## 本节交付与边界

本文不会证明 Dense 一定优于 Lexical，也不会把距离最近的 Chunk 直接当成正确证据。检索距离只能说明表示空间中的接近程度；证据是否充分、否定是否被正确理解、最终回答是否可信，还需要后续的融合、Context、Citation 和评估机制。

本节已经交付：

- 从 Query 到可见 Chunk 候选的 Dense Retrieval 机制。
- Chunk、向量和 Embedding 空间身份之间的绑定原则。
- cosine distance 的方向、exact 基线和 HNSW 近似路线的取舍。
- 候选范围、空间一致性和索引采用情况的观察方式。
- 与Lexical Retrieval共用资料和问题的 dense / lexical 对照。

仍未交付：

- lexical 与 dense 的 RRF 融合。
- 每路阈值、完整 Metadata Filter 和统一淘汰原因。
- 最终 `RetrievalResult` 与 `RetrievalReport`。
- Context Construction 适配。
- 结构化评审生成与 Citation Candidate。
- Citation 支持性校验和证据充分性判断。
- 固定数据集上的完整检索评估。

完成后回到 [标准学习路径](../learning-path.md)，由唯一课表决定后续内容。

## 官方参考

- [pgvector：Getting Started、距离运算符、HNSW、IVFFlat 与过滤](https://github.com/pgvector/pgvector)
- [pgvector-python：Psycopg 3 类型注册与查询](https://github.com/pgvector/pgvector-python)
- [PostgreSQL：CREATE EXTENSION](https://www.postgresql.org/docs/current/sql-createextension.html)
- [PostgreSQL：CREATE INDEX](https://www.postgresql.org/docs/current/sql-createindex.html)
