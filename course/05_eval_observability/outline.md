# 05 评估、可观测与质量工程大纲

## 课程定位

`05_eval_observability` 是 AI 应用从“能跑”走向“可持续迭代”的质量工程主线。

`03_rag` 解决知识系统和单 Agent 知识助手，`04_agent` 解决工具系统和工作流实现，`05_eval_observability` 解决这些系统如何被评估、追踪、回归和优化。

这一门课不重新学习 LangChain 或 LangGraph 的主功能，而是围绕 RAG、Agent、Workflow 和项目建立评估集、trace、指标、bad case、回归测试和反馈闭环。

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

## 完成标准

完成本课程后，应能做到：

- 为 LLM / RAG / Agent / Workflow 建立 golden set。
- 评估检索、生成、引用、拒答、工具轨迹、工作流节点和人工审核结果。
- 使用 trace 还原一次 AI 请求从输入到输出的全过程。
- 对 Prompt、Retriever、Tool、Graph、Model 的变化做版本对比和回归。
- 管理 bad case，并判断应该回流到知识库、Prompt、Retriever、Tool、Graph 还是人工流程。
- 为需求评审助手和金融 Copilot 建立基础质量面板。

## 代码组织建议

```text
source/05_eval_observability/
├── packages/
│   ├── eval_core/
│   └── trace_core/
├── demos/
│   ├── rag_eval_dashboard/
│   ├── agent_trajectory_eval/
│   ├── workflow_trace_demo/
│   └── bad_case_review/
└── README.md
```

## 专题目录

```text
course/05_eval_observability/
├── 00_quality_engineering_problem_space.md
├── 01_evaluation_dataset_and_golden_set.md
├── 02_rag_retrieval_generation_eval.md
├── 03_citation_refusal_eval.md
├── 04_bad_case_management.md
├── 05_agent_trajectory_tool_eval.md
├── 06_workflow_eval_and_human_review.md
├── 07_observability_trace_span.md
├── 08_versioning_regression_experiments.md
├── 09_cost_latency_metrics.md
├── 10_llm_as_judge_and_human_eval.md
├── 11_feedback_loop.md
├── 12_project_quality_dashboard.md
└── outline.md
```

## 00. 质量工程问题空间

### 真实问题

AI 应用不能靠“感觉效果还行”迭代。每次改 Prompt、chunk、embedding、retriever、tool、graph 或模型，都可能让某些能力变好、另一些能力变差。

### 基础原理

- Evaluation。
- Observability。
- Trace。
- Regression。
- Bad Case。
- Feedback Loop。

### 最小实现

- 对同一批问题运行两个版本。
- 比较答案、来源、成本、延迟和失败样本。

### 主流框架实现

- 自定义评估脚本。
- LangSmith / OpenTelemetry / tracing 工具认知。
- 简单 dashboard。

### 失败分析与能力边界

- 只看最终答案。
- 只靠人工感受。
- 评估样本太少。
- trace 不包含中间状态。

### 评估观测

- 明确每类系统的关键指标。
- 建立最小质量基线。

### 小项目实战

为需求评审助手建立质量工程目标：

- 检索命中。
- 引用正确。
- 拒答合理。
- 单 Agent 工具选择正确。

### 项目收敛

本章输出质量工程指标清单。

## 01. Evaluation Dataset 与 Golden Set

### 真实问题

没有固定样本，就无法知道系统是否变好。RAG、Agent 和 Workflow 都需要自己的 golden set。

### 基础原理

- input。
- expected output。
- expected sources。
- expected tools。
- forbidden tools。
- expected workflow path。
- human review label。

### 最小实现

- 建立 30 条需求评审助手样本。
- 建立 20 条金融 Copilot 样本。
- 标注问题类型和预期行为。

### 主流框架实现

- JSON / YAML 数据集。
- pytest 参数化。
- LangSmith dataset 认知。

### 失败分析与能力边界

- 样本只覆盖简单问题。
- expected answer 太死。
- 没有无答案、需拒答、需人工确认样本。

### 评估观测

- 样本覆盖率。
- 问题类型分布。
- 版本回归通过率。

### 小项目实战

建立两个项目的 golden set：

- 需求评审 RAG 助手。
- 金融 Copilot。

### 项目收敛

沉淀 `eval_core.datasets`。

## 02. RAG Retrieval 与 Generation Eval

### 真实问题

RAG 答案错误时，需要知道是检索错了，还是生成错了。

### 基础原理

- Retrieval eval。
- Generation eval。
- source hit。
- Recall@k。
- MRR。
- answer correctness。
- groundedness。

### 最小实现

- 对 golden set 跑检索。
- 计算 expected source hit。
- 再跑生成并记录答案质量。

### 主流框架实现

- 自定义 metrics。
- RAGAS / LangSmith 认知。

### 失败分析与能力边界

- 检索没命中却让生成背锅。
- 只评 answer，不评 source。
- LLM judge 不稳定。

### 评估观测

- retrieval recall。
- answer correctness。
- groundedness。
- latency / cost。

### 小项目实战

评估需求评审助手：

- chunk 策略变化。
- retriever 变化。
- rerank 变化。
- query rewrite 变化。

### 项目收敛

沉淀 `eval_core.rag_metrics`。

## 03. Citation 与 Refusal Eval

### 真实问题

RAG 应用最重要的不是“说得像”，而是是否有依据、引用是否正确、无依据时是否拒答。

### 基础原理

- Citation correctness。
- Citation coverage。
- Refusal accuracy。
- Over-refusal。
- Under-refusal。

### 最小实现

- 构造有答案、无答案、证据不足、需人工确认四类样本。
- 检查引用是否存在于 context。

### 主流框架实现

- 自定义 citation checker。
- LLM-as-judge 辅助判断。

### 失败分析与能力边界

- 引用不存在的 source。
- 有依据却拒答。
- 无依据却强答。
- 引用正确但解释错误。

### 评估观测

- citation correctness。
- refusal accuracy。
- over-refusal rate。
- missing citation rate。

### 小项目实战

需求评审助手必须输出：

- sources。
- refusal reason。
- risk note。
- need_human_review。

### 项目收敛

沉淀 `eval_core.citation_refusal`。

## 04. Bad Case Management

### 真实问题

失败样本如果只停留在聊天记录里，就不会真正改善系统。需要把 bad case 分类、归因、修复和回归。

### 基础原理

- Bad case taxonomy。
- Root cause。
- Fix owner。
- Regression status。
- Feedback loop。

### 最小实现

- 对 20 个失败样本分类。
- 标记失败来自文档、chunk、retriever、prompt、tool、graph 还是模型。

### 主流框架实现

- JSON bad case store。
- issue tracker。
- dashboard。

### 失败分析与能力边界

- 只记录坏答案，不记录中间状态。
- 修复后不回归。
- 把所有问题都归因给模型。

### 评估观测

- bad case 数量。
- 修复率。
- 回归通过率。
- 重复失败类型。

### 小项目实战

建立需求评审助手 bad case review：

- 每周归因。
- 修复策略。
- 回归验证。

### 项目收敛

沉淀 `eval_core.bad_cases`。

## 05. Agent Trajectory 与 Tool Eval

### 真实问题

Agent 最终答案对，不代表过程对。它可能调用了不该调用的工具、跳过人工确认、循环多次或使用错误参数。

### 基础原理

- Trajectory。
- Tool call correctness。
- Allowed tools。
- Forbidden tools。
- Argument validation。
- Iteration budget。

### 最小实现

- 为 20 条 Agent 样本标注 expected tools 和 forbidden tools。
- 运行 Agent 并检查工具轨迹。

### 主流框架实现

- Trace based eval。
- LangSmith trajectory eval 认知。
- 自定义 tool call checker。

### 失败分析与能力边界

- 最终答案正确但越权调用。
- 工具参数错误但被模型掩盖。
- Agent 循环过多。
- 没有人工确认。

### 评估观测

- tool selection accuracy。
- forbidden tool rate。
- argument validation pass rate。
- max iteration breach。

### 小项目实战

金融 Copilot Agent eval：

- 查询工具。
- 合规审核工具。
- 人工审批工具。
- 禁止越权工具。

### 项目收敛

沉淀 `eval_core.agent_metrics`。

## 06. Workflow Eval 与 Human Review

### 真实问题

LangGraph 工作流是否可靠，不只看最终输出，还要看节点是否走对、分支是否合理、人工审核是否触发、状态是否可恢复。

### 基础原理

- Workflow path。
- Node success。
- Conditional route。
- Human review label。
- Interrupt / resume。

### 最小实现

- 对合规审核工作流标注 expected path。
- 检查是否进入人工审批节点。

### 主流框架实现

- LangGraph trace。
- 自定义 workflow evaluator。

### 失败分析与能力边界

- 条件分支错误。
- 高风险未触发人工审核。
- 中断后无法恢复。
- 人工修改未记录。

### 评估观测

- path accuracy。
- node failure rate。
- human review trigger accuracy。
- resume success rate。

### 小项目实战

金融 Copilot 合规工作流评估：

- 低风险自动建议。
- 中风险人工确认。
- 高风险必须审核。

### 项目收敛

沉淀 `eval_core.workflow_metrics`。

## 07. Observability、Trace 与 Span

### 真实问题

没有 trace，就很难知道一次 AI 请求到底发生了什么。调试 RAG、Agent 和 Workflow 都需要看到输入、上下文、检索、工具、节点、输出和错误。

### 基础原理

- Trace。
- Span。
- Attributes。
- Events。
- Logs。
- Correlation id。

### 最小实现

- 为一次 RAG 请求记录 trace。
- 为一次 Agent 工具调用记录 span。
- 为一次 workflow 节点记录状态变化。

### 主流框架实现

- OpenTelemetry 认知。
- LangSmith trace 认知。
- 自定义 lightweight trace。

### 失败分析与能力边界

- 只记录最终答案。
- trace 泄露敏感数据。
- span 粒度太粗或太细。

### 评估观测

- trace completeness。
- error span。
- latency breakdown。
- token / cost attribution。

### 小项目实战

需求评审助手 trace：

- request。
- rewrite。
- retrieve。
- context。
- generate。
- eval。

### 项目收敛

沉淀 `trace_core`。

## 08. Versioning、Regression 与 Experiments

### 真实问题

Prompt、retriever、tool、graph、model 都会变。如果没有版本和实验记录，就无法判断变化是否有效，也无法回滚。

### 基础原理

- Prompt version。
- Retriever config version。
- Tool version。
- Graph version。
- Model version。
- Experiment run。
- Regression test。

### 最小实现

- 对同一 golden set 运行两个版本。
- 输出差异报告。

### 主流框架实现

- 自定义 experiment log。
- LangSmith experiment 认知。
- CI 回归测试。

### 失败分析与能力边界

- 改了配置但没记录。
- 只看平均分，不看关键样本退化。
- 没有回滚策略。

### 评估观测

- pass rate。
- regression count。
- improved cases。
- degraded cases。

### 小项目实战

需求评审助手对比：

- chunk v1 vs v2。
- retriever v1 vs rerank。
- prompt v1 vs v2。
- single agent on / off。

### 项目收敛

沉淀 `eval_core.experiments`。

## 09. Cost、Latency 与 Metrics

### 真实问题

AI 应用质量不只是准确率。成本、延迟、token、工具调用次数和人工介入率都会影响能否长期使用。

### 基础原理

- Token cost。
- Latency。
- First token time。
- Tool call count。
- Workflow duration。
- Human review cost。

### 最小实现

- 统计每次请求的 token、成本、耗时、工具调用次数。
- 输出任务类型维度的平均值。

### 主流框架实现

- SDK usage。
- trace attributes。
- metrics dashboard。

### 失败分析与能力边界

- 只追求效果忽略成本。
- 多 Agent 带来成本爆炸。
- rerank / deep research 延迟不可接受。

### 评估观测

- cost per task。
- p50 / p95 latency。
- token per answer。
- tool calls per task。

### 小项目实战

金融 Copilot 指标：

- 客服问答成本。
- 合规审核成本。
- 公告解读成本。
- 人工审批耗时。

### 项目收敛

沉淀 `eval_core.metrics`。

## 10. LLM-as-Judge 与 Human Eval

### 真实问题

很多 AI 输出无法用简单规则判断，需要 LLM-as-Judge 或人工评审。但 judge 本身也会不稳定，人工评审也需要标准。

### 基础原理

- LLM-as-Judge。
- Rubric。
- Pairwise comparison。
- Human label。
- Agreement。

### 最小实现

- 为答案准确性、完整性、引用质量、风险提示设计评分 rubric。
- 用 judge 给 20 条样本打分，再抽样人工复核。

### 主流框架实现

- 自定义 judge prompt。
- structured judge output。
- 人工评审表。

### 失败分析与能力边界

- judge 偏好长答案。
- judge 被答案话术欺骗。
- 人工评审标准不一致。

### 评估观测

- judge score。
- human score。
- agreement rate。
- disputed cases。

### 小项目实战

需求评审助手人工评审维度：

- 是否有依据。
- 是否指出风险。
- 是否需要追问。
- 是否可用于评审讨论。

### 项目收敛

沉淀 `eval_core.judges`。

## 11. Feedback Loop

### 真实问题

用户反馈、人工修改、失败样本如果不能回流到知识库、Prompt、Retriever、Tool 或 Graph，系统不会持续变好。

### 基础原理

- Feedback capture。
- Feedback classification。
- Routing。
- Fix。
- Regression。

### 最小实现

- 用户标记答案有用 / 无用。
- 人工标记失败原因。
- 将反馈路由到对应修复项。

### 主流框架实现

- Feedback store。
- Bad case queue。
- Review workflow。

### 失败分析与能力边界

- 反馈太粗，无法行动。
- 收集了反馈但没有修复流程。
- 修复后没有回归。

### 评估观测

- feedback count。
- actionable feedback rate。
- fixed feedback rate。
- repeated issue rate。

### 小项目实战

需求评审助手反馈回流：

- 知识缺失 -> 文档补充。
- 检索失败 -> retriever 调整。
- 答案不稳 -> prompt / schema 调整。
- 工具错误 -> tool / graph 调整。

### 项目收敛

沉淀 `eval_core.feedback`。

## 12. 项目质量面板

### 真实问题

项目作品需要展示的不只是聊天界面，还要展示系统是否可评估、可观测、可迭代。

### 基础原理

- Quality dashboard。
- Eval summary。
- Trace viewer。
- Bad case board。
- Cost / latency panel。

### 最小实现

- 输出一个静态质量报告。
- 展示最近一次评估结果、失败样本和成本延迟。

### 主流框架实现

- 简单前端面板。
- Notebook / markdown report。
- 后续 `06_ai_native_frontend` 做产品化工作台。

### 失败分析与能力边界

- 面板只好看，不支持定位问题。
- 指标太多没有重点。
- 不展示 bad case。

### 评估观测

- 项目版本。
- eval pass rate。
- key regressions。
- cost / latency。
- unresolved bad cases。

### 小项目实战

为两个主项目建立质量面板：

- 需求评审 RAG 助手。
- 金融 Copilot。

### 项目收敛

`05_eval_observability` 的产物进入 `06_ai_native_frontend` 和 `07_projects`，作为作品化展示的重要部分。
