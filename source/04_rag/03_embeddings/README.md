# 03. 向量化 - 实践指南

> 本文档说明如何跟着 [学习文档](/Users/linruiqiang/work/ai_application/docs/04_rag/03_embeddings.md) 学完第三章，并在不依赖第四章以后的前提下，看懂 `SourceChunk -> EmbeddedChunk`、最小相似度排序，以及 query/document 为什么必须保留两个入口。

---

## 核心原则

```text
先看稳定 chunk 如何变成向量 -> 再看 query/document 为什么分开 -> 最后看相似度排序和向量契约边界
```

- 在 `source/04_rag/03_embeddings/` 目录下操作
- 本章只讲向量化和相似度，不讲向量数据库、检索策略和生成
- 为了保持本章独立，代码直接提供一组稳定样例 `SourceChunk[]`
- 本章重点不是“接真实平台”，而是先建立向量层和向量空间的心智模型
- 旧的 `labs/phase_3_embeddings/` 只作为迁移期备份，不再是当前学习入口

---

## 项目结构

```text
03_embeddings/
├── README.md
├── embedding_basics.py
├── 01_embed_chunks.py
├── 02_compare_similarity.py
├── 03_query_vs_document.py
└── tests/
    └── test_embeddings.py
```

- `embedding_basics.py`
  放本章最小对象、样例 `SourceChunk`、provider、向量化、相似度和契约校验逻辑
- `01_embed_chunks.py`
  看 `SourceChunk` 如何变成 `EmbeddedChunk`
- `02_compare_similarity.py`
  看 query 如何和 chunk vectors 做最小排序
- `03_query_vs_document.py`
  看为什么 query/document 要保留两个入口，以及它们怎样在同一向量空间中比较

---

## 前置准备

### 1. 运行目录

```bash
cd source/04_rag/03_embeddings
```

### 2. 当前命令

```bash
python 01_embed_chunks.py
python 02_compare_similarity.py
python 03_query_vs_document.py
python -m unittest discover -s tests
```

### 3. 先跑哪个

建议先跑：

```bash
python 01_embed_chunks.py
```

你最先要建立的直觉是：

- `EmbeddedChunk` 不是替代 `SourceChunk`
- provider 已经出现，但当前仍然保持本地、最小、可重复
- query 和 document 不只是“都能 embed”，还必须落在同一向量空间里
- 第三章交付的是向量层，不是完整检索系统

---

## 第 1 步：看 `SourceChunk -> EmbeddedChunk`

**对应文件**：`01_embed_chunks.py`

重点观察：

- 向量化前后哪些字段被保留
- `provider_name / model_name / dimensions / vector` 是第三章新增的什么信息
- 为什么第二章的 `source / filename / suffix / range` 不能丢

你最值得先看的是：

- `demo_source_chunks()`
- `demo_chunk_metadata()`
- `embed_chunks()`

---

## 第 2 步：看 query 如何和 chunk 做相似度排序

**对应文件**：`02_compare_similarity.py`

重点观察：

- query 先被变成 query vector
- chunk 先被变成 document vectors
- 排序结果仍然保留原始 chunk 身份
- 相似度比较必须发生在同一 provider/model 空间里

运行后重点看：

- 哪个 chunk 得分最高
- 最高分为什么合理
- 不同 query 为什么会命中不同 chunk

---

## 第 3 步：看为什么 query/document 要保留两个入口

**对应文件**：`03_query_vs_document.py`

重点观察：

- 同一段文本走 query path 和 document path 时，结果可以不同
- 它们不同不代表不可比较
- 两条路径不同，但仍然属于同一 provider/model 空间
- 把两个入口分开，后面接真实 provider 更稳妥

---

## 第 4 步：最后看测试在锁定什么

**对应文件**：`tests/test_embeddings.py`

测试里会保留一个 mini golden set，并额外锁定本章最重要的几件事：

1. 向量维度固定
2. `EmbeddedChunk` 保留原始 chunk 身份
3. query/document 两条路径不同但可比较
4. 相关文本相似度高于无关文本
5. provider 返回错误数量或错误维度会直接失败
6. query 和 document 向量不能跨 provider/model 空间混算

---

## 建议学习顺序

1. 先读 [03_embeddings.md](/Users/linruiqiang/work/ai_application/docs/04_rag/03_embeddings.md)
2. 再跑 `python 01_embed_chunks.py`
3. 再跑 `python 02_compare_similarity.py`
4. 最后跑 `python 03_query_vs_document.py`

---

## 第三章最小回归集

第三章不做完整评估系统，但应该保留一个最小回归集，避免你改 provider、concept group 或相似度逻辑以后，不知道教学主线有没有跑偏。

一个足够小的回归集可以长这样：

```python
mini_golden_set = [
    {
        "question": "如何申请退费？",
        "expected_top_chunk": "refund:0",
    },
    {
        "question": "为什么 metadata 很重要？",
        "expected_top_chunk": "metadata:0",
    },
    {
        "question": "工作日什么时候可以答疑？",
        "expected_top_chunk": "support:0",
    },
]
```

这不是完整评估体系，但已经足够回答几个关键问题：

- 最相关 chunk 还能不能被排到最前面
- provider 的最小语义空间是否还在工作
- chapter demo 是否仍然稳定

---

## 失败案例也要刻意观察

第三章至少要刻意看两类失败：

1. provider 契约失败

如果 provider 返回：

- 文档向量数量和输入文本数量不匹配
- 向量维度和 `provider.dimensions` 不匹配

系统应该立即失败，而不是把错误向量静默传到下一章。

2. 向量空间混用失败

如果 query 用的 provider/model 和 document 向量不是同一个空间，系统也应该拒绝比较。

这说明第三章不是“先随便算个相似度”，而是在建立一个有明确契约的向量层。

---

## 学完这一章后你应该能回答

- 为什么第三章只增加向量层，而不是重做输入管道
- 为什么 `EmbeddedChunk` 要保留 `SourceChunk`
- 为什么 `embed_query()` 和 `embed_documents()` 不该混成一个模糊接口
- 为什么 query/document 必须落在同一向量空间里
- 为什么 provider 契约错误应该在第三章就直接失败
- 为什么第三章现在还不应该把向量数据库写进来

---

## 当前真实进度和下一章

- 当前真实进度：第三章已经改成独立学习单元
- 完成标准：能看懂向量化增量、相似度排序、provider 契约和 query/document 边界
- 下一章：进入 [source/04_rag/04_vector_databases/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/04_vector_databases/README.md)，把 `EmbeddedChunk[]` 写进向量存储，做最小查询、过滤和删除
