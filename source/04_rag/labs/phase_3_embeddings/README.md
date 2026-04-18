# phase_3_embeddings - 实践指南

> 本文档说明如何跟着 [学习文档](/Users/linruiqiang/work/ai_application/docs/04_rag/03_embeddings.md) 阅读第三章代码快照。

---

## 核心原则

```text
先确认 Phase 2 已经产出稳定 SourceChunk -> 再看 Provider -> 再看 SourceChunk 如何升级成 EmbeddedChunk
```

- 在 `source/04_rag/labs/phase_3_embeddings/` 目录下操作
- 这一章的重点不是“又多了几个脚本”，而是系统第一次长出了语义表示层
- 没有 API Key 也可以完整学习这一章，因为默认 provider 是本地 `local_hash`

---

## 本章定位

- 对应章节：[03_embeddings.md](/Users/linruiqiang/work/ai_application/docs/04_rag/03_embeddings.md)
- 本章目标：把 `SourceChunk[]` 变成 `EmbeddedChunk[]`，建立 provider 抽象，区分 query/document 两条向量化入口
- 上一章输入契约：稳定 `SourceChunk[]`，稳定 `chunk_id / document_id / metadata`
- 输出契约：`EmbeddedChunk[]`、`EmbeddingProvider`、`embed_documents()`、`embed_query()`、最小相似度计算能力
- 本章新增：`app/embeddings/providers.py`、`app/embeddings/vectorizer.py`、`app/embeddings/similarity.py`、`EmbeddedChunk`、`embed_documents.py`、`compare_similarity.py`
- 本章可忽略：真实向量数据库、检索策略优化、完整 RAG 生成
- 第一命令：`python scripts/embed_documents.py`

---

## 项目结构

```text
phase_3_embeddings/
├── README.md
├── app/
│   ├── config.py
│   ├── schemas.py
│   ├── embeddings/
│   │   ├── providers.py
│   │   ├── vectorizer.py
│   │   └── similarity.py
│   ├── ingestion/
│   ├── indexing/
│   └── ...
├── data/
├── scripts/
└── tests/
```

这一章真正新增的主角只有三块：

1. `app/embeddings/providers.py`
2. `app/embeddings/vectorizer.py`
3. `app/embeddings/similarity.py`

---

## 前置准备

### 1. 运行目录

```bash
cd source/04_rag/labs/phase_3_embeddings
```

### 2. 当前命令

```bash
python scripts/build_index.py
python scripts/embed_documents.py
python scripts/compare_similarity.py
python -m unittest discover -s tests
```

### 3. 先跑哪个

建议先跑：

```bash
python scripts/embed_documents.py
```

你现在最该先建立的直觉是：

- `EmbeddedChunk` 保留了原始 chunk 身份
- provider 已经出现
- 第三章交付的是向量层，不是完整检索系统

---

## 第 1 步：先确认第三章真正吃的输入

**对应文件**：`../phase_2_document_processing/app/indexing/index_manager.py`、`../phase_2_document_processing/scripts/inspect_chunks.py`

### 这一步要解决什么

- 第三章真正的输入不是文件，而是稳定 `SourceChunk[]`
- `chunk_id / document_id / metadata` 是在第二章就已经固定下来的

---

## 第 2 步：看配置和 Provider

**对应文件**：`app/config.py`、`app/embeddings/providers.py`

### 这一步要解决什么

- 当前默认 provider 是什么
- 为什么本地 provider 适合当前阶段
- 为什么还要保留 `openai_compatible` 接口位

### 重点观察

- provider 名称
- 模型信息
- `embed_documents()` / `embed_query()`

### 建议主动修改

- 切换 provider 配置
- 改 embedding 维度或模型名占位

---

## 第 3 步：看 `SourceChunk -> EmbeddedChunk`

**对应文件**：`app/embeddings/vectorizer.py`、`app/schemas.py`

### 这一步要解决什么

- 第三章到底补了哪一层
- 为什么 `EmbeddedChunk` 不是替代 `SourceChunk`

### 重点观察

- `EmbeddedChunk`
- 批量向量化流水线
- 结果里如何保留原始 chunk

---

## 第 4 步：看相似度实验

**对应文件**：`app/embeddings/similarity.py`、`scripts/compare_similarity.py`

### 这一步要解决什么

- 为什么 query 和 document 走两条语义分开的入口
- 为什么相关文本的相似度应更高

### 建议先跑

```bash
python scripts/compare_similarity.py
```

---

## 第 5 步：最后看测试在锁定什么

**对应文件**：`tests/test_embeddings.py`

### 重点观察

- 第三章是否复用了第二章的 chunk 身份
- 向量化是不是当前章节增量，而不是重写

---

## 推荐完整阅读顺序

如果你是第一次读这一章，建议严格按这个顺序：

1. `app/config.py`
2. `app/embeddings/providers.py`
3. `app/schemas.py`
4. `app/embeddings/vectorizer.py`
5. `app/embeddings/similarity.py`
6. `scripts/embed_documents.py`
7. `scripts/compare_similarity.py`
8. `tests/test_embeddings.py`

## 建议主动修改的地方

1. 切换 provider 配置，观察 `local_hash` 和 `openai_compatible` 的接口共性。
2. 改 embedding 维度或模型名占位，观察 `EmbeddedChunk` 里新增字段如何变化。
3. 让 `compare_similarity.py` 多比较一组明显不相关文本，观察相似度差异。

## 学完这一章后你应该能回答

- 为什么第三章必须建立在前两章之上
- 为什么 `EmbeddedChunk` 要保留 `SourceChunk`
- 为什么 `embed_query()` 和 `embed_documents()` 不应混成模糊接口
- 为什么第三章现在还不应该把向量数据库也写进来

## 当前真实进度和下一章

- 当前真实进度：这一章已经交付向量表示层，但真实向量库存储和检索还没有落地
- 完成标准：能解释为什么第三章只是当前章节增量，能说明 `EmbeddedChunk` 为什么保留 `SourceChunk`，能区分 query/document 两条入口
- 下一章：把 `EmbeddedChunk[]` 写入向量存储，支持 Top-K 查询、过滤和删除
