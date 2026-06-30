# 01. Model API 与 Provider 抽象

> 在 00 跑通「一次最小 chat」之后，学会用 **统一客户端 + 配置文件** 接模型、切换供应商、读懂请求/响应，并为后续 RAG / Agent 复用同一套调用方式。

---

## 真实问题

专题 00 建立了问题空间：需求评审助手需要稳定的 LLM 层。本篇回答：**具体怎么接模型，业务代码才不写死** `model="gpt-4o"`，以及一次 Chat 调用在工程上到底经过哪些环节。

### 学习者真实问题

- **调 API 到底在调什么？** 是你的 Python 程序向云端发一次 HTTP 请求，云端模型根据 `messages` 生成文本；不是在本机跑模型文件。
- **Token 是什么？** 文本切成词元后的计数单位；`usage.prompt_tokens` / `completion_tokens` 决定成本，也反映上下文有多长。
- **OpenAI 兼容是什么意思？** 很多平台（含 DeepSeek）提供与 OpenAI Chat API **相同 JSON 格式**的接口；换 `base_url` + Key 即可，不必重写业务逻辑。
- **Embedding 和 Chat 不都是「模型」吗？** API 路径、输入输出完全不同；Chat 生成文本，Embedding 生成向量；配置必须分开（RAG 课再用 embedding）。

### 产品真实问题

继续小周团队的售后 PRD 场景。00 用 `first_chat.py` 直连 OpenAI SDK 已经能打出风险预览，团队很高兴。两周后要做三件事：

1. **开发用便宜模型、演示用强模型**——若 `model="gpt-4o"` 写死在业务里，每个脚本都要改。
2. **接入 DeepSeek 降本**——若 Key、`base_url` 散落在五个文件里，换一次供应商要全库搜索。
3. **前端要展示每次调用的 model、耗时、token**——若有的模块返回 SDK 原始对象、有的只返回字符串，日志和 eval 无法汇总。

某次上线前，后端在风险审查、摘要、追问三个模块里各写了一份 `OpenAI(api_key=...)`，模型名还不一致。运维把 `.env` 里的 `OPENAI_MODEL` 改成 `deepseek-chat` 后，只有两个模块生效，第三个仍打旧 endpoint，评审会上出现「同一 PRD、两份结论、模型还不同」的尴尬。

产品需要的是：**业务只声明「用哪类任务配置」**（如 `chat.dev_chat`），模型名、供应商、默认参数集中在仓库里的配置真源；每次调用返回统一结构，便于对比和记账。

### 工程真实问题

| 问题 | 典型表现 | 本节方向 |
| --- | --- | --- |
| 直接依赖 SDK 原始对象 | 日志字段不一致，eval 难汇总 | 统一 `LLMResponse` |
| 写死 model 字符串 | 换阶段 / 换供应商改多处 | `config_ref` + `models.yaml` |
| 假设「兼容 OpenAI = 所有参数都能用」 | structured / tool call 在部分平台失败 | `capabilities` 认知；03 起实测 |
| 错误全部 `except Exception` | 429 与 Key 错误混在一起 | `LLMError` + `LLMErrorCode` 分类 |

本篇在 `llm_core` 建立 **`LLMClient` + `models.yaml` + `LLMResponse`**，把调用与可观测收敛到一层。00 的 `02_first_chat` 保留作 SDK 直调对照，本篇是项目内的标准入口。

---

## 基础原理

### 一次 Chat 调用是什么

**输入**：`messages`（`system` / `user` / `assistant` 角色文本）+ 模型参数（`temperature`、`max_tokens` 等）+ 选哪条模型配置（`config_ref`）。  
**输出**：`LLMResponse`——至少包含 `content`、`usage`、`latency_ms`、`model`、`config_ref`；`raw_response` 仅供调试。

与 00 SDK 直调的区别：00 证明「能通」；01 证明「能换、能记、能统一」。

### 从直调到抽象：机制递进

下面这条链是本章认知主线。每一步解决上一步的遗留问题；**不能跳过**理解最终为什么要 `config_ref`。

**第 1 步 · SDK 直调（00 `first_chat`）**

```python
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
resp = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
text = resp.choices[0].message.content
```

能跑通，但 model、base_url、默认参数散落在脚本里；换供应商要改代码；返回值是 SDK 对象，上层难以统一记日志。

**第 2 步 · 环境变量（`.env`）**

密钥和 endpoint 不进仓库。`api_key`、`OPENAI_BASE_URL` 等由 `.env` 注入。  
**遗留**：model 名、默认 `temperature` 仍在 Python 字符串里；多环境（开发 / 演示）仍要改代码。

**第 3 步 · `models.yaml`（配置真源）**

把 `model`、`base_url`、`default_params`、`api_key_env` 收到 YAML；支持 `${OPENAI_MODEL:-gpt-4o-mini}` 占位符，由 `ConfigRegistry` 解析环境变量。  
**遗留**：业务若仍写 YAML 里的具体 model 字符串，换配置条目时调用方还要改。

**第 4 步 · `config_ref`（稳定别名）**

业务只写 `config_ref="chat.dev_chat"`，不碰具体 model 名。换模型改 YAML 或 `.env`，业务无感。  
**遗留**：仍需要一层客户端统一返回结构与错误类型。

**第 5 步 · `LLMClient` + `LLMResponse`**

`LLMClient.chat(messages, config_ref)` 完成：查配置 → 选 Provider → 发请求 → 包装 `LLMResponse`；可选 `debug=True` 打印完整日志。  
RAG、Agent、结构化输出（03）都通过同一入口扩展，而不是再 copy 一份 `OpenAI()`。

```text
first_chat 直调 → .env 密钥 → models.yaml → config_ref → LLMClient / LLMResponse
```

### 数据流

```text
业务 / demo
    │  messages + config_ref + 可选 temperature / max_tokens
    ▼
LLMClient.chat()
    │  ConfigRegistry.get_config(config_ref)
    ▼
OpenAICompatProvider.chat()
    │  OpenAI SDK → HTTP POST /v1/chat/completions
    ▼
LLMResponse（content, usage, latency_ms, model, config_ref, …）
```

### messages：system / user / assistant

| role | 谁写的 | 用途 |
| --- | --- | --- |
| `system` | 开发者 | 全局约束：「你是需求评审助手，只基于材料…」 |
| `user` | 用户或程序 | PRD 片段、问题 |
| `assistant` | 模型（历史轮） | 多轮对话中上一轮的模型回复 |

多轮时**历史存在应用的 `messages` 列表里**，API 没有 `session_id`。专题 04 会讲对话状态管理；当节只需知道：多轮 = 每次请求把历史 messages 一并传入。

```json
[
  {"role": "system", "content": "你是需求评审助手。"},
  {"role": "user", "content": "【PRD】… 列出风险。"},
  {"role": "assistant", "content": "1. 接口 v2 兼容性…"},
  {"role": "user", "content": "第 1 条依据是哪一段？"}
]
```

### 常用请求参数

| 参数 | 作用 | 观察方式 |
| --- | --- | --- |
| `temperature` | 随机性：越低越稳定 | `provider_switching.py --temperature 0` vs `0.7` |
| `max_tokens` | 限制**生成**的最大 token 数 | 输出变短时检查是否触顶 |
| `model` | 供应商侧模型 id | 由 `models.yaml` 配置，业务用 `config_ref` |

默认值在 [`config/models.yaml`](../../source/packages/llm_core/config/models.yaml) 的 `default_params`；调用时可覆盖。

### Provider、ModelConfig、config_ref

- **Provider**：适配某一类 API（01 实现 `openai_compat`）。
- **ModelConfig**：一条具体配置（model、base_url、默认参数、能力标签 `capabilities`）。
- **config_ref**：点分别名，如 `chat.dev_chat`；由 YAML 的 section + name 自动生成。

### 三类模型角色（配置分离）

| 角色 | 输入 | 输出 | 01 是否调用 |
| --- | --- | --- | --- |
| Chat | messages | 文本 | 是（`LLMClient.chat`） |
| Embedding | 文本 | 向量 | 否（YAML 预置，`03_rag` 用） |
| Rerank | query + 文档 | 分数 | 否（后续可选） |

对 `embedding.default_embed` 调 `chat` 会触发 `LLMErrorCode.CAPABILITY_MISMATCH`——这是刻意的角色守卫，避免 Chat 与 Embedding 混用。

---

## 最小实现

### 1. 从 YAML 加载配置

[`providers/registry.py`](../../source/packages/llm_core/providers/registry.py) 把 `chat.dev_chat` 等条目解析为 `ModelConfig`，并解析 `${ENV:-default}`：

```python
for section, entries in raw.items():
    for name, entry in entries.items():
        config_ref = f"{section}.{name}"
        configs[config_ref] = ModelConfig(
            config_ref=config_ref,
            role=entry.get("role", section),
            provider=entry["provider"],
            model=entry["model"],
            api_key_env=entry["api_key_env"],
            base_url=base_url,
            default_params=dict(entry.get("default_params") or {}),
            ...
        )
```

`models.yaml` 中一段示例：

```yaml
chat:
  dev_chat:
    role: chat
    provider: openai_compat
    model: ${OPENAI_MODEL:-gpt-4o-mini}
    base_url: ${OPENAI_BASE_URL}
    api_key_env: OPENAI_API_KEY
    default_params:
      temperature: 0.2
      max_tokens: 2048
```

### 2. `LLMClient.chat` 核心路径

[`client.py`](../../source/packages/llm_core/client.py)：

```python
config = self._registry.get_config(config_ref)
if config.role != "chat":
    raise LLMError(
        code=LLMErrorCode.CAPABILITY_MISMATCH,
        message=f"{config_ref} 的 role 是 {config.role}，不能用于 chat",
        config_ref=config_ref,
    )
provider = self._registry.get_provider(config.provider)
response = provider.chat(messages, config, **params)
return response
```

业务侧理想调用：

```python
client = LLMClient.from_default_config()
response = client.chat(messages, "chat.dev_chat", temperature=0, debug=True)
# response.content, response.usage, response.latency_ms, response.model
```

### 3. Provider 发请求与错误分类

[`openai_compat.py`](../../source/packages/llm_core/providers/openai_compat.py) 在发请求前检查 Key，并把 SDK 异常映射为 `LLMError`：

```python
api_key = os.environ.get(config.api_key_env, "").strip()
if not api_key:
    raise LLMError(
        code=LLMErrorCode.AUTH,
        message=f"环境变量 {config.api_key_env} 未配置",
        config_ref=config.config_ref,
    )
...
except RateLimitError as exc:
    raise LLMError(code=LLMErrorCode.RATE_LIMIT, ..., config_ref=config.config_ref) from exc
```

这样上层可以按 `exc.code` 分支，而不是解析异常字符串。

### 4. 统一响应 `LLMResponse`

[`config.py`](../../source/packages/llm_core/config.py)：

```python
@dataclass(frozen=True)
class LLMResponse:
    content: str
    raw_response: Any
    usage: Optional[TokenUsage]
    latency_ms: float
    provider: str
    model: str
    config_ref: str
```

无论 OpenAI 还是 DeepSeek，业务读同一套字段；`demo` 与后续 harness 都依赖这一形状。

---

## 主流框架实现

| 方式 | 与本项目 |
| --- | --- |
| **OpenAI SDK** | `OpenAICompatProvider` 内部使用；`base_url` 对接兼容平台 |
| **本项目 LLMClient** | 业务与 demo 通过 `config_ref` 调用；日志与切换集中 |
| **LangChain ChatModel** | 后续 RAG 拼链时可从同一 `models.yaml` 读 model，避免两套配置 |

原则：**配置真源在 `models.yaml` + `.env`**；框架是消费方，不在业务里再写一份 model 名。

---

## 失败分析与能力边界

### 排查路径（表现 → 原因 → 怎么验证）

**1. `auth`：一调用就失败，提示环境变量未配置**

- **表现**：`LLMError` code 为 `auth`，消息含 `OPENAI_API_KEY 未配置` 或 401。
- **原因**：`.env` 未复制、Key 名与 `api_key_env` 不一致、`base_url` 与 Key 不匹配。
- **验证**：检查仓库根 `.env`；`provider_switching.py --verbose` 看请求是否发出；换 Key 后是否立即恢复。

**2. `rate_limit`：偶发 429**

- **表现**：`rate_limit`，有时重试又好。
- **原因**：供应商 QPS / 配额；开发环境多人共用一个 Key。
- **验证**：换 `chat.fallback_chat` 对比；记录 `latency_ms` 与发生时段；完整重试策略在专题 06，**当节**会换 config_ref 即可。

**3. `capability_mismatch`：配置条目用错角色**

- **表现**：对 `embedding.default_embed` 调 `chat` 立刻报错。
- **原因**：Chat 与 Embedding API 路径不同，不能混用 `config_ref`。
- **验证**：`models.yaml` 看 `role` 字段；业务是否误把 embed 配置传给 `LLMClient.chat`。

**4. 兼容平台「能 chat 但不能 structured / tool」**

- **表现**：普通 `chat` 正常，03 的 `json_schema` 报 `API_ERROR`。
- **原因**：OpenAI 兼容 ≠ 全功能兼容；`capabilities.structured_output` 仅为文档性标签，不自动降级。
- **验证**：对比 `chat.dev_chat` 与 `chat.structured_chat`；结构化细节在专题 03。

### 常见误区

| 误区 | 纠正 |
| --- | --- |
| 「有 `base_url` 就等于 OpenAI」 | 参数支持与限额因平台而异 |
| 「`config_ref` 可以随意命名」 | 必须与 YAML section.name 一致，否则 `KeyError` |
| 「多轮对话 API 会记住」 | 历史由应用拼进 `messages` |
| 「`usage` 可省略」 | 成本与上下文问题靠 usage 发现；08 专讲成本 |

### 本节不做（defer）

| 能力 | 目标节 | 当节最小判断 |
| --- | --- | --- |
| 流式输出 | 04 | 知道非流式一次返回 `content` 即可 |
| 完整重试 / 熔断 | 06 | 会用 `LLMErrorCode` 分类，遇 429 知换 `fallback` |
| Structured Outputs | 03 | 知 `chat.structured_chat` 预留给结构化任务 |
| 实际调用 embedding | 03_rag | 知 YAML 里已有 `embedding.default_embed`，01 不调 |
| harness 落盘 | 07 | demo 对比 + 笔记记录 token/latency |
| 多轮会话持久化 | 04 | 知历史在 `messages`，不由 API 保存 |

---

## 本节实战

### 目标

业务通过 `config_ref` 调用模型；所有调用返回统一 `LLMResponse`；`--verbose` 时可看清 system/user、参数与完整回复；能在 S2 样例上对比至少两个 `config_ref`。

### 涉及文件

```text
source/packages/llm_core/
├── client.py
├── config.py
├── errors.py
├── observability.py
├── config/models.yaml
└── providers/
    ├── openai_compat.py
    └── registry.py

source/demos/02_provider_switching/
├── provider_switching.py
├── _shared.py
└── README.md
```

### 实现步骤（与最小实现对照）

1. `find_and_load_env()` 加载根目录 `.env`。
2. `load_sample("S2")` 取 PRD 文本，`build_messages` 组成 system + user。
3. `LLMClient.from_default_config()` → 对每个 `config_ref` 调用 `client.chat(..., debug=verbose)`。
4. 打印表格行：`config_ref`、`model`、`latency_ms`、`total_tokens`、`content` 预览；`--verbose` 走 `render_call_log` 打全量。

### 步骤 1：配置环境（OpenAI 默认）

```bash
cd <仓库根>
cp .env.example .env
# 编辑 .env，填写 OPENAI_API_KEY
pip install -r requirements.txt
pip install -e .
```

### 步骤 2：配置 DeepSeek（可选）

```bash
OPENAI_API_KEY=你的DeepSeek密钥
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-chat
OPENAI_STRUCTURED_MODEL=deepseek-chat
```

无需改 Python；`models.yaml` 通过占位符读 `.env`。

### 步骤 3：走读 models.yaml

| config_ref | 用途 |
| --- | --- |
| `chat.dev_chat` | 日常开发；`model` 读 `OPENAI_MODEL` |
| `chat.structured_chat` | 结构化任务（03 深化） |
| `chat.fallback_chat` | 兜底 |
| `embedding.default_embed` | 预置给 RAG，01 不调用 |

### 步骤 4：运行对比 demo

```bash
cd source/demos/02_provider_switching
python provider_switching.py
python provider_switching.py --verbose
python provider_switching.py --configs chat.dev_chat,chat.structured_chat
python provider_switching.py --temperature 0.7
```

使用与 00 相同的 [`samples.json`](../../source/demos/02_first_chat/samples.json)（默认 **S2**）。

### 预期结果

**默认模式**：终端 Markdown 表格，每行含 `config_ref`、`model`、`latency_ms`、`total_tokens`、`content` 预览。

`--verbose`：每次调用额外打印 config_ref、provider、model、请求参数、完整 messages、完整 assistant content、usage JSON。

### 对比实验

固定 `sample=S2`，只换 `config_ref` 或 `--temperature`，记录：`model`, `temperature`, `prompt_tokens`, `completion_tokens`, `latency_ms`, `notes`。系统化落盘在专题 07。

### 建议观察清单

- [ ] 两个 `config_ref` 的 `model` 字段是否如 YAML 预期
- [ ] `temperature=0` vs `0.7` 下 `content` 稳定性差异
- [ ] `usage` 是否随 Prompt 长度变化（体会 token 与成本）
- [ ] `--verbose` 能否看清完整 `messages` 传给云端的内容

---

## 完成标准

- **能解释**：一次 Chat 的输入（messages、config_ref、参数）与输出（`LLMResponse` 各字段）。
- **能说明**：`temperature` / `max_tokens` 对输出的影响。
- **能画出**：从直调 SDK 到 `config_ref` 的五步递进，各步遗留什么问题。
- **能配置**：OpenAI 或 DeepSeek（`.env` + `models.yaml`）。
- **能运行**：`provider_switching` 默认对比与 `--verbose`。
- **能说明**：为何业务写 `config_ref` 而不是写死 model 字符串。

### 运行与观察

```bash
cd source/demos/02_provider_switching
python provider_switching.py
python provider_switching.py --verbose
```

应看到至少 2 行对比；verbose 下可见 system/user 与完整 assistant 回复。详见 [demo README](../../source/demos/02_provider_switching/README.md)。

### 自检题

1. 多轮对话的历史存在哪里？通过 API 的哪个字段带给模型？
2. 为什么业务代码应写 `config_ref="chat.dev_chat"` 而不是 `model="gpt-4o"`？
3. 把 Chat 模型名填进 embedding 接口会导致什么问题？
4. `.env` 与 `models.yaml` 各解决什么，为什么不能只用其中一个？
5. 收到 `LLMErrorCode.RATE_LIMIT` 时，当节可以先做哪一步，完整重试策略在哪一节？
6. `LLMResponse` 相比 SDK 原始响应，多解决了哪两个工程问题？

---

## 本节沉淀

- 新增 `llm_core` 调用层（`LLMClient`、`models.yaml`、`ConfigRegistry`、`LLMResponse`、`LLMError`）与 `02_provider_switching` demo。
- 需求评审助手具备：**按任务切换模型配置、统一响应结构与可观测日志**；00 的 `02_first_chat` 保留作 SDK 直调对照。
- 下一节 [02_prompt_engineering_for_apps.md](02_prompt_engineering_for_apps.md) 在同一 `LLMClient` 上叠加 Prompt 模板。

---

## 相关专题

- 上一篇：[00_llm_problem_space.md](00_llm_problem_space.md)
- 下一篇：[02_prompt_engineering_for_apps.md](02_prompt_engineering_for_apps.md)
- 课程大纲：[outline.md](outline.md)
