# rag_lab 设计说明

> 本节目标：说明 `04_rag` 为什么采用“九章文档 + 独立章节代码 + 最终 rag_lab 项目”的结构，让学习入口、章节代码和最终项目之间的关系保持清晰。

---

## 1. 概述

`04_rag` 不应该一开始就给学习者一个完整 `rag_lab` 项目。

完整项目适合作为最终参考，但不适合作为第一学习入口。对学习者来说，更清晰的方式是：

1. 每章先读对应文档
2. 已经落地的章节，再进入对应代码目录
3. 学完第九章后，再看最终完整 `rag_lab`

所以当前结构是：

```plain
docs/04_rag/九章正文
source/04_rag/01-06 独立章节代码
source/04_rag/rag_lab/最终完整项目
```

第七章到第九章当前只有正文文档，代码目录后续再补。

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

## 3. 当前目录设计

推荐结构如下：

```plain
source/04_rag/
  README.md
  01_rag_basics/
  02_document_processing/
  03_embeddings/
  04_vector_databases/
  05_retrieval_strategies/
  06_rag_generation/
  rag_lab/
```

### 3.1 独立章节目录的职责

`01_rag_basics/` 到 `06_rag_generation/` 负责：

- 对应章节正文
- 让每一章都有明确、独立的运行入口
- 只展开当前章节真正需要的对象和脚本
- 避免把最终项目结构过早压到学习入口上

独立章节目录的首要目标是教学清晰，而不是提前做完整项目抽象。

### 3.2 rag_lab 的职责

`rag_lab/` 是最终完整项目。

它负责：

- 汇总第九章后的完整实现
- 作为 `04_rag` 阶段的最终参考项目
- 为 `06_application` 迁移知识库能力提供基础

`rag_lab/` 不作为初学入口。

## 4. 九章文档和代码映射

| 章节 | 文档 | 当前代码入口 | 主要学习目标 |
|------|------|--------------|--------------|
| 1 | `01_rag_basics.md` | `source/04_rag/01_rag_basics/` | 理解 RAG 主数据流和方案边界 |
| 2 | `02_document_processing.md` | `source/04_rag/02_document_processing/` | 文档加载、切分、metadata、ID |
| 3 | `03_embeddings.md` | `source/04_rag/03_embeddings/` | Embedding 接口和相似度 |
| 4 | `04_vector_databases.md` | `source/04_rag/04_vector_databases/` | 向量存储、查询、删除 |
| 5 | `05_retrieval_strategies.md` | `source/04_rag/05_retrieval_strategies/` | Retriever、Top-K、过滤、增强策略 |
| 6 | `06_rag_generation.md` | `source/04_rag/06_rag_generation/` | Prompt、Chain、答案和来源 |
| 7 | `07_rag_optimization.md` | 暂无代码目录 | Golden Set、评估、坏案例 |
| 8 | `08_advanced_rag.md` | 暂无代码目录 | GraphRAG、Agentic RAG 边界认知 |
| 9 | `09_rag_project.md` | `source/04_rag/rag_lab/` 作为最终收口目标 | 项目整合和最终收口 |

## 5. 已落地章节目录的设计原则

每个已落地章节目录都应满足：

1. 有自己的 README
2. 能说明对应哪一章文档
3. 能说明当前阶段新增了什么
4. 能说明当前还没有实现什么
5. 尽量可以独立运行当前阶段的脚本或测试

每个已落地章节目录不要求：

1. 提前实现后面章节能力
2. 为了复用而牺牲当前教学清晰度
3. 直接变成最终生产项目

对于第七章到第九章：

1. 可以先有正文文档
2. 可以等需求明确后再补独立代码目录
3. 不需要为了占位而额外保留失效目录

## 6. 最终项目生成规则

最终 `rag_lab` 应在第九章后形成。

它可以来自：

1. 对前面独立章节实现的清理合并
2. 对 README、运行命令、测试和评估入口的最终收口
3. 对项目边界和可运行方式的统一整理

最终项目必须保留清楚边界：

- 它是参考实现
- 它不是第一学习入口
- 它不包含完整 Agent 工作流
- 它不替代 `06_application`

## 7. 完成标准

- 九章文档都存在并保持可读
- 第一章到第六章有稳定的独立代码目录
- 第七章到第九章的“代码尚未落地”状态在文档里被清楚说明
- `source/04_rag/README.md` 能解释独立章节目录和 `rag_lab` 的关系
- 最终 `rag_lab` 只在第九章后作为完整项目出现
