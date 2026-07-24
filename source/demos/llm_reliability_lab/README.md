# llm_reliability_lab

> 课表位置：[标准学习路径](../../../course/learning-path.md) V0 步骤 6（可学习）。  
> 必要前置：步骤 3–5（Provider、Prompt、Structured）。  
> 本 lab **不包含** Harness / Cost；那些在后续 [`llm_regression_lab`](../llm_regression_lab/)。

观察可靠调用外壳如何记录 attempt、重试、fallback 与显式失败。

## 本 lab 调用面

允许：`ReliableLLMService`、`RetryPolicy`、`DegradationPolicy`、`LLMClient`、`errors`、结构化 parse（用于 schema failure 对照）。

不调用：`context`、`harness`、`streaming`、`conversation`、`cache`（作为本节主观察对象）。

## 运行

```bash
# 仓库根目录
uv sync
uv run python source/demos/llm_reliability_lab/reliability_compare.py
```

默认调用真实模型。需要稳定复现 timeout、fallback、auth 或 schema failure 时，在脚本顶部把 `USE_REAL_LLM` 改为 `False`。

## 输出怎么看

```text
[case]
→ [call_plan]
→ [messages]        # 仅 PRINT_MESSAGES=True 时出现
→ [attempts]
→ [final]
→ [lesson]
```

1. `[call_plan]`：允许重试几次，有没有 fallback。  
2. `[attempts]`：每次成功、超时、限流或其他错误。  
3. `[final]`：最终成功、失败，还是降级成功。

## 实验开关

| 开关 | 默认值 | 含义 |
| --- | --- | --- |
| `DEFAULT_CASE` | `"timeout_then_success"` | 失败场景 |
| `USE_REAL_LLM` | `True` | 真实模型；`False` 时本地模拟失败路径 |
| `PRINT_MESSAGES` | `False` | 打印发给模型的 messages |
| `PRINT_ATTEMPT_DETAIL` | `True` | 打印每次失败详情 |
| `COMPARE_WITH_NO_RETRY` | `True` | 先跑无重试对照 |

| case | 观察点 |
| --- | --- |
| `timeout_then_success` | 第一次超时，第二次重试成功 |
| `primary_timeout_then_fallback` | 主模型重试失败后切 fallback |
| `auth_error` | 鉴权失败不重试、不降级 |
| `schema_failure` | 结构化失败应被视为可靠性失败 |

## 相关

- Package：[source/packages/llm_core/](../../packages/llm_core/)
- 机制篇：[Reliability 与错误分类](../../../course/mechanisms/reliability-and-errors.md)
- 下一步（课表）：完成 RAG 前置后进入 Context；Harness 在 [`llm_regression_lab`](../llm_regression_lab/)
