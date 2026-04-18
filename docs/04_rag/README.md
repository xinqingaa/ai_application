# 04 RAG 学习导航

> `04_rag` 的目标不是“先看一个最终项目”，而是按章节把一个最小 RAG 系统从骨架一步步长出来。

---

## 先记住这条学习主线

```text
先读当前章节文档 -> 再进入对应 phase 代码 -> 跑当前章节命令 -> 理解这一章只解决什么问题 -> 再进入下一章
```

这门课必须按 Phase 顺序学习。

- 不要一开始就打开最终 `rag_lab/`
- 不要跳到后面章节直接看“完整 RAG”
- 不要把还没实现的 Phase 当成已经完成的课程正文

如果你的目标是：

- 一章一章对着文档理解代码
- 知道当前代码到底做到哪里
- 明白下一章是在当前骨架上增加什么能力

那么这份 README 就是 `04_rag` 的第一入口。

## 这门课在整个课程体系里的位置

`04_rag` 位于：

```text
02_llm -> 03_foundation -> 04_rag -> 05_agent -> 06_application
```

它负责把前面学过的：

- LLM 调用
- Prompt
- Structured Output
- Document / Retriever / Runnable

收束成一个真实的知识系统主线：

```text
文档 -> 切分 -> 向量化 -> 向量存储 -> 检索 -> 上下文 -> LLM -> 答案 + 来源
```

## 本阶段的目录怎么理解

### 文档目录

- [outline.md](/Users/linruiqiang/work/ai_application/docs/04_rag/outline.md)
  课程总纲。说明九个 Phase 的目标、边界和推进顺序。
- [01_rag_basics.md](/Users/linruiqiang/work/ai_application/docs/04_rag/01_rag_basics.md) 到 [09_rag_project.md](/Users/linruiqiang/work/ai_application/docs/04_rag/09_rag_project.md)
  每章正文。真正承担“先读文档，再读代码”的学习入口职责。
- [rag_lab_design.md](/Users/linruiqiang/work/ai_application/docs/04_rag/rag_lab_design.md)
  解释为什么课程采用 `labs/phase_*` 和最终 `rag_lab/` 的双层结构。
- [rag_lab_tasks.md](/Users/linruiqiang/work/ai_application/docs/04_rag/rag_lab_tasks.md)
  说明九章对应的落地顺序。

### 代码目录

- [source/04_rag/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/README.md)
  `04_rag` 的代码总入口。
- `source/04_rag/labs/phase_*`
  每一章对应一个代码快照，供你按章阅读。
- `source/04_rag/rag_lab/`
  课程最后的完整项目目录。不是第一阅读入口。

## 课程必须怎么学

推荐固定采用这一套节奏：

1. 先读当前章节文档，明确本章目标、边界和代码入口。
2. 再进入当前 Phase 目录，只看这一章对应的代码。
3. 先跑本章命令，再按文档给出的阅读顺序理解代码。
4. 用自己的话说清楚“这一章新增了什么能力”。
5. 只有当前一章完成后，再进入下一章。

这套节奏的本质是：

- 文档负责建立问题意识和阅读顺序
- 代码负责把抽象变成真实对象和链路
- README 负责把两者连起来

## 九章和代码快照的对应关系

| 章节 | 文档 | 代码目录 | 学习目标 | 当前状态 |
|------|------|----------|----------|----------|
| 1 | [01_rag_basics.md](/Users/linruiqiang/work/ai_application/docs/04_rag/01_rag_basics.md) | `source/04_rag/labs/phase_1_scaffold/` | 理解项目骨架、数据结构和最小 RAG 链路形状 | 已有真实骨架 |
| 2 | [02_document_processing.md](/Users/linruiqiang/work/ai_application/docs/04_rag/02_document_processing.md) | `source/04_rag/labs/phase_2_document_processing/` | 文档加载、切分、metadata、稳定 ID | 已有真实代码快照 |
| 3 | [03_embeddings.md](/Users/linruiqiang/work/ai_application/docs/04_rag/03_embeddings.md) | `source/04_rag/labs/phase_3_embeddings/` | Embedding 接入、query/document 区分与向量表示 | 已有真实代码快照 |
| 4 | [04_vector_databases.md](/Users/linruiqiang/work/ai_application/docs/04_rag/04_vector_databases.md) | `source/04_rag/labs/phase_4_vector_databases/` | 向量存储与检索入口 | 占位 |
| 5 | [05_retrieval_strategies.md](/Users/linruiqiang/work/ai_application/docs/04_rag/05_retrieval_strategies.md) | `source/04_rag/labs/phase_5_retrieval_strategies/` | 基础检索、混合检索、Rerank | 占位 |
| 6 | [06_rag_generation.md](/Users/linruiqiang/work/ai_application/docs/04_rag/06_rag_generation.md) | `source/04_rag/labs/phase_6_rag_generation/` | Prompt、RAG Chain、带来源回答 | 占位 |
| 7 | [07_rag_optimization.md](/Users/linruiqiang/work/ai_application/docs/04_rag/07_rag_optimization.md) | `source/04_rag/labs/phase_7_rag_optimization/` | Golden Set、评估、回归和调优 | 占位 |
| 8 | [08_advanced_rag.md](/Users/linruiqiang/work/ai_application/docs/04_rag/08_advanced_rag.md) | `source/04_rag/labs/phase_8_advanced_rag/` | GraphRAG / Agentic RAG 的边界认知 | 占位 |
| 9 | [09_rag_project.md](/Users/linruiqiang/work/ai_application/docs/04_rag/09_rag_project.md) | `source/04_rag/labs/phase_9_project_integration/` | 综合项目整合 | 占位 |

## 当前真实进度

当前真正可对着代码学习的内容有：

- [01_rag_basics.md](/Users/linruiqiang/work/ai_application/docs/04_rag/01_rag_basics.md)
- [source/04_rag/labs/phase_1_scaffold/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/README.md)
- `phase_1_scaffold` 下的骨架代码
- [02_document_processing.md](/Users/linruiqiang/work/ai_application/docs/04_rag/02_document_processing.md)
- [source/04_rag/labs/phase_2_document_processing/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/README.md)
- `phase_2_document_processing` 下的文档处理代码、样例数据和测试
- [03_embeddings.md](/Users/linruiqiang/work/ai_application/docs/04_rag/03_embeddings.md)
- [source/04_rag/labs/phase_3_embeddings/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_3_embeddings/README.md)
- `phase_3_embeddings` 下的向量化代码、相似度脚本和测试

当前还不能当作“已完成课程内容”的部分：

- `phase_4` 到 `phase_9` 的代码
- 最终 `rag_lab/`

所以这门课当前的正确学习姿势不是“把九章全部看完”，而是：

1. 先完成 Phase 1
2. 再进入 Phase 2，理解文档如何变成稳定 chunk
3. 再进入 Phase 3，理解 chunk 如何变成稳定向量
4. 后续每章都按同样方式推进

## 当前第一阅读入口

如果你现在就要开始 `04_rag`，建议按这个顺序：

1. [outline.md](/Users/linruiqiang/work/ai_application/docs/04_rag/outline.md)
2. [01_rag_basics.md](/Users/linruiqiang/work/ai_application/docs/04_rag/01_rag_basics.md)
3. [source/04_rag/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/README.md)
4. [phase_1_scaffold/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/README.md)

## 这门课的文档规范

后续每一章都应该遵守同一套写法：

1. 先说明本章目标、边界和与前后章节的关系。
2. 明确告诉读者本章应该先看哪些代码文件。
3. 提供真实可运行的命令和建议阅读顺序。
4. 解释代码里关键对象分别负责什么。
5. 给出“重点观察什么”和“建议主动修改什么”。

如果某一章还没有真实代码快照，就不应该伪装成已经可以完整学习的章节。

## 阶段边界

`04_rag` 的默认主线是稳定的 `2-step RAG`：

```text
文档 -> 切分 -> 向量化 -> 向量存储
用户问题 -> 检索 -> 上下文 -> LLM -> 答案 + 来源
```

本阶段必须覆盖：

- 文档加载与切分
- metadata 设计
- Embedding 接入
- 向量存储
- 检索链路
- 引用式回答
- 最小评估集
- 回归和治理意识

本阶段不把这些内容展开成完整实现：

- GraphRAG 完整系统
- Agentic RAG 完整系统
- 企业级知识库后台平台
- 复杂前后端工作台

## 对维护者的推进要求

如果要继续完善 `04_rag`，必须坚持这个顺序：

1. 先实现当前 Phase 的真实代码快照。
2. 再重写当前章节文档。
3. 再重写当前 Phase 的 README。
4. 最后更新课程总入口状态。

不能继续采用“先铺九章文档骨架，再慢慢补代码”的方式。

## 当前完成标准

当前阶段至少应该做到：

- 学员能看懂 `Phase 1` 骨架为什么这样分层
- 学员能看懂 `Phase 2` 为什么先稳定 loader、splitter、metadata 和 ID
- 学员能看懂 `Phase 3` 为什么新增 `embeddings/`，而不是重写输入层
- 学员能顺着文档找到代码入口
- 学员能说清 `SourceChunk / RetrievalResult / AnswerResult` 这些对象为什么先定义
- 学员能理解为什么当前要先做文档处理，再进入 Embedding、向量库和检索
