# 07. RAG 优化

## 1. 本章目标

- 能建立最小 Golden Set
- 能评估检索命中率和来源质量
- 能对比不同切分、检索和 Prompt 配置
- 能记录坏案例并驱动下一轮优化

## 2. 本章在 04_rag 中的位置

本章把 RAG 从“能跑 Demo”推进到“能判断是否变好”。

## 3. 学习前提

- 已完成最小 RAG Chain
- 已能拿到 answer 和 sources

## 4. 本章边界

本章不建设完整 LLMOps 平台，只做学习阶段可重复运行的最小评估闭环。

## 5. 学习顺序

1. 先读 [outline.md](/Users/lrq/work/ai_application/docs/04_rag/outline.md) 中“开始前”和“七、RAG 优化”
2. 再进入 `phase_7_rag_optimization`
3. 先建立 Golden Set
4. 再跑检索评估
5. 最后做一轮配置对比

## 6. 核心知识点

- Golden Set
- 检索召回
- MRR
- 来源命中
- 答案准确性
- 配置对比
- 坏案例回流

## 7. 对应代码

| 学习内容 | 对应代码 | 当前角色 |
|----------|----------|----------|
| Golden Set | `source/04_rag/labs/phase_7_rag_optimization/evals/` | 评估数据 |
| 评估器 | `source/04_rag/labs/phase_7_rag_optimization/app/evaluation/` | 主示例 |
| 配置对比 | `source/04_rag/labs/phase_7_rag_optimization/scripts/evaluate.py` | 第一运行入口 |
| 坏案例记录 | `source/04_rag/labs/phase_7_rag_optimization/evals/bad_cases.md` | 优化依据 |

## 8. 实践任务

1. 写 20 条以内的最小 Golden Set
2. 跑一次基础检索评估
3. 调整 `chunk_size` 或 `top_k`
4. 对比前后结果并记录坏案例

## 9. 完成标准

- 能用固定样本重复评估
- 能说明某次优化是否真的变好
- 能把坏案例转成下一轮工程改动依据
