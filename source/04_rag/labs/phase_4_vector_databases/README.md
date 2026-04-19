# phase_4_vector_databases - 旧版备份

> 迁移说明：第四章新的学习入口已经切换到 [source/04_rag/04_vector_databases/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/04_vector_databases/README.md)。这个目录目前只作为迁移期备份保留，等前六章替换完成后会删除。

> 下面内容保留原样，方便对照旧结构，不再推荐作为第四章主入口。

---

## 核心原则

```text
先确认 Phase 3 已经产出稳定 EmbeddedChunk -> 再看 Chroma 适配层 -> 再跑写入 / 查询 / 过滤 / 删除 -> 最后用测试确认持久化行为
```

- 在 `source/04_rag/labs/phase_4_vector_databases/` 目录下操作
- 这一章的重点不是“再加一个库名”，而是让向量第一次进入真实可维护的存储层
- 默认仍然用本地 `local_hash` embedding，所以没有 API Key 也能完成本章
- 本章需要本地安装 `chromadb`

---

## 本章定位

- 对应章节：[04_vector_databases.md](/Users/linruiqiang/work/ai_application/docs/04_rag/04_vector_databases.md)
- 本章目标：把 `EmbeddedChunk[]` 写入真实 Chroma，完成持久化、Top-K 查询、metadata 过滤和按 `document_id` 删除
- 上一章输入契约：稳定 `EmbeddedChunk[]`、稳定 `chunk_id / document_id / metadata`、稳定 query/document embedding 入口
- 输出契约：真实 `ChromaVectorStore`、持久化 collection、最小查询脚本、删除脚本、可回归测试
- 本章新增：`app/vectorstores/chroma_store.py`、`scripts/index_chroma.py`、`scripts/search_chroma.py`、`scripts/delete_document.py`、`tests/test_vectorstores.py`、`requirements.txt`
- 本章可忽略：MMR、Rerank、多路召回、完整生成链路
- 第一命令：`python scripts/index_chroma.py --reset`

---

## 项目结构

```text
phase_4_vector_databases/
├── README.md
├── requirements.txt
├── app/
│   ├── config.py
│   ├── schemas.py
│   ├── embeddings/
│   ├── vectorstores/
│   │   ├── __init__.py
│   │   └── chroma_store.py
│   └── ...
├── data/
├── scripts/
│   ├── index_chroma.py
│   ├── search_chroma.py
│   ├── delete_document.py
│   └── query_demo.py
└── tests/
    └── test_vectorstores.py
```

这一章真正新增的主角只有三块：

1. `app/vectorstores/chroma_store.py`
2. `scripts/index_chroma.py / search_chroma.py / delete_document.py`
3. `tests/test_vectorstores.py`

---

## 前置准备

### 1. 运行目录

```bash
cd source/04_rag/labs/phase_4_vector_databases
```

### 2. 安装依赖

```bash
python -m pip install -r requirements.txt
```

### 3. 当前命令

```bash
python scripts/index_chroma.py --reset
python scripts/search_chroma.py
python scripts/search_chroma.py "Where do we keep source path and chunk index metadata?" product_overview.md
python scripts/delete_document.py faq.txt
python scripts/query_demo.py
python -m unittest discover -s tests
```

### 4. 先跑哪个

建议先跑：

```bash
python scripts/index_chroma.py --reset
```

你现在最该先建立的直觉是：

- `EmbeddedChunk` 现在会被真正写进持久化存储
- `chunk_id / document_id / metadata` 不再只是“留着以后用”，而是现在就要参与查询和删除
- 第四章交付的是向量存储层，不是完整 Retriever 策略层

---

## 第 1 步：先确认第四章真正吃的输入

**对应文件**：`app/schemas.py`、`app/embeddings/vectorizer.py`、`scripts/embed_documents.py`

### 这一步要解决什么

- 第四章真正的输入不是文件，也不是原始文本，而是稳定 `EmbeddedChunk[]`
- 第三章已经把 query/document embedding 的职责边界立住了
- 第四章不能重新造一套 embedding 流程，只能复用 Phase 3 输出

### 重点观察

- `EmbeddedChunk`
- `build_embedded_chunk_corpus()`
- provider 信息是如何跟着 chunk 一起进入下一层的

---

## 第 2 步：看配置和 Chroma 适配器

**对应文件**：`app/config.py`、`app/vectorstores/chroma_store.py`

### 这一步要解决什么

- Chroma 的持久化目录和 collection 名是怎么配置的
- 为什么这一章要把写入、查询、删除都集中收束到 `vectorstores/`
- metadata 里哪些字段会被写入 Chroma，哪些字段会在读回时剥离

### 重点观察

- `ChromaVectorStoreConfig`
- `upsert()`
- `get_chunks()`
- `similarity_search()`
- `delete_by_document_id()`
- `chromadb_is_available()`

### 建议主动修改

- 改 `default_vector_collection`
- 改 `default_vector_store_batch_size`
- 故意新增一个 metadata 字段，再看 round-trip 后是否还能取回

---

## 第 3 步：看真实写入如何发生

**对应文件**：`scripts/index_chroma.py`

### 这一步要解决什么

- 写入前为什么先复用 Phase 3 的 `build_embedded_chunk_corpus()`
- Chroma 写入时为什么不能丢掉 `chunk_id / document_id`
- 为什么 `--reset` 对课程实验很重要

### 建议先跑

```bash
python scripts/index_chroma.py --reset
```

运行后重点看：

- collection 名称
- persist 目录
- 本次写入的 chunk 总数
- 当前包含哪些文档

---

## 第 4 步：看查询和 metadata 过滤

**对应文件**：`scripts/search_chroma.py`

### 这一步要解决什么

- query vector 如何真正进入 Chroma 查询
- metadata 过滤为什么属于第四章而不是第五章
- Chroma 返回结果后如何重新还原成 `SourceChunk`

### 建议先跑

```bash
python scripts/search_chroma.py
python scripts/search_chroma.py "Where do we keep source path and chunk index metadata?" product_overview.md
```

运行后重点看：

- `score`
- `filename`
- `chunk_index`
- filter 前后结果范围的变化

---

## 第 5 步：看删除和重建

**对应文件**：`scripts/delete_document.py`

### 这一步要解决什么

- 为什么删除必须基于 `document_id`
- 为什么只删 chunk 内容不够
- 为什么第四章就要建立“索引一致性”意识

### 建议先跑

```bash
python scripts/delete_document.py faq.txt
python scripts/index_chroma.py --reset
```

---

## 第 6 步：看最小 RAG 演示和测试

**对应文件**：`scripts/query_demo.py`、`tests/test_vectorstores.py`

### 这一步要解决什么

- 第四章虽然还没做 Retriever 策略，但已经可以让 `RagService` 吃到真实检索结果
- 测试锁定的不是“Chroma 名字存在”，而是持久化、查询、过滤、删除行为

### 重点观察

- `query_demo.py` 如何用最小适配器把向量查询接到 `RagService`
- `test_upsert_persists_and_reloads_chunks()`
- `test_similarity_search_prefers_relevant_chunk()`
- `test_metadata_filter_limits_results()`
- `test_delete_by_document_id_removes_every_chunk_for_that_document()`

---

## 推荐完整阅读顺序

如果你是第一次读这一章，建议严格按这个顺序：

1. `app/config.py`
2. `app/schemas.py`
3. `app/embeddings/vectorizer.py`
4. `app/vectorstores/chroma_store.py`
5. `scripts/index_chroma.py`
6. `scripts/search_chroma.py`
7. `scripts/delete_document.py`
8. `scripts/query_demo.py`
9. `tests/test_vectorstores.py`

## 建议主动修改的地方

1. 把 collection 名改掉，再重新索引，观察持久化目录里会出现什么变化。
2. 在 `search_chroma.py` 里把 `where` 换成不同 `filename`，确认 filter 真正缩小了检索范围。
3. 先删 `faq.txt`，再跑查询脚本，观察结果如何变化，再用 `--reset` 重建。

## 学完这一章后你应该能回答

- 为什么 `EmbeddedChunk[]` 还不等于可用检索系统
- 为什么 `Vector Store` 和 `Retriever` 最好拆层
- 为什么 metadata 过滤和删除要在第四章就立住
- 为什么 `document_id` 会变成后续增量更新的一致性锚点

## 当前真实进度和下一章

- 当前真实进度：第四章已经交付真实 Chroma 存储层，`query_demo.py` 也已经能吃到真实检索结果，但检索策略仍然保持最小形态
- 完成标准：能写入、查询、过滤、删除，能解释 `Vector Store` 和 `Retriever` 的职责差异
- 下一章：把当前最小查询能力封装成更清晰的 Retriever，并开始比较 `top_k / threshold / MMR` 等检索策略
