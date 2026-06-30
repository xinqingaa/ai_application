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

这里最容易误解的是：Structured Output 不是“让模型听话地返回 JSON”。如果只停在 JSON 语法层，前端仍然可能拿到中文字段、错误枚举、缺失字段或根结构漂移。真正的结构化输出要回答三个问题：

1. 这份输出的字段契约由谁定义？
2. 模型返回后由谁校验？
3. 失败时应用如何判断错在格式、契约还是供应商能力？

需求评审助手后续要把风险结果交给前端卡片、数据库、评估样例和 Workflow 节点。只要其中任何一层把「看起来像 JSON」误当成「已经可信」，系统就会在后面更难调试的位置失败。

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

这条链的关键不是要求每次都使用最强的 `json_schema`，而是理解每层在解决什么问题。供应商不支持 `json_schema` 时，项目仍然可以退回 `json_object` 或 prompt-only；但无论退到哪一层，本地 Pydantic 校验都不能省。否则应用就无法知道「模型输出不可用」和「模型输出可用但内容质量差」之间的区别。

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

这三层经常被初学者混在一起。一个简单判断方法是：

- Prompt 解决“模型是否知道你想要什么”。
- `response_format` 解决“生成阶段是否受到格式或 schema 约束”。
- Pydantic 解决“应用是否承认这份结果可用”。

其中只有第三层是应用自己的最终防线。前两层都可能因为模型、供应商、提示词或上下文变化而失败。Pydantic 不会让模型更聪明，但它会让应用更诚实：能用就是能用，不能用就明确失败，而不是把不合格输出悄悄塞给下游。

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

这份契约刻意不追求复杂。初学结构化输出时，最重要的是把根形态、字段名、枚举和失败分层跑通，而不是一开始设计完整 `ReviewReport`。`ReviewRiskList` 小到足以观察每个失败点，又贴近需求评审助手的真实业务对象。

### 与 02 的分工

| | 02 | 03 |
| --- | --- | --- |
| 任务描述 | Prompt 六段式、版本化 | v4 Output 与 Schema 字段一致 |
| 输出形态 | v3 文字要求 JSON | 契约 + 校验 + 可选 API 约束 |
| 应用侧类型 | 无 | `list[ReviewRisk]` |

02 和 03 的边界也可以这样理解：02 让模型“尽量按约定说话”，03 让应用“只接受符合契约的话”。这两个动作缺一不可。

如果只有 02，没有 03，模型可能大多数时候返回看起来正确的 JSON，但一旦字段漂移，前端和数据库会在更远的位置失败。如果只有 03，没有 02，模型完全不知道要输出哪些字段，解析失败会非常频繁。Prompt 和 Schema 的关系不是替代，而是前后两道门：Prompt 在生成前对齐意图，Schema 在生成后确认结果。

### 四类失败案例

结构化输出的学习重点不是“让模型一次成功”，而是能把失败分层。下面四类失败在真实 AI 应用里非常常见。

**1. API 层失败**

`json_schema` 模式请求发出后，供应商直接返回错误。此时没有 assistant 文本，也就谈不上 `json.loads` 或 Pydantic。你应先怀疑 provider 能力、参数格式、模型是否支持该 response_format，而不是立刻改 Prompt。

**2. JSON 层失败**

模型返回了一段文字，里面也许有 JSON 片段，但整体不是合法 JSON。常见表现是 Markdown 围栏、多余解释、截断、根类型不支持。此时要看 `assistant_raw`，再比较 `prompt_only` 和 `json_mode` 是否减少了格式层失败。

**3. Schema 层失败**

JSON 语法合法，但字段不符合契约。比如 `category` 写成中文「交互」，`level` 写成「较高」，或者根对象不是 `{ "risks": [...] }`。此时不要只说“模型没听话”，而要检查 Prompt Output 是否和 Pydantic 字段一致，枚举是否写清，示例是否误导。

**4. 契约通过但内容质量差**

`parse.ok=True`，但 `rationale` 仍可能泛泛而谈，citation 也可能指向不存在的来源。这说明 Schema 只保证形状，不能保证事实正确。这个问题要交给 RAG citation 校验、eval 样例和人工评审，而不是继续加字段约束。

这四类失败对应不同处理方式。把它们混为一谈，就会出现错误修复：API 不支持却改 Pydantic，字段枚举错却盲目重试，引用不存在却以为 Schema 能解决。

### `chat_structured` 即本项目的「提取器」

旧式教学常单独讲「通用提取器」脚本。在本项目里，`LLMClient.chat_structured` + `response_model` + `parse_risk_list` **就是**提取器抽象：一次调用返回 `StructuredLLMResponse`（含 `llm`、`parse`、`request_params`）。批量跑样例、harness 落盘在专题 07 深化；本节先学会单次调用的判层与校验。

这也是本轮课程组织和旧脚本模式的差异：我们不再为“JSON Mode”“Pydantic”“Retry”“Extractor”各写一组孤立脚本，而是在 `llm_core` 里把结构化调用收成一个可复用能力。后续需求评审助手要生成风险卡片、测试点、追问列表或报告摘要，都应该复用同一套“调用 → 解析 → 判层”的模式。

你真正要掌握的不是某个函数名，而是这条工程原则：**模型输出进入业务之前，必须经过应用定义的契约边界**。

---

## 最小实现

本节最小实现要验证一件事：模型返回文本后，应用能不能稳定判断「是否可用」以及「不可用时错在哪一层」。因此正文只保留两个关键片段：Schema 真源与解析判层。`response_format` 和 `chat_structured` 是把这两者接进请求流程的胶水，理解职责即可。

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

[`structured.py`](../../source/packages/llm_core/structured.py) 根据 `structured_mode` 决定是否给 API 传 `response_format`：

- `none`：不传，让 Prompt 自己约束输出。
- `json_object`：传 JSON Mode，约束格式层。
- `json_schema`：把 `ReviewRiskList.model_json_schema()` 前移到 API 层。

这里的关键是：`json_schema` 的 schema **来自 Pydantic**，而不是手写第二份 JSON Schema。否则最常见的事故就是 Prompt、Pydantic、API Schema 三份字段不同步。

### 3. 调用与解析合一

[`client.py`](../../source/packages/llm_core/client.py) 的 `chat_structured` 做三件事：先按 mode 组装 `response_format`，再调用普通 `chat`，最后立刻把 `llm.content` 交给 `parse_structured_content`。它返回的不是单纯文本，而是 `StructuredLLMResponse`：里面同时保留原始模型响应、解析结果和请求参数。

注意顺序：**调用后立刻 parse**。如果先把原始字符串交给 UI 或数据库，再在别处解析，失败就会扩散。结构化输出的工程习惯是：在模型调用边界处就把「可用 / 不可用」判清楚。

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

业务消费只看一个原则：**只有 `parse.ok` 为真时，才把数据交给 UI、数据库或 Workflow**。失败时保存 `error_stage` 和 `message`，而不是把原始 assistant 文本强行当作成功结果。

这条边界会直接影响前端体验。前端拿到 `ReviewRisk` 时可以放心渲染枚举、标签和引用列表；拿到 parse 失败时应该展示「结构化生成失败 / 可重试 / 需要人工查看」这样的状态，而不是崩在 JSON 解析上。

从 AI Native 前端视角看，Structured Output 是把模型输出变成界面状态的前提。自由文本只能展示成一段话；结构化结果可以变成风险卡片、筛选器、引用列表、状态标签、人工确认队列和评估样本。也就是说，结构化输出不是后端洁癖，而是前端体验和后续工作流的基础。

但也要保持边界感：`parse.ok=True` 只说明形状可信，不说明内容一定正确。比如模型可能返回了合法的 `source_id` 字符串，但这个 source 是否真实存在，要到 RAG citation 校验；模型可能给出合法的 `medium` 风险等级，但等级判断是否合理，要靠 eval 或人工评审。Schema 负责形状，质量仍要继续评估。

### 前端如何消费结构化状态

需求评审助手的前端不应该只接收一段 `assistant_text`。更合理的状态分层是：

- `parse.ok=True`：渲染风险卡片，支持按 `category` / `level` 筛选。
- `error_stage=json`：提示“模型输出格式异常”，允许重试或查看原文。
- `error_stage=schema`：提示“模型输出字段不符合契约”，记录 bad case。
- `API_ERROR`：提示“模型能力或供应商调用失败”，可换配置或降级。
- `parse.ok=True` 但 citation 待校验：展示风险卡片，但把引用可信度交给后续 RAG 校验。

这类状态设计会在 06_ai_native 和 07_projects 里进一步进入工作台体验。本节先把后端结果分层做好，前端未来才有条件展示“AI 到底卡在哪一步”。

### 为什么本节不做自动重试

很多人学结构化输出时，会立刻想到“解析失败就重试”。这确实重要，但本节先不做，是因为不判层的重试经常是无效的。

如果失败来自供应商不支持 `json_schema`，重试同一个请求大概率还是失败；应该降级到 `json_object` 或换模型。如果失败来自枚举非法，简单重试可能偶尔成功，但更好的做法是把错误反馈给模型或修正 Prompt Output。如果失败来自 citation 不真实，重试不一定解决，需要检索和引用校验。

所以本节只要求你学会读 `error_stage`。自动重试、错误反馈和降级策略放到专题 06，是在判层能力之上继续加工程控制。

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

关键路径：

- [`source/packages/llm_core/schemas/review.py`](../../source/packages/llm_core/schemas/review.py)：风险列表 Schema 真源。
- [`source/packages/llm_core/schemas/parse.py`](../../source/packages/llm_core/schemas/parse.py)：解析与 `error_stage` 判层。
- [`source/packages/llm_core/structured.py`](../../source/packages/llm_core/structured.py)：`response_format` 构建。
- [`source/demos/02_provider_switching/structured_risk.py`](../../source/demos/02_provider_switching/structured_risk.py)：本节观察入口。

完整文件说明与参数变体放在 [demo README](../../source/demos/02_provider_switching/README.md)。

### 实现步骤（与最小实现对照）

1. `get_prompt("review.risk_review", version="4.0.0")` + `render_prompt` → `messages`（与 02 相同变量 `requirement_text`、`evidence_block`）。
2. 对每种 demo mode 映射 `structured_mode`：`prompt_only`→`none`，`json_mode`→`json_object`，`json_schema`→`json_schema`。
3. `client.chat_structured(messages, CONFIG_REF, structured_mode=...)`；捕获 `LLMError` 记 API 失败。
4. 读 `result.parse.ok`、`error_stage`、`risks`，判断失败层级。

demo 默认固定 S2、Prompt v4、`chat.dev_chat` 和 `temperature=0`，只改变 `structured_mode`。这个设计是为了让你把注意力放在「约束层级」上，而不是把样例、模型和 Prompt 改动混在一起。

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

本节最重要的观察不是「哪种 mode 一定最好」，而是你能否说清失败发生在哪一层：没有返回文本、不是合法 JSON、字段不符合 Schema，还是供应商不支持某个 API 参数。这个判层能力会直接服务 06 的重试降级和 07 的 harness 统计。

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
