# V0 retrieval fixtures

步骤 10 起的检索实验材料。

- `embedding_probes.json`：步骤 10 的真实 Embedding 成对相似度探针，不建立 Retriever。
- `lexical_queries.json`：步骤 11 的 PostgreSQL FTS 探索性有效业务问题，观察精确标识、词面一致、自然问句、同义改写和噪声边界。

这些材料用于机制观察，不是冻结的 V0 acceptance 数据集。步骤 11 的 Chunk 仍由 ingestion fixture 经过真实 Loader 与 Chunker 产生，不在这里复制一份平行索引数据。

`embedding_probes.json` 使用与 ingestion fixtures 相同的“售后入口与订单状态”业务域，观察同义改写、例外约束、精确标识和无关噪声在表示空间中的距离。这些分数不能代替 Dense Retrieval、词面检索或生成评估。
