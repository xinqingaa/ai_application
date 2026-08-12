# rag_core

需求评审助手的共享 RAG package。课程正文解释机制；本 README 维护代码职责、阅读入口和运行边界。

当前实现标准学习路径 V0 步骤 8 的文档加载、确定性清洗和来源定位，步骤 9 的可回查 Chunking，步骤 10 的 Embedding 表示与成对相似度观察，步骤 11 的应用侧中文词法分析与 PostgreSQL FTS Lexical Retrieval，步骤 12 的 pgvector 持久化、exact Dense Retrieval 和按 Embedding 空间建立的 HNSW 索引，步骤 13 的应用侧 RRF，以及步骤 14 的固定 Retrieval 控制与诊断。Context 装配和可信生成尚未接入这条 RAG 数据流。

## 当前数据流

```text
FileArtifact + LoaderConfig
→ format detection
→ TXT / Markdown / DOCX / PDF parser
→ deterministic cleaning
→ KnowledgeDocument + DocumentElement[] + LoadReport
→ ChunkPolicy
→ element / fixed-window / structure-aware / parent-child
→ Chunk[] + ChunkReport
→ embed_texts / pairwise_similarity
→ EmbeddingRecord[] + SimilarityObservation[]

Chunk[]
→ LexicalAnalyzer（中文词项 + 技术标识）
→ lexical_text + lexical_config_ref
→ PostgresChunkStore.upsert_chunks
→ PostgreSQL tsvector + GIN
→ PostgresFTSRetriever.search
→ LexicalHit[] + LexicalDiagnostics

同一 Chunk[]
→ llm_core 真实 Embedding
→ EmbeddingRecord[] + EmbeddingSpace
→ PostgresVectorStore.upsert_embeddings
→ PostgreSQL vector + 当前空间 HNSW index
→ PostgresDenseRetriever.search
→ DenseHit[] + DenseDiagnostics

LexicalHit[] + DenseHit[]
→ RankedRoute("lexical") + RankedRoute("dense")
→ reciprocal_rank_fusion
→ RRFCandidate[] + RRFDiagnostics

相同 Metadata pre-filter
→ lexical / dense candidate_k
→ 各路原生分数 threshold
→ reciprocal_rank_fusion
→ final_top_k
→ RetrievalResult + RetrievalReport
```

## 代码入口

| 文件 | 职责 |
| --- | --- |
| `ingestion/models.py` | 文件、文档、元素、locator、来源角色和加载报告契约 |
| `ingestion/errors.py` | format detection、parse、cleaning、empty content 错误分层 |
| `ingestion/parsers.py` | 四种格式的结构化解析和原生位置保留 |
| `ingestion/cleaning.py` | 可说明、可测试的确定性文本规范化 |
| `ingestion/loader.py` | 文件检查、解析调度、清洗和结果组装 |
| `tests/test_ingestion.py` | 正常格式、稳定身份、来源边界和明确错误契约测试 |
| `chunking/models.py` | Chunk、来源跨度、策略和报告契约 |
| `chunking/tokenization.py` | 固定 tokenizer 下的 token 计数和字符边界切分 |
| `chunking/identity.py` | 根据文档、有效策略和来源跨度生成稳定 Chunk ID |
| `chunking/service.py` | element、fixed、structure-aware 与 parent-child 策略 |
| `tests/test_chunking.py` | 来源回查、父子关系、Metadata 与稳定身份不变量 |
| `embedding/models.py` | EmbeddingRecord、相似度度量与成对观察契约 |
| `tests/test_embedding.py` | 表示顺序、度量方向和 Embedding 空间一致性边界 |
| `lexical/models.py` | 中文词法配置、查询操作符和可重建的配置身份 |
| `lexical/analyzer.py` | NFKC、大小写、jieba 搜索模式、问句停用词和技术标识哨兵 |
| `retrieval/models.py` | LexicalHit、原生 FTS rank 与查询诊断契约 |
| `retrieval/errors.py` | 连接、鉴权、迁移、权限和数据库执行错误分层 |
| `retrieval/postgres_fts.py` | 参数化 PostgreSQL FTS 查询和词面结果组装 |
| `retrieval/postgres_chunks.py` | lexical 与 dense 共用的 Chunk 行持久化；维护原文、来源和词法表示 |
| `vector_store/models.py` | Embedding 空间身份、向量入库和 HNSW 索引报告 |
| `vector_store/postgres.py` | Chunk 向量入库、按空间建立 HNSW partial index 和删除 |
| `retrieval/postgres_dense.py` | pgvector cosine distance、exact / HNSW 查询、可见范围和查询计划诊断 |
| `retrieval/fusion.py` | 路由状态、统一排名候选、RRF 贡献、稳定去重与融合诊断 |
| `retrieval/hybrid.py` | 固定预过滤、每路候选与阈值、RRF、最终截断和无结果诊断 |
| `tests/test_lexical.py` | 词法策略、标识符、配置身份和空输入契约 |
| `tests/test_postgres_fts.py` | Retriever 输入契约和可选真实 PostgreSQL 集成测试 |
| `tests/test_pgvector_dense.py` | Chunk/向量绑定、空间身份、距离方向和可选真实 pgvector 集成测试 |
| `tests/test_rrf.py` | 名次融合、空/失败路线、稳定身份和跨路线一致性不变量 |
| `tests/test_hybrid_retriever.py` | 控制顺序、Metadata 传递、阈值方向、最终截断和失败分类 |

建议按能力链分组阅读。步骤 8–9 运行 [`rag_ingestion_lab`](../../demos/rag_ingestion_lab/)；步骤 10–14 运行 [`rag_retrieval_lab`](../../demos/rag_retrieval_lab/)。

## 公共入口

```python
from rag_core import EvidenceEligibility, SourceRole, load_document

result = load_document(
    "rules.md",
    document_id="KR-ORDER-STATE",
    document_version="1.0.0",
    source_role=SourceRole.REFERENCE_KNOWLEDGE,
    evidence_eligibility=EvidenceEligibility.CURRENT_EVIDENCE,
)
print(result.document.elements)
print(result.report.warnings)
```

调用者提供稳定的业务 `document_id` 和 `document_version`；Loader 计算物理文件内容哈希。数据库自增 ID 和文件名都不能替代业务身份。

Loader 在读取完整字节前先通过文件状态检查 `max_file_bytes`，避免超限文件已经占用内存后才失败；读取后仍保留一次大小校验以防文件在检查与读取之间变化。

Chunking 公共入口接收完整 `KnowledgeDocument`，不重复接收一份可能与 `document.elements` 不一致的元素列表：

```python
from rag_core import ChunkPolicy, ChunkStrategy, chunk_document

result = chunk_document(
    document,
    ChunkPolicy(
        name="structure_aware",
        version="1.0.0",
        strategy=ChunkStrategy.STRUCTURE_AWARE,
        max_tokens=96,
    ),
)
```

`ChunkSourceSpan` 保存原始 `element_id`、locator 和元素内字符范围。Chunk 可以合并、截取或重复原文，但每个来源片段必须能够回到真实 `DocumentElement`。

`chunk_id` 同时包含文档身份、版本、有效策略 fingerprint、Chunk 类型、文本和来源跨度。同一输入与策略重复运行可预测；内容、版本或有效策略改变后不会复用旧 ID。数据库清理、索引迁移和 Citation 失效属于后续知识治理，不由当前模块执行。

## Embedding 表示边界

真实 Embedding HTTP 调用位于 [`llm_core.LLMClient.embed`](../llm_core/client/service.py)。`rag_core.embedding` 只负责：

- 把文本整理成带 Provider、配置、模型、维度、预处理版本和可选 `text_id` 的 `EmbeddingRecord`
- 在同一 Embedding 空间内计算 cosine / dot / Euclidean
- 产出成对 `SimilarityObservation`

它只做表示记录与成对相似度观察，不对知识库候选做匹配排名，也不持久化向量。当前 Embedding 空间身份由 Provider、配置引用、模型、维度和预处理版本共同表达；任一项变化后不得与旧记录直接比较。

```python
from rag_core import SimilarityMetric, embed_texts, pairwise_similarity

batch = embed_texts(
    ["申请售后", "发起逆向服务", "售前活动规则"],
    text_ids=["synonym_a", "synonym_b", "noise"],
    preprocessing_version="raw-v1",
)
for item in pairwise_similarity(batch.records, metric=SimilarityMetric.COSINE):
    print(item.left_id, item.right_id, round(item.score, 4))
```

## PostgreSQL FTS 公共入口

`LexicalAnalyzer` 必须以同一配置处理文档和查询。它保留重复文档词项用于词频观察，查询词项则去重；`source_channel`、`v2` 等技术标识会增加稳定的技术哨兵词，避免只依赖标点边界。

```python
from rag_core import PostgresFTSRetriever

retriever = PostgresFTSRetriever()  # 从 DATABASE_URL 读取真实 PostgreSQL
retriever.upsert_chunks(chunk_result.retrieval_chunks)
result = retriever.search("source_channel 什么时候必填？", candidate_k=5)

for hit in result.hits:
    print(hit.route_rank, hit.fts_rank, hit.chunk_id)
```

当前 FTS 使用显式 `pg_catalog.simple`、生成的 `tsvector` 列、GIN 索引和 PostgreSQL 原生 `ts_rank`。返回字段名是 `fts_rank`，方向是 higher-is-better；不能改称 BM25 score。

`lexical_config_ref` 包含名称、版本和所有影响文档/查询共同词项空间的配置 fingerprint。jieba 模式、领域词、停用词或 PostgreSQL text search config 变化时身份都会改变，旧行不会与新查询静默混用，调用者需要重新入库。查询 AND/OR 不改变已存词项，因此进入独立 `retriever_config_ref`，切换时需要记录实验配置但不需要重建文档索引。

完整 migration 和数据库运行方式由 [`review_assistant/README.md`](../../../review_assistant/README.md) 维护。package 不自动建表、不自动执行 migration，也不在 PostgreSQL 失败后回退到 SQLite 或内存搜索。

## pgvector 与 Dense Retrieval 公共入口

向量入库继续使用 `llm_core` 的真实 Embedding 调用，不在 `rag_core` 内维护第二套 Provider。`EmbeddingSpace` 由 Provider、配置引用、模型、维度和预处理版本共同确定；这些字段任一变化都会产生新的 `space_ref`。

```python
from rag_core import (
    PostgresChunkStore,
    PostgresVectorStore,
    embed_texts,
)

PostgresChunkStore().upsert_chunks(chunks)
batch = embed_texts(
    [chunk.text for chunk in chunks],
    text_ids=[chunk.chunk_id for chunk in chunks],
    preprocessing_version="retrieval-text-v1",
)
report = PostgresVectorStore().upsert_embeddings(chunks, batch.records)
```

查询文本必须使用兼容的 Embedding 空间。默认 exact 路线计算当前可见范围内的真实 cosine distance；返回字段明确命名为 `cosine_distance` 且 `lower_is_better=true`，不会与第 10 步的 cosine similarity 或第 11 步的 `fts_rank` 混写成通用 `score`。

HNSW 索引不是 migration 中的固定 1536 维索引。`ensure_hnsw_index` 根据真实运行得到的维度和 `space_ref` 创建 expression + partial index，避免把同维度但模型或预处理不同的向量放进一个索引空间。小 fixture 上 PostgreSQL 可能仍选择顺序扫描；`inspect_plan=True` 会返回 `index_used` 和查询计划节点，索引存在不等于本次查询使用了索引。

`rag_chunk_embeddings.embedding` 使用无固定维度的 `vector` 存储，以允许不同真实 Provider 的机制实验；每一行仍通过 `embedding_dimensions`、数据库 CHECK 和应用校验阻止维度声明不一致。当前 cosine 路线拒绝零向量。HNSW 的 `vector` 类型上限和真实服务维度不兼容时会明确失败，不自动换存储类型。

## RRF 公共入口

`lexical_ranked_route` 与 `dense_ranked_route` 将两种原生结果适配成 `RankedRoute`，保留原生字段名称、值和方向；`reciprocal_rank_fusion` 只使用 `route_rank` 计算，不归一化或相加 `fts_rank` 与 cosine distance。

```python
fused = reciprocal_rank_fusion(
    (
        lexical_ranked_route(lexical_result),
        dense_ranked_route(dense_result),
    ),
    rrf_k=60,
)
```

同一路由成功 0 条使用 `EMPTY`，执行错误使用带结构化错误的 `FAILED`。RRF 会保留失败事实和其他路线候选，但是否允许部分结果成为产品成功由上层决定。融合按稳定 `chunk_id` 去重，并拒绝同一 ID 在两路对应不同来源内容。

## 固定 Retriever 公共入口

`FixedHybridRetriever` 把 Metadata 预过滤、两路 `candidate_k`、各自原生阈值、RRF 和 `final_top_k` 固定成一个调用顺序。两路阈值不共享通用相关度：PostgreSQL `fts_rank` 越大越好，pgvector cosine distance 越小越好。

```python
config = HybridRetrieverConfig(
    knowledge_scope="after_sale",
    lexical_candidate_k=5,
    dense_candidate_k=5,
    final_top_k=3,
)
result = FixedHybridRetriever(lexical, dense).retrieve(
    query,
    query_embedding,
    config=config,
)
```

`RetrievalReport` 保留每路 indexed/visible/candidate/pass 数量、原生阈值决策、融合统计、最终截断和结构化无结果原因。空检索不能证明知识中没有答案；一路失败也不能伪装成成功空结果。当前固定 Retriever 只形成候选，不负责 Context 预算或生成。

## Chunking 策略边界

| 策略 | 当前行为 | 不应推断 |
| --- | --- | --- |
| `element` | 将解析元素作为基线单元，超长元素仍按 token 上限切分 | Element 天然适合检索 |
| `fixed_window` | 在文档文本上按 token 窗口和 overlap 切分 | overlap 能理解业务关系 |
| `structure_aware` | 优先按标题节、元素和表格边界组织，必要时重复标题上下文 | 已恢复 Parser 没有提供的结构 |
| `parent_child` | section 形成 parent，较小 child 作为 retrieval unit | 父子块一定优于普通 Chunk |

当前 token 边界使用显式 `tiktoken` encoding，不在 tokenizer 不可用时静默改成字符估算。具体参数是策略配置和实验输入，不是课程固定答案。

来源事实、业务过滤字段、策略信息和运行诊断分开保存：文档身份、来源角色和证据资格是 Chunk 强类型字段；`knowledge_scope` 等进入 `business_metadata`；token 分布、重复量和来源跨度数量进入 `ChunkReport`。

## 支持边界

| 格式 | 当前保留的位置 | 明确边界 |
| --- | --- | --- |
| TXT | 连续文本块的行范围 | 默认只接受 UTF-8/UTF-8-SIG；其他编码需显式配置或转换 |
| Markdown | 源行范围、标题路径 | 当前解析标题、段落、列表和代码块；不推测渲染后页码 |
| DOCX | 段落序号、表格序号、标题路径 | 不还原复杂浮动布局、图片文字和视觉分页 |
| 文本型 PDF | 页码 | 内容流顺序可能不同于复杂版面的视觉阅读顺序 |
| 扫描 PDF | 不支持 | 返回 `pdf_text_layer_missing`，不静默调用 OCR/VLM |

清洗只规范换行、Unicode、行尾空白、外层空白和过多空行，不删除业务符号、标题、表头或否定条件。

## 错误定位

| stage | 先检查什么 |
| --- | --- |
| `format_detection` | 扩展名、文件头、大小和文件是否存在 |
| `parse` | 编码、文件损坏、加密和格式解析库 |
| `cleaning` | 确定性清洗配置与异常输入 |
| `empty_content` | 空文档、图片页或扫描 PDF 的文本层 |

主路径不返回 fake 文档，也不把失败格式当成空成功结果。

终端颜色、表格、JSON Lines 和日志级别由全仓共享的 [`app_log`](../app_log/) 负责。`rag_core` 只返回领域结果、报告和错误，不直接决定终端布局。
