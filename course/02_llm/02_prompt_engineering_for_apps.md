# 02. 面向应用的 Prompt Engineering

> 在 01 学会用 `LLMClient` 调模型之后，本篇回答：**messages 里的任务描述从哪来、怎么版本化、怎么与 Schema / 检索证据分工**——把 Prompt 当作需求评审助手与模型之间的**任务协议**，而不是聊天框里随手多打几句话。

---

## 真实问题

专题 01 解决了「用 `config_ref` 调哪台引擎」。但同一引擎上，**你塞给模型的文字不同，输出可以天差地别**。需求评审助手不是单一聊天任务：既要读 PRD、又要找风险、又要追问缺失、最后还要汇总报告——如果所有场景共用一段 system prompt，或把约束散落在业务代码字符串里，产品会很快失控。

### 学习者真实问题

- **Prompt 和「多写几句提示」有什么区别？**  
  Prompt 在本项目里指**可命名、可版本化、可渲染**的任务协议（通常落在 YAML + 变量），不是某次请求里临时拼的一段字。

- **system 和 user 里各写什么？**  
  常见约定：`system` 放角色与长期约束；`user` 放**本次任务**、材料占位（PRD 片段、证据块）、输出要求。具体划分可按任务调整，但要有稳定模板，便于回归对比。

- **改了一个词的 Prompt，怎么知道变好还是变坏？**  
  需要 `prompt_id + version`、固定样例（如 `samples.json` 的 S2）、固定 `temperature`，对比输出——本节用三版 `review.risk_review` 练这件事；系统化 harness 在专题 07。

- **模型输出的 JSON 字段名谁定？**  
  **Prompt** 用自然语言或示例描述「希望长什么样」；**Schema（专题 03）** 用 Pydantic / API 约束「字段叫什么、类型是什么」。本节 v3 只在 Prompt 里**文字要求** JSON，不做校验。

### 产品真实问题：同一助手，多种任务

继续小周团队的「订单详情 · 申请售后」PRD。评审助手在生命周期里会反复调用模型，**任务不同，对 Prompt 的要求也不同**：

| 任务 | 模型要做什么 | Prompt 若写得太糊会怎样 |
| --- | --- | --- |
| 需求理解 | 从 PRD 提炼目标、范围、涉及模块 | 摘要漏模块、把假设当事实 |
| 风险审查 | 按交互、状态、接口等维度找风险 | 空泛「可能有问题」、编造未出现的接口 |
| 技术影响 | 判断接口/数据/依赖变化 | 与 PRD 无关的架构臆测 |
| 测试验收 | 产出可执行的验收点 | 无法落地的测试口号 |
| 缺失追问 | 证据不足时列出 blocking 问题 | 该问不问，或问非所问 |
| 报告汇总 | 合并多段结论 | 重复、矛盾、新增无依据风险 |

若每个场景在代码里 `f"你是助手... {prd}"`，会出现：

- **约束互相冲突**（一处要求简短，另一处要求列全所有风险维度）。
- **无法单任务回归**（改风险 Prompt 却影响摘要行为）。
- **无法与 eval 绑定**（日志里只有「调了一次模型」，不知道用的哪版 Prompt）。

产品需要的是：**按任务选 `prompt_id`（如 `review.risk_review`）+ `version`**，材料通过变量注入，而不是在业务里散落长字符串。

### 工程真实问题

| 问题 | 典型表现 | 本节方向 |
| --- | --- | --- |
| Prompt 与调用耦合 | `client.chat` 前硬编码 system 字符串 | `get_prompt` + `render_prompt` |
| 无版本 | 「上周那版比较好」但找不到 | YAML 内 `version: "2.0.0"` |
| 与 RAG 职责混淆 | 在 Prompt 里塞编造的公司规章 | `evidence_block` 变量；真检索在 03_rag |
| 与 Schema 职责混淆 | 只靠 Prompt 说「输出 JSON」却不校验 | v3 练格式；03 做 Pydantic + API |
| 观测缺失 | 不知道生产用了哪版 Prompt | 日志应带 `prompt_id@version`（本节先在手写实验里养成习惯） |

本篇在 `llm_core.prompts` 沉淀 **YAML 真源 + 渲染为 messages**，并在 demo 里对**同一 PRD 样例**对比三版风险审查 Prompt。

---

## 基础原理

### Prompt 是什么：任务协议，不是咒语

在应用工程里，可以把一次 Chat 调用拆成：

```text
messages = 任务协议（Prompt 模板 + 变量）
         + 模型参数（temperature、max_tokens，来自 models.yaml / 调用方）
         + 引擎（config_ref → 哪家 API、哪个 model）
```

**Prompt 不负责选模型**（01 的 `config_ref`），**不负责执行工具**（04_agent），**不负责检索**（03_rag）。它负责告诉模型：

1. 你是谁、专业边界是什么（role）  
2. 这一步要完成什么（task）  
3. 依据哪些材料（context / 变量）  
4. 必须遵守什么（constraints）  
5. （可选）参考什么例子（examples）  
6. 输出长什么样（output_format，可与 Schema 衔接）

这六段语义称为**六段式任务协议**——顺序在 YAML 里可以合并，但语义建议齐全，尤其是 **constraints** 与 **output_format**。

### 六段式协议详解（以风险审查为例）

| 段落 | 作用 | `review.risk_review` 示例要点 |
| --- | --- | --- |
| **role** | 角色与专业边界 | 「研发团队的需求评审助手」「只基于材料」 |
| **task** | 当前一步的原子目标 | 「识别研发侧风险，标明类别与依据」 |
| **context** | 输入材料占位 | `{{requirement_text}}`、`{{evidence_block}}` |
| **constraints** | 必须/禁止 | 不得编造；证据不足不硬答；覆盖交互/状态/接口等维度 |
| **examples** | few-shot 参考 | v3 给一条「合格风险长什么样」（防照搬） |
| **output_format** | 输出形态 | v2：自然语言列表；v3：要求 JSON 数组字段 |

**为什么要拆段？** 方便 diff 与版本管理：v1→v2 往往只加 **constraints**；v2→v3 往往只动 **examples + output_format**。若全部糊在一段里，无法做受控实验。

### Prompt 与 Schema 的分工

| 层 | 谁定义 | 做什么 | 本节 |
| --- | --- | --- | --- |
| Prompt | 产品 / 提示工程师 | 任务目标、材料边界、输出**描述** | v3 文字要求 JSON 字段 |
| Schema | 应用 / 后端 | 字段名、类型、枚举、必填 | **03** 实现 `ReviewRisk` 等 |
| 校验器 | 应用 | `model_validate`、业务规则、citation 检查 | **03** |

类比：Prompt 像「请按报名表填写」；Schema 像「报名表表格本身」。只改 Prompt 而不做 Schema，模型仍可能字段漂移——所以 v3 你会看到「像 JSON 但不一定能 `json.loads` / 字段不全」的现象，这正是 03 存在的理由。

### Prompt 与 RAG 证据的分工

| 层 | 职责 |
| --- | --- |
| **RAG（03_rag）** | 从知识库检索，格式化出带 `source_id` 的片段 |
| **Prompt** | 通过 `{{evidence_block}}` 接收片段，并要求结论绑定材料、证据不足时拒答或追问 |
| **应用** | 校验 citation 是否指向真实 source（03_rag / 03 结构化课深化） |

本节使用静态文件 [`evidence_s2.json`](../../source/demos/02_provider_switching/evidence_s2.json) 模拟检索结果，让你观察 **有 Evidence 约束时输出如何变化**——不实现向量检索。

### 变量与模板渲染

常用变量（需求评审助手）：

| 变量 | 含义 | 本节来源 |
| --- | --- | --- |
| `requirement_text` | 用户 PRD / 需求描述 | `samples.json` 样例 `user_content` |
| `evidence_block` | 检索到的证据格式化文本 | `evidence_s2.json`（静态） |
| `review_dimensions` | 可选维度标签 | 后续 workflow 用 |
| `previous_summary` | 多步工作流上游摘要 | 04_agent / workflow 用 |

渲染规则（实现见 [`registry.py`](../../source/packages/llm_core/prompts/registry.py)）：

- YAML 中 `system` / `user` 字符串里的 `{{variable}}` 由 `render_prompt(template, variables)` 替换。  
- 未提供的占位符替换为空字符串（应避免漏传关键变量）。  
- 输出为 OpenAI 风格 `[{"role":"system",...},{"role":"user",...}]`，直接交给 `LLMClient.chat`。

### 版本管理：`prompt_id` + `version`

每个 YAML 文件包含：

```yaml
prompt_id: review.risk_review
version: "2.0.0"
model_config_ref: chat.dev_chat
```

- **`prompt_id`**：逻辑名，业务代码只引用它。  
- **`version`**：语义化版本字符串；改约束或示例应**升版本**，便于对比与回滚。  
- **`model_config_ref`**：该 Prompt **默认**用哪条模型配置（可与 01 的 `chat.dev_chat` 对齐）。

**加载规则（`get_prompt`）**：扫描 `llm_core/prompts/` 下各子目录中的 `*.yaml`，用文件内的 **`prompt_id` + `version` 字段** 定位模板——**不是**用文件名。`risk_review_v1.yaml` 只是人工命名习惯；即便改名，只要 yaml 里仍是 `version: "1.0.0"`，`get_prompt(..., "1.0.0")` 就能找到。

约定：同一 `(prompt_id, version)` 只对应**一个** yaml 文件，避免重复注册。

未来 harness（07）会把样例绑定到 `prompt_id@version`；本节在笔记里手动记录即可。

### 从 01 的硬编码到 02 的模板：数据流

```text
prompt_compare.py（实验配置：样例 id、版本列表、temperature）
    │
    ├─ load_sample(S2)  → requirement_text
    ├─ load evidence_s2.json → evidence_block
    │
    ▼
get_prompt("review.risk_review", version="2.0.0")
    │
    ▼
render_prompt(tpl, variables)  → messages
    │
    ▼
LLMClient.chat(messages, tpl.model_config_ref, temperature=0)
    │
    ▼
对比表：v1 / v2 / v3 的 latency、tokens、content 预览
```

01 里写在 `provider_switching.py` 顶部的 `SYSTEM_PROMPT`，在 02 之后应逐步消失——**任务描述进 YAML**，Python 只负责选版本、灌变量、调用客户端。

---

## 最小实现

### 三版 `review.risk_review` 的设计意图

同一任务（风险审查）、同一样例（S2）、同一 `temperature=0`，只变 Prompt 版本：

| 版本 | 文件 | 刻意差异 | 观察重点 |
| --- | --- | --- | --- |
| **v1.0.0** | [`risk_review_v1.yaml`](../../source/packages/llm_core/prompts/review/risk_review_v1.yaml) | 短 system + 直接把 PRD 当 user | 是否空泛、是否编造接口细节 |
| **v2.0.0** | [`risk_review_v2.yaml`](../../source/packages/llm_core/prompts/review/risk_review_v2.yaml) | + Task / Evidence / Constraints / 维度 checklist | 是否更贴材料、少幻觉 |
| **v3.0.0** | [`risk_review_v3.yaml`](../../source/packages/llm_core/prompts/review/risk_review_v3.yaml) | v2 + 1 条 example + **要求 JSON 字段** | 结构是否更稳；JSON 是否可解析（仍可能失败） |

### 核心 API（真实代码）

```python
from llm_core import LLMClient
from llm_core.prompts import get_prompt, render_prompt

tpl = get_prompt("review.risk_review", version="2.0.0")
messages = render_prompt(tpl, {
    "requirement_text": prd_text,
    "evidence_block": evidence_text,
})
resp = client.chat(messages, tpl.model_config_ref, temperature=0)
```

`get_prompt` 在 [`prompts/registry.py`](../../source/packages/llm_core/prompts/registry.py) 扫描 `prompts/review/*.yaml`；`PromptTemplate` 定义在 [`prompts/template.py`](../../source/packages/llm_core/prompts/template.py)。

### v1 YAML 片段（极简对照）

```yaml
system: |
  你是研发团队的需求评审助手，负责从研发视角识别 PRD 中的潜在风险。
user: |
  {{requirement_text}}
```

### v2 为何多加 Constraints

v2 的 user 模板显式分出 `## Task`、`## Requirement`、`## Evidence`、`## Constraints`。这是产品里最常见的「质量跃迁」：**不是换更大的模型，而是把禁止编造、维度 checklist 写清楚**。你应在对比实验里重点看 v1→v2 是否减少了「接口 v3」「未提及的埋点」类幻觉。

### v3 为何加 Example + JSON 文字

- **Example**：few-shot 只给**风格**，并注明「勿照搬」，降低过时业务规则污染（见失败分析）。  
- **JSON output_format**：为 03 结构化输出做铺垫——本节**不**做 `json.loads` 成功率统计，只在笔记里肉眼看是否多出 Markdown 包裹、字段是否齐全。

---

## 主流框架实现

| 方式 | 做什么 | 与本项目关系 |
| --- | --- | --- |
| **字符串 + `.format` / `{{}}` 替换** | 模板与数据分离 | `llm_core.prompts` 当前实现 |
| **Jinja2** | 条件、循环、包含 | 未引入；任务协议复杂后再考虑 |
| **LangChain `ChatPromptTemplate`** | 把 template 包成 Runnable | `03_rag` 链可读取**同一 YAML 真源**，避免两套 Prompt |
| **厂商 Prompt 管理后台** | 云端版本、A/B | 认知即可；本仓库 YAML + Git 便于学习与 diff |

原则：**配置真源在仓库**（YAML + 变量契约），框架只是消费方。不要在 LangChain 里再写一份与 YAML 不同步的长字符串。

---

## 失败分析与能力边界

### 常见失败模式

| 失败 | 原因 | 缓解 |
| --- | --- | --- |
| **约束冲突** | 同一 Prompt 里「尽量简短」与「列全所有风险」 | 单任务单目标；拆成不同 `prompt_id` |
| **Few-shot 污染** | 示例含过时业务规则，模型照搬 | 示例进版本管理；注明勿照搬；用 eval 淘汰 |
| **Prompt 过长** | 塞全文 PRD + 全库 evidence | 上下文工程（专题 05）；RAG 压缩 |
| **无证据强答** | 只有 Prompt 没有检索或 evidence 为空 | constraints 写拒答规则；03_rag 提供真证据 |
| **字段漂移** | output_format 与 Schema 不一致 | Schema 真源在 03；改字段同步改 Prompt |
| **版本漂移** | 生产不知用了哪版 | 日志打 `prompt_id@version`；07 harness |

### Prompt 不能替代什么

- **检索是否命中**、引用是否真实 → RAG + 应用侧 citation checker  
- **工具是否该调用、参数是否合法** → Tool Runtime（04_agent）  
- **权限、审计、人工审批** → 业务服务与 Workflow  
- **「变好变差」的统计结论** → eval / harness（05、07）

### 本节不做（边界清单）

- 不实现六份完整 Prompt YAML（只落地 `review.risk_review` 三版；其余 `prompt_id` 见下表作规划）。  
- 不实现 `llm_core.schemas`、`ReviewRisk` Pydantic、Structured Outputs API（**03**）。  
- 不实现 harness 落盘、自动字段缺失率（**07**）。  
- 不实现真实向量检索（**03_rag**）；仅用 `evidence_s2.json` 静态块。  
- 不新建 demo 目录；02 实验入口为同目录 [`prompt_compare.py`](../../source/demos/02_provider_switching/prompt_compare.py)。

### 需求评审助手 Prompt 集（规划表，非本节代码）

| prompt_id | 适用场景 | 主要变量 | 输出（03 深化） |
| --- | --- | --- | --- |
| `review.requirement_summary` | 评审入口压缩材料 | `requirement_text` | 短摘要 |
| **`review.risk_review`** | **风险识别（本节实现）** | `requirement_text`, `evidence_block` | 风险列表 / JSON |
| `review.technical_impact` | 接口与数据影响 | `requirement_text`, `evidence_block` | impact 列表 |
| `review.test_acceptance` | 测试验收点 | `requirement_text`, `evidence_block` | test_points |
| `review.clarification` | 证据不足追问 | `requirement_text`, `evidence_block` | 追问列表 |
| `review.report_synthesis` | 汇总报告 | 上游结构化字段 | `ReviewReport` |

---

## 本节实战

### 目标

本节结束后，需求评审助手具备：**命名 Prompt 模板（YAML）→ 变量渲染 → `LLMClient` 调用** 的闭环；并能在固定样例上对比 v1/v2/v3 风险审查 Prompt 的差异。

### 涉及文件

```text
source/packages/llm_core/prompts/
├── template.py
├── registry.py
└── review/
    ├── risk_review_v1.yaml
    ├── risk_review_v2.yaml
    └── risk_review_v3.yaml

source/demos/02_provider_switching/
├── _shared.py
├── prompt_compare.py      # 02 入口
├── evidence_s2.json
├── provider_switching.py  # 01 入口（未改行为）
└── README.md
```

### `prompt_compare.py` 实验配置

入口文件：[`prompt_compare.py`](../../source/demos/02_provider_switching/prompt_compare.py) 第 25–38 行「实验配置」块。**无需命令行参数**；改常量后重新 `python prompt_compare.py` 即可。

| 常量 | 作用 | 默认值 | 可改示例 | 改完后观察什么 |
| --- | --- | --- | --- | --- |
| **`SAMPLE_ID`** | 选用哪条 PRD 样例 | `"S2"` | `"S1"`、`"S3"`、`"S5"` | `requirement_text` 来源；S3 无材料看是否胡编；S5 长文本看 token 与遗漏 |
| **`PROMPT_ID`** | 加载哪套命名 Prompt | `"review.risk_review"` | 仅当仓库有对应 yaml 时改 | 必须等于目标 yaml 内的 **`prompt_id` 字段**（非文件名） |
| **`PROMPT_VERSIONS`** | 对比哪些版本（顺序=表格行顺序） | `("1.0.0","2.0.0","3.0.0")` | `("2.0.0","3.0.0")` 或 `("1","2","3")` | 每一项必须等于某个 yaml 内的 **`version` 字段**；简写 `"1"`→`"1.0.0"` |
| **`VERBOSE`** | 表后是否输出完整日志 | `False` | `True` | 见 `format_call_log`：完整 messages、params、assistant、usage |
| **`TEMPERATURE`** | 三次调用的采样温度 | `0` | `0.7` | 对比 **Prompt 版本**时应固定 `0`，否则结论不干净 |
| **`EVIDENCE_FILE`** | 静态 evidence 文件路径 | `evidence_s2.json` | 指向不存在的路径 | 文件缺失 → 占位文案「无检索证据…」；观察 v2/v3 约束是否生效 |

#### 与 `prompts/review/*.yaml` 的对应关系

`prompt_compare.py` 里的 **`PROMPT_ID` / `PROMPT_VERSIONS`** 与 yaml **内部字段**一一对应，**与文件名无强制绑定**：

```text
PROMPT_ID          →  每个 yaml 顶部的 prompt_id 字段
PROMPT_VERSIONS[]  →  每个 yaml 顶部的 version 字段（逐项调用 get_prompt）
```

实现见 [`registry.py`](../../source/packages/llm_core/prompts/registry.py)：`get_prompt(prompt_id, version)` 在所有 `prompts/*/*.yaml` 中查找 **`prompt_id` 相等且 `version` 规范化后相等** 的那一份。`"1"`、`"1.0"`、`"1.0.0"` 在本仓库中等价。

**本节仓库中的对照表**（当前三文件一一对应）：

| `prompt_compare.py` | yaml 文件（仅便于人读） | yaml 内 `prompt_id` | yaml 内 `version` |
| --- | --- | --- | --- |
| `PROMPT_ID = "review.risk_review"` | （三个文件相同） | `review.risk_review` | — |
| `PROMPT_VERSIONS` 含 `"1.0.0"` | `risk_review_v1.yaml` | `review.risk_review` | `"1.0.0"` |
| 含 `"2.0.0"` | `risk_review_v2.yaml` | `review.risk_review` | `"2.0.0"` |
| 含 `"3.0.0"` | `risk_review_v3.yaml` | `review.risk_review` | `"3.0.0"` |

因此：

- 改 **`PROMPT_VERSIONS`** 时，改的是「要跑哪些 **yaml 里的 version 字段**」，不是改文件名。  
- 新增 v4：复制 yaml、把内部 `version` 改为 `"4.0.0"`，再把 `"4.0.0"` 加进 `PROMPT_VERSIONS`（文件名可叫 `risk_review_v4.yaml` 或任意合法名）。  
- **`PROMPT_VERSIONS` 可以是真子集**（如只写 `("2.0.0","3.0.0")`），不要求列全目录下所有版本。  
- 若 yaml 里没有匹配的 `(prompt_id, version)`，对比表会出现 **ERROR** 行。

**样例一览**（[`samples.json`](../../source/demos/02_first_chat/samples.json)）：

| id | 类型 | 适合练什么 |
| --- | --- | --- |
| S1 | 需求摘要 | 短 PRD 概括（非本节默认任务） |
| S2 | 风险识别 | **默认**；售后按钮 + 接口 v2 |
| S3 | 无材料 | 只有一句问题，看是否编造 |
| S4 | 约束输出 | 要求 JSON 列表（可配合 v3） |
| S5 | 长文本 | 较长 PRD，看 token 与是否漏段 |

**`evidence_s2.json` 格式**：

```json
{
  "sample_id": "S2",
  "evidence_block": "【Evidence · …】\n- 多条内部文档摘录…"
}
```

仅 `evidence_block` 字段会注入 Prompt 的 `{{evidence_block}}`；03_rag 课将改为真实检索结果。

**本脚本里不能直接改的项**：

| 想改什么 | 应去哪里改 |
| --- | --- |
| 用哪条模型 / `config_ref` | 各版 yaml 的 `model_config_ref`（默认 `chat.dev_chat`），或根目录 `.env` + `models.yaml` |
| Prompt 正文（constraints、example 等） | `llm_core/prompts/review/risk_review_v*.yaml` |
| API Key、base_url | 仓库根 `.env`（与 01 相同） |

**推荐实验顺序**（改配置 → 运行 → 记笔记）：

1. 默认跑一遍（S2 + 三版 + `evidence_s2.json` + `TEMPERATURE=0`）。  
2. `VERBOSE = True` 重跑，对照 v2 的 system/user 是否包含 Evidence / Constraints。  
3. `SAMPLE_ID = "S3"`，看 v1 与 v2 对无材料的差异。  
4. `EVIDENCE_FILE = DEMO_DIR / "not_exist.json"`（或任意不存在路径），看 v2/v3 是否弱化无依据风险。  
5. `PROMPT_VERSIONS = ("2.0.0", "3.0.0")` 只对比有约束的两版，节省时间。

### 实现步骤

1. **阅读三份 YAML**，标出 v1→v2→v3 各多了哪一段语义（constraints / evidence / example / JSON）。  
2. **打开 `prompt_compare.py` 顶部「实验配置」**，按上表确认或修改各常量。  
3. **配置 `.env`**（与 01 相同，`OPENAI_API_KEY`；DeepSeek 用户同步改 `OPENAI_MODEL` 等）。  
4. **运行对比**（见下）。  
5. **（可选）** `VERBOSE = True` 重跑。  
6. **（可选）** 按「推荐实验顺序」尝试 S3、无 evidence 文件等。

### 运行方式

```bash
# 仓库根目录
pip install -r requirements.txt
pip install -e .

cd source/demos/02_provider_switching
python prompt_compare.py
```

改实验：编辑 `prompt_compare.py` 顶部「实验配置」块（见上文 **`prompt_compare.py` 实验配置`** 表），**无需长命令行参数**。

### 预期结果

1. 终端先打印样例、prompt id、版本列表。  
2. 输出对比表三行（v1 / v2 / v3）：`model`、`latency_ms`、`total_tokens`、`content_preview`。  
3. 主观对比（建议记入笔记）：

| 对比项 | v1 | v2 | v3 |
| --- | --- | --- | --- |
| 是否出现未在 PRD/Evidence 出现的接口名 |  |  |  |
| 是否覆盖交互/状态/接口中至少 2 类 |  |  |  |
| 输出是否便于程序解析 |  |  |  |

4. `VERBOSE = True` 时，表后按版本打印 `format_call_log` 详情。

### 人工观察清单（代替本节自动化 eval）

- [ ] v2 比 v1 更少「凭空」接口/埋点/权限描述  
- [ ] v2 或 v3 会引用 `evidence_s2.json` 中的接口 v2、状态机表述  
- [ ] v3 输出更接近 JSON；尝试 `json.loads` 是否一次成功（失败也正常，记原因）  
- [ ] 三版 `prompt_tokens` 随 Prompt 变长而增加——体会 **Prompt 长度即成本**

---

## 完成标准

- **能解释**：六段式任务协议各段作用；Prompt 与 Schema、RAG evidence 的边界。  
- **能说明**：为何业务用 `prompt_id + version` 而不是在代码里改长字符串。  
- **能运行**：`python prompt_compare.py`，并读懂对比表。  
- **能改造**：复制 v2 为 v2.1（改一条 constraint），升 `version`，再对比输出。  
- **能判断**：至少 3 种 Prompt 失败模式及缓解思路。

### 运行与观察

```bash
cd source/demos/02_provider_switching
python prompt_compare.py
```

将 `VERBOSE` 改为 `True` 后重跑，应能在表后看到完整 messages 与 assistant 回复。实验配置逐项说明见正文 **「`prompt_compare.py` 实验配置」** 或 [demo README](../../source/demos/02_provider_switching/README.md#02prompt_comparepy-实验配置)。

### 自检题（不看正文能否答）

1. `requirement_text` 和 `evidence_block` 在真实产品里分别通常由谁提供？  
2. 为什么 v1 只有 role，往往比 v2 更容易编造？  
3. v3 在 Prompt 里要求 JSON 字段，和 03 的 Pydantic Schema 还有什么差别？  
4. 若只升 Prompt 版本而不固定 `temperature` 和样例，对比实验还有什么问题？  
5. 为什么本节把 Prompt 放在 YAML 而不是写在 `provider_switching.py` 里？  
6. `PROMPT_ID` / `PROMPT_VERSIONS` 与 `risk_review_v1.yaml` 文件名是什么关系？改版本对比时应改哪一侧？

---

## 本节沉淀

- 新增 `llm_core.prompts`（`get_prompt`、`render_prompt`、三份 `review.risk_review` YAML）与 demo `prompt_compare.py`。  
- 需求评审助手具备：**按任务版本渲染 messages、与 01 的 `LLMClient` 衔接**；风险审查可在固定样例上受控对比。  
- 下一节 [03_structured_outputs.md](03_structured_outputs.md) 将在 v3 的「JSON 意图」之上，落地 Schema、校验与 `structured_chat`。

---

## 相关专题

- 上一篇：[01_model_api_and_provider_abstraction.md](01_model_api_and_provider_abstraction.md)  
- 下一篇：[03_structured_outputs.md](03_structured_outputs.md)  
- 课程大纲：[outline.md](outline.md)
