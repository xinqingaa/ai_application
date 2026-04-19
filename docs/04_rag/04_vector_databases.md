# 04. 向量存储

> 本节目标：理解为什么只有向量还不够，跑通一个最小的“写入、查询、过滤、删除、持久化”闭环，并建立“向量存储层”和“Retriever 策略层”之间的边界。

---

## 1. 概述

### 学习目标

- 理解为什么第三章的 `EmbeddedChunk[]` 还不能直接等同于可用检索系统
- 理解向量存储在 RAG 系统中的职责边界
- 理解为什么第四章应该先解决写入、查询、过滤、删除，再进入第五章的 Retriever 策略
- 能运行第四章脚本，并看懂持久化存储如何保留 `chunk_id / document_id / metadata`
- 能说明为什么删除和持久化属于检索工程的前置能力，而不是“以后再说”的细节

### 预计学习时间

- 向量存储职责和边界：30-40 分钟
- 写入 / 查询 / 删除：40-60 分钟
- 第四章代码实践：40-60 分钟

### 本章与前后章节的关系

第三章已经解决：

1. `SourceChunk[] -> EmbeddedChunk[]`
2. query/document 两条向量化路径

第四章接着解决：

1. 向量如何真正落到持久化存储
2. 查询如何重新返回标准 chunk
3. metadata 过滤和按 `document_id` 删除如何建立

第五章会继续建立在这里之上：

1. 把当前最小查询能力封装成 Retriever
2. 围绕召回质量开始做策略比较和优化

### 本章代码入口

本章对应的代码目录是：

- [source/04_rag/04_vector_databases/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/04_vector_databases/README.md)
- [vector_store_basics.py](/Users/linruiqiang/work/ai_application/source/04_rag/04_vector_databases/vector_store_basics.py)
- [01_index_store.py](/Users/linruiqiang/work/ai_application/source/04_rag/04_vector_databases/01_index_store.py)
- [02_search_store.py](/Users/linruiqiang/work/ai_application/source/04_rag/04_vector_databases/02_search_store.py)
- [03_delete_document.py](/Users/linruiqiang/work/ai_application/source/04_rag/04_vector_databases/03_delete_document.py)

### 本章边界

本章重点解决：

1. 向量存储的职责
2. 写入、查询、过滤、删除
3. 持久化和一致性意识
4. 为什么第四章只做到存储层

本章不系统展开：

- MMR、Multi-query、HyDE 等策略优化
- Rerank 和混合检索
- 完整 RAG 生成
- 真实云向量库的供应商差异
- ANN 底层算法细节

为了保持章节独立和最小化，本章代码使用一个本地 JSON 持久化的最小向量存储。

目的不是替代真实向量库，而是先把“向量怎么存、怎么查、怎么删、怎么保持一致”讲清楚。

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

### 2.2 向量存储在系统里负责什么

向量存储负责的是：

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

### 2.3 为什么第四章先用最小本地存储

这门课当前的目标不是做供应商比较，而是把心智模型做稳。

所以第四章先选择一个本地、最小、可读的持久化实现，有三个原因：

1. 没有外部依赖，学习成本低
2. 可以直接看见写入、过滤、删除和持久化行为
3. 更容易把注意力放在职责边界，而不是库 API

这一章的重要性不在于“会不会背某个库名”，而在于：

> 你开始第一次用真实持久化行为来验证前面三章建立的数据契约是否合理。

---

## 3. 第四章到底新增了什么 📌

### 3.1 新增的核心数据流

第四章没有重做 `SourceChunk`，也没有重做 `EmbeddedChunk`。

真正新增的是：

```text
EmbeddedChunk[]
-> upsert()
-> persistent store
-> similarity_search()
-> RetrievalResult[]
```

这说明第四章依然是“在前一章稳定输出上做增量”，而不是开新分支。

### 3.2 当前最小向量存储做了什么

[vector_store_basics.py](/Users/linruiqiang/work/ai_application/source/04_rag/04_vector_databases/vector_store_basics.py) 当前主要交付了这些能力：

1. `VectorStoreConfig`
   负责持久化文件路径
2. `PersistentVectorStore.upsert()`
   把 `EmbeddedChunk[]` 真正写入磁盘
3. `load_chunks()`
   把存储层数据重新还原为标准 `EmbeddedChunk`
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

当前课程建议你这样看：

| 层 | 当前章节 | 解决什么问题 |
|----|----------|--------------|
| 文档输入层 | 第二章 | 文件怎样进入系统 |
| 向量化层 | 第三章 | chunk 怎样变成向量 |
| 向量存储层 | 第四章 | 向量怎样真正存、查、删 |
| Retriever 层 | 第五章 | 怎样查得更好 |

### 4.2 为什么向量存储和 Retriever 还要继续分开

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

---

## 5. 第四章实践：独立向量存储闭环

### 5.1 目录结构

本章代码目录是：

```text
source/04_rag/04_vector_databases/
├── README.md
├── vector_store_basics.py
├── 01_index_store.py
├── 02_search_store.py
├── 03_delete_document.py
├── store/
└── tests/
```

第四章和前几章一样，保持平铺目录。

这里不做：

- 外部库依赖
- 项目级配置和模块骨架
- Retriever 策略层

因为本章重点是理解向量存储本身。

### 5.2 输入和输出

本章代码的输入是：

- 一组固定样例 `EmbeddedChunk[]`
- 一个 query vector
- 可选 filename filter

本章代码的输出是：

- 持久化存储文件
- `RetrievalResult[]`
- 删除后的剩余文档状态

在 [vector_store_basics.py](/Users/linruiqiang/work/ai_application/source/04_rag/04_vector_databases/vector_store_basics.py) 里，你最值得先看的是：

- `VectorStoreConfig`
- `PersistentVectorStore`
- `demo_embedded_chunks()`
- `upsert()`
- `similarity_search()`
- `delete_by_document_id()`

### 5.3 运行方式

```bash
cd source/04_rag/04_vector_databases

python 01_index_store.py --reset
python 02_search_store.py
python 02_search_store.py "为什么 metadata 很重要？" --filename metadata_rules.md
python 03_delete_document.py trial
python -m unittest discover -s tests
```

### 5.4 你应该观察到什么

跑 [01_index_store.py](/Users/linruiqiang/work/ai_application/source/04_rag/04_vector_databases/01_index_store.py) 时：

- 存储文件真正被创建
- 当前写入了多少个 chunk
- 当前有哪些 `document_id`

跑 [02_search_store.py](/Users/linruiqiang/work/ai_application/source/04_rag/04_vector_databases/02_search_store.py) 时：

- query 会先变成 query vector
- store 会按相似度排序
- 返回结果仍然保留 `chunk_id / document_id / metadata`
- 带 filename filter 时，结果范围会明显缩小

跑 [03_delete_document.py](/Users/linruiqiang/work/ai_application/source/04_rag/04_vector_databases/03_delete_document.py) 时：

- 删除是围绕 `document_id` 做的
- 删除后 count 会下降
- 剩余 document ids 会变化

### 5.5 本章代码刻意简化了什么

这一章的实现刻意简化了四件事：

1. 只用本地持久化文件
2. 不接真实向量数据库产品
3. 只做最小相似度查询
4. 不做 Retriever 策略层

这是故意的。

因为本章要先把下面这件事学会：

> 第四章解决的是“向量怎么存、怎么查、怎么删”，不是“怎么把召回调到最好”。

---

## 6. 本章学完后你应该能回答

- 为什么 `EmbeddedChunk[]` 还不等于可用检索系统
- 为什么向量存储要负责写入、查询、过滤、删除和持久化
- 为什么 `document_id` 会在这一章变成真实职责
- 为什么 metadata 过滤要在第四章就立住
- 为什么第四章现在还不应该把 Retriever 策略混进来

---

## 7. 下一章

第五章开始，你才会进入 Retriever 策略问题：

- `top_k` 怎么设
- `threshold` 有什么边界
- `MMR` 在解决什么问题

也就是说，第五章处理的是“查得更好”，不是“能不能查”。

第四章先把“能存、能查、能删、能过滤”立住，就够了。
