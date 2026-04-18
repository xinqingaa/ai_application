# 03. 向量化

> 本节目标：理解第三章为什么不能脱离前两章单独学习，并能对着 `phase_1_scaffold -> phase_2_document_processing -> phase_3_embeddings` 这三份代码快照，看懂 RAG 的对象、输入链路和向量化能力是怎样连续长出来的。

---

## 1. 概述

### 学习目标

完成本章后，你应该能够：

- 能说明第一章、第二章、第三章分别在整条 RAG 主线里解决什么问题
- 能解释为什么第一章先立 `SourceChunk / RetrievalResult / AnswerResult` 和项目分层，而不是直接讲 Embedding
- 能解释为什么第二章必须先把原始文件稳定整理成 `SourceChunk`
- 能说明第三章新增的不是“另一套输入管道”，而是 `SourceChunk -> EmbeddedChunk` 这层增量
- 能区分 `embed_query()` 和 `embed_documents()` 为什么要保留为两个入口
- 能运行第三章脚本，并直接看出向量结果如何继承前两章的 `chunk_id / document_id / metadata`
- 能说清第三章为什么只做到向量化，而不提前混进向量数据库和完整检索

### 本章在 `04_rag` 中的位置

第三章不是一章独立的“Embedding 知识点”，而是前三章主线里的第三个连续实现阶段。

如果把前三章压缩成一句话：

- 第一章回答：这套系统的骨架、对象和分层为什么这样设计
- 第二章回答：原始文件怎样稳定变成标准 `SourceChunk`
- 第三章回答：标准 `SourceChunk` 怎样稳定变成 `EmbeddedChunk`

三章连起来，最小主线是：

```text
Phase 1:
项目骨架 -> SourceChunk / RetrievalResult / AnswerResult -> 最小 RAG 形状

Phase 2:
文件 -> loader -> splitter -> metadata -> stable ids -> SourceChunk[]

Phase 3:
SourceChunk[] -> EmbeddingProvider -> vector -> EmbeddedChunk[]
```

后面章节都会建立在这个连续结果之上：

- 第四章：把 `EmbeddedChunk` 写入向量存储
- 第五章：围绕这些向量做召回和排序
- 第六章：把检索结果接成真正的回答

### 学习前提

开始第三章前，建议你至少已经回看下面这些内容：

- [01_rag_basics.md](/Users/linruiqiang/work/ai_application/docs/04_rag/01_rag_basics.md)
- [02_document_processing.md](/Users/linruiqiang/work/ai_application/docs/04_rag/02_document_processing.md)
- [phase_1_scaffold/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/README.md)
- [phase_2_document_processing/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/README.md)
- [phase_1_scaffold/app/schemas.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/schemas.py)
- [phase_2_document_processing/app/indexing/index_manager.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/indexing/index_manager.py)

如果这几处没先看清，第三章很容易被误读成“从文本直接生成几个向量”。

### 本章边界

本章重点解决的是：

1. 为什么向量化必须建立在前两章之上
2. `SourceChunk` 如何批量变成 `EmbeddedChunk`
3. `EmbeddingProvider` 接口应该长什么样
4. 为什么 query 和 document 的向量化入口要分开
5. 第三章怎样为下一章向量数据库提供标准输入

本章不展开：

- 真实向量数据库写入
- Top-K 检索、MMR、Threshold 等召回策略
- Rerank 和混合检索
- LLM 生成答案
- Embedding 模型横向评测
- 本地推理部署和 GPU 优化

第三章的目标不是“把检索系统做完”，而是先把三章主线里的“向量层”独立讲清楚。

### 第一入口

第三章有三个层次的入口，职责不同：

- 回顾入口 1：
  [phase_1_scaffold/app/schemas.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/schemas.py)
- 回顾入口 2：
  [phase_2_document_processing/app/indexing/index_manager.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/indexing/index_manager.py)
- 本章阅读入口：
  [phase_3_embeddings/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_3_embeddings/README.md)

为什么这样安排：

- 第一章先提醒你：本课程最早就把 `SourceChunk` 这种标准对象立住了
- 第二章先提醒你：第三章真正的输入不是原始文件，而是稳定 `SourceChunk`
- 第三章 README 再带你进入向量化层本身

### 第一运行入口

本章第一运行入口是：

- [scripts/embed_documents.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_3_embeddings/scripts/embed_documents.py)

这份脚本现在不仅展示向量结果，还会明确打印：

- 当前向量化是怎样承接第一章的对象契约
- 当前 `EmbeddedChunk` 是怎样继承第二章的 `chunk_id / document_id / metadata`

### 第二运行入口

真正理解第三章时，还要尽快跑：

- [scripts/compare_similarity.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_3_embeddings/scripts/compare_similarity.py)

因为第三章最关键的观察对象不是“向量长什么样”，而是：

- 为什么相关文本更近
- 为什么 query/document 两条路径要分开
- 为什么排序结果仍然保留第二章的 chunk 身份

---

## 2. 先把前三章串起来：第三章到底接在什么后面 📌

第三章必须始终服从 [outline.md](/Users/linruiqiang/work/ai_application/docs/04_rag/outline.md) 的学习路线，但真正理解它时，不能只看第三章自己。

### 2.1 第一章先立下了什么

第一章的真正任务不是“把 RAG 做出来”，而是先立下后面所有章节都要复用的骨架和对象。

你需要先记住第一章已经完成了三件事：

1. 项目分层已经立住
2. `SourceChunk / RetrievalResult / AnswerResult` 已经立住
3. `embeddings/`、`vectorstores/`、`retrievers/` 这些目录已经预留好扩展位

对应代码主要在：

- [phase_1_scaffold/app/schemas.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/schemas.py)
- [phase_1_scaffold/app/retrievers/base.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/retrievers/base.py)
- [phase_1_scaffold/app/services/rag_service.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/services/rag_service.py)
- [phase_1_scaffold/app/embeddings/providers.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/embeddings/providers.py)

所以第三章今天能直接把 `app/embeddings/` 补成真实实现，不是突然多出来的设计，而是第一章一开始就预留好的位置。

### 2.2 第二章真正产出了什么

第二章的真正完成物不是“能读文件”，而是：

> 把原始文件稳定整理成后续系统可复用的 `SourceChunk[]`。

第二章在工程上真正交付的是：

```text
文件
-> discover_documents()
-> load_document()
-> split_text()
-> build_base_metadata()
-> build_chunk_metadata()
-> stable_document_id() / stable_chunk_id()
-> SourceChunk[]
```

对应代码主要在：

- [phase_2_document_processing/app/ingestion/loaders.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/ingestion/loaders.py)
- [phase_2_document_processing/app/ingestion/splitters.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/ingestion/splitters.py)
- [phase_2_document_processing/app/ingestion/metadata.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/ingestion/metadata.py)
- [phase_2_document_processing/app/indexing/index_manager.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/indexing/index_manager.py)

这就是第三章真正的输入层。

### 2.3 第三章新增的到底是什么

第三章新增的不是另一套 loader，也不是另一套索引脚本。

第三章只新增这一层：

```text
SourceChunk[]
-> embed_documents()
-> EmbeddedChunk[]
```

对应代码主要在：

- [phase_3_embeddings/app/schemas.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_3_embeddings/app/schemas.py)
- [phase_3_embeddings/app/embeddings/providers.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_3_embeddings/app/embeddings/providers.py)
- [phase_3_embeddings/app/embeddings/vectorizer.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_3_embeddings/app/embeddings/vectorizer.py)
- [phase_3_embeddings/app/embeddings/similarity.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_3_embeddings/app/embeddings/similarity.py)

你现在最需要建立的判断不是“第三章会不会更复杂”，而是：

> 第三章只是把第二章稳定产出的 `SourceChunk` 再升级一层，而不是推翻前两章。

### 2.4 三章对象是怎样连续演进的

| 阶段 | 核心对象 | 这一章新增了什么 | 下一章会拿它做什么 |
|------|----------|------------------|--------------------|
| 第一章 | `SourceChunk`、`RetrievalResult`、`AnswerResult` | 把对象契约和系统分层立住 | 让后续每章都在同一套对象上继续长 |
| 第二章 | `SourceChunk` | 把文件稳定产成带 metadata 和 stable ids 的 chunk | 给第三章提供统一输入 |
| 第三章 | `EmbeddedChunk` | 在 `SourceChunk` 外包一层向量、provider、model 信息 | 给第四章提供向量存储输入 |

这里最关键的一点是：

- `EmbeddedChunk` 不是替代 `SourceChunk`
- `EmbeddedChunk` 是把 `SourceChunk` 保留下来，再额外加上向量负载

### 2.5 三章合在一起的最小主数据流

把前三章合起来，最小主线应该这样理解：

```text
Phase 1:
定义 SourceChunk / RetrievalResult / AnswerResult

Phase 2:
文件 -> loader -> splitter -> metadata -> stable ids -> SourceChunk[]

Phase 3:
SourceChunk[] -> provider.embed_documents() -> EmbeddedChunk[]
question -> provider.embed_query() -> query vector
query vector + EmbeddedChunk[] -> similarity score
```

如果不先这样看，第三章最常见的误解就是：

1. 把向量化误读成“直接对原始文件做 embedding”
2. 把 `EmbeddedChunk` 误读成完全替代了 `SourceChunk`
3. 把 `embed_query()` 和 `embed_documents()` 误读成只是两个名字不同的同一接口

---

## 3. 第三章的代码设计与目录规划 📌

### 3.1 为什么第三章必须继续沿用前两章的目录

第三章没有另起一套项目，而是直接继承 `phase_2_document_processing`，根本原因是：

1. 第一章已经把分层和扩展点立住了
2. 第二章已经把 chunk 输入层做稳了
3. 第三章只需要在 `app/embeddings/` 里补当前章节的增量

这也是为什么第三章的正确理解方式不是“再看一个新项目”，而是：

> 在同一套项目骨架上，看本章到底补了哪一层。

### 3.2 哪些部分是继承的，哪些部分是第三章新增的

| 模块 | 第一章角色 | 第二章角色 | 第三章角色 |
|------|------------|------------|------------|
| `app/schemas.py` | 定义公共对象契约 | 继续复用 `SourceChunk` | 新增 `EmbeddedChunk` |
| `app/ingestion/` | 先露出最小入口 | 变成真实文件输入层 | 继续沿用，不新增职责 |
| `app/indexing/` | 先露出 chunk 收口点 | 变成真实 `SourceChunk` 生产入口 | 继续沿用，作为向量化输入 |
| `app/embeddings/` | 只有预留接口位 | 仍然占位 | 本章补成真实实现 |
| `scripts/` | 观察骨架和最小链路 | 观察真实 chunk | 观察 chunk 如何变成 vector |
| `tests/` | 验证骨架存在 | 验证 chunk 稳定 | 验证向量化是对前两章的增量，而不是重写 |

### 3.3 为什么 `app/embeddings/` 必须单独成层

这是第三章最核心的设计判断之一。

很多人在做 RAG 时会把这些步骤全写进一个“大索引脚本”里，但这样会破坏前三章好不容易建立起来的边界。

这里必须分清：

| 层 | 解决什么问题 | 不解决什么问题 |
|----|--------------|----------------|
| `ingestion` | 文件如何进入系统 | 不负责生成 chunk ID 和向量 |
| `indexing` | 标准 `SourceChunk` 如何被组织出来 | 不负责生成向量 |
| `embeddings` | `SourceChunk` 如何变成向量 | 不负责写入向量存储 |
| `vectorstores` | 向量如何存和查 | 不负责重新切分文档 |

你当前阶段最需要建立的判断不是“少写几层是不是更省事”，而是：

> 前三章每一层都先解决一个清晰问题，后面章节才不用回头重构。

### 3.4 为什么第三章默认先用本地 Provider

第三章当前最重要的学习目标是：

1. 看懂接口
2. 看懂对象
3. 看懂数据流

不是一上来就被 API Key、网络和计费打断。

所以第三章默认策略是：

- 先用 `local_hash` Provider 建立完整向量化直觉
- 保留 `openai_compatible` Provider 接口位
- 等真正需要真实 Provider 时，再切配置，而不是推翻目录和脚本

这和前面 `02_llm` 里“把平台差异收敛到 Provider 和配置层”的思路是一致的。

---

## 4. 按什么顺序对着三章代码学习

### 第 1 步：先回看第一章的对象和分层

**对应文件**：

- [phase_1_scaffold/app/schemas.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/schemas.py)
- [phase_1_scaffold/app/retrievers/base.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/retrievers/base.py)
- [phase_1_scaffold/app/embeddings/providers.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/embeddings/providers.py)

这一小步要解决什么：

- 第一章最早就把哪些对象和目录边界立住了
- 为什么第三章今天能直接在 `app/embeddings/` 里继续长
- 为什么 `SourceChunk` 在第三章仍然是核心对象

### 第 2 步：再确认第二章到底交付了什么

**对应文件**：

- [phase_2_document_processing/app/indexing/index_manager.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/indexing/index_manager.py)
- [phase_2_document_processing/scripts/inspect_chunks.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/scripts/inspect_chunks.py)
- [phase_2_document_processing/tests/test_document_processing.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/tests/test_document_processing.py)

这一小步要解决什么：

- 第二章的输出为什么是稳定 `SourceChunk`
- 第三章为什么不需要再重写一套文档处理
- `chunk_id / document_id / metadata` 为什么今天还能继续被看到

### 第 3 步：再进入第三章的配置和 Provider

**对应文件**：

- [phase_3_embeddings/app/config.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_3_embeddings/app/config.py)
- [phase_3_embeddings/app/embeddings/providers.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_3_embeddings/app/embeddings/providers.py)

这一小步要解决什么：

- 当前默认 Provider 是谁
- 默认维度和模型名是什么
- 为什么 `local_hash` 和 `openai_compatible` 都要收敛到同一接口
- 为什么 query/document 的向量化入口从这一章开始就要分开

### 第 4 步：看第三章真正新增的数据流

**对应文件**：

- [phase_3_embeddings/app/schemas.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_3_embeddings/app/schemas.py)
- [phase_3_embeddings/app/embeddings/vectorizer.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_3_embeddings/app/embeddings/vectorizer.py)
- [phase_3_embeddings/scripts/embed_documents.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_3_embeddings/scripts/embed_documents.py)

这一小步要解决什么：

- `EmbeddedChunk` 为什么不是裸 `list[float]`
- 为什么第三章要把 `SourceChunk` 保留下来而不是替换掉
- 为什么脚本输出里应该还能看到 `chunk_id / document_id / metadata`

### 第 5 步：最后看最小相似度实验和测试

**对应文件**：

- [phase_3_embeddings/app/embeddings/similarity.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_3_embeddings/app/embeddings/similarity.py)
- [phase_3_embeddings/scripts/compare_similarity.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_3_embeddings/scripts/compare_similarity.py)
- [phase_3_embeddings/tests/test_embeddings.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_3_embeddings/tests/test_embeddings.py)

这一小步要解决什么：

- 为什么向量相似度能表达“语义上更接近”
- 为什么排序结果仍然保留第二章的 chunk 身份
- 为什么第三章测试会专门验证“Phase 3 复用 Phase 2 的 chunk id 和 metadata”

---

## 5. 三章代码映射表

| 你现在要理解的内容 | 第一章代码 | 第二章代码 | 第三章代码 |
|--------------------|------------|------------|------------|
| 公共对象契约 | [phase_1_scaffold/app/schemas.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/schemas.py) | 继续复用 `SourceChunk` | [phase_3_embeddings/app/schemas.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_3_embeddings/app/schemas.py) 新增 `EmbeddedChunk` |
| 输入层和 chunk 收口点 | [phase_1_scaffold/app/indexing/index_manager.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/indexing/index_manager.py) 先露出形状 | [phase_2_document_processing/app/indexing/index_manager.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/indexing/index_manager.py) 真正产出稳定 chunk | [phase_3_embeddings/app/embeddings/vectorizer.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_3_embeddings/app/embeddings/vectorizer.py) 继续消费这些 chunk |
| Embedding 抽象位 | [phase_1_scaffold/app/embeddings/providers.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/embeddings/providers.py) 预留接口 | 仍然只是占位 | [phase_3_embeddings/app/embeddings/providers.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_3_embeddings/app/embeddings/providers.py) 补成真实实现 |
| 第一观察入口 | [phase_1_scaffold/scripts/query_demo.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/scripts/query_demo.py) 看最小 RAG 形状 | [phase_2_document_processing/scripts/inspect_chunks.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/scripts/inspect_chunks.py) 看真实 chunk | [phase_3_embeddings/scripts/embed_documents.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_3_embeddings/scripts/embed_documents.py) 看 chunk 变成 vector |
| 本章验收方式 | [phase_1_scaffold/tests/test_scaffold.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/tests/test_scaffold.py) 验骨架 | [phase_2_document_processing/tests/test_document_processing.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/tests/test_document_processing.py) 验稳定 chunk | [phase_3_embeddings/tests/test_embeddings.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_3_embeddings/tests/test_embeddings.py) 验向量化增量仍保留前两章结果 |

---

## 6. 这一章建议怎么跑

如果你要真正把前三章串起来，建议按这个顺序：

### 第 1 组：回顾第一章的最小闭环

```bash
cd source/04_rag/labs/phase_1_scaffold
python3 scripts/query_demo.py
```

这一组命令的意义是：

- 先回想第一章真正固定的是最小对象和最小服务链路
- 提醒自己第三章不是突然出现的新系统

### 第 2 组：回顾第二章的稳定 chunk

```bash
cd source/04_rag/labs/phase_2_document_processing
python3 scripts/inspect_chunks.py
```

这一组命令的意义是：

- 先确认第二章真正交付的是稳定 `SourceChunk`
- 看清 `chunk_id / document_id / metadata` 在第三章之前就已经存在

### 第 3 组：进入第三章的向量化增量

```bash
cd source/04_rag/labs/phase_3_embeddings
python3 scripts/embed_documents.py
python3 scripts/compare_similarity.py
python3 -m unittest discover -s tests
```

这一组命令的意义是：

- `embed_documents.py`
  直接看第三章如何保留前两章的 chunk 身份，并新增向量信息。
- `compare_similarity.py`
  直接看 query/document 路径和相似度排序。
- `unittest`
  直接看第三章怎样用测试锁定“它只是增量，不是重写”。

---

## 7. 实践任务

1. 用自己的话复述前三章各自的完成物是什么，不能只说“第一章讲概念、第二章讲文档、第三章讲 embedding”。
2. 对照 [phase_1_scaffold/app/schemas.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/schemas.py) 和 [phase_3_embeddings/app/schemas.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_3_embeddings/app/schemas.py)，说清 `EmbeddedChunk` 为什么不是替代 `SourceChunk`。
3. 跑一次 [phase_2_document_processing/scripts/inspect_chunks.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/scripts/inspect_chunks.py)，再跑一次 [phase_3_embeddings/scripts/embed_documents.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_3_embeddings/scripts/embed_documents.py)，对比哪些字段是继承的，哪些字段是第三章新增的。
4. 修改 `default_embedding_dimensions`，重新运行第三章脚本，观察哪些输出会变，哪些 chunk 身份字段不会变。
5. 自己增加两组文本，比较“相关文本”和“无关文本”的相似度差异，并解释为什么这一步现在还不需要向量数据库。

---

## 8. 完成标准

完成这一章后，至少应满足：

- 能把前三章串成一条连续工程主线，而不是三个分散知识点
- 能解释为什么第一章先立骨架和对象，第二章先稳 `SourceChunk`，第三章再补 `EmbeddedChunk`
- 能说明第三章为什么不应该重新实现 loader、splitter 和 stable id
- 能运行第三章脚本，并直接看出它保留了第二章的 `chunk_id / document_id / metadata`
- 能区分 `embed_query()` 和 `embed_documents()` 的职责
- 能说明第三章输出为什么能直接交给第四章向量数据库使用
