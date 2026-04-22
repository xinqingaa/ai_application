# 04. 向量数据库

> 本章目标：先用一个最小 JSON store 把“向量怎么存、怎么查、怎么替换、怎么删”讲清楚，再补上真实 `Chroma` 和 `LangChain VectorStore`，让第四章的标题和实际交付重新一致。

---

## 1. 概述

### 学习目标

- 理解为什么第三章的 `EmbeddedChunk[]` 还不等于可用检索系统
- 理解第四章为什么要同时讲“原理实现”和“真实工具”
- 看懂第四章如何继续沿用第三章的 `SourceChunk / EmbeddedChunk / provider / model / dimensions` 契约
- 能运行第四章脚本，并解释 `upsert()`、`replace_document()`、`similarity_search()`、`delete_by_document_id()` 的职责
- 能说明 JSON store、Chroma、LangChain Chroma 在这一章里的对应关系

### 预计学习时间

- 向量存储职责与边界：30-40 分钟
- 最小 JSON store：30-40 分钟
- Chroma 实践：30-40 分钟
- LangChain VectorStore 映射：20-30 分钟

### 本章在 RAG 工程中的重要性

| 场景 | 本章先解决什么 |
|------|----------------|
| 离线索引 | `EmbeddedChunk[]` 怎样真正落到持久化存储 |
| 在线检索 | query vector 怎样在同一 embedding space 中查回 chunk |
| 文档更新 | 为什么要区分 chunk 级 `upsert()` 和文档级 `replace_document()` |
| 数据治理 | 为什么删除和替换必须围绕 `document_id` |
| 工具接入 | 为什么你既要懂原理，也要会用真实向量数据库 |

### 本章与前后章节的关系

第三章已经解决：

1. `SourceChunk[] -> EmbeddedChunk[]`
2. `embed_query / embed_documents`
3. provider/model/dimensions 的最小契约

第四章接着解决：

1. 向量怎样真正被存下来
2. 查询怎样把结果重新还原成标准 chunk
3. metadata 和 `document_id` 怎样进入真实查询/替换/删除路径
4. 最小原理实现和真实工具如何一一对应

第五章才继续解决：

1. `top_k / threshold / MMR`
2. Retriever 抽象
3. “怎么查得更好”

### 学习前提

- 建议先完成第二章和第三章
- 建议你已经掌握 `02_llm/02_multi_provider` 中的真实 provider 基础调用
- 第四章不会重讲 OpenAI-compatible 的基础接入

本章的重点不是“怎么调 embeddings API”，而是“向量进入真实存储以后，系统需要补上哪些能力”。

### 本章代码入口

- [README.md](../../source/04_rag/04_vector_databases/README.md)
- [requirements.txt](../../source/04_rag/04_vector_databases/requirements.txt)
- [vector_store_basics.py](../../source/04_rag/04_vector_databases/vector_store_basics.py)
- [chroma_store.py](../../source/04_rag/04_vector_databases/chroma_store.py)
- [langchain_adapter.py](../../source/04_rag/04_vector_databases/langchain_adapter.py)
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
6. JSON store、Chroma、LangChain Chroma 的映射关系

本章不展开：

- `MMR`、`Multi-query`、`HyDE`
- rerank
- hybrid retrieval
- 复杂 metadata DSL
- 多向量库横评
- ANN 底层算法细节

---

## 2. 为什么只有向量还不够 📌

### 2.1 `EmbeddedChunk[]` 还不是可用检索系统

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

### 2.2 向量存储层负责什么

向量存储层至少要负责五件事：

1. 存向量
2. 查向量
3. 保留向量和原始 chunk/metadata 的绑定关系
4. 支持删除和文档级替换
5. 守住 embedding space 一致性

它不负责：

- 重新切分文档
- 重新生成向量
- 优化召回策略
- 组织 Prompt
- 让 LLM 生成答案

### 2.3 为什么第四章现在必须补真实工具

原来的第四章已经把“最小存储原理”讲得差不多了，但相对课程标题还有两个明显缺口：

- 没有真实向量数据库
- 没有 LangChain VectorStore

所以本章现在拆成两层：

1. 原理层：本地 JSON store
2. 实践层：真实 `Chroma` + `LangChain Chroma`

JSON store 不删除，因为它仍然是最容易看清契约的教学放大镜。

---

## 3. 本章真正新增了什么 📌

### 3.1 核心数据流

第四章沿用第三章的对象契约，新增的是这条数据流：

```text
EmbeddedChunk[]
-> replace_document()
-> vector store
-> similarity_search(query_vector)
-> RetrievalResult[]
```

如果是底层原语，则会退回到：

```text
EmbeddedChunk[]
-> upsert()
```

### 3.2 本章要立住的存储层契约

第四章至少要守住这些契约：

1. 同一个 store 只能保存一个 provider/model/dimensions 空间
2. query 和 stored vectors 必须来自同一个 embedding space
3. metadata 不能在写入时被悄悄丢掉
4. `upsert()` 和 `replace_document()` 必须是两个不同语义
5. `document_id` 删除必须是真实能力，而不是演示名词

### 3.3 为什么 `document_id` 在这一章变成真实职责

到了第四章，`document_id` 不再只是“结构上应该有”：

- 它是删除入口
- 它是文档级替换入口
- 它是增量更新的一致性锚点

这就是为什么第二章的 stable id 不能只停留在“看起来规范”。

### 3.4 metadata 在这一章里为什么必须一起落库

第四章至少会继续保留：

- `source`
- `filename`
- `suffix`
- `chunk_index`
- `char_start / char_end / chunk_chars`

因为现在这些字段已经进入真实路径：

- `filename` 会进入过滤
- `source / chunk_index / range` 会进入调试输出
- `document_id` 会进入替换和删除

---

## 4. 原理层：最小 JSON store 📌

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

### 4.2 JSON store 当前交付了什么

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
4. 不引入外部库

这不是因为这些能力不重要，而是为了把注意力集中在存储层契约上。

---

## 5. 真实工具层：Chroma 📌

### 5.1 为什么选 Chroma

在第四章里，`Chroma` 是一个合适的真实工具层：

- 它有真实持久化目录
- 它有真实 collection
- 它能直接做 query / filter / delete
- 它足够轻量，适合作为课程里的第一站

### 5.2 本章里 Chroma 的定位

本章不是做 Chroma 产品横评，而是用 Chroma 去对照你刚学会的原理层动作：

| 原理层 | Chroma 层 |
|--------|-----------|
| `PersistentVectorStore` | `ChromaVectorStore` |
| JSON 文件 | persistent collection |
| `filename` 过滤 | metadata `where` |
| `delete_by_document_id()` | Chroma `delete(where=...)` |
| `load_chunks()` | 从 Chroma 读回并重新水合 |

### 5.3 Chroma 层为什么还要补自己的契约校验

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

### 5.4 当前 Chroma 层演示到什么程度

本章当前交付：

- [chroma_store.py](../../source/04_rag/04_vector_databases/chroma_store.py)
- [04_chroma_crud.py](../../source/04_rag/04_vector_databases/04_chroma_crud.py)
- [05_chroma_filter_delete.py](../../source/04_rag/04_vector_databases/05_chroma_filter_delete.py)

你可以直接看到：

- collection 的持久化目录
- 写入后的文档列表
- metadata filter
- `document_id` 删除
- 真实数据库里依然要守住 embedding space

---

## 6. 真实工具层：LangChain VectorStore 📌

### 6.1 为什么第四章现在还要补 LangChain

只会原生 Chroma API 还不够，因为工程里很常见的上层接口是：

> `VectorStore`

也就是：

- 你不一定直接调用底层数据库 SDK
- 你可能通过 LangChain 等上层抽象接入同一个数据库

### 6.2 这一章里 LangChain 的关注点

你已经在前面掌握了 provider 真实调用，这一章不再重讲 `OpenAIEmbeddings` 一类平台接入。

第四章只关注：

1. 现有 `EmbeddingProvider` 怎样包装成 LangChain 的 `Embeddings`
2. `SourceChunk` 怎样映射成 LangChain `Document`
3. `similarity_search_with_score()` 怎样对应当前存储层查询

### 6.3 当前映射关系

本章当前的映射是：

| 第四章对象/能力 | LangChain 对应 |
|----------------|----------------|
| `EmbeddingProvider` | `ProviderEmbeddingsAdapter` |
| `SourceChunk` | `Document` |
| `filename` metadata | `filter={"filename": ...}` |
| query 搜索 | `similarity_search_with_score()` |

对应实现：

- [langchain_adapter.py](../../source/04_rag/04_vector_databases/langchain_adapter.py)
- [06_langchain_vectorstore.py](../../source/04_rag/04_vector_databases/06_langchain_vectorstore.py)

### 6.4 为什么这里不直接进入 Retriever

因为 LangChain VectorStore 仍然是：

- 向量存储抽象
- 不是 Retriever 策略层

第五章才会继续讨论：

- `top_k`
- `threshold`
- `MMR`
- bad cases

---

## 7. 第四章实践：建议运行顺序

### 7.1 安装依赖

```bash
cd source/04_rag/04_vector_databases
python -m pip install -r requirements.txt
```

### 7.2 先跑原理层

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

### 7.3 再跑 Chroma

```bash
python 04_chroma_crud.py --reset
python 05_chroma_filter_delete.py "为什么 metadata 很重要？" --filename metadata_rules.md
python 05_chroma_filter_delete.py "如何申请退费？" --delete-document-id trial
```

你应该观察到：

- Chroma 真的创建了 collection
- metadata filter 现在走真实数据库
- 删除和替换已经不是“本地文件操作”，而是数据库行为

### 7.4 最后跑 LangChain Chroma

```bash
python 06_langchain_vectorstore.py "为什么 metadata 很重要？" --filename metadata_rules.md --reset
python 07_vector_store_manager.py --backend json "如何申请退费？"
python 07_vector_store_manager.py --backend chroma "如何申请退费？"
python 07_vector_store_manager.py --backend langchain "如何申请退费？"
```

你应该观察到：

- 同一个 provider 可以通过 LangChain `Embeddings` 适配器接入
- LangChain Chroma 仍然在做“向量存储”
- 三个 backend 的调用形态不同，但职责边界相同

### 7.5 测试

```bash
python -m unittest discover -s tests
```

当前测试锁定三层行为：

1. JSON store
2. 原生 Chroma
3. LangChain Chroma

---

## 8. Mini 回归集

第四章当前的最小回归观察点至少包括：

1. `如何申请退费？` 应优先命中 `refund:0`
2. `为什么 metadata 很重要？` 应优先命中 `metadata:0`
3. `filename=metadata_rules.md` 过滤后，结果范围必须明显收窄
4. 删除 `trial` 后，不应再保留该文档 chunk
5. query 和 store 若不在同一 embedding space，应直接失败

---

## 9. 本章学完后你应该能回答

- 为什么 `EmbeddedChunk[]` 还不等于可用检索系统
- 为什么第四章现在必须同时讲原理层和真实工具层
- 为什么 `upsert()` 和 `replace_document()` 不能混成一个模糊接口
- 为什么真实 Chroma 里仍然要自己守住 embedding space
- 为什么 LangChain VectorStore 仍然属于第四章，而不是第五章

---

## 10. 下一章

第五章开始，你才会真正进入 Retriever 策略：

- `top_k`
- `threshold`
- `MMR`
- bad cases

也就是说：

> 第四章解决“能不能稳地存和查”，第五章解决“怎么查得更好”。
