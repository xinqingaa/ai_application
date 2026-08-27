# AI 应用课程

本课程只围绕一个产品展开：把需求评审助手从固定 RAG 应用演进为以 Agentic RAG 为知识基础的多 Agent 协作系统。

## 从哪里开始

按 [标准学习路径](learning-path.md) 学习。只有这份文件维护课程序号和阅读顺序；目录、文件名、知识地图、项目篇和代码结构都不编号，也不能用来推断先后。

遇到不同问题时回到对应真源：

| 想确认什么 | 去哪里 |
| --- | --- |
| 下一步学什么 | [标准学习路径](learning-path.md) |
| 某项知识是否在范围内、依赖什么、落在哪里 | [知识地图](knowledge-map.md) |
| 产品最终必须做到什么 | [SPEC.md](../SPEC.md) |
| 通用能力和产品代码怎样分工 | [PLAN.md](../PLAN.md) |
| 当前阶段怎样综合实践和验收 | [第一阶段项目篇](project/stage-1-rag-application/rag-review-assistant.md)或[第二阶段项目篇](project/stage-2-agent-system/agent-review-assistant.md) |

学习者不需要先读完 SPEC 和 PLAN；项目篇会把当前阶段需要理解和完成的部分转化为综合任务，但不会复制这些真源。

## 完整学习主线

课程始终演进同一个需求评审助手：

```text
模型调用与结构化输出
→ 固定 RAG、可信证据与产品交付
→ Agent Harness、Tool Runtime 与权限治理
→ MCP、Search、Browser、File 与 Code Tool
→ Agentic RAG 与 Agent Skills
→ Conversation、Run State、短期与长期记忆、事件和运行界面
→ Deep Research
→ Multi-Agent 与 A2A
→ 必要 Workflow
→ Trace、Regression、Human Eval 与 Feedback
```

这条链表示能力怎样在同一产品中逐步闭环，不是另一套阅读顺序。具体先后仍只看学习路径。

## 两个阶段

| 阶段 | 交付目标 |
| --- | --- |
| 第一阶段：RAG 应用基础 | 固定 RAG、可信证据边界、Review API、Web 工作台和最小质量基线 |
| 第二阶段：Agent、Tools 与 Multi-Agent | Agent Harness、受治理工具、状态与记忆、研究、协作、恢复和统一质量闭环 |

两个阶段沿同一产品连续演进，不建立阶段内版本轴。

## 四类课程文档

| 类型 | 目录 | 主要回答 |
| --- | --- | --- |
| 概念篇 | `concepts/` | 这是什么、为什么需要、与相邻概念怎样区分 |
| 机制篇 | `mechanisms/` | 数据如何流动、机制为何成立、边界和失败怎样出现 |
| 实验篇 | `labs/` | 如何准备、运行、调试、观察日志和阅读对应实现 |
| 项目篇 | `project/` | 如何把多个能力组合进同一产品并完成阶段验收 |

机制篇是学习正文，但不承担源码逐行讲解、安装命令和运行手册。实验篇与机制篇配套：前者让机制可观察，后者解释观察结果为什么出现。项目篇引用产品要求和代码入口，不复制产品规格或产品 README。

## 代码入口

| 目录 | 职责 |
| --- | --- |
| `source/packages/` | 可复用能力的唯一实现 |
| `source/demos/` | 机制观察、对照和稳定失败复现 |
| `source/apps/review_assistant/` | 唯一可运行产品 |

课程不在 `course/` 复制实现，也不在 demo 中维护第二份产品。产品安装、配置、启动、测试和部署见 [需求评审助手 README](../source/apps/review_assistant/README.md)。

## 学习规则

- Python、HTTP、JSON、配置、异步和 PostgreSQL 是必备基础；已掌握时可以通过路径中的检查，不必为形式重学。
- LLM、RAG、Agent 和 Eval 主路径使用真实模型或真实外部服务；失败必须显式暴露。
- Mock 只用于单元测试、离线排查、稳定失败复现或明确对照，不能证明真实效果。
- 每节先解决一个主问题。若同时需要学习多个独立生命周期、协议角色或实现系统，应继续拆节。
- 完整能力链以本页总图为导航，以学习路径为顺序；每增加一层复杂度，都保留与之相称的固定样例、运行记录和失败证据。
