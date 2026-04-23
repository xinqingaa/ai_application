# 04. 向量数据库

> 本章目标：把第三章的 `EmbeddedChunk[]` 推进成真正可持久化、可查询、可替换、可删除的存储层。你会先看最小 JSON store，再进入真实 `Chroma` 和 `LangChain VectorStore`，最后用一个最小 `VectorStoreManager` 把不同 backend 收束成统一接口。

---

## 1. 概述

### 学习目标

- 理解为什么第三章的 `EmbeddedChunk[]` 还不等于可用检索系统
- 理解向量数据库在 RAG 工程中的职责边界
- 掌握第四章的核心契约：`upsert / replace_document / similarity_search / delete_by_document_id`
- 理解 JSON store、Chroma、LangChain Chroma 在本章里的对应关系
- 认识 `ANN vs 精确搜索` 的权衡和主流向量数据库的选型差异
- 了解为什么第四章要有统一的 `VectorStoreManager`

### 本章与前后章节的关系

第三章已经解决：

1. `SourceChunk[] -> EmbeddedChunk[]`
2. `embed_query / embed_documents`
3. provider / model / dimensions 的最小契约

第四章继续解决：

1. 向量怎样真正落到持久化存储
2. 查询怎样把结果重新还原成标准 chunk
3. metadata 和 `document_id` 怎样进入真实查询/更新/删除路径
4. 原理层和真实工具层怎样一一对应

第五章才继续解决：

1. `top_k / threshold / MMR`
2. Retriever 抽象
3. “怎么查得更好”

### 当前代码入口

- [README.md](../../source/04_rag/04_vector_databases/README.md)
- [vector_store_basics.py](../../source/04_rag/04_vector_databases/vector_store_basics.py)
- [chroma_store.py](../../source/04_rag/04_vector_databases/chroma_store.py)
- [langchain_adapter.py](../../source/04_rag/04_vector_databases/langchain_adapter.py)
- [vector_store_manager.py](../../source/04_rag/04_vector_databases/vector_store_manager.py)
- [01_index_store.py](../../source/04_rag/04_vector_databases/01_index_store.py)
- [02_search_store.py](../../source/04_rag/04_vector_databases/02_search_store.py)
- [03_delete_document.py](../../source/04_rag/04_vector_databases/03_delete_document.py)
- [04_chroma_crud.py](../../source/04_rag/04_vector_databases/04_chroma_crud.py)
- [05_chroma_filter_delete.py](../../source/04_rag/04_vector_databases/05_chroma_filter_delete.py)
- [06_langchain_vectorstore.py](../../source/04_rag/04_vector_databases/06_langchain_vectorstore.py)
- [07_vector_store_manager.py](../../source/04_rag/04_vector_databases/07_vector_store_manager.py)

### 本章边界

本章重点解决：

1. 持久化写入
2. 最小相似度查询
3. 文档级替换
4. `document_id` 删除
5. metadata 过滤路径
6. LangChain VectorStore 接口映射
7. 统一管理器的最小适配器结构

本章不展开：

- `MMR`、`threshold`、`Multi-query`、`HyDE`
- rerank
- hybrid retrieval
- 复杂 metadata DSL
- 多向量库完整实现横评

---

## 2. 向量数据库基础（对应大纲第 10 节） 📌

### 2.1 什么是向量数据库

向量数据库本质上是在解决三件事：

1. 把高维向量稳定存下来
2. 能用相似度快速查回最相关的向量
3. 让向量和原始文档、metadata、文档身份保持绑定

所以它不是“只会存一个 `list[float]` 的数据库”，而是：

> 面向语义检索场景的存储和查询系统。

### 2.2 ANN vs 精确搜索

大纲要求你至少知道：

- 精确搜索会逐个比较候选，结果最准，但规模一大就慢
- `ANN`（Approximate Nearest Neighbor）会牺牲一点精确性，换取更好的查询速度

第四章当前不会手写 ANN 索引实现，因为这会把注意力从“存储契约”拉走。

你现在只需要先建立这个判断：

- 教学 demo、小规模数据：可以先不深挖 ANN 细节
- 真正上线、数据量大：ANN 是现实选择

### 2.3 主流向量数据库的最小选型表

这一节按大纲要求做认知对齐，但不强行给每个库都补 demo。

| 数据库 | 特点 | 更适合什么 |
|--------|------|------------|
| Chroma | 轻量、上手快、本地持久化方便 | 教学、原型、小项目 |
| FAISS | Meta 开源、纯本地、高性能 | 本地实验、离线索引、高性能原型 |
| Pinecone | 云服务、免运维 | 不想自建基础设施的生产场景 |
| Milvus | 开源、分布式、规模能力强 | 大规模生产部署 |
| Weaviate | 开源、功能丰富 | 企业知识库和复杂检索场景 |

为什么第四章当前只正式实现 `Chroma`：

- 它最适合作为第一站真实数据库
- 能直接看清 persistent collection、metadata filter、delete
- 不会让课程一开始就掉进运维和平台差异里

为什么这里不硬造 FAISS / Pinecone / Milvus demo：

> 第 10 节的核心是选型认知，不是为了“代码覆盖率”而把第四章拖成工具拼盘。

### 2.4 向量数据库的核心操作

无论你最终用哪一种库，这一章都要先把下面这些动作立住：

1. 插入向量
2. 相似度搜索
3. 更新 / 替换
4. 删除
5. metadata 过滤

第四章接下来的代码，就是围绕这五件事展开。

---

## 3. 为什么只有向量还不够 📌

第三章已经让系统拥有：

- chunk 身份
- metadata
- 向量表示

但系统还必须回答：

- 向量放在哪里
- 重启以后还能不能查
- 同一份文档怎样整体替换
- query 和库存向量是不是同一个 embedding space
- metadata 能不能进入真实查询路径

如果这些问题没有先立住，第五章的 Retriever 只会建立在松散对象上。

### 3.1 存储层负责什么

向量存储层至少要负责五件事：

1. 存向量
2. 查向量
3. 保留向量和原始 chunk / metadata 的绑定关系
4. 支持删除和文档级替换
5. 守住 embedding space 一致性

它不负责：

- 重新切分文档
- 重新生成向量
- 优化召回策略
- 组织 Prompt
- 让 LLM 生成答案

### 3.2 第四章要立住的最小契约

1. 同一个 store 只能保存一个 provider / model / dimensions 空间
2. query 和 stored vectors 必须来自同一个 embedding space
3. metadata 不能在写入时悄悄丢失
4. `upsert()` 和 `replace_document()` 必须是两个不同语义
5. `document_id` 删除必须是真实能力，不是演示名词

---

## 4. 原理层：最小 JSON store

### 4.1 这一层解决什么

这一层对应：

- [vector_store_basics.py](../../source/04_rag/04_vector_databases/vector_store_basics.py)
- [01_index_store.py](../../source/04_rag/04_vector_databases/01_index_store.py)
- [02_search_store.py](../../source/04_rag/04_vector_databases/02_search_store.py)
- [03_delete_document.py](../../source/04_rag/04_vector_databases/03_delete_document.py)

它的目标不是替代真实向量库，而是先把以下问题讲清楚：

- 向量怎么持久化
- 查询怎么校验 embedding space
- `replace_document()` 和 `upsert()` 为什么不是一回事
- 删除为什么必须围绕 `document_id`

### 4.2 JSON store 当前交付

`PersistentVectorStore` 当前交付：

1. `upsert()`
2. `replace_document()`
3. `load_chunks()`
4. `similarity_search()`
5. `delete_by_document_id()`
6. `embedding_space()`

### 4.3 这一层刻意简化了什么

原理层刻意简化了：

1. 只用本地 JSON 文件
2. 只做最小相似度查询
3. 过滤只支持 `filename`
4. 不引入外部索引库

这不是因为这些能力不重要，而是为了先把存储层契约看清楚。

---

## 5. Chroma 实践（对应大纲第 11 节） 📌

### 5.1 为什么选 Chroma

在第四章里，`Chroma` 是合适的第一站真实工具层：

- 有真实持久化目录
- 有真实 collection
- 能直接做 query / filter / delete
- 足够轻量，适合作为课程里的第一种真实数据库

### 5.2 本章里 Chroma 的定位

本章不是做 Chroma 产品横评，而是用 Chroma 去对照你刚学会的原理层动作：

| 原理层 | Chroma 层 |
|--------|-----------|
| `PersistentVectorStore` | `ChromaVectorStore` |
| JSON 文件 | persistent collection |
| `filename` 过滤 | metadata `where` |
| `delete_by_document_id()` | Chroma `delete(where=...)` |
| `load_chunks()` | 从 Chroma 读回并重新水合 |

### 5.3 Chroma 层为什么还要做自己的契约校验

真实向量数据库不会替你自动保证：

- provider 一致
- model 一致
- dimensions 一致

所以第四章的 `ChromaVectorStore` 仍然会把：

- `provider_name`
- `model_name`
- `dimensions`
- `chunk_id`
- `document_id`

写进 metadata，并在读取和查询时自己做校验。

### 5.4 Chroma 的 CRUD 与过滤

当前代码入口：

- [chroma_store.py](../../source/04_rag/04_vector_databases/chroma_store.py)
- [04_chroma_crud.py](../../source/04_rag/04_vector_databases/04_chroma_crud.py)
- [05_chroma_filter_delete.py](../../source/04_rag/04_vector_databases/05_chroma_filter_delete.py)

这一层当前覆盖：

1. 添加 / 替换
2. 查询
3. 按 `document_id` 删除
4. metadata 过滤
5. 复合过滤

这里需要注意一个真实细节：

> Chroma 的复合 `where` 过滤不是简单多 key dict，而是显式 `$and` 条件。

第五章不会再回头讲这个细节，所以第四章就要先把这件事讲清楚。

---

## 6. 基于 LangChain 的向量数据库接入（对应大纲第 12 节） 📌

### 6.1 为什么第四章现在还要补 LangChain

只会原生 Chroma API 还不够，因为工程里很常见的上层接口是：

> `VectorStore`

也就是：

- 你不一定直接调数据库 SDK
- 你可能通过 LangChain 等上层抽象接入同一个数据库

### 6.2 这一章里 LangChain 的关注点

第四章不再重讲平台 embeddings 接入，而是只关注：

1. 现有 `EmbeddingProvider` 怎样包装成 LangChain `Embeddings`
2. `SourceChunk` 怎样映射成 LangChain `Document`
3. `add_documents()` 和 `from_documents()` 是什么关系
4. `similarity_search()`、`similarity_search_with_score()` 怎样对应存储层查询
5. `as_retriever()` 的接口长什么样

### 6.3 当前映射关系

| 第四章对象/能力 | LangChain 对应 |
|----------------|----------------|
| `EmbeddingProvider` | `ProviderEmbeddingsAdapter` |
| `SourceChunk` | `Document` |
| `filename` metadata | `filter={"filename": ...}` |
| query 搜索 | `similarity_search()` / `similarity_search_with_score()` |
| 上层检索入口 | `as_retriever()` |

对应实现：

- [langchain_adapter.py](../../source/04_rag/04_vector_databases/langchain_adapter.py)
- [06_langchain_vectorstore.py](../../source/04_rag/04_vector_databases/06_langchain_vectorstore.py)

### 6.4 为什么这里不直接进入 Retriever

因为 LangChain VectorStore 仍然是：

- 向量存储抽象
- 不是 Retriever 策略层

第四章只让你看到：

- `as_retriever()` 存在
- 它是上层接口入口

真正去展开：

- `top_k`
- `threshold`
- `MMR`
- bad cases

是在第五章。

---

## 7. 综合案例：向量存储管理器

大纲要求的不是“再写一个 backend 对照脚本”，而是一个最小可扩展管理器。

当前代码入口：

- 模块：[vector_store_manager.py](../../source/04_rag/04_vector_databases/vector_store_manager.py)
- CLI：[07_vector_store_manager.py](../../source/04_rag/04_vector_databases/07_vector_store_manager.py)

### 7.1 这个综合案例解决什么

它要把这些动作统一起来：

1. `add_documents()`
2. `search()`
3. `replace_document()`
4. `delete_document()`

并且把这些动作统一映射到不同 backend：

- `json`
- `chroma`
- `langchain`

### 7.2 当前 manager 的边界

当前 `VectorStoreManager` 是教学最小实现，所以有两个边界要说明白：

1. 一条输入文本先当成一个文档块，不在这里引入切分流水线
2. 大纲里提到的 `FAISS` 当前不做硬接入，而是保留适配器扩展位

这不是偷懒，而是因为第四章真正要先立住的是：

> “统一接口”比“堆更多 backend 名字”更重要。

### 7.3 当前综合案例已覆盖什么

1. 自动 embedding 处理
2. 文档添加
3. 文档删除
4. 文档替换
5. metadata 透传
6. backend 适配

也就是说，第四章现在已经从：

- 只会单独跑 JSON
- 只会单独跑 Chroma
- 只会单独跑 LangChain

推进到了：

- 有一个统一管理入口

---

## 8. 第四章实践：建议运行顺序

### 8.1 安装依赖

```bash
cd source/04_rag/04_vector_databases
python -m pip install -r requirements.txt
```

### 8.2 先跑原理层

```bash
python 01_index_store.py --reset
python 02_search_store.py
python 02_search_store.py "为什么 metadata 很重要？" --filename metadata_rules.md
python 03_delete_document.py trial
```

你应该观察到：

- JSON store 的持久化路径
- `replace_document()` 的默认写入路径
- `filename` 过滤怎么缩小范围
- 删除为什么围绕 `document_id`

### 8.3 再跑 Chroma

```bash
python 04_chroma_crud.py --reset
python 05_chroma_filter_delete.py "为什么 metadata 很重要？" --filename metadata_rules.md --suffix .md --document-id metadata
python 05_chroma_filter_delete.py "如何申请退费？" --delete-document-id trial
```

你应该观察到：

- Chroma 真的创建了 collection
- metadata filter 现在走真实数据库
- 复合过滤会显式落成 `$and`
- 删除和替换已经不是“本地文件操作”，而是数据库行为

### 8.4 最后跑 LangChain Chroma

```bash
python 06_langchain_vectorstore.py "为什么 metadata 很重要？" --filename metadata_rules.md --init-mode add_documents --reset
python 06_langchain_vectorstore.py "为什么 metadata 很重要？" --filename metadata_rules.md --init-mode from_documents
python 06_langchain_vectorstore.py "如何申请退费？" --retriever-search-type mmr
```

你应该观察到：

- 同一个 provider 可以通过 LangChain `Embeddings` 适配器接入
- `add_documents()` 和 `from_documents()` 都只是不同初始化入口
- `as_retriever()` 现在只做接口演示，策略解释放到第五章

### 8.5 跑统一管理器

```bash
python 07_vector_store_manager.py --backend json --delete-document-id trial "如何申请退费？"
python 07_vector_store_manager.py --backend chroma --add-document-id faq --add-text "课程退款请联系助教。" "如何申请退费？"
python 07_vector_store_manager.py --backend langchain --replace-document-id trial --replace-text "试学需要提前预约并完成登记。" "如何预约试学？"
```

你应该观察到：

- manager 已经不是纯 backend 对照脚本
- 它已经具备真实 `add / search / replace / delete`
- 不同 backend 的调用形态不同，但管理职责相同

### 8.6 测试

```bash
python -m unittest discover -s tests
```

当前测试锁定四层行为：

1. JSON store
2. 原生 Chroma
3. LangChain Chroma
4. `VectorStoreManager`

---

## 9. Mini 回归集

第四章当前的最小回归观察点至少包括：

1. `如何申请退费？` 应优先命中 `refund:0`
2. `为什么 metadata 很重要？` 应优先命中 `metadata:0`
3. `filename=metadata_rules.md` 过滤后，结果范围必须明显收窄
4. Chroma 复合过滤会使用显式 `$and`
5. 删除 `trial` 后，不应再保留该文档 chunk
6. query 和 store 若不在同一 embedding space，应直接失败

---

## 10. 本章学完后你应该能回答

- 为什么 `EmbeddedChunk[]` 还不等于可用检索系统
- 为什么第四章必须同时讲原理层和真实工具层
- 为什么第 10 节的“选型基础”更适合先放在文档里讲清楚
- 为什么 `upsert()` 和 `replace_document()` 不能混成一个模糊接口
- 为什么真实 Chroma 里仍然要自己守住 embedding space
- 为什么 LangChain VectorStore 仍然属于第四章，而不是第五章
- 为什么综合案例需要统一 manager，而不是继续堆 backend 对照脚本

---

## 11. 下一章

第五章开始，你才会真正进入 Retriever 策略：

- `top_k`
- `threshold`
- `MMR`
- bad cases

也就是说：

> 第四章解决“能不能稳地存和查”，第五章解决“怎么查得更好”。
