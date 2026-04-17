# 04 RAG 文档导航

`04_rag` 是 `03_foundation -> 05_agent -> 06_application` 之间的知识系统工程阶段。

本阶段的核心目标不是一次性看完一个完整项目，而是按九章学习路径逐步完成 RAG 系统：

1. 先理解 RAG 为什么存在
2. 再理解文档如何进入系统
3. 再理解向量化和向量数据库
4. 再理解检索策略
5. 再把检索接到生成
6. 再做评估、优化和最终项目整合

本阶段必须坚持一个原则：

- 文档是学习入口
- `labs/phase_*` 是章节代码快照
- `rag_lab` 是最终完整项目

也就是说，你真正学习时不应该先打开完整 `rag_lab`，而应该按章节阅读对应文档，再进入对应的 phase 代码。

## 第一入口

如果你现在要开始学习 `04_rag`，第一阅读入口是：

- [README.md](/Users/lrq/work/ai_application/docs/04_rag/README.md)

如果你要看完整知识范围和总验收面，第二入口是：

- [outline.md](/Users/lrq/work/ai_application/docs/04_rag/outline.md)

如果你要理解项目为什么这样组织，项目入口文档是：

- [rag_lab_design.md](/Users/lrq/work/ai_application/docs/04_rag/rag_lab_design.md)
- [rag_lab_tasks.md](/Users/lrq/work/ai_application/docs/04_rag/rag_lab_tasks.md)

如果你要查看代码入口，进入：

- [source/04_rag/README.md](/Users/lrq/work/ai_application/source/04_rag/README.md)

## 文档结构

本目录分为三类文档。

### 学习主线文档

这些文档对应大纲九章，是你真正学习时逐章阅读的入口：

| 章节 | 文档 | 对应代码 |
|------|------|----------|
| 一、RAG 基础概念 | [01_rag_basics.md](/Users/lrq/work/ai_application/docs/04_rag/01_rag_basics.md) | `source/04_rag/labs/phase_1_scaffold/` |
| 二、文档处理 | [02_document_processing.md](/Users/lrq/work/ai_application/docs/04_rag/02_document_processing.md) | `source/04_rag/labs/phase_2_document_processing/` |
| 三、向量化 | [03_embeddings.md](/Users/lrq/work/ai_application/docs/04_rag/03_embeddings.md) | `source/04_rag/labs/phase_3_embeddings/` |
| 四、向量数据库 | [04_vector_databases.md](/Users/lrq/work/ai_application/docs/04_rag/04_vector_databases.md) | `source/04_rag/labs/phase_4_vector_databases/` |
| 五、检索策略 | [05_retrieval_strategies.md](/Users/lrq/work/ai_application/docs/04_rag/05_retrieval_strategies.md) | `source/04_rag/labs/phase_5_retrieval_strategies/` |
| 六、RAG 生成 | [06_rag_generation.md](/Users/lrq/work/ai_application/docs/04_rag/06_rag_generation.md) | `source/04_rag/labs/phase_6_rag_generation/` |
| 七、RAG 优化 | [07_rag_optimization.md](/Users/lrq/work/ai_application/docs/04_rag/07_rag_optimization.md) | `source/04_rag/labs/phase_7_rag_optimization/` |
| 八、进阶 RAG 方向 | [08_advanced_rag.md](/Users/lrq/work/ai_application/docs/04_rag/08_advanced_rag.md) | `source/04_rag/labs/phase_8_advanced_rag/` |
| 九、综合项目 | [09_rag_project.md](/Users/lrq/work/ai_application/docs/04_rag/09_rag_project.md) | `source/04_rag/labs/phase_9_project_integration/` 和 `source/04_rag/rag_lab/` |

### 总纲与项目文档

这些文档不直接等于某一章正文：

| 文档 | 角色 |
|------|------|
| [outline.md](/Users/lrq/work/ai_application/docs/04_rag/outline.md) | 阶段完整大纲和知识范围 |
| [rag_lab_design.md](/Users/lrq/work/ai_application/docs/04_rag/rag_lab_design.md) | 说明 labs 快照和最终项目的关系 |
| [rag_lab_tasks.md](/Users/lrq/work/ai_application/docs/04_rag/rag_lab_tasks.md) | 说明九章对应九个 Phase 的实施顺序 |

### 持续更新的实施文档

这些文档说明代码当前已经做到哪里：

- [source/04_rag/README.md](/Users/lrq/work/ai_application/source/04_rag/README.md)
- `source/04_rag/labs/*/README.md`
- `source/04_rag/rag_lab/README.md`

## 推荐学习顺序

建议按这个顺序进入：

1. 先读本 README，理解阶段结构
2. 再读 [outline.md](/Users/lrq/work/ai_application/docs/04_rag/outline.md)，理解全景
3. 再按九章顺序读 `01 -> 09`
4. 每读一章，只进入该章对应的 `labs/phase_*` 代码
5. 学完第九章后，再看最终完整项目 `source/04_rag/rag_lab/`

## 当前状态

当前已经完成：

- 阶段入口文档
- 九章正文文档骨架
- 项目设计与任务文档
- `phase_1_scaffold` 代码快照
- 最终 `rag_lab` 占位入口

当前还没有完成：

- `phase_2_document_processing` 及后续真实实现
- 最终完整 `rag_lab`

## 阶段边界

本阶段默认主线是稳定的 `2-step RAG`：

```plain
文档 -> 切分 -> 向量化 -> 向量数据库
用户问题 -> 检索 -> 上下文 -> LLM -> 答案 + 来源
```

主线内必须覆盖：

- 文档加载与切分
- metadata 设计
- Embedding 接入
- 向量存储
- 基础检索
- 引用式回答
- Golden Set 与离线评估
- 检索优化与基础治理

本阶段只做概念认知，不做完整实现的内容：

- GraphRAG 完整系统
- Agentic RAG 完整系统
- 复杂 Agent 编排
- 企业级知识库后台平台

## 本阶段完成标准

### 理解层

- 能解释什么时候该用长上下文、固定 RAG、混合检索和 Agentic RAG
- 能说明文档处理、切分、Embedding、向量存储、Retriever、Prompt、评估之间的关系
- 能说明为什么 RAG 要先建立评估集，而不是只看一次回答效果

### 操作层

- 能按九章文档顺序阅读和运行对应 phase 代码
- 能从 `phase_1_scaffold` 逐步推进到 `phase_9_project_integration`
- 能理解 `labs/phase_*` 和最终 `rag_lab` 的区别

### 项目层

- 能跑通一个带来源引用的最小 RAG 问答链路
- 能建立并复用最小 Golden Set
- 能在改动切分、检索或 Prompt 后做一次固定回归
