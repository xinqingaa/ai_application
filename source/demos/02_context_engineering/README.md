# 02_context_engineering

`02_llm/05` 的上下文工程观察 demo。它不是新的业务实现，也不承载核心算法；核心逻辑在 [`llm_core.context`](../../packages/llm_core/context/)，本 demo 只加载样例、选择策略、调用 package API 并打印诊断报告。

课程正文负责解释 Context Engineering 的机制；本 README 负责说明怎么跑、怎么看输出、如何定位 bad case。

## 为什么单独建 demo

05 的观察维度不是“模型是否返回 JSON”，而是：

- 候选材料如何进入材料池。
- 不同策略如何分配 section budget。
- 哪些 source 被 included / dropped / compressed。
- 哪些 source 可以成为 citation candidate。
- Prompt 预览是否符合预期。
- bad case 应该查预算、排序、压缩、Prompt，还是模型。

这些维度如果继续塞进 `02_provider_switching/structured_risk.py`，会把 03 Structured Outputs 与 05 Context Engineering 混在一起。因此本节单独建 demo，但仍复用同一个 `llm_core` package。

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

默认离线运行，不需要 API key：

```bash
uv run python source/demos/02_context_engineering/context_compare.py
```

只看某个策略：

```bash
uv run python source/demos/02_context_engineering/context_compare.py --strategy evidence_first
uv run python source/demos/02_context_engineering/context_compare.py --strategy tight_budget
```

可选真实模型调用：

```bash
uv run python source/demos/02_context_engineering/context_compare.py --strategy evidence_first --call-llm
```

`--call-llm` 会读取根目录 `.env`，用 `review.risk_review@4.0.0` + `chat_structured(..., json_object)` 做一次结构化风险识别。默认不调用模型，是为了让 context 诊断本身可离线观察、可测试。

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
| `[included_sources]` | 最终进入 Prompt 的 source id |
| `[section_tokens]` | requirement / evidence / history / agent_summary / other 各 section 的估算 tokens |
| `[citation_candidates]` | 允许模型引用的证据 source；history 和 agent_summary 不进入 citation candidates |
| `[compressed_sources]` | 被确定性压缩过的 source |
| `[dropped_sources]` | 未进入 Prompt 的 source 及原因 |
| `[warnings]` | 可用于调试的上下文异常或风险提示 |
| `[prompt_preview]` | 最终上下文块预览 |

## 常见定位

| 现象 | 优先检查 |
| --- | --- |
| 模型引用了不存在的 source id | `[citation_candidates]` 是否包含它；若不包含，属于模型编造或 Prompt 约束不足 |
| 关键接口文档没进入 Prompt | `[dropped_sources]` reason；看是预算不足、重复内容、还是策略排除 |
| 历史评审污染当前结果 | 换 `evidence_first` 或调低 history budget，观察输出是否更贴当前需求 |
| `tight_budget` 下内容断裂 | 看 `[compressed_sources]` 与 `prompt_preview`，确认 source id 是否仍保留 |
| 无 evidence 仍生成确定结论 | `[warnings] no_evidence_included`；Prompt 或调用层应提示依据不足 |

## 与 03 demo 的关系

- `02_provider_switching/structured_risk.py`：观察 structured output 三种 mode。
- `02_context_engineering/context_compare.py`：观察 context builder 策略和诊断。

二者都调用 `llm_core`，但观察问题不同。
