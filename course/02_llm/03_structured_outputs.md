# 03. Structured Outputs

> 在 02 用 Prompt **描述**「希望输出 JSON」之后，本篇回答：**为什么“像 JSON”还不够，如何把模型输出变成应用可信的数据契约**，以及 `response_format` 与 Pydantic 各自解决哪一层问题。

---

## 真实问题

专题 02 已经把 Prompt 从“随手写提示”收敛成 `prompt_id + version + YAML`。风险审查 Prompt v3 也开始用文字要求模型输出 JSON。到这里会自然遇到一个新问题：**Prompt 说“请输出 JSON”，并不等于应用真的拿到了可用数据**。

Structured Outputs 这一节不只是学习某个 API 参数，也不是为了让终端里打印一段漂亮 JSON。它要解决的是：**模型生成的内容如何进入前端、数据库、评估和后续 Workflow，而不是停留在聊天文本里**。

### 学习者真实问题

如果你主要来自前端 / Flutter / 客户端开发，最容易把 Structured Outputs 理解成“让模型返回 JSON”。这只说对了一半。真实应用里更关键的是：

- JSON 语法对了，字段名和枚举值是否也对？
- 字段缺失时，程序怎么知道失败发生在 JSON 解析还是业务字段校验？
- 前端要渲染卡片、列表和状态标签时，拿到的是一段字符串，还是已经校验过的结构？
- `response_format`、JSON Mode、Pydantic 分别解决哪一层问题？

本节要建立的直觉是：**Structured Outputs 的核心不是 JSON，而是契约**。JSON 只是载体；字段名、类型、枚举、失败原因和应用侧校验，才是 AI 应用能继续往下走的关键。

### 产品真实问题

继续看「订单详情页新增申请售后按钮，对接售后接口 v2」这个 PRD。评审助手识别出风险后，用户看到的不应该是一整段 Markdown：“第一条风险……第二条风险……”。产品需要的是可被界面消费的数据：

- 前端把每条风险渲染成卡片。
- 卡片上能稳定显示标题、类别、等级、依据和引用。
- 后端可以把风险写入数据库。
- 评估脚本可以统计字段缺失、枚举非法和解析失败。
- 后续 Workflow 可以把这些风险继续汇总成评审报告。

如果这里只靠 Prompt 写一句“请输出 JSON”，模型可能返回一段肉眼能懂、程序却接不住的内容。

例如：

```json
[
  {"风险类别": "接口", "风险等级": "较高", "说明": "..."}
]
```

这段内容在聊天窗口里“看起来可用”，但程序并不知道 `风险类别` 是否等于 `category`，也不能把 `较高` 放进只接受 `high / medium / low` 的 UI 和评估逻辑。Structured Outputs 要解决的就是这个断点：**从人能看懂，变成应用能接住**。

### 工程真实问题

从工程上看，输出结构化有三类问题，不能混在一起：

| 层级 | 典型问题 | 需要谁解决 |
| --- | --- | --- |
| 格式层 | 输出不是 JSON、被 Markdown 包住、被截断 | Prompt + JSON Mode + 本地 JSON 解析 |
| 契约层 | 字段名漂移、缺字段、枚举非法 | Schema + Pydantic |
| 能力层 | 某些供应商不支持 `json_schema` | Provider 能力识别 + 降级策略 |

这就是为什么本节不只比较“输出像不像 JSON”，而要同时观察：

- 请求里有没有 `response_format`。
- 模型是否返回合法 JSON。
- 返回内容是否通过 Pydantic。
- 失败发生在 API、JSON 解析还是 Schema 校验。

本节的最小落点选择「风险列表」，不是因为 Structured Outputs 只能用于风险，而是因为它足够小、足够贴近需求评审助手，又能完整覆盖“字段、枚举、引用、失败阶段”这几个关键点。完整评审报告、citation 真伪校验、自动重试和 harness 统计都先不做。

---

## 本节产出

本节最终要让需求评审助手多一个能力：

```text
模型文本输出
→ JSON 解析
→ Schema 校验
→ 应用可使用的风险结构
```

落到这次 demo，就是一次 `review.risk_review@4.0.0` 调用成功后，应用侧能拿到经过 Pydantic 校验的风险列表：

```python
result.parse.risks  # list[ReviewRisk]，长度通常 2–4，S2 样例 PRD 要求「3 条」故常见为 3
```

这里的 `ReviewRisk` 只是本节的业务例子。真正要掌握的是这条通用模式：**模型输出必须先经过应用自己的契约校验，才能继续进入 UI、数据库、评估或 Workflow**。失败时不把文本强行当成功，而是返回 `StructuredParseResult`，记录失败阶段和原因。

---

## 数据契约：模型应返回什么 JSON

真源在 [`schemas/review.py`](../../source/packages/llm_core/schemas/review.py)。Prompt（[`risk_review_v4.yaml`](../../source/packages/llm_core/prompts/review/risk_review_v4.yaml)）的 Output 段、Pydantic、`json_schema` 模式的 API Schema **必须描述同一份字段**。

### 根形态

v4 要求模型返回 **JSON 对象**，且必须有 `risks` 数组（不能是裸数组——OpenAI Structured Outputs 也要求根为 object）：

```json
{
  "risks": [ /* ReviewRisk[] */ ]
}
```

`parse_risk_list` 为兼容 02 v3，仍接受根为数组的 legacy 形态；**本节契约与 v4 Prompt 均以 `{ "risks": [...] }` 为准**。

### 完整样例（单条风险）

```json
{
  "risks": [
    {
      "title": "订单详情页「申请售后」按钮展示条件与订单状态机可能不一致",
      "category": "interaction",
      "level": "medium",
      "rationale": "按钮展示由 after_sale_eligible 控制，但状态机要求 status=paid 且 sub_status!=closed，两者若不一致会导致错误展示或隐藏。",
      "citations": [
        {
          "source_id": "Evidence - 订单状态机",
          "excerpt": "仅 status=paid 且 sub_status!=closed 的订单允许发起售后"
        }
      ]
    }
  ]
}
```

### 字段说明

| 字段 | JSON 类型 | Python（`ReviewRisk`） | 必填 | 取值 / 约束 | 含义 |
| --- | --- | --- | --- | --- | --- |
| `risks` | array | `list[ReviewRisk]` | 是 | 0..n 项 | 风险列表；条数由任务与材料决定，Schema **不固定** 为 3 |
| `title` | string | `str` | 是 | 非空建议 | 风险标题，卡片主文案 |
| `category` | string | `RiskCategory` 枚举 | 是 | 见下表 | 研发视角分类 |
| `level` | string | `RiskLevel` 枚举 | 是 | `high` / `medium` / `low` | 严重程度 |
| `rationale` | string | `str` | 是 | 应引用材料表述 | 依据说明 |
| `citations` | array | `list[Citation]` | 否，默认 `[]` | 见下 | 引用的证据片段 |

**`RiskCategory` 合法值**（必须英文 snake，不能写「交互」）：

`interaction` · `state_flow` · `api` · `multi_platform` · `exception` · `other`

**`Citation` 子对象**：

| 字段 | 类型 | 必填 | 含义 |
| --- | --- | --- | --- |
| `source_id` | string | 是 | 证据片段 id；本节不校验是否存在，03_rag 校验 |
| `excerpt` | string | 否 | 材料中的短引文 |

### 设计取舍（为何这样定）

1. **根对象包 `risks`**：满足 Structured Outputs 的 object 根；将来 `ReviewReport` 可在同一根上增加 `summary`、`clarifications` 等字段，而不改单条风险结构。  
2. **枚举用英文字符串**：前后端、eval、日志统一；Pydantic `str, Enum` 在 `model_validate` 时拒绝中文类别。  
3. **`citations` 默认空数组**：证据不足时可无引用；有引用时结构先对齐 RAG 的 `source_id`。  
4. **Prompt 与 Schema 双写**：模型「读」Prompt 里的 Output 段；应用「验」Pydantic。`json_schema` 模式还把 `ReviewRiskList.model_json_schema()` 发给 API，与 Pydantic 验的是**同一份契约**。  
5. **S2 与「3 条」**：样例 PRD 文本写「请列出 3 条研发侧潜在风险」，模型常返回 3 条，这是**任务提示**，不是 Schema 的 `minItems: 3`。

---

## 解决方案：三层约束

本节的核心不是“选一种最强模式”，而是把输出控制拆成三层。三层都重要，但职责不同：

```text
第 1 层 · Prompt（软约束）
  risk_review_v4 的 ## Output 描述字段名与枚举

第 2 层 · API response_format（生成约束，可选）
  none          → 不传 response_format
  json_object   → {"type":"json_object"}
  json_schema   → Pydantic 导出的 JSON Schema + strict

第 3 层 · Pydantic（应用契约，始终执行）
  parse_risk_list：extract_json_text → json.loads → model_validate
```

Pydantic **始终执行**。`json_schema` 只是把同一份 Schema **前移到生成阶段**（平台支持时）；不支持时（如 DeepSeek 常返回 400）仍可用 `json_mode` + Pydantic。

### 三种 `structured_mode`（demo 唯一变量）

固定：`prompt@4.0.0`、`config_ref`、`temperature`、S2 样例。**只换** `structured_mode`：

| demo 标签 | `structured_mode` | 请求差异 | 约束到什么程度 |
| --- | --- | --- | --- |
| `prompt_only` | `none` | 无 `response_format` | 只靠 Prompt |
| `json_mode` | `json_object` | `response_format: {type: json_object}` | 合法 JSON 对象 |
| `json_schema` | `json_schema` | 完整 `ReviewRiskList` JSON Schema | 字段级（平台支持时） |

**JSON 可解析 ≠ Schema 通过**：`category: "交互"` 可 `json.loads`，但 `model_validate` 失败 → `error_stage=schema`。见 `llm_core/tests/test_parse.py` 中 `test_bad_enum`。

### 与 02 的分工

| | 02 | 03 |
| --- | --- | --- |
| 任务描述 | Prompt 六段式、版本化 | v4 Output 与 Schema 字段一致 |
| 输出形态 | v3 文字要求 JSON | 契约 + 校验 + 可选 API 约束 |
| 应用侧类型 | 无 | `list[ReviewRisk]` |

---

## 最小实现

按一次 `chat_structured` 的调用顺序。

### 1. Schema：`schemas/review.py`

```python
class ReviewRisk(BaseModel):
    title: str
    category: RiskCategory
    level: RiskLevel
    rationale: str
    citations: list[Citation] = Field(default_factory=list)

class ReviewRiskList(BaseModel):
    risks: list[ReviewRisk]
```

改字段时同步：`review.py` → `risk_review_v4.yaml` Output → 相关测试。

### 2. `response_format`：`structured.build_response_format`

```python
def build_response_format(response_model, mode, *, schema_name="response"):
    if mode == "none":
        return None
    if mode == "json_object":
        return {"type": "json_object"}
    schema = response_model.model_json_schema()
    return {
        "type": "json_schema",
        "json_schema": {"name": schema_name, "schema": schema, "strict": True},
    }
```

`json_schema` 的 schema **来自** `ReviewRiskList.model_json_schema()`，不是手写第二份。

### 3. 调用：`LLMClient.chat_structured`

```python
result = client.chat_structured(
    messages,
    "chat.dev_chat",
    structured_mode="json_object",
    temperature=0,
)
# result.llm.content      → 模型返回的字符串（通常为 JSON）
# result.parse.risks      → list[ReviewRisk] 或 None
# result.parse.ok         → 是否通过 Pydantic
# result.request_params   → 含 response_format 的完整请求参数（便于日志与调试）
```

### 4. 解析：`parse_risk_list`

[`schemas/parse.py`](../../source/packages/llm_core/schemas/parse.py)：

```text
assistant 文本
  → extract_json_text（去掉 ```json 围栏）
  → json.loads          → 失败：error_stage=json
  → ReviewRiskList 或 list[ReviewRisk] 校验 → 失败：error_stage=schema
  → StructuredParseResult(ok=True, risks=[...])
```

### 5. Prompt v4：让模型读懂同一份契约

三种 demo mode **共用** [`risk_review_v4.yaml`](../../source/packages/llm_core/prompts/review/risk_review_v4.yaml)；Constraints 与 v3 同级，Output 段字段与上表一致。

### 6. 业务使用：只消费校验后的结果

```python
if result.parse.ok:
    for risk in result.parse.risks:
        save_risk_card(risk.title, risk.category, risk.level, risk.rationale, risk.citations)
else:
    record_parse_failure(result.parse.error_stage, result.parse.message)
```

### 本节实现重点

读代码时优先抓住四个点，不必把注意力放在日志格式或完整报告设计上：

| 重点 | 文件 | 要理解什么 |
| --- | --- | --- |
| Schema 真源 | `schemas/review.py` | 字段、枚举和根对象由应用定义，不由模型临时决定 |
| API 约束 | `structured.py` | `response_format` 只是把 Schema 前移到生成阶段，不替代本地校验 |
| 统一调用 | `client.py` | `chat_structured` 负责调模型后立刻解析，不把原始文本伪装成成功 |
| 解析分层 | `schemas/parse.py` | 区分 `empty`、`json`、`schema`，方便后续重试、降级和评估 |

本节不追求“模型一定输出完美 JSON”。更重要的是：**无论模型和供应商表现如何，应用侧都能知道结果是否可用，以及失败发生在哪一层**。

---

## 主流框架实现

| 方式 | 本项目 |
| --- | --- |
| OpenAI `response_format` | `OpenAICompatProvider` 透传 |
| Pydantic v2 | `model_validate` / `model_json_schema` |
| LangChain output parser | 可包装 `parse_risk_list` |

---

## 失败分析与能力边界

| 阶段 | 表现 | 缓解 |
| --- | --- | --- |
| API | `response_format type unavailable` | 降级 `json_mode`；DeepSeek 常见 |
| `empty` | 无内容 | max_tokens / 重试 |
| `json` | 非 JSON、截断 | `json_object` |
| `schema` | 缺字段、枚举非法 | Prompt/Schema 同步；或 `json_schema`（若平台支持） |

本节不做：完整 `ReviewReport`、harness 落盘、citation 存在性校验、schema 失败自动重试。

---

## 本节实战

### 目标

在 S2 上理解：**同一 JSON 契约**下，只换 API `response_format`，观察 tokens、延迟、parse 结果与风险内容差异。

### 配置（`structured_risk.py` 顶部）

| 常量 | 默认 | 说明 |
| --- | --- | --- |
| `PROMPT_VERSION` | `4.0.0` | 三种 mode 共用 |
| `CONFIG_REF` | `chat.dev_chat` | 三种 mode 共用 |
| `MODES` | 三种全跑 | 可改为 `("json_mode",)` |
| `VERBOSE` | `False` | 见下 |
| `TEMPERATURE` | `0` | 对比时固定 |

```bash
pip install -e .
cd source/demos/02_provider_switching
python structured_risk.py
```

### 输出含义（简要）

- **默认模式（`VERBOSE=False`）**：每个 mode 一块，只看运行结果。保留 `status`、`model`、`latency_ms`、`tokens`、`parse`，以及校验后的风险字段；长的 `rationale` / `excerpt` 会截断，字段名不省略。
- **全量模式（`VERBOSE=True`）**：用于调试请求与响应。`messages` 在实验头打印一次；每个 mode 打完整 `request_params`、`assistant_raw`、`usage` 和 `parse_result`。不再打印压缩后的风险字段。

典型观察（DeepSeek 等）：`json_mode` 相对 `prompt_only` completion tokens 更少、延迟更低；`json_schema` 常 `API_ERROR`，属平台能力而非 parse 失败。

---

## 完成标准

- 能说出模型 JSON 根形态、`ReviewRisk` 各字段类型与枚举取值。  
- 能画三层模型，说明 Pydantic 为何始终执行。  
- 能按顺序说明：Schema → `build_response_format` → `chat_structured` → `parse_risk_list`。  
- 能解释 demo 固定 Prompt/`config_ref`、只变 `structured_mode` 的原因。  
- 能区分 API 失败、`json` 失败、`schema` 失败。

### 运行与观察

```bash
cd source/demos/02_provider_switching
python structured_risk.py
```

应能看到 `[experiment]` 头部，以及 `prompt_only`、`json_mode`、`json_schema` 三个结果块：

- `prompt_only`：只靠 Prompt 输出 JSON，若模型夹带 Markdown 或根形态漂移，可能出现 `parse_fail(json)` 或 `parse_fail(schema)`。
- `json_mode`：请求里带 `response_format: {"type":"json_object"}`，通常能保证 JSON 对象，但仍可能因字段缺失、枚举不合法而 `schema` 失败。
- `json_schema`：请求里带 Pydantic 导出的完整 JSON Schema；若供应商支持，字段稳定性最高；若供应商不支持，可能出现 `API_ERROR`，这属于模型平台能力差异，不是本地解析失败。

无论使用哪种 mode，只要 API 返回了文本，应用侧都必须经过 `parse_risk_list` 和 Pydantic；只有 `result.parse.ok=True` 时，才能把 `result.parse.risks` 交给前端卡片、数据库或后续 Workflow。

### 自检题

1. JSON 里的 `risks` 与 Python 的 `result.parse.risks` 是什么关系？  
2. 为何 `category` 不能写成中文「交互」？  
3. `json_object` 解决了什么、没解决什么？  
4. `ReviewRiskList` 为何要包一层 `risks`？  
5. 如果 `json_schema` 返回 `API_ERROR`，应先怀疑 Prompt、Pydantic，还是供应商能力？为什么？
6. 改 `RiskCategory` 后还要改哪些文件？

---

## 本节沉淀

- `llm_core.schemas`、`parse_risk_list`、`build_response_format`、`chat_structured`、`risk_review_v4.yaml`。  
- 下一节 [04_streaming_and_conversation.md](04_streaming_and_conversation.md) 在保持结构化契约下讨论流式与对话状态。

---

## 相关专题

- 上一篇：[02_prompt_engineering_for_apps.md](02_prompt_engineering_for_apps.md)  
- 下一篇：[04_streaming_and_conversation.md](04_streaming_and_conversation.md)  
- 课程大纲：[outline.md](outline.md)
