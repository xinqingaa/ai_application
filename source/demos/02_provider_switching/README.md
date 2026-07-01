# 02_provider_switching

`02_llm/01`–`03` 的观察 demo 目录。这里不是三套独立小项目，而是在同一个 `llm_core` 底座上逐步观察：

```text
01 Provider      config_ref → LLMClient.chat → LLMResponse
02 Prompt        prompt_id@version → render_prompt → LLMClient.chat
03 Structured    structured_mode → response_format → parse_risk_list
05 Context       requirement + sources + token_budget → prompt variables
```

课程正文负责讲原理；本 README 负责告诉你怎么读脚本、怎么运行、输出怎么看。

| 脚本 | 课程节 | 运行 |
| --- | --- | --- |
| `provider_switching.py` | 01 Provider / `config_ref` | `python provider_switching.py` |
| `prompt_compare.py` | 02 Prompt 三版对比 | `python prompt_compare.py` |
| `structured_risk.py` | 03 Structured Outputs / 05 Context Engineering | `python structured_risk.py` |

00 的 [`02_first_chat`](../02_first_chat/) 保留直调 OpenAI SDK，用于对照「抽象前后」的差异。

## 前置

```bash
# 仓库根目录
pip install -r requirements.txt
pip install -e .
cp .env.example .env   # 填写 OPENAI_API_KEY
```

如使用 OpenAI-compatible 平台，可在根目录 `.env` 中设置 `OPENAI_BASE_URL`、`OPENAI_MODEL`、`OPENAI_STRUCTURED_MODEL`。模型配置真源见 [`llm_core/config/models.yaml`](../../packages/llm_core/config/models.yaml)。

## 读脚本顺序

### 01：`provider_switching.py`

先读顶部参数，再读主流程：

1. `find_and_load_env()`：加载根目录 `.env`。
2. `load_sample("S2")`：读取 00 的 PRD 样例。
3. `build_messages(...)`：拼出 system / user。
4. `LLMClient.from_default_config()`：读取 `models.yaml`。
5. `client.chat(messages, config_ref, ...)`：得到 `LLMResponse`。

观察重点：

- `config_ref` 是否命中预期模型。
- `LLMResponse.model` / `usage` / `latency_ms` 是否可读。
- `--verbose` 下完整 messages 是否符合预期。

### 02：`prompt_compare.py`

这个脚本用于观察 Prompt 版本化，不用于证明某个 Prompt 是标准答案。

读代码时关注：

1. 顶部实验变量：固定样例、版本列表、温度。
2. `get_prompt(PROMPT_ID, version)`：按 `prompt_id@version` 找 YAML。
3. `render_prompt(tpl, variables)`：把 PRD 和 evidence 注入 messages。
4. `client.chat(...)`：用同一模型配置调用三版 Prompt。

观察重点：

- v1 是否更容易空泛或编造。
- v2 加 Evidence / Constraints 后是否更贴材料。
- v3 是否更接近 JSON 意图，但仍可能无法稳定解析。
- `prompt_tokens` 是否随 Prompt 变长而增加。

### 03：`structured_risk.py`

这个脚本用于观察结构化输出的约束层级，也在 05 复用为上下文构造观察入口。它不用于证明某个 mode 永远最好。

读代码时关注：

1. `PROMPT_VERSION = "4.0.0"`：三种 mode 共用同一 Prompt。
2. `ContextSource` + `build_review_context(...)`：静态 evidence 如何变成带 source id 的 `evidence_block`。
3. `MODES`：`prompt_only` / `json_mode` / `json_schema`。
4. `client.chat_structured(...)`：调用后立刻 parse。
5. `result.parse.ok` / `error_stage`：判断输出是否可被业务消费。

观察重点：

- `[context]` 中的 `token_budget`、`estimated_tokens`、`included_sources`、`dropped_sources`。
- `prompt_only` 是否出现围栏、裸数组或字段漂移。
- `json_mode` 是否减少 JSON 格式层失败。
- `json_schema` 是成功、parse 失败，还是供应商 `API_ERROR`。
- 校验通过时，`category` / `level` 是否为英文枚举值。

## 运行命令

```bash
cd source/demos/02_provider_switching

python provider_switching.py
python provider_switching.py --verbose
python provider_switching.py --configs chat.dev_chat,chat.structured_chat

python prompt_compare.py

python structured_risk.py
```

## 实验配置

### `provider_switching.py`

常用参数：

| 参数 | 作用 |
| --- | --- |
| `--configs` | 指定要对比的 `config_ref`，如 `chat.dev_chat,chat.structured_chat` |
| `--temperature` | 覆盖模型温度 |
| `--verbose` | 打印完整 messages、请求参数、assistant、usage |

### `prompt_compare.py`

修改文件顶部实验变量后重新运行：

| 常量 | 作用 | 默认 |
| --- | --- | --- |
| `SAMPLE_ID` | PRD 样例 | `"S2"` |
| `PROMPT_ID` | Prompt 逻辑名 | `"review.risk_review"` |
| `PROMPT_VERSIONS` | 对比版本 | `("1.0.0", "2.0.0", "3.0.0")` |
| `VERBOSE` | 是否输出完整日志 | `False` |
| `TEMPERATURE` | 采样温度 | `0` |
| `EVIDENCE_FILE` | 静态 evidence 文件 | `evidence_s2.json` |
| `CONTEXT_TOKEN_BUDGET` | 05 上下文材料预算 | `900` |

`PROMPT_ID` 和 `PROMPT_VERSIONS` 对应 YAML 内部字段，不依赖文件名。当前三版位于 [`llm_core/prompts/review/`](../../packages/llm_core/prompts/review/)。

### `structured_risk.py`

修改文件顶部实验变量后重新运行：

| 常量 | 作用 | 默认 |
| --- | --- | --- |
| `SAMPLE_ID` | PRD 样例 | `"S2"` |
| `PROMPT_ID` / `PROMPT_VERSION` | Prompt 逻辑名与版本 | `review.risk_review` / `4.0.0` |
| `CONFIG_REF` | 模型配置 | `chat.dev_chat` |
| `MODES` | 对比模式 | 三种全跑 |
| `VERBOSE` | 是否输出完整日志 | `False` |
| `TEMPERATURE` | 采样温度 | `0` |
| `EVIDENCE_FILE` | 静态 evidence 文件 | `evidence_s2.json` |

对照原则：固定 Prompt、`config_ref`、temperature，**只换** `structured_mode`。

## 输出怎么看

三个脚本均经 `llm_core.observability.DemoLog` 输出 `[tag]` 块。

| tag / 字段 | 含义 |
| --- | --- |
| `[experiment]` | 当前样例、配置、版本或 mode |
| `[context]` | 05 context builder 诊断：预算、估算 token、进入/丢弃的 source |
| `[content]` | 模型正文输出 |
| `[call_detail]` | verbose 下的 messages、params、assistant、usage |
| `model` | 实际命中的模型 |
| `usage` / `total_tokens` | token 消耗，用于观察成本 |
| `latency_ms` | 调用耗时 |
| `parse.ok` | 结构化结果是否通过应用校验 |
| `error_stage` | `empty` / `json` / `schema`，用于判层 |
| `API_ERROR` | 供应商调用层失败，通常不是本地 JSON parse 问题 |

## 常见问题

| 现象 | 优先检查 |
| --- | --- |
| `auth` / Key 未配置 | 根目录 `.env` 是否存在，`OPENAI_API_KEY` 是否匹配平台 |
| `config_ref` 找不到 | `llm_core/config/models.yaml` 是否有对应 section.name |
| Prompt 版本找不到 | YAML 内 `prompt_id` / `version`，不是文件名 |
| v2/v3 没有 evidence | `EVIDENCE_FILE` 是否存在，`evidence_block` 字段是否存在 |
| `[context] included_sources` 为空 | evidence 文件是否存在；`CONTEXT_TOKEN_BUDGET` 是否太小 |
| citation 没有对应 source id | 先看 `[context] evidence_block` 是否含 source id；真实 citation 校验在 03_rag |
| `json_schema` API 失败 | 当前供应商是否支持该 `response_format` |
| `error_stage=json` | assistant 是否为合法 JSON、是否被截断或带多余说明 |
| `error_stage=schema` | 字段名、枚举值、根形态是否符合 `ReviewRiskList` |

## 相关

- Package：[source/packages/llm_core/](../../packages/llm_core/)
- 01 文档：[course/02_llm/01_model_api_and_provider_abstraction.md](../../../course/02_llm/01_model_api_and_provider_abstraction.md)
- 02 文档：[course/02_llm/02_prompt_engineering_for_apps.md](../../../course/02_llm/02_prompt_engineering_for_apps.md)
- 03 文档：[course/02_llm/03_structured_outputs.md](../../../course/02_llm/03_structured_outputs.md)
