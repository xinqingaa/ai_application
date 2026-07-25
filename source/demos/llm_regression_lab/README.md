# llm_regression_lab

> 课表位置：[标准学习路径](../../../course/learning-path.md) V0 步骤 20（Calling Harness，等待 RAG 前置）与按需 Cost。
> **不要在完成步骤 6 后立刻把本 lab 当主线。** Reliability 已独立到 [`llm_reliability_lab`](../llm_reliability_lab/)。

本 lab 观察：同一批 Case 如何批量运行、记录、汇总，以及 token / 成本 / 延迟 / exact-match cache 边界。

## 本 lab 调用面

允许：`LLMCallingHarness`、`HarnessCase` / `HarnessRunRecord` / `HarnessSummary`、`ReliableLLMService`、`costing`、`cache`。

不调用：`context` Builder（Cost 脚本里的 `context_fingerprint` 只是字符串指纹，不是 Context Engineering）、`streaming`。

正式用 Harness 比较「直接 LLM vs 检索 RAG」时，需要 RAG 链路可跑；当前脚本可先观察直接 LLM 的 Case / Record 形状。

## 跑序

| 顺序 | 脚本 | 课表 | 说明 |
| --- | --- | --- | --- |
| 1 | `harness_compare.py` | 步骤 20 | Case 批量运行与汇总 |
| 2 | `cost_latency_cache.py` | 按需支撑 | 依赖 Harness 记录形态；比较预算、延迟、cache hit/miss |

```bash
# 仓库根目录
uv sync
uv run python source/demos/llm_regression_lab/harness_compare.py
uv run python source/demos/llm_regression_lab/cost_latency_cache.py
```

默认真实模型。离线复现时在脚本顶部将 `USE_REAL_LLM` 改为 `False`。

## harness 输出怎么看

```text
[harness]
→ [records]
→ [summary]
→ [detail]
→ [lesson]
```

1. `[records]`：`status`、`parse`、`degraded`、`attempts`、`tokens`、`cost`、`error`  
2. `[summary]`：成功数、解析成功率、降级数、错误分布  
3. `[detail]`：内容预览，不是完整评估结论  

| 开关 | 默认值 | 含义 |
| --- | --- | --- |
| `USE_REAL_LLM` | `True` | 真实 `LLMClient`；`False` 本地模拟 |
| `PRINT_RECORD_DETAIL` | `True` | 打印内容预览或错误 |
| `PRIMARY_CONFIG_REF` | `"chat.dev_chat"` | 主模型 |
| `FALLBACK_CONFIG_REF` | `"chat.fallback_chat"` | fallback |

## cost / latency / cache 输出怎么看

```text
[cost_latency]
→ [records:cold]
→ [summary:cold]
→ [cache_rounds]
→ [records:repeat]
→ [budget_shape]
→ [lesson]
```

1. cold 记录是否含 `tokens` / `latency_ms` / `cost`  
2. summary 的总量与平均延迟  
3. cold 应 miss；同输入 repeat 应 hit；`changed_context` 应 miss  
4. 理解不同调用形状的成本差异  

| 开关 | 默认值 | 含义 |
| --- | --- | --- |
| `USE_REAL_LLM` | `True` | 真实模型 |
| `ENABLE_CACHE` | `True` | 进程内 exact-match cache |
| `CONTEXT_FINGERPRINT` | `"ctx-review-rules-v1"` | 证据上下文版本指纹（学习用） |

`cost` 是学习用估算，不是供应商账单。

## 相关

- Package：[source/packages/llm_core/](../../packages/llm_core/)
- [Calling Harness](../../../course/mechanisms/calling-harness-and-regression.md)
- [Token、成本、延迟与缓存](../../../course/mechanisms/cost-latency-and-caching.md)
- 步骤 6：[llm_reliability_lab](../llm_reliability_lab/)
