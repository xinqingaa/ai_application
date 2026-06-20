# 04. 向量数据库

> 本章目标：把第三章得到的 `EmbeddedChunk[]` 推进成真正可持久化、可查询、可替换、可删除的存储层。学习顺序建议先按 `01-07` 脚本跑通代码，再回头复盘对象、契约、backend 差异和治理锚点。

---

## 1. 本章主线

第四章不要先从“哪个向量数据库更好”开始，而是先抓住这一条链路：

```text
SourceChunk[]
-> embed_chunks()
-> EmbeddedChunk[]
-> upsert() / replace_document()
-> JSON records / Chroma collection / LangChain VectorStore
-> similarity_search()
-> RetrievalResult[]
```

用自然语言说：

1. 第三章已经让文本 chunk 具备稳定身份和向量表示。
2. 第四章解决这些 chunk 怎样稳定写入 store。
3. 用户提问时，query 也要进入同一个 embedding space。
4. store 负责查回相似 chunk，并还原成标准 `RetrievalResult[]`。
5. 后续第五章才继续讨论怎样查得更好。

第四章的核心不是“背 Chroma API”，而是看懂：

```text
写入
查询
替换
删除
metadata 过滤
embedding space 校验
结果还原
backend 适配
```

### 1.1 学习目标

- 理解为什么第三章的 `EmbeddedChunk[]` 还不等于可用检索系统
- 理解向量数据库在 RAG 工程中的职责边界
- 掌握第四章的核心契约：`upsert / replace_document / similarity_search / delete_by_document_id`
- 理解 JSON store、Chroma、LangChain Chroma 在本章里的对应关系
- 认识 `ANN vs 精确搜索` 的基本权衡和主流向量数据库的选型差异
- 了解为什么第四章最后需要一个统一的 `VectorStoreManager`

### 1.2 本章在 AI 应用中的重要性

| 场景 | 本章先解决什么 |
|------|----------------|
| 知识库存储 | 向量怎样真正写进可持久化系统 |
| 检索查询 | query 怎样在存储层里查回候选 chunk |
| 数据治理 | 文档替换、删除、过滤怎样落到真实接口 |
| 框架接入 | 原生数据库 API 与 LangChain VectorStore 怎样对应 |

### 1.3 学习前提

- 建议先完成第三章，已经理解 `SourceChunk[] -> EmbeddedChunk[]`
- 建议已经理解 `provider_name / model_name / dimensions` 的 embedding space 约束
- 如果你已经接触过 LangChain `Document` / `VectorStore` 抽象，读起来会更快

这一章不再重复讲：

- 向量是怎样生成的
- `embed_query / embed_documents` 的基础语义
- OpenAI-compatible embeddings 的接入细节

第四章只关注存储层 specific 的问题。

### 1.4 本章与前后章节的关系

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

### 1.5 本章边界

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

### 1.6 代码入口

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

### 1.7 学习方式

推荐的学习路径是：

```text
先粗读本章主线
-> 逐个运行 01-07 脚本
-> 从 main() 入口顺着调用链读代码
-> 回头看本章后半部分的概念复盘
```

这样读的好处是：你不是先被大量“为什么这样做”淹没，而是先知道每个脚本真实做了什么，再把设计原因挂回代码上。

运行前先进入本章目录：

```bash
cd source/04_rag/04_vector_databases
python -m pip install -r requirements.txt
```

如果暂时没有安装 `chromadb`、`langchain-core` 或 `langchain-chroma`，原理层 JSON store 仍然可以先读和跑；Chroma / LangChain 相关脚本会明确提示缺少依赖。

### 1.8 学习地图

建议按下面这条主线阅读本章，而不是一开始就陷入某个数据库名、某个 SDK 或某个过滤语法：

```text
先看第四章完整主线
-> 再按 01-07 跑脚本
-> 再看运行时对象和存储层契约
-> 再用 JSON store 理解持久化 / 查询 / 替换 / 删除
-> 再看真实向量数据库解决的工程问题
-> 再进入 Chroma 和 LangChain 映射
-> 最后看统一 manager 如何收束不同 backend
```

这一章后面的失败案例、治理锚点和建议运行顺序，更适合在你已经跑过代码以后回头复盘。

### 1.9 01-07 脚本总览

| 脚本 | 对应层次 | 学习重点 |
|------|----------|----------|
| [01_index_store.py](../../source/04_rag/04_vector_databases/01_index_store.py) | JSON 原理层写入 | `EmbeddedChunk[]` 怎样持久化成 JSON records |
| [02_search_store.py](../../source/04_rag/04_vector_databases/02_search_store.py) | JSON 原理层查询 | query vector 怎样查回 `RetrievalResult[]` |
| [03_delete_document.py](../../source/04_rag/04_vector_databases/03_delete_document.py) | JSON 原理层删除 | 为什么删除围绕 `document_id` |
| [04_chroma_crud.py](../../source/04_rag/04_vector_databases/04_chroma_crud.py) | 原生 Chroma 写入 | 同一套契约怎样落到真实 collection |
| [05_chroma_filter_delete.py](../../source/04_rag/04_vector_databases/05_chroma_filter_delete.py) | 原生 Chroma 查询/过滤/删除 | `where` 过滤和数据库级删除 |
| [06_langchain_vectorstore.py](../../source/04_rag/04_vector_databases/06_langchain_vectorstore.py) | LangChain VectorStore 映射 | `SourceChunk -> Document`，provider -> `Embeddings` |
| [07_vector_store_manager.py](../../source/04_rag/04_vector_databases/07_vector_store_manager.py) | 统一管理入口 | `json / chroma / langchain` 怎样收束为统一 add/search/replace/delete |

### 1.10 本章文件分层

| 层次 | 文件 | 职责 |
|------|------|------|
| 原理层 | [vector_store_basics.py](../../source/04_rag/04_vector_databases/vector_store_basics.py) | 定义对象、embedding space、JSON store |
| 原生数据库层 | [chroma_store.py](../../source/04_rag/04_vector_databases/chroma_store.py) | 把同一套契约映射到 Chroma |
| 框架适配层 | [langchain_adapter.py](../../source/04_rag/04_vector_databases/langchain_adapter.py) | 把本章对象映射到 LangChain |
| 统一管理层 | [vector_store_manager.py](../../source/04_rag/04_vector_databases/vector_store_manager.py) | 统一不同 backend 的上层操作 |
| CLI 演示层 | `01-07` | 用可运行脚本串起每个学习点 |

---

## 2. 原理层 JSON Store

原理层的目的不是替代真实向量数据库，而是用最小依赖看清存储层契约。

这一层对应：

- [vector_store_basics.py](../../source/04_rag/04_vector_databases/vector_store_basics.py)
- [01_index_store.py](../../source/04_rag/04_vector_databases/01_index_store.py)
- [02_search_store.py](../../source/04_rag/04_vector_databases/02_search_store.py)
- [03_delete_document.py](../../source/04_rag/04_vector_databases/03_delete_document.py)

### 2.1 `01_index_store.py`：写入 JSON store

运行：

```bash
cd source/04_rag/04_vector_databases
python 01_index_store.py --reset
```

主流程是：

```text
解析 --reset
-> 创建 LocalKeywordEmbeddingProvider
-> 创建 PersistentVectorStore
-> 可选 reset
-> demo_embedded_chunks(provider)
-> store.replace_document(...)
-> 写入 store/demo_vector_store.json
-> 打印 store 状态
```

最关键的一行在 [01_index_store.py](../../source/04_rag/04_vector_databases/01_index_store.py)：

```python
inserted = store.replace_document(demo_embedded_chunks(provider))
```

这里的真实流转是：

```text
demo_source_chunks()
-> embed_chunks(chunks, provider)
-> EmbeddedChunk[]
-> PersistentVectorStore.replace_document(...)
-> _serialize_embedded_chunk(...)
-> demo_vector_store.json
```

注意：本章样例不是从 `data/*.md` 文件实时读取的。`source=data/refund_policy.md` 是 demo metadata，真实文本写在 `demo_source_chunks()` 里。

JSON store 持久化的不只是向量，而是：

```text
chunk.chunk_id
chunk.document_id
chunk.content
chunk.metadata
vector
provider_name
model_name
dimensions
store 级 embedding_space
```

这说明第四章从一开始就强调：

> 向量不能脱离 chunk 身份、metadata 和 embedding space 单独存在。

### 2.2 `02_search_store.py`：查询 JSON store

运行：

```bash
python 02_search_store.py
python 02_search_store.py "为什么 metadata 很重要？" --filename metadata_rules.md
```

完整流程是：

```text
解析 question / filename / top_k
-> 创建 provider / store
-> ensure_index(store, provider)
-> provider.embed_query(question)
-> print(store)
-> store.similarity_search(...)
-> 打印 RetrievalResult[]
```

`ensure_index()` 的职责是保证当前 JSON store 至少可查询：

- JSON payload 损坏：reset 后用 demo 数据重建
- store 为空：用 demo 数据创建索引
- embedding space 不匹配：reset 后重建
- store 已存在且兼容：直接沿用当前 JSON store

所以 `02_search_store.py` 不是每次都强制恢复完整 demo 数据。如果你之前运行过删除脚本删掉 `trial`，只要 store 仍合法，它会继续查询当前这份 JSON store。

真正查询时：

```text
query text
-> provider.embed_query(...)
-> query_vector
-> store.load_chunks()
-> 从 JSON records 反序列化回 EmbeddedChunk[]
-> 校验 query provider 和 stored chunks 的 embedding space
-> 可选 filename 过滤
-> query_vector 和每个 chunk.vector 计算 cosine similarity
-> 按 score 降序
-> 返回 RetrievalResult[]
```

`print(store)` 现在会展示当前 store 快照：

```text
path
exists
count
embedding_space
document_ids
chunk_id / document_id / filename / vector_dims / preview
```

它的作用是让你先确认：

```text
现在查的是哪份本地 store？
store 里有哪些 chunk？
这些 chunk 属于哪个 embedding space？
preview 从哪里来？
```

### 2.3 `preview` 到底来自哪里

如果输出里看到：

```text
preview=购买后 7 天内且学习进度不超过 20%，可以申请全额退款。
```

不要理解成搜索脚本直接读了 `demo_source_chunks()`。更准确的链路是：

```text
demo_source_chunks()
-> demo_embedded_chunks(provider)
-> store.replace_document(...)
-> store/demo_vector_store.json
-> store.load_chunks()
-> similarity_search()
-> RetrievalResult.chunk.content
-> preview
```

也就是说：

- 源头是 `demo_source_chunks()`
- 持久化副本是 `demo_vector_store.json`
- 查询阶段读取的是 JSON store 反序列化后的 `EmbeddedChunk`
- 结果展示取的是 `RetrievalResult.chunk.content[:70]`

真实 RAG 系统里也是类似：

```text
原始文档
-> chunk
-> embedding
-> vector store
-> 查询时从 vector store 还原 chunk
-> 放进 prompt 或展示引用
```

### 2.4 `03_delete_document.py`：按文档删除

运行：

```bash
python 03_delete_document.py trial
```

主流程是：

```text
解析 document_id
-> 打开 JSON store
-> delete_by_document_id(document_id)
-> 打印删除数量和剩余 document ids
```

删除围绕 `document_id`，不是只围绕 `chunk_id`，原因是现实文档通常会被切成多个 chunk。

如果删除只按一个 `chunk_id` 做，就会出现：

```text
删掉 trial:0
但 trial:1 / trial:2 仍然残留
```

所以第四章把 `delete_by_document_id()` 立成真实能力。它是后续知识库更新、下架和重新索引的基础。

### 2.5 原理层复盘

JSON store 当前交付：

```text
upsert()
replace_document()
load_chunks()
similarity_search()
delete_by_document_id()
embedding_space()
list_document_ids()
count()
```

几个关键语义：

| 概念 | 要点 |
|------|------|
| `upsert()` | 按 `chunk_id` 写入或覆盖，不主动删除同文档其他旧 chunk |
| `replace_document()` | 先删除同 `document_id` 的旧 chunk，再写入新 chunk |
| `delete_by_document_id()` | 删除一份逻辑文档下的全部 chunk |
| `similarity_search()` | 校验、过滤、算分、排序、返回 `RetrievalResult[]` |
| `EmbeddingSpace` | `provider_name / model_name / dimensions` 的整体身份 |

`upsert()` 和 `replace_document()` 不建议合并：

```text
upsert 解决“这些 chunk 怎么写进去”
replace_document 解决“这份文档怎么整体换代”
```

如果文档更新时只 upsert 新 chunk，不删除旧 chunk，很容易留下 stale chunks。

---

## 3. 真实 Chroma Backend

Chroma 是本章第一种真实向量数据库 backend。它不是替换第四章主线，而是把原理层契约落到真实 persistent collection 上。

对应代码：

- [chroma_store.py](../../source/04_rag/04_vector_databases/chroma_store.py)
- [04_chroma_crud.py](../../source/04_rag/04_vector_databases/04_chroma_crud.py)
- [05_chroma_filter_delete.py](../../source/04_rag/04_vector_databases/05_chroma_filter_delete.py)

### 3.1 `04_chroma_crud.py`：写入真实 collection

运行：

```bash
python 04_chroma_crud.py --reset
```

主流程是：

```text
解析 --reset
-> 创建 LocalKeywordEmbeddingProvider
-> 创建 ChromaVectorStore
-> 可选 reset collection
-> demo_embedded_chunks(provider)
-> store.replace_document(...)
-> Chroma collection.upsert(...)
-> 打印 persist dir / collection / count / document ids / preview
```

数据源仍然是：

```text
demo_source_chunks()
-> demo_embedded_chunks(provider)
```

不是从 JSON 文件“转换”到 Chroma。更准确地说：

```text
JSON store 和 Chroma store 使用同一份 demo 逻辑语料
分别写入不同 backend
```

真正写入 Chroma 的位置在 `ChromaVectorStore.upsert()`：

```python
self._collection.upsert(
    ids=[item.chunk.chunk_id for item in batch],
    documents=[item.chunk.content for item in batch],
    metadatas=[_serialize_metadata(item) for item in batch],
    embeddings=[item.vector for item in batch],
)
```

一条 Chroma record 里对应：

```text
id        = chunk_id
document  = chunk.content
metadata  = chunk metadata + 内部字段
embedding = chunk.vector
```

### 3.2 `--reset` 的边界

`04_chroma_crud.py --reset` 重置的是 Chroma collection，不是一定物理删除整个 `store/chroma` 目录。

代码语义是：

```text
delete_collection(collection_name)
-> get_or_create_collection(collection_name)
```

不是：

```text
rm -rf store/chroma
```

所以你可能看到 `store/chroma/` 下有多个 UUID 目录。它们通常是 Chroma 内部向量索引 segment 文件，不等同于课程里的“多个 collection”。

逻辑数据层面：当前 collection 会被删除重建。

物理目录层面：Chroma 不一定清理所有旧 segment 目录。

如果你想彻底物理清空，需要删除整个目录后再运行脚本。

### 3.3 `05_chroma_filter_delete.py`：过滤、查询和删除

运行：

```bash
python 05_chroma_filter_delete.py "为什么 metadata 很重要？" --filename metadata_rules.md --suffix .md --document-id metadata
python 05_chroma_filter_delete.py "如何申请退费？" --delete-document-id trial
```

主流程是：

```text
解析 question / filename / suffix / document-id / top-k / delete-document-id
-> 创建 provider / ChromaVectorStore
-> ensure_index(store, provider)
-> build_where_filter(...)
-> provider.embed_query(question)
-> store.similarity_search(query_vector, provider, where=where)
-> 打印结果
-> 可选 delete_by_document_id(...)
```

`05` 的重点不是写入，而是：

```text
metadata filter 进入真实数据库查询路径
```

原理层 JSON store 只演示了 `filename` 过滤。Chroma 层开始展示更真实的 `where`：

```text
filename
suffix
document_id
```

多个过滤条件在 Chroma 中需要显式 `$and`：

```python
{"$and": [{"filename": "metadata_rules.md"}, {"suffix": ".md"}]}
```

这说明 metadata 过滤不是展示层筛选，而是数据库 query 的一部分。

### 3.4 Chroma metadata 中的内部字段

Chroma metadata 不只保存原文 metadata，还会补充本章内部字段：

```text
_rag_chunk_id
_rag_document_id
_rag_provider_name
_rag_model_name
_rag_dimensions
```

这些字段用于：

```text
恢复 SourceChunk / EmbeddedChunk / RetrievalResult
校验 embedding space
按 document_id 删除
按 metadata 过滤
```

真实向量数据库不会替你自动保证 provider/model/dimensions 一致，所以本章 wrapper 仍然显式守住这个契约。

### 3.5 Chroma 与 JSON 的映射关系

| 原理层 JSON | 原生 Chroma |
|-------------|-------------|
| JSON 文件 | persistent collection |
| records list | collection records |
| `chunk.content` | `documents` |
| `chunk.metadata` | `metadatas` |
| `vector` | `embeddings` |
| `filename` 过滤 | `where` filter |
| `delete_by_document_id()` | `delete(where={...})` |
| `_deserialize_embedded_chunk()` | hydrate Chroma response |

你不需要背完整 Chroma SDK。第四章要你看清：

```text
JSON store 里的存储契约
-> 怎样落到真实 collection / metadata / query / delete
```

---

## 4. LangChain VectorStore

第六节不是再学一个新的数据库，而是看：

```text
本章对象如何映射到 LangChain 框架抽象
```

对应代码：

- [langchain_adapter.py](../../source/04_rag/04_vector_databases/langchain_adapter.py)
- [06_langchain_vectorstore.py](../../source/04_rag/04_vector_databases/06_langchain_vectorstore.py)

### 4.1 `06_langchain_vectorstore.py`：整体流程

运行：

```bash
python 06_langchain_vectorstore.py "为什么 metadata 很重要？" --filename metadata_rules.md --init-mode add_documents --reset
python 06_langchain_vectorstore.py "为什么 metadata 很重要？" --filename metadata_rules.md --init-mode from_documents
python 06_langchain_vectorstore.py "如何申请退费？" --retriever-search-type mmr
```

主流程是：

```text
解析 question / filename / top-k / init-mode / retriever-search-type / reset
-> 创建 LocalKeywordEmbeddingProvider
-> 创建 LangChainChromaConfig
-> 可选 reset langchain_chroma 目录
-> create_or_load_vectorstore(...)
-> 构造 search_kwargs
-> similarity_search(...)
-> similarity_search_with_score(...)
-> as_retriever(...).invoke(...)
-> 把 LangChain 输出转回 RetrievalResult 风格
-> 并排打印三种结果
```

初始化有两条路径：

```text
add_documents:
create Chroma(...)
-> build_documents()
-> vectorstore.add_documents(...)

from_documents:
build_documents()
-> Chroma.from_documents(...)
```

两者都是写入 LangChain Chroma，只是入口不同。

### 4.2 三个库分别负责什么

| 库 | 角色 | 在本章里的体现 |
|----|------|----------------|
| `chromadb` | Chroma 原生数据库 SDK | 真正负责底层 collection、向量索引、持久化目录 |
| `langchain-core` | LangChain 核心抽象包 | 提供 `Document`、`Embeddings` 等标准接口 |
| `langchain-chroma` | LangChain 对 Chroma 的 VectorStore 集成 | 提供 LangChain 风格的 `Chroma` VectorStore |

关系是：

```text
langchain-core 定义接口
langchain-chroma 实现 Chroma VectorStore
chromadb 是底层真实数据库
```

`langchain-chroma` 不是另一个独立数据库。它底层仍然使用 Chroma，只是把 Chroma 包装成 LangChain 的 VectorStore。

### 4.3 原生 Chroma vs LangChain Chroma

| 问题 | 原生 Chroma | LangChain Chroma |
|------|-------------|------------------|
| 写入对象 | `ids / documents / metadatas / embeddings` | `Document[]` |
| embedding 调用 | 本章显式生成向量再传入 | VectorStore 通过 `Embeddings` 自动调用 |
| 查询输入 | `query_embeddings` | query 字符串 |
| 过滤参数 | `where` | `filter` |
| 返回结果 | Chroma 原始响应结构 | `Document[]` 或 `(Document, distance)` |
| 更适合 | 理解数据库行为、控制底层细节 | 接 LangChain Chain / Retriever / LCEL |

所以第六节回答的是：

> 如果不直接写 Chroma SDK，而是通过 LangChain 接 Chroma，同一套存储契约如何映射过去？

### 4.4 `SourceChunk -> Document`

LangChain 的标准文档对象是 `Document`：

```text
Document(page_content=..., metadata=...)
```

本章的映射在 `build_documents()` 中完成：

```text
SourceChunk.content -> Document.page_content
SourceChunk.metadata -> Document.metadata
chunk_id / document_id -> Document.metadata
```

必须把 `chunk_id` 和 `document_id` 放进 metadata，因为 LangChain 查询回来主要给你：

```text
page_content
metadata
```

如果 metadata 里没有 chunk 身份，本章就无法稳定恢复：

```text
SourceChunk(chunk_id, document_id, content, metadata)
```

### 4.5 `EmbeddingProvider -> Embeddings`

LangChain 期待的是 `Embeddings` 接口：

```text
embed_documents(texts)
embed_query(text)
```

本章已有自己的 `EmbeddingProvider`。所以需要：

```text
ProviderEmbeddingsAdapter(Embeddings)
```

它的作用是：

```text
LangChain 写入时调用 embed_documents()
LangChain 查询时调用 embed_query()
底层实际转给本章 LocalKeywordEmbeddingProvider
```

这也是为什么 `06_langchain_vectorstore.py` 里没有显式写：

```python
query_vector = provider.embed_query(question)
```

因为 query embedding 已经被 LangChain VectorStore 接管。

### 4.6 三个 LangChain 查询 API

`06_langchain_vectorstore.py` 并排展示：

```python
vectorstore.similarity_search(...)
vectorstore.similarity_search_with_score(...)
vectorstore.as_retriever(...).invoke(...)
```

| API | 返回 | 适合场景 |
|-----|------|----------|
| `similarity_search(question, **search_kwargs)` | `Document[]` | 只需要拿相关文档去拼 Prompt，不关心显式分数 |
| `similarity_search_with_score(question, **search_kwargs)` | `(Document, distance)[]` | 调试检索质量、观察排序、做评测、做阈值判断 |
| `as_retriever(...).invoke(question)` | `Document[]` | 接 LangChain Chain / LCEL / RAG pipeline |

最小判断方式：

```text
临时查文档
-> similarity_search()

看分数、排序、坏例
-> similarity_search_with_score()

进入 LangChain 编排
-> as_retriever()
```

第四章只展示 `as_retriever()` 的入口。`MMR / threshold / top_k 策略 / bad cases` 到第五章再系统展开。

---

## 5. VectorStoreManager

第七节是第四章的收束：把 JSON、原生 Chroma、LangChain Chroma 三套 backend 收到一个统一管理入口下。

对应代码：

- [vector_store_manager.py](../../source/04_rag/04_vector_databases/vector_store_manager.py)
- [07_vector_store_manager.py](../../source/04_rag/04_vector_databases/07_vector_store_manager.py)

### 5.1 `07_vector_store_manager.py`：整体流程

运行：

```bash
python 07_vector_store_manager.py --backend json --delete-document-id trial "如何申请退费？"
python 07_vector_store_manager.py --backend chroma --add-document-id faq --add-text "课程退款请联系助教。" "如何申请退费？"
python 07_vector_store_manager.py --backend langchain --replace-document-id trial --replace-text "试学需要提前预约并完成登记。" "如何预约试学？"
```

主流程是：

```text
解析 backend / question / filename / top-k / reset / add / replace / delete
-> 校验成对参数
-> 创建 VectorStoreManager
-> 可选 reset
-> ensure_index()
-> 可选 add_documents()
-> 可选 replace_document()
-> 可选 delete_document()
-> manager.search(...)
-> 打印统一 RetrievalResult[]
```

### 5.2 manager 统一了什么

`VectorStoreManager` 统一暴露：

```text
reset()
ensure_index()
add_documents()
replace_document()
delete_document()
search()
count()
list_document_ids()
```

它统一的是上层职责，不是假装底层没有差异。

```text
业务层关心：我要添加、搜索、替换、删除文档
adapter 层关心：json / chroma / langchain 具体怎么做
```

### 5.3 `search()` 的 backend 分支

`VectorStoreManager.search()` 最能体现统一入口。

JSON backend：

```text
question
-> provider.embed_query(question)
-> PersistentVectorStore.similarity_search(...)
-> RetrievalResult[]
```

Chroma backend：

```text
question
-> provider.embed_query(question)
-> ChromaVectorStore.similarity_search(..., where=...)
-> RetrievalResult[]
```

LangChain backend：

```text
question
-> vectorstore.similarity_search_with_score(...)
-> retrieval_results_from_scored_documents(...)
-> RetrievalResult[]
```

差异点：

```text
JSON / 原生 Chroma：manager 显式生成 query vector
LangChain Chroma：VectorStore 内部通过 Embeddings 适配器生成 query vector
```

相同点：

```text
最后都归一成 RetrievalResult[]
```

### 5.4 add / replace / delete 的统一

添加文档：

```text
raw text
-> _build_source_chunk()
-> SourceChunk
```

然后分 backend：

```text
json/chroma:
SourceChunk -> embed_chunks() -> EmbeddedChunk[] -> upsert()

langchain:
SourceChunk -> build_documents() -> Document[] -> add_documents()
```

替换文档：

```text
json/chroma:
replace_document()

langchain:
delete_document()
-> add_documents()
```

LangChain Chroma 没有本章定义的文档级 `replace_document()` helper，所以 manager 用“先删再加”保留文档级整体替换语义。

删除文档：

```text
json:
delete_by_document_id(document_id)

chroma:
delete_by_document_id(document_id)

langchain:
document_id -> chunk_id
-> vectorstore.delete(ids=...)
```

### 5.5 manager 的学习价值

如果一开始就看 manager，很容易误以为第四章重点是“写一个门面类”。

但 manager 放在最后，是为了让你先看清：

```text
JSON 怎么做
Chroma 怎么做
LangChain 怎么做
```

再理解：

```text
统一接口是在收束已经看懂的职责
不是替代你理解 backend 差异
```

### 5.6 manager 边界

当前 manager 是教学最小实现：

1. 一段输入文本先当成一个 `SourceChunk`
2. 不接完整文档切分流水线
3. 不强行接 FAISS / Pinecone / Milvus
4. 不抹平所有 backend 差异

它真正要立住的是：

> 上层接口稳定，底层差异留在 adapter 内部。

---

## 6. 核心对象与契约总复盘

### 6.1 运行时对象

| 对象 | 作用 |
|------|------|
| `SourceChunk` | 从文档处理阶段传下来的文本单元，带 `chunk_id / document_id / content / metadata` |
| `EmbeddedChunk` | `SourceChunk` 加上 `vector / provider_name / model_name / dimensions` |
| `RetrievalResult` | 存储层统一查询结果，包含 `chunk` 和 `score` |
| `EmbeddingSpace` | `provider_name / model_name / dimensions` 的整体身份 |
| `PersistentVectorStore` | 教学 JSON store |
| `ChromaVectorStore` | 原生 Chroma backend adapter |
| `ProviderEmbeddingsAdapter` | 本章 provider 到 LangChain `Embeddings` 的桥 |
| `VectorStoreManager` | 多 backend 统一入口 |

### 6.2 第四章最小契约

第四章最关键的约束：

1. 同一个 store 只能保存一个 embedding space。
2. query 和 stored vectors 必须来自同一个 embedding space。
3. metadata 不能在写入时丢失。
4. `upsert()` 和 `replace_document()` 是不同语义。
5. 删除应该支持 `document_id` 级别。
6. 查询结果必须能还原成 `RetrievalResult[]`。
7. backend 可以不同，但上层行为要可比较。

### 6.3 `EmbeddingSpace` 为什么重要

`EmbeddingSpace` 记录：

```text
provider_name
model_name
dimensions
```

它的意义是：

- 写入时校验 incoming chunks
- 查询时校验 query provider
- 读取时确认 store 没有混入异构向量

如果不校验 embedding space，系统可能会计算出“看似正常”的相似度分数，但语义上没有比较意义。

### 6.4 `RetrievalResult` 为什么重要

第四章不是返回裸分数，而是返回：

```text
RetrievalResult(chunk=SourceChunk, score=float)
```

这说明存储层做的不是“向量算分工具”，而是：

> 能把相似度结果重新还原成标准 chunk 结果的查询层。

第五章的 Retriever、后续生成层的引用、调试和评测，都依赖这个结果形状。

---

## 7. Backend 对比总表

| 能力 | JSON store | 原生 Chroma | LangChain Chroma |
|------|------------|-------------|------------------|
| 教学定位 | 原理层 | 真实数据库层 | 框架映射层 |
| 持久化位置 | `store/demo_vector_store.json` | `store/chroma/` | `store/langchain_chroma/` |
| 写入输入 | `EmbeddedChunk[]` | `EmbeddedChunk[]` | `Document[]` |
| 文本字段 | `chunk.content` | `documents` | `Document.page_content` |
| metadata | JSON dict | Chroma `metadatas` | `Document.metadata` |
| 向量字段 | `vector` | `embeddings` | 由 `Embeddings` 适配器生成 |
| query embedding | manager / 脚本显式调用 | manager / 脚本显式调用 | VectorStore 内部调用 |
| 过滤 | `filename` | `where` | `filter` |
| 删除 | `delete_by_document_id()` | `delete(where=...)` | `delete(ids=...)` |
| 返回 | `RetrievalResult[]` | wrapper 水合成 `RetrievalResult[]` | adapter 转成 `RetrievalResult[]` |

本章真正想让你看到的是：

```text
存储契约不变
backend 实现不同
适配层负责差异
上层尽量稳定
```

---

## 8. 治理锚点与失败案例

第四章还没有进入复杂 Retriever 策略，但已经有持久化状态和 backend 差异，所以必须建立最小治理锚点。

### 8.1 最重要的治理锚点

至少要关注：

1. `chunk_id / document_id`
2. `provider_name / model_name / dimensions`
3. `source / filename / suffix / char_start / char_end / chunk_chars`
4. store 路径或 collection 名称
5. `RetrievalResult` 标准结果形状

它们共同回答：

```text
当前存的是谁？
属于哪个 embedding space？
删除 / 替换的对象是谁？
查询命中的结果能不能还原成标准 chunk？
```

### 8.2 最小回归观察点

| 场景 | 期望 |
|------|------|
| `如何申请退费？` | 优先命中 `refund:0` |
| `为什么 metadata 很重要？` | 优先命中 `metadata:0` |
| `filename=metadata_rules.md` | 结果范围明显收窄 |
| 删除 `trial` | `trial:0` 不应继续出现在查询结果里 |
| 替换同一 `document_id` | 旧 chunk 不应残留 |
| 换 `model_name` 查询旧 store | 应直接失败 |
| 切换 backend | 结果仍应能回到 `RetrievalResult` |

### 8.3 值得刻意观察的失败案例

第一类是 embedding space 混用。

你可以故意换一个 `model_name` 或 `dimensions`，观察写入或查询怎样失败。这个失败很重要，因为跨空间相似度分数看起来也可能有数值，但语义上没有比较意义。

第二类是文档替换残留。

如果 `replace_document()` 只是简单 upsert 新 chunk，而没有删掉旧 chunk，同一份文档更新后就可能同时命中新旧版本。

第三类是删除不彻底。

如果删除只按一个 `chunk_id` 做，现实文档一旦被切成多个 chunk，就会出现旧内容残留。

第四类是 metadata filter 假生效。

过滤后如果结果范围没有明显收窄，就要检查 filter 是否真的传给了 store，而不是只在展示层筛了一下。

第五类是依赖缺失。

`chromadb`、`langchain-core`、`langchain-chroma` 缺失时，真实 backend 应该清晰失败，而不是让用户以为检索质量出了问题。

### 8.4 测试锁定什么

测试入口：

```bash
python -m unittest discover -s tests
```

当前测试锁定四层行为：

1. JSON store 的基本契约
2. Chroma 的真实持久化、过滤、删除
3. LangChain Chroma 的 `from_documents / similarity_search / as_retriever`
4. `VectorStoreManager` 的统一增删查改能力

测试不是为了追求覆盖率数字，而是在锁定第四章最重要的不变量：

- 同一个 store 不混用 embedding space
- `replace_document()` 不留下旧 chunk
- `delete_by_document_id()` 真正删除整份文档
- metadata filter 能缩小结果范围
- 不同 backend 返回的仍然是标准结果形状

---

## 9. 简化范围与选型认知

第四章代码刻意简化了这些内容：

1. 样例语料固定在 `demo_source_chunks()`
2. 不重新接第二章完整文档切分 pipeline
3. 不重新讲第三章真实 embeddings endpoint
4. JSON store 只做最小精确搜索
5. JSON store 的 metadata 过滤只支持 `filename`
6. Chroma 只实现本章需要的最小 CRUD、filter 和 delete
7. LangChain 只讲 VectorStore 映射，不展开 Retriever 策略
8. FAISS / Pinecone / Milvus / Weaviate 只做选型认知，不硬造 demo

这些简化不是降低知识密度，而是为了保证第四章的学习重心始终在：

> 存储层契约、真实 backend 映射、状态治理和可替换接口。

### 9.1 向量数据库选型认知

第四章当前正式实现 Chroma，是因为它适合第一站真实数据库：

- 轻量
- 本地持久化方便
- 能直接看 collection、metadata filter、delete
- 不会把学习重心带到运维和平台差异上

常见向量库的最小认知：

| 数据库 | 特点 | 更适合什么 |
|--------|------|------------|
| Chroma | 轻量、上手快、本地持久化方便 | 教学、原型、小项目 |
| FAISS | Meta 开源、纯本地、高性能 | 本地实验、离线索引、高性能原型 |
| Pinecone | 云服务、免运维 | 不想自建基础设施的生产场景 |
| Milvus | 开源、分布式、规模能力强 | 大规模生产部署 |
| Weaviate | 开源、功能丰富 | 企业知识库和复杂检索场景 |

这部分先建立选型感即可，不需要在第四章强行补所有 demo。

### 9.2 ANN vs 精确搜索

至少先知道：

- 精确搜索会逐个比较候选，结果最准，但规模大时慢
- ANN 会牺牲一点精确性，换取更好的查询速度

第四章不手写 ANN 索引，因为这会把注意力从“存储契约”拉走。

---

## 10. 常见疑惑与复盘问题

### 10.1 向量数据库是不是只是在保存向量

不是。

如果只保存 `list[float]`，检索结果就无法回到原文 chunk，也无法做引用、删除、替换和过滤。第四章里的向量存储必须同时保存：

- vector
- chunk 身份
- metadata
- embedding space

所以向量数据库在 RAG 里不是“向量数组仓库”，而是“语义索引和文档身份绑定的存储层”。

### 10.2 JSON store 已经能查，真实向量数据库还有什么价值

JSON store 的价值是教学原理层。它能让你看懂：

```text
写入
查询
替换
删除
过滤
空间校验
```

真实向量数据库补的是更工程化的能力，例如持久 collection、索引结构、批量写入、真实 metadata filter、数据库级删除和更适合扩展的数据组织方式。

### 10.3 `upsert()` 和 `replace_document()` 能不能合并

不建议合并。

`upsert()` 是 chunk 级语义，适合写入或覆盖一批明确的 chunk。

`replace_document()` 是 document 级语义，适合一份文档重新处理以后，用新 chunk 整体替换旧 chunk。

这两个动作混在一起，会让文档更新时很容易留下 stale chunks。

### 10.4 为什么删除不直接按 `chunk_id`

真实文档通常会被切成多个 chunk。

如果只按一个 `chunk_id` 删除，系统很容易删掉一小段，却留下同一文档的其他旧片段。第四章把 `delete_by_document_id()` 立成真实能力，是为了让文档级更新、下架和回填都有稳定操作入口。

### 10.5 为什么 Chroma metadata 里要放内部字段

Chroma 返回结果时需要能恢复本章自己的对象。

所以 metadata 里不仅有原文 metadata，还要保存：

- `_rag_chunk_id`
- `_rag_document_id`
- `_rag_provider_name`
- `_rag_model_name`
- `_rag_dimensions`

这些字段让 store 能在读回时重新构造 `SourceChunk / EmbeddedChunk / RetrievalResult`，也让 embedding space 校验和文档级删除有真实落点。

### 10.6 LangChain VectorStore 为什么仍然属于第四章

因为这里讲的是存储层接口映射。

`similarity_search()`、`similarity_search_with_score()` 和 `as_retriever()` 虽然已经接近检索入口，但本章只关心：

- provider 怎样适配成 LangChain `Embeddings`
- chunk 怎样适配成 LangChain `Document`
- 查询结果怎样回到 `RetrievalResult`
- VectorStore 怎样接上真实存储 backend

检索策略本身，例如 `top_k / threshold / MMR / bad cases`，放到第五章再系统讲。

### 10.7 manager 会不会掩盖 backend 差异

一个好的 manager 不应该假装 backend 没有差异。

第四章的 `VectorStoreManager` 只统一上层职责：

```text
add
search
replace
delete
```

底层差异仍然保留在各自 adapter 里。这样业务调用更稳定，同时读代码时仍然能看清 JSON、Chroma、LangChain 的不同实现方式。

---

## 11. 学完后应该能回答

学完第四章后，你应该能回答：

- 为什么 `EmbeddedChunk[]` 还不等于可用检索系统
- 第四章为什么先讲原理层 JSON store，再进入真实 Chroma
- `demo_source_chunks()`、`demo_vector_store.json`、Chroma collection 之间是什么关系
- query vector 什么时候生成，document vector 什么时候生成
- 为什么同一个 store 要守住同一个 embedding space
- `upsert()` 和 `replace_document()` 为什么不是同一个动作
- 为什么删除要围绕 `document_id`
- Chroma metadata 为什么要补内部字段
- `where` 和 LangChain `filter` 分别对应什么
- `chromadb / langchain-core / langchain-chroma` 分别是什么
- `similarity_search / similarity_search_with_score / as_retriever` 分别适合什么场景
- 为什么 `VectorStoreManager` 统一的是职责，而不是抹平所有 backend 差异

---

## 12. 下一章

第五章开始正式进入 Retriever 策略：

- `top_k`
- threshold
- MMR
- bad cases
- rerank
- hybrid retrieval

也就是说：

> 第四章解决“能不能稳地存和查”，第五章解决“怎么查得更好”。
