# AI Application Projects 横向对比

## 文档定位

本文件用于沉淀 `ai_application/other` 下已归档项目之间的横向对比。

它不是单个项目的源码拆解，而是回答这些问题：

- 多个项目分别解决什么问题？
- 各自的工程重心和业务侧重点是什么？
- 哪些设计可以组合学习？
- 面对具体业务场景时，应该优先参考哪个项目？

后续引入新的 AI 应用项目时，继续在本文中新增对比章节，而不是把详细对比堆进 `README.md`。

## 当前对比结论总览

| 对比主题 | 覆盖项目 | 核心结论 |
| --- | --- | --- |
| RAG 平台与 Agent 应用平台的侧重点 | RAGFlow、MaxKB | RAGFlow 更重知识生产与检索上下文，MaxKB 更重应用产品化与业务流程编排 |

## RAGFlow 与 MaxKB 横向对比

这两个项目都属于 AI 应用平台方向，也都覆盖 RAG、应用、Workflow、Agent、工具调用等能力。但它们的工程重心不同，不应该简单理解成谁替代谁。

一句话概括：

> RAGFlow 更适合学习“复杂知识资产如何被生产成可靠上下文”；MaxKB 更适合学习“AI 能力如何被包装成可发布、可运营、可编排的业务应用”。

| 维度 | RAGFlow | MaxKB |
| --- | --- | --- |
| 核心定位 | 企业级 RAG / Agent Context Engine | 企业级智能体应用平台 |
| 第一价值 | 知识生产质量、复杂文档解析、混合检索、引用可信 | 应用产品化、Workflow 编排、工具调用、业务交付 |
| 更强的地方 | DeepDoc、分块策略、父子块、TOC、RAPTOR、GraphRAG、DocStore 抽象、评测意识 | Application / Version、ChatRecord、Workflow Runtime、Node 协议、MCP / Tool、子应用、表单中断 |
| 关注对象 | Knowledgebase、Document、Task、Chunk、Retriever、Dialog、Canvas | Application、Knowledge、Chat、ChatRecord、Workflow、Node、Tool、ApplicationVersion |
| 更像什么 | 知识中台 + 检索引擎 + 上下文层 | AI 应用工厂 + Agent 编排平台 |
| 学习重点 | 如何把脏乱复杂资料加工成可靠上下文 | 如何把 AI 能力变成业务可用的应用产品 |
| 适合优先学习的人 | 做知识库质量、复杂 RAG、文档解析、检索评测的人 | 做 AI 应用平台、内部助手、流程自动化、Agent 编排的人 |

### 核心差异

RAGFlow 更关心的问题是：

```text
资料复杂怎么办？
文档怎么解析？
chunk 怎么更准？
检索为什么命中？
引用怎么可信？
长文档怎么回答？
表格怎么查询？
知识怎么评估？
```

MaxKB 更关心的问题是：

```text
AI 应用怎么发布？
用户怎么访问？
会话怎么记录？
流程怎么编排？
工具怎么治理？
Agent 怎么调用系统？
子应用怎么协作？
业务怎么持续运营？
```

所以更准确的判断不是“RAGFlow 能做 RAG，MaxKB 能做 Agent”，而是：

- RAGFlow 的最强项在知识处理、复杂资料解析、检索质量和引用可信。
- MaxKB 的最强项在应用产品化、Workflow 运行时、工具治理和业务流程编排。
- RAGFlow 也有 Agent Canvas、MCP、Memory、Workflow；MaxKB 也有知识库、文档入库、向量检索和固定 RAG 应用。
- 两者都覆盖 RAG + Agent，但工程深度投放的位置不同。

### 各自特点与优点

RAGFlow 的特点是 RAG 前半段特别深。它不满足于上传文件、切 chunk、embedding，而是把文档解析、任务拆分、digest 复用、语义增强、父子块、TOC、表格 SQL、混合检索、rerank、引用处理都做成体系。它真正重视的是：资料进入系统后，如何被加工成高质量知识资产。

| RAGFlow 优点 | 业务价值 |
| --- | --- |
| 文档处理深 | 适合 PDF、合同、论文、表格、扫描件、长文档 |
| 检索体系完整 | 全文 + 向量 + rerank + metadata + 父子块 + TOC |
| 知识生命周期完整 | 上传、解析、任务、取消、重试、删除清理、统计 |
| 高级索引意识强 | RAPTOR、GraphRAG、TOC 适合长文档、多章节、多跳问题 |
| Context Layer 思维强 | 先把上下文做好，再谈 Agent 和自动化 |

MaxKB 的特点是 RAG 后半段和业务交付特别完整。它也有文档、段落、向量、关键词检索，但更突出的不是解析深度，而是如何把 RAG 包装成应用：应用配置、发布版本、聊天入口、OpenAI 兼容 API、嵌入页、权限、统计、ChatRecord、Workflow、工具、MCP、子应用、长期记忆。

| MaxKB 优点 | 业务价值 |
| --- | --- |
| 应用对象建模完整 | AI 应用不只是 prompt，而是可发布、可统计、可集成的产品 |
| 双模式清晰 | 固定 RAG 应用覆盖常见场景，Workflow 承接复杂流程 |
| Workflow Runtime 细 | NodeResult、runtime_node_id、上下文变量、流式输出、中断恢复 |
| Agent 工具治理强 | Tool、ToolRecord、MCP、Skill、Workflow 工具化、子应用 |
| 业务落地感强 | 更容易映射到客服、内部助手、流程助手、数据源入库等真实场景 |

### 适合场景

RAGFlow 更适合这些场景：

| 场景 | 原因 |
| --- | --- |
| 合同 / 法务 / 合规审查 | 需要复杂文档解析、页码坐标、条款级引用 |
| 论文 / 研报 / 长文档研究 | 需要 TOC、父子块、RAPTOR、跨章节总结 |
| 企业多源知识中台 | Connector、同步、任务、metadata、检索治理更重要 |
| Git 仓库 / 研发知识库解析 | Markdown、代码、Issue、API 文档等资料需要先被稳定知识化 |
| 表格 / 报表问答 | table chunker、field_map、SQL path 更适合结构化查询 |
| 高质量知识库建设 | 重点在知识入库、解析、召回、评测、引用可信 |

MaxKB 更适合这些场景：

| 场景 | 原因 |
| --- | --- |
| 企业内部知识助手 | 应用发布、权限、嵌入、反馈、统计链路完整 |
| 客服 / 售后机器人 | 固定 RAG 应用、直接命中、问题优化、ChatRecord 分析 |
| 政务 / 医疗 / 教育问答 | 多知识库、引用、访问限制、Workflow 表单补充 |
| 业务流程助手 | 条件节点、表单节点、工具节点、子应用节点更直接 |
| Agent 平台 / 工具调用平台 | MCP、Tool、Workflow 工具化、ToolRecord 更成熟 |
| 多应用协作 | 主应用负责路由和编排，子应用负责专业能力 |

### 对“长问题 / 大仓库 / 自动化流程”的判断

如果问题是：

```text
给 AI 一个很大的 Git 仓库、很多长文档、合同、PDF、表格，
希望它稳定解析、索引、检索、引用、总结、回答细节问题。
```

优先学习 RAGFlow。它的核心价值在于把复杂资料变成可靠上下文。

如果问题是：

```text
用户提交一个业务需求，
AI 先判断意图，
再查知识库，
再调用系统 API，
必要时让用户补表单，
然后创建工单、生成报告、调用子应用或写入知识库。
```

优先学习 MaxKB。它的核心价值在于把 AI 组织进业务流程。

需要注意的是，RAGFlow 不是只能做文档解析，它也有 Agent Canvas、MCP、Memory 和 Workflow；MaxKB 也不是不能做 RAG，它也有文档入库、知识库、检索和问答链路。真正的区别在于：

```text
RAGFlow 更重 Context Layer：知识如何被生产、检索、引用。
MaxKB 更重 Application / Action Layer：AI 如何被发布、编排、调用工具、参与业务。
```

### 迁移到自己业务的组合思路

如果要吸收两个项目的经验，可以按下面的分层来设计自己的 AI 应用系统：

| 层级 | 优先学习对象 | 应该沉淀的能力 |
| --- | --- | --- |
| 知识生产层 | RAGFlow | 文档解析、分块策略、任务化入库、语义增强、metadata、删除清理 |
| 检索上下文层 | RAGFlow | 全文 + 向量 + rerank、父子块、TOC、表格 SQL、引用、评测 |
| AI 应用层 | MaxKB | Application、发布版本、API Key、嵌入页、权限、反馈、统计 |
| Workflow 编排层 | MaxKB | Node / Edge、NodeResult、变量上下文、流式事件、表单中断、续跑 |
| Agent 行动层 | MaxKB | Tool、ToolRecord、MCP、Workflow 工具化、子应用协作、审计 |

一个较理想的业务架构是：

```text
复杂知识处理层：学习 RAGFlow
AI 应用编排层：学习 MaxKB
```

也可以理解为：

```text
RAGFlow 负责让 AI 有可靠资料可读。
MaxKB 负责让 AI 能进入业务流程做事。
```
