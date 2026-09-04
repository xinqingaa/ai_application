# rag_retrieval_lab

这里保存固定 RAG 的可执行机制探针，不维护课程顺序和原理说明。学习时从 [标准学习路径](../../../course/learning-path.md) 进入对应实验篇。

## 入口

| 观察对象 | 程序 | 实验篇 |
| --- | --- | --- |
| Embedding 相似度 | `inspect_embedding.py` | [Embedding 与相似度](../../../course/lessons/010.embedding-and-similarity.lab.md) |
| PostgreSQL FTS | `inspect_lexical_retrieval.py` | [Lexical Retrieval](../../../course/lessons/011.lexical-retrieval.lab.md) |
| pgvector Dense Retrieval | `inspect_dense_retrieval.py` | [向量存储与 pgvector](../../../course/lessons/012.vector-store-and-pgvector.lab.md) |
| RRF 融合 | `inspect_rrf_retrieval.py` | [多路召回与 RRF](../../../course/lessons/013.multi-retrieval-and-rrf.lab.md) |
| Retriever 控制与诊断 | `inspect_retrieval_contract.py` | [Retriever 契约](../../../course/lessons/014.retriever-contract.lab.md) |
| Context 装配 | `inspect_rag_context.py` | [Context Engineering](../../../course/lessons/015.context-engineering.lab.md) |
| 结构化生成与来源声明集合检查 | `inspect_trusted_generation.py` | [来源声明集合检查](../../../course/lessons/016.trusted-generation.lab.md) |
| Citation 逐字引文定位与支持性 | `inspect_citation_support.py` | [Citation 支持性](../../../course/lessons/017.citation-support.lab.md) |
| 证据充分性、Refusal 与补充问题 | `inspect_evidence_sufficiency.py` | [证据充分性、Refusal 与补充问题](../../../course/lessons/018.evidence-sufficiency.lab.md) |

主路径使用真实 PostgreSQL、Embedding 和模型服务；缺少配置或外部服务失败时返回非零状态，不回退到 SQLite、Mock 或静态结果。数据库和 migration 准备见 [产品 README](../../apps/review_assistant/README.md#postgresql-本地准备)。SQL 展开观察见 [sql/README.md](sql/README.md)。

离线测试验证数据契约和失败边界，不证明真实检索或生成质量。具体命令、变量、观察点、调试和代码阅读路径只在对应实验篇维护。
