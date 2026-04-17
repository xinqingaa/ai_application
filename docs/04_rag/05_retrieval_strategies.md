# 05. 检索策略

## 1. 本章目标

- 能实现基础 similarity 检索
- 能理解 `top_k / score_threshold / mmr`
- 能判断什么时候需要混合检索和 Rerank
- 能用最小样例评估召回质量

## 2. 本章在 04_rag 中的位置

本章把向量数据库能力封装成可替换 Retriever，是 RAG 效果优化的核心入口。

## 3. 学习前提

- 已完成向量数据库写入和查询
- 已能观察 Top-K 检索结果

## 4. 本章边界

本章会引入增强检索意识，但不把所有高级 Retriever 都实现一遍。

## 5. 学习顺序

1. 先读 [outline.md](/Users/lrq/work/ai_application/docs/04_rag/outline.md) 中“五、检索策略”
2. 再进入 `phase_5_retrieval_strategies`
3. 先实现 similarity
4. 再观察 MMR、阈值过滤和 metadata filter
5. 最后基于坏案例判断是否需要增强策略

## 6. 核心知识点

- Retriever 的职责
- similarity 检索
- MMR 检索
- metadata filter
- 混合检索
- Rerank
- 查询变换和 HyDE 的适用边界

## 7. 对应代码

| 学习内容 | 对应代码 | 当前角色 |
|----------|----------|----------|
| Retriever 封装 | `source/04_rag/labs/phase_5_retrieval_strategies/app/retrievers/` | 主示例 |
| 检索脚本 | `source/04_rag/labs/phase_5_retrieval_strategies/scripts/retrieve_demo.py` | 第一运行入口 |
| 检索参数对比 | `source/04_rag/labs/phase_5_retrieval_strategies/scripts/compare_retrieval.py` | 对照实验 |
| 坏案例记录 | `source/04_rag/labs/phase_5_retrieval_strategies/evals/bad_cases.md` | 评估准备 |

## 8. 实践任务

1. 对同一问题比较不同 `top_k`
2. 对同一知识库比较 similarity 和 MMR
3. 使用 metadata filter 限定文档范围
4. 记录至少三个检索失败样例

## 9. 完成标准

- 能解释检索效果差时应先看哪些因素
- 能封装一个可替换 Retriever
- 能为第六章 RAG Chain 提供稳定上下文
