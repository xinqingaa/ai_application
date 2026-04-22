# 04. 向量数据库 - 实践指南

> 这份 README 只负责一件事：带你按正确顺序跑完第四章，先看最小 JSON store，再看真实 `Chroma`，最后看 `LangChain Chroma`，把“原理层”和“真实工具层”连起来。

---

## 核心原则

```text
先看原理层 -> 再看真实数据库 -> 最后看上层 VectorStore 抽象
```

- 在 `source/04_rag/04_vector_databases/` 目录下操作
- 第四章只讲向量存储层，不讲 Retriever 策略和生成
- 原有 JSON store 继续保留，作为教学原理层
- `Chroma` 和 `LangChain Chroma` 是本章新增的真实工具层
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
    └── test_langchain_vectorstore.py
```

- `vector_store_basics.py`
  第四章原理层：对象、最小 JSON store、契约校验
- `chroma_store.py`
  真实 `Chroma` 存储适配
- `langchain_adapter.py`
  把当前章节的 `EmbeddingProvider` 包成 LangChain `Embeddings`
- `01-03`
  原理层脚本
- `04-05`
  原生 Chroma 脚本
- `06-07`
  LangChain Chroma 和 backend 对照脚本

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
python 05_chroma_filter_delete.py "为什么 metadata 很重要？" --filename metadata_rules.md
python 06_langchain_vectorstore.py "为什么 metadata 很重要？" --filename metadata_rules.md --reset
python 07_vector_store_manager.py --backend chroma "如何申请退费？"
python -m unittest discover -s tests
```

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
- query/store 的 embedding space 校验
- 删除为什么围绕 `document_id`

### 第 2 步：再跑真实 Chroma

```bash
python 04_chroma_crud.py --reset
python 05_chroma_filter_delete.py "为什么 metadata 很重要？" --filename metadata_rules.md
python 05_chroma_filter_delete.py "如何申请退费？" --delete-document-id trial
```

重点观察：

- `store/chroma/` 下真的会有持久化数据
- Chroma 也必须保留 `chunk_id / document_id / provider / model / dimensions`
- metadata filter 已经走真实数据库
- 删除已经不是“删 JSON 记录”，而是删 collection 中的一批向量

### 第 3 步：最后跑 LangChain Chroma

```bash
python 06_langchain_vectorstore.py "为什么 metadata 很重要？" --filename metadata_rules.md --reset
python 07_vector_store_manager.py --backend json "如何申请退费？"
python 07_vector_store_manager.py --backend chroma "如何申请退费？"
python 07_vector_store_manager.py --backend langchain "如何申请退费？"
```

重点观察：

- 同一个本章 provider 怎样映射成 LangChain `Embeddings`
- 同一批 chunk 怎样映射成 LangChain `Document`
- `json / chroma / langchain` 三个 backend 只是接口形态不同，职责边界相同

### 第 4 步：最后跑测试

```bash
python -m unittest discover -s tests
```

这组测试锁定三类行为：

1. JSON store 的基本契约
2. Chroma 的真实持久化、过滤、删除
3. LangChain Chroma 的最小接入闭环

---

## Mini 回归集

第四章当前最值得反复观察的几条 case：

1. `如何申请退费？` 应优先命中 `refund:0`
2. `为什么 metadata 很重要？` 应优先命中 `metadata:0`
3. `filename=metadata_rules.md` 过滤后，结果只应留在对应文档范围
4. 删除 `trial` 后，不应再保留该文档 chunk
5. 若 query/provider 和 store 不在同一 embedding space，系统应直接拒绝

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
- 为什么 Chroma 里仍然需要自己守住 embedding space
- 为什么 LangChain VectorStore 仍然属于第四章而不是第五章
- 为什么 `upsert()` 和 `replace_document()` 不能混成一个模糊概念

---

## 下一章

下一章进入 [../05_retrieval_strategies/README.md](../05_retrieval_strategies/README.md)。

第五章开始，你才会正式把当前最小查询能力抽象成 Retriever，并比较 `top_k / threshold / MMR` 等策略。
