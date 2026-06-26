# 01. Model API 与 Provider 抽象

> 在 00 跑通「一次最小 chat」之后，学会用 **统一客户端 + 配置文件** 接模型、切换供应商、读懂请求/响应，并为后续 RAG / Agent 复用同一套调用方式。

---

## 真实问题

专题 00 建立了问题空间：需求评审助手需要稳定的 LLM 层。本篇回答：**具体怎么接模型，业务代码才不写死** `model="gpt-4o"`。

### 学习者真实问题

- **调 API 到底在调什么？** 是你的 Python 程序向云端发一次 HTTP 请求，云端模型根据 `messages` 生成文本；不是在本机跑模型文件。
- ``
- **Token 是什么？** 文本切成词元后的计数单位；`usage.prompt_tokens` / `completion_tokens` 决定成本，也反映上下文有多长。
- **OpenAI 兼容是什么意思？** 很多平台（含 DeepSeek）提供与 OpenAI Chat API **相同 JSON 格式**的接口；换 `base_url` + Key 即可，不必重写业务逻辑。
- **Embedding 和 Chat 不都是「模型」吗？** API 路径、输入输出完全不同；Chat 生成文本，Embedding 生成向量；配置必须分开（RAG 课再用 embedding）。



### 产品真实问题

同一助手在不同阶段需要不同「引擎」：


| 阶段      | 典型任务            | 对模型的要求  |
| ------- | --------------- | ------- |
| 日常开发    | 调试 Prompt、试风险描述 | 便宜、快    |
| 正式评审    | 结构化报告（专题 03）    | 输出更稳定   |
| 限流 / 兜底 | 主模型 429         | 备用低成本模型 |


若业务里 everywhere 写死 `model="gpt-4o"`，换平台、换阶段都要改很多文件。产品应通过 `config_ref`（如 `chat.dev_chat`）选配置，而不是散落 model 字符串。

### 工程真实问题


| 问题                      | 后果                         |
| ----------------------- | -------------------------- |
| 直接依赖 SDK 原始对象           | 日志、eval 无法统一汇总             |
| 假设「兼容 OpenAI = 所有参数都能用」 | structured / tool call 常失败 |
| 错误全部 `except Exception` | 无法区分重试还是换模型                |


本篇在 `llm_core` 建立 `LLMClient` **+** `models.yaml` **+** `LLMResponse`，把调用与可观测收敛到一层。

---



## 基础原理



### 一次 Chat 调用的数据流

```text
业务 / demo
    │  messages + config_ref
    ▼
LLMClient.chat()
    │  加载 ModelConfig（models.yaml）
    ▼
OpenAICompatProvider
    │  OpenAI SDK → HTTP POST /v1/chat/completions
    ▼
LLMResponse（content, usage, latency_ms, model, …）
```

实现见 `[source/packages/llm_core/client.py](../../source/packages/llm_core/client.py)`。

### messages：system / user / assistant


| role        | 谁写的     | 用途                     |
| ----------- | ------- | ---------------------- |
| `system`    | 开发者     | 全局约束：「你是需求评审助手，只基于材料…」 |
| `user`      | 用户或程序   | PRD 片段、问题              |
| `assistant` | 模型（历史轮） | 多轮对话中上一轮的模型回复          |


多轮示例：

```json
[
  {"role": "system", "content": "你是需求评审助手。"},
  {"role": "user", "content": "【PRD】… 列出风险。"},
  {"role": "assistant", "content": "1. 接口 v2 兼容性…"},
  {"role": "user", "content": "第 1 条依据是哪一段？"}
]
```



### 常用请求参数（新手必读）


| 参数            | 作用                    | 观察方式                                             |
| ------------- | --------------------- | ------------------------------------------------ |
| `temperature` | 随机性：越低越稳定，越高越发散       | `provider_switching.py --temperature 0` vs `0.7` |
| `max_tokens`  | 限制模型**生成**的最大 token 数 | 输出变短时检查是否触顶                                      |
| `model`       | 供应商侧的模型 id            | 由 `models.yaml` 配置，业务用 `config_ref`              |


默认值写在 `[config/models.yaml](../../source/packages/llm_core/config/models.yaml)` 的 `default_params`；调用时可覆盖。

### 三类模型角色（配置分离）


| 角色        | 输入         | 输出  | 01 是否调用                |
| --------- | ---------- | --- | ---------------------- |
| Chat      | messages   | 文本  | 是（`LLMClient.chat`）    |
| Embedding | 文本         | 向量  | 否（YAML 预置， `03_rag` 用） |
| Rerank    | query + 文档 | 分数  | 否（后续可选）                |




### Provider、ModelConfig、config_ref

- **Provider**：适配某一类 API（01 实现 `openai_compat`）。
- **ModelConfig**：一条具体配置（model、base_url、默认参数、能力标签）。
- **config_ref**：别名，如 `chat.dev_chat`；业务只写别名，不改 YAML 也能切换模型。



### 最小实现（代码走读）

`LLMClient.chat` 核心逻辑（节选）：

```python
config = self._registry.get_config(config_ref)
provider = self._registry.get_provider(config.provider)
response = provider.chat(messages, config, **params)
if debug:
    print_call_log(messages, merged_params, response)
return response
```

统一返回 `[LLMResponse](../../source/packages/llm_core/config.py)`：`content`、`usage`、`latency_ms`、`model`、`config_ref`；`raw_response` 仅供调试。

---



## 主流框架实现


| 方式                      | 与本项目关系                                           |
| ----------------------- | ------------------------------------------------ |
| **OpenAI SDK**          | `OpenAICompatProvider` 内部使用；支持 `base_url` 对接兼容平台 |
| **本项目 LLMClient**       | 业务与 demo 应通过 `config_ref` 调用，便于日志与切换             |
| **LangChain ChatModel** | 后续 RAG 拼链时从同一 `models.yaml` 读 model，避免两套配置       |


---



## 失败分析与能力边界



### LLMErrorCode（分类，重试策略在专题 06）


| 代码                    | 典型原因                  | 第一反应                         |
| --------------------- | --------------------- | ---------------------------- |
| `auth`                | Key 错、base_url 错      | 检查 `.env`，fail fast          |
| `rate_limit`          | 429                   | 换 `chat.fallback_chat` 或稍后重试 |
| `timeout`             | 网络 / 模型慢              | 记录 latency，考虑 fallback       |
| `capability_mismatch` | 如对 embedding 配置调 chat | 换 config_ref                 |
| `provider_error`      | 5xx 等                 | 记录 raw，有限重试                  |
| `unknown`             | 未分类                   | 记录现场                         |




### 常见误区

- **OpenAI 兼容 ≠ 所有 OpenAI 参数都能用**（structured、tool call 常不完整）。
- **Chat 模型名不能用于 embedding 接口**（会报错或产生无意义向量）。
- **API 没有 session_id**；历史在 `messages` 里，由应用维护。



### 本节不做

- 流式输出（专题 04）
- 完整重试 / 熔断（专题 06）
- Structured Outputs API（专题 03）
- 实际调用 embedding（`03_rag`）
- schema 成功率统计与 harness 落盘（专题 03 / 07）

---



## 本节实战



### 目标

业务通过 `config_ref` 调用模型；所有调用返回统一 `LLMResponse`；`debug=True` 时可看清 system/user、参数与完整回复。

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
└── README.md
```



### 步骤 1：配置环境（OpenAI 默认）

```bash
cd <仓库根>
cp .env.example .env
# 编辑 .env，填写 OPENAI_API_KEY
pip install -r requirements.txt
pip install -e .
```



### 步骤 2：配置 DeepSeek（可选）

在 `.env` 中设置（无需改 Python）：

```bash
OPENAI_API_KEY=你的DeepSeek密钥
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-chat
OPENAI_STRUCTURED_MODEL=deepseek-chat
```



### 步骤 3：走读 models.yaml

打开 `[config/models.yaml](../../source/packages/llm_core/config/models.yaml)`：


| config_ref                | 用途                                |
| ------------------------- | --------------------------------- |
| `chat.dev_chat`           | 日常开发；`model` 读 `OPENAI_MODEL`     |
| `chat.structured_chat`    | 结构化任务；读 `OPENAI_STRUCTURED_MODEL` |
| `chat.fallback_chat`      | 兜底                                |
| `embedding.default_embed` | 预置给 RAG，01 不调用                    |


密钥只通过 `api_key_env: OPENAI_API_KEY` 引用环境变量。

### 步骤 4：运行对比 demo

```bash
cd source/demos/02_provider_switching

python provider_switching.py
python provider_switching.py --verbose
python provider_switching.py --configs chat.dev_chat,chat.structured_chat
python provider_switching.py --temperature 0.7
```

使用与 00 相同的样例 `[samples.json](../02_first_chat/samples.json)`（默认 **S2** 售后 PRD 风险）。

### 预期结果

**默认模式**：终端打印 Markdown 表格行，每行包含 `config_ref`、`model`、`latency_ms`、`total_tokens`、`content` 预览。

`--verbose`：每次调用额外打印：

- `config_ref`、provider、model、latency_ms  
- 请求参数（含 temperature、max_tokens）  
- 完整 **messages**（system / user 全文）  
- 完整 **assistant content**  
- **usage** JSON



### 对比实验

固定 `sample=S2`，只换 `config_ref` 或 `--temperature`，在笔记中记录：`model`, `temperature`, `prompt_tokens`, `completion_tokens`, `latency_ms`, `notes`。系统化落盘在专题 07。

---



## 完成标准

- **能解释**：一次 Chat 的输入（messages、model、参数）与输出（content、usage、model）。
- **能说明**：`temperature` / `max_tokens` 对输出的影响。
- **能配置**：OpenAI 或 DeepSeek（`.env` + `models.yaml` 占位符）。
- **能运行**：`02_provider_switching` 默认对比与 `--verbose` 全量日志。
- **能说明**：为何业务用 `config_ref` 而不是写死 model 字符串。



### 运行与观察

```bash
cd source/demos/02_provider_switching
python provider_switching.py
python provider_switching.py --verbose
```

应看到至少 2 行对比；verbose 下可见 system/user 与完整 assistant 回复。详见 [demo README](../../source/demos/02_provider_switching/README.md)。

### 自检题（不看正文能否答）

1. 多轮对话的历史存在哪里？通过 API 的哪个字段带给模型？
2. 为什么业务代码应写 `config_ref="chat.dev_chat"` 而不是 `model="gpt-4o"`？
3. 把 Chat 模型名填进 embedding 接口会导致什么问题？

---



## 本节沉淀

- 新增 `llm_core` 调用层（`LLMClient`、`models.yaml`、`observability`）与 `02_provider_switching` demo。  
- 需求评审助手具备：**按任务切换模型配置、统一响应结构与可观测日志**；00 的 `02_first_chat` 保留作 SDK 直调对照。  
- 下一节 [02_prompt_engineering_for_apps.md](02_prompt_engineering_for_apps.md) 将在同一 `LLMClient` 上叠加 Prompt 模板。

---



## 相关专题

- 上一篇：[00_llm_problem_space.md](00_llm_problem_space.md)  
- 下一篇：[02_prompt_engineering_for_apps.md](02_prompt_engineering_for_apps.md)  
- 课程大纲：[outline.md](outline.md)

