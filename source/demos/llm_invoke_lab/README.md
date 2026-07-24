# llm_invoke_lab

> 课表位置：[标准学习路径](../../../course/learning-path.md) V0 步骤 3–5（可学习）。  
> 本 lab 观察「怎样调用模型 → 怎样定任务 → 怎样收结果」。不要在本目录寻找 Context / Harness / Streaming 入口。

```text
SDK 直调对照     first_chat.py
→ Provider       config_ref → LLMClient.chat → LLMResponse
→ Prompt         prompt_id@version → render_prompt → LLMClient.chat
→ Structured     structured_mode → response_format → parse_risk_list
```

课程正文负责讲原理；本 README 负责跑序、命令和输出解读。

## 本 lab 调用面

允许：`LLMClient.chat` / `chat_structured`、`prompts`、`structured`、`schemas`、`errors`、`observability`、直调 OpenAI SDK（仅 `first_chat.py`）。

不调用：`context`、`harness`、`reliability`、`streaming`、`conversation`、`cache`、`costing`。

证据在 Prompt / Structured 脚本中来自静态 `evidence_s2.json`，**不是** Context Builder 或 Retriever。

## 跑序（必须按此顺序）

| 顺序 | 脚本 | 对应步骤 | 观察点 |
| --- | --- | --- | --- |
| 1 | `first_chat.py` | 步骤 3 对照 | SDK 直调：`usage` / `latency_ms` |
| 2 | `provider_switching.py` | 步骤 3 | `config_ref` → `LLMResponse` |
| 3 | `prompt_compare.py` | 步骤 4 | Prompt 三版对比 |
| 4 | `structured_risk.py` | 步骤 5 | `prompt_only` / `json_mode` / `json_schema` |

## 前置

```bash
# 仓库根目录
uv sync
cp .env.example .env   # 填写 OPENAI_API_KEY
```

OpenAI-compatible 平台可设置 `OPENAI_BASE_URL`、`OPENAI_MODEL`、`OPENAI_STRUCTURED_MODEL`。模型配置真源见 [`llm_core/config/models.yaml`](../../packages/llm_core/config/models.yaml)。

## 运行命令

```bash
cd source/demos/llm_invoke_lab

uv run python first_chat.py
uv run python first_chat.py --temperature 0.7

uv run python provider_switching.py
uv run python provider_switching.py --verbose
uv run python provider_switching.py --configs chat.dev_chat,chat.structured_chat

uv run python prompt_compare.py

uv run python structured_risk.py
```

## 读脚本要点

### 1. `first_chat.py`

SDK 直调基线。观察缺少统一 `config_ref` / `LLMResponse` 时，业务代码如何绑死模型与供应商对象。

### 2. `provider_switching.py`

1. `find_and_load_env()` → 根目录 `.env`
2. `load_sample("S2")` → `samples.json`
3. `LLMClient.from_default_config()` → `models.yaml`
4. `client.chat(messages, config_ref)` → `LLMResponse`

观察：`config_ref` 是否命中预期模型；`usage` / `latency_ms` 是否可读。

### 3. `prompt_compare.py`

顶部固定样例、版本列表、温度；用同一模型配置比较 `review.risk_review` v1–v3。静态 evidence 只作 Prompt 变量，不实现检索。

### 4. `structured_risk.py`

固定 Prompt `@4.0.0`、PRD、evidence，**只换** `structured_mode`。观察 `parse.ok` / `error_stage`，不引入 Context Builder。

## 实验配置

### `provider_switching.py`

| 参数 | 作用 |
| --- | --- |
| `--configs` | 对比的 `config_ref` |
| `--temperature` | 覆盖温度 |
| `--verbose` | 打印完整 messages / params |

### `prompt_compare.py`

| 常量 | 默认 | 作用 |
| --- | --- | --- |
| `SAMPLE_ID` | `"S2"` | PRD 样例 |
| `PROMPT_VERSIONS` | `("1.0.0", "2.0.0", "3.0.0")` | 对比版本 |
| `EVIDENCE_FILE` | `evidence_s2.json` | 静态 evidence |
| `TEMPERATURE` | `0` | 采样温度 |
| `VERBOSE` | `False` | 完整日志 |

### `structured_risk.py`

| 常量 | 默认 | 作用 |
| --- | --- | --- |
| `PROMPT_VERSION` | `"4.0.0"` | 共用 Prompt |
| `MODES` | 三种全跑 | 只换 structured mode |
| `CONFIG_REF` | `chat.dev_chat` | 模型配置 |
| `EVIDENCE_FILE` | `evidence_s2.json` | 静态 evidence |

## 输出怎么看

`provider_switching` / `prompt_compare` / `structured_risk` 经 `DemoLog` 输出 `[tag]` 块。

| tag / 字段 | 含义 |
| --- | --- |
| `[experiment]` | 样例、配置、版本或 mode |
| `model` / `usage` / `latency_ms` | 调用事实 |
| `parse.ok` / `error_stage` | 结构化校验分层 |
| `API_ERROR` | 供应商调用层失败 |

## 常见问题

| 现象 | 优先检查 |
| --- | --- |
| Key 未配置 | 根目录 `.env` 的 `OPENAI_API_KEY` |
| `config_ref` 找不到 | `models.yaml` 的 section.name |
| Prompt 版本找不到 | YAML 内 `prompt_id` / `version`，不是文件名 |
| 想比较材料预算与裁剪 | 完成 RAG 前置后进入 [`llm_context_lab`](../llm_context_lab/) |
| 想看 retry / fallback | 步骤 6：[`llm_reliability_lab`](../llm_reliability_lab/) |

## 相关

- Package：[source/packages/llm_core/](../../packages/llm_core/)
- [Model API 与 Provider](../../../course/mechanisms/model-api-and-provider.md)
- [Prompt Engineering](../../../course/mechanisms/prompt-engineering.md)
- [Structured Output](../../../course/mechanisms/structured-output.md)
