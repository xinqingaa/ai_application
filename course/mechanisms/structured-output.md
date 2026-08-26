# Structured Output 与应用侧校验

> 机制篇：解释为什么“像 JSON”还不够，以及生成约束、JSON 解析、Schema 校验和业务消费如何形成可信输出链路。
>
> 课程位置：[标准学习路径](../learning-path.md)。必要前置是 [Prompt Engineering](prompt-engineering.md)；本文交付模型结果的生成约束、解析、Schema 校验和业务接受边界。

---

## 为什么“请输出 JSON”不是数据契约

假设模型返回下面这段内容：

```text
以下是结果：
[
  {"category": "api", "severity": "严重", "description": "..."}
]
```

人可以看懂，程序却至少面临四个问题：前缀让 JSON 解析失败，根对象可能不符，severity 不在业务枚举中，字段内容也可能没有证据。

因此“输出 JSON”不是一个开关，而是一条分层链路：

```text
Prompt 描述输出意图
→ 供应商生成约束尽量限制形状
→ JSON parser 判断语法
→ Pydantic 判断字段和类型
→ 业务校验判断来源与规则
```

本文沿这条链实现，并要求每次失败都保留发生阶段。应用不能把 HTTP 200 或 JSON 可解析直接当作业务成功。

## 从概率文本到分层校验

### 本节方案性质

Structured Outputs 也没有唯一标准答案。不同模型、SDK、业务对象和前端形态，都会影响最终实现方式。本节给的是需求评审助手当前阶段的一套最小工程实践，而不是要求所有 AI 应用都照搬 `ReviewRiskList` 或三种 mode 对比。

需要区分三层：

| 层级 | 本节怎么理解 |
| --- | --- |
| **通用原则** | 模型输出进入业务前必须有应用侧契约校验；JSON 可解析不等于业务可用；失败要区分 API / JSON / Schema / 内容质量 |
| **工程实践** | 用 Pydantic 作为 Schema 真源，用 `response_format` 尝试前移约束，用 `parse_risk_list` 统一判层 |
| **项目取舍** | 本节只设计 `ReviewRiskList`，只比较 `none / json_object / json_schema`，只校验 citation 结构，不校验 citation 真伪 |

所以本节不是在说“所有项目都应该这样定义风险字段”。真正要迁移的是方法：先定义业务能消费的数据契约，再让模型尽量按契约生成，最后由应用校验并记录失败层级。

### Structured Output 是什么

**输入**：`messages`（含 Prompt 渲染后的任务与材料）+ 可选 `response_format` + 模型参数。  
**输出（应用可信部分）**：经 Pydantic 校验后的 `list[ReviewRisk]`，或带 `error_stage` 的解析失败结果——**不是**原始的 `assistant` 字符串。

与 Prompt Engineering 的区别是：Prompt 用来**描述**希望输出的形态；Schema 用来**定义**应用契约，解析器负责**强制执行**，必要时还可以把 Schema 前移到 API 的生成约束阶段。

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

Prompt 的输出说明、应用 Schema 和模型 API 的结构化约束必须描述同一份业务字段，不能各自维护相互漂移的契约。

**根形态**：v4 要求 JSON 对象且含 `risks` 数组（不能是裸数组——OpenAI Structured Outputs 也要求根为 object）：

```json
{
  "risks": [ /* ReviewRisk[] */ ]
}
```

`parse_risk_list` 为兼容 Prompt 工程 v3，仍接受根为数组的 legacy 形态；**本节契约与 v4 Prompt 均以 `{ "risks": [...] }` 为准**。

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

### 与 Prompt Engineering 的分工

| | Prompt 工程 | 结构化输出 |
| --- | --- | --- |
| 任务描述 | Prompt 六段式、版本化 | v4 Output 与 Schema 字段一致 |
| 输出形态 | v3 文字要求 JSON | 契约 + 校验 + 可选 API 约束 |
| 应用侧类型 | 无 | `list[ReviewRisk]` |

Prompt 工程 和 结构化输出 的边界也可以这样理解：Prompt 工程 让模型“尽量按约定说话”，结构化输出 让应用“只接受符合契约的话”。这两个动作缺一不可。

如果只有 Prompt 工程，没有 结构化输出，模型可能大多数时候返回看起来正确的 JSON，但一旦字段漂移，前端和数据库会在更远的位置失败。如果只有 结构化输出，没有 Prompt 工程，模型完全不知道要输出哪些字段，解析失败会非常频繁。Prompt 和 Schema 的关系不是替代，而是前后两道门：Prompt 在生成前对齐意图，Schema 在生成后确认结果。

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

旧式教学常单独讲「通用提取器」脚本。在本项目里，`LLMClient.chat_structured` + `response_model` + `parse_risk_list` **就是**提取器抽象：一次调用返回 `StructuredLLMResponse`（含 `llm`、`parse`、`request_params`）。批量跑样例、harness 落盘在调用 Harness 深化；本节先学会单次调用的判层与校验。

这也是本轮课程组织和旧脚本模式的差异：我们不再为“JSON Mode”“Pydantic”“Retry”“Extractor”各写一组孤立脚本，而是在 `llm_core` 里把结构化调用收成一个可复用能力。后续需求评审助手要生成风险卡片、测试点、追问列表或报告摘要，都应该复用同一套“调用 → 解析 → 判层”的模式。

你真正要掌握的不是某个函数名，而是这条工程原则：**模型输出进入业务之前，必须经过应用定义的契约边界**。

---

## 建立 Schema、调用与解析闭环

同一份业务 Schema 必须贯穿 Prompt 输出说明、模型 API 的结构化约束、本地解析校验和业务消费。模型侧约束减少格式漂移，本地校验负责最终信任边界；解析失败必须保留原始输出和失败阶段，不能用空对象伪装成功。

## 框架模式与本地校验怎样协作

| 方式 | 与本项目 |
| --- | --- |
| OpenAI `response_format` | `OpenAICompatProvider` 透传；`json_object` / `json_schema` 依平台而定 |
| Pydantic v2 | `model_validate` / `model_json_schema()` 作为 Schema 真源 |
| LangChain output parser | 可包装 `parse_risk_list`；本仓库 YAML + Pydantic 为真源，避免两套 Prompt |

---

## 按失败阶段定位结构化问题

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
- **当节判断**：记录 bad case；引用是否存在由 RAG 链路校验；批量结果由 Calling Harness 留档，质量判断再交给 Eval。

### 常见误区

| 误区 | 纠正 |
| --- | --- |
| 「用了 JSON Mode 就不需要 Pydantic」 | `json_object` 不保证字段契约；Pydantic 始终执行 |
| 「API_ERROR = 解析写错了」 | 先区分 API 能力层与 `parse` 层 |
| 「parse 失败就多试几次」 | schema 失败若 Prompt/Schema 未改，重试无效；完整重试环见 可靠调用 |
| 「assistant 字符串能 parse 就算成功」 | 必须 `parse.ok`；原文只作日志 |

### 本节不做（defer）

| 能力 | 目标节 | 当节最小判断 |
| --- | --- | --- |
| schema 失败自动重试、错误反馈给模型 | 可靠调用 | 会读 `error_stage` / `message` 定位层，不盲目重试 |
| harness 落盘、字段缺失率统计 | 调用 Harness | demo 三 mode 肉眼对比 + 笔记 |
| citation `source_id` 是否存在 | RAG | 只校验 citation **结构**，不校验真伪 |
| 完整 `ReviewReport`、六类评审输出 | 后续专题 | 本节只做 `risks` 列表 |
| 流式 + 结构化同时 | 流式机制 | 本节假定非流式一次返回 |

---

## 用模式对照观察约束强度

对照实验固定任务和业务 Schema，只改变模型侧结构化模式，观察 API 能力不支持、JSON 解析失败和业务校验失败分别出现在哪一层。命令、输出和读码路径见[配套实验](../labs/structured-output.md)。

## 怎样判断输出可以进入业务

只有当结构可解析、字段满足业务约束、失败阶段可定位、原始响应可追溯，并且前端能够区分成功与失败时，结果才可以进入业务链路。Schema 变化还必须触发相应的 Prompt、测试和消费者检查。

## 交给项目的结果契约

- `llm_core.schemas`、`parse_risk_list`、`build_response_format`、`chat_structured`、`risk_review_v4.yaml`。
- 需求评审助手具备：**结构化风险列表契约 + 分层解析 + 三 mode 可观测**。
- Reliability 会复用这里的解析结果判断一次调用是否真正成功；Streaming 则是独立的按需交互支撑。

完成实验后回到 [标准学习路径](../learning-path.md)。需要查完整知识关系时再使用 [知识地图](../knowledge-map.md)。
