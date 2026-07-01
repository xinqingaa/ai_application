# 05. Context Engineering

> 04 已经把流式 token、事件协议和 conversation history 分开。本篇回答：**下一次模型调用到底应该带哪些材料**，以及如何在有限预算内保留需求、证据、历史和中间结论的边界。

---

## 真实问题

到 04 为止，需求评审助手已经能完成一次调用、Prompt 版本化、结构化输出和流式展示。但这些能力都有一个共同前提：模型收到的 `messages` 是正确的。真正进入项目时，`messages` 不再只是一个 user 字符串，而会混入 PRD、业务规则、接口文档、历史评审、上一轮对话、RAG 召回片段、Agent 中间结论和 Workflow 状态。

如果没有 Context Engineering，后续系统会自然滑向两个极端：要么把能拿到的材料全部塞进 Prompt，导致成本高、噪声大、模型忽略关键证据；要么只塞当前用户问题，导致模型凭常识补全接口、状态机和业务规则。两者在 demo 里可能都能生成“看起来合理”的回答，但一旦进入需求评审，问题会变得很真实：模型引用了没有进入上下文的规则，前端展示了无法溯源的风险，评估脚本也无法判断坏结果到底是检索没命中、上下文被裁掉，还是 Prompt 没约束好。

### 学习者真实问题

如果你有前端 / Flutter / 客户端背景，上下文很容易被理解成“聊天历史”或“Prompt 里的材料”。这个理解太窄。AI 应用里的 context 更像一次运行前的**输入装配层**：它决定哪些信息被模型看见，哪些信息被丢弃，哪些信息只用于 UI 或 trace，哪些信息可以成为最终答案的依据。

前端开发里也有类似经验：一个页面不会把所有接口返回、埋点日志、调试信息和缓存状态都塞进一个组件 props；你会区分页面主数据、派生状态、临时状态、错误状态和调试信息。Context Engineering 做的是同一类事，只是对象变成了模型调用。模型没有真正的“背景知识管理器”，它只看本次输入窗口。窗口里放错材料，后面再强的结构化输出、流式 UI 或 Agent loop 都会被污染。

本节要建立的直觉是：**上下文不是越多越好，而是越可控越好**。Context Builder 的价值不是把长文本压进窗口，而是让应用能回答：这次调用用了哪些 source？为什么这条证据进了 Prompt、另一条没有？如果模型没有引用关键材料，我应该查检索、预算、排序，还是 Prompt？

### 产品真实问题

产品同学小周继续评审 S2：订单详情页新增「申请售后」按钮，对接售后接口 v2。前几节里，我们把 PRD 和静态 `evidence_s2.json` 一起交给模型，模型可以输出风险列表。现在评审负责人提出一个很自然的要求：下次不只看这一段接口说明，还要参考订单状态机、客户端展示规则、历史评审里类似售后入口的坑，以及上一轮会议中人工补充的限制。

第一次尝试时，后端把这些材料简单拼接：

```text
PRD + 历史对话 + 接口说明 + 状态机 + 会议纪要 + 模型上一轮输出
```

结果模型确实“知道得更多”，但风险列表反而变糊了。它把上一轮模型的半成品当成事实，把历史评审里的旧接口规则套到新接口 v2 上，还引用了一个前端页面根本看不到的材料片段。产品侧看到的是：AI 很勤奋，但依据不可信。

这说明需求评审助手需要一层上下文规则：当前 PRD 永远优先；业务规则和接口片段要带 source id；历史对话只能保留稳定结论，不能把 token delta 或错误日志塞进去；Agent 中间结果只能用结构化摘要；预算不足时宁可丢低优先级证据，也不能静默截断 source id。这样模型输出风险时，前端和评估才知道它到底基于哪些材料。

### 工程真实问题

工程上，Context Engineering 至少要拆开五件事：

| 概念 | 解决什么 | 本节边界 |
| --- | --- | --- |
| 当前任务 | 本轮用户真正要模型处理什么 | `requirement_text` 永远保留 |
| 证据片段 | 可作为依据的外部材料 | `ContextSource` + source id |
| 会话历史 | 稳定的 user / assistant 最终消息 | 04 已有 `ConversationBuffer`，05 只讲预算边界 |
| 中间结果 | 检索、工具、Agent、Workflow 的过程产物 | 本节只说明压缩原则，真实 runtime defer |
| 预算诊断 | 为什么某些材料进了或没进 Prompt | `included_sources` / `dropped_sources` |

这里最容易错的是把“能看到”误认为“可作为依据”。UI 可以展示流式 token、trace、工具日志和错误信息，但这些不一定应该进入下一次模型调用。Context Builder 的职责就是在调用边界前做一次取舍，让模型只看到当轮任务真正需要的材料。

---

## 基础原理

### 本节方案性质

Context Engineering 没有唯一标准答案。长文本摘要、RAG context compression、Conversation memory、Agent scratchpad、Workflow state 都是上下文工程的一部分，但它们不应在 02_llm 阶段一次做完。本节只落一个最小工程实践：**把当前需求和带编号证据片段构造成 Prompt 变量，并记录预算诊断**。

需要区分四层：

| 层级 | 本节怎么理解 |
| --- | --- |
| **通用原则** | 上下文要分层；当前任务优先；证据必须可追溯；预算不足要可见；中间过程不能直接污染 history |
| **工程实践** | 用 `ContextSource` 表示可追溯片段，用 `build_review_context` 统一组装 `requirement_text` 与 `evidence_block` |
| **项目取舍** | 本节复用静态 `evidence_s2.json`，按 source 粒度保留或丢弃，不做真实 RAG 和自动摘要 |
| **非目标** | 不把本节的 source-level 裁剪当作完整 RAG compression；不把 token 估算当作供应商精确计费 |

也就是说，本节不是要设计一个完整 memory 系统，而是先让需求评审助手具备最小上下文边界：材料进入模型前有编号、有优先级、有预算、有诊断。

### Context Engineering 是什么

**输入**：当前需求文本、可追溯 source 列表、预算、模型名。  
**输出**：Prompt 可直接使用的变量，以及上下文诊断。

在本节代码里，输出落成 `BuiltContext`：

- `requirement_text`：当前 PRD / 用户需求。
- `evidence_block`：格式化后的证据块，带 source id。
- `included_sources`：进入 Prompt 的 source。
- `dropped_sources`：因为预算等原因没进入 Prompt 的 source。
- `estimated_tokens`：本次上下文材料的估算 token。
- `token_budget`：本次材料预算。

注意：这里的 `token_budget` 不是模型完整上下文窗口，也不是最终回答 token 上限。它只是本项目当前阶段对**插入材料**的本地预算。完整调用还包括 system prompt、任务说明、JSON schema、模型输出等，这些会在 07 harness 与 08 成本延迟里继续统计。

### 为什么不能只靠模型 context length

`models.yaml` 里 `chat.dev_chat` 声明了 `context_length: 128000`。这不等于每次都应该塞 12 万 token。

大窗口解决的是“装得下”，不是“用得好”。需求评审里，关键问题通常不是窗口不够，而是上下文里混入了太多相似、过期或不该作为依据的材料。模型可能把低优先级历史案例看得比当前 PRD 更重，也可能在一堆片段里忽略真正需要引用的接口约束。

所以 Context Engineering 的第一原则不是追求塞满窗口，而是明确优先级：

```text
当前需求 > 明确命中的业务规则 / 接口片段 > 稳定历史摘要 > Agent 中间摘要 > 原始过程日志
```

本节最小实现只处理前两层：当前需求和静态 evidence。后续 RAG 会负责从知识库生产 evidence，Agent / Workflow 会负责生产结构化中间摘要，但它们都应该进入同一类 context builder，而不是各自拼字符串。

### 证据上下文必须可追溯

Structured Outputs 在 03 已经有 `Citation(source_id, excerpt)`。如果 Prompt 里的 evidence 没有稳定编号，模型就算输出了 `source_id`，应用也很难判断它指向哪里。

因此本节的 evidence block 不是普通段落，而是带编号的 source：

```text
[S2.evidence.after_sale_api_v2] 内部接口说明摘录
metadata: sample_id=S2
售后接口 v2 路径：POST /api/after-sale/v2/cases；...
```

source id 的价值不只在最终引用。它还让调试路径变短：如果模型没有提接口 v2，可以先看这条 source 是否进入 `included_sources`；如果没进，再看预算和优先级；如果进了但模型没用，再看 Prompt 约束或模型能力。没有 source id 时，这些问题都会退化成“模型不稳定”。

### 从弱到强的机制递进

**第 1 步 · 只放用户问题**

模型只看到“这个需求有什么风险”。实现最简单，但会大量依赖常识和猜测。**反例**：PRD 没写接口版本，模型却编造一个接口迁移风险。

**第 2 步 · 把 PRD 全文塞进 Prompt**

模型至少看到了当前材料，但长 PRD 会增加成本，也容易让关键条款淹没在背景说明里。**反例**：PRD 有十页，真正关键的订单状态约束只出现一次，模型生成时漏掉。

**第 3 步 · Prompt 变量分层**

像 02 一样拆成 `requirement_text` 与 `evidence_block`。模型知道哪部分是用户需求，哪部分是证据。**仍遗留**：evidence 从哪里来、怎么编号、预算不足时怎么丢？

**第 4 步 · ContextSource + 预算诊断**

每个证据片段有 `source_id`、类型、优先级和内容。Builder 决定哪些 source 进入 Prompt，并记录被丢弃的 source。**仍遗留**：当前只按 source 粒度保留或丢弃，不做句子级压缩。

**第 5 步 · RAG / compression / memory**

后续 RAG 会把真实检索结果变成 source；context compression 会压缩片段；Agent memory 会把长期信息摘要化。本节只要求能判断它们未来应该接入哪里：都应该先变成可追溯、可预算的 context 单元，再进入 Prompt。

这条链的关键是：Context Engineering 不是 Prompt Engineering 的替代品。Prompt 规定任务和约束，Context Builder 决定材料来源和取舍，Schema 校验输出形状，RAG / Agent 生产更多候选材料。

### 与 Conversation 的边界

04 的 `ConversationBuffer` 只保存稳定 user / assistant 消息。05 继续强化这个边界：history 不是上下文垃圾桶。

进入 context 的可以是：

- 用户当前需求。
- 上一轮最终 assistant 结论的摘要。
- 人工确认过的补充信息。
- RAG 命中的业务规则。

不应直接进入 context 的是：

- 流式 `token.delta`。
- `message_start` / `done` 事件。
- 错误栈。
- 工具原始日志。
- Agent scratchpad 的推理噪声。

这些内容可以进入 trace 或 UI 时间线，但不能默认成为下一次模型调用的事实依据。否则模型会把“运行过程”误当成“业务事实”。

### 本节数据流

```text
S2 PRD 样例
→ evidence_s2.json
→ ContextSource(source_id, title, content, priority)
→ build_review_context(token_budget=900)
→ variables = {requirement_text, evidence_block}
→ risk_review_v4.yaml
→ LLMClient.chat_structured
→ ReviewRiskList / error_stage
```

与 03 相比，本节没有改变结构化输出的契约，只改变 Prompt 变量的来源：`evidence_block` 不再是随手传入的字符串，而是由 context builder 生成。

---

## 最小实现

本节最小实现要验证两件事：

1. evidence 进入 Prompt 前有 source id 与预算诊断。
2. 现有结构化调用不需要关心 evidence 来自静态文件还是未来 RAG。

正文只保留三个关键片段，完整阅读顺序见 [llm_core README](../../source/packages/llm_core/README.md) 和 [demo README](../../source/demos/02_provider_switching/README.md)。

### 1. 可追溯 source

[`context.py`](../../source/packages/llm_core/context.py)：

```python
@dataclass(frozen=True)
class ContextSource:
    source_id: str
    content: str
    source_type: ContextSourceType = "evidence"
    title: Optional[str] = None
    priority: int = 50
    metadata: dict[str, str] = field(default_factory=dict)
```

`ContextSource` 的重点是把“材料”从普通字符串变成有身份的片段。`source_id` 用于引用和调试，`source_type` 用于区分 evidence / history / agent_summary，`priority` 用于预算不足时排序。

本节没有引入复杂继承或框架对象，因为当前只需要一个可读、可测试、可被 RAG 复用的最小单元。

### 2. Context Builder

[`context.py`](../../source/packages/llm_core/context.py)：

```python
def build_review_context(
    *,
    requirement_text: str,
    sources: Sequence[ContextSource] = (),
    token_budget: int = 1200,
    model: Optional[str] = None,
) -> BuiltContext:
    requirement = requirement_text.strip()
    total_tokens = estimate_tokens(requirement, model=model)

    for source in _dedupe_sources(sources):
        formatted = format_context_source(source)
        source_tokens = estimate_tokens(formatted, model=model)
        if total_tokens + source_tokens <= token_budget:
            included.append(source)
            total_tokens += source_tokens
        else:
            dropped.append(DroppedContextSource(...))
```

这里有三个取舍：

- 当前需求文本必须保留，不因为预算不足被静默丢弃。
- evidence 按 source 粒度进入或丢弃，不在本节做半截截断，避免 source id 与内容不一致。
- 被丢弃的 source 进入 `dropped_sources`，让调试和后续评估知道缺了什么。

`estimate_tokens` 使用 `tiktoken` 做本地估算；失败时退回粗估。它服务的是预算决策，不等价于供应商最终账单。

### 3. 复用结构化风险入口

[`structured_risk.py`](../../source/demos/02_provider_switching/structured_risk.py)：

```python
evidence_sources = [
    ContextSource(
        source_id=f"{SAMPLE_ID}.evidence.after_sale_api_v2",
        source_type="evidence",
        title="内部接口说明摘录",
        content=load_evidence_block(EVIDENCE_FILE),
        priority=80,
        metadata={"sample_id": SAMPLE_ID},
    )
]
context = build_review_context(
    requirement_text=sample["user_content"],
    sources=evidence_sources,
    token_budget=CONTEXT_TOKEN_BUDGET,
    model=config.model,
)
variables = context.to_prompt_variables()
```

这段改造很小，但意义明确：03 的结构化链路仍然使用 `render_prompt` 与 `chat_structured`，只是变量来源从“直接拼字符串”变成“context builder 输出”。后续真实 RAG 接入时，只要把检索结果转换成 `ContextSource`，Prompt 和 Schema 都可以继续复用。

---

## 主流框架实现

| 方式 | 做什么 | 与本节关系 |
| --- | --- | --- |
| LangChain document formatting | 把 `Document(page_content, metadata)` 格式化进 Prompt | 可映射为 `ContextSource` |
| map-reduce / refine 摘要 | 长文档分块总结，再逐步合并 | 适合长 PRD 或报告，不在本节实现 |
| Contextual compression retriever | 检索后按问题压缩 chunk | 03_rag 深化，本节只保留 source-level 裁剪 |
| Conversation memory | 多轮对话裁剪、摘要、长期记忆 | 04 只做 buffer；更完整 memory 后续再做 |
| LangGraph state | Workflow 节点状态进入后续节点 | 04_agent / Workflow 再展开 |

真正要迁移的不是某个框架类名，而是分层原则：候选材料先有 source、metadata 和优先级，再由 builder 决定进入 Prompt 的最终形态。

---

## 失败分析与能力边界

### 1. 模型没有引用关键证据

- **表现**：S2 风险结果没有提售后接口 v2 或订单状态机。
- **原因**：证据没进入 Prompt，或进入了但 Prompt 没要求依据绑定。
- **怎么验证**：先看 demo 的 `[context] included_sources` 是否包含 `S2.evidence.after_sale_api_v2`；再看 verbose 下 `messages` 的 `Evidence` 段。

### 2. 引用 source id 不存在

- **表现**：结构化结果里的 `citations.source_id` 指向一个 Prompt 中没有的 id。
- **原因**：模型编造 citation，或 evidence block 没有稳定编号。
- **怎么验证**：对照 `context.included_source_ids`；本节只让 source id 可见，citation 真伪校验 defer 到 `03_rag`。

### 3. 上下文预算太小导致证据被丢

- **表现**：`[context] dropped_sources` 非空，模型只能基于 PRD 泛化分析。
- **原因**：`CONTEXT_TOKEN_BUDGET` 小于需求 + evidence 的估算总量，或低优先级 source 排在后面。
- **怎么验证**：调大 `CONTEXT_TOKEN_BUDGET` 或提高关键 source 的 `priority`，观察 `included_sources` 是否变化。

### 4. 上下文过多反而质量下降

- **表现**：模型输出覆盖很多无关风险，或把历史案例套到当前需求。
- **原因**：把低相关历史、过程日志、旧 Agent 结论都塞进 Prompt。
- **怎么验证**：减少 source，只保留当前 PRD 与一条 evidence；若结果更贴材料，说明噪声上下文在干扰。

### 5. Token 估算与真实 usage 不一致

- **表现**：`estimated_tokens` 与 API 返回 `usage.prompt_tokens` 不完全相等。
- **原因**：本地估算只计算插入材料；真实调用还包含 system prompt、任务说明、schema、消息包装和供应商 tokenizer 差异。
- **怎么验证**：把 `estimated_tokens` 当预算参考，不当账单；真实成本基线放到 08。

### 常见误区

| 误区 | 纠正 |
| --- | --- |
| 「模型窗口很大，所以不用做 context」 | 大窗口只解决装得下，不解决相关性和可追溯 |
| 「history 就是 context」 | history 只是 context 候选之一，且只能保存稳定消息 |
| 「裁剪就是截断字符串」 | 本节按 source 粒度丢弃，避免半截证据造成引用错乱 |
| 「Context Builder 能替代 RAG」 | Builder 只组装材料；真实材料生产由 RAG / Tool / Agent 提供 |
| 「估算 token 就是成本统计」 | 估算用于预算；真实成本统计在 08 |

### 本节不做（defer）

| 能力 | 目标节 | 当节最小判断 |
| --- | --- | --- |
| 真实向量检索、chunk、rerank | 03_rag | evidence 先用静态 source 模拟 |
| citation 是否真实命中 source | 03_rag | 本节只保证 Prompt 中有 source id |
| 自动摘要、context compression | 03_rag / 后续 | 知道 source-level 裁剪的边界 |
| Agent scratchpad / tool result 管理 | 04_agent | 中间过程必须压缩成结构化摘要后再进 context |
| 调用记录落盘与样例回归 | 07 | 当前只打印 `[context]` 诊断 |
| 成本、延迟、缓存 | 08 | 当前只估算插入材料 token |

---

## 本节实战

### 目标

为需求评审助手增加最小 Context Builder：在 S2 结构化风险审查前，把 PRD 与 evidence 转成带 source id 的上下文变量，并打印预算诊断。

### 涉及文件

关键路径：

- [`source/packages/llm_core/context.py`](../../source/packages/llm_core/context.py)：上下文 source、预算估算、构造结果。
- [`source/demos/02_provider_switching/structured_risk.py`](../../source/demos/02_provider_switching/structured_risk.py)：复用结构化风险 demo，新增 context 诊断。
- [`source/packages/llm_core/tests/test_context.py`](../../source/packages/llm_core/tests/test_context.py)：离线上下文构造测试。
- [`source/packages/llm_core/README.md`](../../source/packages/llm_core/README.md)：代码阅读顺序。
- [`source/demos/02_provider_switching/README.md`](../../source/demos/02_provider_switching/README.md)：运行与输出观察说明。

完整参数与输出字段见 demo README；课程正文只保留主路径。

### 实现步骤

1. `evidence_s2.json` 读取静态 evidence。
2. evidence 变成 `ContextSource(source_id="S2.evidence.after_sale_api_v2", priority=80, ...)`。
3. `build_review_context` 根据 `CONTEXT_TOKEN_BUDGET` 生成 `requirement_text` 与 `evidence_block`。
4. `render_prompt(risk_review_v4, variables)` 继续渲染结构化风险 Prompt。
5. `client.chat_structured(...)` 继续比较三种 `structured_mode`。

### 运行方式

离线测试：

```bash
.venv/bin/pytest source/packages/llm_core/tests/test_context.py
```

需要真实模型调用时：

```bash
cd source/demos/02_provider_switching
../../../.venv/bin/python structured_risk.py
```

如果当前 shell 已激活 `.venv`，也可以运行：

```bash
python structured_risk.py
```

### 预期结果

`structured_risk.py` 会先打印 `[experiment]`，然后打印 `[context]`：

```text
[context]
  [token_budget] 900
  [estimated_tokens] ...
  [included_sources] S2.evidence.after_sale_api_v2
  [dropped_sources] —
```

之后继续输出 `prompt_only`、`json_mode`、`json_schema` 三个结构化结果块。Context Engineering 的观察重点不是哪种 mode 最好，而是：模型生成前，关键 evidence 是否已经带 source id 进入 Prompt。

---

## 完成标准

- 能解释 context、Prompt、Conversation history、RAG evidence 的区别。
- 能说明为什么当前需求必须优先于历史和中间结果。
- 能解释 `ContextSource.source_id` 对 citation、前端展示和调试的价值。
- 能运行 `test_context.py`，并理解 included / dropped source 的判断。
- 能运行或阅读 `structured_risk.py` 的 `[context]` 输出，判断 evidence 是否进入 Prompt。
- 能说出本节没有解决真实检索、引用真伪校验、自动摘要、成本统计。

### 运行与观察

```bash
.venv/bin/pytest source/packages/llm_core/tests/test_context.py
cd source/demos/02_provider_switching
../../../.venv/bin/python structured_risk.py
```

观察点：

- `[context] included_sources` 是否包含 `S2.evidence.after_sale_api_v2`。
- `[context] dropped_sources` 是否为空。
- verbose 下 `messages` 的 Evidence 段是否带 source id。
- 结构化输出的 `citations.source_id` 是否倾向于引用已进入 Prompt 的 source。
- 调小 `CONTEXT_TOKEN_BUDGET` 后，是否能看到 source 被 drop。

### 自检题

1. 为什么不能把 RAG 召回片段、conversation history、tool logs 全部直接拼进 user message？
2. `context_length` 很大时，为什么仍然需要 context budget？
3. `token.delta` 为什么不应该进入下一轮 context？什么内容可以进入？
4. 如果模型输出了不存在的 `source_id`，你会先查 `ContextSource`、Prompt、还是 Schema？为什么？
5. 本节的 `estimated_tokens` 与 API 返回的 `usage.prompt_tokens` 为什么可能不同？
6. 后续接入真实 RAG 时，检索结果应该如何接到本节的 `ContextSource`？

---

## 本节沉淀

- `llm_core` 新增 `context.py`：`ContextSource`、`BuiltContext`、`build_review_context` 与预算诊断。
- 需求评审助手获得：**当前需求 + 可追溯 evidence + token budget** 的最小上下文构造能力。
- 下一节 06 Reliability、Errors 与 Degradation 将处理模型调用失败、结构化失败、超时和降级，而不是继续扩大上下文。

---

## 相关专题

- 上一篇：[04_streaming_and_conversation.md](04_streaming_and_conversation.md)
- 下一篇：06 Reliability、Errors 与 Degradation（待落地）
- 课程大纲：[outline.md](outline.md)
