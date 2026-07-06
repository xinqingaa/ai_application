# 06. Reliability、Errors 与 Degradation

> 05 已经回答了“模型调用前，应用应该让模型看到什么”。本篇继续回答：**当上下文、Prompt、Schema 都准备好了，模型调用仍然失败时，应用应该如何分类、重试、降级，并把失败过程解释清楚**。

---

## 真实问题

05 的 `Context Builder` 让需求评审助手可以把 PRD、业务规则、接口文档和客户端说明装配成可追溯的 Prompt。你已经能看到哪些 source 进了上下文，哪些被丢弃，哪些可以作为 citation。到这一步，很容易产生一种错觉：只要上下文构造正确，模型调用就应该稳定产出结构化结果。

真实项目不会这么听话。一次评审请求可能在任何位置失败：网络抖动导致超时，供应商限流，API key 配错，模型不支持 `json_schema`，响应被截断，返回了自然语言而不是 JSON，Pydantic 解析失败，或者主模型不可用但 fallback 模型还能回答。更麻烦的是，这些失败不能用同一种处理方式。超时可以有限重试；鉴权失败不应该重试；结构化解析失败可能需要换 `structured_mode` 或换模型；高风险评审如果降级到能力更弱的模型，应该让后续 trace 和人工审核知道，而不是伪装成一次普通成功。

本节要解决的不是“怎么让模型永不失败”。LLM 应用里没有这个保证。真正可交付的目标是：**失败要被分类，重试要有边界，降级要可见，最终结果要能解释是正常成功、重试后成功、降级成功，还是失败退出**。

### 学习者真实问题

如果你有前端 / Flutter / 客户端经验，可以把这节类比成复杂接口调用的错误处理。一个支付接口失败时，你不会简单写成：

```text
try request
catch error
retry forever
```

你会区分网络失败、参数错误、鉴权失败、余额不足、业务拒绝、服务不可用。网络失败可以提示重试；参数错误应该改代码；业务拒绝要展示明确原因；服务不可用可以降级或稍后再试。AI 应用也是一样，只是失败类型更多，而且有一类新问题：**请求成功了，但模型内容不能被应用使用**。

例如 `chat_structured()` 收到 HTTP 200，不代表应用成功。如果模型返回：

```text
这个需求主要有三类风险：接口参数、状态机、三端一致性。
```

这段话对人有意义，但如果本节任务要求 `ReviewRiskList`，它就是结构化失败。前端无法稳定渲染风险卡片，评估无法统计字段完整率，Workflow 也不知道下一步怎么走。所以本节要训练的判断是：应用成功不等于 HTTP 成功；模型输出可读不等于业务可用；失败处理要围绕应用契约，而不是只围绕 SDK 异常。

### 产品真实问题

继续看售后入口评审。用户提交 PRD 后，系统构造了 `evidence_first` 上下文：订单状态机、售后接口 v2、客户端接入说明都进入 Prompt。第一次调用主模型时超时了。如果系统直接失败，用户会看到“评审失败”，但其实第二次请求可能就能成功；如果系统无限重试，用户会等很久，成本也会放大；如果系统偷偷切到便宜模型并输出结果，评审负责人后续又无法判断这份结论是否经过同等能力模型处理。

再看另一个场景：主模型返回了一段自然语言总结，没有返回 JSON。对普通聊天来说这算回答成功；对需求评审助手来说，这无法进入风险列表组件。此时系统应该把它归类为 `schema_parse` 或 `empty_response`，记录原始输出与解析失败阶段，然后决定是否重试、切换 fallback、或者失败可见。

产品真正需要的是这样的反馈：

```text
本次评审：
1. 第一次调用 chat.dev_chat 超时；
2. 第二次调用 chat.dev_chat 成功；
3. 没有发生模型降级；
4. 最终输出可解析为结构化风险列表。
```

或者：

```text
本次评审：
1. 主模型两次超时；
2. fallback 模型成功返回；
3. 结果标记为 degraded；
4. 后续报告页和 trace 中保留降级标记。
```

这比一句“成功 / 失败”更有价值，因为它让用户和开发者都知道系统到底经历了什么。

### 工程真实问题

工程上，Reliability 至少要拆成五层：

| 层 | 解决什么 | 本节落点 |
| --- | --- | --- |
| 错误分类 | 不同失败不能同样处理 | `LLMErrorCode` |
| 重试策略 | 哪些错误可重试、最多几次 | `RetryPolicy` |
| 降级策略 | 主模型失败后能否换 fallback | `DegradationPolicy` |
| 结果校验 | HTTP 成功后内容是否可用 | `chat_structured` parse validation |
| 尝试报告 | 每次 attempt 如何被诊断 | `ReliableCallReport` |

这五层共同构成一个可靠调用外壳。它不替代 `LLMClient`，而是包在 `LLMClient` 外面：基础 client 负责“按配置调一次模型”；可靠性层负责“这次失败了怎么办，以及过程如何记录”。

---

## 基础原理

### 本节方案性质

Reliability 也没有唯一标准答案。真实生产系统可能使用 SDK 内置 retry、Tenacity、服务端任务队列、熔断器、限流器、trace 平台、消息队列和人工介入。本节先做学习阶段最小闭环。

| 层级 | 本节怎么理解 |
| --- | --- |
| **通用原则** | 错误要分类；重试要有限；不可恢复错误要快速失败；降级要可见；内容契约失败也算失败 |
| **工程实践** | 用 `ReliableLLMService` 包住 `LLMClient`，返回 `ReliableCallResult + ReliableCallReport` |
| **项目取舍** | 本节只做同步调用级 retry / fallback，不引入队列、熔断器和分布式任务状态 |
| **非目标** | 不做完整生产级限流；不做 Prompt Injection 安全体系；不做成本统计和 trace 平台 |

你可以把本节看成 07 harness、08 cost latency、后续 eval observability 的前置层。没有可靠调用报告，后续就很难判断一次失败是模型能力问题、网络问题、schema 问题，还是 fallback 后质量下降。

### 先用一个小例子抓住主线

假设系统要调用主模型生成结构化风险列表：

```text
输入：已经由 05 构造好的 messages
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

关键点是：**降级成功仍然不是普通成功**。如果主模型两次超时后 fallback 成功，最终业务可以继续，但 `ReliableCallReport.degraded` 必须是 `True`。后续 08 统计成本和延迟时要知道它发生过；后续评估时也要知道这条结果来自 fallback。

反例：如果系统悄悄切模型，用户看到的答案也许能用，但 bad case 复盘时无法解释为什么同一类输入昨天好、今天差。

### 结构化失败也是可靠性问题

03 已经讲过 Structured Outputs：Schema 能让模型输出进入程序。但 03 更多关注“如何定义和解析结构”。06 关注的是：解析失败以后，这次调用算不算成功？

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

每次 attempt、最终 config、是否 degraded、最终错误都可观察。仍遗留：批量回归、成本统计、P95 延迟进入 07 / 08 / 05_eval_observability。

这条递进和前几节连起来就是：

```text
02 Prompt：任务说清楚
03 Structured Output：输出形状可校验
04 Streaming：过程可展示
05 Context：输入可追溯
06 Reliability：失败可解释、可恢复、可降级
```

---

## 最小实现

本节的最小实现守住四个不变量：

1. `LLMClient.chat()` 仍然只负责单次调用，不内置复杂重试。
2. `ReliableLLMService` 包装 `LLMClient`，统一处理 retry / fallback / validation。
3. 结构化解析失败会被转成可靠性错误，而不是被当作普通成功。
4. 每次 attempt 都进入 `ReliableCallReport`，demo 和后续 trace 都能读取。

完整代码阅读顺序见 [llm_core README](../../source/packages/llm_core/README.md) 和 [call ops lab README](../../source/demos/02_call_ops_lab/README.md)。

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

这样 03 的 `parse_risk_list` 不只是本地校验工具，也能进入 06 的 retry / fallback / report 链路。

### 4. Demo 只观察可靠性行为

[`reliability_compare.py`](../../source/demos/02_call_ops_lab/reliability_compare.py) 默认不调用真实模型，而是用 fake client 模拟失败：

```text
timeout_then_success
primary_timeout_then_fallback
auth_error
schema_failure
```

这是为了稳定观察失败路径。真实模型调用很可能一次成功，反而不利于学习“失败时 report 怎么看”。如果要观察真实调用，把脚本顶部 `USE_REAL_LLM = True` 打开即可。

---

## 主流框架实现

OpenAI SDK、Anthropic SDK 和其他兼容平台都会抛出自己的异常类型，例如 timeout、rate limit、status error。项目里不应该让业务层到处判断供应商异常名，而应在 provider 层先映射为统一的 `LLMErrorCode`。本仓库的 [`OpenAICompatProvider`](../../source/packages/llm_core/providers/openai_compat.py) 已经做了第一层映射。

Tenacity / backoff 这类 Python 库可以帮助实现重试、退避和停止条件。它们适合生产项目，但学习阶段直接写一个小的 `RetryPolicy` 更容易看清机制：哪些错误可重试，最多重试几次，失败记录在哪里。

LangChain 也有 fallback、retry parser 和 output parser 等能力。它们解决的是同一类问题：模型调用不是一次裸请求，而是一个可恢复、可校验、可观测的 runnable。区别在于，本节先用自研最小实现把边界讲清楚；后续进入 LangChain / Agent / Workflow 时，才能判断框架封装的是哪一层。

---

## 失败分析与能力边界

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

- **表现**：fallback 结果引用了不存在的 source id，或忽略 05 的 citation candidates。
- **原因**：降级路径没有使用同一份 messages / context report，或 Prompt 约束变弱。
- **怎么验证**：确认 fallback 调用仍使用 05 构造出的同一份 messages；再检查输出 citation 是否在 candidates 中。完整 citation eval defer 到后续评估课程。

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
| 批量调用记录与回归集 | 07 | 本节只返回单次调用 report |
| 成本、延迟 P95、缓存 | 08 | 本节只记录 attempt latency，不做统计面板 |
| Prompt Injection 和工具权限安全 | 04_agent | 本节只处理模型调用失败，不处理工具安全 |
| 生产级熔断和任务队列 | 06_ai_native / 07_projects | 本节只做同步调用外壳 |
| 完整 trace 平台 | 05_eval_observability | 本节 report 是后续 trace 的输入 |

---

## 本节实战

### 目标

为需求评审助手增加一个可靠调用外壳：能够对模型调用进行错误分类、有限重试、fallback 降级，并输出每次 attempt 的诊断报告。

### 涉及文件

关键路径：

- [`source/packages/llm_core/errors/types.py`](../../source/packages/llm_core/errors/types.py)：统一错误码。
- [`source/packages/llm_core/reliability/`](../../source/packages/llm_core/reliability/)：`RetryPolicy`、`DegradationPolicy`、`ReliableLLMService` 和 report。
- [`source/packages/llm_core/tests/test_reliability.py`](../../source/packages/llm_core/tests/test_reliability.py)：可靠性单元测试。
- [`source/demos/02_call_ops_lab/reliability_compare.py`](../../source/demos/02_call_ops_lab/reliability_compare.py)：06 call ops lab 观察入口。
- [`source/demos/02_call_ops_lab/README.md`](../../source/demos/02_call_ops_lab/README.md)：reliability 与 harness 的输出说明。

### 实现步骤

1. 在 `LLMErrorCode` 中补齐内容安全、空响应等错误类型。
2. 用 `RetryPolicy` 定义可重试错误和最大尝试次数。
3. 用 `DegradationPolicy` 定义 fallback config 和允许降级的错误。
4. 用 `ReliableLLMService` 包装 `LLMClient.chat()` / `chat_structured()`。
5. 用 `ReliableCallReport` 输出 attempts、final config、degraded 和 final error。
6. 用 demo 模拟 timeout、auth、schema failure 和 fallback。

### 运行方式

离线测试：

```bash
uv run pytest source/packages/llm_core/tests/test_reliability.py
```

demo：

```bash
uv run python source/demos/02_call_ops_lab/reliability_compare.py
```

`reliability_compare.py` 顶部提供学习期实验开关：

```python
DEFAULT_CASE = "timeout_then_success"
USE_REAL_LLM = False
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

## 完成标准

- 能解释 `timeout`、`rate_limit`、`auth`、`schema_parse` 为什么不能用同一种处理方式。
- 能说明 retry 适合处理什么，不适合处理什么。
- 能说明 fallback 为什么必须通过 `degraded` 暴露出来。
- 能运行 `test_reliability.py`，理解 timeout 重试、auth 不重试、fallback 和 schema parse failure 的测试意图。
- 能运行 `reliability_compare.py`，读懂 `[call_plan]`、`[attempts]`、`[final]`。
- 能说明本节为什么不做批量 harness、成本统计、熔断器和任务队列。

### 运行与观察

```bash
uv run pytest source/packages/llm_core/tests/test_reliability.py
uv run python source/demos/02_call_ops_lab/reliability_compare.py
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
5. 如果模型输出缺少 citation，你会先查 05 的 context report，还是 06 的 reliability report？为什么？
6. 为什么本节不把 retry 逻辑直接写进 `LLMClient.chat()`？

---

## 本节沉淀

- `llm_core` 新增 `reliability/`，把单次模型调用升级为可重试、可降级、可诊断的可靠调用。
- 扩展 `02_call_ops_lab`，用稳定模拟 case 学习失败路径，不默认消耗真实模型额度，也不保存运行文件。
- 下一节 07 LLM Calling Harness 将把单次可靠调用扩展为批量样例、调用记录和回归对比。

---

## 相关专题

- 上一篇：[05_context_engineering.md](05_context_engineering.md)
- 下一篇：[07_llm_calling_harness.md](07_llm_calling_harness.md)
- 课程大纲：[outline.md](outline.md)
