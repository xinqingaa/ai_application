# 04. 向量存储 - 实践指南

> 本文档说明如何跟着 [学习文档](../../../docs/04_rag/04_vector_databases.md) 学完第四章，并在不依赖第五章以后的前提下，看懂向量如何被真正存下来、查回来、按文档替换、按 `document_id` 删除，以及为什么存储层必须守住 embedding space 契约。

---

## 核心原则

```text
先把向量写进持久化存储 -> 再看 query 如何查回来 -> 最后看文档替换、filename 过滤和删除为什么必须提前出现
```

- 在 `source/04_rag/04_vector_databases/` 目录下操作
- 本章只讲向量存储层，不讲 Retriever 策略和生成
- 为了保持章节独立，代码在本章目录里保留一份可单章运行的最小实现
- 这份实现继续沿用第三章已经建立好的 `provider/model/dimensions` 和 metadata 契约
- 本章目录就是当前学习入口

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
  放本章最小对象、样例 `EmbeddedChunk[]`、本地持久化向量存储和契约校验逻辑
- `01_index_store.py`
  看 demo chunks 如何按文档级 `replace_document()` 真正写入磁盘
- `02_search_store.py`
  看 query 如何在同一 embedding space 里查回最相关 chunk
- `03_delete_document.py`
  看按 `document_id` 删除为什么重要，以及文档更新为什么不能只做 chunk 级 `upsert()`

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
- store 会打印当前 `provider/model/dimensions` 空间
- 文档更新路径应该优先走 `replace_document()`
- `chunk_id / document_id / metadata` 不再只是“留着以后用”，而是现在就进入存储和查询路径

---

## 第 1 步：看真实写入如何发生

**对应文件**：`01_index_store.py`

重点观察：

- 存储文件路径在哪里
- 当前 store 使用的 embedding space 是什么
- 为什么 demo index 默认走文档级 `replace_document()`
- 为什么 `--reset` 对实验很重要

---

## 第 2 步：看 query 如何查回 chunk

**对应文件**：`02_search_store.py`

重点观察：

- query 会先变成 query vector
- store 会校验 query provider 和 store provider 是否一致
- store 当前只支持 `filename` 过滤，不是通用 metadata filter
- 返回结果里为什么还要保留 `filename / source / suffix / chunk_index / range`

运行后重点看：

- `score`
- `document_id`
- `filename`
- filter 前后结果范围的变化

---

## 第 3 步：看删除为什么必须按 document_id 做

**对应文件**：`03_delete_document.py`

重点观察：

- 为什么删除不能只删一条文本
- 为什么 `document_id` 是一致性锚点
- 为什么文档更新应该走 `replace_document()`，而不是仅依赖 `upsert()`

---

## 第 4 步：最后看测试在锁定什么

**对应文件**：`tests/test_vector_store.py`

测试不是这一章的重点，但可以用来锁定最重要的边界：

1. 写入后重新加载仍然能读回 chunk
2. 相似度查询会优先返回相关内容
3. `filename` filter 会限制结果范围
4. 按 `document_id` 删除会移除整份文档
5. `replace_document()` 会清理同文档旧 chunk
6. query 和 store 不能跨 embedding space 混查

---

## 建议学习顺序

1. 先读 [第四章学习文档](../../../docs/04_rag/04_vector_databases.md)
2. 再跑 `python 01_index_store.py --reset`
3. 再跑 `python 02_search_store.py`
4. 最后跑 `python 03_delete_document.py trial`

---

## 学完这一章后你应该能回答

- 为什么只有向量还不够
- 为什么向量存储要负责写入、查询、替换、删除和持久化
- 为什么同一个 store 只能保留一个 embedding space
- 为什么 `upsert()` 和 `replace_document()` 不能混成一个模糊接口
- 为什么第四章当前只支持 `filename` 过滤

---

## 当前真实进度和下一章

- 当前真实进度：第四章已经改成独立学习单元，并与第三章对象契约对齐
- 完成标准：能写入、查询、按文档替换、删除，并解释这些能力为什么属于存储层
- 下一章：进入 [../05_retrieval_strategies/README.md](../05_retrieval_strategies/README.md)，把当前最小查询能力抽象成 Retriever，并比较 `top_k / threshold / MMR` 等策略
