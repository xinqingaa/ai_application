# 02 LLM 模型交互与上下文工程大纲

## 课程定位

`02_llm` 是 AI 应用的模型交互底座。

这门课不是重新学习“如何调一次模型接口”，而是系统建立后续 RAG、Agent、评估观测和项目实战都要复用的 LLM 应用工程能力。

本课程服务两个长期项目：

- 需求评审 RAG 助手 / 智能客服。
- 金融 Copilot。

本课程的核心问题是：

- 如何稳定调用不同模型供应商。
- 如何设计 Prompt、结构化输出和上下文。
- 如何让模型调用可测试、可回归、可观测。
- 如何控制成本、延迟和失败边界。
- 如何为 RAG 和 Agent 提供统一模型调用底座。

## 学习链路

每个专题都遵循统一链路：

```text
真实问题
-> 基础原理
-> 最小实现
-> 主流框架实现
-> 失败分析与能力边界
-> 评估观测
-> 小项目实战
-> 项目收敛
```

代码不按章节机械堆脚本，而是围绕可复用 package、关键 demo 和项目底座组织。

## 完成标准

完成本课程后，应能做到：

- 设计统一的 LLM 调用接口。
- 在多模型供应商之间切换，并知道能力差异和成本差异。
- 为不同任务设计 Prompt、结构化输出和失败兜底。
- 管理多轮对话和上下文预算。
- 建立模型调用 harness，让调用结果可记录、可对比、可回归。
- 理解 Function Calling 的 API 形态，并知道它为什么是 Agent 的入口。
- 为 `03_rag` 和 `04_agent` 提供可复用的 `llm_core` 能力。

## 代码组织建议

```text
source/02_llm/
├── packages/
│   └── llm_core/
├── demos/
│   ├── provider_switching/
│   ├── structured_review_output/
│   ├── streaming_chat/
│   ├── context_budgeting/
│   └── llm_harness_eval/
└── README.md
```

`llm_core` 是后续 RAG 和 Agent 复用的模型调用底座。Demo 只验证关键机制，不要求每篇文档都配套脚本。

## 专题目录

```text
course/02_llm/
├── 00_llm_problem_space.md
├── 01_model_api_and_provider_abstraction.md
├── 02_prompt_engineering_for_apps.md
├── 03_structured_outputs.md
├── 04_streaming_and_conversation.md
├── 05_context_engineering.md
├── 06_llm_calling_harness.md
├── 07_cost_latency_caching.md
├── 08_function_calling_api_boundary.md
├── 09_llm_project_foundation.md
└── outline.md
```

## 00. LLM 应用问题空间

### 真实问题

AI 应用不是“调用一次模型接口”。真实项目里需要处理模型不稳定、上下文超限、输出不可解析、成本不可控、供应商切换、失败重试和前端体验等问题。

### 基础原理

- LLM 作为概率生成系统。
- 应用侧需要负责上下文、约束、校验、回归和观测。
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
- 单次调用无法解决长期记忆和复杂工具执行问题。

### 评估观测

- 建立最小调用样例集。
- 记录模型、参数、输入、输出、成本、耗时。
- 为后续 Prompt / 模型 / schema 调整保留对比基础。

### 小项目实战

为需求评审助手定义 LLM 在项目中的职责：

- 总结需求。
- 抽取风险。
- 生成结构化评审项。
- 解释引用来源。
- 在依据不足时拒答或提示人工确认。

### 项目收敛

本章输出项目级模型调用需求清单，作为 `llm_core` 的设计输入。

## 01. Model API 与 Provider 抽象

### 真实问题

项目不能被单一模型供应商绑定。学习和项目阶段需要低成本模型，效果验证阶段可能需要更强模型，国内外平台 API 也存在差异。

### 基础原理

- Provider、model、base_url、api_key、参数和响应结构的关系。
- OpenAI SDK 风格为什么适合作为应用侧抽象参考。
- 供应商差异应收敛在配置层和 adapter 层。

### 最小实现

- 使用同一套调用函数切换不同 OpenAI 兼容模型。
- 统一返回 `content / raw_response / usage / latency / provider`。

### 主流框架实现

- OpenAI SDK。
- OpenAI 兼容平台。
- LangChain ChatModel 的封装思路。

### 失败分析与能力边界

- OpenAI 兼容不代表能力完全一致。
- 不同模型对 structured output、tool calling、streaming 的支持不同。
- 供应商限流、超时、错误码需要统一处理。

### 评估观测

- 对同一批 prompt 比较不同模型输出质量、成本和延迟。
- 记录 provider 切换是否影响 schema 成功率。

### 小项目实战

为需求评审助手建立模型配置：

- 日常开发模型。
- 效果验证模型。
- 结构化输出模型。
- 兜底模型。

### 项目收敛

沉淀 `llm_core.providers` 和统一 `LLMClient`。

## 02. 面向应用的 Prompt Engineering

### 真实问题

Prompt 不是“写一句提示词”，而是模型和应用之间的任务协议。需求评审、客服回复、风险抽取和摘要生成都需要稳定的任务描述、输入边界和输出要求。

### 基础原理

- Role、task、context、constraints、examples、output format。
- Prompt 与 schema 的协作关系。
- Prompt 变量、模板和版本管理。

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

### 评估观测

- 建立 Prompt 回归样例。
- 记录版本、输入、输出、失败类型。
- 对比字段缺失率、拒答正确率和人工可用性。

### 小项目实战

设计需求评审助手的 Prompt 集：

- 需求摘要。
- 风险识别。
- 问题清单。
- 缺失信息追问。
- 带依据的回答。

### 项目收敛

沉淀 `llm_core.prompts`，为 RAG generation 和 Agent tool response 复用。

## 03. Structured Outputs

### 真实问题

项目不能只依赖自然语言输出。评审结论、风险等级、引用来源、拒答原因和待确认事项都需要结构化，才能进入前端、数据库、评估和工作流。

### 基础原理

- JSON 输出、JSON Mode、Structured Outputs、Pydantic validation。
- Schema 是应用和模型之间的数据契约。
- 校验失败需要重试、修复或降级。

### 最小实现

- 定义 `ReviewResult` schema。
- 从需求文本中抽取风险项、问题、建议和置信度。
- 校验失败时触发修复或兜底。

### 主流框架实现

- Pydantic。
- OpenAI Structured Outputs。
- LangChain structured output parser。

### 失败分析与能力边界

- 字段缺失。
- 类型错误。
- 枚举值不合法。
- 模型输出解释文本污染 JSON。
- schema 过复杂导致成功率下降。

### 评估观测

- 统计 schema 成功率。
- 统计重试次数。
- 记录失败样本和失败字段。

### 小项目实战

需求评审助手的结构化输出：

- `summary`
- `risks`
- `questions`
- `suggestions`
- `citations`
- `confidence`
- `need_human_review`

### 项目收敛

沉淀 `llm_core.schemas` 和 `llm_core.structured_call`。

## 04. Streaming 与 Conversation

### 真实问题

AI 应用需要可感知的响应过程。前端需要流式输出，后端需要管理多轮消息，项目需要知道哪些历史应该保留、裁剪或摘要。

### 基础原理

- SSE / streaming chunk。
- 模型不记得历史，历史由应用侧传入。
- 多轮对话本质是上下文状态管理。

### 最小实现

- 实现一个流式聊天接口。
- 保存最近若干轮消息。
- 超出 token budget 时裁剪历史。

### 主流框架实现

- FastAPI StreamingResponse。
- EventSource / fetch stream。
- LangChain streaming callbacks。

### 失败分析与能力边界

- 流式中断。
- 前端和后端状态不一致。
- 历史消息过长导致成本升高。
- 多轮上下文污染当前任务。

### 评估观测

- 记录首 token 时间、总耗时、token 数。
- 记录 conversation trim 前后的上下文。
- 检查多轮回答是否引用过期信息。

### 小项目实战

需求评审助手支持多轮追问：

- 用户补充背景。
- AI 追问缺失信息。
- 保留当前评审任务状态。

### 项目收敛

沉淀 `llm_core.conversation`，但复杂 memory 留到 RAG / Agent 继续展开。

## 05. Context Engineering

### 真实问题

RAG 和 Agent 的效果很大程度取决于“给模型看什么”。上下文不是越多越好，而是要选择、排序、压缩和隔离。

### 基础原理

- System prompt、developer instruction、user input、examples、retrieved context 的职责边界。
- Context budget。
- 上下文裁剪、摘要、压缩和优先级。
- 任务上下文、知识上下文、历史上下文的区别。

### 最小实现

- 构造一个带 system、任务说明、用户输入、检索片段、输出 schema 的上下文。
- 超出预算时按优先级裁剪。

### 主流框架实现

- Prompt template + context builder。
- LangChain document formatting。
- LangGraph state 中的 context 管理思路。

### 失败分析与能力边界

- 无关上下文污染输出。
- 上下文顺序影响回答。
- 历史记忆和知识库混用导致错误。
- 压缩过度导致关键信息丢失。

### 评估观测

- 对比不同 context 构造策略的输出。
- 记录被裁剪内容。
- 检查引用是否来自真实上下文。

### 小项目实战

为需求评审助手设计 context builder：

- 当前问题。
- 需求文档片段。
- 历史评审规则。
- 输出格式。
- 拒答规则。

### 项目收敛

沉淀 `llm_core.context`，供 `03_rag` 的 context construction 复用。

## 06. LLM Calling Harness

### 真实问题

如果模型调用没有统一 harness，每次改 prompt、schema、模型或参数都只能靠手感判断，后续 RAG 和 Agent 会难以调试。

### 基础原理

- Harness 是模型调用的工程外壳。
- 它统一输入、输出、日志、错误、重试、评估样例和实验记录。
- 它让模型调用从“试一试”变成“可回归”。

### 最小实现

- 定义统一 request / response 对象。
- 记录 prompt version、model、params、usage、latency、error。
- 对固定样例重复运行并比较结果。

### 主流框架实现

- 自定义 lightweight harness。
- LangSmith / OpenTelemetry / trace 的基本思路。
- 后续 `05_eval_observability` 系统展开。

### 失败分析与能力边界

- 过早引入复杂平台会增加学习负担。
- 只记录最终答案不够，需要记录输入、上下文和结构化结果。
- 对非确定性输出不能只做字符串精确匹配。

### 评估观测

- 最小 golden cases。
- schema success rate。
- latency / cost。
- bad case 记录。

### 小项目实战

为需求评审助手建立最小评估样例：

- 正常需求。
- 信息缺失需求。
- 高风险需求。
- 无依据问题。

### 项目收敛

沉淀 `llm_core.harness`，为 RAG eval 和 Agent trajectory eval 提供基础格式。

## 07. 成本、延迟与缓存

### 真实问题

学习和项目都需要控制成本。不同模型、上下文长度、流式输出、缓存策略都会影响体验和预算。

### 基础原理

- 输入 token、输出 token、缓存 token。
- 成本、延迟、质量之间的权衡。
- Prompt caching 适合稳定前缀和长系统提示。

### 最小实现

- 统计一次调用的 token、耗时和估算成本。
- 对比短 prompt、长上下文、缓存友好 prompt 的差异。

### 主流框架实现

- SDK usage 字段。
- 模型供应商 prompt caching 能力。
- 本地响应缓存和实验缓存。

### 失败分析与能力边界

- 缓存不能掩盖错误上下文。
- 便宜模型不一定适合结构化输出或复杂推理。
- 过度压缩上下文可能降低效果。

### 评估观测

- 记录每个任务类型的平均成本。
- 记录首 token 时间和总耗时。
- 记录模型切换后的质量变化。

### 小项目实战

为需求评审助手定义模型使用策略：

- 开发调试模型。
- 结构化抽取模型。
- 高质量评审模型。
- 低风险兜底模型。

### 项目收敛

沉淀 `llm_core.costing` 和模型选择策略。

## 08. Function Calling API 边界

### 真实问题

Function Calling 是 Agent 的入口，但在 LLM 阶段需要先理解它的 API 形态和边界，避免把工具调用和 Agent 系统混在一起。

### 基础原理

- Tool schema。
- 模型选择工具和生成参数。
- 应用侧执行工具。
- 工具结果再回传模型。

### 最小实现

- 定义一个 `get_requirement_doc` 工具 schema。
- 让模型生成工具调用参数。
- 应用侧执行 mock 工具并返回结果。

### 主流框架实现

- OpenAI tools / function calling。
- Anthropic / Gemini 工具调用差异认知。
- LangChain tool binding 的入口。

### 失败分析与能力边界

- Function Calling 不等于 Agent。
- 模型可能选择错误工具或生成错误参数。
- 工具执行需要权限、校验、重试和审计。
- 多步工具循环放到 `04_agent` 系统学习。

### 评估观测

- 记录工具选择是否正确。
- 记录参数 schema 是否通过。
- 记录工具调用是否需要人工确认。

### 小项目实战

需求评审助手预留工具：

- 查询需求文档。
- 查询历史评审规则。
- 查询接口规范。
- 创建待确认问题。

### 项目收敛

本章只沉淀 Function Calling API 认知，工具 runtime 和 Agent loop 进入 `04_agent`。

## 09. LLM 项目底座

### 真实问题

进入 RAG 前，需要有一套可复用的 LLM 调用底座，否则每个 RAG demo 都会重复处理模型配置、prompt、schema、日志、重试和成本统计。

### 基础原理

- `llm_core` 不是通用平台，而是项目学习阶段的最小复用层。
- 它服务 RAG、Agent、评估和项目，不追求过度抽象。

### 最小实现

- `LLMClient`
- `PromptTemplate`
- `StructuredCall`
- `ContextBuilder`
- `CallLogger`
- `EvalCase`

### 主流框架实现

- 可对接 OpenAI SDK。
- 可被 LangChain / LangGraph adapter 复用。
- 可接入后续 trace / eval。

### 失败分析与能力边界

- 不做复杂模型网关。
- 不做企业级权限系统。
- 不做完整 LLMOps 平台。
- 不屏蔽所有供应商能力差异。

### 评估观测

- 跑通最小 LLM golden set。
- 输出调用日志。
- 对比两个模型在同一任务上的表现。

### 小项目实战

构建需求评审助手的 LLM foundation：

- 需求摘要。
- 风险抽取。
- 结构化评审输出。
- 流式回复。
- 基础成本统计。

### 项目收敛

`02_llm` 的最终产物是 `llm_core`，作为 `03_rag`、`04_agent` 和 `07_projects` 的底座。
