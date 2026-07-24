# AI 应用课程

这里是课程的唯一阅读入口。

课程围绕唯一项目“需求评审助手”展开，按 V0–V6 逐步从固定 RAG 演进为可信单 Agent、可控 Workflow 和多 Agent 评审系统。LLM、RAG、Agent、Eval 和 AI Native 是能力域，不是必须依次毕业的课程。

长期目标与版本定义见 [strategy.md](../docs/strategy.md)，学习和工程规则见 [learning-guide.md](../docs/learning-guide.md)。

## 从哪里开始

当前主线从阶段一 V0 开始：

1. 阅读 [V0 固定 RAG 基线](project/stage-1-single-agent-rag/v0-fixed-rag.md)。
2. 根据项目篇列出的知识 ID，到 [集中知识清单](knowledge-map.md) 查找概念、机制、代码和前置。
3. 阅读必要的概念篇和机制篇。
4. 按项目篇指向的 package、demo 和产品入口运行真实链路。
5. 完成失败题、需求变更、评估和版本验收。

标准路径：

```text
项目篇
→ 必要概念
→ 必要机制
→ package / demo
→ review_assistant 产品
→ 真实运行
→ bad case 与回归
→ 版本验收
```

## 两个阶段

### 阶段一：可信 RAG + 单 Agent

| 版本 | 结果 | 项目篇 |
| --- | --- | --- |
| V0 | 固定 RAG 基线 | [开始学习](project/stage-1-single-agent-rag/v0-fixed-rag.md) |
| V1 | 结构化评审、Sources、Citation、Refusal | 对应版本开始时创建 |
| V2 | Golden Set、RAG Eval、bad case、feedback | 对应版本开始时创建 |
| V3 | Query Rewrite、Source Routing、补检索和追问的单 Agent | 对应版本开始时创建 |

### 阶段二：Workflow + Multi-Agent

| 版本 | 结果 | 项目篇 |
| --- | --- | --- |
| V4 | 显式 Workflow、状态、分支、人工审核和恢复 | 对应版本开始时创建 |
| V5 | 多 Agent 分工、协作、汇总和冲突处理 | 对应版本开始时创建 |
| V6 | AI Native 工作台、质量面板、部署和作品化 | 对应版本开始时创建 |

没有真实项目内容时不预建空版本文档或目录。

## 三类文档怎样读

### 概念篇

回答“是什么、为什么需要、与相近概念有什么区别、边界在哪里”。

概念篇用于建立判断，不要求每篇都有代码。

### 机制篇

回答“为什么有效、数据如何变化、怎样实验、失败时先查哪里”。

机制篇按能力域组织，但只读当前项目版本需要的部分。

### 项目篇

回答“这一版要完成什么业务结果、需要作出哪些设计选择、如何运行和验收”。

V0–V6 的强顺序只在项目篇中体现。

## 集中查看知识路线

[knowledge-map.md](knowledge-map.md) 提供两种入口：

- 按 V0–V6 查看项目学习路线。
- 按 LLM、RAG、Agent、Workflow、Eval、AI Native 和工程基础查看完整知识路线。

知识清单是能力书架，不替代项目篇的强顺序。

## 文档、代码与产品

```text
course/concepts/      概念篇
course/mechanisms/    机制篇
course/project/       项目篇教材
source/packages/      通用能力唯一实现
source/demos/         机制实验与失败复现
source/apps/          学习期组合实验
review_assistant/     可运行产品真源
```

项目篇不复制产品运行手册；产品 README 不复制课程原理。

## Python 基础

`python_base/` 是已完成的 Python 基础练习，保留原有结构，不参与当前课程重组，也不是 V0–V6 的前置门禁。

## 真实调用

LLM、RAG、Agent 和 Eval 主路径调用真实模型或真实外部服务。缺少 key、限流、超时和模型能力不支持应清晰失败，不静默返回 Mock 结果。
