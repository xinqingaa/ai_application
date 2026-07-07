# 08. Cost、Latency 与 Caching

> 07 已经让同一批需求评审 case 可以被 harness 批量运行，并记录成功、失败、parse、fallback 和 attempt。本节继续回答：**当模型调用从“能回归”进入“要长期可用”后，应用如何看懂 token、成本、延迟和缓存边界，避免 AI 链路越做越慢、越做越贵、越做越不可控**。

---

## 真实问题

前面几节已经把需求评审助手的 LLM 调用做成了一个比较像应用底座的形态：有 provider 抽象，有 Prompt 版本，有结构化输出，有上下文装配，有可靠调用，也有 harness。到这里，你已经不只是“调一次模型接口”，而是在逐步构建后续 RAG、Agent、Workflow 都会复用的模型调用层。

新的问题是：系统越完整，调用就越容易变贵、变慢。

一开始，用户只输入一句“订单详情页新增申请售后入口”，模型生成一组风险。后来你加入更完整的需求材料、业务规则、历史评审片段、接口说明和多端约束；再后来，系统可能先做需求摘要，再做风险识别，再生成追问，再汇总报告。每一步都可能多一次模型调用，每次调用又会带上更多上下文。表面上看，功能只是“更聪明了”；实际上，token、延迟、重试、fallback 和重复评审的成本都在增长。

想象一个具体场景：产品同学上传一份 PRD，前端正在显示“正在分析风险”。第一次版本只跑一个结构化评审，3 秒内返回。你为了提高质量，加了业务规则上下文，结果 prompt tokens 翻倍；又为了稳定 parse，加了重试和 fallback，偶发情况下会多调一次模型；再为了拆清职责，把“风险识别、测试关注点、报告生成”拆成三个步骤。现在同一份材料评审可能要十几秒，用户反复点“重新生成”还会重复消耗额度。如果没有成本、延迟和缓存记录，你只能看到最终文本，不知道慢在哪里、贵在哪里，也不知道哪些重复调用其实可以安全复用。

本节默认使用真实模型运行 demo。因为成本、延迟、usage 字段、供应商兼容差异、schema 支持情况和偶发错误，本来就是 LLM 应用工程的一部分。如果长期只看 fake 输出，你会误以为所有模型都会稳定返回 usage、稳定支持 JSON、稳定在 1ms 内完成调用；这恰好避开了最该学习的真实边界。fake 只保留给单元测试、离线排查和稳定复现 cache hit / miss。

### 学习者真实问题

如果你来自前端或 Flutter，成本和延迟可以类比成页面性能与接口预算。一个页面“能打开”不代表它体验可用；你还会看首屏时间、接口耗时、缓存命中、重复请求、弱网表现。LLM 调用也是一样：一次模型回答“看起来不错”，不代表它适合被放进产品链路。你需要知道这次调用用了多少 token、耗时多少、有没有 retry / fallback、同样输入下能不能复用结果。

### 产品真实问题

需求评审助手不能只追求“回答更完整”。如果用户上传一份材料后等待太久，或者每次切换页面回来都重新评审，产品体验会很差。尤其在后续 RAG 和 Agent 阶段，系统会引入检索、补检索、工具调用、报告汇总和人工确认；如果没有调用预算意识，产品会很快从“可演示”变成“不可日常使用”。

### 工程真实问题

工程上，本节要解决的是最小调用治理闭环：

```text
HarnessRunRecord
→ token / latency / estimated cost
→ cache key / cache hit / cache miss
→ 一批 case 的成本延迟基线
```

这里的重点不是做完整 FinOps，也不是接入线上 APM 或 Redis，而是先把成本、延迟和缓存边界沉淀进 `llm_core`，让后续课程继续复用同一套诊断字段。

---

## 基础原理

### Usage 是事实，价格是配置，账单是外部系统

模型 SDK 返回的 `usage` 通常会告诉你 prompt tokens、completion tokens 和 total tokens。它是一次调用的 token 事实，但它还不是成本本身。

成本至少还取决于：

- 当前模型的输入 token 单价。
- 当前模型的输出 token 单价。
- 供应商是否有缓存、批处理、阶梯价或特殊计费规则。
- 请求是否发生 retry / fallback。
- 一次业务任务到底包含几次模型调用。

所以本节在 `llm_core.costing` 中做的是**学习用估算**，不是供应商真实账单。真实项目必须把当前价格作为配置输入，并定期和供应商账单对齐。

如果真实模型没有返回 `usage`，应用不应该编一个数字。正确做法是把成本估算标记为 unknown，同时保留 latency、model、config_ref、parse、error 等其他事实。unknown 本身就是一个诊断信号：它说明当前供应商或兼容平台没有给出足够的计费事实，后续做成本面板时必须补采集或换计费口径。

一个反例：你看到某条 record 的 `total_tokens=1500`，就直接认为它“很便宜”。但如果它来自一个多步骤评审链路，前面还有 4 次检索改写和 2 次报告汇总，那么这条 record 只是整次任务的一部分。排查时应先确认“这条调用属于哪个任务步骤”，再看整条链路的调用次数。

### 延迟不只是一段等待时间

07 的 harness 已经记录了 `latency_ms`。08 要继续把它放进批量视角里看：

- 单条调用 latency：这一次模型响应花多久。
- average latency：一批 case 的平均耗时。
- max latency：最慢的一条 case。
- retry / fallback 隐含耗时：06 的 attempt report 能告诉你是不是重试放大了延迟。
- cache hit 节省耗时：重复输入命中缓存时，理论上可以少等一次模型调用。

流式首 token 时间已经在 04 建立概念；本节重点放在非流式结构化调用和 batch harness 的成本延迟基线上。

### 缓存不是“把问题和答案存起来”

缓存最容易被误解成：

```text
用户输入文本 -> 模型结果
```

这在需求评审里非常危险。因为同一句需求，在不同 Prompt 版本、不同模型、不同 schema、不同证据上下文下，都可能得到不同结论。

更安全的 cache key 至少要包含：

| 维度 | 为什么需要 |
| --- | --- |
| `config_ref` / model | 模型变化会改变输出质量和格式 |
| messages hash | 用户输入和系统指令变化必须 miss |
| prompt id / version | Prompt 改版后旧结果不能复用 |
| structured mode / schema version | 输出契约变化后旧结果可能不可用 |
| temperature | 采样策略变化会影响结果稳定性 |
| context fingerprint | 证据、规则、引用材料变化后必须重新评审 |

本节只做进程内 exact-match cache。它的目标是让你看懂缓存边界，不是提供生产缓存系统。检索缓存放到 RAG 阶段，任务状态缓存和持久化缓存放到后续 AI Native / 项目阶段。

### 从弱到强的机制递进

| 阶段 | 解决什么 | 仍然遗留什么 |
| --- | --- | --- |
| 只看最终文本 | 知道模型有没有回答 | 不知道 token、耗时、fallback |
| 记录 usage / latency | 知道单次调用事实 | 不知道一批 case 的总成本 |
| 汇总 harness summary | 知道批量基线 | 不知道重复调用能否复用 |
| exact-match cache | 避免同配置同上下文重复调用 | 不能处理语义相似、权限变化、证据变化 |
| 后续 eval / observability | 判断质量、成本和线上趋势 | 进入 05_eval_observability |

本节只做到第四步。语义缓存、分布式缓存、预算告警和线上成本面板都不是 02_llm 的目标。

### 方案性质说明

| 层级 | 本节怎么理解 |
| --- | --- |
| 通用原则 | 成本、延迟、缓存命中必须可见；缓存不能绕过证据、schema 和质量校验 |
| 工程实践 | 用 `HarnessRunRecord` 承载 token / latency / estimated cost，用 `CacheKeyParts` 构造 exact-match key |
| 项目取舍 | 先用学习价格表和 in-memory cache，服务需求评审助手的本地学习闭环 |
| 非目标 | 不把本节实现当作行业标准缓存系统，不接 Redis，不做线上账单对账 |

---

## 最小实现

本节的最小实现遵守一个原则：**成本和缓存进入 `llm_core`，demo 只负责观察**。

### 成本估算为什么独立成 `costing`

[`costing/estimate.py`](../../source/packages/llm_core/costing/estimate.py) 接收 `TokenUsage`，输出一个 `CostEstimate`。usage 缺失时，它不会抛错，而是返回 unknown。

```python
def estimate_usage_cost(
    usage: Optional[TokenUsage],
    *,
    config_ref: Optional[str] = None,
    model: Optional[str] = None,
    price_table: Optional[PriceTable] = None,
) -> CostEstimate:
    if usage is None:
        return CostEstimate(
            prompt_tokens=None,
            completion_tokens=None,
            total_tokens=None,
            input_cost=None,
            output_cost=None,
            total_cost=None,
        )
```

这样设计是为了避免把“供应商没有返回 usage”误处理成应用崩溃。对学习 demo 来说，unknown 比报错更有价值：它提醒你这条调用缺少成本事实，后续不能拿它做预算判断。

价格表放在 [`costing/pricing.py`](../../source/packages/llm_core/costing/pricing.py)，并明确标记为 `learning_estimate`。这不是最新官方价格，也不是账单真源。

### Harness record 如何接入成本字段

07 的 `HarnessRunRecord` 已经记录了 `total_tokens` 和 `latency_ms`。08 在 [`harness/records.py`](../../source/packages/llm_core/harness/records.py) 中继续补充：

- `prompt_tokens`
- `completion_tokens`
- `estimated_cost`
- `cost_estimate_known`
- `cache_hit`

这样 summary 就能回答：

```text
这一批 case 总共用了多少 token？
估算成本是多少？
平均延迟和最大延迟是多少？
缓存命中率是多少？
```

这些仍然是工程健康信号，不是业务质量评分。

### Cache key 为什么必须显式构造

[`cache/keys.py`](../../source/packages/llm_core/cache/keys.py) 中的 `CacheKeyParts` 把影响模型结果的因素显式列出来：

```python
@dataclass(frozen=True)
class CacheKeyParts:
    config_ref: str
    messages: list[dict[str, str]]
    model: Optional[str] = None
    prompt_id: Optional[str] = None
    prompt_version: Optional[str] = None
    structured_mode: Optional[str] = None
    schema_version: Optional[str] = None
    temperature: Optional[float] = None
    context_fingerprint: Optional[str] = None
```

这里最关键的是 `context_fingerprint`。在需求评审助手里，最终结论必须依赖当前材料和证据。如果业务规则、接口文档或历史评审片段变了，即使用户输入没有变，也应该 cache miss。

### Demo 如何验证这个机制

[`cost_latency_cache.py`](../../source/demos/02_call_ops_lab/cost_latency_cache.py) 做三轮观察：

```text
cold：第一次运行，同一批 case 全部 miss，产生 token / cost / latency。
repeat_same_input：同配置同上下文重复运行，全部 hit，节省 token / cost / latency。
changed_context：只改 context_fingerprint，必须全部 miss。
```

这三轮不是为了证明缓存“很厉害”，而是为了建立判断：什么时候能省，什么时候必须重新生成。

---

## 主流框架实现

OpenAI 兼容 SDK 会返回 `usage` 字段，但它不负责你的业务预算。应用侧仍然要决定：一次任务有几次调用、调用属于哪个步骤、失败后是否重试、fallback 是否可接受、价格如何配置。

LangChain / LangSmith 可以把 run、token、latency、cache 和 trace 组织成更完整的观测系统。它们适合后续做 eval 和 observability，但本节不把 `llm_core` 迁移到框架。原因很简单：02_llm 的目标是先理解调用治理的最小对象，而不是把问题交给平台隐藏起来。

Redis 或其他分布式缓存解决的是生产部署问题：跨进程共享、TTL、命名空间、权限隔离、失效策略和容量管理。本节只做 in-memory cache。它一重启就消失，正好适合作为学习实验。

Provider-side prompt caching 也只做认知。供应商缓存能降低某些重复前缀成本，但它不能替代应用侧 cache key，也不能保证业务结论在证据变化后自动失效。

---

## 成本与延迟排查路径

当你发现一次需求评审变慢或变贵时，不要第一反应就换模型或删 Prompt。更稳的排查顺序是：

```text
先看是否真的变慢 / 变贵
→ 再看是 token 增长、调用次数增长，还是 retry / fallback 增长
→ 再看是 Prompt、context、schema、模型配置，还是缓存失效导致
→ 最后才决定优化策略
```

### 情况 1：`total_tokens` 增长

先回到 05 的 context report，看 `section_tokens`、`included_sources`、`compressed_sources` 和 `dropped_sources`。如果 evidence 变多但没有提升引用质量，问题可能不是模型，而是 context policy 太宽。如果 completion tokens 增长，检查 Prompt 是否要求模型输出过长解释，或者 schema 是否允许无边界的长字段。

### 情况 2：`latency_ms` 增长，但 tokens 没明显变

先看 06 的 `attempt_count` 和 `degraded`。如果 retry 增加，说明供应商、网络或能力兼容性可能不稳定；如果 fallback 增加，说明主模型路径正在退化。此时不要只看最终 `success`，因为成功可能是“慢慢恢复后的成功”。

### 情况 3：cache hit rate 降低

先看 cache key 的组成。Prompt 版本、schema 版本、temperature、context fingerprint 任一变化都会导致 miss。如果这些变化是有意的，miss 是正确行为；如果只是因为某个无关字段被塞进 key，导致每次都 miss，就需要收窄 key 的 extra 信息。

### 情况 4：成本下降但人工感觉答案变差

这通常不是 08 能单独解决的问题。08 只能告诉你更省了，不能告诉你更好。下一步要把同一批 records 进入 eval，检查风险识别完整性、引用正确性、拒答合理性和人工可用性。成本优化必须和质量评估一起看，否则很容易把系统优化成“便宜但不可用”。

---

## 失败分析与能力边界

### 失败 1：缓存返回了旧结论

表现：同一条需求第二次评审速度很快，但引用的业务规则还是旧版本。

原因：cache key 只包含用户输入，没有包含 Prompt 版本、schema 版本或 `context_fingerprint`。

怎么验证：运行 `cost_latency_cache.py`，观察 `changed_context` 是否 miss。如果 context 改了还 hit，说明 cache key 不安全。

### 失败 2：成本下降，但质量变差

表现：换成便宜模型后，`estimated_total_cost` 下降，parse 也成功，但风险内容变得空泛。

原因：成本指标只能说明调用更省，不能说明答案更好。`parse_ok=True` 只代表结构可解析，不代表业务风险识别完整。

怎么验证：把这批 case 进入后续 eval，用 golden set 检查风险识别、引用质量、拒答和追问是否合理。

### 失败 3：summary 成功率没变，成本却上升

表现：`success=3`、`parse_success_rate=100%` 没变，但 `total_tokens` 或 `estimated_total_cost` 明显增加。

原因：可能是 Prompt 变长、context 变多、retry / fallback 增加，或者 multi-step 链路多调了几次模型。

怎么验证：先看 `total_tokens`，再看 06 的 attempt report 和 `degraded`，最后回到 context builder 看哪些证据进入了 Prompt。

### 本节不做

- 不做真实账单统计。
- 不接 Redis 或持久化缓存。
- 不做语义缓存。
- 不做多租户成本分摊。
- 不做线上预算告警。
- 不实现真实 RAG / Multi-Agent 链路，只做预算形状估算。

---

## 本节实战

### 目标

本节结束后，需求评审助手的 LLM 调用底座多出一层最小调用治理能力：能在 harness records 上观察 token、估算成本、延迟和缓存命中。

### 涉及文件

- [`source/packages/llm_core/costing/`](../../source/packages/llm_core/costing/)：学习用价格表与成本估算。
- [`source/packages/llm_core/cache/`](../../source/packages/llm_core/cache/)：cache key、进程内 cache、cache event / stats。
- [`source/packages/llm_core/harness/records.py`](../../source/packages/llm_core/harness/records.py)：record / summary 增加成本延迟字段。
- [`source/demos/02_call_ops_lab/cost_latency_cache.py`](../../source/demos/02_call_ops_lab/cost_latency_cache.py)：08 观察入口。
- [`source/demos/02_call_ops_lab/README.md`](../../source/demos/02_call_ops_lab/README.md)：输出解读。

### 运行方式

```bash
uv run python source/demos/02_call_ops_lab/cost_latency_cache.py
```

默认调用真实模型，不写磁盘。运行前确认根目录 `.env` 已配置 `OPENAI_API_KEY`，以及需要时的 `OPENAI_BASE_URL` / `OPENAI_MODEL`。如果缺 key、模型不支持 structured output 或供应商异常，demo 会把真实错误暴露出来；这不是噪声，而是本节要学习的真实工程边界。

如果需要离线排查或稳定复现缓存行为，可以把脚本顶部改为：

```python
USE_REAL_LLM = False
```

模拟路径只用于对照，不代表真实模型的 usage、latency 或输出质量。

### 输出怎么看

先看 `[records:cold]`：

```text
case_id  status   parse  tokens  latency_ms  cost       cache
S1       success  ok     1420    1280.5      $0.000312  -
```

这说明每条 case 不再只是“成功 / 失败”，还记录了 token、估算成本、延迟和缓存状态。真实模型下 `latency_ms` 不会像 fake 一样固定，恰好可以观察当前供应商和网络条件。

再看 `[cache_rounds]`：

```text
cold: hit_rate=0%
repeat_same_input: hit_rate=100%
changed_context: hit_rate=0%
```

这说明同配置同上下文重复运行可以命中；上下文指纹变化后必须 miss。

最后看 `[budget_shape]`。这里不是实现 RAG 或 Agent，只是帮助你提前看到：single call、context-enriched call、multi-step review 的成本形状会不同。

### 真实模型输出怎么看

真实运行时，不要只看 `[detail]` 里的自然语言内容。建议按下面顺序读：

1. 先看 `[records:cold]`：`status` / `parse` / `error` 决定这条 case 是否形成了可用结构化结果。
2. 再看 `tokens` 和 `latency_ms`：这是供应商响应和应用计时得到的调用事实。
3. 再看 `cost`：这是本地学习价格表算出的估算值，不是账单。
4. 再看 `[cache_rounds]`：判断重复输入是否命中，以及 `changed_context` 是否正确 miss。
5. 最后看 `[detail]`：内容预览只能辅助人工查看，不能替代 eval。

如果你看到 `cost=-`，通常说明真实响应缺少 usage，或者当前模型没有学习价格配置。此时不要把它当作 0 成本，而应记录为“成本未知”。

---

## 完成标准

### 能解释

- `prompt_tokens`、`completion_tokens`、`total_tokens` 分别代表什么。
- `estimated_cost` 为什么不是供应商账单。
- 为什么 `latency_ms`、`average_latency_ms`、`max_latency_ms` 要和 success rate 一起看。
- 为什么 cache key 不能只用用户输入。

### 能判断

- 哪些低风险、同配置、同上下文的重复调用可以缓存。
- 哪些评审结论在材料、证据、权限或 Prompt 变化后必须重新生成。
- 什么时候宁可多花 token，也不能复用缓存。

### 能运行与观察

```bash
uv run pytest source/packages/llm_core/tests
uv run python source/demos/02_call_ops_lab/cost_latency_cache.py
```

应看到：

- `total_tokens` 和 `estimated_total_cost` 出现在 summary 中。
- `repeat_same_input` 的 cache hit rate 为 100%。
- `changed_context` 的 cache hit rate 为 0%。
- 默认真实模型路径可以暴露真实 usage、latency 和供应商错误；模拟路径只用于对照。
- 测试全部通过。

### 自检题

1. 为什么 `usage.total_tokens` 不等于真实业务成本的全部？
2. 为什么缓存 key 必须包含 `context_fingerprint`？
3. 为什么 `parse_success_rate=100%` 仍然不能证明成本优化方案可以上线？
4. 如果换便宜模型后成本下降，但风险内容变空泛，你会先看哪些记录？
5. 为什么本节不接 Redis？
6. 为什么课程 demo 默认应该跑真实模型，而测试仍然使用 fake？

---

## 本节沉淀

本节新增 `llm_core.costing` 与 `llm_core.cache`，并让 harness summary 具备 token、估算成本、延迟和 cache hit 视角。

对需求评审助手来说，这意味着模型调用底座不只会“生成结果”，还开始能回答：这一批评审调用是否可承受、重复调用是否可节省、哪些缓存必须失效。

下一节进入 Function Calling API 边界；工具运行时、权限、审计和 Agent loop 仍然放到 `04_agent` 系统学习。

---

## 相关专题

- [07. LLM Calling Harness](07_llm_calling_harness.md)
