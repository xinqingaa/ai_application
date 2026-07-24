# Call Ops Lab

这个 lab 集中承载可靠调用、回归 Harness、成本与缓存实验，不按“一节一个 demo”继续拆目录。

- `reliability_compare.py`：观察 retry、fallback、schema failure 和 attempt report。
- `harness_compare.py`：观察一组 case 如何批量运行、记录、汇总。
- `cost_latency_cache.py`：观察 token、估算成本、延迟和 exact-match cache 边界。

三个入口默认都调用真实模型，不保存任何文件。需要离线排查或稳定复现 timeout、schema failure、fallback、cache hit / miss 时，在脚本顶部把对应 `USE_REAL_LLM` 改为 `False`。

真实模型路径会读取根目录 `.env`。如果 `OPENAI_API_KEY`、`OPENAI_BASE_URL` 或模型能力配置有问题，demo 会暴露真实错误；这正是本 lab 要学习的工程边界之一。

## 运行

```bash
uv run python source/demos/02_call_ops_lab/reliability_compare.py
uv run python source/demos/02_call_ops_lab/harness_compare.py
uv run python source/demos/02_call_ops_lab/cost_latency_cache.py
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
| `USE_REAL_LLM` | `True` | 是否调用真实模型；改为 `False` 时使用本地模拟复现失败路径 |
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

1. 先看 `[records]`：每条 case 的 `status`、`parse`、`degraded`、`attempts`、`tokens`、`cost` 和 `error`。
2. 再看 `[summary]`：这一批 case 的成功数、解析成功率、降级数和错误分布。
3. 最后看 `[detail]`：只作为内容预览，不把它当成完整评估结论。

典型记录：

```text
case_id  status   parse  degraded  attempts  tokens  latency_ms  cost       cache  error
S1       success  ok     false     1         1420    1280.5      $0.000312  -      -
S2       success  ok     true      2         1610    2410.2      $0.000358  -      -
S3       failed   -      true      2         -       2050.0      -          -      schema_parse
```

这说明 harness 不只看最终文本，而是把 parse、降级、attempt 和错误码都记录下来，给后续 eval / observability 使用。

`harness_compare.py` 顶部可改：

| 开关 | 默认值 | 含义 |
| --- | --- | --- |
| `USE_REAL_LLM` | `True` | 是否用真实 `LLMClient` 跑同一批 case；改为 `False` 时使用本地模拟 |
| `PRINT_RECORD_DETAIL` | `True` | 是否打印每条 case 的内容预览或错误信息 |
| `PRIMARY_CONFIG_REF` | `"chat.dev_chat"` | 主模型配置 |
| `FALLBACK_CONFIG_REF` | `"chat.fallback_chat"` | fallback 模型配置 |

真实模型路径的目的不是稳定触发失败，而是观察同一批业务 case 在当前模型、Prompt 和结构化输出约束下的真实调用事实：parse 是否通过、是否降级、耗时、token 和错误分布如何。模拟路径只用于稳定复现 success / timeout / fallback / schema_parse。

## cost / latency / cache 输出怎么看

`cost_latency_cache.py` 输出按固定顺序分段：

```text
[cost_latency]
→ [records:cold]
→ [summary:cold]
→ [cache_rounds]
→ [records:repeat]
→ [budget_shape]
→ [lesson]
```

读输出时按四步：

1. 先看 `[records:cold]`：每条 case 的 `tokens`、`latency_ms`、`cost` 和 `cache` 是否被记录。
2. 再看 `[summary:cold]`：这一批 case 的 `total_tokens`、`estimated_total_cost` 和平均延迟。
3. 再看 `[cache_rounds]`：第一次 cold 应该 miss；同输入 repeat 应该 hit；`changed_context` 应该 miss。
4. 最后看 `[budget_shape]`：理解 single call、context-enriched call、multi-step review 的成本形状差异。

典型缓存轮次：

```text
cold: hit_rate=0%, hits=0, misses=3, saved_tokens=0
repeat_same_input: hit_rate=100%, hits=3, misses=0, saved_tokens=4340
changed_context: hit_rate=0%, hits=0, misses=3, saved_tokens=0
```

这说明缓存 key 不是只看用户输入。只要 evidence / context 指纹变化，就必须重新生成，避免把旧证据下的评审结论复用到新材料。

`cost_latency_cache.py` 顶部可改：

| 开关 | 默认值 | 含义 |
| --- | --- | --- |
| `USE_REAL_LLM` | `True` | 是否调用真实模型；改为 `False` 时使用本地模拟观察缓存机制 |
| `PRIMARY_CONFIG_REF` | `"chat.dev_chat"` | 主模型配置 |
| `FALLBACK_CONFIG_REF` | `"chat.fallback_chat"` | fallback 模型配置 |
| `ENABLE_CACHE` | `True` | 是否启用本地进程内 exact-match cache |
| `CONTEXT_FINGERPRINT` | `"ctx-review-rules-v1"` | 代表当前证据上下文版本的学习用指纹 |

`cost` 是学习用估算，不是供应商账单。真实项目必须把当前价格作为配置输入，并按供应商实际计费口径更新。
