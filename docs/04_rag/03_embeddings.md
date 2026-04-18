# 03. 向量化

> 本节目标：理解第三章为什么必须建立在前两章之上，掌握 `SourceChunk -> EmbeddedChunk` 这层增量能力，并理解为什么 query 和 document 的向量化入口要分开。

---

## 1. 概述

### 学习目标

- 能说明第一章、第二章、第三章在整条 RAG 主线里分别解决什么问题
- 理解为什么第三章不是“另一套输入管道”，而是 `SourceChunk -> EmbeddedChunk` 的增量
- 理解 `EmbeddingProvider` 在系统里的职责
- 理解为什么 `embed_query()` 和 `embed_documents()` 要保留为两个入口
- 能运行第三章脚本，并看出向量结果如何继承前两章的 `chunk_id / document_id / metadata`
- 能说明第三章为什么只做到向量化，而不提前混进向量数据库和完整检索

### 预计学习时间

- 向量化原理与对象关系：1 小时
- query/document 区分：45 分钟
- 第三章代码快照阅读：1-1.5 小时

### 本节在 AI 应用中的重要性

| 场景 | 相关知识 |
|------|---------|
| 语义检索 | 文本向量化、相似度计算 |
| 知识库索引 | chunk 变向量、provider 抽象 |
| 检索排序 | query/document 表征差异 |
| 模型替换 | provider 配置、维度和模型信息 |
| 后续向量库接入 | `EmbeddedChunk[]` 作为标准输入 |

> **第三章的重点不是“生成几个向量”，而是让系统第一次拥有可比较、可存储、可检索的语义表示层。**

### 本章与前后章节的关系

第一章解决的是：

1. 系统为什么这样分层
2. 核心对象为什么先定义

第二章解决的是：

1. 原始文件怎样变成稳定 `SourceChunk[]`
2. metadata 和 stable id 怎样固定下来

第三章接着解决的是：

1. `SourceChunk[]` 怎样批量变成 `EmbeddedChunk[]`
2. query 和 document 怎样进入两条不同的向量化路径

第四章会继续建立在这里之上：

1. 把 `EmbeddedChunk[]` 写入向量存储
2. 基于向量做最小检索

### 本章的学习边界

本章重点解决：

1. 向量化必须建立在前两章之上的原因
2. `EmbeddingProvider` 和向量化流水线
3. `SourceChunk -> EmbeddedChunk`
4. query/document 两条向量化入口
5. 最小相似度比较

本章不展开：

- 真实向量数据库写入
- Top-K、MMR、Threshold 等检索策略
- Rerank 和混合检索
- LLM 生成答案
- Embedding 模型大规模横评
- 本地推理部署和 GPU 优化

### 当前代码快照

本章对应的代码快照是：

- [phase_3_embeddings/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_3_embeddings/README.md)
- [scripts/embed_documents.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_3_embeddings/scripts/embed_documents.py)
- [scripts/compare_similarity.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_3_embeddings/scripts/compare_similarity.py)

---

## 2. 第三章到底接在什么后面 📌

### 2.1 第一章先立下了什么

第一章最重要的贡献不是“把 RAG 做出来”，而是先立住了：

1. 项目分层
2. `SourceChunk / RetrievalResult / AnswerResult`
3. `embeddings/`、`vectorstores/`、`retrievers/` 这些扩展位

所以第三章今天能直接在 `app/embeddings/` 里继续长，不是突然多出来的设计，而是第一章一开始就预留好的位置。

### 2.2 第二章真正交付了什么

第二章真正交付的是：

```text
文件
-> discover_documents()
-> load_document()
-> split_text()
-> build_metadata()
-> stable ids
-> SourceChunk[]
```

第三章真正吃的输入不是文件，而是：

```text
稳定的 chunk 列表
+ 每个 chunk 的来源信息
+ 可重复定位的 stable id
```

如果这一步没有先做稳，第三章就会立刻遇到：

- 相同文档每次 embedding 输入不一致
- 后续向量写入无法知道 chunk 身份
- 调试和删除时没有稳定锚点

### 2.3 第三章新增的到底是什么

第三章新增的不是另一套 loader，也不是另一套索引脚本。

第三章只新增这一层：

```text
SourceChunk[]
-> embed_documents()
-> EmbeddedChunk[]
```

这就是第三章最重要的判断：

> 第三章是在第二章稳定产出的 `SourceChunk` 外面，再包一层向量表示，而不是推翻前两章。

---

## 3. 向量化到底在做什么 📌

### 3.1 为什么要把文本变成向量

模型和程序都无法直接对“语义相近”做传统字符串比较。

例如：

- “退款规则是什么？”
- “如何申请退费？”

它们字面上并不完全一样，但语义很接近。

向量化的目标就是把文本映射成一个数值空间里的点，让：

- 语义接近的文本距离更近
- 语义无关的文本距离更远

这样后续系统才能基于相似度去检索相关 chunk。

### 3.2 为什么 `EmbeddedChunk` 不是替代 `SourceChunk`

第三章的对象演进应该这样理解：

| 阶段 | 核心对象 | 作用 |
|------|----------|------|
| 第一章 | `SourceChunk`、`RetrievalResult`、`AnswerResult` | 立住对象契约和系统边界 |
| 第二章 | `SourceChunk` | 让文件稳定产出标准 chunk |
| 第三章 | `EmbeddedChunk` | 在 `SourceChunk` 外再加向量、provider、model 信息 |

关键点在于：

- `EmbeddedChunk` 不是替代 `SourceChunk`
- `EmbeddedChunk` 是把 `SourceChunk` 保留下来，再额外加上向量负载

这能确保后续向量库、检索、引用和调试仍然能拿到原始 chunk 身份。

### 3.3 为什么 `app/embeddings/` 必须单独成层

这里必须分清几层职责：

| 层 | 解决什么问题 | 不解决什么问题 |
|----|--------------|----------------|
| `ingestion` | 文件如何进入系统 | 不负责生成向量 |
| `indexing` | 标准 `SourceChunk` 如何产生 | 不负责生成向量 |
| `embeddings` | `SourceChunk` 如何变成向量 | 不负责写入向量存储 |
| `vectorstores` | 向量如何存和查 | 不负责重新切分文档 |

很多人在做 RAG 时会把这些步骤全塞进一个“大索引脚本”，这样短期看起来省事，长期会很难维护。

第三章单独成层的意义就是：

> 让“文档处理”“向量化”“向量存储”成为可独立替换、可独立调试的三个层次。

---

## 4. 为什么 query 和 document 要分开向量化 📌

### 4.1 两者在系统中的角色不同

document embedding 的目标是：

- 表示知识库里的静态内容
- 为后续索引和检索提供向量基础

query embedding 的目标是：

- 表示用户当前的问题
- 在同一个向量空间里去匹配最相关的 document vectors

虽然它们都叫 embedding，但在很多模型和接口设计里，这两者并不一定完全等价。

### 4.2 为什么保留两个入口更稳妥

保留 `embed_documents()` 和 `embed_query()` 两个入口的好处是：

1. 接口语义清晰
2. 未来更换 provider 时更容易适配
3. 便于区分离线索引和在线检索的调用路径
4. 便于在不同模型或不同参数下做实验

即使当前 provider 内部实现很接近，这两个入口也值得保留。

### 4.3 为什么第三章先用本地 provider

第三章当前最重要的目标是：

1. 看懂接口
2. 看懂对象
3. 看懂数据流

不是一上来就被 API Key、网络、计费和 provider 差异打断。

所以当前代码快照默认先用本地 `local_hash` provider，保留 `openai_compatible` 接口位。

这和 `02_llm` 的思路是一致的：

> 先把平台差异收敛到 provider 和配置层，再在业务链路上建立稳定心智模型。

---

## 5. 第三章应该怎么学

### 5.1 推荐顺序

建议按这个顺序进入：

1. 先回看 [phase_2_document_processing/app/indexing/index_manager.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/indexing/index_manager.py)
2. 再看 [phase_3_embeddings/app/config.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_3_embeddings/app/config.py)
3. 再看 [app/embeddings/providers.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_3_embeddings/app/embeddings/providers.py)
4. 再看 [app/embeddings/vectorizer.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_3_embeddings/app/embeddings/vectorizer.py)
5. 最后看 [app/embeddings/similarity.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_3_embeddings/app/embeddings/similarity.py)

### 5.2 建议先跑的命令

```bash
cd source/04_rag/labs/phase_3_embeddings

python scripts/embed_documents.py
python scripts/compare_similarity.py
python -m unittest discover -s tests
```

这些命令最该帮你建立的直觉是：

1. 向量结果仍然保留 `chunk_id / document_id / metadata`
2. query 和 document 走的是两条语义上分开的入口
3. 相关文本的相似度应该更高
4. 第三章交付的是向量层，不是完整检索系统

---

## 综合案例：为 FAQ 知识库设计向量化层

```python
# 你现在已经有稳定的 SourceChunk[]：
#
# 请回答：
# 1. 为什么第三章不应该重新从文件开始做 embedding？
# 2. EmbeddedChunk 至少应该比 SourceChunk 多哪些信息？
# 3. 为什么 embed_query() 和 embed_documents() 不应合并成一个模糊入口？
# 4. 为什么第三章适合先用本地 provider 建立直觉，而不是一开始就绑定真实平台？
```

当你能清楚回答这 4 个问题时，第三章的主线就真正建立起来了。

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
python scripts/query_demo.py
```

这一组命令的意义是：

- 先回想第一章真正固定的是最小对象和最小服务链路
- 提醒自己第三章不是突然出现的新系统

### 第 2 组：回顾第二章的稳定 chunk

```bash
cd source/04_rag/labs/phase_2_document_processing
python scripts/inspect_chunks.py
```

这一组命令的意义是：

- 先确认第二章真正交付的是稳定 `SourceChunk`
- 看清 `chunk_id / document_id / metadata` 在第三章之前就已经存在

### 第 3 组：进入第三章的向量化增量

```bash
cd source/04_rag/labs/phase_3_embeddings
python scripts/embed_documents.py
python scripts/compare_similarity.py
python -m unittest discover -s tests
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
