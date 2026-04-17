# 08. 进阶 RAG 方向

## 1. 本章目标

- 能理解 GraphRAG 的适用场景
- 能理解 Agentic RAG 的升级条件
- 能判断什么时候不该引入复杂方案
- 能把复杂方案和固定 RAG 主线区分开

## 2. 本章在 04_rag 中的位置

本章是进阶认知章节，负责建立边界判断，不负责完整实现复杂 RAG 系统。

## 3. 学习前提

- 已完成固定 RAG 链路
- 已完成最小评估闭环

## 4. 本章边界

本章只做概念认知和方案判断。

GraphRAG、Agentic RAG 的完整实现分别属于更复杂的知识图谱工程或 `05_agent` 阶段。

## 5. 学习顺序

1. 先读 [outline.md](/Users/lrq/work/ai_application/docs/04_rag/outline.md) 中“八、进阶 RAG 方向”
2. 再进入 `phase_8_advanced_rag`
3. 只看概念示例和场景判断
4. 不把本章当成必须实现的主线功能

## 6. 核心知识点

- GraphRAG
- Agentic RAG
- 多跳问题
- 动态检索决策
- 知识源路由
- 固定 RAG 的升级信号

## 7. 对应代码

| 学习内容 | 对应代码 | 当前角色 |
|----------|----------|----------|
| 场景判断 | `source/04_rag/labs/phase_8_advanced_rag/README.md` | 概念入口 |
| 升级边界 | `source/04_rag/labs/phase_8_advanced_rag/examples/` | 可选示例 |
| Agentic RAG 说明 | `docs/05_agent/outline.md` | 后续阶段入口 |

## 8. 实践任务

1. 判断三个场景是否需要 GraphRAG
2. 判断三个场景是否需要 Agentic RAG
3. 写出固定 RAG 不够用的信号
4. 写出本阶段不实现复杂 Agentic RAG 的理由

## 9. 完成标准

- 能说明 GraphRAG 和传统 RAG 的区别
- 能说明 Agentic RAG 和固定 RAG 的区别
- 能避免因为“高级”而过早引入复杂方案
