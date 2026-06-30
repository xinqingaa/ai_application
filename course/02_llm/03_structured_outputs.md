# 03. Structured Outputs

> 在 02 用 Prompt **描述**「希望输出 JSON」之后，本篇回答：**为什么“像 JSON”还不够，如何把模型输出变成应用可信的数据契约**，以及 `response_format` 与 Pydantic 各自解决哪一层问题。

---

## 真实问题

专题 02 已经把 Prompt 从随手写的提示收敛成 `prompt_id + version + YAML`。风险审查 Prompt v3 也开始用文字要求模型输出 JSON。到这里会自然遇到一个新问题：**Prompt 说“请输出 JSON”，并不等于应用真的拿到了可用数据**。

Structured Outputs 不是某个 API 参数的别名，也不是为了让终端打印漂亮 JSON。它要解决的是：**模型生成的内容如何进入前端、数据库、评估和后续 Workflow，而不是停留在聊天文本里**。

### 学习者真实问题

如果你主要来自前端 / Flutter / 客户端开发，最容易把 Structured Outputs 理解成「让模型返回 JSON」。这只说对了一半。真实应用里更关键的是：

- JSON 语法对了，字段名和枚举值是否也对？
- 字段缺失时，程序怎么知道失败发生在 JSON 解析还是业务字段校验？
- 前端要渲染卡片、列表和状态标签时，拿到的是一段字符串，还是已经校验过的结构？
- `response_format`、JSON Mode、Pydantic 分别解决哪一层问题？

本节要建立的直觉是：**Structured Outputs 的核心不是 JSON，而是契约**。JSON 只是载体；字段名、类型、枚举、失败阶段和应用侧校验，才是 AI 应用能继续往下走的关键。

### 产品真实问题

产品同学小周提交 S2 样例 PRD：订单详情页新增「申请售后」按钮，需对接售后接口 v2。评审助手在 02 已经能列出风险，评审负责人希望在会前看到**可筛选、可对比、可入库**的风险卡片，而不是每次复制一大段 Markdown 到会议纪要里。

第一次联调时，后端把模型返回的 `assistant` 全文存进数据库，前端直接 `JSON.parse`。某次模型返回：

```json
[
  {"风险类别": "接口", "风险等级": "较高", "说明": "售后 v2 兼容性未在 PRD 中说明"}
]
```

聊天窗口里「看起来能用」，但产品很快发现问题：前端枚举只认 `high / medium / low`，筛选器绑的是 `category` 不是「风险类别」；第二次跑同一 PRD，模型改成根对象包 `risks`，字段名又换成英文但 `category` 写成「交互」。会议里无法对比「这次比上次多发现了什么」，评估脚本也无法统计「枚举非法占比」。

这些不是「模型不够聪明」，而是**没有把输出当作程序接口来设计**。应用需要一份稳定的**数据契约**：字段名、类型、枚举、根形态在发请求前就定好，返回后必须经过校验，失败时要能判断错在哪一层，而不是把原始字符串伪装成成功。

### 工程真实问题

从工程上看，输出结构化至少分三层，不能混在一起：

| 层级 | 典型问题 | 当节由谁解决 |
| --- | --- | --- |
| 格式层 | 不是 JSON、被 Markdown 围栏包住、被截断 | Prompt + JSON Mode + `extract_json_text` / `json.loads` |
| 契约层 | 字段名漂移、缺字段、枚举非法 | Schema + Pydantic `model_validate` |
| 能力层 | 供应商不支持 `json_schema` | Provider 能力识别 + 降级 `structured_mode` |

因此本节要同时观察：请求里有没有 `response_format`、模型是否返回可解析 JSON、是否通过 Pydantic、失败发生在 API、JSON 解析还是 Schema 校验。

本节最小落点选「风险列表」`ReviewRisk` / `ReviewRiskList`，因为足够小、贴近需求评审助手，又能覆盖字段、枚举、引用与 `error_stage`。完整 `ReviewReport`、citation 真伪校验、自动重试与 harness 统计本节不展开（见文末边界与 defer）。

---

## 基础原理

### Structured Output 是什么

**输入**：`messages`（含 Prompt 渲染后的任务与材料）+ 可选 `response_format` + 模型参数。  
**输出（应用可信部分）**：经 Pydantic 校验后的 `list[ReviewRisk]`，或带 `error_stage` 的解析失败结果——**不是**原始的 `assistant` 字符串。

与 02 的区别：02 用 Prompt **描述**希望输出的形状；03 用 Schema **定义**契约，用解析器 **强制执行**，并可选把 Schema 前移到 API 生成阶段。

### 从自由文本到契约：机制递进

下面这条链是本章的认知主线。每一步都更强，但**不能互相替代**；项目里的 `chat_structured` 是把整条链收成一次调用，学习时仍须逐步理解。

**第 1 步 · 自由文本 / Markdown**

模型返回「第一条风险：接口兼容性……」人类能读，程序无法稳定绑定到 `title`、`level` 字段，更不能做枚举筛选和入库。**反例**：前端把 Markdown 当 JSON 解析直接报错。

**第 2 步 · Prompt 要求 JSON（软约束）**

在 Prompt 的 Output 段写明字段名与枚举（如 `risk_review_v4.yaml`）。比自由文本强很多，但模型仍可能：用中文 key、根形态改成裸数组、夹带 ` ```json ` 围栏、枚举写成「较高」。**反例**：`{"风险类别":"接口"}` 肉眼可用，`category` 字段不存在。

**第 3 步 · JSON Mode（`response_format: json_object`）**

API 层要求模型输出合法 JSON **对象**（具体能力因平台而异）。保证「大概是 JSON」，**不保证**字段名、枚举、嵌套形状与业务 Schema 一致。**反例**：`category: "交互"` 能 `json.loads`，但 `RiskCategory` 枚举校验失败。

**第 4 步 · Structured Outputs / `json_schema`（可选，生成约束）**

把 `ReviewRiskList.model_json_schema()` 发给 API，在生成阶段前移字段约束。平台支持时字段更稳；不支持时（如部分 DeepSeek 配置）可能直接 `API_ERROR`——这是**能力层**问题，不是本地 parse 写错。**当节判断**：见 `error_stage` 前先区分是 `LLMError`（API）还是有 body 但 parse 失败。

**第 5 步 · Pydantic 校验（应用契约，始终执行）**

无论前几步如何，应用侧必须用同一份 Schema 做 `model_validate`。通过才得到 `list[ReviewRisk]`；失败返回 `StructuredParseResult`，`error_stage` 为 `json` 或 `schema`。**原则**：JSON 可解析 ≠ Schema 通过。

**第 6 步 · 业务只消费 `parse.ok`**

UI、数据库、Workflow 只读校验后的结构；`assistant` 原文仅用于日志与调试。`chat_structured` 把 3–5 步串成一次调用，但**第 5 步永远不能省**。

```text
自由文本 → Prompt JSON → json_object → json_schema（可选）→ Pydantic（必须）→ 业务
         软约束      格式层        生成层契约          应用层契约
```

### 三层约束与职责

与上表对应，本项目把职责拆成三层：

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

`json_schema` 只是把同一份 Schema **前移到生成阶段**；不支持时仍用 `json_mode` 或 `none` + Pydantic。改字段时必须同步：`schemas/review.py` → `risk_review_v4.yaml` Output → 相关测试。

### 三种 `structured_mode`（demo 对照变量）

`structured_risk.py` 固定 `prompt@4.0.0`、`config_ref`、`temperature`、S2 样例，**只换** `structured_mode`：

| demo 标签 | `structured_mode` | 请求差异 | 约束到什么程度 |
| --- | --- | --- | --- |
| `prompt_only` | `none` | 无 `response_format` | 只靠 Prompt |
| `json_mode` | `json_object` | `response_format: {type: json_object}` | 合法 JSON 对象 |
| `json_schema` | `json_schema` | 完整 `ReviewRiskList` JSON Schema | 字段级（平台支持时） |

### 数据契约：`ReviewRiskList`

真源在 [`schemas/review.py`](../../source/packages/llm_core/schemas/review.py)。Prompt（[`risk_review_v4.yaml`](../../source/packages/llm_core/prompts/review/risk_review_v4.yaml)）的 Output 段、Pydantic、`json_schema` 模式的 API Schema **必须描述同一份字段**。

**根形态**：v4 要求 JSON 对象且含 `risks` 数组（不能是裸数组——OpenAI Structured Outputs 也要求根为 object）：

```json
{
  "risks": [ /* ReviewRisk[] */ ]
}
```

`parse_risk_list` 为兼容 02 v3，仍接受根为数组的 legacy 形态；**本节契约与 v4 Prompt 均以 `{ "risks": [...] }` 为准**。

**单条风险样例**：

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

| 字段 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| `risks` | array | 是 | `list[ReviewRisk]`；条数由任务决定，Schema 不固定 `minItems: 3` |
| `title` | string | 是 | 卡片主文案 |
| `category` | string | 是 | `RiskCategory` 枚举，英文 snake |
| `level` | string | 是 | `high` / `medium` / `low` |
| `rationale` | string | 是 | 应引用材料表述 |
| `citations` | array | 否 | `source_id` + 可选 `excerpt` |

**`RiskCategory`**：`interaction` · `state_flow` · `api` · `multi_platform` · `exception` · `other`（不能写中文「交互」）。

**设计取舍（摘要）**：根对象包 `risks` 便于日后扩展 `summary`；枚举用英文字符串统一前后端与 eval；`citations` 默认 `[]`；Prompt 与 Schema 双写；S2 PRD 写「列出 3 条」是任务提示，不是 Schema 的 `minItems`。

### 与 02 的分工

| | 02 | 03 |
| --- | --- | --- |
| 任务描述 | Prompt 六段式、版本化 | v4 Output 与 Schema 字段一致 |
| 输出形态 | v3 文字要求 JSON | 契约 + 校验 + 可选 API 约束 |
| 应用侧类型 | 无 | `list[ReviewRisk]` |

### `chat_structured` 即本项目的「提取器」

旧式教学常单独讲「通用提取器」脚本。在本项目里，`LLMClient.chat_structured` + `response_model` + `parse_risk_list` **就是**提取器抽象：一次调用返回 `StructuredLLMResponse`（含 `llm`、`parse`、`request_params`）。批量跑样例、harness 落盘在专题 07 深化；本节先学会单次调用的判层与校验。

---

## 最小实现

按一次结构化调用的顺序走读代码。

### 1. Schema 真源

[`schemas/review.py`](../../source/packages/llm_core/schemas/review.py)：

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

字段由应用定义，不由模型临时发明。`ReviewRiskList` 包装一层 `risks` 是为了满足 API 根对象要求，并为日后 `ReviewReport` 留扩展位。

### 2. 构建 `response_format`

[`structured.py`](../../source/packages/llm_core/structured.py)：

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

`json_schema` 的 schema **来自** `model_json_schema()`，避免手写第二份 JSON Schema 与 Pydantic 漂移。

### 3. 调用与解析合一

[`client.py`](../../source/packages/llm_core/client.py)：

```python
response_format = build_response_format(response_model, structured_mode, schema_name=schema_name)
if response_format is not None:
    call_params["response_format"] = response_format
request_params = merge_chat_request_params(config, call_params)

llm = self.chat(messages, config_ref, debug=debug, **call_params)
parse = parse_structured_content(llm.content)
return StructuredLLMResponse(
    llm=llm, parse=parse, structured_mode=structured_mode, request_params=request_params,
)
```

注意：`chat` 之后**立刻** `parse`，不把原始 `content` 当成功。`request_params` 保留完整请求参数，便于日志与 demo 对照。

### 4. 解析分层与 `error_stage`

[`schemas/parse.py`](../../source/packages/llm_core/schemas/parse.py)：

```python
def parse_risk_list(content: str) -> StructuredParseResult:
    text = extract_json_text(content)
    if not text:
        return StructuredParseResult(ok=False, risks=None, error_stage="empty", ...)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return StructuredParseResult(ok=False, risks=None, error_stage="json", message=str(exc), ...)
    try:
        if isinstance(data, list):
            risks = TypeAdapter(list[ReviewRisk]).validate_python(data)
        elif isinstance(data, dict) and "risks" in data:
            risks = ReviewRiskList.model_validate(data).risks
        ...
        return StructuredParseResult(ok=True, risks=risks)
    except ValidationError as exc:
        return StructuredParseResult(ok=False, risks=None, error_stage="schema", message=str(exc), ...)
```

**判层口诀**：

- `empty`：无内容 → 怀疑 `max_tokens`、模型拒答、或 API 未返回 body。
- `json`：`json.loads` 失败 → 怀疑 Markdown 围栏、截断、非 JSON 文本；可对比 `json_mode`。
- `schema`：JSON 合法但 `model_validate` 失败 → 怀疑字段名/枚举/根形态与 Schema 不一致；查 Prompt Output 是否与 `review.py` 同步。

`extract_json_text` 会剥掉 ` ```json ` 围栏——这是 Prompt-only 场景常见的格式层问题。

### 5. 业务消费

```python
if result.parse.ok:
    for risk in result.parse.risks:
        save_risk_card(risk.title, risk.category, risk.level, risk.rationale, risk.citations)
else:
    record_parse_failure(result.parse.error_stage, result.parse.message)
```

只有 `parse.ok` 为真时，才把数据交给 UI 或数据库。

---

## 主流框架实现

| 方式 | 与本项目 |
| --- | --- |
| OpenAI `response_format` | `OpenAICompatProvider` 透传；`json_object` / `json_schema` 依平台而定 |
| Pydantic v2 | `model_validate` / `model_json_schema()` 作为 Schema 真源 |
| LangChain output parser | 可包装 `parse_risk_list`；本仓库 YAML + Pydantic 为真源，避免两套 Prompt |

---

## 失败分析与能力边界

### 排查路径（表现 → 原因 → 怎么验证）

**1. `API_ERROR`（`json_schema` 模式）**

- **表现**：demo 该 mode 块显示 `API_ERROR`，无 `parse_result`。
- **原因**：供应商不支持或拒绝该 `response_format`（DeepSeek 等常见），属于能力层。
- **验证**：看是否仅在 `json_schema` 失败；改 `json_mode` 或 `prompt_only` 是否恢复；**不要**先改 Pydantic。

**2. `parse_fail(json)`**

- **表现**：`error_stage=json`，`message` 含 `JSONDecodeError` 或「不支持的 JSON 根类型」。
- **原因**：Markdown 围栏、多余说明文字、截断、根类型不是 object/array。
- **验证**：`VERBOSE` 下看 `assistant_raw`；对比 `prompt_only` vs `json_mode`；单测见 `test_parse` 对围栏的处理。

**3. `parse_fail(schema)`**

- **表现**：`error_stage=schema`，JSON 能 `loads` 但枚举或字段非法。
- **原因**：`category: "交互"`、缺 `title`、中文 key 等契约漂移。
- **验证**：对照 `review.py` 与 v4 Output；运行 `llm_core/tests/test_parse.py` 中 `test_bad_enum`。

**4. JSON 合法、业务仍不可信**

- **表现**：`parse.ok` 为真，但 `rationale` 胡编、citation 指向不存在材料。
- **原因**：Schema 只保证**形状**，不保证**内容真伪**。
- **当节判断**：记录 bad case；引用是否存在由 `03_rag` 校验；质量统计由专题 07 harness 负责。

### 常见误区

| 误区 | 纠正 |
| --- | --- |
| 「用了 JSON Mode 就不需要 Pydantic」 | `json_object` 不保证字段契约；Pydantic 始终执行 |
| 「API_ERROR = 解析写错了」 | 先区分 API 能力层与 `parse` 层 |
| 「parse 失败就多试几次」 | schema 失败若 Prompt/Schema 未改，重试无效；完整重试环见 06 |
| 「assistant 字符串能 parse 就算成功」 | 必须 `parse.ok`；原文只作日志 |

### 本节不做（defer）

| 能力 | 目标节 | 当节最小判断 |
| --- | --- | --- |
| schema 失败自动重试、错误反馈给模型 | 06 | 会读 `error_stage` / `message` 定位层，不盲目重试 |
| harness 落盘、字段缺失率统计 | 07 | demo 三 mode 肉眼对比 + 笔记 |
| citation `source_id` 是否存在 | 03_rag | 只校验 citation **结构**，不校验真伪 |
| 完整 `ReviewReport`、六类评审输出 | 后续专题 | 本节只做 `risks` 列表 |
| 流式 + 结构化同时 | 04 | 本节假定非流式一次返回 |

---

## 本节实战

### 目标

在 S2 上理解：**同一 JSON 契约**下，只换 API `response_format`（三种 `structured_mode`），观察 parse 结果、tokens 与延迟差异，并会用 `error_stage` 判层。

### 涉及文件

```text
source/packages/llm_core/
├── client.py              # chat_structured
├── structured.py          # build_response_format, StructuredLLMResponse
├── schemas/
│   ├── review.py          # ReviewRisk, ReviewRiskList
│   └── parse.py           # parse_risk_list, StructuredParseResult
└── prompts/review/
    └── risk_review_v4.yaml

source/demos/02_provider_switching/
├── structured_risk.py     # 本节入口
├── _shared.py             # 样例、evidence、日志
└── evidence_s2.json
```

### 实现步骤（与最小实现对照）

1. `get_prompt("review.risk_review", version="4.0.0")` + `render_prompt` → `messages`（与 02 相同变量 `requirement_text`、`evidence_block`）。
2. 对每种 demo mode 映射 `structured_mode`：`prompt_only`→`none`，`json_mode`→`json_object`，`json_schema`→`json_schema`。
3. `client.chat_structured(messages, CONFIG_REF, structured_mode=...)`；捕获 `LLMError` 记 API 失败。
4. 读 `result.parse.ok`、`error_stage`、`risks`；`VERBOSE` 时可对照 `request_params` 与 `assistant_raw`。

### 配置（`structured_risk.py` 顶部）

| 常量 | 默认 | 说明 |
| --- | --- | --- |
| `SAMPLE_ID` | `S2` | PRD 样例 |
| `PROMPT_VERSION` | `4.0.0` | 三 mode 共用 |
| `CONFIG_REF` | `chat.dev_chat` | 三 mode 共用 |
| `MODES` | 三种全跑 | 可改为 `("json_mode",)` 加快 |
| `TEMPERATURE` | `0` | 对比时固定 |

### 运行方式

```bash
pip install -e .
cd source/demos/02_provider_switching
python structured_risk.py
```

### 预期结果

应看到 `[experiment]` 头部，以及 `prompt_only`、`json_mode`、`json_schema` 三个结果块：

- **`prompt_only`**：只靠 Prompt；可能出现围栏、裸数组或字段漂移 → `json` / `schema` 失败。
- **`json_mode`**：通常得到 JSON 对象；仍可能 `schema` 失败（枚举、缺字段）。
- **`json_schema`**：平台支持时字段最稳；不支持时出现 `API_ERROR`（能力层，非 parse 实现错误）。

无论哪种 mode，有文本就必须过 `parse_risk_list`；仅 `result.parse.ok=True` 时可把 `result.parse.risks` 交给下游。

### 建议观察清单

- [ ] 三 mode 的 `parse.ok` / `error_stage` 差异
- [ ] `json_mode` 相对 `prompt_only` 是否减少 `json` 阶段失败
- [ ] `json_schema` 是 `API_ERROR` 还是 parse 失败——能否说出判层理由
- [ ] 校验通过时，`category` / `level` 是否为英文枚举值

---

## 完成标准

- 能解释自由文本、Prompt JSON、`json_object`、`json_schema`、Pydantic 各解决哪一层遗留问题。
- 能说出 `ReviewRisk` / `ReviewRiskList` 根形态与主要字段枚举。
- 能按顺序说明：Schema → `build_response_format` → `chat_structured` → `parse_risk_list`。
- 能解释 demo 固定 Prompt/`config_ref`、只变 `structured_mode` 的原因。
- 能区分 API 失败、`error_stage=json`、`error_stage=schema`。

### 运行与观察

```bash
cd source/demos/02_provider_switching
python structured_risk.py
```

### 自检题

1. 为什么评审会需要 Structured Output，而不能只把模型 Markdown 存库？
2. Prompt v4 已要求 JSON，为什么还要 Pydantic？`json_object` 能否替代 Pydantic？
3. `error_stage=json` 与 `error_stage=schema` 各应先查 Prompt 还是 Schema？
4. `json_schema` 返回 `API_ERROR` 时，应先怀疑 Prompt、Pydantic，还是供应商能力？
5. `ReviewRiskList` 为什么要包一层 `risks`，而不是裸数组？
6. 改 `RiskCategory` 枚举后还要改哪些文件？

---

## 本节沉淀

- `llm_core.schemas`、`parse_risk_list`、`build_response_format`、`chat_structured`、`risk_review_v4.yaml`。
- 需求评审助手具备：**结构化风险列表契约 + 分层解析 + 三 mode 可观测**。
- 下一节 [04_streaming_and_conversation.md](04_streaming_and_conversation.md) 在保持结构化契约下讨论流式与对话状态。

---

## 相关专题

- 上一篇：[02_prompt_engineering_for_apps.md](02_prompt_engineering_for_apps.md)
- 下一篇：[04_streaming_and_conversation.md](04_streaming_and_conversation.md)
- 课程大纲：[outline.md](outline.md)
