# 第一阶段 retrieval fixtures

步骤 10 起的检索实验材料。

- `embedding_probes.json`：步骤 10 的真实 Embedding 成对相似度探针，不建立 Retriever。
- `retrieval_queries.json`：步骤 11 起共享的探索性有效业务问题。步骤 11 观察 lexical，步骤 12 使用同一问题观察 dense，步骤 13 比较两路与 RRF，步骤 14 观察统一控制与淘汰原因，不为每条检索路线复制问题集。

这些材料用于机制观察，不是冻结的第一阶段 acceptance 数据集。第 11 节的 Chunk 仍由 ingestion fixture 经过真实 Loader 与 Chunker 产生，不在这里复制一份平行索引数据。

`embedding_probes.json` 使用与 ingestion fixtures 相同的“售后入口与订单状态”业务域，观察同义改写、例外约束、精确标识和无关噪声在表示空间中的距离。这些分数不能代替 Dense Retrieval、词面检索或生成评估。

`retrieval_queries.json` 的每个问题分别记录当前已落地路线的观察目标。它是机制探索材料，不是冻结的第一阶段 acceptance 数据集；观察到一个好结果不能代替后续固定评估。
