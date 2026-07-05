# 02 Reliability Errors Demo

本 demo 对应 `course/02_llm/06_reliability_errors_and_degradation.md`，用于观察一次 LLM 调用失败后，应用侧如何重试、降级，并输出可读的尝试报告。

默认使用本地模拟，不调用真实模型，也不保存任何文件。

## 运行

```bash
uv run python source/demos/02_reliability_errors/reliability_compare.py
```

## 顶部配置开关

打开 [`reliability_compare.py`](reliability_compare.py) 顶部，可以改这些值：

| 开关 | 默认值 | 含义 |
| --- | --- | --- |
| `DEFAULT_CASE` | `"timeout_then_success"` | 选择要观察的失败场景 |
| `USE_REAL_LLM` | `False` | 是否调用真实模型；默认不消耗额度 |
| `PRINT_MESSAGES` | `False` | 是否打印发给模型的 messages |
| `PRINT_ATTEMPT_DETAIL` | `True` | 是否打印每次失败的错误详情 |
| `COMPARE_WITH_NO_RETRY` | `True` | 是否先跑一组无重试对照 |

可选 case：

| case | 观察点 |
| --- | --- |
| `timeout_then_success` | 第一次超时，第二次重试成功 |
| `primary_timeout_then_fallback` | 主模型重试失败后切到 fallback |
| `auth_error` | 鉴权失败不重试、不降级 |
| `schema_failure` | 结构化失败应被视为可靠性失败 |

## 输出怎么看

终端输出按固定顺序分段：

```text
[case]
→ [call_plan]
→ [messages]        # 仅 PRINT_MESSAGES=True 时出现
→ [attempts]
→ [final]
→ [lesson]
```

读输出时按三步：

1. 先看 `[call_plan]`：本次允许重试几次，有没有 fallback。
2. 再看 `[attempts]`：每一次调用是成功、超时、限流，还是其他错误。
3. 最后看 `[final]`：本次最终是成功、失败，还是降级成功。

示例：

```text
[attempts]
  [1] config=chat.dev_chat status=failed code=timeout
  [2] config=chat.dev_chat status=success latency_ms=1.0

[final]
  [status] success
  [final_config] chat.dev_chat
  [degraded] false
```

这说明主模型第一次超时，但第二次重试成功。它不是“模型一直稳定”，而是应用侧把可恢复失败限制在可控次数内，并把过程记录下来。

如果看到：

```text
[final]
  [status] failed
  [final_error] auth
```

说明这是不可恢复配置问题。此时不应该继续重试，应该检查 `.env`、API key、`config_ref` 和供应商配置。

## 真实模型调用

如果要观察真实调用，把脚本顶部改为：

```python
USE_REAL_LLM = True
```

仍运行同一条命令：

```bash
uv run python source/demos/02_reliability_errors/reliability_compare.py
```

真实模型不一定会触发失败；它主要用于确认可靠性外壳在成功路径下也能输出 report。要稳定观察失败路径，使用默认模拟 case。
