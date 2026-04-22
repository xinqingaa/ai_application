# rag_lab 设计说明

> 本节目标：说明 `04_rag` 为什么采用“九章文档 + labs 代码快照 + 最终 rag_lab 项目”的结构，让学习入口、阶段代码和最终项目之间的关系保持清晰

---

## 1. 概述

`04_rag` 不应该一开始就给学习者一个完整 `rag_lab` 项目。

完整项目适合作为最终参考，但不适合作为第一学习入口。对学习者来说，更清晰的方式是：

1. 每章先读对应文档
2. 每章只看对应的 phase 代码快照
3. 学完第九章后，再看最终完整 `rag_lab`

所以本阶段采用三层结构：

```plain
docs/04_rag/九章正文
source/04_rag/labs/phase_* 学习快照
source/04_rag/rag_lab/最终完整项目
```

## 2. 为什么不一次性实现完整 rag_lab

如果一开始就实现完整 `rag_lab`，会出现三个问题：

1. 学习入口不清晰，不知道从哪个文件开始看
2. 每个模块都已经存在，难以感受系统是如何逐步长出来的
3. 文档和代码容易脱节，最后变成“看项目猜课程”

`04_rag` 的目标不是让你背一个完整目录，而是让你理解：

- 为什么需要这一层
- 这一层解决什么问题
- 这一层什么时候才应该出现

所以代码必须跟着九章文档逐步展开。

## 3. 整体目录设计

推荐结构如下：

```plain
source/04_rag/
  README.md
  labs/
    phase_1_scaffold/
    phase_2_document_processing/
    phase_3_embeddings/
    phase_4_vector_databases/
    phase_5_retrieval_strategies/
    phase_6_rag_generation/
    phase_7_rag_optimization/
    phase_8_advanced_rag/
    phase_9_project_integration/
  rag_lab/
```

### 3.1 labs 的职责

`labs/` 是学习快照目录。

它负责：

- 对应九章正文
- 保留每章学习时的代码状态
- 让每个阶段都有明确入口
- 方便横向对比相邻阶段差异

`labs/` 不追求消除代码重复，因为它的首要目标是教学清晰。

### 3.2 rag_lab 的职责

`rag_lab/` 是最终完整项目。

它负责：

- 汇总第九章后的完整实现
- 作为 `04_rag` 阶段的最终参考项目
- 为 `06_application` 迁移知识库能力提供基础

`rag_lab/` 不作为初学入口。

## 4. 九章文档和代码快照映射

| 章节 | 文档 | 代码快照 | 主要学习目标 |
|------|------|----------|--------------|
| 1 | `01_rag_basics.md` | `labs/phase_1_scaffold/` | 理解 RAG 主数据流和项目骨架 |
| 2 | `02_document_processing.md` | `labs/phase_2_document_processing/` | 文档加载、切分、metadata、ID |
| 3 | `03_embeddings.md` | `labs/phase_3_embeddings/` | Embedding 接口和相似度 |
| 4 | `04_vector_databases.md` | `labs/phase_4_vector_databases/` | 向量存储、查询、删除 |
| 5 | `05_retrieval_strategies.md` | `labs/phase_5_retrieval_strategies/` | Retriever、Top-K、过滤、增强策略 |
| 6 | `06_rag_generation.md` | `labs/phase_6_rag_generation/` | Prompt、Chain、答案和来源 |
| 7 | `07_rag_optimization.md` | `labs/phase_7_rag_optimization/` | Golden Set、评估、坏案例 |
| 8 | `08_advanced_rag.md` | `labs/phase_8_advanced_rag/` | GraphRAG、Agentic RAG 边界认知 |
| 9 | `09_rag_project.md` | `labs/phase_9_project_integration/` | 项目整合和最终收口 |

## 5. 每个 phase 的设计原则

每个 `phase_*` 都应满足：

1. 有自己的 README
2. 能说明对应哪一章文档
3. 能说明当前阶段新增了什么
4. 能说明当前还没有实现什么
5. 尽量可以独立运行当前阶段的脚本或测试

每个 `phase_*` 不要求：

1. 消除和前一阶段的重复代码
2. 提前实现后面章节能力
3. 成为最终生产项目

## 6. 最终项目生成规则

最终 `rag_lab` 应在第九章后形成。

它可以来自：

1. `phase_9_project_integration` 的整理版
2. 对前面 phase 代码的清理合并
3. 对 README、运行命令、测试和评估入口的最终收口

最终项目必须保留清楚边界：

- 它是参考实现
- 它不是第一学习入口
- 它不包含完整 Agent 工作流
- 它不替代 `06_application`

## 7. 完成标准

- 九章文档都有对应代码快照
- 每个 phase 的 README 都能说明学习入口和当前边界
- `source/04_rag/README.md` 能解释 labs 和 rag_lab 的关系
- 最终 `rag_lab` 只在第九章后作为完整项目出现
