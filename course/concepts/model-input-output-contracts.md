# 模型输入输出契约：Prompt、Schema 与 Context

> 概念篇：建立一条统一主线，理解应用如何把“希望模型完成什么、允许模型依据什么、程序最终接受什么”变成可验证契约。
>
> 阅读顺序见[标准学习路径](../learning-path.md)。必要前置是 [LLM 在 AI 应用中的位置与边界](llm-in-ai-applications.md)；本文交付 Prompt、Context 与 Schema 的统一契约心智。

---

## 为什么需要模型契约

传统函数通常有明确签名：

```text
输入类型
→ 确定性处理
→ 输出类型或异常
```

模型调用不同。应用传入自然语言和材料，模型生成概率性结果。即使 HTTP 请求成功，也可能出现：

- 模型理解错任务。
- 输出内容缺字段。
- 使用了不应该使用的材料。
- 引用了不存在的来源。
- JSON 合法，但业务枚举非法。
- 结果对人可读，但程序无法消费。

因此，AI 应用不能把一次模型调用理解成“发送字符串、收到字符串”。更准确的模型是：

```text
Prompt：模型要完成什么任务
Context：模型本次可以依据什么材料
Schema：应用最终接受什么结果
本地校验：这次输出是否真的满足契约
```

这四层共同构成模型输入输出契约。

## 一个需求评审例子

用户提交：

> 订单详情页增加“申请售后”入口，对接售后接口 v2。

如果只发送：

> 帮我评审一下。

模型可能返回一段看似合理的建议，但应用不知道：

- 应该从哪些维度评审。
- 是否允许模型使用常识补充。
- 结果应该显示为 Markdown 还是风险卡片。
- 风险等级允许哪些值。
- 哪条结论来自哪份资料。
- 证据不足时应该猜测还是追问。

加入契约后，调用会变成：

```text
Prompt
  识别接口、状态机、多端一致性和验收风险

Context
  当前 PRD
  订单状态规则
  售后接口 v2 文档
  客户端展示规则

Schema
  risks[]
    category
    severity
    description
    suggestion
    source_ids[]
  missing_information[]

本地校验
  JSON 是否可解析
  字段和枚举是否合法
  source_id 是否存在
```

这并不能让模型变成确定性程序，但能让不确定性进入应用可观察、可拒绝和可回归的边界。

## 同一份需求怎样穿过四层契约

继续使用“申请售后入口”需求。应用收到的原始输入只有：

```text
订单详情页增加“申请售后”入口，对接售后接口 v2。
```

### 第一步：Prompt 把开放问题收敛成任务

应用不是要求模型“随便评审”，而是明确：

```text
任务
  从状态约束、接口失败、多端一致性和验收标准四个维度识别风险

约束
  不得补充材料中不存在的接口
  证据不足时进入 missing_information

输出意图
  产生风险项，而不是长篇会议纪要
```

这一步改变的是模型要做什么，但还没有给它业务依据。

### 第二步：Context 决定本轮看见什么

假设知识系统找到三份候选材料：

```text
订单状态规则
  已完成、已发货订单允许申请售后

售后接口 v2
  请求必须携带 order_id 和 item_id

客户端展示规则
  入口由服务端 can_apply_after_sale 字段控制
```

Context Builder 还可能拿到一份两年前的历史评审。应用必须决定：

- 当前 PRD 是任务主体。
- 三份现行规则可以作为证据。
- 旧评审只能作为历史参考，不能成为 Citation。
- 超出预算时优先保留接口约束和状态规则。

这一步改变的是模型本轮可以依据什么。

### 第三步：Schema 定义程序接受什么

模型不能只返回“建议关注状态判断”。应用需要的结果可能是：

```text
ReviewReport
  summary
  risks[]
    category
    severity
    description
    suggestion
    source_ids[]
  missing_information[]
```

Schema 会拒绝缺少必填字段、严重程度枚举非法或根对象错误的结果。

### 第四步：本地校验判断内容能否继续流转

即使模型返回：

```json
{
  "risks": [
    {
      "category": "api",
      "severity": "high",
      "description": "接口需要 user_id",
      "suggestion": "补充 user_id",
      "source_ids": ["API-AFTER-SALE-V3"]
    }
  ]
}
```

这段 JSON 可能通过基础 Schema，却仍然不能进入评审报告：

- 当前资料写的是 `order_id` 和 `item_id`，没有 `user_id`。
- 本次候选来源中不存在 `API-AFTER-SALE-V3`。
- 模型把不存在的事实包装成了结构正确的结果。

因此还需要业务校验：

```text
source_ids 是否属于本轮 citation candidates
→ 风险描述中的关键事实能否在证据中找到
→ 证据不足时是否应该降级为待确认问题
```

这条完整链路说明了四层契约的分工：

```text
Prompt 收敛任务
→ Context 收敛依据
→ Schema 收敛形状
→ 本地校验收敛业务可接受性
```

## Prompt：任务协议

Prompt 主要回答：

- 模型扮演什么角色。
- 当前任务是什么。
- 需要遵守哪些业务规则。
- 应优先关注哪些维度。
- 证据不足时应该怎样表现。
- 输出应符合什么高层要求。

Prompt 不是 Schema 的替代品。

例如 Prompt 写“风险等级只能是 high、medium、low”，模型仍可能生成 `critical`。自然语言要求能提高遵守概率，但应用不能只靠模型自觉保证字段合法。

Prompt 也不是 Context。把所有业务文档塞进 system prompt，会让任务规则、业务材料、历史状态和证据混在一起，难以版本化和排查。

## Context：证据边界

Context 回答：

- 这次调用让模型看见哪些材料。
- 哪些材料是当前任务。
- 哪些材料可以作为证据。
- 哪些只是历史参考或中间结论。
- 材料以什么顺序进入。
- 超出 Token 预算时保留和丢弃什么。

模型没有自动连接业务数据库或知识库。它只看当前请求里的输入。因此：

```text
资料存在于系统
≠
资料已经被检索
≠
资料已经进入 Context
≠
模型一定正确使用资料
```

Context Engineering 负责输入装配和诊断，RAG 负责从外部知识中生产候选材料。两者相连但不是同一机制。

## Schema：结果契约

Schema 回答：

- 根对象是什么。
- 有哪些字段。
- 字段类型和必填关系是什么。
- 枚举允许哪些值。
- 嵌套对象如何组织。
- 哪些结果业务可以继续消费。

从弱到强可以经历：

```text
自由文本
→ Prompt 要求 JSON
→ JSON Mode
→ JSON Schema 生成约束
→ Pydantic 本地校验
→ 业务规则与来源校验
```

每层解决的问题不同：

- Prompt 主要描述意图。
- JSON Mode 主要保证输出更像合法 JSON。
- JSON Schema 尝试约束生成结构。
- Pydantic 在应用侧验证类型和字段。
- 业务校验检查来源、权限和真实业务规则。

即使供应商支持 Structured Output，本地校验仍然不能省略。供应商能力差异、截断、降级模型和业务规则都可能让返回结果无法使用。

## 三者如何分工

| 问题 | 主要负责者 |
| --- | --- |
| 模型要做什么 | Prompt |
| 本次允许依据什么 | Context |
| 应用接受什么结构 | Schema |
| 输出是否真的可用 | 本地校验 |
| 来源是否真实存在 | Evidence / Citation 校验 |
| 失败后重试、降级还是终止 | 应用可靠性层 |

一个常见错误是把所有约束都塞进 Prompt。Prompt 会变得越来越长，但应用仍无法可靠判断成功与失败。

另一个错误是只设计 Schema，不解释字段语义。模型可能生成结构完全合法、内容却空泛的结果。Schema 约束形状，不自动保证业务质量。

## 输入契约与输出契约不是对称的

输出可以通过 Schema 做较强校验，输入 Context 却常常包含长文本、检索结果和历史状态，质量更难用单一 Schema 保证。

因此输入侧还需要：

- 来源标识。
- 文档类型。
- 版本和更新时间。
- 权限与可见范围。
- 排序和 Token 预算。
- 纳入或丢弃原因。

输出侧则需要：

- 解析阶段。
- Schema 校验结果。
- 业务校验结果。
- 原始输出保留边界。
- 可展示错误。

这也是为什么 AI 应用不能只关注 Prompt Engineering。很多失败其实发生在 Context 选择、Schema 设计或本地消费阶段。

## 契约不能解决什么

完整契约仍不能保证：

- 检索一定找到正确证据。
- 模型一定理解复杂业务。
- 每项风险都完整。
- Citation 一定真实。
- 相同输入得到完全相同结果。
- 多步骤 Agent 一定作出正确决策。

这些问题需要 RAG Evaluation、Citation 校验、Agent 轨迹评估和人工审核继续约束。

## 在需求评审助手中的位置

模型契约从第一阶段就进入项目，并在第二阶段扩展：

- 第一阶段使用 Prompt、Context 和 Structured Output 建立固定 RAG 输出，并增加 Citation、Refusal、证据充分性和固定样例对照。
- 第二阶段让单 Agent 在契约内选择知识源、补检索或追问，再把契约扩展到 Tool、State、Workflow Node 和多个 Agent 之间。

后续 Agent 系统中的 Tool Schema、Workflow State 和 Agent 输出契约，本质上都是同一种工程思想：模型参与判断，但应用必须定义可校验边界。

## 判断是否真正理解

你应该能够回答：

- Prompt、Context 和 Schema 分别控制什么？
- 为什么 Prompt 要求 JSON 仍然不能直接给前端使用？
- 为什么资料进入知识库不等于进入模型 Context？
- JSON Schema 与 Pydantic 本地校验有什么区别？
- 如果模型返回合法结构但引用不存在，应修改哪一层？
- Agent 调用 Tool 时，这套契约思想如何继续使用？

这些契约分别会在不同机制篇中展开，它们是相关知识入口，不代表阅读顺序：

- [Prompt Engineering](../mechanisms/prompt-engineering.md)
- [Structured Output](../mechanisms/structured-output.md)
- [Context Engineering](../mechanisms/context-engineering.md)

完成后回到 [标准学习路径](../learning-path.md)。
