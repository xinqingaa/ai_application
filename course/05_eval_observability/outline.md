# 05 评估、可观测与质量工程大纲

> **定稿说明（暂定）**：本大纲为备课清单，已与 [learning-guide.md](../../docs/learning-guide.md) 对齐；真实实施时可能对单节边界微调，但不改变「一节一交付、单包 import、逐步完善」原则。专题正文结构以 learning-guide §7 为准。
> **能力路线与项目版本**：本课程属于**能力路线**（学什么）；需求评审助手 **V0–V6** 是**项目版本**（产品演进到哪），二者相关但不一一对应。


## 课程定位

`05_eval_observability` 是需求评审助手从「能跑」走向「可持续迭代」的质量工程主线。

`03_rag` 解决知识系统和单 Agent RAG，`04_agent` 解决工具系统、多 Agent 和 Workflow，`05_eval_observability` 解决这些系统如何被评估、追踪、回归和优化。

这一门课不重新学习 LangChain 或 LangGraph 的主功能，而是围绕 RAG、Agent、Workflow 和项目建立评估集、trace、指标、bad case、回归测试和反馈闭环。

### 与 `03_rag/12` 的分工

- `03_rag/12` 已建立 RAG golden set、`rag_eval` 与 citation/refusal 最小指标（V2）。
- 本课程**不重复** RAG eval 入门，而是从已有 `rag_eval` 出发，扩展 Agent trajectory、Workflow path、trace、版本回归、工程契约测试与质量面板（V4–V6）。
- 若尚未完成 V2，可先只做 `03_rag/12`，再进入本课程专题 01–04。

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

## 完成标准

完成本课程后，应能做到：

- 为 LLM / RAG / Agent / Workflow 建立 golden set。
- 评估检索、生成、引用、拒答、追问、工具轨迹、Agent 输出、工作流节点和人工审核结果。
- 使用 trace 还原一次 AI 请求从输入到输出的全过程。
- 对 Prompt、Retriever、Tool、Graph、Model 的变化做版本对比和回归。
- 管理 bad case，并判断应该回流到知识库、Prompt、Retriever、Tool、Graph 还是人工流程。
- 为需求评审助手建立基础质量面板。

## 代码组织建议

```text
source/
├── packages/
│   ├── eval_core/
│   └── trace_core/
├── demos/
│   ├── 05_rag_eval_dashboard/
│   ├── 05_agent_trajectory_eval/
│   ├── 05_workflow_trace_demo/
│   └── 05_bad_case_review/
├── apps/
│   └── review_assistant/
└── python_base/

review_assistant/                # 07_projects 起：完整产品（import source/packages）
├── app/
├── workbench/
└── infra/
```

`05/00` 在 `source/packages/` 创建 `eval_core`、`trace_core`；扩展 `03_rag/12` 已有 `rag_eval` 能力时 **import** 而非复制。与 `03_rag/12` 分工见上文。

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
├── 12_engineering_contract_tests.md
├── 13_project_quality_dashboard.md
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

- 建立 `source/packages/eval_core`、`trace_core` package 壳（`05/00`；扩展 `rag_eval` 时 import 单实例，见代码组织说明）。
- 在文档中列出「改 Prompt / 改检索 / 改模型」时希望对比的维度（答案、来源、成本、延迟等），00 不要求可运行对比脚本。

### 主流框架实现

- 自定义评估脚本、LangSmith / OpenTelemetry 认知、简单 dashboard（本课后续专题落地）。

### 失败分析与能力边界

- 只看最终答案。
- 只靠人工感受。
- 评估样本太少。
- trace 不包含中间状态。

### 本节不做（推迟到后续节）

- 可运行的 eval dashboard、trace 采集（**05 后续节**）。
- 与 `03_rag/12` 分工的完整 `rag_eval` 回归（**03/12 + 05**）。

### 完成标准（运行与观察）

- **代码**：`eval_core` / `trace_core` 壳存在（或明确与 `rag_eval` 的扩展关系）。
- **文档**：能说出 eval / trace / bad case 各解决什么；列出需求评审助手 3–5 个关键质量指标（笔记即可）。

### 本节实战

为需求评审助手建立质量工程目标（文档）：

- 检索命中。
- 引用正确。
- 拒答合理。
- 单 Agent 工具选择正确。
- 多 Agent 角色输出完整。
- Workflow 人工确认合理。

### 本节沉淀

输出质量工程指标清单。

## 01. Evaluation Dataset 与 Golden Set

### 真实问题

没有固定样本，就无法知道系统是否变好。RAG、Agent 和 Workflow 都需要自己的 golden set。

### 基础原理

- input。
- expected output。
- expected sources。
- expected tools。
- expected agent roles。
- forbidden tools。
- expected workflow path。
- human review label。

### 最小实现

- 建立 30 条 RAG 问答样本。
- 建立 20 条风险识别样本。
- 建立 20 条多 Agent 协作样本。
- 建立 10 条 Workflow / 人工确认样本。

### 主流框架实现

- JSON / YAML 数据集。
- pytest 参数化。
- LangSmith dataset 认知。

### 失败分析与能力边界

- 样本只覆盖简单问题。
- expected answer 太死。
- 没有无答案、需拒答、需追问、需人工确认样本。

### 完成标准（运行与观察）

- 样本覆盖率。
- 问题类型分布。
- 版本回归通过率。

### 本节实战

建立需求评审助手 golden set：

- 有明确依据的问题。
- 无依据问题。
- 跨知识源问题。
- 风险识别问题。
- Agent 工具调用问题。
- Workflow 人工确认问题。

### 本节沉淀

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

### 完成标准（运行与观察）

- retrieval recall。
- answer correctness。
- groundedness。
- latency / cost。

### 本节实战

评估需求评审助手：

- chunk 策略变化。
- retriever 变化。
- rerank 变化。
- query rewrite 变化。
- context builder 变化。

### 本节沉淀

沉淀 `eval_core.rag_metrics`。

## 03. Citation 与 Refusal Eval

### 真实问题

RAG 应用最重要的不是“说得像”，而是是否有依据、引用是否正确、无依据时是否拒答或追问。

### 基础原理

- Citation correctness。
- Citation coverage。
- Refusal accuracy。
- Over-refusal。
- Under-refusal。
- Clarification accuracy。

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

### 完成标准（运行与观察）

- citation correctness。
- citation coverage。
- refusal accuracy。
- clarification accuracy。

### 本节实战

评估需求评审回答：

- 每条风险是否有来源。
- 证据不足时是否追问。
- 无答案时是否拒答。
- 是否错误引用。

### 本节沉淀

沉淀 `eval_core.citation_refusal`。

## 04. Bad Case Management

### 真实问题

发现错误只是开始。真正有价值的是把 bad case 归因，并回流到正确的修复位置。

### 基础原理

- bad case 分类。
- failure attribution。
- root cause。
- owner。
- fix action。
- regression sample。
- review status。

### 最小实现

- 建立 bad case 表。
- 为每个失败样本标注失败原因和修复动作。

### 主流框架实现

- bad case board。
- issue / label 工作流。
- eval run diff。

### 失败分析与能力边界

- 只记录错误，不归因。
- 所有错误都归咎于模型。
- 修复后没有回归验证。

### 完成标准（运行与观察）

- bad case 数量。
- 失败类型分布。
- 修复周期。
- 回归通过率。

### 本节实战

把 bad case 归因到：

- 文档解析。
- chunk。
- metadata。
- embedding。
- retriever。
- prompt。
- model。
- tool。
- agent role。
- workflow。
- human process。

### 本节沉淀

沉淀 bad case board 数据结构。

## 05. Agent Trajectory 与 Tool Eval

### 真实问题

多 Agent 系统不能只评最终报告。需要看每个 Agent 是否做了该做的事，工具是否选对，参数是否正确，是否产生无依据结论。

### 基础原理

- tool selection accuracy。
- tool argument correctness。
- trajectory completeness。
- agent role quality。
- conflict detection。
- supervisor decision。

### 最小实现

- 为多 Agent 样本标注 expected tools 和 expected role outputs。
- 对实际轨迹做对比。

### 主流框架实现

- LangSmith trace 认知。
- 自定义 trajectory evaluator。
- LLM-as-judge 辅助角色输出判断。

### 失败分析与能力边界

- 工具选对但参数错。
- 单个 Agent 输出正确，汇总时丢失。
- Agent 之间结论冲突但未被发现。

### 完成标准（运行与观察）

- tool accuracy。
- argument validity。
- role completeness。
- conflict detection rate。

### 本节实战

评估多 Agent 需求评审：

- 需求理解 Agent 是否抽取完整。
- 知识检索 Agent 是否查对知识源。
- 风险审查 Agent 是否覆盖关键风险。
- 技术影响 Agent 是否识别接口和数据影响。
- 测试验收 Agent 是否生成可执行验收点。
- 汇总 Agent 是否保留证据和冲突。

### 本节沉淀

沉淀 `eval_core.agent_metrics`。

## 06. Workflow Eval 与 Human Review

### 真实问题

Workflow 不是节点跑完就成功。节点路径、条件分支、人工确认、失败恢复和最终产物都要评估。

### 基础原理

- expected workflow path。
- node success rate。
- interrupt rate。
- resume success。
- human approval result。
- high-risk confirmation。

### 最小实现

- 为 workflow 样本标注 expected path。
- 记录每个节点状态和人工确认结果。

### 主流框架实现

- LangGraph trace。
- 自定义 workflow run record。
- OpenTelemetry span 认知。

### 失败分析与能力边界

- 条件分支错误。
- 该人工确认时未中断。
- 中断后无法恢复。
- 人工修改没有进入后续上下文。

### 完成标准（运行与观察）

- node success rate。
- interrupt precision。
- resume success。
- report edit distance。

### 本节实战

评估需求评审 Workflow：

- 是否进入正确节点。
- 是否在证据不足时追问。
- 是否在高风险时触发人工确认。
- 人工修改是否被记录。
- 失败是否可恢复。

### 本节沉淀

沉淀 `eval_core.workflow_metrics`。

## 07. Observability、Trace 与 Span

### 真实问题

当用户说“这次结果不对”时，需要能还原一次请求从输入到输出的全过程。

### 基础原理

- trace id。
- run id。
- span。
- event。
- model call。
- retrieval call。
- tool call。
- agent step。
- workflow node。
- frontend event。

### 最小实现

- 为一次需求评审生成 trace。
- 每个模型调用、检索、工具调用和节点执行生成 span。

### 主流框架实现

- OpenTelemetry。
- LangSmith trace。
- 自定义 trace_core。

### 失败分析与能力边界

- trace 只记录最终答案。
- 没有关联 run id。
- 中间状态丢失。
- trace 太细导致无法阅读。

### 完成标准（运行与观察）

- trace 完整率。
- span 缺失率。
- 错误定位耗时。

### 本节实战

为一次需求评审生成完整 trace：

```text
user input
-> document selection
-> retrieval
-> agent steps
-> tool calls
-> workflow nodes
-> human review
-> report generation
-> feedback
```

### 本节沉淀

沉淀 `trace_core`。

## 08. Versioning、Regression 与 Experiments

### 真实问题

Prompt、模型、chunk、retriever 和 workflow 都会变化。没有版本和回归，就无法安全迭代。

### 基础原理

- prompt version。
- dataset version。
- model config version。
- retriever config version。
- workflow graph version。
- experiment run。
- regression report。

### 最小实现

- 记录一次实验的配置和结果。
- 对比两个版本的指标差异。

### 主流框架实现

- JSON config。
- pytest regression。
- LangSmith experiments 认知。

### 失败分析与能力边界

- 改了配置但无法复现。
- 只看平均指标，忽略关键样本回退。
- 实验没有绑定数据集版本。

### 完成标准（运行与观察）

- regression pass rate。
- metric diff。
- failed sample diff。
- cost / latency diff。

### 本节实战

比较两个版本：

- 新 chunk 策略是否提高 source hit。
- 新 Prompt 是否降低 schema failure。
- 新多 Agent 流程是否提高风险覆盖。

### 本节沉淀

沉淀实验记录规范。

## 09. Cost、Latency 与 Metrics

### 真实问题

多 Agent 会增加调用次数。项目必须知道成本和延迟从哪里来。

### 基础原理

- token usage。
- model cost。
- retrieval latency。
- first token latency。
- total latency。
- agent step count。
- tool latency。
- workflow duration。

### 最小实现

- 记录每次模型调用 token 和耗时。
- 汇总一次评审的总成本和总耗时。

### 主流框架实现

- SDK usage。
- 自定义 metrics。
- Prometheus / dashboard 认知。

### 失败分析与能力边界

- 只记录总耗时，无法定位慢节点。
- 多 Agent 过度拆分导致成本失控。
- 缓存导致评估结果不可复现。

### 完成标准（运行与观察）

- 平均成本。
- P95 latency。
- Agent step count。
- token by role。

### 本节实战

为一次需求评审展示成本和耗时：

- 检索耗时。
- 每个 Agent 调用耗时。
- 工具耗时。
- 最终报告耗时。
- token 总量。

### 本节沉淀

进入项目质量面板。

## 10. LLM-as-Judge 与 Human Eval

### 真实问题

有些评审质量无法完全用规则判断，需要 LLM judge 和人工评审结合。

### 基础原理

- LLM-as-judge 的适用边界。
- rubric。
- pairwise comparison。
- human label。
- judge consistency。

### 最小实现

- 为评审报告设计评分 rubric。
- 用 LLM judge 和人工分别打分并对比。

### 主流框架实现

- RAGAS / judge prompt 认知。
- LangSmith evaluators 认知。
- 人工标注表。

### 失败分析与能力边界

- judge 偏好长答案。
- judge 会被无依据内容迷惑。
- judge 不能替代 citation 和 retrieval 指标。

### 完成标准（运行与观察）

- judge-human agreement。
- score variance。
- rubric coverage。

### 本节实战

为评审报告设计评分 rubric：

- 依据充分性。
- 风险覆盖度。
- 建议可执行性。
- 引用准确性。
- 追问合理性。

### 本节沉淀

建立人工评价与 LLM judge 的组合方式。

## 11. Feedback Loop

### 真实问题

用户反馈如果只是点赞点踩，就很难真正改进系统。

### 基础原理

- feedback type。
- user correction。
- missing source。
- wrong source。
- wrong risk。
- unclear report。
- accepted / rejected suggestion。
- 回流动作。

### 最小实现

- 为回答和报告添加反馈入口。
- 将反馈转为 bad case 或知识修复任务。

### 主流框架实现

- feedback table。
- annotation workflow。
- bad case board。

### 失败分析与能力边界

- 点赞点踩信息量太少。
- 用户反馈没有责任人和修复状态。
- 反馈没有进入回归集。

### 完成标准（运行与观察）

- feedback count。
- feedback type distribution。
- fix rate。
- regression pass rate。

### 本节实战

设计反馈入口：

- 标记引用错误。
- 标记风险遗漏。
- 标记建议不可执行。
- 补充正确材料。
- 创建 bad case。

### 本节沉淀

沉淀 feedback loop。

## 12. Engineering Contract Tests

### 真实问题

AI 质量工程之外，还需要普通工程保障：API、事件流、结构化输出和前端状态机的契约稳定，否则 eval 通过但集成仍频繁断裂。

### 基础原理

- API schema contract test（Pydantic / OpenAPI 一致）。
- SSE / event contract test（事件类型、必填字段、顺序）。
- Structured output schema test（ReviewReport 等回归）。
- Frontend state machine transition test。
- Workflow event replay test。

### 最小实现

- 为 review API 和 SSE 事件定义契约样例。
- 用 pytest 验证 schema 与事件结构。

### 主流框架实现

- pytest + Pydantic validation。
- 快照测试或 JSON schema 校验。
- 与 `06_ai_native` 状态机协议对齐。

### 失败分析与能力边界

- 契约测试不能替代 RAG / Agent 质量 eval。
- 契约过严会阻碍合理演进；需版本化契约。

### 完成标准（运行与观察）

- 契约测试通过率。
- 破坏性变更检出率。

### 本节实战

为需求评审助手建立最小契约集：review run API、SSE 事件、ReviewReport schema、核心状态转移。

### 本节沉淀

沉淀 `eval_core.contracts`，与 CI / 回归流程衔接。

## 13. 项目质量面板

### 真实问题

作品化项目需要展示质量闭环，但当前不需要做完整 LLMOps 平台。

### 基础原理

- RAG quality panel。
- Agent trajectory panel。
- Workflow trace panel。
- Bad case board。
- Cost / latency panel。
- Dataset run report。

### 最小实现

- 展示最近一次 eval run。
- 展示核心指标和失败样本。

### 主流框架实现

- Streamlit / simple web dashboard。
- 前端管理页。
- LangSmith dashboard 认知。

### 失败分析与能力边界

- 面板只有图表，没有修复动作。
- 指标太多导致无法行动。
- 平台化过早，掩盖项目质量问题。

### 完成标准（运行与观察）

- 面板指标是否对应项目风险。
- bad case 是否能追踪修复。
- 质量趋势是否可比较。

### 本节实战

为需求评审助手建立基础质量面板：

- 检索命中率。
- 引用正确率。
- 拒答准确率。
- 风险覆盖率。
- 工具调用成功率。
- 人工确认触发率。
- bad case 修复状态。

### 本节沉淀

`05_eval_observability` 的产物进入 `06_ai_native` 和 `07_projects`，作为作品化展示的重要部分。

## 参考设计映射

- 参考 MaxKB 的 ChatRecord、引用、token、反馈、节点详情和统计记录。
- 参考 RAGFlow 的 Search / Evaluation、检索评估、回答追踪和复杂 RAG 质量治理思路。
