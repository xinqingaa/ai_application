# 02_context_lab

Context Engineering 观察 demo。它不是新的业务实现，也不承载核心算法；核心逻辑在 [`llm_core.context`](../../packages/llm_core/context/)，本 demo 只加载样例、选择策略、调用 package API 并打印诊断报告。

课程正文负责解释 Context Engineering 的机制；本 README 负责说明怎么跑、怎么看输出、如何定位 bad case。

## 为什么单独建 demo

这里的观察维度不是“模型是否返回 JSON”，而是：

- 候选材料如何进入材料池。
- 不同策略如何分配 section budget。
- 哪些 source 被 included / dropped / compressed。
- 哪些 source 可以成为 citation candidate。
- Prompt 预览是否符合预期。
- bad case 应该查预算、排序、压缩、Prompt，还是模型。

这些维度如果继续塞进 `02_model_contracts/structured_risk.py`，会把 Structured Outputs 与 Context Engineering 混在一起。因此单独保留这个观察入口，但仍复用同一个 `llm_core` package。

## 文件

| 文件 | 职责 |
| --- | --- |
| `context_cases.json` | 一个较真实的需求评审材料池：PRD、业务规则、接口文档、客户端说明、历史评审、Agent 摘要和过期噪声材料 |
| `context_compare.py` | 调用 `llm_core.context` 的策略对比脚本，不实现核心算法 |

## 运行

仓库根目录先安装：

```bash
uv sync
```

默认运行 `evidence_first`，并调用真实模型。请先确认根目录 `.env` 已配置 `OPENAI_API_KEY`（以及需要时的 `OPENAI_BASE_URL` / `OPENAI_MODEL`）：

```bash
uv run python source/demos/02_context_lab/context_compare.py
```

常用开关在 [`context_compare.py`](context_compare.py) 顶部，改完后仍运行上面这一条短命令：

```python
DEFAULT_STRATEGY = "evidence_first"
CALL_LLM = True
COMPARE_WITH_MINIMAL = False
PRINT_MESSAGES = False
PRINT_FULL_CONTEXT = False
```

真实项目里这些值通常来自配置文件、环境变量、数据库配置或后台管理页；本 demo 为了学习方便，先集中放在脚本顶部。

## 配置开关

| 开关 | 含义 | 常用改法 |
| --- | --- | --- |
| `DEFAULT_STRATEGY` | 本次使用哪种上下文构建策略 | `"evidence_first"` 看默认证据优先；`"tight_budget"` 看紧预算压缩；`"minimal"` 看不带证据；`"all"` 看全部策略 |
| `CALL_LLM` | 是否调用真实模型 | 默认 `True` 输出 `[llm_result]`；改为 `False` 时只看上下文构建诊断 |
| `COMPARE_WITH_MINIMAL` | 是否额外跑一遍 `minimal` 做对照 | `True` 时会先跑不带证据，再跑 `DEFAULT_STRATEGY`；适合比较带/不带上下文差异 |
| `PRINT_MESSAGES` | 是否打印完整 system / user messages | `True` 时能看到最终发给模型的完整 Prompt，适合学习 Prompt 和 context 如何合并 |
| `PRINT_FULL_CONTEXT` | 是否打印完整 context block | `True` 时不截断上下文，适合排查某条 source 是否真的进入 Prompt |

几个常见组合：

| 想观察什么 | 推荐配置 |
| --- | --- |
| 默认真实模型结果 | `DEFAULT_STRATEGY = "evidence_first"`，`CALL_LLM = True` |
| 离线上下文诊断 | `DEFAULT_STRATEGY = "evidence_first"`，`CALL_LLM = False` |
| 紧预算压缩 | `DEFAULT_STRATEGY = "tight_budget"`，`CALL_LLM = True` |
| 带/不带证据对比 | `DEFAULT_STRATEGY = "evidence_first"`，`COMPARE_WITH_MINIMAL = True`，`PRINT_MESSAGES = True` |

`CALL_LLM=True` 或 `COMPARE_WITH_MINIMAL=True` 会读取根目录 `.env`，用 `review.risk_review@4.0.0` + `chat_structured(..., json_object)` 做结构化风险识别。

## 策略怎么看

策略由 package 提供：`llm_core.get_context_policy(...)`。

| 策略 | 观察重点 |
| --- | --- |
| `minimal` | 只保留 Requirement，所有 evidence 被排除；观察无证据时的 warning |
| `full_context` | 尽量保留全部材料；观察噪声、历史和过期 source 是否进入上下文 |
| `balanced` | 需求、证据、历史、Agent 摘要都有预算；观察默认工程取舍 |
| `evidence_first` | 证据优先，历史和 Agent 摘要预算较小；适合结构化风险审查 |
| `tight_budget` | 小预算 + 压缩；观察 compressed / dropped source |
| `agent_summary_only` | 只允许 Agent 摘要类 source；观察中间结论与证据引用的边界 |

## 输出字段

| 字段 | 含义 |
| --- | --- |
| `[context_build]` | 下面是上下文构建诊断，不是模型最终回答 |
| `[included_sources]` | 最终进入 Prompt 的 source id |
| `[section_tokens]` | requirement / evidence / history / agent_summary / other 各 section 的估算 tokens |
| `[citation_candidates]` | 允许模型引用的证据 source；history 和 agent_summary 不进入 citation candidates |
| `[compressed_sources]` | 被确定性压缩过的 source |
| `[dropped_sources]` | 未进入 Prompt 的 source 及原因 |
| `[warnings]` | 可用于调试的上下文异常或风险提示 |
| `[built_context_preview]` | 最终上下文块预览；这是即将进入 Prompt 的材料 |
| `[llm_result] not_run` | 仅在 `CALL_LLM=False` 时出现；表示本次只看上下文构建诊断 |

真实调用时还会看到：

| 字段 | 含义 |
| --- | --- |
| `[messages]` | `PRINT_MESSAGES = True` 时打印的完整 system / user 输入 |
| `[llm_result] parse=ok` | 模型返回通过结构化解析；这里才是模型结果 |
| `tokens` / `latency_ms` | 供应商返回的 token 用量和耗时 |
| `cites=...` | 每条风险声明引用的 source id |

## 经典输出怎么看

若配置为：

```python
DEFAULT_STRATEGY = "evidence_first"
COMPARE_WITH_MINIMAL = True
PRINT_MESSAGES = True
```

终端会先输出 `minimal`，再输出 `evidence_first`。建议按下面顺序读，不要从头到尾硬啃。

### 1. 看策略

```text
[strategy] minimal
```

表示只带 Requirement，不带 Evidence。它是“无上下文”的对照组。

```text
[strategy] evidence_first
```

表示优先带业务规则、接口文档和客户端说明。它是“带证据上下文”的实验组。

### 2. 看上下文构建

`minimal` 里通常会看到：

```text
[included_sources] —
[citation_candidates] —
no_evidence_included
```

意思是：没有任何 source 进入 Prompt，也没有合法引用候选。

`evidence_first` 里通常会看到：

```text
[included_sources] BR-ORDER-STATE, API-AFTER-SALE-V2, CLIENT-DETAIL-API
[citation_candidates] BR-ORDER-STATE, API-AFTER-SALE-V2, CLIENT-DETAIL-API
```

意思是：模型可以基于这三条证据输出引用。

### 3. 看 messages

`messages` 是最终发给模型的完整输入。重点确认：

- `minimal` 的 Evidence 段是“无可用证据”。
- `evidence_first` 的 Evidence 段确实包含三个 source id。

### 4. 看模型结果

```text
[llm_result] parse=ok risks=...
```

这才是模型输出结果。读每条风险时，重点看 `cites=...`。

如果 `minimal` 输出 `cites=PRD片段`，但 `citation_candidates` 为空，说明模型自造了引用名。结构化解析通过了，不代表 citation 可信。

如果 `evidence_first` 输出 `cites=API-AFTER-SALE-V2`，并且它在 `citation_candidates` 里，说明这条引用至少指向了本次 Prompt 中真实存在的证据。

## 常见定位

| 现象 | 优先检查 |
| --- | --- |
| 模型引用了不存在的 source id | `[citation_candidates]` 是否包含它；若不包含，属于模型编造或 Prompt 约束不足 |
| 关键接口文档没进入 Prompt | `[dropped_sources]` reason；看是预算不足、重复内容、还是策略排除 |
| 历史评审污染当前结果 | 换 `evidence_first` 或调低 history budget，观察输出是否更贴当前需求 |
| `tight_budget` 下内容断裂 | 看 `[compressed_sources]` 与 `prompt_preview`，确认 source id 是否仍保留 |
| 无 evidence 仍生成确定结论 | `[warnings] no_evidence_included`；Prompt 或调用层应提示依据不足 |

## 与 结构化输出 demo 的关系

- `02_model_contracts/structured_risk.py`：观察 structured output 三种 mode。
- `02_context_lab/context_compare.py`：观察 context builder 策略和诊断。

二者都调用 `llm_core`，但观察问题不同。
