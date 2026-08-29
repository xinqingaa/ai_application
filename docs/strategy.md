# AI 应用学习战略

本文只维护仓库的长期定位、唯一目标和两个阶段。产品要求见根 [SPEC.md](../SPEC.md)，学习规则见 [learning-guide.md](learning-guide.md)，课程顺序见 [learning-path.md](../course/learning-path.md)。

## 定位

本仓库面向有前端、Flutter 或跨端经验的开发者，目标不是训练模型算法或建设通用 AI 平台，而是补齐 LLM、RAG、Agent、Tools、Multi-Agent、评估观测和 AI Native 产品能力。

目标角色是能够独立完成 AI 应用闭环的高级前端或跨端工程师：既能理解模型与知识机制，也能实现 API、状态、证据、运行过程和用户交互。

## 唯一主项目

仓库只维护“需求评审助手”一个产品：

```text
真实业务资料
→ 固定 RAG 与可信评审
→ Agent Harness 与受治理 Tools
→ MCP、通用工具、Agentic RAG 与 Agent Skills
→ Deep Research
→ Multi-Agent 与 A2A
→ 必要 Workflow
→ 可运行、可观察、可评估的产品
```

“完整”指业务闭环完整，不指功能平台庞大。产品必须有真实输入输出、可追溯证据、可见状态与失败、明确权限与停止、最小质量证据和可交互入口。

## 垂直切口与架构可迁移性

“售后入口与订单状态”以及后续“售后接口 v2 与多端契约一致性评审”是贯穿学习、实验和验收的稳定垂直切口。固定切口是为了复用同一批业务事实、控制比较变量，并观察固定 RAG 怎样演进为 Agent 与 Multi-Agent；它不是产品只能回答这一个问题的白名单。需求评审助手可以处理不同主题的需求，以及 PRD、会议纪要、验收条件、接口契约、客户端模型、配置和验证结果等配套材料，但当前产品职责仍然是需求评审。

架构同时区分通用运行能力和领域装配。Model Provider、Structured Output、RAG 基础能力、Agent Harness、Tool Runtime、状态与事件、Deep Research、Multi-Agent 和必要 Workflow 原语应尽量保持领域可复用；Prompt、业务 Schema、知识库与 Metadata、Agent Skills、工具与权限策略、Agent 责任、证据与拒答规则、评估标准和产品交互则由具体领域决定。

因此，迁移到智能客服、金融或医疗等领域，通常不是替换 Harness，而是在通用运行能力上建立新的领域契约和产品装配。高风险领域还必须增加与其风险相称的来源资格、权限、合规和人工复核。架构可迁移不等于当前仓库建设万能助手：本仓库仍只实现需求评审助手，不为证明复用性创建平行产品或通用 Agent 平台。

## 第一阶段：RAG 应用基础

交付可运行、可诊断、具备最小可信证据的固定 RAG 需求评审助手：

- 真实文档解析、Chunk、Metadata 和来源定位。
- PostgreSQL FTS、pgvector、RRF 与 Retriever 诊断。
- Context、Structured Output、Citation、Refusal 和补充问题。
- Review API、Web 工作台、Golden Set 与固定对照。

第一阶段不建设 Agent、Multi-Agent、通用 Workflow 或完整质量平台。结束时 Retriever 必须形成稳定 Tool 契约。

## 第二阶段：Agent、Tools 与 Multi-Agent

在同一产品上增加动态决策、工具执行、研究和协作：

- Agent Harness、Tool Runtime、权限和停止治理。
- MCP、Search、Browser、File 与 Code Tool。
- Agentic RAG、Agent Skills 与受控补检索。
- Conversation、Run State、短期记忆与长期偏好记忆、事件协议与运行界面。
- Deep Research、多 Agent 分工与 A2A。
- 必要的 Checkpoint、恢复、人工介入与副作用治理。
- 固定 RAG、单 Agent 和 Multi-Agent 的质量、成本与延迟比较。

Multi-Agent 必须学习独立责任、上下文、工具、状态、证据和失败隔离，并通过与单 Agent 的比较理解质量、成本、延迟和失败定位的变化。比较结果用于具体产品选型，不预设 Multi-Agent 必须证明收益大于新增成本和复杂度。Workflow 只解决显式状态、恢复和人工控制，不单独占一个阶段。

## 能力优先级

```text
RAG
→ Agent Harness 与 Tools
→ Multi-Agent 与 A2A
→ 必要 Workflow
→ 完整质量收束
```

质量不是最后才出现：每一层保留与复杂度相称的最小固定样例、运行记录和失败证据，完整 Trace、Regression、Human Eval 与 Feedback 在后部统一收束。

Python、HTTP、JSON、异步、配置和 PostgreSQL 是必备基础，已掌握时可以通过检查。FastAPI、SSE、Conversation 和事件协议是必须学习的产品主线能力；二者都不是保守的按需支持。

## 扩展与非目标

Reranker、GraphRAG、RAPTOR、OCR/VLM、复杂知识治理和完整评估平台只有在真实问题与收益证据成立时进入产品。多租户、工具市场、低代码画布、企业权限中台和 Kubernetes 属于远期认知，不是当前验收项。

仓库不建设多个平行项目，不为展示复杂度引入 Agent，也不复制 RAGFlow、MaxKB 或 Dify 的平台规模。

## 最终能力

完成主线后，学习者应能判断问题需要固定程序、RAG、Agent、Multi-Agent 还是 Workflow；解释模型、知识、工具、状态、协议和 UI 的完整链路；并用证据定位应修改数据、Prompt、Retriever、Tool、Agent、Workflow 还是交互。
