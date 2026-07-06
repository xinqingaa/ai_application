# 02 Call Ops Lab

这个 lab 承载 `02_llm` 后半段的调用治理实验，不再按“一节一个 demo”继续拆目录。

- `reliability_compare.py`：对应 06，观察 retry、fallback、schema failure 和 attempt report。
- `harness_compare.py`：对应 07，观察一组 case 如何批量运行、记录、汇总。

两个入口默认都使用本地模拟，不调用真实模型，也不保存任何文件。需要观察真实模型时，在脚本顶部打开对应 `USE_REAL_LLM` 开关。

## 运行

```bash
uv run python source/demos/02_call_ops_lab/reliability_compare.py
uv run python source/demos/02_call_ops_lab/harness_compare.py
```

## reliability 输出怎么看

输出按固定顺序分段：

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

`reliability_compare.py` 顶部可改：

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

## harness 输出怎么看

`harness_compare.py` 输出按固定顺序分段：

```text
[harness]
→ [records]
→ [summary]
→ [detail]
→ [lesson]
```

读输出时按三步：

1. 先看 `[records]`：每条 case 的 `status`、`parse`、`degraded`、`attempts` 和 `error`。
2. 再看 `[summary]`：这一批 case 的成功数、解析成功率、降级数和错误分布。
3. 最后看 `[detail]`：只作为内容预览，不把它当成完整评估结论。

典型记录：

```text
case_id  status   parse  degraded  attempts  latency_ms  error
S1       success  ok     false     1         1.0         -
S2       success  ok     true      2         2.0         -
S3       failed   -      true      2         2.0         schema_parse
```

这说明 harness 不只看最终文本，而是把 parse、降级、attempt 和错误码都记录下来，给后续 eval / observability 使用。

`harness_compare.py` 顶部可改：

| 开关 | 默认值 | 含义 |
| --- | --- | --- |
| `USE_REAL_LLM` | `False` | 是否用真实 `LLMClient` 跑同一批 case |
| `PRINT_RECORD_DETAIL` | `True` | 是否打印每条 case 的内容预览或错误信息 |
| `PRIMARY_CONFIG_REF` | `"chat.dev_chat"` | 主模型配置 |
| `FALLBACK_CONFIG_REF` | `"chat.fallback_chat"` | fallback 模型配置 |

真实模型路径会读取根目录 `.env`。它的目的不是稳定触发失败，而是观察同一批业务 case 在当前模型、Prompt 和结构化输出约束下的真实调用事实：parse 是否通过、是否降级、耗时和错误分布如何。
