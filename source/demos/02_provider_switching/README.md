# 02_provider_switching

`02_llm/01`–`03` demo 目录：模型配置、Prompt 版本、结构化 parse 对比。

| 脚本 | 课程节 | 运行 |
| --- | --- | --- |
| `provider_switching.py` | 01 Provider / `config_ref` | `python provider_switching.py` |
| `prompt_compare.py` | 02 Prompt 三版对比 | `python prompt_compare.py` |
| `structured_risk.py` | 03 Structured Outputs | `python structured_risk.py` |

00 的 [`02_first_chat`](../02_first_chat/) 仍保留直调 OpenAI SDK，用于对照「抽象前后」的差异。

**日志输出**：三个脚本均经 `llm_core.observability.DemoLog`（`[tag]` 块），与 `LLMClient.chat(..., debug=True)` 同一套方法；实现见 [`_shared.py`](_shared.py) 与 [`observability.py`](../../packages/llm_core/observability.py)。

## 前置

```bash
# 仓库根目录
pip install -r requirements.txt
pip install -e .
cp .env.example .env   # 填写 OPENAI_API_KEY
```

## 01：Provider 对比

```bash
cd source/demos/02_provider_switching

python provider_switching.py
python provider_switching.py --verbose
python provider_switching.py --configs chat.dev_chat,chat.structured_chat
```

## 02：Prompt 三版对比

**改 [`prompt_compare.py`](prompt_compare.py) 顶部「实验配置」**（约第 25–32 行），然后：

```bash
python prompt_compare.py
```

### `prompt_compare.py` 实验配置

| 常量 | 作用 | 默认 | 说明 |
| --- | --- | --- | --- |
| `SAMPLE_ID` | PRD 样例 | `"S2"` | `S1`–`S5`，见 [`../02_first_chat/samples.json`](../02_first_chat/samples.json) |
| `PROMPT_ID` | Prompt 逻辑名 | `"review.risk_review"` | 等于 yaml 内 **`prompt_id` 字段**（非文件名） |
| `PROMPT_VERSIONS` | 对比版本元组 | `("1.0.0","2.0.0","3.0.0")` | 每一项等于 yaml 内 **`version` 字段**；可简写 `"1"` |

**与 `llm_core/prompts/review/` 对照**（字段对应，文件名仅便于阅读）：

| `PROMPT_VERSIONS` | yaml 文件 | yaml 内 `version` |
| --- | --- | --- |
| `"1.0.0"` | `risk_review_v1.yaml` | `"1.0.0"` |
| `"2.0.0"` | `risk_review_v2.yaml` | `"2.0.0"` |
| `"3.0.0"` | `risk_review_v3.yaml` | `"3.0.0"` |

| `VERBOSE` | 表后完整日志 | `False` | 改 `True` 看 `[call_detail]` 全文 |
| `TEMPERATURE` | 采样温度 | `0` | 对比 Prompt 时建议保持 0 |
| `EVIDENCE_FILE` | evidence JSON 路径 | `evidence_s2.json` | 缺文件则用「无检索证据」占位 |

完整说明：[02 正文「实验配置」](../../../course/02_llm/02_prompt_engineering_for_apps.md#prompt_comparepy-实验配置)

## 03：结构化风险列表

**改 [`structured_risk.py`](structured_risk.py) 顶部「实验配置」**，然后：

```bash
python structured_risk.py
```

### `structured_risk.py` 实验配置

| 常量 | 默认 | 说明 |
| --- | --- | --- |
| `SAMPLE_ID` | `"S2"` | 同 02 |
| `PROMPT_ID` / `PROMPT_VERSION` | `review.risk_review` / `4.0.0` | 三种 mode **共用** |
| `CONFIG_REF` | `chat.dev_chat` | 三种 mode **共用** |
| `MODES` | 三种全跑 | `prompt_only` / `json_mode` / `json_schema` |
| `VERBOSE` | `False` | `False`：摘要结果；`True`：完整 `messages` / `request_params` / `assistant_raw` / `usage` / `parse_result` |
| `TEMPERATURE` / `EVIDENCE_FILE` | 同 02 | — |

**对照原则**：固定 Prompt、`config_ref`、temperature，**只换** `structured_mode`。

完整说明：[03 正文](../../../course/02_llm/03_structured_outputs.md#本节实战)

## 应看到什么

**provider_switching**：`[experiment]` 头 + 每个 `config_ref` 一块，含 `[content]` 全文。  
**prompt_compare**：每个 `version` 一块（v1/v2/v3）。  
**structured_risk**：每个 `mode` 一块；默认输出精简摘要与校验后的风险字段（长值截断）。`VERBOSE=True` 时输出完整 `messages`、每个 mode 的 `request_params`、`assistant_raw`、`usage` 与 `parse_result`。

## 相关

- Package：[source/packages/llm_core/](../../packages/llm_core/)
- 01 文档：[course/02_llm/01_model_api_and_provider_abstraction.md](../../../course/02_llm/01_model_api_and_provider_abstraction.md)
- 02 文档：[course/02_llm/02_prompt_engineering_for_apps.md](../../../course/02_llm/02_prompt_engineering_for_apps.md)
- 03 文档：[course/02_llm/03_structured_outputs.md](../../../course/02_llm/03_structured_outputs.md)
