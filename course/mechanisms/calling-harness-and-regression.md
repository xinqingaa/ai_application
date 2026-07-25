# LLM Calling Harness 与最小回归

> 机制篇：解释如何用固定业务样例和调用记录，让 Prompt、模型、Schema、Context 与可靠性改动可以重复比较。
>
> 课程位置：[标准学习路径](../learning-path.md) V0 第十七步。必要前提是 [Prompt Engineering](prompt-engineering.md)、[Structured Output](structured-output.md)、[可靠调用](reliability-and-errors.md)，以及已经可以运行的固定 RAG 生成链；本文交付直接 LLM 与检索 RAG 可复用的 Case、Record 和 Summary。

---

## 为什么单次成功无法支持持续迭代

单独运行一次 Prompt 并觉得结果不错，不能说明改动有效。要比较两个版本，至少必须固定：

```text
同一批业务 Case
同一模型配置
同一温度
同一 Schema
同一 Context
```

然后把每次调用留下的事实放进同一种 Record：

```text
Case + Run Config
→ Reliable Call
→ HarnessRunRecord
→ HarnessSummary
→ 两次 Run 对比
```

Harness 不替结果质量打分。它先保证实验变量、调用事实和失败信息没有散失，让后续人工评审或 Eval 能回答“究竟改了什么、结果为什么不同”。

## Harness 如何控制变量并留下事实

### Harness 是实验装置，不是评估系统

Harness 的第一责任，是让同一批输入可以在同一套运行配置下反复执行，并把过程记录下来。它回答的是：

```text
这批 case 在这套配置下发生了什么？
```

Eval 回答的是另一个问题：

```text
这些结果质量好不好？
```

两者必须区分。`parse_ok=True` 只说明结构化解析通过，不说明风险识别完整；`degraded=True` 只说明发生了降级，不说明答案不能用；`success_count` 上升只说明调用层更稳定，不说明业务结论更准确。

反过来，如果没有 harness，eval 也站不住。你可能知道“这条答案不好”，但不知道它来自哪个 Prompt 版本、哪个模型、是否 fallback、是否 context 缺证据、是否 parse 其实失败过。

### Case 是业务样本，不是随便几条 Prompt

很多初学者会把 harness case 理解成“多写几条用户问题”。这不够。Case 应该代表一类业务风险或一类失败模式。

例如“售后入口”不是一句普通问题，而是用来观察：

- 是否识别订单状态机风险。
- 是否追问售后接口参数。
- 是否关注 H5 / Flutter / 原生入口一致性。
- 是否在材料不足时保守表达。

所以 `HarnessCase` 里除了 `messages`，还保留 `case_id`、`title`、`expected_focus`、`tags`。调用 Harness 不用 `expected_focus` 自动打分，但它给后续 eval 留下“这条样例本来要看什么”的业务入口。

### Run Config 是变量控制

如果你今天改了 Prompt，明天换了模型，后天又改了 structured mode，却没有记录这些变量，那么结果变化就无法解释。

`HarnessRunConfig` 的作用是让一次实验有名字、有配置：

- `run_name`：这次实验叫什么。
- `config_ref`：用哪个模型配置。
- `structured_mode`：用哪种结构化约束。
- `temperature` / `max_tokens`：采样和输出边界。
- `retry_policy` / `degradation_policy`：调用失败时怎么恢复。

它不是为了字段好看，而是为了让“本次改动是什么”可追溯。

### Record 是事实，不是结论

`HarnessRunRecord` 记录的是每条 case 的调用事实：

```text
case_id
status
parse_ok
risk_count
latency_ms
total_tokens
error_code
attempt_count
degraded
```

这些字段的价值在于排查路径非常清楚：

- `status=failed`：先看 `error_code`。
- `parse_ok=False`：先看 structured output 和 schema。
- `attempt_count` 变多：先看 可靠调用 reliability report。
- `degraded=True`：先确认结果是否来自 fallback。
- `latency_ms` / `total_tokens` 变高：成本治理 再继续做成本和延迟分析。

Record 不负责判断“答案好不好”。它负责让你知道“发生了什么”。

### Summary 是早期健康信号

`HarnessSummary` 把一批 records 汇总成工程健康信号：

- 成功数。
- 失败数。
- 解析成功数。
- 降级数。
- 平均耗时。
- 错误分布。

它的作用是快速提醒“这次 run 是否值得继续看”。如果 parse 成功率突然下降，说明 Prompt、Schema 或模型能力可能出问题；如果 degraded 数量突然上升，说明主模型或网络路径可能不稳定；如果平均耗时上升，就要继续检查 token、重试次数和 latency。

但 summary 仍然不是质量评分。它只能告诉你“工程表现是否异常”，不能告诉你“风险识别是否准确”。

### 从弱到强的机制递进

**第 1 步：手动跑一次 demo**

解决“能不能跑”。遗留问题：只能看到一个输入的一次结果。反例：S2 正常，不代表 S1、S3 正常。

**第 2 步：固定一组 case**

解决“每次都用同一批输入”。遗留问题：如果只看文本，仍然不知道 parse、error、fallback。反例：两次输出都像中文答案，但一次结构化解析失败。

**第 3 步：记录 run config**

解决“本次变量是什么”。遗留问题：还没有统一记录每条 case 的调用事实。反例：效果变化了，但不知道是模型、Prompt 还是 structured mode 导致。

**第 4 步：生成 record**

解决“每条 case 发生了什么”。遗留问题：一批 case 的整体趋势仍然需要肉眼汇总。

**第 5 步：生成 summary**

解决“这一批 run 的健康信号是什么”。遗留问题：答案是否准确、引用是否正确、拒答是否合理，进入后续 评估观测。

---

## 建立最小可回归调用链

本节的最小实现遵守一个原则：**核心能力进 `llm_core.harness`，demo 只负责观察**。

### 为什么要有 HarnessCase

[`harness/cases.py`](../../source/packages/llm_core/harness/cases.py) 中的 `HarnessCase` 不是为了包装一层对象，而是为了让业务样例离开 demo 脚本，成为后续可以复用、筛选、标注和扩展的输入单位。

```python
@dataclass(frozen=True)
class HarnessCase:
    case_id: str
    title: str
    messages: list[dict[str, str]]
    expected_focus: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
```

如果没有 `HarnessCase`，样例就会散落在脚本变量里。后面想做“只跑高风险 case”“只跑材料不足 case”“比较售后入口历史 bad case”，都会很难。

### 为什么要有 HarnessRunConfig

`HarnessRunConfig` 解决的是实验变量控制。一次 run 至少要知道：用哪个模型、哪种结构化模式、温度多少、是否允许 fallback。

```python
@dataclass(frozen=True)
class HarnessRunConfig:
    run_name: str
    config_ref: str = "chat.dev_chat"
    structured: bool = True
    structured_mode: StructuredMode = "json_object"
    temperature: float = 0
```

这和前端调试也很像：如果你不知道当前环境、feature flag、接口版本和设备尺寸，就无法解释 UI 表现差异。LLM 调用也是一样，不记录 run config，就无法比较两次结果。

### 为什么 record 要接住 reliability report

[`harness/runner.py`](../../source/packages/llm_core/harness/runner.py) 没有直接调用 Provider，而是复用可靠调用层的 `ReliableLLMService`：

```python
records, summary = LLMCallingHarness(service).run_cases(
    cases,
    HarnessRunConfig(run_name="risk_review_v4_real"),
)
```

这个设计非常关键。因为对业务来说，“成功”有不同来源：

- 第一次主模型成功。
- 主模型超时后重试成功。
- 主模型失败后 fallback 成功。
- HTTP 成功但结构化解析失败。

如果 harness 直接调用 `LLMClient`，它就拿不到完整 attempt 和 degraded 信息。这样后续 summary 里的 success 会混在一起，掩盖调用路径差异。

### 为什么默认真实 LLM，但仍保留 fake

本节有两条运行路径：

```text
默认 real LLM：
用真实模型跑同一批业务 case，观察当前 Prompt、模型和 schema 在真实调用下的表现。

可选 fake：
稳定制造 success / timeout / fallback / schema_parse，适合离线排查和学习 record 结构。
```

单元测试必须 fake，否则测试不稳定、受供应商影响。学习 demo 则默认真实模型，因为 harness 的核心价值正是观察同一批 case 在当前真实模型下 parse 是否通过、耗时多少、是否触发 fallback、错误分布是什么。

[`harness_compare.py`](../../source/demos/llm_regression_lab/harness_compare.py) 顶部提供：

```python
USE_REAL_LLM = True
```

默认运行会读取根目录 `.env`，用真实 `LLMClient` 接入同一个 `LLMCallingHarness`。如果需要稳定复现 schema failure 或 fallback，把它改成 `False`，仍运行同一条命令。

---

## Harness 与评估平台的责任边界

`pytest.mark.parametrize` 可以把 case 集变成测试输入，适合验证确定性行为：例如 parse 必须成功、schema failure 必须归类为 `schema_parse`、fallback 后 `degraded=True`。本节的 `test_harness.py` 就用 fake client 验证 harness 的结构，不依赖真实模型。

LangSmith、LangFuse 或企业内部 eval 平台通常会把 dataset、run、trace、annotation、dashboard 串起来。它们比本节完整得多，但底层思路相同：固定输入、记录配置、保存输出、对比版本、回流 bad case。

本仓库现在不接这些平台，是因为还没有到完整评估观测阶段。调用 Harness 先把 record 形状、run 边界和调用事实整理清楚，后续接平台才不会变成只会上传一段文本。

---

## 回归实验最容易得出的错误结论

### 1. Case 集太少导致虚假信心

- **表现**：默认样例一直成功，但真实需求一换就失败。
- **原因**：case 没覆盖不同业务类型、材料缺失、长上下文、异常输出。
- **怎么验证**：至少准备售后入口、优惠叠加、发票改造、材料不足几类样例；不要只跑 S2。

### 2. 把 parse 成功误当成质量正确

- **表现**：summary 里 parse 成功率很高，但人工看结果发现风险漏了。
- **原因**：schema 只校验形状，不校验事实完整性。
- **怎么验证**：把 `parse_ok` 当工程事实；准确性、引用正确性、拒答合理性进入 评估观测。

### 3. 只看最终 success，忽略 degraded

- **表现**：成功率没有下降，但回答质量变弱、耗时异常。
- **原因**：大量 case 是 fallback 成功，不是主路径成功。
- **怎么验证**：看 `degraded_count`、`attempt_count` 和 `final_config_ref`。如果降级上升，要回到 可靠调用 查 reliability。

### 4. 真实 LLM 路径没有固定变量

- **表现**：今天结果和昨天不同，但不知道改了什么。
- **原因**：没有固定 run config，或同时改了模型、Prompt、temperature、context。
- **怎么验证**：一次 run 尽量只改一个变量；把 run name 写清楚，例如 `risk_review_v4_deepseek_json_object`。

### 本节不做（defer）

| 能力 | 目标阶段 | 当节最小判断 |
| --- | --- | --- |
| 准确性、引用正确性、拒答评分 | 评估观测 | 调用 Harness 只记录可评分所需事实 |
| LangSmith / trace 平台接入 | 评估观测 | 调用 Harness 先保证 record 结构清楚 |
| 数据库存储与 run 版本管理 | 评估观测 / 项目篇 | 调用 Harness 默认只打印，不落盘 |
| Web dashboard | AI Native / 项目篇 | 调用 Harness 先用终端表格观察 |
| CI 质量门禁 | 项目工程化后段 | 调用 Harness 先建立可批量运行入口 |
| 成本、缓存优化 | 成本与缓存机制 | 调用 Harness 只记录 token / latency 字段 |

---

## 运行一轮可比较 Harness

### 目标

为需求评审助手增加一个轻量 calling harness：能批量运行固定 case，记录每条调用的结果、错误、解析状态、attempt 和降级情况，并输出汇总。

### 涉及文件

- [`source/packages/llm_core/harness/`](../../source/packages/llm_core/harness/)：harness 核心对象与 runner。
- [`source/packages/llm_core/tests/test_harness.py`](../../source/packages/llm_core/tests/test_harness.py)：fake client 单元测试。
- [`source/demos/llm_regression_lab/harness_compare.py`](../../source/demos/llm_regression_lab/harness_compare.py)：调用 Harness 观察入口，默认真实 LLM，支持 fake 对照路径。
- [`source/demos/llm_regression_lab/README.md`](../../source/demos/llm_regression_lab/README.md)：Harness 与 Cost 输出说明。

### 运行方式

默认真实 LLM 路径：

```bash
uv run pytest source/packages/llm_core/tests/test_harness.py
uv run python source/demos/llm_regression_lab/harness_compare.py
```

运行前确认根目录 `.env` 已配置 `OPENAI_API_KEY`，以及可选的 `OPENAI_BASE_URL` / `OPENAI_MODEL`。

模拟对照路径：

把 `harness_compare.py` 顶部改为：

```python
USE_REAL_LLM = False
```

仍运行：

```bash
uv run python source/demos/llm_regression_lab/harness_compare.py
```

模拟路径能稳定复现 success、schema failure、fallback，但它不代表真实模型表现。

### 输出怎么看

先看 `[records]`：

```text
case_id  status   parse  degraded  attempts  latency_ms  error
S1       success  ok     false     1         0.1         -
S2       success  ok     true      2         0.0         -
S3       failed   -      true      2         0.0         schema_parse
```

再看 `[summary]`：

```text
total: 3
success: 2
failed: 1
parse_success_rate: 67%
degraded: 2
errors: schema_parse=1
```

最后再看 `[detail]`。detail 只是内容预览，不是最终评估结论。调用 Harness 的阅读顺序必须是：先看 record 和 summary，再看文本内容。

---

## 亲手建立一次可比较回归

增加一条“证据不足时应提出待确认问题”的业务 Case，然后执行两轮 Run：

1. 两轮使用相同 Case 集、模型、温度、Schema 和 Context。
2. 第一轮使用原 Prompt，第二轮只切换 Prompt 版本。
3. 比较 parse、degraded、attempts、Token 和 latency。
4. 人工标注是否仍产生无依据风险。
5. 写出结论时区分调用事实和质量判断，不用 parse 成功率代替答案质量。

## 怎样判断已经建立回归能力

- 能解释 Harness、Eval、Reliability 三者的区别。
- 能说明为什么同一批 case 比单次 demo 更适合回归。
- 能说明 `HarnessCase`、`HarnessRunConfig`、`HarnessRunRecord`、`HarnessSummary` 各自为什么存在。
- 能运行 `test_harness.py`，理解 fake 单元测试如何稳定覆盖 success、schema failure、fallback。
- 能运行 `harness_compare.py`，读懂 `[records]` 与 `[summary]`。
- 能用默认 `USE_REAL_LLM=True` 跑真实模型，并说明真实路径观察什么、不保证什么。
- 能把 `USE_REAL_LLM=False` 作为对照，说明模拟路径只用于失败复现。
- 能说明 调用 Harness 为什么不做数据库、dashboard、LangSmith 和完整 eval 打分。

### 运行与观察

```bash
uv run pytest source/packages/llm_core/tests/test_harness.py
uv run python source/demos/llm_regression_lab/harness_compare.py
```

观察点：

- `S1` 是否普通成功。
- `S2` 是否 fallback 后成功，并保留 `degraded=true`。
- `S3` 是否最终失败，并把错误归到 `schema_parse`。
- summary 是否统计出成功数、解析成功率、降级数和错误分布。
- 默认真实 LLM 路径下，是否能看到真实模型的 parse、latency、token、error、degraded 分布。

### 自检题

1. 为什么 harness 不应该只记录最终文本？
2. 为什么 `parse_ok=True` 不等于答案质量正确？
3. 为什么 调用 Harness 要复用 `ReliableLLMService`，而不是直接调用 `LLMClient`？
4. 如果一次 Prompt 修改后 `success_count` 不变，但 `degraded_count` 上升，你会怎么判断风险？
5. 为什么学习 demo 默认用真实 LLM，但单元测试仍然用 fake？
6. 调用 Harness 的 record 到后续 eval 平台还缺哪些信息？

---

## 交给评估系统的调用事实

- `llm_core.harness` 把批量 case、run config、record 和 summary 沉淀为正式 package 能力。
- `llm_regression_lab` 承载 Harness 与按需 Cost；Reliability 已独立为 `llm_reliability_lab`，避免与早期主线混目录。
- 成本、延迟与缓存机制会继续消费 harness record。

完成实验后回到 [标准学习路径](../learning-path.md)。成本与缓存是 Harness 记录稳定后的 [按需支撑](cost-latency-and-caching.md)。
