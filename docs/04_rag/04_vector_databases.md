# 04. 向量数据库

> 本节目标：理解为什么只有向量还不够，掌握 `EmbeddedChunk[] -> ChromaVectorStore` 这层新增能力，并能对着第四章代码快照看清写入、查询、过滤、删除和持久化分别落在哪里。

---

## 1. 概述

### 学习目标

- 理解为什么第三章的 `EmbeddedChunk[]` 还不能直接等同于可用检索系统
- 理解向量数据库在 RAG 系统中的职责边界
- 理解为什么第四章应该先解决写入、查询、过滤、删除，再进入第五章的 Retriever 策略
- 能运行第四章脚本，并看懂 Chroma 如何保留 `chunk_id / document_id / metadata`
- 能说明为什么删除和持久化属于检索工程的前置能力，而不是“以后再说”的运维细节

### 预计学习时间

- 向量存储职责和边界：45 分钟
- Chroma 写入 / 查询 / 删除：1 小时
- 第四章代码快照阅读：1-1.5 小时

### 本节在 AI 应用中的重要性

| 场景 | 相关知识 |
|------|---------|
| 知识库入库 | `EmbeddedChunk[]` 写入持久化 collection |
| 在线问答 | query vector + Top-K 查询 |
| 多来源知识库 | metadata 过滤 |
| 增量更新 | 按 `document_id` 删除和重建 |
| 后续 Retriever 封装 | Vector Store 与 Retriever 拆层 |

> **第三章解决的是“向量怎么来”，第四章解决的是“这些向量怎么存、怎么查、怎么维护”。**

### 本章与前后章节的关系

第三章已经解决：

1. `SourceChunk[] -> EmbeddedChunk[]`
2. query/document 两条向量化路径

第四章接着解决：

1. 向量如何真正落到持久化存储
2. 查询如何重新返回标准 `SourceChunk`
3. metadata 过滤和按 `document_id` 删除如何建立

第五章会继续建立在这里之上：

1. 把当前最小查询能力封装成 Retriever
2. 围绕召回质量开始做策略比较和优化

### 本章的学习边界

本章重点解决：

1. 向量存储的职责
2. 写入、查询、过滤、删除
3. 持久化和一致性意识
4. 当前阶段为什么选真实 Chroma

本章不系统展开：

- MMR、Multi-query、HyDE 等策略优化
- Rerank 和混合检索
- 完整 RAG 生成
- Milvus / Pinecone / Weaviate 的生产部署差异
- ANN 底层算法细节

### 当前代码快照

本章对应的代码快照是：

- [phase_4_vector_databases/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_4_vector_databases/README.md)
- [app/vectorstores/chroma_store.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_4_vector_databases/app/vectorstores/chroma_store.py)
- [scripts/index_chroma.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_4_vector_databases/scripts/index_chroma.py)
- [scripts/search_chroma.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_4_vector_databases/scripts/search_chroma.py)
- [scripts/delete_document.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_4_vector_databases/scripts/delete_document.py)

---

## 2. 为什么只有向量还不够 📌

### 2.1 `EmbeddedChunk[]` 不等于可检索系统

第三章已经让系统拥有：

- chunk 身份
- metadata
- 向量表示

但这还不够。

因为真正的在线系统还需要回答：

- 这些向量放在哪里
- 下次重启后还能不能查
- 同一个 `document_id` 如何更新和删除
- 如何按来源、类型、租户做过滤

如果这些问题没有先解决，后面的 Retriever 和生成链路都会建立在不稳定底座上。

### 2.2 Vector Store 在系统里负责什么

Vector Store 负责的是：

1. 存向量
2. 查向量
3. 维护向量和 metadata 的对应关系
4. 提供后续 Retriever 可复用的查询入口

它不负责：

- 重新切分文档
- 重新生成向量
- 组织 Prompt
- 调模型回答

也就是说，它是：

> 向量层和检索层之间的持久化基础设施。

### 2.3 为什么这章要用真实 Chroma

这门课当前的目标不是做供应商比较，而是把心智模型做稳。

所以第四章选择真实 Chroma，有三个原因：

1. 本地可跑，适合课程实验
2. 具备真实 collection / metadata / delete 语义
3. 足够让你建立后续迁移到其他向量库时需要保留的抽象边界

换句话说，这一章的重要性不在于“会不会背 Chroma API”，而在于：

> 你开始第一次用真实向量库来验证前面三章建立的数据契约是否合理。

---

## 3. 第四章当前代码到底新增了什么 📌

### 3.1 新增的核心对象

第四章没有重做 `SourceChunk`，也没有重做 `EmbeddedChunk`。

真正新增的是：

```text
EmbeddedChunk[]
-> ChromaVectorStore.upsert()
-> Persistent collection
-> similarity_search()
-> RetrievalResult[]
```

这说明第四章依然是“在前一章稳定输出上做增量”，而不是开新分支。

### 3.2 当前 Chroma 适配器做了什么

[app/vectorstores/chroma_store.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_4_vector_databases/app/vectorstores/chroma_store.py) 当前主要交付了这些能力：

1. `ChromaVectorStoreConfig`
   负责持久化目录、collection 名、距离度量配置
2. `upsert()`
   把 `EmbeddedChunk[]` 真正写入 Chroma
3. `get_chunks()`
   把存储层数据重新还原为标准 `SourceChunk`
4. `similarity_search()`
   用 query vector 查询 Top-K 结果
5. `delete_by_document_id()`
   建立最小删除入口

### 3.3 为什么 metadata 必须一起写入

第四章的一个关键点是：

> metadata 不再只是“方便调试看看”，而是会进入真实查询和删除路径。

例如现在的代码里：

- `filename` 可以直接拿来做过滤
- `document_id` 可以拿来做删除
- `chunk_index / source` 可以拿来做调试和展示

如果你在写入时把这些字段丢掉，后面就会出现两个典型问题：

1. 查到了内容，却无法解释它来自哪里
2. 文档更新时，不知道该删哪一批旧 chunk

### 3.4 为什么 `document_id` 在这一章变得特别重要

第二章引入 stable id 时，这件事还只是“结构上应该有”。

到了第四章，`document_id` 已经开始承担真实职责：

- 作为删除入口
- 作为一致性锚点
- 作为后续增量更新的基础

这就是为什么第二章的 stable id 不是“学术正确”，而是后面真会用到。

---

## 4. 第四章如何分层 📌

### 4.1 当前分层关系

当前代码建议你这样看：

| 层 | 当前文件 | 解决什么问题 |
|----|----------|--------------|
| 文档输入层 | `app/ingestion/` | 文件怎样进入系统 |
| 标准 chunk 层 | `app/indexing/` | 如何稳定产出 `SourceChunk[]` |
| 向量化层 | `app/embeddings/` | 如何产出 `EmbeddedChunk[]` |
| 向量存储层 | `app/vectorstores/chroma_store.py` | 如何真正存、查、删 |
| 最小服务演示 | `scripts/query_demo.py` | 如何让当前检索结果流进回答占位链路 |

### 4.2 为什么 Vector Store 和 Retriever 还要继续分开

很多初学者会觉得：

> “既然现在都能查 Top-K 了，这不就是 Retriever 吗？”

还不是。

当前第四章的能力更接近：

- 给你一个 query vector
- 返给你最相近的 chunk
- 支持 metadata 过滤和删除

而第五章会在这里之上继续做：

- 更清晰的 Retriever 接口
- `top_k / threshold / MMR` 等策略选择
- 召回行为的对比和坏案例分析

所以第四章和第五章拆开的意义在于：

- 第四章先把存储和查询基础设施做稳
- 第五章再把“怎么召回更好”做成策略问题

### 4.3 `query_demo.py` 为什么现在就接了真实检索

第四章的 [scripts/query_demo.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_4_vector_databases/scripts/query_demo.py) 已经不再用 mock 检索。

它现在做的是：

1. 确保 Chroma 里有索引
2. 用真实向量查询召回 chunk
3. 把结果交给仍然是占位的 `RagService`

这样处理的好处是：

- 能保持与第一章到第三章的数据流连续
- 又不会提前把第五章的 Retriever 设计塞进来

---

## 5. 第四章应该怎么学

### 5.1 推荐顺序

建议按这个顺序进入：

1. 先看 [app/config.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_4_vector_databases/app/config.py)
2. 再看 [app/vectorstores/chroma_store.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_4_vector_databases/app/vectorstores/chroma_store.py)
3. 再看 [scripts/index_chroma.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_4_vector_databases/scripts/index_chroma.py)
4. 再看 [scripts/search_chroma.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_4_vector_databases/scripts/search_chroma.py)
5. 最后看 [tests/test_vectorstores.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_4_vector_databases/tests/test_vectorstores.py)

### 5.2 建议先跑的命令

```bash
cd source/04_rag/labs/phase_4_vector_databases
python -m pip install -r requirements.txt
python scripts/index_chroma.py --reset
python scripts/search_chroma.py
```

### 5.3 跑完后重点观察什么

- 写入后 collection count 是否和 chunk 数一致
- 查询结果里是否还能看到稳定的 `filename / source / chunk_index`
- metadata filter 是否真的缩小了结果范围
- 删除之后 collection count 是否变化
- 重新索引后结果是否恢复

### 5.4 测试在锁定什么

[tests/test_vectorstores.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_4_vector_databases/tests/test_vectorstores.py) 现在锁定的是：

1. 写入后重新加载仍然能取回 chunk
2. 相似度查询会优先返回相关内容
3. metadata 过滤会限制查询范围
4. 按 `document_id` 删除会移除整份文档的所有 chunk

这说明第四章测试的重心已经不是“目录存在”，而是开始锁定真实存储行为。

---

## 6. 学完这一章后你应该能回答

- 为什么 `EmbeddedChunk[]` 还不等于可用检索系统
- 为什么 metadata 不应该在写入时丢掉
- 为什么 `document_id` 会变成删除和更新的一致性锚点
- 为什么 `Vector Store` 和 `Retriever` 应该继续拆层
- 为什么第四章已经能做真实查询，但仍然不应该提前把第五章的策略混进来

---

## 综合案例：为课程资料问答建立最小向量存储层

```python
# 你现在已经有 Phase 3 产出的 EmbeddedChunk[]：
#
# 请回答：
# 1. 为什么还需要 Vector Store，而不是直接在内存里保留这些向量？
# 2. 写入时为什么必须保留 chunk_id / document_id / metadata？
# 3. 为什么 metadata 过滤和删除要在第四章就建立？
# 4. 第四章当前代码里，哪些能力属于 Vector Store，哪些能力应该留给第五章 Retriever？
```
