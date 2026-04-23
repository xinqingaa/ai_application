# 04. 向量数据库 - 实践指南

> 这份 README 只负责一件事：带你按正确顺序跑完第四章，先看最小 JSON store，再看真实 `Chroma`，然后补上 LangChain VectorStore 和统一管理器，把“原理层”和“真实工具层”连起来。

---

## 核心原则

```text
先看原理层 -> 再看真实数据库 -> 再看 LangChain 映射 -> 最后看统一管理器
```

- 在 `source/04_rag/04_vector_databases/` 目录下操作
- 第四章只讲向量存储层，不讲 Retriever 策略和生成
- 原有 JSON store 继续保留，作为教学原理层
- `Chroma` 和 `LangChain Chroma` 是本章新增的真实工具层
- 第 10 节“向量数据库基础”以文档讲解为主，不额外造 FAISS / Pinecone / Milvus demo
- 旧的 `labs/phase_4_vector_databases/` 只作为迁移期备份，不再是当前学习入口

---

## 项目结构

```text
04_vector_databases/
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

- `vector_store_basics.py`
  第四章原理层：对象、`EmbeddingSpace`、最小 JSON store、契约校验
- `chroma_store.py`
  真实 `Chroma` 存储适配
- `langchain_adapter.py`
  把当前章节的 `EmbeddingProvider` 包成 LangChain `Embeddings`
- `vector_store_manager.py`
  第四章综合案例：统一的向量存储管理器
- `01-03`
  原理层脚本
- `04-05`
  原生 Chroma 脚本，包含复合 `where` 过滤演示
- `06-07`
  LangChain Chroma 和统一管理器脚本

---

## 前置准备

### 1. 运行目录

```bash
cd source/04_rag/04_vector_databases
```

### 2. 安装依赖

```bash
python -m pip install -r requirements.txt
```

### 3. 当前命令

```bash
python 01_index_store.py --reset
python 02_search_store.py
python 03_delete_document.py trial
python 04_chroma_crud.py --reset
python 05_chroma_filter_delete.py "为什么 metadata 很重要？" --filename metadata_rules.md --suffix .md --document-id metadata
python 06_langchain_vectorstore.py "为什么 metadata 很重要？" --filename metadata_rules.md --init-mode from_documents --retriever-search-type similarity --reset
python 07_vector_store_manager.py --backend chroma --add-document-id faq --add-text "课程退款请联系助教。" "如何申请退费？"
python 07_vector_store_manager.py --backend langchain --replace-document-id trial --replace-text "试学需要提前预约并完成登记。" "如何预约试学？"
python -m unittest discover -s tests
```

---

## 先怎么读代码

### 1. 第一遍只看对象

先打开 [vector_store_basics.py](./vector_store_basics.py)，只看这些对象：

- `SourceChunk`
- `EmbeddedChunk`
- `RetrievalResult`
- `EmbeddingSpace`
- `VectorStoreConfig`
- `PersistentVectorStore`

然后再补看：

- `ChromaVectorStoreConfig`
- `ChromaVectorStore`
- `ProviderEmbeddingsAdapter`
- `VectorStoreManager`

这一遍的目标不是理解所有逻辑，而是先知道：

- 第四章有哪些最小运行时对象
- 哪些对象属于原理层，哪些属于真实工具层
- 为什么第四章不是只返回一组相似度分数

### 2. 第二遍只看主流程

然后再看这些函数和方法：

- `embed_chunks()`
- `embedding_space()`
- `upsert()`
- `replace_document()`
- `similarity_search()`
- `delete_by_document_id()`
- `build_documents()`
- `retrieval_results_from_scored_documents()`
- `VectorStoreManager.search()`

这一遍只回答一个问题：

```text
一组 EmbeddedChunk 进入第四章以后，到底按什么顺序变成可持久化、可查询、可替换、可删除的结果？
```

### 3. 第三遍再看 backend 映射和回归

最后再看：

- `chroma_store.py`
- `langchain_adapter.py`
- `vector_store_manager.py`
- `tests/`

这样读会比一开始从头到尾顺着扫更容易建立结构感。

---

## 建议学习顺序

### 第 1 步：先跑原理层

```bash
python 01_index_store.py --reset
python 02_search_store.py
python 03_delete_document.py trial
```

重点观察：

- JSON store 的持久化路径
- `replace_document()` 为什么是默认更新入口
- query / store 的 embedding space 校验
- 删除为什么围绕 `document_id`

### 第 2 步：再跑真实 Chroma

```bash
python 04_chroma_crud.py --reset
python 05_chroma_filter_delete.py "为什么 metadata 很重要？" --filename metadata_rules.md
python 05_chroma_filter_delete.py "为什么 metadata 很重要？" --filename metadata_rules.md --suffix .md --document-id metadata
python 05_chroma_filter_delete.py "如何申请退费？" --delete-document-id trial
```

重点观察：

- `store/chroma/` 下真的会有持久化数据
- Chroma 也必须保留 `chunk_id / document_id / provider / model / dimensions`
- metadata filter 已经走真实数据库
- 多字段过滤在 Chroma 中会落成显式 `$and`
- 删除已经不是“删 JSON 记录”，而是删 collection 中的一批向量

### 第 3 步：最后跑 LangChain Chroma

```bash
python 06_langchain_vectorstore.py "为什么 metadata 很重要？" --filename metadata_rules.md --init-mode add_documents --reset
python 06_langchain_vectorstore.py "为什么 metadata 很重要？" --filename metadata_rules.md --init-mode from_documents
python 06_langchain_vectorstore.py "如何申请退费？" --retriever-search-type mmr
python 07_vector_store_manager.py --backend json "如何申请退费？"
python 07_vector_store_manager.py --backend chroma --add-document-id faq --add-text "课程退款请联系助教。" "如何申请退费？"
python 07_vector_store_manager.py --backend langchain --replace-document-id trial --replace-text "试学需要提前预约并完成登记。" "如何预约试学？"
```

重点观察：

- 同一个本章 provider 怎样映射成 LangChain `Embeddings`
- 同一批 chunk 怎样映射成 LangChain `Document`
- `add_documents` 和 `from_documents` 都只是不同初始化入口
- `as_retriever()` 在第四章只做接口认知，第五章才展开策略
- `json / chroma / langchain` 三个 backend 只是接口形态不同，职责边界相同

### 第 4 步：最后跑统一管理器

```bash
python 07_vector_store_manager.py --backend json --delete-document-id trial "如何申请退费？"
python 07_vector_store_manager.py --backend chroma --add-document-id faq --add-text "课程退款请联系助教。" "如何申请退费？"
python 07_vector_store_manager.py --backend langchain --replace-document-id trial --replace-text "试学需要提前预约并完成登记。" "如何预约试学？"
```

重点观察：

- manager 不再只是 backend 对照脚本，而是有真实 `add / search / replace / delete`
- 当前综合案例先统一 `json / chroma / langchain`
- `FAISS` 作为适配器扩展位保留在文档层，不在第四章硬造伪实现

### 第 5 步：最后看测试在锁定什么

```bash
python -m unittest discover -s tests
```

这组测试锁定四类行为：

1. JSON store 的基本契约
2. Chroma 的真实持久化、过滤、删除
3. LangChain Chroma 的 `from_documents / similarity_search / as_retriever`
4. `VectorStoreManager` 的统一增删查改能力

---

## 第四章最小回归集

第四章当前最值得反复观察的几条 case：

1. `如何申请退费？` 应优先命中 `refund:0`
2. `为什么 metadata 很重要？` 应优先命中 `metadata:0`
3. `filename=metadata_rules.md` 过滤后，结果只应留在对应文档范围
4. 删除 `trial` 后，不应再保留该文档 chunk
5. 若 query / provider 和 store 不在同一 embedding space，系统应直接拒绝
6. Chroma 复合过滤会使用显式 `$and`
7. LangChain `from_documents` 和 `add_documents` 都能建立同一类查询闭环

---

## 失败案例也要刻意观察

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

这些失败案例很重要，因为它们会帮你分清：

- 哪些是章节边界
- 哪些是存储层不变量
- 哪些变化会影响后续章节

---

## 建议主动修改的地方

如果你只阅读不改动，很容易停留在“看懂了”的错觉里。

建议主动试三类小改动：

1. 改一个 `document_id`，观察 replace / delete 路径会怎样变化
2. 增加一个 metadata 字段，观察 JSON / Chroma / LangChain 三层如何透传
3. 故意换一个 `model_name`，观察 store space 校验如何直接失败

每次只改一处，这样你才能看清楚：

- 哪个字段在支撑替换和删除
- 哪个规则在支撑空间一致性
- 哪种变化属于“存储契约变化”，哪种只是“样例内容变化”

---

## 本章边界

- 不展开 Retriever 策略
- 不展开 rerank
- 不展开 hybrid retrieval
- 不做多向量库横评
- 不系统展开复杂 metadata DSL

第四章当前真正要立住的是：

> 向量怎么稳地存、查、替换、删，以及这些能力怎样映射到真实工具。

---

## 学完这一章后你应该能回答

- 为什么第四章不能只剩一个本地 JSON 示例
- 为什么第 10 节的“选型基础”更适合先放在文档里讲清楚
- 为什么 `EmbeddingSpace` 是第四章真正的核心身份对象
- 为什么 Chroma 里仍然需要自己守住 embedding space
- 为什么 LangChain VectorStore 仍然属于第四章而不是第五章
- 为什么 `upsert()` 和 `replace_document()` 不能混成一个模糊概念
- 为什么综合案例需要统一 manager，而不是继续堆 backend 对照脚本

---

## 下一章

下一章进入 [../05_retrieval_strategies/README.md](../05_retrieval_strategies/README.md)。

第五章开始，你才会正式把当前最小查询能力抽象成 Retriever，并比较 `top_k / threshold / MMR` 等策略。
