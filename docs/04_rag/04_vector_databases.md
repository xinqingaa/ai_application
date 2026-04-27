# 04. 向量数据库

> 本章目标：把第三章的 `EmbeddedChunk[]` 推进成真正可持久化、可查询、可替换、可删除的存储层。你会先建立第四章自己的运行时主线和存储契约，再看最小 JSON store，然后进入真实 `Chroma` 和 `LangChain VectorStore`，最后用一个最小 `VectorStoreManager` 把不同 backend 收束成统一接口。

---

## 1. 概述

### 学习目标

- 理解为什么第三章的 `EmbeddedChunk[]` 还不等于可用检索系统
- 理解向量数据库在 RAG 工程中的职责边界
- 掌握第四章的核心契约：`upsert / replace_document / similarity_search / delete_by_document_id`
- 理解 JSON store、Chroma、LangChain Chroma 在本章里的对应关系
- 认识 `ANN vs 精确搜索` 的权衡和主流向量数据库的选型差异
- 了解为什么第四章要有统一的 `VectorStoreManager`

### 预计学习时间

- 存储层主线与契约：40 分钟
- 原理层 JSON store：40-60 分钟
- Chroma 与 LangChain 映射：40-60 分钟
- 管理器与实践闭环：40-60 分钟

### 本章在 AI 应用中的重要性

| 场景 | 本章先解决什么 |
|------|----------------|
| 知识库存储 | 向量怎样真正写进可持久化系统 |
| 检索查询 | query 怎样在存储层里查回候选 chunk |
| 数据治理 | 文档替换、删除、过滤怎样落到真实接口 |
| 框架接入 | 原生数据库 API 与 LangChain VectorStore 怎样对应 |

### 学习前提

- 建议先完成第三章，已经理解 `SourceChunk[] -> EmbeddedChunk[]`
- 建议已经理解 `provider_name / model_name / dimensions` 的 embedding space 约束
- 如果你已经接触过 LangChain `Document` / `VectorStore` 抽象，读起来会更快

这一章不再重复讲：

- 向量是怎样生成的
- `embed_query / embed_documents` 的基础语义
- OpenAI-compatible embeddings 的接入细节

第四章只关注存储层 specific 的问题。

### 本章与前后章节的关系

第三章已经解决：

1. `SourceChunk[] -> EmbeddedChunk[]`
2. `embed_query / embed_documents`
3. provider / model / dimensions 的最小契约

第四章继续解决：

1. 向量怎样真正落到持久化存储
2. 查询怎样把结果重新还原成标准 chunk
3. metadata 和 `document_id` 怎样进入真实查询 / 更新 / 删除路径
4. 原理层和真实工具层怎样一一对应

第五章才继续解决：

1. `top_k / threshold / MMR`
2. Retriever 抽象
3. “怎么查得更好”

### 本章代码入口

- [README.md](../../source/04_rag/04_vector_databases/README.md)
- [requirements.txt](../../source/04_rag/04_vector_databases/requirements.txt)
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
- [tests/test_vector_store.py](../../source/04_rag/04_vector_databases/tests/test_vector_store.py)
- [tests/test_chroma_store.py](../../source/04_rag/04_vector_databases/tests/test_chroma_store.py)
- [tests/test_langchain_vectorstore.py](../../source/04_rag/04_vector_databases/tests/test_langchain_vectorstore.py)
- [tests/test_vector_store_manager.py](../../source/04_rag/04_vector_databases/tests/test_vector_store_manager.py)

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

这里故意只保留：

- 一个最小 JSON store
- 一个真实 `Chroma` backend
- 一个 LangChain Chroma 适配层
- 一个教学最小 `VectorStoreManager`

目的不是追求“数据库覆盖最多”，而是先把第四章存储层主线讲清楚。

### 本章学习地图

建议按下面这条主线阅读本章，而不是一开始就陷入某个数据库名、某个 SDK 或某个过滤语法：

```text
先看第四章完整主线
-> 再看运行时对象和存储层契约
-> 再用最小 JSON store 理解持久化 / 查询 / 替换 / 删除
-> 再看真实向量数据库解决的工程问题
-> 再进入 Chroma 和 LangChain 映射
-> 最后看统一 manager 如何收束不同 backend
```

这一章后面的失败案例、治理锚点和建议运行顺序，更适合在你已经跑过代码以后回头复盘。

---

## 2. 向量存储层的完整流程 📌

第四章可以先不要从“哪个向量数据库更好”开始，而是先建立一条完整主线。

这一章做的是把第三章留下来的稳定 `EmbeddedChunk[]`，加工成后续 Retriever 可以稳定消费的持久化查询层：

```text
EmbeddedChunk[]
-> 校验 embedding space
-> upsert() / replace_document()
-> 写入 JSON records / Chroma collection / LangChain VectorStore
-> query 也使用同一个 embedding provider
-> similarity_search()
-> metadata filter
-> RetrievalResult[]
-> delete_by_document_id()
```

这条链路里每一步都有明确输入和输出：

| 阶段 | 输入 | 输出 | 对应代码 |
|------|------|------|----------|
| 样例资产准备 | `SourceChunk[]` | `EmbeddedChunk[]` | `demo_source_chunks()` / `embed_chunks()` |
| 空间身份校验 | provider / model / dimensions | `EmbeddingSpace` | `embedding_space_from_provider()` / `infer_chunks_embedding_space()` |
| 原理层写入 | `EmbeddedChunk[]` | JSON records | `PersistentVectorStore.upsert()` / `replace_document()` |
| 原理层查询 | query vector + JSON records | `RetrievalResult[]` | `PersistentVectorStore.similarity_search()` |
| 真实数据库写入 | `EmbeddedChunk[]` | Chroma collection | `ChromaVectorStore.upsert()` / `replace_document()` |
| 真实数据库查询 | query vector + `where` | `RetrievalResult[]` | `ChromaVectorStore.similarity_search()` |
| 框架映射 | `SourceChunk[]` + provider | LangChain `Document` / `Embeddings` | `build_documents()` / `ProviderEmbeddingsAdapter` |
| 统一入口 | backend + 操作参数 | 标准 add / search / replace / delete | `VectorStoreManager` |

初学时可以先记住一个判断标准：

> 第三章解决“文本怎样进入同一个可比较的向量空间”，第四章解决“这些向量怎样被稳定地存、查、换、删”。

后面的章节会按这条主线展开：先讲存储层主流程，再讲对象和契约，再用 JSON store 建立原理闭环，然后映射到 Chroma、LangChain 和统一 manager。

---

## 3. 主流程拆解：从 `EmbeddedChunk[]` 到 `RetrievalResult[]` 📌

### 3.1 第三章交付的内容

第三章已经让系统拥有：

- chunk 身份
- metadata
- 向量表示

但它还没有解决：

- 向量放在哪里
- 重启以后还能不能查
- 同一份文档怎样整体替换
- query 和库存向量是不是同一个 embedding space
- metadata 能不能进入真实查询路径

### 3.2 第四章新增的标准接口

第四章真正新增的不是“再做一次相似度计算”，而是：

```text
EmbeddedChunk[]
-> store.upsert() / store.replace_document()
-> persisted records / collection
-> similarity_search()
-> RetrievalResult[]
```

也就是说，第四章新增的是：

- 持久化
- 查询入口
- 删除和替换能力
- 存储层契约

### 3.3 只有向量还不够

如果系统只有内存中的 `EmbeddedChunk[]`，后面很快会出现问题：

- 进程重启以后索引直接消失
- 无法把一份文档整体替换掉旧 chunk
- 无法按 `document_id` 删除
- metadata 过滤没有真实落点
- query 很容易和错误的 store space 混用

所以第四章不是“把第三章结果放进某个库”这么简单，而是在定义：

> 后续检索层要依赖的标准存储接口。

### 3.4 第四章的运行时主链路

这一章最值得先建立手感的，不是某个数据库名，而是一条完整的运行时链路：

```text
EmbeddedChunk[]
-> upsert() / replace_document()
-> PersistentVectorStore / ChromaVectorStore / LangChain Chroma
-> similarity_search()
-> RetrievalResult[]
```

如果你能把这条链路讲清楚，第四章的大部分内容就已经真正掌握了。

### 3.5 第四章交付的是稳定存储层

很多资料会把这一章讲成：

- 接一个向量库
- 能查出结果
- 结束

这种讲法不够。

更准确的说法是：

> 第四章在定义后续 Retriever 和生成层要消费的标准存储接口。

所以这里的重点不是“查得出来”，而是：

- embedding space 要稳定
- chunk 身份不能丢
- `document_id` 要能更新和删除
- metadata 要能进入真实过滤路径
- backend 替换时接口语义要保持一致

### 3.6 存储层的职责边界

存储层负责的是：

- 存向量
- 查向量
- 保留向量和 chunk / metadata 的绑定关系
- 支持替换、删除和最小过滤

存储层不负责：

- 重新切分文档
- 重新生成向量
- 优化召回策略
- 组织 Prompt
- 让 LLM 生成答案

它的职责是“让向量可存可查可维护”，不是“替整个 RAG 做决策”。

### 3.7 现在应该建立的最小心智模型

读到这里，你应该先把第四章看成一个稳定存储层，而不是某个具体数据库教程：

```text
第三章解决：文本怎样进入同一个可比较的向量空间
第四章解决：这些向量怎样被稳定地存、查、换、删
第五章解决：这些结果怎样被更好地取回来
```

如果这条主线已经清楚，后面再去看 JSON store、Chroma、LangChain，就不会把它们误看成互不相干的专题。

---

## 4. 运行时对象与存储层契约 📌

主流程清楚以后，再看对象会更容易。第四章的对象不是为了把代码拆散，而是在共同守住存储层的不变量。

### 4.1 第四章最值得先看的运行时对象

在 [vector_store_basics.py](../../source/04_rag/04_vector_databases/vector_store_basics.py) 里，最值得先建立手感的不是“函数很多”，而是对象已经很清楚。

你可以先把这些对象看成第四章存储层的运行时骨架：

| 对象 | 作用 |
|------|------|
| `SourceChunk` | 从第三章继承来的原始 chunk 身份 |
| `EmbeddedChunk` | 进入存储层的向量增强对象 |
| `RetrievalResult` | 存储层查询返回的标准结果 |
| `EmbeddingSpace` | `provider / model / dimensions` 的统一身份标签 |
| `VectorStoreConfig` | JSON store 的最小配置 |
| `PersistentVectorStore` | 原理层本地 JSON store |
| `ChromaVectorStoreConfig` | 真实 Chroma backend 的配置 |
| `ChromaVectorStore` | Chroma 的最小适配实现 |
| `ProviderEmbeddingsAdapter` | 把本章 provider 映射成 LangChain `Embeddings` |
| `VectorStoreManager` | 不同 backend 的统一管理入口 |

这和第二、三章先看运行时对象是同一类学习方式：

> 先看清对象和契约，再看函数如何把它们串起来。

### 4.2 `EmbeddingSpace` 是第四章核心对象

很多人会把第四章只看成“存点数据”。

但真正重要的是，store 必须知道自己在存哪一个空间的向量。

`EmbeddingSpace` 明确记录：

- `provider_name`
- `model_name`
- `dimensions`

它的意义是：

- 写入时能校验 incoming chunks
- 查询时能校验 query provider
- 读取时能确认 store 没有混入异构向量

### 4.3 第四章要立住的最小契约

这一章最关键的几个约束是：

1. 同一个 store 只能保存一个 provider / model / dimensions 空间
2. query 和 stored vectors 必须来自同一个 embedding space
3. metadata 不能在写入时悄悄丢失
4. `upsert()` 和 `replace_document()` 必须是两个不同语义
5. `document_id` 删除必须是真实能力，不是演示名词

### 4.4 `upsert()` 和 `replace_document()` 的语义差异

这是第四章最容易被讲模糊的点。

`upsert()` 的语义是：

- 按 `chunk_id` 写入或覆盖
- 不主动删除同文档里旧的其他 chunk

`replace_document()` 的语义是：

- 先围绕 `document_id` 找到整份文档的旧 chunk
- 再用新的 chunk 集合整体替换

也就是说：

> `upsert()` 解决的是“这几个 chunk 怎么写进去”，`replace_document()` 解决的是“这份文档怎么整体换代”。

### 4.5 删除围绕 `document_id`

如果删除只能按 `chunk_id` 做，现实里很快会出问题：

- 同一份文档切成多个 chunk 时删不干净
- 替换文档时容易留下 stale chunks
- 调试时也很难确认是文档没删净还是排序出了问题

所以第四章必须把：

- `delete_by_document_id()`

立成真实能力，而不是只在文档里提一下名字。

### 4.6 `RetrievalResult` 的返回形状

第四章不是直接返回一组裸分数，而是返回：

- `chunk`
- `score`

这说明存储层在做的不是“向量算分工具”，而是在做：

> 能把相似度结果重新还原成标准 chunk 结果的查询层。

第五章的 Retriever 也正是建立在这个结果形状之上。

### 4.7 错误在第四章尽早失败

第四章有几类错误必须尽早失败：

- query vector 维度不对
- incoming chunks 的 embedding space 不一致
- store 中混入不同 provider / model 的向量
- `top_k <= 0`
- LangChain / Chroma 依赖缺失

这些错误如果不在第四章拦住，后面就会变成更难排查的“为什么检索效果越来越怪”。

### 4.8 这一节和代码主入口的对应关系

现在最推荐先看的不是所有脚本，而是这些实现入口：

- [vector_store_basics.py](../../source/04_rag/04_vector_databases/vector_store_basics.py)
- [chroma_store.py](../../source/04_rag/04_vector_databases/chroma_store.py)
- [langchain_adapter.py](../../source/04_rag/04_vector_databases/langchain_adapter.py)
- [vector_store_manager.py](../../source/04_rag/04_vector_databases/vector_store_manager.py)

这一遍只需要回答一个问题：

```text
第四章到底在围绕哪些对象和哪些不变量组织代码？
```

如果这个问题已经有答案，后面看各 backend 时就会更稳。

---

## 5. 原理层：最小 JSON store 📌

真实数据库之前，第四章先保留一个最小 JSON store。它不是为了替代向量数据库，而是为了把存储层契约用最少依赖讲清楚。

### 5.1 原理层解决的内容

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

### 5.2 `PersistentVectorStore` 当前交付的能力

`PersistentVectorStore` 当前交付：

1. `upsert()`
2. `replace_document()`
3. `load_chunks()`
4. `similarity_search()`
5. `delete_by_document_id()`
6. `embedding_space()`
7. `list_document_ids()`
8. `count()`

### 5.3 JSON store 持久化的内容

JSON store 不是只把向量数组直接 dump 掉。

它真正持久化的是：

- `chunk.chunk_id`
- `chunk.document_id`
- `chunk.content`
- `chunk.metadata`
- `vector`
- `provider_name`
- `model_name`
- `dimensions`
- store 级的 `embedding_space`

这意味着第四章从原理层开始就在强调：

> 向量从来不是脱离 chunk 身份和空间身份单独存在的。

### 5.4 `similarity_search()` 的查询动作

这个函数看上去只是最小 cosine similarity 排序，但它其实同时在做三件事：

1. 校验 `top_k`
2. 校验 query vector 维度
3. 校验 query provider 和 store 中 chunk 的 embedding space 一致

然后才会：

- 过滤 `filename`
- 计算分数
- 组装 `RetrievalResult[]`

### 5.5 原理层的 `filename` 过滤

JSON store 当前只支持：

- `filename`

这不是因为 metadata 过滤不重要，而是为了先把过滤入口的最小语义讲清楚。

它真正要让你看到的是：

- metadata 过滤不是第五章才出现
- 第四章就必须有真实的过滤落点
- 后面换到 Chroma 时，过滤只是从本地条件判断映射到数据库 `where`

### 5.6 原理层刻意简化的范围

原理层刻意简化了：

1. 只用本地 JSON 文件
2. 只做最小相似度查询
3. 过滤只支持 `filename`
4. 不引入外部索引库

这不是因为这些能力不重要，而是为了先把存储层契约看清楚。

### 5.7 先学原理层，再看真实数据库

如果一开始就直接进入 Chroma 或 LangChain，读者很容易把注意力放到：

- SDK 怎么调
- collection 参数叫什么
- filter 语法长什么样

这样会错过第四章真正的主线。

先学 JSON store 的意义是：

> 先把“写入 / 查询 / 替换 / 删除 / 空间一致性”这套骨架看懂，再去看真实数据库只是怎么把这些骨架落到更真实的存储接口上。

### 5.8 现在应该建立的最小闭环

读完这一节，你至少应该能自己讲清楚这条最小闭环：

```text
EmbeddedChunk[]
-> PersistentVectorStore.upsert() / replace_document()
-> JSON records
-> similarity_search()
-> RetrievalResult[]
```

如果你已经能讲清这条链路，后面切到真实数据库时就不会失焦。

---

## 6. 真实向量数据库：从原理层走向工程存储 📌

JSON store 可以帮助你看清契约，但现实工程仍然需要真正的向量数据库。这里先补齐向量数据库的基本认知，再进入本章选择的 Chroma 实践。

### 6.1 向量数据库的职责

向量数据库本质上是在解决三件事：

1. 把高维向量稳定存下来
2. 能用相似度快速查回最相关的向量
3. 让向量和原始文档、metadata、文档身份保持绑定

所以它不是“只会存一个 `list[float]` 的数据库”，而是：

> 面向语义检索场景的存储和查询系统。

### 6.2 ANN vs 精确搜索

这一节至少要先知道：

- 精确搜索会逐个比较候选，结果最准，但规模一大就慢
- `ANN`（Approximate Nearest Neighbor）会牺牲一点精确性，换取更好的查询速度

第四章当前不会手写 ANN 索引实现，因为这会把注意力从“存储契约”拉走。

你现在只需要先建立这个判断：

- 教学 demo、小规模数据：可以先不深挖 ANN 细节
- 真正上线、数据量大：ANN 是现实选择

### 6.3 主流向量数据库的最小选型表

这一节按大纲要求做认知对齐，但不强行给每个库都补 demo。

| 数据库 | 特点 | 更适合什么 |
|--------|------|------------|
| Chroma | 轻量、上手快、本地持久化方便 | 教学、原型、小项目 |
| FAISS | Meta 开源、纯本地、高性能 | 本地实验、离线索引、高性能原型 |
| Pinecone | 云服务、免运维 | 不想自建基础设施的生产场景 |
| Milvus | 开源、分布式、规模能力强 | 大规模生产部署 |
| Weaviate | 开源、功能丰富 | 企业知识库和复杂检索场景 |

第四章当前只正式实现 `Chroma` 的原因：

- 它最适合作为第一站真实数据库
- 能直接看清 persistent collection、metadata filter、delete
- 不会让课程一开始就掉进运维和平台差异里

这里不硬造 FAISS / Pinecone / Milvus demo 的原因：

> 本节的核心是选型认知，不是为了“代码覆盖率”而把第四章拖成工具拼盘。

### 6.4 向量数据库的核心操作

无论你最终用哪一种库，这一章都要先把下面这些动作立住：

1. 插入向量
2. 相似度搜索
3. 更新 / 替换
4. 删除
5. metadata 过滤

第四章接下来的代码，就是围绕这五件事展开。

### 6.5 这一节在学习顺序中的位置

如果把选型、ANN、数据库横向认知放在文档更前面，读者很容易在还没理解第四章主线之前，就先陷入：

- “到底该选哪个库”
- “ANN 原理怎么实现”
- “不同数据库名字有什么区别”

把这一节放在 JSON store 之后的目的，是先让你知道：

> 真实向量数据库不是在替换第四章主线，而是在承接你已经看懂的存储层契约。

---

## 7. Chroma：真实持久化 collection 与过滤 📌

从这一节开始，第四章从原理层进入真实工具层。Chroma 在这里承担第一种真实向量数据库 backend 的角色。

### 7.1 Chroma 在本章里的位置

在第四章里，`Chroma` 是合适的第一站真实工具层：

- 有真实持久化目录
- 有真实 collection
- 能直接做 query / filter / delete
- 足够轻量，适合作为课程里的第一种真实数据库

### 7.2 Chroma 与原理层的映射关系

本章不是做 Chroma 产品横评，而是用 Chroma 去对照你刚学会的原理层动作：

| 原理层 | Chroma 层 |
|--------|-----------|
| `PersistentVectorStore` | `ChromaVectorStore` |
| JSON 文件 | persistent collection |
| `filename` 过滤 | metadata `where` |
| `delete_by_document_id()` | Chroma `delete(where=...)` |
| `load_chunks()` | 从 Chroma 读回并重新水合 |

### 7.3 `ChromaVectorStore` 补上的能力

这一层当前补的是：

1. 真实持久化目录
2. collection 级存储
3. query-time `where` 过滤
4. 批量写入
5. 从 Chroma 响应重新水合 `EmbeddedChunk / RetrievalResult`

### 7.4 Chroma 层仍然保留契约校验

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

### 7.5 Chroma 的 CRUD 与过滤

对应代码入口：

- [chroma_store.py](../../source/04_rag/04_vector_databases/chroma_store.py)
- [04_chroma_crud.py](../../source/04_rag/04_vector_databases/04_chroma_crud.py)
- [05_chroma_filter_delete.py](../../source/04_rag/04_vector_databases/05_chroma_filter_delete.py)

这一层当前覆盖：

1. 添加 / 替换
2. 查询
3. 按 `document_id` 删除
4. metadata 过滤
5. 复合过滤

### 7.6 Chroma metadata 中的内部字段

在 Chroma 这一层，metadata 不只是原文 metadata。

它还会补进内部字段，例如：

- `_rag_chunk_id`
- `_rag_document_id`
- `_rag_provider_name`
- `_rag_model_name`
- `_rag_dimensions`

这样做不是“字段太多”，而是在保证：

- store 读回后还能恢复标准对象
- embedding space 校验有真实落点
- 删除和过滤不依赖外部额外索引

### 7.7 复合 `where` 过滤

这里需要注意一个真实细节：

> Chroma 的复合 `where` 过滤不是简单多 key dict，而是显式 `$and` 条件。

第五章不会再回头讲这个细节，所以第四章就要先把这件事讲清楚。

### 7.8 从这一节应该带走的内容

这一节最重要的不是“会不会调用 Chroma SDK”，而是：

```text
你已经在 JSON store 里看懂的契约
-> 现在怎样落成真实 collection / metadata / delete / query 行为
```

如果你带着这条映射去看代码，Chroma 层会清楚很多。

---

## 8. LangChain VectorStore：框架抽象映射 📌

很多工程不会直接调用数据库 SDK，而是通过 LangChain 这类框架抽象接入向量库。第四章在这里讲的仍然是存储层映射，不是检索策略。

### 8.1 LangChain 进入第四章的原因

只会原生 Chroma API 还不够，因为工程里很常见的上层接口是：

> `VectorStore`

也就是：

- 你不一定直接调数据库 SDK
- 你可能通过 LangChain 等上层抽象接入同一个数据库

### 8.2 本章里 LangChain 的关注点

第四章不再重讲平台 embeddings 接入，而是只关注：

1. 现有 `EmbeddingProvider` 怎样包装成 LangChain `Embeddings`
2. `SourceChunk` 怎样映射成 LangChain `Document`
3. `add_documents()` 和 `from_documents()` 是什么关系
4. `similarity_search()`、`similarity_search_with_score()` 怎样对应存储层查询
5. `as_retriever()` 的接口长什么样

### 8.3 当前映射关系

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

### 8.4 `ProviderEmbeddingsAdapter` 的作用

这个适配器的意义不是“又包了一层没必要的壳”，而是：

> 用第四章已经建立的 provider 契约，去对接 LangChain 期待的 `Embeddings` 接口。

这样做的价值是：

- 课程里前面建立的 provider 设计不会被框架抽象打断
- 你能看清“框架接入”其实是在映射现有契约，而不是重新发明一套 embedding 语义

### 8.5 `build_documents()` 和结果反序列化

LangChain `Document` 不是第四章自己的对象。

所以这里必须做双向映射：

- 写入前：`SourceChunk -> Document`
- 读取后：`Document / scored documents -> RetrievalResult`

对应函数就是：

- `build_documents()`
- `similarity_results_from_documents()`
- `retrieval_results_from_scored_documents()`

### 8.6 这里暂时不进入 Retriever

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

### 8.7 这一节和前后章节的衔接

这里最容易混淆的点是：

- `as_retriever()` 已经出现，但这一节仍然属于第四章。

原因是这一节仍然在做：

> 存储层接口映射。

也就是说，第四章现在是在讲：

- 底层数据库怎样对接
- 框架抽象怎样承接

但还没有正式进入：

- 检索策略怎么调
- 结果怎么优化

这也是它仍然属于第四章，而不是第五章的原因。

---

## 9. 综合案例：向量存储管理器 📌

当你已经分别看过 JSON、Chroma、LangChain 之后，第四章最后用一个最小管理器把不同 backend 收束成统一入口。

### 9.1 综合案例解决的内容

大纲要求的不是“再写一个 backend 对照脚本”，而是一个最小可扩展管理器。

对应代码入口：

- 模块：[vector_store_manager.py](../../source/04_rag/04_vector_databases/vector_store_manager.py)
- CLI：[07_vector_store_manager.py](../../source/04_rag/04_vector_databases/07_vector_store_manager.py)

它要把这些动作统一起来：

1. `add_documents()`
2. `search()`
3. `replace_document()`
4. `delete_document()`

并且把这些动作统一映射到不同 backend：

- `json`
- `chroma`
- `langchain`

### 9.2 第四章需要 manager 的原因

如果第四章只停留在：

- 单独跑 JSON
- 单独跑 Chroma
- 单独跑 LangChain

你会知道“每个 backend 都能工作”，但你还不知道：

> 它们能不能被一个更稳定的上层接口统一起来。

这正是 `VectorStoreManager` 的价值。

### 9.3 当前 manager 的边界

当前 `VectorStoreManager` 是教学最小实现，所以有两个边界要说明白：

1. 一条输入文本先当成一个文档块，不在这里引入切分流水线
2. 大纲里提到的 `FAISS` 当前不做硬接入，而是保留适配器扩展位

这不是偷懒，而是因为第四章真正要先立住的是：

> “统一接口”比“堆更多 backend 名字”更重要。

### 9.4 当前综合案例已覆盖的能力

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

### 9.5 manager 收束职责而不是抹平差异

这一点很重要。

`json / chroma / langchain` 三个 backend 的底层形态并不一样：

- JSON store 是文件记录
- Chroma 是原生 collection
- LangChain 是框架包装后的向量存储接口

但 manager 统一的是：

- add
- search
- replace
- delete

所以它在做的是职责收束，而不是假装所有底层完全相同。

### 9.6 manager 放在后面的学习价值

如果在一开始就看 manager，读者很容易误以为第四章的重点是：

- 写一个统一门面类
- 适配多个 backend

但这会把更重要的东西遮住：

- 第四章到底在保什么契约
- backend 差异具体落在什么位置

把 manager 放在 JSON / Chroma / LangChain 之后，目的是先分清：

> 统一接口是在收束已经看懂的职责，不是在替代你理解底层差异。

---

## 10. 存储层治理与最小回归锚点 📌

第四章还没有进入 Retriever 策略，但已经开始出现持久化状态和 backend 差异，所以这里必须建立最小治理锚点。

### 10.1 第四章建立治理视角的原因

很多人会把“治理”理解成很后面的企业级平台问题。

但第四章已经必须有最小治理视角，因为这里已经开始出现：

- 持久化状态
- 文档替换
- 文档删除
- metadata 过滤
- backend 切换

如果这里不先立住锚点，第五章以后很难判断：

- 是检索策略变了
- 是存储层状态脏了
- 还是 embedding space 已经混了

### 10.2 第四章最重要的治理锚点

这一章里最值得先立住的锚点至少有五个：

1. `chunk_id / document_id`
2. `provider_name / model_name / dimensions`
3. `filename` 等 metadata
4. store 的持久化路径或 collection 名称
5. `RetrievalResult` 的标准返回形状

它们共同回答的是：

- 当前存的是谁
- 当前属于哪个空间
- 当前删除 / 替换的对象是谁
- 当前查询命中的结果能不能还原成标准 chunk

### 10.3 治理锚点缺失后的连锁问题

如果这些锚点没有先立住，后面很快会出现问题：

- 你不知道一条查询结果属于哪份文档
- 你不知道 stale chunks 是替换没删净还是排序有问题
- 你不知道不同 backend 的结果差异来自框架还是来自 embedding space
- 你不知道 metadata filter 是真的生效了，还是只是样例凑巧命中

所以第四章的治理视角不是企业级治理平台，而是：

> 先把存储层最小不变量立住。

### 10.4 第四章最小回归观察点

第四章当前的最小回归观察点至少包括：

1. `如何申请退费？` 应优先命中 `refund:0`
2. `为什么 metadata 很重要？` 应优先命中 `metadata:0`
3. `filename=metadata_rules.md` 过滤后，结果范围必须明显收窄
4. Chroma 复合过滤会使用显式 `$and`
5. 删除 `trial` 后，不应再保留该文档 chunk
6. query 和 store 若不在同一 embedding space，应直接失败
7. 不同 backend 返回的仍然应该是同一类 `RetrievalResult`

### 10.5 第四章最值得刻意观察的失败案例

第四章至少要刻意看五类失败：

1. embedding space 混用失败
   - query provider 和 store 空间不一致

2. 文档替换失败
   - `replace_document()` 后旧 chunk 没有被清掉

3. 删除失败
   - `delete_by_document_id()` 后同文档结果仍然残留

4. metadata 过滤失败
   - 过滤后结果没有明显收窄

5. 依赖缺失失败
   - `chromadb` 或 `langchain_chroma` 缺失时无法进入真实 backend

这些失败案例会帮你分清：

- 哪些是章节边界
- 哪些是存储层不变量
- 哪些变化会直接影响第五章

### 10.6 治理视角和前面各节的关系

到这里你应该能把前面几节连成一条更完整的因果链：

```text
先定义稳定存储层主线
-> 再定义对象和契约
-> 再用 JSON store 验证最小闭环
-> 再映射到真实数据库和框架抽象
-> 最后用治理锚点保证这套东西后面还能持续复用和排错
```

这条链路一旦建立，第五章的检索策略调整才不会失去参照物。

---

## 11. 代码实践：按流程阅读第四章 📌

这一节把前面的抽象落实到代码阅读和命令运行。建议不要一上来就从 `07_vector_store_manager.py` 开始，因为 manager 会把很多 backend 细节藏起来。

更适合的顺序是：

```text
先跑 JSON store
-> 再跑 Chroma
-> 再跑 LangChain Chroma
-> 最后跑 VectorStoreManager
-> 回头看 tests 在锁什么
```

### 11.1 目录结构

本章代码目录是：

```text
source/04_rag/04_vector_databases/
├── README.md
├── requirements.txt
├── vector_store_basics.py
├── chroma_store.py
├── langchain_adapter.py
├── vector_store_manager.py
├── 01_index_store.py
├── 02_search_store.py
├── 03_delete_document.py
├── 04_chroma_crud.py
├── 05_chroma_filter_delete.py
├── 06_langchain_vectorstore.py
├── 07_vector_store_manager.py
├── store/
└── tests/
    ├── test_vector_store.py
    ├── test_chroma_store.py
    ├── test_langchain_vectorstore.py
    └── test_vector_store_manager.py
```

这些文件可以分成四层：

| 层次 | 文件 | 作用 |
|------|------|------|
| 原理层 | `vector_store_basics.py` / `01-03` | 用 JSON store 看清存储契约 |
| 真实数据库层 | `chroma_store.py` / `04-05` | 把同一套契约落到 Chroma |
| 框架映射层 | `langchain_adapter.py` / `06` | 把 provider 和 chunk 映射到 LangChain |
| 统一管理层 | `vector_store_manager.py` / `07` | 收束不同 backend 的增删查改 |

### 11.2 本章的输入和输出

第四章的输入不是原始文件，也不是裸文本，而是第三章已经形成的稳定对象：

```text
SourceChunk[] -> EmbeddedChunk[]
```

第四章的标准输出也不是一组裸向量分数，而是：

```text
RetrievalResult[]
```

这意味着第四章的代码要同时保住三类信息：

- chunk 身份：`chunk_id / document_id`
- metadata：`source / filename / suffix / char_start / char_end / chunk_chars`
- embedding space：`provider_name / model_name / dimensions`

如果输出结果里只剩下向量分数，第四章就没有真正完成任务。

### 11.3 本章最值得先看的对象和函数

第一遍阅读时，建议先看这些对象：

| 对象 | 阅读重点 |
|------|----------|
| `SourceChunk` | 第三章传下来的 chunk 身份和 metadata |
| `EmbeddedChunk` | chunk 加向量后的存储层输入 |
| `RetrievalResult` | 第四章对外返回的标准查询结果 |
| `EmbeddingSpace` | provider / model / dimensions 的统一身份 |
| `PersistentVectorStore` | 最小 JSON store 的契约实现 |
| `ChromaVectorStore` | 真实 Chroma backend 的契约实现 |
| `ProviderEmbeddingsAdapter` | 本章 provider 到 LangChain `Embeddings` 的桥 |
| `VectorStoreManager` | 不同 backend 的统一入口 |

第二遍再看这些函数和方法：

| 函数/方法 | 阅读重点 |
|-----------|----------|
| `embed_chunks()` | `SourceChunk[]` 怎样变成 `EmbeddedChunk[]` |
| `infer_chunks_embedding_space()` | 写入前如何推断空间身份 |
| `ensure_matching_embedding_space()` | provider / model / dimensions 如何一起校验 |
| `upsert()` | chunk 级写入或覆盖 |
| `replace_document()` | document 级整体替换 |
| `similarity_search()` | 查询、过滤、排序、结果还原 |
| `delete_by_document_id()` | 文档级删除 |
| `build_documents()` | `SourceChunk` 到 LangChain `Document` 的映射 |
| `retrieval_results_from_scored_documents()` | LangChain 结果回到 `RetrievalResult` |
| `VectorStoreManager.search()` | 三种 backend 如何收束成统一查询 |

### 11.4 运行方式

先进入本章代码目录：

```bash
cd source/04_rag/04_vector_databases
python -m pip install -r requirements.txt
```

如果你的环境暂时没有安装 `chromadb`、`langchain-core` 或 `langchain-chroma`，原理层 JSON store 仍然可以先读和跑；Chroma / LangChain 相关脚本会明确提示缺少依赖。

### 11.5 推荐运行顺序

建议按下面顺序跑，而不是先挑一个最复杂的脚本：

1. `01_index_store.py`
2. `02_search_store.py`
3. `03_delete_document.py`
4. `04_chroma_crud.py`
5. `05_chroma_filter_delete.py`
6. `06_langchain_vectorstore.py`
7. `07_vector_store_manager.py`
8. `python -m unittest discover -s tests`

这个顺序和文档主线一致：

```text
JSON 原理层 -> Chroma 真实数据库 -> LangChain 框架映射 -> 统一 manager -> tests
```

### 11.6 第一步：`01_index_store.py`

```bash
python 01_index_store.py --reset
```

你应该观察到：

- JSON store 的持久化路径
- 样例 `SourceChunk[]` 怎样先被向量化
- `EmbeddedChunk[]` 怎样写成 JSON records
- store 文件里同时保留 chunk、vector、metadata 和 embedding space
- `replace_document()` 为什么可以作为文档级写入入口

这一阶段对应的是：

```text
SourceChunk[] -> EmbeddedChunk[] -> PersistentVectorStore.replace_document() -> JSON records
```

### 11.7 第二步：`02_search_store.py`

```bash
python 02_search_store.py
python 02_search_store.py "为什么 metadata 很重要？" --filename metadata_rules.md
```

你应该观察到：

- query 会先走同一个 provider 的 `embed_query()`
- store 会校验 query vector 维度
- store 会校验 query provider 和库存向量的 embedding space
- `filename` 过滤怎么缩小范围
- 返回结果仍然是 `RetrievalResult[]`，不是裸分数列表

这一阶段对应的是：

```text
question -> query vector -> PersistentVectorStore.similarity_search() -> RetrievalResult[]
```

### 11.8 第三步：`03_delete_document.py`

```bash
python 03_delete_document.py trial
```

你应该观察到：

- 删除动作围绕 `document_id`
- 一个文档有多个 chunk 时也应该整体删除
- 删除后再检索，不应该还能命中被删文档的旧 chunk

这一步要建立的意识是：

> 第四章的删除不是演示命令，而是后续知识库更新和回填的基础能力。

### 11.9 第四步：`04_chroma_crud.py`

```bash
python 04_chroma_crud.py --reset
```

你应该观察到：

- `store/chroma/` 下会出现真实持久化数据
- Chroma collection 会被创建或复用
- 写入时仍然保留 `chunk_id / document_id / provider_name / model_name / dimensions`
- 查询结果需要从 Chroma 响应重新水合成 `RetrievalResult`

这一阶段不是要你记住 Chroma 的全部 SDK，而是要看清：

```text
JSON store 里的存储契约 -> Chroma collection 里的真实存储行为
```

### 11.10 第五步：`05_chroma_filter_delete.py`

```bash
python 05_chroma_filter_delete.py "为什么 metadata 很重要？" --filename metadata_rules.md --suffix .md --document-id metadata
python 05_chroma_filter_delete.py "如何申请退费？" --delete-document-id trial
```

你应该观察到：

- Chroma 真的创建了 collection
- metadata filter 现在走真实数据库
- 复合过滤会显式落成 `$and`
- 删除和替换已经不是“本地文件操作”，而是数据库行为

这里尤其要注意：

```text
where={"filename": "...", "suffix": "..."}
```

并不等于所有数据库都接受的复合条件。Chroma 的复合过滤需要显式 `$and`，所以本章代码会做这层转换和演示。

### 11.11 第六步：`06_langchain_vectorstore.py`

```bash
python 06_langchain_vectorstore.py "为什么 metadata 很重要？" --filename metadata_rules.md --init-mode add_documents --reset
python 06_langchain_vectorstore.py "为什么 metadata 很重要？" --filename metadata_rules.md --init-mode from_documents
python 06_langchain_vectorstore.py "如何申请退费？" --retriever-search-type mmr
```

你应该观察到：

- 同一个 provider 可以通过 LangChain `Embeddings` 适配器接入
- `add_documents()` 和 `from_documents()` 都只是不同初始化入口
- `as_retriever()` 现在只做接口演示，策略解释放到第五章

这一阶段要特别分清：

- `similarity_search()` 仍然是 VectorStore 查询
- `as_retriever()` 只是展示上层入口
- `MMR / threshold / top_k 策略` 到第五章再系统展开

### 11.12 第七步：`07_vector_store_manager.py`

```bash
python 07_vector_store_manager.py --backend json --delete-document-id trial "如何申请退费？"
python 07_vector_store_manager.py --backend chroma --add-document-id faq --add-text "课程退款请联系助教。" "如何申请退费？"
python 07_vector_store_manager.py --backend langchain --replace-document-id trial --replace-text "试学需要提前预约并完成登记。" "如何预约试学？"
```

你应该观察到：

- manager 已经不是纯 backend 对照脚本
- 它已经具备真实 `add / search / replace / delete`
- 不同 backend 的调用形态不同，但管理职责相同

这一阶段要看的是：

```text
json / chroma / langchain
-> 都能通过 add / search / replace / delete 进入同一个管理语义
```

manager 不负责抹平所有底层差异，它只负责让上层调用者不用在业务代码里到处分叉。

### 11.13 测试：`tests/`

当前测试锁定四层行为：

1. JSON store 的基本契约
2. Chroma 的真实持久化、过滤、删除
3. LangChain Chroma 的 `from_documents / similarity_search / as_retriever`
4. `VectorStoreManager` 的统一增删查改能力

建议运行：

```bash
python -m unittest discover -s tests
```

这些测试不是为了追求覆盖率数字，而是在锁定第四章最重要的契约：

- 同一个 store 不混用 embedding space
- `replace_document()` 不留下旧 chunk
- `delete_by_document_id()` 真正删除整份文档
- metadata filter 能缩小结果范围
- 不同 backend 返回的仍然是标准结果形状

### 11.14 第四章最小回归集

第四章最小回归集可以先记住这几条：

| 场景 | 期望 |
|------|------|
| `如何申请退费？` | 优先命中 `refund:0` |
| `为什么 metadata 很重要？` | 优先命中 `metadata:0` |
| `filename=metadata_rules.md` | 结果范围明显收窄 |
| 删除 `trial` | `trial:0` 不应继续出现在查询结果里 |
| 替换同一 `document_id` | 旧 chunk 不应残留 |
| 换 `model_name` 查询旧 store | 应直接失败 |
| 切换 backend | 结果仍应能回到 `RetrievalResult` |

### 11.15 本章代码刻意简化的范围

第四章代码刻意简化了几件事：

1. 样例语料固定在 `demo_source_chunks()`
2. 本章不重新接第二章的完整文档切分 pipeline
3. 本章不重新讲第三章真实 embeddings endpoint
4. JSON store 只做最小精确搜索
5. JSON store 的 metadata 过滤只支持 `filename`
6. Chroma 只实现本章需要的最小 CRUD、filter 和 delete
7. LangChain 只讲 VectorStore 映射，不展开 Retriever 策略
8. FAISS / Pinecone / Milvus / Weaviate 只做选型认知，不硬造 demo

这些简化不是降低知识密度，而是为了保证第四章的学习重心始终在：

> 存储层契约、真实 backend 映射、状态治理和可替换接口。

### 11.16 第四章最值得刻意观察的失败案例

第一类是 embedding space 混用。

你可以故意换一个 `model_name` 或 `dimensions`，观察写入或查询怎样失败。这个失败非常重要，因为跨空间相似度分数看起来也可能“有数值”，但语义上没有比较意义。

第二类是文档替换残留。

如果 `replace_document()` 只是简单 upsert 新 chunk，而没有删掉旧 chunk，同一份文档更新后就可能同时命中新旧版本。

第三类是删除不彻底。

如果删除只按一个 `chunk_id` 做，现实文档一旦被切成多个 chunk，就会出现旧内容残留。

第四类是 metadata filter 假生效。

过滤后如果结果范围没有明显收窄，就要检查 filter 是否真的传给了 store，而不是只在展示层筛了一下。

第五类是依赖缺失。

`chromadb`、`langchain-core`、`langchain-chroma` 缺失时，真实 backend 应该清晰失败，而不是让用户以为检索质量出了问题。

### 11.17 建议你主动改的地方

如果你想把第四章真正学扎实，建议主动改三类地方再跑一遍：

1. 改一个 `document_id`，观察 replace / delete 路径会怎样变化
2. 增加一个 metadata 字段，观察 JSON / Chroma / LangChain 三层如何透传
3. 故意换一个 `model_name`，观察 store space 校验如何直接失败

这样你会真正把“持久化、查询、过滤、替换、删除、空间一致性”连在一起。

### 11.18 最推荐的阅读配套顺序

跑代码时，建议对应打开这些文件：

1. 跑 `01-03` 时看 [vector_store_basics.py](../../source/04_rag/04_vector_databases/vector_store_basics.py)
2. 跑 `04-05` 时看 [chroma_store.py](../../source/04_rag/04_vector_databases/chroma_store.py)
3. 跑 `06` 时看 [langchain_adapter.py](../../source/04_rag/04_vector_databases/langchain_adapter.py)
4. 跑 `07` 时看 [vector_store_manager.py](../../source/04_rag/04_vector_databases/vector_store_manager.py)

这样会比“先把所有脚本都跑一遍，再回头找实现”更容易建立结构感。

---

## 12. 常见疑惑与复盘问题

### 12.1 向量数据库是不是只是在保存向量

不是。

如果只保存 `list[float]`，检索结果就无法回到原文 chunk，也无法做引用、删除、替换和过滤。第四章里的向量存储必须同时保存：

- vector
- chunk 身份
- metadata
- embedding space

所以向量数据库在 RAG 里不是“向量数组仓库”，而是“语义索引和文档身份绑定的存储层”。

### 12.2 JSON store 已经能查，真实向量数据库还有什么价值

JSON store 的价值是教学原理层。

它能让你看懂：

- 写入
- 查询
- 替换
- 删除
- 过滤
- 空间校验

真实向量数据库补的是更工程化的能力，例如持久 collection、索引结构、批量写入、真实 metadata filter、数据库级删除和更适合扩展的数据组织方式。

### 12.3 `upsert()` 和 `replace_document()` 能不能合并

不建议合并。

`upsert()` 是 chunk 级语义，适合写入或覆盖一批明确的 chunk。

`replace_document()` 是 document 级语义，适合一份文档重新处理以后，用新 chunk 整体替换旧 chunk。

这两个动作混在一起，会让文档更新时很容易留下 stale chunks。

### 12.4 为什么删除不直接按 `chunk_id`

真实文档通常会被切成多个 chunk。

如果只按一个 `chunk_id` 删除，系统很容易删掉一小段，却留下同一文档的其他旧片段。第四章把 `delete_by_document_id()` 立成真实能力，是为了让文档级更新、下架和回填都有稳定操作入口。

### 12.5 为什么 Chroma metadata 里要放内部字段

Chroma 返回结果时需要能恢复本章自己的对象。

所以 metadata 里不仅有原文 metadata，还要保存：

- `_rag_chunk_id`
- `_rag_document_id`
- `_rag_provider_name`
- `_rag_model_name`
- `_rag_dimensions`

这些字段让 store 能在读回时重新构造 `SourceChunk / EmbeddedChunk / RetrievalResult`，也让 embedding space 校验和文档级删除有真实落点。

### 12.6 LangChain VectorStore 为什么仍然属于第四章

因为这里讲的是存储层接口映射。

`similarity_search()`、`similarity_search_with_score()` 和 `as_retriever()` 虽然已经接近检索入口，但本章只关心：

- provider 怎样适配成 LangChain `Embeddings`
- chunk 怎样适配成 LangChain `Document`
- 查询结果怎样回到 `RetrievalResult`
- VectorStore 怎样接上真实存储 backend

检索策略本身，例如 `top_k / threshold / MMR / bad cases`，放到第五章再系统讲。

### 12.7 manager 会不会掩盖 backend 差异

一个好的 manager 不应该假装 backend 没有差异。

第四章的 `VectorStoreManager` 只统一上层职责：

- add
- search
- replace
- delete

底层差异仍然保留在各自 adapter 里。这样业务调用更稳定，同时读代码时仍然能看清 JSON、Chroma、LangChain 的不同实现方式。

---

## 13. 本章学完后你应该能回答

- 为什么 `EmbeddedChunk[]` 还不等于可用检索系统
- 为什么第四章必须先讲运行时主线和存储契约，再讲具体 backend
- 为什么第四章必须同时讲原理层和真实工具层
- 为什么向量数据库选型基础更适合放在主线和原理层之后
- 为什么 `EmbeddingSpace` 是第四章真正的核心身份对象
- 为什么 `upsert()` 和 `replace_document()` 不能混成一个模糊接口
- 为什么真实 Chroma 里仍然要自己守住 embedding space
- 为什么 LangChain VectorStore 仍然属于第四章，而不是第五章
- 为什么综合案例需要统一 manager，而不是继续堆 backend 对照脚本

---

## 14. 下一章

第五章开始，你才会真正进入 Retriever 策略：

- `top_k`
- `threshold`
- `MMR`
- bad cases

也就是说：

> 第四章解决“能不能稳地存和查”，第五章解决“怎么查得更好”。
