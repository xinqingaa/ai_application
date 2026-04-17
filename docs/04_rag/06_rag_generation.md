# 06. RAG 生成

## 1. 本章目标

- 能把 Retriever 接入 Prompt 和 LLM
- 能构建最小 RAG Chain
- 能返回答案和来源
- 能处理无答案场景

## 2. 本章在 04_rag 中的位置

本章把前五章的检索能力转成真正用户可见的问答能力。

## 3. 学习前提

- 已完成基础 Retriever
- 已理解 Prompt、结构化输出和流式输出

## 4. 本章边界

本章只做固定 RAG Chain，不做 Agent loop、复杂状态机和多工具动态决策。

## 5. 学习顺序

1. 先读 [outline.md](/Users/lrq/work/ai_application/docs/04_rag/outline.md) 中“六、RAG 生成”
2. 再进入 `phase_6_rag_generation`
3. 先实现 context formatter
4. 再实现 Prompt 和 Chain
5. 最后返回 answer + sources

## 6. 核心知识点

- RAG Prompt 结构
- 上下文格式化
- 来源引用
- 拒答策略
- LCEL Chain
- service 层编排

## 7. 对应代码

| 学习内容 | 对应代码 | 当前角色 |
|----------|----------|----------|
| Prompt 模板 | `source/04_rag/labs/phase_6_rag_generation/app/prompts/` | 主示例 |
| RAG Chain | `source/04_rag/labs/phase_6_rag_generation/app/chains/` | 主示例 |
| RAG Service | `source/04_rag/labs/phase_6_rag_generation/app/services/` | 工程入口 |
| 问答脚本 | `source/04_rag/labs/phase_6_rag_generation/scripts/query_demo.py` | 第一运行入口 |

## 8. 实践任务

1. 用检索结果构造上下文
2. 让模型基于上下文回答
3. 返回来源列表
4. 设计一个无答案问题并验证拒答

## 9. 完成标准

- 能跑通最小 RAG 问答链路
- 答案能携带来源
- 能说明哪些问题是检索问题，哪些是生成问题
