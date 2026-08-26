# 可靠调用、重试与结构化错误实验

配套机制：[Reliability、错误分类与可见降级](../mechanisms/reliability-and-errors.md)。本实验先运行真实模型，观察可靠调用外壳怎样记录 attempt；再用稳定失败复现检查 timeout、fallback、鉴权和 Schema 失败的控制逻辑。

稳定失败只证明重试和错误状态机，不证明真实 Provider 一定以相同时间或顺序失败。

## 1. 实验配置

配置位于 `source/demos/llm_reliability_lab/reliability_compare.py` 顶部：

| 配置 | 默认 | 作用 |
| --- | --- | --- |
| `USE_REAL_LLM` | `True` | 真实调用主路径；`False` 进入稳定失败复现 |
| `DEFAULT_CASE` | `timeout_then_success` | 稳定失败类型 |
| `COMPARE_WITH_NO_RETRY` | `True` | 先跑无重试对照 |
| `PRINT_MESSAGES` | `False` | 是否打印完整 messages |
| `PRINT_ATTEMPT_DETAIL` | `True` | 是否展示每次失败详情 |
| `PRIMARY_CONFIG_REF` | `chat.dev_chat` | 主模型配置 |
| `FALLBACK_CONFIG_REF` | `chat.fallback_chat` | 显式 fallback 配置 |

真实路径需要根 `.env` 和有效模型配置。没有 Key、鉴权失败或 fallback 配置不存在时应真实失败。

## 2. 先运行真实调用

保持 `USE_REAL_LLM = True`：

```bash
uv run python source/demos/llm_reliability_lab/reliability_compare.py
```

运行前预测：一次正常请求通常只产生一个成功 attempt；可靠调用层不应为了展示重试而主动制造失败。

按顺序读取：

```text
[case]
→ [call_plan]
→ [messages]        仅打开 PRINT_MESSAGES 时
→ [attempts]
→ [final]
→ [lesson]
```

重点记录：

- 主配置和允许的 fallback。
- `max_attempts`。
- 每次 attempt 的 config、状态、错误和耗时。
- 最终是主模型成功、降级成功还是失败。
- 降级后实际模型和配置是否可见。

真实调用一次成功不能证明 timeout 重试分支正确，因此还需要确定性对照。

## 3. 稳定复现失败

将 `USE_REAL_LLM` 临时改为 `False`，每次只选择一个 `DEFAULT_CASE`：

| Case | 运行前预测 |
| --- | --- |
| `timeout_then_success` | 无重试失败；可靠调用第二次成功 |
| `primary_timeout_then_fallback` | 主配置达到尝试上限后切显式 fallback |
| `auth_error` | 鉴权错误立即失败，不重试、不 fallback |
| `schema_failure` | 调用返回内容但结构化解析失败，最终不能记为成功 |

重新运行同一命令。比较 `no_retry` 与 `reliable` 的 attempts 和 final，而不是只比较最后有没有文本。

实验结束后恢复 `USE_REAL_LLM = True`，避免后续学习者误把模拟路径当主路径。

## 4. 怎样判断策略正确

- 只有明确可恢复的错误进入有限重试。
- 鉴权、配置和能力不支持不会被反复请求。
- fallback 必须显式配置，并在最终报告中可见。
- Schema 失败属于调用结果失败，不能因为 HTTP 成功就进入业务成功。
- 达到尝试上限后返回结构化失败，不继续无限循环。
- 每次 attempt 保留 config、错误、耗时和顺序。

本实验不判断 fallback 模型的业务质量。质量下降需要固定数据集另行比较。

## 5. 失败时按层排查

| 表现 | 优先检查 | 验证方式 |
| --- | --- | --- |
| 真实模式没有 Key | 根 `.env` 与主配置 | 保留真实配置错误，不切换模拟后声称真实通过 |
| fallback 找不到 | `FALLBACK_CONFIG_REF` | 查看模型配置真源 |
| 鉴权错误被重试 | Provider 错误映射和 retryable 分类 | 运行 `auth_error` 稳定 case 与测试 |
| timeout 没有停止 | `max_attempts` 与 attempt 计数 | 比较 no_retry / reliable 输出 |
| 降级成功但身份不清 | final report | 检查最终 config_ref 和 attempts |
| Schema 失败显示成功 | 结构化解析进入可靠性报告的路径 | 运行 `schema_failure` 与解析测试 |

## 6. 读码顺序

1. `source/demos/llm_reliability_lab/reliability_compare.py`：真实与稳定失败怎样切换。
2. `source/packages/llm_core/reliability/service.py`：尝试、重试、fallback 和最终结果怎样推进。
3. `source/packages/llm_core/reliability/policies.py` 与 `report.py`：哪些错误可重试、哪些可降级，以及 attempt 怎样记录。
4. `source/packages/llm_core/errors/types.py` 与 Provider 错误映射：供应商异常怎样进入统一错误。
5. `source/packages/llm_core/tests/test_reliability.py`：尝试次数、错误和降级不变量。

## 7. 修改与验证

选择一个策略参数，例如把某个稳定 timeout case 的最大尝试次数从 2 改为 3。先预测 attempts 数量、最终状态和总延迟怎样变化，以及鉴权错误为什么仍不应重试。

运行：

```bash
uv run pytest source/packages/llm_core/tests/test_reliability.py \
  source/packages/llm_core/tests/test_parse.py -q
```

再恢复真实模式运行一次，确认测试使用的稳定失败没有替代真实调用入口。
