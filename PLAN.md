# 需求评审助手工程实现方案

本文说明怎样在 `source/` 中实现 [SPEC.md](SPEC.md)。它是稳定的工程分解，不记录实时进度，不替代 `course/learning-path.md` 的学习顺序。

## 1. 代码结构

```text
source/
├── packages/
│   ├── llm_core/
│   ├── rag_core/
│   ├── agent_core/       # 真实需要时建立
│   └── eval_core/        # 真实需要时建立
├── demos/                # 机制实验代码
├── apps/
│   └── review_assistant/ # 唯一产品
└── python_base/
```

每个能力域只维护一个 package。demo 和产品通过 import 复用，不复制实现。

## 2. 第一阶段实现顺序

```text
LLM 调用与结构化输出
→ 文档解析、Chunk 与 Metadata
→ Lexical / Dense Retrieval
→ RRF 与 Retriever Contract
→ Context 与可信生成
→ Citation、证据充分性与 Refusal
→ Review API
→ Web 工作台
→ Golden Set 与固定对照
```

第一阶段结束时，Retriever 必须可以作为稳定 Tool 被第二阶段直接调用。

## 3. 第二阶段实现顺序

```text
Agent Harness
→ Tool Schema 与 Tool Runtime
→ Retriever as Tool 与 Agent Loop
→ MCP、通用 Tool 与 Agent Skills
→ Conversation、事件和运行界面
→ Deep Research
→ Multi-Agent 与 A2A
→ 必要 Workflow
→ Trace、Regression 与 Feedback
```

该顺序是工程依赖关系，不是第二套课程编号。

## 4. Package 边界

### `llm_core`

负责模型 Provider、Prompt、Structured Output、Context、Calling Harness、成本和基础事件，不承载产品业务流程。

### `rag_core`

负责解析、Chunk、Embedding、Lexical / Dense Retrieval、RRF、Retriever Contract、Context 适配、可信生成和证据校验。

### `agent_core`

在第二阶段真实实现开始时建立，负责 Agent Harness、Tool Runtime、Agent Loop、状态、MCP 适配、Skills、Research、Multi-Agent 与必要 Workflow 原语。

### `eval_core`

在跨产品复用需求成立时建立，负责数据集、运行记录、评估器、回归和反馈模型；仅有产品局部逻辑时先留在产品内。

## 5. 产品边界

`source/apps/review_assistant/` 负责：

- FastAPI 和产品服务。
- Web 工作台。
- 产品 Schema、状态和组合流程。
- 产品测试、fixtures、eval 和数据库 migration。
- 安装、配置、运行和部署。

通用算法进入 package，产品业务取舍留在 app。

## 6. 实验边界

`source/demos/` 只用于观察机制、对照变量和稳定复现失败。实验操作教材位于 `course/labs/`；demo README 只维护代码入口和测试索引。

## 7. 实现准入

新增能力前依次确认：

1. 它解决 SPEC 中哪个真实问题。
2. 最简单结构是否足够。
3. 通用能力还是产品取舍。
4. 输入、输出、状态、错误和权限是否明确。
5. 怎样用实验、测试或评估证明。

没有真实职责和收益证据时，不提前建立 Multi-Agent、完整 Workflow、平台化连接器或评估平台。

## 8. 验证要求

- 主路径使用真实模型与真实外部服务。
- 单元测试只证明确定性契约。
- 集成测试验证数据库、Provider 或协议边界。
- 固定数据集比较质量、成本和延迟。
- 重要变更同步更新 SPEC、项目篇、产品 README、测试和评估样例中真正受影响的真源。
