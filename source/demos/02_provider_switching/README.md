# 02_provider_switching

`02_llm/01` + `02` demo 目录：模型配置对比与 Prompt 版本对比。

| 脚本 | 课程节 | 运行 |
| --- | --- | --- |
| `provider_switching.py` | 01 Provider / `config_ref` | `python provider_switching.py` |
| `prompt_compare.py` | 02 Prompt 三版对比 | `python prompt_compare.py` |

00 的 [`02_first_chat`](../02_first_chat/) 仍保留直调 OpenAI SDK，用于对照「抽象前后」的差异。

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
python provider_switching.py --configs chat.dev_chat,chat.fallback_chat
```

## 02：Prompt 三版对比

**改 [`prompt_compare.py`](prompt_compare.py) 顶部「实验配置」**（约第 25–38 行），然后：

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

三者 `prompt_id` 均为 `review.risk_review`，与 `PROMPT_ID` 相同。加载逻辑见 `prompts/registry.py`（按字段匹配，不按文件名）。

| `VERBOSE` | 表后完整日志 | `False` | 改 `True` 看 messages 全文 |
| `TEMPERATURE` | 采样温度 | `0` | 对比 Prompt 时建议保持 0 |
| `EVIDENCE_FILE` | evidence JSON 路径 | `evidence_s2.json` | 缺文件则用「无检索证据」占位 |

**不在此改的**：`model_config_ref` → 各版 yaml；Prompt 正文 → `llm_core/prompts/review/`；Key → 根目录 `.env`。

**可试**：`SAMPLE_ID="S3"`（无材料）；`EVIDENCE_FILE` 指向不存在路径；`PROMPT_VERSIONS=("2.0.0","3.0.0")` 只比两版。

完整说明：[02 正文「实验配置」](../../../course/02_llm/02_prompt_engineering_for_apps.md#prompt_comparepy-实验配置)

## 应看到什么

**provider_switching**：对比表按 `config_ref` 分行。  
**prompt_compare**：对比表按 `version`（v1/v2/v3）分行；v2 通常更贴材料，v3 尝试 JSON 结构。

## 相关

- Package：[source/packages/llm_core/](../../packages/llm_core/)
- 01 文档：[course/02_llm/01_model_api_and_provider_abstraction.md](../../../course/02_llm/01_model_api_and_provider_abstraction.md)
- 02 文档：[course/02_llm/02_prompt_engineering_for_apps.md](../../../course/02_llm/02_prompt_engineering_for_apps.md)
