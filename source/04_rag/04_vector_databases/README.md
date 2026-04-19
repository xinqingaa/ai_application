# 04. 向量存储 - 实践指南

> 本文档说明如何跟着 [学习文档](/Users/linruiqiang/work/ai_application/docs/04_rag/04_vector_databases.md) 学完第四章，并在不依赖第五章以后的前提下，看懂向量如何被真正存下来、查出来、过滤掉和删除掉。

---

## 核心原则

```text
先把向量写进持久化存储 -> 再看 query 如何查回来 -> 最后看过滤和删除为什么必须提前出现
```

- 在 `source/04_rag/04_vector_databases/` 目录下操作
- 本章只讲向量存储层，不讲 Retriever 策略和生成
- 为了保持章节独立，代码使用一个本地 JSON 持久化的最小向量存储
- 本章重点不是记某个库的 API，而是理解向量存储职责
- 旧的 `labs/phase_4_vector_databases/` 只作为迁移期备份，不再是当前学习入口

---

## 项目结构

```text
04_vector_databases/
├── README.md
├── vector_store_basics.py
├── 01_index_store.py
├── 02_search_store.py
├── 03_delete_document.py
├── store/
│   └── .gitignore
└── tests/
    └── test_vector_store.py
```

- `vector_store_basics.py`
  放本章所有最小对象、样例 `EmbeddedChunk[]`、本地持久化向量存储和查询逻辑
- `01_index_store.py`
  看向量如何被真正写入磁盘
- `02_search_store.py`
  看 query 如何命中最相关的 chunk
- `03_delete_document.py`
  看按 `document_id` 删除为什么重要

---

## 前置准备

### 1. 运行目录

```bash
cd source/04_rag/04_vector_databases
```

### 2. 当前命令

```bash
python 01_index_store.py --reset
python 02_search_store.py
python 02_search_store.py "为什么 metadata 很重要？" --filename metadata_rules.md
python 03_delete_document.py trial
python -m unittest discover -s tests
```

### 3. 先跑哪个

建议先跑：

```bash
python 01_index_store.py --reset
```

你最先要建立的直觉是：

- `EmbeddedChunk[]` 现在会被真正写进持久化存储
- `chunk_id / document_id / metadata` 不再只是“留着以后用”，而是现在就要参与查询和删除
- 第四章交付的是向量存储层，不是完整 Retriever 策略层

---

## 第 1 步：看真实写入如何发生

**对应文件**：`01_index_store.py`

重点观察：

- 存储文件路径在哪里
- 本次写入了多少个 chunk
- 当前有哪些 `document_id`
- 为什么 `--reset` 对实验很重要

---

## 第 2 步：看 query 如何查回 chunk

**对应文件**：`02_search_store.py`

重点观察：

- query 会先变成 query vector
- store 会按相似度找回最相关的 chunk
- 返回结果里为什么还要保留 `filename / source / chunk_index`

运行后重点看：

- `score`
- `filename`
- `document_id`
- filter 前后结果范围的变化

---

## 第 3 步：看删除为什么必须按 document_id 做

**对应文件**：`03_delete_document.py`

重点观察：

- 为什么删除不能只删一条文本
- 为什么 `document_id` 是一致性锚点
- 删除后剩余文档会怎样变化

---

## 第 4 步：最后看测试在锁定什么

**对应文件**：`tests/test_vector_store.py`

测试只锁定本章最重要的几件事：

1. 写入后重新加载仍然能读回 chunk
2. 相似度查询会优先返回相关内容
3. filename filter 会限制结果范围
4. 按 `document_id` 删除会移除整份文档

---

## 建议学习顺序

1. 先读 [04_vector_databases.md](/Users/linruiqiang/work/ai_application/docs/04_rag/04_vector_databases.md)
2. 再跑 `python 01_index_store.py --reset`
3. 再跑 `python 02_search_store.py`
4. 最后跑 `python 03_delete_document.py trial`

---

## 学完这一章后你应该能回答

- 为什么只有向量还不够
- 为什么向量存储要负责写入、查询、过滤、删除和持久化
- 为什么 `document_id` 会在这一章变成真实职责
- 为什么第四章现在还不应该把 Retriever 策略也塞进来

---

## 当前真实进度和下一章

- 当前真实进度：第四章已经改成独立学习单元
- 完成标准：能写入、查询、过滤、删除，并解释为什么这些能力属于存储层
- 下一章：进入 [source/04_rag/05_retrieval_strategies/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/05_retrieval_strategies/README.md)，把当前最小查询能力封装成 Retriever，并比较 `top_k / threshold / MMR` 等策略
