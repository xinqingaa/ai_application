# Reliability、错误分类与可见降级

> 机制篇：解释模型调用失败如何被分类、有限重试、显式降级，并保留完整 attempt 记录。
>
> 课程位置：[标准学习路径](../learning-path.md) V0 第六步。必要前置是 [模型 API 与 Provider](model-api-and-provider.md)和 [Structured Output](structured-output.md)；本文交付错误分类、有限重试、显式降级和 Attempt Report。

---

## 为什么一次失败不能统一重试

同一次结构化评审可能经历：

```text
第一次请求超时
→ 判断 timeout 是否允许重试
→ 第二次请求仍失败
→ 判断是否允许切换 fallback
→ fallback 返回文本
→ Structured Output 校验
→ 结果可用，但标记 degraded
```

这条链中任何一步都不能被一个通用 retry 装饰器替代。鉴权失败不应重试，Schema 失败在 Prompt 和输入没有变化时盲目重试意义很小，fallback 成功也不能伪装成普通成功。

本文把一次可靠调用拆成错误分类、Retry Policy、Degradation Policy、结果校验和 Attempt Report。目标不是“尽量返回答案”，而是让成功、降级成功和最终失败都可解释。

## 分类、重试、降级与报告

### 本节方案性质

Reliability 也没有唯一标准答案。真实生产系统可能使用 SDK 内置 retry、Tenacity、服务端任务队列、熔断器、限流器、trace 平台、消息队列和人工介入。本节先做学习阶段最小闭环。

| 层级 | 本节怎么理解 |
| --- | --- |
| **通用原则** | 错误要分类；重试要有限；不可恢复错误要快速失败；降级要可见；内容契约失败也算失败 |
| **工程实践** | 用 `ReliableLLMService` 包住 `LLMClient`，返回 `ReliableCallResult + ReliableCallReport` |
| **项目取舍** | 本节只做同步调用级 retry / fallback，不引入队列、熔断器和分布式任务状态 |
| **非目标** | 不做完整生产级限流；不做 Prompt Injection 安全体系；不做成本统计和 trace 平台 |

你可以把本节看成 Calling Harness、成本与延迟治理、后续 Eval 与可观测性的前置层。没有可靠调用报告，后续就很难判断一次失败是模型能力问题、网络问题、Schema 问题，还是 fallback 后质量下降。

### 先用一个小例子抓住主线

假设系统要调用主模型生成结构化风险列表：

```text
输入：由固定 PRD 和静态 evidence 渲染出的 messages
目标：返回 ReviewRiskList
主模型：chat.dev_chat
fallback：chat.fallback_chat
```

第一次调用超时。此时系统有三种选择：

1. 直接失败：用户体验差，偶发网络抖动无法恢复。
2. 无限重试：成本和延迟失控。
3. 有限重试：最多重试 2 次，如果仍失败，再按策略决定是否 fallback。

本节选择第三种。于是一次可靠调用的数据流是：

```text
messages + primary config_ref
→ ReliableLLMService
→ 按 RetryPolicy 调用 LLMClient
→ 必要时按 DegradationPolicy 切换 fallback
→ 校验内容是否满足结构化契约
→ 返回 output + ReliableCallReport
```

先抓住这条线，再看 `LLMErrorCode`、`RetryPolicy`、`DegradationPolicy` 和 `ReliableCallReport`，就不会觉得它们只是多出来的一组类名。

### 错误分类：不是所有失败都该重试

错误分类的作用，是把“失败了”拆成可行动的判断。

| 错误 | 典型原因 | 是否重试 | 常见处理 |
| --- | --- | --- | --- |
| `timeout` | 网络抖动、供应商响应慢 | 可以有限重试 | 重试 1–2 次，仍失败再 fallback |
| `rate_limit` | 供应商限流 | 可以有限重试 | 等待或切换低成本 fallback |
| `provider_error` | 供应商 5xx 或异常 | 可以有限重试 | 重试或 fallback |
| `auth` | API key 缺失、权限错误 | 不应重试 | 快速失败，检查配置 |
| `capability_mismatch` | 模型不支持该能力 | 通常不重试 | 换支持能力的 config |
| `schema_parse` | 返回内容不符合 schema | 看任务决定 | 换模式、换模型或失败可见 |
| `empty_response` | 模型返回空内容 | 可以重试或 fallback | 记录原始响应 |
| `content_safety` | 内容安全拦截 | 通常不重试 | 进入安全或人工流程 |

反例：如果 `auth` 也被放进 retryable errors，系统会连续请求同一个错误 key，浪费时间还污染日志。如果 `schema_parse` 被当作普通成功，前端会拿不到稳定字段，后续 eval 也会误以为调用通过。

### 重试边界：恢复偶发失败，不掩盖系统问题

重试只适合处理“可能下一次就恢复”的失败，例如超时、限流、临时供应商错误。它不适合修复代码错误、配置错误、schema 设计错误和业务拒绝。

本节的 `RetryPolicy` 只做三件事：

```text
max_attempts：同一个 config_ref 最多尝试几次
retryable_errors：哪些错误允许重试
backoff_seconds：两次尝试之间是否等待
```

学习阶段默认 `backoff_seconds=0`，这样测试和 demo 更快。真实项目可以加入指数退避，但原则不变：重试次数必须有上限，且每次 attempt 要进入 report。

### 降级不是偷偷换模型

降级的意思是：主路径失败后，系统选择一个能力、成本或速度不同的备用路径完成任务。对 LLM 应用来说，常见降级包括：

- 从主模型切到 fallback 模型。
- 从 `json_schema` 改成 `json_object`。
- 从完整结构化评审降级为“失败可见 + 人工提示”。
- 从实时生成降级为排队任务。

本节只实现最小的一种：主模型失败后切到 `chat.fallback_chat`。

关键点是：**降级成功仍然不是普通成功**。如果主模型两次超时后 fallback 成功，最终业务可以继续，但 `ReliableCallReport.degraded` 必须是 `True`。后续 成本治理 统计成本和延迟时要知道它发生过；后续评估时也要知道这条结果来自 fallback。

反例：如果系统悄悄切模型，用户看到的答案也许能用，但 bad case 复盘时无法解释为什么同一类输入昨天好、今天差。

### 结构化失败也是可靠性问题

结构化输出 已经讲过 Structured Outputs：Schema 能让模型输出进入程序。但 结构化输出 更多关注“如何定义和解析结构”。可靠调用 关注的是：解析失败以后，这次调用算不算成功？

答案是：对结构化任务来说，不算。

一次 `chat_structured()` 有两层结果：

```text
LLMResponse：模型是否返回了文本
StructuredParseResult：文本是否能被应用解析为目标 schema
```

如果第一层成功、第二层失败，系统不能只看 HTTP 或 SDK 返回。它应该把失败转换为 `LLMErrorCode.SCHEMA_PARSE` 或 `LLMErrorCode.EMPTY_RESPONSE`，进入 retry / fallback / report 链路。

这也解释了为什么可靠性层放在 `chat_structured()` 外面，而不是只包普通 `chat()`。真实项目里，最终可用性由业务契约决定。

### 从弱到强的机制递进

**第 1 步 · 直接调用模型**

实现最简单，但失败时只能抛异常。反例：用户只看到“请求失败”，不知道是超时还是 schema 失败。

**第 2 步 · catch 所有异常并重试**

偶发超时能恢复，但会把鉴权、能力不匹配、配置错误也拿去重试。反例：API key 错误重试 3 次，问题仍然是 key 错。

**第 3 步 · 错误分类 + 有限重试**

可恢复错误有限重试，不可恢复错误快速失败。仍遗留：主模型持续不可用怎么办？

**第 4 步 · fallback 降级**

主模型失败后切换备用模型。仍遗留：降级是否对用户、trace、评估可见？

**第 5 步 · ReliableCallReport**

每次 attempt、最终 config、是否 degraded、最终错误都可观察。仍遗留：批量回归、成本统计、P95 延迟进入 调用 Harness / 成本治理 / 评估观测。

这条递进和当前已经完成的机制连起来就是：

```text
Prompt：任务说清楚
Structured Output：输出形状可校验
Reliability：失败可解释、可恢复、可降级
```

后续 Context、RAG、Streaming 和 Harness 会从不同方向复用这份可靠调用结果，但它们不是理解本文的前置。

---

## 给真实调用增加有限控制

本节的最小实现守住四个不变量：

1. `LLMClient.chat()` 仍然只负责单次调用，不内置复杂重试。
2. `ReliableLLMService` 包装 `LLMClient`，统一处理 retry / fallback / validation。
3. 结构化解析失败会被转成可靠性错误，而不是被当作普通成功。
4. 每次 attempt 都进入 `ReliableCallReport`，demo 和后续 trace 都能读取。

完整代码阅读顺序见 [llm_core README](../../source/packages/llm_core/README.md) 和 [reliability lab README](../../source/demos/llm_reliability_lab/README.md)。

### 1. 策略和报告

[`reliability/`](../../source/packages/llm_core/reliability/) 先定义可靠性层的数据契约：

```python
@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 2
    retryable_errors: tuple[LLMErrorCode, ...] = DEFAULT_RETRYABLE_ERRORS
    backoff_seconds: float = 0.0

@dataclass(frozen=True)
class DegradationPolicy:
    fallback_config_refs: tuple[str, ...] = ("chat.fallback_chat",)
    fallback_on_errors: tuple[LLMErrorCode, ...] = DEFAULT_FALLBACK_ERRORS

@dataclass(frozen=True)
class ReliableCallReport:
    primary_config_ref: str
    final_config_ref: Optional[str]
    attempts: list[ReliableCallAttempt] = field(default_factory=list)
    degraded: bool = False
    final_error_code: Optional[LLMErrorCode] = None
```

这里的关键不是字段多，而是把“怎么处理失败”和“处理过程是什么”分开。`RetryPolicy` / `DegradationPolicy` 是本次调用前的计划；`ReliableCallReport` 是调用后的事实记录。

### 2. 可靠调用外壳

[`ReliableLLMService`](../../source/packages/llm_core/reliability/) 的主职责是包住 `LLMClient`：

```python
result = service.chat(
    messages,
    "chat.dev_chat",
    retry_policy=RetryPolicy(max_attempts=2),
    degradation_policy=DegradationPolicy(
        fallback_config_refs=("chat.fallback_chat",),
    ),
    temperature=0,
)
```

如果第一次 `chat.dev_chat` 超时，report 会记录一次 failed attempt；如果第二次成功，`result.ok=True`，`report.degraded=False`。如果主模型两次失败后 fallback 成功，`result.ok=True`，但 `report.degraded=True`。

这比直接返回 `LLMResponse` 多了一层解释能力：业务仍能拿到结果，但也能知道结果是如何来的。

### 3. 结构化输出校验进入可靠性层

`ReliableLLMService.chat_structured()` 会调用 `LLMClient.chat_structured()`，然后检查 `response.parse.ok`。如果 parse 失败，会转换为 `LLMError`：

```text
parse.error_stage == "empty"  -> empty_response
parse.error_stage == "json"   -> schema_parse
parse.error_stage == "schema" -> schema_parse
```

这样，Structured Output 中的 `parse_risk_list` 不只是本地校验工具，也能进入可靠调用的 retry / fallback / report 链路。

### 4. Demo 默认真实调用，模拟只做失败复现

[`reliability_compare.py`](../../source/demos/llm_reliability_lab/reliability_compare.py) 默认调用真实模型，观察可靠调用外壳如何记录真实 attempt、latency、final config 和错误。真实调用的价值是让你看到供应商、模型能力、API key、网络和 structured mode 等真实工程变量。

但真实模型通常不会稳定触发 timeout、auth、schema failure 或 fallback。为了学习失败路径，脚本保留 `USE_REAL_LLM = False` 的模拟模式，可稳定复现：

```text
timeout_then_success
primary_timeout_then_fallback
auth_error
schema_failure
```

这类模拟结果只用于理解 report 结构，不代表真实模型表现。课程主路径仍是先跑真实模型，再按需要切到模拟模式观察特定失败。

---

## 重试框架不能替你决定什么

OpenAI SDK、Anthropic SDK 和其他兼容平台都会抛出自己的异常类型，例如 timeout、rate limit、status error。项目里不应该让业务层到处判断供应商异常名，而应在 provider 层先映射为统一的 `LLMErrorCode`。本仓库的 [`OpenAICompatProvider`](../../source/packages/llm_core/providers/openai_compat.py) 已经做了第一层映射。

Tenacity / backoff 这类 Python 库可以帮助实现重试、退避和停止条件。它们适合生产项目，但学习阶段直接写一个小的 `RetryPolicy` 更容易看清机制：哪些错误可重试，最多重试几次，失败记录在哪里。

LangChain 也有 fallback、retry parser 和 output parser 等能力。它们解决的是同一类问题：模型调用不是一次裸请求，而是一个可恢复、可校验、可观测的 runnable。区别在于，本节先用自研最小实现把边界讲清楚；后续进入 LangChain / Agent / Workflow 时，才能判断框架封装的是哪一层。

---

## 可靠性策略本身怎样制造事故

### 1. 无限重试放大成本和延迟

- **表现**：用户等待很久，日志里同一请求重复多次，模型费用异常。
- **原因**：把可恢复错误和不可恢复错误混在一起，或没有 `max_attempts`。
- **怎么验证**：看 `ReliableCallReport.attempts` 数量；如果同一个 config_ref 重复过多，先查 `RetryPolicy`。

### 2. 鉴权失败被错误重试

- **表现**：终端连续出现 `auth` 错误。
- **原因**：把 `AUTH` 放进了 retryable errors。
- **怎么验证**：`auth` 应该只出现一次；出现多次说明策略错误，而不是供应商不稳定。

### 3. fallback 成功但质量下降

- **表现**：本次评审有输出，但风险更泛，引用更少。
- **原因**：主模型失败后降级到能力更弱的模型。
- **怎么验证**：看 `report.degraded` 和 `final_config_ref`。降级结果应进入后续 trace / eval，而不是和普通成功混在一起。

### 4. 结构化解析失败被当作成功

- **表现**：模型返回自然语言，终端显示请求成功，但前端渲染风险卡片失败。
- **原因**：只看 SDK 调用成功，没有检查 `parse.ok`。
- **怎么验证**：`chat_structured()` 后必须检查 parse；可靠性层应把失败转换为 `schema_parse` 或 `empty_response`。

### 5. 降级破坏 citation 和 context 追溯

- **表现**：fallback 结果引用了不存在的 source id，或忽略 上下文工程 的 citation candidates。
- **原因**：降级路径没有使用同一份 messages / context report，或 Prompt 约束变弱。
- **怎么验证**：确认 fallback 调用仍使用 上下文工程 构造出的同一份 messages；再检查输出 citation 是否在 candidates 中。完整 citation eval defer 到后续评估课程。

### 常见误区

| 误区 | 纠正 |
| --- | --- |
| 「加 retry 就等于可靠」 | retry 只处理偶发失败，不能修复 schema、配置和业务错误 |
| 「HTTP 200 就是成功」 | 对结构化任务，parse 失败也是失败 |
| 「fallback 成功就不用管了」 | fallback 必须可见，否则评估和复盘会失真 |
| 「所有错误都可以重试」 | auth、参数错误、能力不匹配通常应快速失败或换配置 |
| 「可靠性层应该写进 demo」 | demo 只观察；核心逻辑必须沉淀在 `llm_core` |

### 本节不做（defer）

| 能力 | 目标节 | 当节最小判断 |
| --- | --- | --- |
| 批量调用记录与回归集 | 调用 Harness | 本节只返回单次调用 report |
| 成本、延迟 P95、缓存 | 成本治理 | 本节只记录 attempt latency，不做统计面板 |
| Prompt Injection 和工具权限安全 | Agent | 本节只处理模型调用失败，不处理工具安全 |
| 生产级熔断和任务队列 | AI Native / 项目篇 | 本节只做同步调用外壳 |
| 完整 trace 平台 | 评估观测 | 本节 report 是后续 trace 的输入 |

---

## 比较直接调用与可靠调用

### 目标

为需求评审助手增加一个可靠调用外壳：能够对模型调用进行错误分类、有限重试、fallback 降级，并输出每次 attempt 的诊断报告。

### 涉及文件

关键路径：

- [`source/packages/llm_core/errors/types.py`](../../source/packages/llm_core/errors/types.py)：统一错误码。
- [`source/packages/llm_core/reliability/`](../../source/packages/llm_core/reliability/)：`RetryPolicy`、`DegradationPolicy`、`ReliableLLMService` 和 report。
- [`source/packages/llm_core/tests/test_reliability.py`](../../source/packages/llm_core/tests/test_reliability.py)：可靠性单元测试。
- [`source/demos/llm_reliability_lab/reliability_compare.py`](../../source/demos/llm_reliability_lab/reliability_compare.py)：本节观察入口。
- [`source/demos/llm_reliability_lab/README.md`](../../source/demos/llm_reliability_lab/README.md)：输出解读与实验开关。

### 实现步骤

1. 在 `LLMErrorCode` 中补齐内容安全、空响应等错误类型。
2. 用 `RetryPolicy` 定义可重试错误和最大尝试次数。
3. 用 `DegradationPolicy` 定义 fallback config 和允许降级的错误。
4. 用 `ReliableLLMService` 包装 `LLMClient.chat()` / `chat_structured()`。
5. 用 `ReliableCallReport` 输出 attempts、final config、degraded 和 final error。
6. 用 demo 默认观察真实 attempt；必要时切到模拟模式复现 timeout、auth、schema failure 和 fallback。

### 运行方式

离线测试：

```bash
uv run pytest source/packages/llm_core/tests/test_reliability.py
```

demo：

```bash
uv run python source/demos/llm_reliability_lab/reliability_compare.py
```

`reliability_compare.py` 顶部提供学习期实验开关：

```python
DEFAULT_CASE = "timeout_then_success"
USE_REAL_LLM = True
PRINT_MESSAGES = False
PRINT_ATTEMPT_DETAIL = True
COMPARE_WITH_NO_RETRY = True
```

真实项目中，这类值通常来自配置中心、环境变量或后台开关。本节 demo 先放在文件顶部，方便你用“注释 / 取消注释、改一个值”的方式观察机制。

### 输出怎么看

demo 输出按固定顺序：

```text
[case]
→ [call_plan]
→ [messages]    # PRINT_MESSAGES=True 时出现
→ [attempts]
→ [final]
→ [lesson]
```

读输出不要从头到尾逐字看。按三步：

1. 看 `[call_plan]`：本次最多尝试几次，有没有 fallback。
2. 看 `[attempts]`：每次调用成功还是失败，错误码是什么。
3. 看 `[final]`：最终是 success、failed，还是 degraded success。

默认 case 的典型输出是：

```text
[attempts]
  [1] config=chat.dev_chat status=failed code=timeout
  [2] config=chat.dev_chat status=success latency_ms=0.0

[final]
  [status] success
  [final_config] chat.dev_chat
  [degraded] false
```

这说明主模型第一次超时，但第二次重试成功，没有发生降级。它不是证明模型稳定，而是证明应用侧能处理一次可恢复失败。

### 经典案例：读懂一次 no_retry vs reliable 输出

默认配置：

```python
DEFAULT_CASE = "timeout_then_success"
COMPARE_WITH_NO_RETRY = True
```

脚本会先跑无重试对照，再跑可靠调用。

第一组 `no_retry`：

```text
[call_plan]
  [max_attempts_per_config] 1

[attempts]
  [1] config=chat.dev_chat status=failed code=timeout

[final]
  [status] failed
  [final_error] timeout
```

这说明同一个超时错误，在没有 retry 的情况下会直接变成用户可见失败。

第二组 `reliable`：

```text
[call_plan]
  [max_attempts_per_config] 2

[attempts]
  [1] config=chat.dev_chat status=failed code=timeout
  [2] config=chat.dev_chat status=success

[final]
  [status] success
  [degraded] false
```

这说明可靠性层没有改变业务输入，也没有让模型“更聪明”；它只是给可恢复错误一次受控恢复机会，并把恢复过程记录下来。

如果你把 `DEFAULT_CASE` 改为：

```python
DEFAULT_CASE = "primary_timeout_then_fallback"
```

应重点看：

```text
[final]
  [status] success
  [final_config] chat.fallback_chat
  [degraded] true
```

这类结果不能和普通成功混为一谈。它可以给用户返回答案，但后续质量评估、成本分析、trace 面板都应该知道这次发生了降级。

---

## 亲手增加一种失败策略

新增一个“供应商明确不支持当前能力”的失败样例：

1. 把它映射为独立且不可重试的错误类型。
2. 断言该错误只产生一次 attempt。
3. 分别配置“禁止 fallback”和“允许切到具备该能力的 fallback”。
4. 检查最终结果中的 success、degraded、final config 和 attempts。
5. 说明为什么不能把能力不支持当作普通 API 异常无限重试。

真实模型仍是主路径；本地 fake 只用于稳定复现这一条控制流。

## 怎样判断失败已可观察、可控制

- 能解释 `timeout`、`rate_limit`、`auth`、`schema_parse` 为什么不能用同一种处理方式。
- 能说明 retry 适合处理什么，不适合处理什么。
- 能说明 fallback 为什么必须通过 `degraded` 暴露出来。
- 能运行 `test_reliability.py`，理解 timeout 重试、auth 不重试、fallback 和 schema parse failure 的测试意图。
- 能运行 `reliability_compare.py`，读懂 `[call_plan]`、`[attempts]`、`[final]`。
- 能说明本节为什么不做批量 harness、成本统计、熔断器和任务队列。

### 运行与观察

```bash
uv run pytest source/packages/llm_core/tests/test_reliability.py
uv run python source/demos/llm_reliability_lab/reliability_compare.py
```

观察点：

- `no_retry` 是否在第一次 timeout 后直接失败。
- `reliable` 是否在第二次 attempt 成功。
- 改成 `auth_error` 后是否不会重试。
- 改成 `primary_timeout_then_fallback` 后 `degraded` 是否为 `true`。
- 改成 `schema_failure` 后最终错误是否能归到结构化失败。

### 自检题

1. 为什么 `auth` 错误不应该进入普通 retry？
2. 为什么 HTTP 请求成功，但 `parse.ok=False` 时仍应算调用失败？
3. fallback 成功后，为什么还要保留 `degraded=True`？
4. 如果某次评审成本突然升高，你会如何从 `ReliableCallReport.attempts` 开始排查？
5. 未来接入 RAG 后，如果模型输出缺少 citation，你会先查 Context Report，还是 Reliability Report？为什么？
6. 为什么本节不把 retry 逻辑直接写进 `LLMClient.chat()`？

---

## 交给项目的可靠调用报告

- `llm_core` 新增 `reliability/`，把单次模型调用升级为可重试、可降级、可诊断的可靠调用。
- 扩展 `llm_reliability_lab`：默认真实调用观察真实 attempt；模拟 case 仅用于稳定学习 timeout、auth、schema failure 和 fallback。Harness / Cost 在后续 `llm_regression_lab`，不要与本节入口混读。
- Context、RAG Pipeline 和 Calling Harness 后续都可以携带这里的可靠调用报告，但 Context 不是本文前置。

完成实验后回到 [标准学习路径](../learning-path.md)。需要查完整知识关系时再使用 [知识地图](../knowledge-map.md)。
