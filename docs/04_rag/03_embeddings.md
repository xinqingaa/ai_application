# 03. 向量化

> 本节目标：理解文本为什么要变成向量，跑通一个最小的 `SourceChunk -> EmbeddedChunk` 闭环，并建立“query 和 document 为什么要分开向量化”“为什么它们必须落在同一向量空间”的判断。

---

## 1. 概述

### 学习目标

- 理解为什么第三章只增加向量层，而不是重做输入管道
- 理解 `EmbeddingProvider` 在系统里的职责
- 理解为什么 `embed_query()` 和 `embed_documents()` 要保留为两个入口
- 理解为什么 query 和 document 虽然走不同路径，但必须共享同一个 provider/model 空间
- 能运行第三章脚本，并看出向量结果如何保留 `chunk_id / document_id / metadata`
- 能说明第三章为什么只做到向量化，而不提前混进向量数据库和完整检索

### 预计学习时间

- 向量化原理与对象关系：40 分钟
- query/document 区分：30-40 分钟
- 第三章代码实践：40-60 分钟

### 本章在 AI 应用中的重要性

| 场景 | 本章先解决什么 |
|------|----------------|
| 离线索引 | 稳定 chunk 如何变成可存储的向量 |
| 在线检索 | 用户问题如何进入同一个向量空间 |
| 检索调试 | 为什么排序结果必须保留 chunk 身份 |
| 后续向量库 | 为什么 provider/model/dimensions 的契约要先立住 |

### 学习前提

- 建议先完成第二章，理解稳定 `SourceChunk[]` 是如何形成的
- 建议先理解第一章里“RAG 不等于直接生成答案”
- 不要求你先接入真实 embedding API
- 但你需要先接受一个前提：第三章不是在重做数据输入层，而是在其外再包一层向量表示

### 本章与前后章节的关系

第二章解决的是：

1. 原始文件怎样变成稳定 `SourceChunk[]`
2. metadata 和 stable id 怎样固定下来

第三章接着解决的是：

1. `SourceChunk[]` 怎样变成 `EmbeddedChunk[]`
2. query 和 document 怎样进入两条不同的向量化路径
3. provider/model/dimensions 的最小契约怎样立住

第四章会继续建立在这里之上：

1. 把 `EmbeddedChunk[]` 写入向量存储
2. 基于向量做最小查询和删除

### 本章代码入口

本章对应的代码目录是：

- [source/04_rag/03_embeddings/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/03_embeddings/README.md)
- [embedding_basics.py](/Users/linruiqiang/work/ai_application/source/04_rag/03_embeddings/embedding_basics.py)
- [01_embed_chunks.py](/Users/linruiqiang/work/ai_application/source/04_rag/03_embeddings/01_embed_chunks.py)
- [02_compare_similarity.py](/Users/linruiqiang/work/ai_application/source/04_rag/03_embeddings/02_compare_similarity.py)
- [03_query_vs_document.py](/Users/linruiqiang/work/ai_application/source/04_rag/03_embeddings/03_query_vs_document.py)

### 本章边界

本章重点解决：

1. 文本为什么要向量化
2. `SourceChunk -> EmbeddedChunk`
3. query/document 两条向量化入口
4. 最小相似度比较
5. 向量空间和 provider 契约的最小边界

本章不展开：

- 真实向量数据库写入
- Top-K、MMR、Threshold 等检索策略
- Rerank 和混合检索
- LLM 生成答案
- Embedding 模型大规模横评
- 本地推理部署和 GPU 优化

为了保持章节独立，本章代码直接提供一组稳定样例 `SourceChunk[]`。

目的不是跳过第二章，而是避免你为了学向量化，再次背上文档处理目录结构。

但第三章仍然会保留一个最小回归集和失败案例，避免 provider 契约问题被悄悄传到第四章。

---

## 2. 向量化到底在做什么 📌

### 2.1 为什么要把文本变成向量

系统和程序都无法直接对“语义相近”做传统字符串比较。

例如：

- “如何申请退费？”
- “购买后 7 天内可以退款吗？”

它们字面上并不完全一样，但语义很接近。

向量化的目标就是把文本映射成一个数值空间里的点，让：

- 语义接近的文本距离更近
- 语义无关的文本距离更远

这样后续系统才能基于相似度去检索相关 chunk。

### 2.2 第三章真正新增的是什么

第三章新增的不是另一套 loader，也不是另一套索引脚本。

第三章只新增这一层：

```text
SourceChunk[]
-> embed_documents()
-> EmbeddedChunk[]
```

这就是第三章最重要的判断：

> 第三章是在稳定 chunk 外面，再包一层向量表示，而不是推翻前面章节。

### 2.3 为什么 `EmbeddedChunk` 不是替代 `SourceChunk`

第三章的对象演进应该这样理解：

| 阶段 | 核心对象 | 作用 |
|------|----------|------|
| 第二章 | `SourceChunk` | 让知识以稳定 chunk 形式存在 |
| 第三章 | `EmbeddedChunk` | 在 `SourceChunk` 外再加向量、provider、model 信息 |

关键点在于：

- `EmbeddedChunk` 不是替代 `SourceChunk`
- `EmbeddedChunk` 是把 `SourceChunk` 保留下来，再额外加上向量负载

这能确保后续向量库、检索、引用和调试仍然能拿到原始 chunk 身份。

### 2.4 第三章到底继承了第二章什么

如果第三章真的是建立在第二章之上，那它至少应该继续保留这些信息：

- `chunk_id`
- `document_id`
- `source`
- `filename`
- `suffix`
- `chunk_index`
- `char_start / char_end / chunk_chars`

第三章真正新增的是：

- `vector`
- `provider_name`
- `model_name`
- `dimensions`

也就是说，第三章的工作不是“把文档变成向量后就忘掉来源”，而是：

> 把向量和原始 chunk 身份绑在一起，作为后续向量存储和检索的基础对象。

---

## 3. 为什么 query 和 document 要分开向量化 📌

### 3.1 两者在系统中的角色不同

document embedding 的目标是：

- 表示知识库里的静态内容
- 为后续索引和检索提供向量基础

query embedding 的目标是：

- 表示用户当前的问题
- 在同一个向量空间里去匹配最相关的 document vectors

虽然它们都叫 embedding，但在很多模型和接口设计里，这两者不一定完全等价。

### 3.2 为什么保留两个入口更稳妥

保留 `embed_documents()` 和 `embed_query()` 两个入口的好处是：

1. 接口语义清晰
2. 未来更换 provider 时更容易适配
3. 便于区分离线索引和在线检索的调用路径
4. 便于在不同模型或不同参数下做实验

即使当前本地 provider 内部实现接近，这两个入口也值得保留。

### 3.3 为什么“分开”不等于“随便用不同空间”

这是第三章一个非常容易混淆的地方。

你要同时记住两件事：

1. query 和 document 应该保留两个入口
2. query 和 document 仍然必须落在同一个可比较的向量空间里

也就是说：

- 路径可以不同
- 输出可以略有差异
- 但 provider/model/dimensions 不能乱混

否则你得到的不是“更灵活的系统”，而是“不可比较的向量”。

### 3.4 为什么第三章先用本地 provider

第三章当前最重要的目标是：

1. 看懂接口
2. 看懂对象
3. 看懂数据流
4. 看懂最小契约

不是一上来就被 API Key、网络、计费和 provider 差异打断。

所以当前代码默认先用本地 `LocalKeywordEmbeddingProvider`。

这样你能先把注意力放在：

- 什么是向量
- 什么是相似度
- 什么是 query/document 分离
- 什么是同一向量空间

而不是先被平台接入问题打断。

---

## 4. provider 契约为什么要在第三章就立住 📌

### 4.1 什么叫最小 provider 契约

第三章至少要锁住三件事：

1. `embed_documents()` 返回的向量数量要和输入文本数量一致
2. 每条向量的维度要等于 `provider.dimensions`
3. query 和 document 比较时，要来自同一个 provider/model 空间

这些事情如果不在第三章就立住，后面会出现两类典型坏结果：

- 错误向量被静默写进向量库
- 相似度排序看起来有数字，但其实比较的是不兼容的向量

### 4.2 为什么错误应该尽早失败

比如下面这些情况，都不应该被悄悄放过：

- provider 返回的 document vector 数量不对
- provider 返回的某条向量维度不对
- query 用的是另一个 model，却去比较旧的 document vectors

如果这些错误直到第四章或第五章才暴露，定位成本会明显变高。

所以第三章要建立的习惯是：

> 向量层的契约问题，应该在向量层就失败。

### 4.3 零向量和空输入怎么理解

第三章还要理解两个边界：

- 空输入：没有 chunk 时，向量化结果和排序结果都应该是空
- 零向量：如果某个向量全零，相似度比较应该安全返回 `0.0`，而不是报数学错误

这类边界虽然简单，但非常适合作为第三章的最小回归样本。

---

## 5. 第三章实践：独立向量化闭环

### 5.1 目录结构

本章代码目录是：

```text
source/04_rag/03_embeddings/
├── README.md
├── embedding_basics.py
├── 01_embed_chunks.py
├── 02_compare_similarity.py
├── 03_query_vs_document.py
└── tests/
```

第三章保持和前两章一样的平铺目录。

这里不做：

- `app/embeddings/`
- `providers/` 子包
- 项目级配置和多模块骨架

因为本章重点是理解向量化，不是理解工程拆分。

### 5.2 输入和输出

本章代码的输入是：

- 一组固定样例 `SourceChunk[]`
- 一个本地 provider
- 一个 query

本章代码的输出是：

- `EmbeddedChunk[]`
- query vector
- document vectors
- similarity scores

在 [embedding_basics.py](/Users/linruiqiang/work/ai_application/source/04_rag/03_embeddings/embedding_basics.py) 里，你最值得先看的是：

- `SourceChunk`
- `EmbeddedChunk`
- `EmbeddingProvider`
- `LocalKeywordEmbeddingProvider`
- `demo_chunk_metadata()`
- `demo_source_chunks()`
- `embed_chunks()`
- `ensure_vector_dimensions()`
- `ensure_same_embedding_space()`
- `cosine_similarity()`
- `score_query_against_chunks()`

### 5.3 运行方式

```bash
cd source/04_rag/03_embeddings

python 01_embed_chunks.py
python 02_compare_similarity.py
python 03_query_vs_document.py
python -m unittest discover -s tests
```

### 5.4 你应该观察到什么

跑 [01_embed_chunks.py](/Users/linruiqiang/work/ai_application/source/04_rag/03_embeddings/01_embed_chunks.py) 时：

- `chunk_id / document_id / metadata` 被保留下来
- 你能看到继承自第二章的 `source / filename / suffix / range`
- 第三章新增的是 `provider_name / model_name / dimensions / vector`
- `EmbeddedChunk` 看起来像“保留原始 chunk 的增强版”

跑 [02_compare_similarity.py](/Users/linruiqiang/work/ai_application/source/04_rag/03_embeddings/02_compare_similarity.py) 时：

- query 会先变成 query vector
- chunk 会先变成 document vectors
- 排序结果仍然保留 chunk 身份
- “如何申请退费？” 应该更接近退款规则 chunk
- “为什么 metadata 很重要？” 应该更接近 metadata 规则 chunk

跑 [03_query_vs_document.py](/Users/linruiqiang/work/ai_application/source/04_rag/03_embeddings/03_query_vs_document.py) 时：

- 同一段文本走 query/document 两条路径时，结果可以不同
- 它们不同不代表不可比较
- query/document 的 mode buckets 可以不同
- 但它们仍然属于同一 provider/model 空间

### 5.5 第三章最小回归集

第三章不做完整评估系统，但应该从一开始就保留一个最小回归集。

因为你后面会不断改：

- concept groups
- hash bucket 逻辑
- provider 契约
- query/document 差异
- 相似度排序逻辑

如果没有最小回归样本，很容易出现这样的情况：

- 文档还说“退款问题应该命中退款 chunk”
- 代码却已经把 metadata chunk 排到第一
- 你自己还没发现

这一章最小回归集只需要锁定几条典型 query：

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

这不是完整评估体系，但已经足够回答：

1. 最小语义空间还在不在工作
2. 相似度排序有没有明显跑偏
3. chapter demo 是否仍然可重复

### 5.6 本章代码刻意简化了什么

这一章的实现刻意简化了五件事：

1. 只用本地 provider
2. 不接真实平台 API
3. 只做最小 cosine similarity
4. 不写向量数据库
5. 不做真实 embedding 模型的横向比较

这是故意的。

因为本章要先把下面这件事学会：

> 第三章解决的是“向量怎么来”，不是“向量怎么存、怎么查、怎么维护”。

---

## 6. 本章学完后你应该能回答

- 为什么第三章只增加向量层，而不是重做输入管道
- 为什么 `EmbeddedChunk` 要保留 `SourceChunk`
- 为什么 `embed_query()` 和 `embed_documents()` 不应混成模糊接口
- 为什么 query/document 必须落在同一向量空间里
- 为什么 provider 契约错误应该在第三章就直接失败
- 为什么相似度排序仍然需要保留 chunk 身份
- 为什么第三章现在还不应该把向量数据库写进来

---

## 7. 下一章

第四章开始，你才会进入向量存储问题：

- 这些向量怎么写进去
- 怎么查 top-k
- 怎么做删除和过滤

也就是说，第四章处理的是“这些向量怎么存、怎么查、怎么维护”。

第三章先把“向量怎么来”“怎么确保它们还可比较”立住，就够了。
