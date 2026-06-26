# 03. Structured Outputs

> 用 Schema 建立模型与应用之间的数据契约，支撑需求评审助手 V1 的结构化报告、引用、拒答与后续 eval / Workflow。

---

## 真实问题

需求评审助手 V1 需要：

- 风险项进入数据库与前端卡片，而不是一段 Markdown。
- 每条结论能绑定 `source_id`，供 source panel 跳转。
- 证据不足时返回**拒答**或**追问**结构，而不是含糊自然语言。
- 多 Agent / Workflow 节点之间传递**结构化中间结果**（字段契约统一）。

若只依赖「请输出 JSON」：

- JSON 可解析但字段名漂移、类型错误、缺字段。
- 模型伪造 `source_id`，引用面板指向不存在文档。
- 前端、eval、LangGraph state 各写一套解析逻辑，无法回归。

---

## 基础原理

### 四种结构化手段对比

| 手段 | 做法 | 优点 | 缺点 | 本项目建议 |
| --- | --- | --- | --- | --- |
| **JSON 提示** | Prompt 里描述 JSON 格式 | 零依赖 | 不稳定、易多余文本 | 仅原型 |
| **JSON Mode** | API `response_format: json_object` | 保证是 JSON | 不保证 schema 字段 | 过渡方案 |
| **Structured Outputs** | API 绑定 JSON Schema / Pydantic | 字段级约束 | 依赖模型与平台能力 | **V1 首选**（`structured_chat`） |
| **后置 Pydantic 校验** | 任意文本 → extract JSON → validate | 通用 | 解析失败多一步 | 与上组合，必做 |

推荐链路：

```text
Prompt（02）+ Structured Outputs API
  → 原始 JSON 字符串
  → Pydantic model_validate
  → 应用层 citation / 业务规则校验
  → 入库 / 返回前端 / 写入 Workflow state
```

### Schema 设计原则

1. **扁平优先**：嵌套不超过 2 层；复杂报告用 `ReviewReport` 聚合子对象列表。
2. **枚举约束**：`risk level`、`category` 用 `Literal` 或 `Enum`，避免自由文本漂移。
3. **可选字段明确**：`Optional` + 文档说明何时可为空。
4. **引用对齐 RAG**：`Citation.source_id` 必须来自 context 中提供的 id 集合（应用侧 checker，`03_rag` 完善）。
5. **服务业务流程**：不为「schema 好看」增加用不到的字段。

---

## 核心 Schema 定义

以下为 **`llm_core.schemas` 唯一字段真源**；[02_prompt_engineering_for_apps.md](02_prompt_engineering_for_apps.md) 仅引用名称。

```python
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RiskCategory(str, Enum):
    INTERACTION = "interaction"       # 页面交互
    STATE_FLOW = "state_flow"           # 状态流转
    API_COMPAT = "api_compat"           # 接口兼容
    MULTI_PLATFORM = "multi_platform"   # 多端一致
    NETWORK_EXCEPTION = "network_exception"
    OBSERVABILITY = "observability"     # 埋点监控
    PERMISSION = "permission"           # 权限脱敏
    OTHER = "other"


class Citation(BaseModel):
    """单条引用，source_id 必须对应 RAG context 中的来源。"""

    source_id: str = Field(..., description="知识库片段 id，如 doc:prd-001#chunk-3")
    quote: str = Field(..., description="支持结论的原文摘录，宜短")
    doc_type: Optional[str] = Field(None, description="prd / api / rule / history_review 等")


class ReviewRisk(BaseModel):
    """单条风险项。"""

    level: RiskLevel
    category: RiskCategory
    description: str = Field(..., min_length=1)
    citations: list[Citation] = Field(default_factory=list)
    suggestion: Optional[str] = Field(None, description="可执行的改进建议")


class TechnicalImpact(BaseModel):
    """技术影响点。"""

    area: str = Field(..., description="如 api / data / dependency / performance")
    description: str
    citations: list[Citation] = Field(default_factory=list)


class TestPoint(BaseModel):
    """测试验收点。"""

    title: str
    steps: str = Field(..., description="可执行步骤或检查点")
    citations: list[Citation] = Field(default_factory=list)


class ClarificationQuestion(BaseModel):
    """证据不足时的追问。"""

    question: str
    reason: str = Field(..., description="为何需要该信息")
    blocking: bool = Field(
        False, description="是否阻塞评审结论"
    )


class RefusalResponse(BaseModel):
    """拒答或建议人工介入。"""

    refused: bool = True
    reason: str
    suggested_action: Literal["provide_more_docs", "human_review", "retry_later"]


class ReviewReport(BaseModel):
    """V1 结构化评审报告（聚合）。"""

    summary: str = Field(..., description="需求摘要")
    risks: list[ReviewRisk] = Field(default_factory=list)
    impacts: list[TechnicalImpact] = Field(default_factory=list)
    test_points: list[TestPoint] = Field(default_factory=list)
    clarifications: list[ClarificationQuestion] = Field(default_factory=list)
    citations: list[Citation] = Field(
        default_factory=list,
        description="报告级引用索引，可与各子项 citations 去重合并",
    )
    recommendation: str = Field(
        ..., description="总体建议：proceed / proceed_with_caution / needs_revision / insufficient_evidence"
    )
```

### Schema 用途速查

| Schema | 用途 | 典型产出阶段 |
| --- | --- | --- |
| `Citation` | 单条引用 | 所有带依据的结论 |
| `ReviewRisk` | 风险项 | `review.risk_review` prompt |
| `ClarificationQuestion` | 追问 | `review.clarification` |
| `ReviewReport` | 完整报告 | V1 报告页 / `review.report_synthesis` |
| `RefusalResponse` | 拒答 | 无 evidence 时 |

---

## 最小实现

### 调用与校验

```python
from pydantic import ValidationError

# 1. LLMClient + structured_chat + response_format（平台支持时绑定 ReviewRisk[] schema）
resp = client.chat(messages, config_ref="chat.structured_chat", response_schema=ReviewRiskList)

# 2. 本地校验
try:
    risks = [ReviewRisk.model_validate(item) for item in parse_json_array(resp.content)]
except ValidationError as e:
    record_failure("validation_error", e)

# 3. 引用存在性（简化版；完整 checker 在 03_rag）
valid_ids = set(context.source_ids)
for risk in risks:
    for c in risk.citations:
        if c.source_id not in valid_ids:
            record_failure("hallucinated_citation", c.source_id)
```

### 与 risk_review prompt 联调流程

```text
1. RAG 返回 evidence_block（含 source_id 列表）
2. render_prompt("review.risk_review", {requirement_text, evidence_block})
3. LLMClient → structured output
4. Pydantic validate → ReviewRisk[]
5. citation checker → 通过则返回 API / 否则拒答或降级
```

Demo 路径：`source/02_llm/demos/structured_review_output/`。

### 解析失败类型

| 代码 | 含义 | 处理建议 |
| --- | --- | --- |
| `parse_error` | 非 JSON 或 JSON 语法错误 | 重试 1 次；换 structured_chat；记录样本 |
| `validation_error` | JSON 可解析但 Pydantic 失败 | 看缺失字段；简化 schema 或加强 prompt |
| `hallucinated_citation` | source_id 不在 context | 剔除该条或整批拒答；bad case 回流 |
| `empty_required_content` | 必填语义字段为空字符串 | prompt 约束 + eval |

---

## 主流框架实现

| 方式 | 说明 |
| --- | --- |
| OpenAI Structured Outputs | `response_format` + JSON Schema；优先用于 `structured_chat` |
| Pydantic v2 | `model_validate` / `model_json_schema()` 生成 API schema |
| LangChain `PydanticOutputParser` | 可在 RAG 链中使用，schema 真源仍在本 package |

---

## 失败分析与能力边界

### 常见误区

- **JSON 可解析 = 内容正确**：仍须 citation checker 与人工 spot check。
- **Schema 过深**：嵌套过深降低生成成功率；优先多个 flat 模型再组装。
- **伪造引用**：模型会编造 plausible 的 `source_id`；必须应用侧校验。
- **拒答与空列表混淆**：「无风险」≠「证据不足」；用 `RefusalResponse` 或 `recommendation=insufficient_evidence` 区分。

### 边界

- **Citation 正确性 eval**（引用是否支持结论）在 `03_rag/12`、`05_eval/03`。
- **前端渲染** ReviewReport 卡片在 `06_ai_native/04`。
- **Workflow 节点间传递** 使用同一 schema，见 `04_agent/05`。

---

## 评估观测

| 指标 | 定义 |
| --- | --- |
| `schema_success_rate` | 调用中 Pydantic 一次通过的比例 |
| `field_missing_rate` | 必填字段缺失或空的比例（validation 报错分类） |
| `citation_missing_rate` | 有风险但 citations 为空的比例 |
| `hallucinated_citation_rate` | source_id 不在 context 的比例 |

失败样本写入 harness（专题 07），并进入 V2 bad case 板（`07_projects/07`）。

---

## 小项目实战

输出一次**结构化需求评审结果**（样例结构，非真实 API）：

```json
{
  "summary": "用户可在订单详情页发起售后申请，需对接售后接口 v2。",
  "risks": [
    {
      "level": "high",
      "category": "state_flow",
      "description": "未定义售后申请失败后的订单状态回退规则。",
      "citations": [
        {
          "source_id": "doc:prd-order#chunk-12",
          "quote": "用户提交售后申请后进入审核中状态",
          "doc_type": "prd"
        }
      ],
      "suggestion": "补充失败/撤销时的状态机与 UI 回退说明。"
    }
  ],
  "impacts": [],
  "test_points": [
    {
      "title": "售后申请成功路径",
      "steps": "提交申请 → 订单状态变为审核中 → 展示进度页",
      "citations": []
    }
  ],
  "clarifications": [
    {
      "question": "售后接口 v2 是否已全量上线？",
      "reason": "PRD 提到 v2 但未给出切换时间",
      "blocking": true
    }
  ],
  "citations": [],
  "recommendation": "proceed_with_caution"
}
```

---

## 项目收敛

写入 `llm_core`：

```text
llm_core/schemas/
├── review.py      # 上文全部模型
├── refusal.py     # RefusalResponse（或合并在 review.py）
└── __init__.py

llm_core/parsing.py
├── parse_structured(content, model: type[BaseModel]) -> T
├── ParseErrorCode 枚举
└── validate_citations(model, valid_source_ids: set[str]) -> list[ParseError]
```

与项目版本：

- **V1** [07_projects/06](../07_projects/outline.md)：Sources / Refusal / Structured Review 依赖本篇 schema。

---

## 完成标准

- 能解释：`Citation`、`ReviewRisk`、`ReviewReport`、`RefusalResponse` 各字段的业务含义。
- 能对比：JSON 提示、JSON Mode、Structured Outputs、Pydantic 校验的适用边界。
- 能设计：一版 `ReviewReport` 并说明与 RAG `source_id` 如何对齐。
- 能列举：`parse_error`、`validation_error`、`hallucinated_citation` 三种失败及处理策略。
- 能描述：`schema_success_rate` 与 `hallucinated_citation_rate` 如何进入 harness 回归。

---

## 相关专题

- 上一篇：[02_prompt_engineering_for_apps.md](02_prompt_engineering_for_apps.md)
- 下一篇：[04_streaming_and_conversation.md](04_streaming_and_conversation.md)（outline 专题 04，文档待编写）
- 模型能力要求：[01_model_api_and_provider_abstraction.md](01_model_api_and_provider_abstraction.md)（`structured_chat`）
- V1 项目收敛：[07_projects/06](../07_projects/outline.md)
- Citation eval：[03_rag/outline.md](../03_rag/outline.md) 专题 12、[05_eval_observability/outline.md](../05_eval_observability/outline.md) 专题 03
