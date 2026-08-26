# Structured Output 与应用校验实验

配套机制：[Structured Output 与应用侧校验](../mechanisms/structured-output.md)。本实验固定 Prompt、需求、Evidence、模型配置和 temperature，只切换模型侧结构化模式，观察格式约束、解析、Schema 和业务对象之间的差异。

## 1. 前置与固定配置

先完成真实模型和 Prompt 实验。`source/demos/llm_invoke_lab/structured_risk.py` 顶部定义本轮身份：

| 配置 | 当前默认 | 作用 |
| --- | --- | --- |
| `SAMPLE_ID` | `S2` | 固定需求 |
| `PROMPT_ID@VERSION` | `review.risk_review@4.0.0` | 固定任务协议 |
| `CONFIG_REF` | `chat.dev_chat` | 固定模型配置 |
| `MODES` | `prompt_only`、`json_mode`、`json_schema` | 唯一主要变量 |
| `TEMPERATURE` | `0` | 降低随机性 |
| `EVIDENCE_FILE` | `evidence_s2.json` | 固定 Evidence |
| `VERBOSE` | `False` | 是否展开 messages 与请求参数 |

确认目标 Provider 对 `json_object` 或 `json_schema` 的真实支持范围。能力不支持必须作为真实错误出现，不能自动改用 Prompt-only 后宣称成功。

## 2. 运行前预测

分别预测三种模式在哪一层提供约束：

| 模式 | 模型侧能力 | 仍需应用检查 |
| --- | --- | --- |
| `prompt_only` | 只有文字要求 | JSON 解析、Schema、业务规则 |
| `json_mode` | 返回合法 JSON 对象 | 目标 Schema 和业务规则 |
| `json_schema` | 服务按目标 Schema 约束输出 | 本地 Schema 复核和业务规则 |

再预测以下失败应出现在哪一层：

- 返回普通文本或截断 JSON。
- JSON 合法但缺少必填字段。
- 字段类型正确但业务值非法。
- Provider 不支持所选结构化模式。

## 3. 运行三种模式

```bash
uv run python source/demos/llm_invoke_lab/structured_risk.py
```

需要查看渲染 messages、最终 `response_format` 和完整响应时，将脚本顶部 `VERBOSE` 临时改为 `True`。

输出重点：

| 字段 | 含义 |
| --- | --- |
| mode / structured_mode | 本轮唯一变化 |
| request params | 实际发给 Provider 的结构化参数 |
| raw content | 模型返回的原始文本或对象事实 |
| parse.ok | 最终是否形成目标业务对象 |
| error_stage | 失败发生在调用、JSON、Schema 还是后续校验 |
| issues / risks | 业务层实际消费的结构化结果 |

不要只看终端最后有没有风险列表。必须同时确认本轮 mode、Provider 能力和 `error_stage`。

## 4. 做一次稳定失败对照

真实模型不保证稳定生成某种坏格式。稳定观察解析和 Schema 失败时，优先运行确定性测试，而不是不断诱导模型犯错：

```bash
uv run pytest source/packages/llm_core/tests/test_parse.py \
  source/packages/llm_core/tests/test_client_structured.py -q
```

这些测试证明：

- 非 JSON、错误形状和字段约束会在预期层失败。
- 结构化失败不会进入成功业务对象。
- 请求模式与本地解析契约保持一致。

它们不能证明当前 Provider 支持某种模式，也不能证明模型输出质量。

## 5. 失败时按层排查

| 表现 | 可能层次 | 验证方式 |
| --- | --- | --- |
| 请求直接失败 | Provider 能力或参数 | 开启 verbose 查看 mode 与 response_format，保留 API 错误 |
| 有文本但 JSON 解析失败 | 语法层 | 查看 raw content 和 parse error，不用字符串截取伪造成功 |
| JSON 合法但 Schema 失败 | 数据契约层 | 查看缺失字段、类型和约束错误 |
| Schema 通过但业务不可用 | 业务校验层 | 检查严重度枚举、空说明、来源资格等业务规则 |
| 三种模式比较失真 | 同时改变了 Prompt、模型或 Evidence | 恢复固定配置只改变 `MODES` |

## 6. 读码顺序

1. `source/demos/llm_invoke_lab/structured_risk.py`：固定变量和三种模式怎样循环。
2. `source/packages/llm_core/structured/response.py`：`response_format` 和请求参数怎样构造。
3. `source/packages/llm_core/schemas/review.py`：目标业务 Schema。
4. `source/packages/llm_core/schemas/parse.py`：解析失败怎样分层。
5. `source/packages/llm_core/client/service.py`：调用与解析怎样形成统一结果。
6. `test_parse.py`、`test_client_structured.py`：确定性契约。

## 7. 修改任务

给风险项增加或收紧一个字段约束，例如限制某个文本字段不能为空。先写下：

- 哪些旧结果可能变成 Schema 失败。
- Provider 请求 Schema 是否需要变化。
- Prompt 是否需要解释业务含义。
- 哪些消费方和测试必须同步。

修改后运行上述测试和真实三模式实验。真实 Provider 不支持 `json_schema` 时，应保留“能力不支持”结果；可以另建 `json_object` 对照，但不能把两者记成同一次通过。
