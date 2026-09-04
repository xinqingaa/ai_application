# AI 应用课程

本课程只围绕一个产品展开：把需求评审助手——一个以需求基线为核心的需求定义、评审与交付工作台——从固定 RAG 应用演进为以 Agentic RAG 为知识基础、在用户裁决下推动需求收敛与变更影响分析的多 Agent 协作系统。

## 从哪里开始

按 [标准学习路径](learning-path.md) 学习。只有这份文件维护课程序号和阅读顺序；目录、文件名、知识地图、项目篇和代码结构都不编号，也不能用来推断先后。

遇到不同问题时回到对应真源：

| 想确认什么 | 去哪里 |
| --- | --- |
| 下一步学什么 | [标准学习路径](learning-path.md) |
| 某项知识是否在范围内、依赖什么、落在哪里 | [知识地图](knowledge-map.md) |
| 产品最终必须做到什么 | [SPEC.md](../SPEC.md) |
| 领域对象、状态和关键系统契约 | [SDD.md](../SDD.md) |
| 通用能力和产品代码怎样分工 | [PLAN.md](../PLAN.md) |
| 当前阶段怎样综合实践和验收 | [第一阶段项目篇](lessons/033.rag-review-assistant.project.md)或[第二阶段项目篇](lessons/110.agent-review-assistant.project.md) |

学习者不需要先读完 SPEC、SDD 和 PLAN；项目篇会把当前阶段需要理解和完成的部分转化为综合任务，但不会复制这些真源。

## 完整学习主线

课程始终演进同一个需求评审助手：

```text
模型调用与结构化输出
→ 固定 RAG 与可信证据
→ 需求对象模型、Finding 与决策、人工批准与交付包
→ agent_core 与 LangChain 第一个真实 Agent
→ Tool Runtime、Agentic RAG 与运行治理
→ LangGraph 状态、恢复与人工介入
→ 需求 Brief 追问与 propose / Diff / apply 确认门
→ MCP、Search、Browser、File 与 Code Tool、变更影响分析
→ Conversation、Run State、记忆、事件和运行界面
→ Agent Skills
→ Deep Research
→ 框架内 Multi-Agent 基线与独立 A2A 互操作
→ 必要的复杂 Workflow 组合
→ Trace、Regression、Human Eval 与 Feedback
```

这条链表示能力怎样在同一产品中逐步闭环，不是另一套阅读顺序。具体先后仍只看学习路径。

## 两个阶段

| 阶段 | 交付目标 |
| --- | --- |
| 第一阶段：RAG 应用基础 | 固定 RAG 的需求定义、评审与交付工作台：可信证据边界、需求对象模型、可定位 Finding 与人的逐项决策、人工批准与基线、交付包、两层角色、Review API、Web 工作台和最小质量基线 |
| 第二阶段：Agent、Tools 与 Multi-Agent | 同一对象模型上框架驱动的 Agent 与 `agent_core`、受治理工具、可恢复状态、记忆、研究、协作和统一质量闭环；Agent 追问缺失信息、经 propose / Diff / apply 在用户裁决下推动需求收敛、分析变更影响；提交批准、退回 / 撤回、批准、正式导出、成员管理与 Brief 编辑仍由人触发 |

两个阶段沿同一产品连续演进，不建立阶段内版本轴。

## 四类课程文档

| 类型 | 目录 | 主要回答 |
| --- | --- | --- |
| 概念篇 | `lessons/` | 这是什么、为什么需要、与相邻概念怎样区分 |
| 机制篇 | `lessons/` | 数据如何流动、机制为何成立、边界和失败怎样出现 |
| 实验篇 | `lessons/` | 如何准备、运行、调试、观察日志和阅读对应实现 |
| 项目篇 | `lessons/` | 如何把多个能力组合进同一产品并完成阶段验收 |

机制篇是课程核心正文，负责解释一项能力解决什么问题、关键对象怎样协作、数据或状态怎样变化，以及框架或应用怎样实现并约束它。成熟框架可以直接承载主要机制，正文应讲清其公开能力、运行流程和应用组合方式。只有存在独立可执行的观察问题时才建立实验篇，用它固定框架与 SDK 版本并完成安装、运行、观察、调试和验证；机制与实验不强制一一对应，相邻机制可以共享一篇实验。项目篇引用产品要求、详细设计和代码入口，不复制产品规格、SDD 或产品 README。

## 代码入口

| 目录 | 职责 |
| --- | --- |
| `source/packages/` | 可复用能力的唯一实现 |
| `source/demos/` | 机制观察、对照和稳定失败复现 |
| `source/apps/review_assistant/` | 唯一可运行产品 |

课程不在 `course/` 复制实现，也不在 demo 中维护第二份产品。产品安装、配置、启动、测试和部署见 [需求评审助手 README](../source/apps/review_assistant/README.md)。

第二阶段随 LangChain Agent 接入建立 `source/packages/agent_core/`，并在课程推进中扩展通用运行、治理、事件和框架适配能力。它组合 LangChain、LangGraph 等成熟框架而不重复实现框架运行时；评审 Prompt、领域 Schema、引用策略、记忆策略和角色组装保留在 `source/apps/review_assistant/agent/`。

## 学习规则

- Python、HTTP、JSON、配置、异步和 PostgreSQL 是必备基础；已掌握时可以通过路径中的检查，不必为形式重学。
- LLM、RAG、Agent 和 Eval 主路径使用真实模型或真实外部服务；失败必须显式暴露。
- Mock 只用于单元测试、离线排查、稳定失败复现或明确对照，不能证明真实效果。
- 每节先解决一个主问题。若同时需要学习多个独立生命周期、协议角色或实现系统，应继续拆节。
- 完整能力链以本页总图为导航，以学习路径为顺序；每增加一层复杂度，都保留与之相称的固定样例、运行记录和失败证据。
