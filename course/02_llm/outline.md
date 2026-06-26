# 02 LLM 模型交互与上下文工程大纲

> **定稿说明（暂定）**：本大纲为备课清单，已与 [learning-guide.md](../../docs/learning-guide.md) 对齐；真实实施时可能对单节边界微调，但不改变「一节一交付、单包 import、逐步完善」原则。专题正文结构以 learning-guide §7 为准。
> **能力路线与项目版本**：本课程属于**能力路线**（学什么）；需求评审助手 **V0–V6** 是**项目版本**（产品演进到哪），二者相关但不一一对应。


## 课程定位

`02_llm` 是需求评审助手的模型交互底座，供 RAG、单 Agent、多 Agent 和 Workflow 复用。

这门课不是重新学习“如何调一次模型接口”，而是系统建立后续 RAG、Agent、Workflow、评估观测和项目实战都要复用的 LLM 应用工程能力。

本课程的核心问题是：

- 如何稳定调用不同模型供应商。
- 如何区分 Chat Model、Embedding Model、Rerank Model 等模型角色。
- 如何设计 Prompt、结构化输出和上下文。
- 如何让模型调用可测试、可回归、可观测。
- 如何控制成本、延迟和失败边界。
- 如何为 RAG、Agent、Workflow 提供统一模型调用底座。

## 学习链路

每个专题都遵循统一链路：

```text
A. 学习认知链路（正文前半，见 learning-guide §7）
真实问题
-> 基础原理
-> 最小实现
-> 主流框架实现
-> 失败分析与能力边界

B. 单节交付约定（正文后半）
-> 本节实战
-> 完成标准（含运行与观察 + 自检题）
-> 本节沉淀
```

代码不按章节机械堆脚本，而是围绕可复用 package、关键 demo 和项目底座组织。

## 完成标准

完成本课程后，应能做到：

- 设计统一的 LLM 调用接口。
- 在多模型供应商之间切换，并知道能力差异和成本差异。
- 为需求理解、风险识别、追问、报告生成等任务设计 Prompt。
- 为不同模型能力设计结构化输出和失败兜底。
- 管理多轮对话、检索上下文、Agent 中间结果和上下文预算。
- 建立模型调用 harness，让调用结果可记录、可对比、可回归。
- 理解 Function Calling 的 API 形态，并知道它为什么是 Agent 的入口。
- 为 `03_rag`、`04_agent` 和 `05_eval_observability` 提供可复用的 `llm_core` 能力。

## 代码里程碑（草案）

> **写作顺序**：以 learning-guide §6.4「一节一交付」为准——每节文档 + 当节代码 + Git。  
> 下表是**全课完成后的 package 终态对照**，不是「先写 00–03 再统一写 M1」的排期。

| 对照项 | 全课完成后的最小验收 |
| --- | --- |
| 调用 + 结构化 | `LLMClient` 可切换 provider；`02_structured_review_output` demo 可跑 |
| 流式 + 可靠性 | streaming demo 可跑；错误分类与有限重试可观测 |
| package 收敛 | `llm_core` 模块齐全；供 `03_rag` import 的 README 与入口清晰 |

各节正文中的设计草图在当节代码完成后，直接替换为 `source/` 真实链接，不必再使用 `[CODE-GATE: M1]` 类标注（除非 outline 备课仍保留该习惯）。

## 代码组织建议

```text
source/
├── packages/
│   └── llm_core/
├── demos/
│   ├── 02_first_chat/
│   ├── 02_provider_switching/
│   ├── 02_structured_review_output/
│   ├── 02_streaming_chat/
│   ├── 02_context_budgeting/
│   ├── 02_reliability_demo/
│   └── 02_llm_harness_eval/
├── apps/
│   └── review_assistant/
└── python_base/

review_assistant/                # 07_projects 起：完整产品（import source/packages）
├── app/
├── workbench/
└── infra/
```

`02_llm/00` 在 `source/packages/llm_core` 创建全仓库唯一实例；demo 使用 `02_` 前缀。后续课与根 `review_assistant/` 仅 `import` 扩展，禁止 copy。

## 专题目录

```text
course/02_llm/
├── 00_llm_problem_space.md
├── 01_model_api_and_provider_abstraction.md
├── 02_prompt_engineering_for_apps.md
├── 03_structured_outputs.md
├── 04_streaming_and_conversation.md
├── 05_context_engineering.md
├── 06_reliability_errors_and_degradation.md
├── 07_llm_calling_harness.md
├── 08_cost_latency_caching.md
├── 09_function_calling_api_boundary.md
├── 10_llm_project_foundation.md
└── outline.md
```

## 00. LLM 应用问题空间

### 真实问题

AI 应用不是“调用一次模型接口”。需求评审助手需要处理模型不稳定、上下文超限、输出不可解析、成本不可控、供应商切换、失败重试和前端流式体验。

### 基础原理

- LLM 是概率生成系统。
- 应用侧负责上下文、约束、校验、回归和观测。
- Prompt、模型参数、上下文内容和输出 schema 共同决定结果稳定性。

### 最小实现

- 发起一次最小聊天请求。
- 打印请求、响应、token 使用和耗时。
- 观察同一输入在不同模型或参数下的差异。

### 主流框架实现

- OpenAI SDK 风格调用。
- OpenAI 兼容平台接入。
- 后续 LangChain / LangGraph 通过统一模型接口复用能力。

### 失败分析与能力边界

- 模型会编造、不稳定、遗漏约束。
- Prompt 不能替代数据治理、权限控制和评估。
- 单次调用无法解决长期记忆、复杂工具执行和多 Agent 协作问题。

### 完成标准（运行与观察）

- 建立最小调用样例集。
- 记录模型、参数、输入、输出、成本、耗时。
- 为后续 Prompt / 模型 / schema 调整保留对比基础。

### 本节实战

为需求评审助手定义 LLM 职责：

- 总结需求。
- 抽取风险。
- 生成结构化评审项。
- 解释引用来源。
- 在依据不足时拒答或提示人工确认。

### 本节沉淀

输出项目级模型调用需求清单，作为 `llm_core` 的设计输入。

## 01. Model API 与 Provider 抽象

### 真实问题

项目不能被单一模型供应商绑定。学习阶段、效果验证阶段和作品展示阶段可能使用不同模型，不同模型对 structured output、tool calling、streaming 的支持也不同。

### 基础原理

- Provider、model、base_url、api_key、参数和响应结构的关系。
- Chat Model、Embedding Model、Rerank Model 应区分配置和职责。
- 模型能力需要显式记录，例如 context length、streaming、tool calling、structured output、cost。

### 最小实现

- 使用同一套调用函数切换不同 OpenAI 兼容模型。
- 统一返回 `content / raw_response / usage / latency / provider / model`。
- 为模型配置增加能力标签。

### 主流框架实现

- OpenAI SDK。
- OpenAI 兼容平台。
- LangChain ChatModel 的封装思路。

### 失败分析与能力边界

- OpenAI 兼容不代表能力完全一致。
- 不同模型对 schema、tool call、stream chunk 的支持差异很大。
- 供应商限流、超时、错误码需要统一处理。

### 完成标准（运行与观察）

- 对同一批 prompt 比较不同模型输出质量、成本和延迟。
- 记录 provider 切换是否影响 schema 成功率。
- 记录模型能力标签和真实表现是否一致。

### 本节实战

为需求评审助手建立模型配置：

- 日常开发模型。
- 结构化输出模型。
- 工具调用模型。
- 低成本批处理模型。
- 兜底模型。

### 本节沉淀

沉淀 `llm_core.providers`、统一 `LLMClient` 和模型配置 schema。

## 02. 面向应用的 Prompt Engineering

### 真实问题

Prompt 不是“写一句提示词”，而是模型和应用之间的任务协议。需求理解、风险审查、技术影响分析、测试验收点生成和最终报告汇总都需要稳定的任务描述、输入边界和输出要求。

### 基础原理

- Role、task、context、constraints、examples、output format。
- Prompt 与 schema 的协作关系。
- Prompt 变量、模板和版本管理。
- 多 Agent 场景下，Prompt 必须明确角色职责和禁止越界。

### 最小实现

- 为同一个需求评审任务写三个 prompt 版本。
- 比较输出稳定性、字段完整性和风险识别效果。

### 主流框架实现

- Prompt template。
- Few-shot 示例管理。
- LangChain PromptTemplate / ChatPromptTemplate 的思路。

### 失败分析与能力边界

- Prompt 过长会增加成本和噪声。
- 约束冲突会导致输出不稳定。
- Few-shot 示例质量差会污染结果。
- Prompt 不能替代检索证据、工具权限和评估。

### 完成标准（运行与观察）

- 建立 Prompt 回归样例。
- 记录版本、输入、输出、失败类型。
- 对比字段缺失率、拒答正确率和人工可用性。

### 本节实战

设计需求评审助手 Prompt 集：

- 需求理解。
- 风险审查。
- 技术影响分析。
- 测试验收点生成。
- 缺失信息追问。
- 证据汇总与报告生成。

### 本节沉淀

沉淀 `llm_core.prompts`，为 RAG generation、Agent role prompt 和 Workflow node prompt 复用。

## 03. Structured Outputs

### 真实问题

项目不能只依赖自然语言输出。评审结论、风险等级、引用来源、拒答原因、待确认事项、多 Agent 中间结果都需要结构化，才能进入前端、数据库、评估和工作流。

### 基础原理

- JSON 输出、JSON Mode、Structured Outputs、Pydantic validation。
- Schema 是应用和模型之间的数据契约。
- 输出 schema 应服务业务流程，不追求复杂。

### 最小实现

- 定义 `ReviewRisk`、`ClarificationQuestion`、`Citation`、`ReviewReport` schema。
- 让模型按 schema 输出，并用本地校验器验证。

### 主流框架实现

- OpenAI Structured Outputs。
- Pydantic parser。
- LangChain output parser。

### 失败分析与能力边界

- JSON 可解析不代表内容正确。
- Schema 太复杂会降低生成稳定性。
- 模型可能补全不存在的引用或风险。

### 完成标准（运行与观察）

- 统计 schema parse 成功率。
- 统计字段缺失率、引用缺失率、风险等级异常率。
- 记录失败样本进入回归集。

### 本节实战

输出结构化需求评审结果：

- 需求摘要。
- 风险列表。
- 技术影响。
- 测试关注点。
- 引用来源。
- 待确认问题。
- 最终建议。

### 本节沉淀

沉淀 `llm_core.schemas` 和结构化解析工具。

## 04. Streaming 与 Conversation

### 真实问题

需求评审助手需要向用户展示模型生成、检索、工具调用、多 Agent 分析和 Workflow 节点状态。前端不能只等待最终回答。

### 基础原理

- Token stream 与 event stream 不同。
- 对话历史、任务状态、工具结果和长期记忆不能混在一起。
- 流式响应要支持取消、失败、重试和最终一致性。

### 最小实现

- 实现 `message_start / token / error / done`。
- 追加 `retrieval_start / tool_call / agent_step / workflow_node` 事件。
- 前端按事件更新状态。

### 主流框架实现

- SSE。
- fetch ReadableStream。
- WebSocket 用于双向实时任务。
- LangGraph / Agent runtime 的事件流思想。

### 失败分析与能力边界

- token 到达顺序错乱。
- 取消请求后后端仍在执行。
- 前端显示 completed，但后端任务未完成。
- 历史对话过长污染当前任务。

### 完成标准（运行与观察）

- 首 token 时间。
- 流中断率。
- 取消成功率。
- 前后端状态一致性。

### 本节实战

为需求评审助手实现流式状态：

- 正在检索。
- 正在分析风险。
- 正在生成报告。
- 等待人工确认。

### 本节沉淀

沉淀 `llm_core.streaming` 事件格式，为 `06_ai_native` 使用。

## 05. Context Engineering

### 真实问题

需求评审材料可能很长，检索片段、历史对话、业务规则、接口文档和 Agent 中间结果都会争夺上下文窗口。

### 基础原理

- 系统指令、用户输入、检索上下文、历史对话、工具结果、工作流状态有不同优先级。
- 上下文不是越多越好，需要压缩、去重、排序和引用映射。
- 证据上下文必须可追溯。

### 最小实现

- 构造一个需求评审 Prompt 上下文。
- 限制 token budget。
- 保留 source id 与引用编号。

### 主流框架实现

- LangChain document formatting。
- map-reduce / refine 摘要思路。
- context compression retriever。

### 失败分析与能力边界

- 上下文过多导致模型忽略关键证据。
- 上下文过少导致模型编造。
- Agent 中间结果如果不压缩，会污染最终报告。

### 完成标准（运行与观察）

- 记录上下文 token 数。
- 记录引用片段是否进入上下文。
- 对比不同 context builder 的回答质量。

### 本节实战

为评审报告生成设计上下文规则：

- 当前需求材料优先。
- 命中的业务规则和历史评审其次。
- Agent 中间结论只保留结构化摘要。
- 无证据内容不能进入最终依据。

### 本节沉淀

沉淀 `llm_core.context`，为 RAG 和多 Agent 汇总服务。

## 06. Reliability、Errors 与 Degradation

### 真实问题

模型调用会遇到限流、超时、schema 失败、内容安全拦截等问题。没有统一的错误分类、重试边界和降级策略，RAG 和 Agent 链路会在生产场景中迅速失控。

### 基础原理

- 错误分类：网络、限流、超时、schema、内容安全、供应商错误。
- 重试边界：什么可重试、什么应快速失败。
- 超时、熔断、降级与兜底模型。
- Reliable Service Layer：把重试、超时、安全检查收进统一调用层。

### 最小实现

- 对同一请求模拟超时和 schema 失败。
- 实现有限重试与兜底模型切换。
- 记录错误类型与恢复路径。

### 主流框架实现

- SDK 错误码与异常处理。
- 自定义 `ReliableLLMService`。
- 与 harness、trace 的衔接。

### 失败分析与能力边界

- 无限重试放大成本和延迟。
- 降级不能牺牲引用与评估可追溯性。
- 安全拦截与 Prompt Injection 防护在 `04_agent` 继续展开。

### 完成标准（运行与观察）

- 错误类型分布。
- 重试成功率。
- 降级触发率。
- 超时 P95。

### 本节实战

为需求评审助手定义调用失败处理：摘要任务可重试、结构化输出失败可换模型、高风险任务应失败可见。

### 本节沉淀

沉淀 `llm_core.reliability`，与 harness 和后续 trace 对接。

## 07. LLM Calling Harness

### 真实问题

没有调用记录和回归样例，就无法判断 Prompt、模型或 schema 调整后系统是否变好。

### 基础原理

- Harness 是模型调用的实验和回归外壳。
- 每次调用应记录模型、参数、Prompt 版本、输入、输出、token、耗时和错误。
- Harness 为后续 `05_eval_observability` 提供原始数据。

### 最小实现

- 建立一组 JSON/YAML 调用样例。
- 批量运行同一 prompt。
- 输出结果对比表。

### 主流框架实现

- pytest 参数化。
- LangSmith dataset / run 认知。
- 自定义 lightweight harness。

### 失败分析与能力边界

- Harness 不等于完整评估系统。
- 样例过少会给出虚假信心。
- 只看最终文本无法定位 schema、成本和延迟问题。

### 完成标准（运行与观察）

- schema 成功率。
- 字段完整率。
- token / latency。
- 模型间差异。

### 本节实战

建立需求评审助手最小调用集：

- 需求摘要样例。
- 风险识别样例。
- 缺失信息追问样例。
- 结构化报告样例。

### 本节沉淀

沉淀 `llm_core.harness`，后续接入 eval runner。

## 08. Cost、Latency 与 Caching

### 真实问题

多 Agent 需求评审会增加模型调用次数。如果不控制成本和延迟，项目很快会变得不可用。

### 基础原理

- token 成本来自输入、输出和中间步骤。
- 首 token 时间影响体验，总耗时影响任务完成。
- 缓存要区分 Prompt 缓存、检索缓存、模型结果缓存和任务状态缓存。

### 最小实现

- 记录每次模型调用 token 和耗时。
- 对同一批样例比较不同模型成本。
- 为低风险重复任务增加缓存实验。

### 主流框架实现

- SDK usage 字段。
- 简单本地缓存。
- Redis 缓存认知。

### 失败分析与能力边界

- 缓存错误会返回过期结论。
- 为省成本牺牲引用和评估会降低可信度。
- 多 Agent 过度拆分会放大成本。

### 完成标准（运行与观察）

- 平均 token。
- 平均延迟。
- 单次评审成本。
- cache hit rate。

### 本节实战

比较同一批评审任务：

- 单次汇总。
- RAG 后汇总。
- 多 Agent 分析后汇总。

### 本节沉淀

输出成本和延迟基线，进入项目质量面板。

## 09. Function Calling API 边界

### 与 `04_agent/01–02` 的分工

- **本专题**：Function Calling 的 **API 形态与边界**——tool schema、模型如何产出调用参数、应用如何校验一次调用；**不实现** Tool Runtime、权限、审计、Agent Loop。
- **`04_agent/01`**：Tool Schema 设计与 `agent_core.tool_schema` 沉淀。
- **`04_agent/02`**：Tool Runtime、权限确认、审计与失败兜底。

完成本专题 = 理解「模型选工具 vs 应用执行工具」；Agent 系统实现继续到 `04_agent`。

### 真实问题

Agent 不是魔法。模型只负责选择工具和生成参数，应用侧负责校验、执行、权限、审计和失败处理。

### 基础原理

- Tool schema 描述工具。
- Tool choice 是模型决策。
- Tool runtime 是应用执行。
- 工具结果需要重新进入上下文。

### 最小实现

- 定义一个查询业务规则的 tool schema。
- 让模型生成调用参数。
- 应用侧校验参数并返回结果。

### 主流框架实现

- OpenAI tools。
- Anthropic / Gemini 工具调用差异认知。
- LangChain tool binding。

### 失败分析与能力边界

- 工具描述不清导致误调用。
- 参数 schema 太松导致执行失败。
- Function Calling 不负责权限、审计和业务幂等。

### 完成标准（运行与观察）

- 工具选择正确率。
- 参数校验通过率。
- 工具调用失败类型。

### 本节实战

定义需求评审助手工具调用边界：

- 查询知识库。
- 查询接口文档。
- 查询历史评审。
- 创建待确认问题。
- 生成评审报告草稿。

### 本节沉淀

输出 `04_agent` 需要继续实现的 tool schema 清单。

## 10. LLM Project Foundation

### 真实问题

课程结束后，LLM 能力必须成为项目底座，而不是散落在 demo 里。

### 基础原理

- `llm_core` 应包含 client、provider、prompt、schema、context、streaming、harness。
- 配置和代码要分离。
- 调用日志是评估和观测的基础。

### 最小实现

- 建立 `llm_core` 包。
- 提供一个统一调用入口。
- 跑通结构化输出和 streaming demo。

### 主流框架实现

- FastAPI service 调用 `llm_core`。
- LangChain / LangGraph 复用统一模型接口。
- 配置文件管理模型能力。

### 失败分析与能力边界

- 过早抽象会增加复杂度。
- 把 provider 差异泄漏到业务代码会导致后续难维护。
- 没有 harness 的底座不可回归。

### 完成标准（运行与观察）

- 是否能替换模型。
- 是否能记录调用。
- 是否能复现失败。
- 是否能被 RAG / Agent 复用。

### 本节实战

搭建需求评审助手的 LLM foundation：

- 统一 `LLMClient`。
- 模型配置。
- Prompt registry。
- 结构化输出 parser。
- 调用日志。
- streaming event。

### 本节沉淀

完成后进入 `03_rag`，用同一套 LLM foundation 构建知识问答和证据生成链路。

## 参考设计映射

- 参考 MaxKB 的模型资源化和应用配置思路，将模型能力收敛到配置和调用底座。
- 参考 RAGFlow 的多模型角色划分，明确 LLM、Embedding、Rerank 在后续知识系统中的职责边界。
