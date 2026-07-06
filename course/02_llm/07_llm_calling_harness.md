# 07. LLM Calling Harness

> 06 已经让一次模型调用具备错误分类、有限重试、fallback 和 attempt report。本篇继续回答：**当你开始反复修改 Prompt、模型、Schema 和 Context 时，如何用一组稳定 case 记录调用结果，而不是凭“我刚才跑了一次感觉还行”判断质量**。

---

## 真实问题

05 和 06 之后，需求评审助手已经不再是裸调模型：输入经过 context builder，输出经过 structured parse，调用经过 reliability shell。到这里，很容易进入另一种误区：每改一次 Prompt 或模型，手动跑一个 demo，看终端输出还不错，就认为系统变好了。

真实项目里这不够。你可能把 `risk_review_v3` 改成 `v4`，默认样例 S2 看起来更稳，但 S1 的需求摘要开始遗漏状态机风险；你可能把模型从 `chat.dev_chat` 切到 fallback，解析成功率没变，但风险描述更空泛；你可能缩短 context budget，token 降低了，但 citation 变少；你也可能只盯最终文本，忽略了 `schema_parse`、`degraded=True` 和 attempt 数量变多。

本节要解决的不是完整评估打分。完整的准确性、引用正确性、拒答合理性、人工标注、趋势面板会进入后续 `05_eval_observability`。07 先做更基础的一层：**把同一批调用样例稳定跑起来，并把每次调用变成可比较的记录**。

### 学习者真实问题

如果你有前端 / Flutter / 客户端经验，可以把 harness 类比成 UI 组件的快照用例或接口契约样例。你不会只点一次按钮说“这个页面没问题”，而会准备几组输入：空数据、长文本、异常状态、权限不足、弱网重试。每次改组件，都用同一批输入重新跑，至少确认没有明显退化。

LLM 调用也需要类似思路。区别在于，LLM 的输出不是固定字符串，不能只做简单断言。07 的 harness 不要求“答案必须一字不差”，而是先记录这些事实：

- 哪个 case 跑了。
- 用了哪个 `config_ref`、Prompt 或 structured mode。
- 最终成功还是失败。
- 结构化解析是否通过。
- 是否发生 retry / fallback。
- token、latency、错误码是什么。

这一步看似朴素，但它把学习方式从“单次 demo 感觉”推进到“同一批输入的可回归记录”。

### 产品真实问题

继续看需求评审助手。产品里至少会有几类稳定样例：

- 售后入口：重点看订单状态、售后接口、三端入口一致性。
- 优惠叠加：重点看业务规则优先级、金额计算、边界状态。
- 发票改造：重点看历史记录复用、权限、异常输入。
- 材料不足：重点看是否追问，而不是编造结论。

如果每次只跑售后入口，你会对系统产生虚假信心。真正有用的反馈应该像这样：

```text
本次 run：
1. 一共 12 条 case；
2. 10 条结构化解析成功；
3. 2 条失败，其中 1 条 schema_parse，1 条 timeout；
4. 3 条发生 fallback；
5. 平均耗时比上次高。
```

这还不是最终质量评估，但它已经能提醒你：本次改动可能引入了工程退化，需要继续看 bad case。

### 工程真实问题

工程上，harness 至少要把四类对象分开：

| 对象 | 解决什么问题 | 本节落点 |
| --- | --- | --- |
| Case | 固定输入是什么 | `HarnessCase` |
| Run Config | 本次用什么模型、参数、结构化模式 | `HarnessRunConfig` |
| Record | 每条 case 的调用事实 | `HarnessRunRecord` |
| Summary | 一批 case 的汇总事实 | `HarnessSummary` |

如果没有这些对象，后续 eval 会缺少原始数据；如果一上来就做完整平台，又会把学习压成数据库、看板和 CI 的工程泥潭。本节选择中间路线：先把 harness 内核沉淀到 `llm_core.harness`，demo 只作为观察入口。

---

## 基础原理

### 本节方案性质

Harness 没有唯一标准形态。企业里可能使用 LangSmith dataset、内部 eval 平台、数据库 run 表、CI 门禁、人工标注系统和 dashboard。本仓库 07 先做本地轻量版。

| 层级 | 本节怎么理解 |
| --- | --- |
| 通用原则 | 用固定 case 集重复运行；记录输入、配置、输出、错误、耗时和解析结果 |
| 工程实践 | `LLMCallingHarness` 复用 `ReliableLLMService`，返回 records + summary |
| 项目取舍 | 先打印终端表格，不落数据库，不做完整评分 |
| 非目标 | 不做 LangSmith 接入、不做 dashboard、不做 CI 门禁、不做人评平台 |

### 先用一个小例子抓住主线

假设你有三条需求评审 case：

```text
S1：售后入口
S2：优惠叠加
S3：发票改造
```

你想比较当前 Prompt 是否还能稳定输出结构化风险列表。单次调用只能回答“某一条有没有返回”。Harness 要回答的是“一组输入整体表现如何”。

数据流是：

```text
HarnessCase[]
→ HarnessRunConfig
→ LLMCallingHarness
→ ReliableLLMService.chat_structured
→ HarnessRunRecord[]
→ HarnessSummary
```

这条链路刻意复用了 06 的 reliable shell。原因很简单：如果一次 case 发生了 fallback，harness 不能只记录“成功”，还要记录 `degraded=True` 和 attempt 数量。否则后续你会把降级成功误看成普通成功。

### Harness 和 Eval 的区别

Harness 是调用外壳，Eval 是质量判断。它们相关，但不是一件事。

| 维度 | Harness | Eval |
| --- | --- | --- |
| 关注点 | 调用事实是否可记录、可回归 | 结果质量是否正确、完整、可信 |
| 典型字段 | status、parse_ok、latency、error_code、degraded | accuracy、citation correctness、refusal quality |
| 本节是否实现 | 是 | 否，后续 `05_eval_observability` |
| 失败例子 | 没记录 schema_parse，无法复盘 | 记录了结果，但不知道答案是否准确 |

反例：如果只做 harness，你能知道 S2 解析成功，却不知道它漏掉了“优惠叠加优先级”。如果只做 eval，但没有 harness record，你又很难追溯那次结果用了哪个模型、是否 fallback、耗时是否异常。

### 从弱到强的机制递进

**第 1 步 · 手动跑一个 demo**

最快，但只能看到一个输入的一次结果。反例：S2 正常不代表 S1、S3 正常。

**第 2 步 · 固定一组 case**

开始具备回归意识，但如果只看终端文本，仍然难以比较。反例：两次输出都像中文答案，但一次 parse 失败。

**第 3 步 · 记录 run config**

知道本次用了哪个模型、参数和 structured mode。仍遗留：每条 case 的调用事实没有统一结构。

**第 4 步 · 生成 run record**

每条 case 都记录 status、parse、latency、error、degraded。仍遗留：一批 case 的整体趋势不明显。

**第 5 步 · 汇总 summary**

得到成功率、解析成功率、错误分布和平均耗时。仍遗留：答案质量还没有被打分；这进入后续 eval。

---

## 最小实现

本节把 harness 放进 [`llm_core.harness`](../../source/packages/llm_core/harness/)，不是写在 demo 脚本里。demo 只负责构造样例、调用 package、打印表格。

### 1. Case 和运行配置

[`harness/cases.py`](../../source/packages/llm_core/harness/cases.py) 定义输入和本次运行配置：

```python
@dataclass(frozen=True)
class HarnessCase:
    case_id: str
    title: str
    messages: list[dict[str, str]]
    expected_focus: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class HarnessRunConfig:
    run_name: str
    config_ref: str = "chat.dev_chat"
    structured: bool = True
    structured_mode: StructuredMode = "json_object"
```

`expected_focus` 不是本节的自动评分规则，只是给后续 eval 留下“这条 case 本来应该关注什么”的入口。07 不用它打分，避免把 harness 和 eval 混在一起。

### 2. Record 和 Summary

[`harness/records.py`](../../source/packages/llm_core/harness/records.py) 把每条调用结果记录下来：

```python
@dataclass(frozen=True)
class HarnessRunRecord:
    case_id: str
    title: str
    status: str
    config_ref: Optional[str]
    parse_ok: Optional[bool] = None
    risk_count: Optional[int] = None
    latency_ms: float = 0.0
    error_code: Optional[LLMErrorCode] = None
    attempt_count: int = 0
    degraded: bool = False
```

注意这里记录的是“调用事实”。`parse_ok=True` 不代表答案正确，只代表它通过了应用 schema。`degraded=True` 不代表答案不可用，只代表它不是主路径普通成功。

### 3. Runner 复用可靠调用

[`harness/runner.py`](../../source/packages/llm_core/harness/runner.py) 的关键取舍是：harness 不直接调 provider，而是调 `ReliableLLMService`。

```python
records, summary = LLMCallingHarness(service).run_cases(
    cases,
    HarnessRunConfig(run_name="risk_review_v4_smoke"),
)
```

这样 06 的 attempt report 会进入 07 的 record。后续如果一次 case 因 timeout 后 fallback 成功，record 仍能保留 `attempt_count=2` 和 `degraded=True`。

---

## 主流框架实现

`pytest.mark.parametrize` 可以把 case 集变成测试输入，适合做确定性断言，例如“parse 必须成功”“错误码必须是 schema_parse”。本节的 `test_harness.py` 就用 fake client 验证核心行为。

LangSmith / LangFuse / 内部 eval 平台通常会提供 dataset、run、trace、annotation 和 dashboard。它们比本节完整得多，但底层问题相同：固定输入、记录配置、保存输出、对比版本、回流 bad case。

自定义 lightweight harness 适合学习期和项目早期。它不替代企业平台，但能帮你先建立正确的数据形状，避免后续 eval 平台只剩一个空壳。

---

## 失败分析与能力边界

### 1. 样例太少带来虚假信心

- **表现**：默认样例一直成功，但真实需求一换就失控。
- **原因**：case 集没有覆盖不同业务类型、材料缺失、长上下文和异常输出。
- **怎么验证**：至少准备摘要、风险识别、材料不足、结构化报告等不同类型 case；不要只跑 S2。

### 2. 只看文本，不看 record 字段

- **表现**：输出看起来像中文答案，但前端或后续 workflow 不能用。
- **原因**：忽略 `parse_ok`、`error_code`、`degraded`、`attempt_count`。
- **怎么验证**：先看 `[records]` 和 `[summary]`，再看内容 preview。

### 3. Harness 被误当成完整评估系统

- **表现**：看到 parse 成功率 100%，就认为模型质量很好。
- **原因**：schema 通过不等于事实正确、引用正确或结论完整。
- **怎么验证**：把 harness record 作为后续 eval 输入，而不是最终质量结论。

### 本节不做（defer）

| 能力 | 目标阶段 | 当节最小判断 |
| --- | --- | --- |
| 准确性、引用正确性、拒答评分 | `05_eval_observability` | 07 只记录可评分所需事实 |
| LangSmith / trace 平台接入 | `05_eval_observability` | 07 先保证 record 结构清楚 |
| 数据库存储与 run 版本管理 | `05_eval_observability` / `07_projects` | 07 默认只打印，不落盘 |
| Web dashboard | `06_ai_native` / `07_projects` | 07 先用终端表格观察 |
| CI 质量门禁 | 项目工程化后段 | 07 先建立可批量运行入口 |
| 成本、缓存优化 | `02_llm/08` | 07 只记录 token / latency 字段 |

---

## 本节实战

### 目标

为需求评审助手增加一个轻量 calling harness：能批量运行固定 case，记录每条调用的结果、错误、解析状态、attempt 和降级情况，并输出汇总。

### 涉及文件

- [`source/packages/llm_core/harness/`](../../source/packages/llm_core/harness/)：harness 核心对象与 runner。
- [`source/packages/llm_core/tests/test_harness.py`](../../source/packages/llm_core/tests/test_harness.py)：fake client 单元测试。
- [`source/demos/02_call_ops_lab/harness_compare.py`](../../source/demos/02_call_ops_lab/harness_compare.py)：07 观察入口。
- [`source/demos/02_call_ops_lab/README.md`](../../source/demos/02_call_ops_lab/README.md)：call ops lab 输出说明。

### 运行方式

```bash
uv run pytest source/packages/llm_core/tests/test_harness.py
uv run python source/demos/02_call_ops_lab/harness_compare.py
```

`harness_compare.py` 默认使用 fake client，不调用真实模型。它的目标不是评估答案质量，而是观察 harness record 如何承接 06 的 reliable report。

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

这说明：本次有 3 条 case，2 条成功，1 条结构化失败；其中 2 条发生了 fallback。它不是最终质量评估，但已经能提醒你：这批调用存在退化风险。

---

## 完成标准

- 能解释 Harness、Eval、Reliability 三者的区别。
- 能说明为什么同一批 case 比单次 demo 更适合回归。
- 能读懂 `HarnessCase`、`HarnessRunConfig`、`HarnessRunRecord`、`HarnessSummary`。
- 能运行 `test_harness.py` 并理解成功、schema failure、fallback 三类路径。
- 能运行 `harness_compare.py`，读懂 `[records]` 与 `[summary]`。
- 能说明 07 为什么不做数据库、dashboard、LangSmith 和完整 eval 打分。

### 运行与观察

```bash
uv run pytest source/packages/llm_core/tests/test_harness.py
uv run python source/demos/02_call_ops_lab/harness_compare.py
```

观察点：

- `S1` 是否普通成功。
- `S2` 是否 fallback 后成功，并保留 `degraded=true`。
- `S3` 是否最终失败，并把错误归到 `schema_parse`。
- summary 是否统计出成功数、解析成功率、降级数和错误分布。

### 自检题

1. 为什么 harness 不应该只记录最终文本？
2. 为什么 `parse_ok=True` 不等于答案质量正确？
3. 为什么 07 要复用 `ReliableLLMService`，而不是直接调用 `LLMClient`？
4. 如果一次 Prompt 修改后 `success_count` 不变，但 `degraded_count` 上升，你会怎么判断风险？
5. 07 的 record 到后续 eval 平台还缺哪些信息？

---

## 本节沉淀

- `llm_core` 新增 `harness/`，把批量 case、run config、record 和 summary 沉淀为正式 package 能力。
- `02_call_ops_lab` 继续承载调用治理实验，避免为 07 再创建孤立 demo。
- 下一节 08 会在 harness record 基础上继续观察成本、延迟和缓存边界。

---

## 相关专题

- 上一篇：[06_reliability_errors_and_degradation.md](06_reliability_errors_and_degradation.md)
- 下一篇：08 Cost、Latency 与 Caching（待落地）
- 课程大纲：[outline.md](outline.md)
