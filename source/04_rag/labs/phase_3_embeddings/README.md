# phase_3_embeddings

> 第三章代码快照的任务，不是单独演示 Embedding，而是把第一章已经立好的对象和分层、第二章已经稳定下来的 `SourceChunk`，继续长成第三章的 `EmbeddedChunk`。

---

## 核心原则

```text
先回看 Phase 1 的对象契约 -> 再确认 Phase 2 的稳定 chunk -> 最后进入 Phase 3 的向量化增量
```

这一章的重点不是“第三章多了几个脚本”，而是：

- 第一章为什么先把 `SourceChunk` 和 `app/embeddings/` 这些扩展位立住
- 第二章为什么必须先把文件整理成稳定 `SourceChunk`
- 第三章为什么只新增 `SourceChunk -> EmbeddedChunk` 这一层
- 为什么下一章可以直接拿第三章输出去接向量数据库

- 你现在看到的是 `04_rag` 第三章的真实代码入口
- 这一章默认和 [docs/04_rag/03_embeddings.md](/Users/linruiqiang/work/ai_application/docs/04_rag/03_embeddings.md) 配套阅读
- 没有 API Key 也可以完整学习这一章，因为默认 Provider 是本地 `local_hash`

## 先把三章的关系看清楚

如果只看第三章，很容易误解成：

> 拿文本直接生成几个向量，再算一下相似度。

这不对。

前三章真正的连续主线是：

```text
Phase 1:
项目骨架 + SourceChunk / RetrievalResult / AnswerResult

Phase 2:
文件 -> loader -> splitter -> metadata -> stable ids -> SourceChunk[]

Phase 3:
SourceChunk[] -> provider.embed_documents() -> EmbeddedChunk[]
question -> provider.embed_query() -> query vector
```

所以第三章不是一个新项目，而是同一套项目骨架上的第三次增量实现。

## 进入本章前，必须先回看这些文件

### 来自 Phase 1

- [phase_1_scaffold/app/schemas.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/schemas.py)
- [phase_1_scaffold/app/embeddings/providers.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/embeddings/providers.py)
- [phase_1_scaffold/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/README.md)

你要先确认：

- `SourceChunk` 不是第三章新造出来的
- `app/embeddings/` 这个扩展位不是第三章临时拼出来的

### 来自 Phase 2

- [phase_2_document_processing/app/indexing/index_manager.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/indexing/index_manager.py)
- [phase_2_document_processing/scripts/inspect_chunks.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/scripts/inspect_chunks.py)
- [phase_2_document_processing/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/README.md)

你要先确认：

- 第三章真正的输入不是文件，而是稳定 `SourceChunk`
- `chunk_id / document_id / metadata` 在第三章之前就已经存在

## 当前目录在整门课里的角色

`phase_3_embeddings` 对应的是：

- 第三章：向量化

和前两章合起来看，这一章新增的是：

- Embedding 配置项
- Provider 协议和 Provider 工厂
- 本地可运行的 `local_hash` Provider
- 可选的 `openai_compatible` Provider 接口位
- `SourceChunk -> EmbeddedChunk` 的批量向量化流水线
- 余弦相似度工具和最小相似度实验
- 锁定前两章继承关系的测试

它暂时仍然不负责：

- 真实向量数据库写入
- 检索策略和排序优化
- Rerank
- 完整 RAG 生成
- 评估回归

## 项目结构

```text
phase_3_embeddings/
├── README.md
├── app/
│   ├── config.py
│   ├── schemas.py
│   ├── ingestion/
│   ├── indexing/
│   ├── embeddings/
│   │   ├── providers.py
│   │   ├── vectorizer.py
│   │   └── similarity.py
│   ├── retrievers/
│   ├── prompts/
│   ├── chains/
│   ├── services/
│   ├── evaluation/
│   ├── api/
│   └── observability/
├── data/
├── scripts/
└── tests/
```

### 这个结构应该怎么理解

不要把这份结构理解成“第三章把目录重新整理了一遍”。

这里真正发生的事情是：

- `ingestion/` 和 `indexing/`
  继续沿用前两章，不是第三章主角
- `embeddings/`
  才是第三章真正新增的主角
- `scripts/`
  不只展示向量结果，也展示当前结果如何继承前两章的 chunk 身份
- `tests/`
  不只验证能跑，也验证第三章没有推翻前两章

## 为什么第三章仍然沿用前两章的目录规划

第三章没有另起一套结构，而是直接继承前一章完整代码，原因很直接：

1. 第一章已经把扩展位立住了
2. 第二章已经把输入层做稳了
3. 第三章只应该补当前章节的增量

如果第三章为了展示 Embedding，重新从文本开始写一套脚本，立刻会出现两个问题：

- 学习者会分不清“文档处理”和“向量化”到底谁负责什么
- 第四章接向量数据库前，必须回头重构第三章

### 这一章的目录设计在保护什么

| 目录 | 当前重点 | 为什么现在就要这样分 |
|------|----------|----------------------|
| `app/schemas.py` | 保留 `SourceChunk`，新增 `EmbeddedChunk` | 对象要连续演进，而不是每章换一套 |
| `app/indexing/` | 继续提供稳定 `SourceChunk` | 第三章的输入不能回到原始文件 |
| `app/embeddings/providers.py` | 统一 Provider 差异 | 模型接入不该散落到脚本里 |
| `app/embeddings/vectorizer.py` | 批量向量化流水线 | 下一章向量库会直接复用 |
| `app/embeddings/similarity.py` | 最小相似度计算 | 第三章先验证向量是可比较的 |
| `scripts/` | 放观察入口 | 让你直观看见三章是连续实现 |
| `tests/` | 放新增验收 | 锁定 Phase 3 对 Phase 1/2 的继承关系 |

## 推荐阅读顺序

### 第 1 步：先回看 Phase 1 的对象和扩展位

先读：

- [phase_1_scaffold/app/schemas.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/schemas.py)
- [phase_1_scaffold/app/embeddings/providers.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/embeddings/providers.py)

这一步要解决：

- `SourceChunk` 最早是怎么定义的
- `app/embeddings/` 为什么在第一章就已经留好位置

### 第 2 步：再确认 Phase 2 的稳定 chunk

再读：

- [phase_2_document_processing/app/indexing/index_manager.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/indexing/index_manager.py)
- [phase_2_document_processing/scripts/inspect_chunks.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/scripts/inspect_chunks.py)

这一步要解决：

- 第三章真正吃的输入是什么
- `chunk_id / document_id / metadata` 是在哪一章先稳定下来的

### 第 3 步：再进入 Phase 3 的 Provider 和向量化流水线

再读：

- [app/config.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_3_embeddings/app/config.py)
- [app/embeddings/providers.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_3_embeddings/app/embeddings/providers.py)
- [app/embeddings/vectorizer.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_3_embeddings/app/embeddings/vectorizer.py)
- [app/schemas.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_3_embeddings/app/schemas.py)

这一步要解决：

- 第三章到底补了哪一层
- `EmbeddedChunk` 为什么保留 `SourceChunk`

### 第 4 步：最后看脚本和测试

最后读：

- [scripts/embed_documents.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_3_embeddings/scripts/embed_documents.py)
- [scripts/compare_similarity.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_3_embeddings/scripts/compare_similarity.py)
- [tests/test_embeddings.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_3_embeddings/tests/test_embeddings.py)

这一步要解决：

- 当前输出为什么还保留前两章的 chunk 身份
- 当前测试为什么要验证 Phase 3 复用 Phase 2 的 chunk id 和 metadata

## 推荐命令

如果你想按“三章连读”的节奏学习，建议这样跑：

```bash
cd source/04_rag/labs/phase_1_scaffold
python3 scripts/query_demo.py
```

```bash
cd source/04_rag/labs/phase_2_document_processing
python3 scripts/inspect_chunks.py
```

```bash
cd source/04_rag/labs/phase_3_embeddings
python3 scripts/embed_documents.py
python3 scripts/compare_similarity.py
python3 -m unittest discover -s tests
```

### 这些命令分别在帮你看什么

- `Phase 1 / query_demo.py`
  回顾第一章固定的是最小对象和最小 RAG 形状。
- `Phase 2 / inspect_chunks.py`
  回顾第二章固定的是稳定 `SourceChunk`。
- `Phase 3 / embed_documents.py`
  观察 `SourceChunk` 怎样升级成 `EmbeddedChunk`。
- `Phase 3 / compare_similarity.py`
  观察 query/document 路径和相似度排序。
- `Phase 3 / unittest`
  确认第三章是前两章之上的增量，而不是重写。

## 本章最该观察什么

这一章最值得重点观察的不是“向量数值本身”，而是这四件事：

1. 第三章脚本输出里为什么还能看到 `chunk_id / document_id / metadata`
2. `EmbeddedChunk` 为什么保留 `chunk`
3. 为什么 `providers.py`、`vectorizer.py`、`similarity.py` 要单独分层
4. 为什么第三章现在还不应该把向量数据库也写进来

## 当前完成标准

当前这一章至少应该做到：

- 学员能把前三章串成一条连续工程主线
- 学员能解释为什么第三章只是当前章节增量，不是另一套独立实现
- 学员能看懂 `EmbeddedChunk` 是怎样继承 `SourceChunk` 的
- 学员能运行脚本并读懂“继承了什么，新增了什么”
- 学员能说明第三章为什么能直接作为第四章向量数据库的输入层
