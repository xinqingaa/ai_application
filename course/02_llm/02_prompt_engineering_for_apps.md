# 02. 面向应用的 Prompt Engineering

> 把 Prompt 当作需求评审助手与模型之间的**任务协议**：可版本化、可回归、可与 Schema 和 RAG 证据分工协作。

---

## 真实问题

需求评审不是单一任务。同一套「你是助手」无法稳定覆盖：

- **需求理解**：从 PRD 提取目标、范围、假设。
- **风险审查**：按交互、状态、接口、多端等维度找风险。
- **技术影响**：接口变更、数据、依赖系统。
- **测试验收**：可执行的验收点。
- **缺失信息追问**：证据不足时问什么。
- **报告汇总**：多段结论合并为一份结构化报告。

若每个场景共用一段长 prompt：

- 约束互相冲突，输出字段不稳定。
- 无法针对单任务做回归（改风险 prompt 却影响摘要）。
- 无法与 `ReviewReport` 等 schema 对齐（字段定义见 [03_structured_outputs.md](03_structured_outputs.md)）。

Prompt **不能**替代：检索证据、权限、Tool 执行、完整 eval——无依据时不能靠 prompt 硬答。

---

## 基础原理

### 六段式任务协议

每个命名 Prompt 建议包含六段（顺序可调，但语义齐全）：

| 段落 | 作用 | 需求评审示例 |
| --- | --- | --- |
| **role** | 角色与专业边界 | 「你是研发团队的需求评审助手，专注发现风险与缺失信息。」 |
| **task** | 当前一步要完成的任务 | 「根据给定 PRD 片段，识别与前端交互相关的风险。」 |
| **context** | 输入材料占位 | `{requirement_text}`、`{evidence_block}` |
| **constraints** | 必须遵守的规则 | 「仅基于 context 中的材料；无依据不得断言。」 |
| **examples** | 可选 few-shot | 1–2 个风险项示例（慎用，见失败分析） |
| **output_format** | 输出形态 | 「按 ReviewRisk 列表 JSON 输出」（schema 名引用 03） |

### Prompt 与 Schema 的分工

- **Prompt**：告诉模型「做什么、依据什么、禁止什么」。
- **Schema**：告诉应用「字段叫什么、类型是什么、如何校验」。
- 二者通过 `output_format` 衔接；**字段真源在 03**，本篇只引用 schema 名称。

### Prompt 与 RAG 证据的分工

- RAG 负责把**企业知识**放进 `{evidence_block}`（带 source_id）。
- Prompt 负责要求：**结论必须绑定 citations**，无证据时拒答或追问。
- 生成阶段完整链路见 `03_rag/11`；本篇只定义 generation prompt 如何引用 `{evidence_block}`。

### 变量与模板

常用变量：

| 变量 | 来源 |
| --- | --- |
| `{requirement_text}` | 用户提交的 PRD / 需求描述 |
| `{evidence_block}` | RAG context builder 格式化后的检索片段 |
| `{review_dimensions}` | 可选，评审维度标签 |
| `{previous_summary}` | 多步 workflow 上游节点摘要 |

模板文件建议组织：

```text
llm_core/prompts/review/
├── requirement_summary/v1.yaml
├── risk_review/v1.yaml
├── technical_impact/v1.yaml
├── test_acceptance/v1.yaml
├── clarification/v1.yaml
└── report_synthesis/v1.yaml
```

### 版本管理

每个 Prompt 记录：

```yaml
prompt_id: review.risk_review
version: "1.0.0"
hash: "<content hash>"   # 内容变更则变
model_config_ref: chat.structured_chat
```

Harness 样例绑定 `prompt_id + version`，对比改动前后指标。

### 多 Agent 前置（认知）

未来 Multi-Agent 每个角色一份独立 prompt，必须写清：

- **职责**：只做什么。
- **禁止越界**：不汇总、不调工具、不替代其他角色（详 `04_agent`）。

---

## 最小实现

### 实验：同一任务三版 Prompt

任务：**风险审查**（给定一段 PRD + 可选 evidence_block）。

| 版本 | 差异 |
| --- | --- |
| v1 | 只有 role + task，无 constraints |
| v2 | 增加 constraints + output_format（ReviewRisk） |
| v3 | v2 + 1 个 few-shot 示例 |

对同一输入跑 3 次（`temperature=0`，`structured_chat`），人工或 checklist 对比：

- 字段是否齐全（level、category、description、citations）。
- 是否出现无依据风险。
- 是否误报 / 漏报（对照 [07_projects 评审维度](../07_projects/outline.md)）。

### 模板结构示例（risk_review v1.yaml）

```yaml
prompt_id: review.risk_review
version: "1.0.0"
model_config_ref: chat.structured_chat

system: |
  {{ role }}

user: |
  ## Task
  {{ task }}

  ## Requirement
  {{ requirement_text }}

  ## Evidence
  {{ evidence_block }}

  ## Constraints
  {{ constraints }}

  ## Output
  输出 ReviewRisk 对象数组，JSON 格式。每条风险必须包含 citations（source_id 来自 Evidence）。

sections:
  role: |
    你是需求评审助手，负责从研发视角识别 PRD 中的风险，尤其关注页面交互、状态流转、接口兼容、多端一致性与异常场景。
  task: |
    识别与给定需求相关的风险项，按 category 分类，标注 level（high/medium/low）。
  constraints: |
    - 仅基于 Requirement 与 Evidence 中的内容，不得编造。
    - Evidence 为空或不足以支持结论时，不要输出该风险；改为在输出中说明需追问（见 clarification 流程）。
    - 每条风险至少一条 citation，source_id 必须来自 Evidence。
```

Registry 加载：`get_prompt("review.risk_review", version="1.0.0")` → 渲染变量 → 交给 `LLMClient`。

---

## 主流框架实现

| 方式 | 本项目用法 |
| --- | --- |
| 字符串模板 + `.format` / Jinja2 轻量 | `llm_core.prompts` 默认 |
| LangChain `ChatPromptTemplate` | `03_rag` 链内可包装同一 yaml 真源 |
| Few-shot `ExampleSelector` | 仅高风险任务少量使用，需 eval 验证 |

不在本课系统学习 LangChain Prompt 全家桶；重点是**任务协议可维护**。

---

## 失败分析与能力边界

| 失败 | 原因 | 缓解 |
| --- | --- | --- |
| 约束冲突 | 「尽量简短」与「列全所有风险」同时出现 | 单任务单目标，删冲突句 |
| Few-shot 污染 | 示例含过时业务规则 | 示例进版本管理；bad case 驱动更新 |
| Prompt 过长 | 塞入全文 PRD + 全库 evidence | context 工程（专题 05）；RAG 压缩 |
| 无证据强答 | 只有 prompt 没有检索 | 必须接 RAG；prompt 写拒答规则 |
| 字段漂移 | output_format 与 schema 不一致 | schema 真源在 03；改 schema 同步改 prompt |

Prompt 不能替代：ACL、Tool 权限、citation 存在性校验（应用侧 checker）。

---

## 评估观测

### Prompt 回归样例表（最小字段）

| 字段 | 说明 |
| --- | --- |
| `sample_id` | 样例 id |
| `prompt_id` / `prompt_version` | 绑定版本 |
| `input` | requirement_text + evidence_block 快照 |
| `expected` | 可选：期望风险 category、是否应拒答 |
| `output` | 模型原始或解析后结果 |
| `failure_type` | `missing_field` / `hallucination` / `wrong_refusal` / … |

### 指标（配合 03 schema 校验）

- **字段缺失率**：必填 schema 字段为空的比例。
- **拒答正确率**：该拒答时是否拒答（需标注样本）。
- **人工可用性**：输出是否可直接用于评审会议（抽样 1–5 分）。

Prompt 变更必须：**升 version → 跑回归样例 → 记录 diff**。

---

## 小项目实战

定义需求评审助手 **Prompt 集**（六份命名模板）。下表为每份 prompt 的协议说明；完整 yaml 在实现阶段放入 `llm_core/prompts/`。

| prompt_id | 适用场景 | 主要输入变量 | output_format（schema 见 03） | 拒答/追问规则 |
| --- | --- | --- | --- | --- |
| `review.requirement_summary` | 评审入口，压缩材料 | `requirement_text` | 短摘要 JSON 或 `ReviewReport.summary` 字段 | 材料为空则拒答 |
| `review.risk_review` | 风险识别 | `requirement_text`, `evidence_block`, `review_dimensions` | `ReviewRisk[]` | 无 evidence 支持的风险不得输出 |
| `review.technical_impact` | 接口/数据影响 | `requirement_text`, `evidence_block` | 结构化 impact 列表（可进 `ReviewReport.impacts`） | 无接口文档证据时标注「需补充」 |
| `review.test_acceptance` | 测试验收点 | `requirement_text`, `evidence_block` | `test_points[]` | 不可执行臆测 case |
| `review.clarification` | 证据不足 | `requirement_text`, `evidence_block` | `ClarificationQuestion[]` | 列出 blocking 问题 |
| `review.report_synthesis` | 汇总报告 | 上游结构化摘要字段 | `ReviewReport` | 不得新增无 citation 的风险 |

### 与评审维度矩阵对齐

`risk_review` 的 constraints 应显式覆盖 [07_projects/03](../07_projects/outline.md) 中的维度，例如：

- 页面交互风险（空态、加载态、回退）
- 状态流转与并发编辑
- 接口兼容与版本
- 多端一致性（Flutter / H5 / Native）
- 异常 / 弱网 / 长连接
- 埋点与监控、权限与脱敏

维度作为 checklist 写入 constraints，而非指望模型「自己想到」。

---

## 项目收敛

### `llm_core.prompts` API（设计）

```python
def get_prompt(prompt_id: str, version: str | None = "latest") -> PromptTemplate: ...

def render_prompt(template: PromptTemplate, variables: dict[str, str]) -> list[dict]: ...
    # 返回 OpenAI messages 格式
```

### 与 LLMClient 组合（伪代码）

```python
tpl = get_prompt("review.risk_review", version="1.0.0")
messages = render_prompt(tpl, {
    "requirement_text": prd,
    "evidence_block": context_builder.format(sources),
})
resp = client.chat(messages, config_ref=tpl.model_config_ref)
# 03：parse_structured(resp.content, ReviewRisk, ...)
```

---

## 完成标准

- 能解释：Prompt 六段式结构及每段在需求评审中的作用。
- 能说明：Prompt 与 Schema、RAG evidence 的分工边界。
- 能为「风险审查」编写一版含 constraints 与 output_format（引用 ReviewRisk）的 prompt 模板。
- 能描述：`prompt_id + version + hash` 如何与 harness 回归样例绑定。
- 能列举：至少 3 种 prompt 失败模式及对应缓解方式。

---

## 相关专题

- 上一篇：[01_model_api_and_provider_abstraction.md](01_model_api_and_provider_abstraction.md)
- 下一篇：[03_structured_outputs.md](03_structured_outputs.md)（Schema 字段真源）
- RAG 生成与 evidence：[03_rag/outline.md](../03_rag/outline.md) 专题 11
- 评审维度矩阵：[07_projects/03](../07_projects/outline.md)
