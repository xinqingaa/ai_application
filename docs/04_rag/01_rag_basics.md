# 01. RAG 基础概念

## 1. 本章目标

- 能解释 RAG 解决什么问题
- 能区分 RAG、长上下文、微调和直接 Prompt
- 能画出最小 `2-step RAG` 数据流
- 能理解为什么本阶段先做固定 RAG，而不是直接做 Agentic RAG

## 2. 本章在 04_rag 中的位置

本章是 `04_rag` 的入口章节，负责建立 RAG 的基本判断力。

后续文档处理、向量化、检索、生成和评估，都是在本章的数据流基础上展开。

## 3. 学习前提

- 已理解 `03_foundation` 中的 `Document / Retriever / Runnable`
- 已理解 `02_llm` 中的 Prompt、上下文窗口、结构化输出和成本意识

## 4. 本章边界

本章只建立概念和架构判断，不展开真实向量数据库、Rerank、评估系统和 API 服务。

## 5. 学习顺序

1. 先读 [outline.md](/Users/lrq/work/ai_application/docs/04_rag/outline.md) 中“开始前”和“一、RAG 基础概念”
2. 再看本章的代码快照
3. 最后用自己的话画出 RAG 数据流

## 6. 核心知识点

- RAG 的定义
- RAG 解决 LLM 知识不可更新、不可追溯、容易幻觉的问题
- RAG 和微调的边界
- RAG 和长上下文的边界
- `2-step RAG` 的默认主线
- 为什么复杂动态决策要放到 `05_agent`

## 7. 对应代码

| 学习内容 | 对应代码 | 当前角色 |
|----------|----------|----------|
| 项目分层骨架 | `source/04_rag/labs/phase_1_scaffold/` | 主示例 |
| 配置入口 | `source/04_rag/labs/phase_1_scaffold/app/config.py` | 理解项目参数 |
| 数据结构 | `source/04_rag/labs/phase_1_scaffold/app/schemas.py` | 理解 Chunk、RetrievalResult、AnswerResult |
| 占位 RAG 服务 | `source/04_rag/labs/phase_1_scaffold/app/services/rag_service.py` | 理解最终数据流的形状 |

## 8. 实践任务

1. 运行 `phase_1_scaffold` 的占位脚本
2. 阅读 `config.py` 和 `schemas.py`
3. 写出你理解的 RAG 最小链路
4. 说明为什么本章不应该直接实现完整问答系统

## 9. 完成标准

- 能解释 `source/04_rag/labs/phase_1_scaffold/` 每个顶层目录的职责
- 能说明 `SourceChunk / RetrievalResult / AnswerResult` 的作用
- 能判断一个需求是否应该先做 RAG，而不是直接微调或上 Agent
