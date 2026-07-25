# AI Agent 协作指南

这份文档规定 AI Agent 在本仓库中如何选择真源、判断任务、执行修改和避免越界。

它不重复课程写作模板、代码组织细节或企业平台能力清单。对应规则应读取各自真源。

## 1. 真源优先级

AI Agent 按以下顺序处理约束：

1. 用户当前明确提出的目标、范围和规则。
2. 根目录 `AGENTS.md`。
3. [strategy.md](strategy.md)：长期目标、两个阶段和 V0–V6。
4. [learning-guide.md](learning-guide.md)：课程、文档、代码、运行和真实模型规则。
5. [ai-coding-mastery.md](ai-coding-mastery.md)：掌握标准和代码所有权。
6. 当前项目篇、概念篇、机制篇和代码 README。
7. [ai-application-platform.md](ai-application-platform.md)：远期能力参考。

远期平台地图不能覆盖当前项目阶段和用户明确范围。

## 2. 工作前读取

处理本仓库任务前优先阅读：

1. 根 `README.md`。
2. 根 `AGENTS.md`。
3. `docs/strategy.md`。
4. `docs/learning-guide.md`。
5. 与当前任务对应的专题文档和代码 README。

涉及代码编写、代码审查或掌握判断时，另读：

- `docs/ai-coding-mastery.md`。

编写或重写 `course/**/*.md` 正文时，另读：

- `skills/course-writing/SKILL.md`。

评估新增知识、技术或功能进入概念篇、机制篇、项目篇还是仅保留未来认知时，使用
[learning-guide.md](learning-guide.md)「知识与功能的分级准入」；其他文档只引用该标准，不复制一套准入规则。

评估平台型能力是否进入项目时，另读：

- `docs/ai-application-platform.md`。

默认不读取 `archive/`。只有用户明确要求参考历史内容时才可以进入。

## 3. 任务分类与真源

| 任务 | 首要真源 | 重点判断 |
| --- | --- | --- |
| 调整职业定位或长期目标 | `strategy.md` | 是否改变唯一主项目或两个阶段 |
| 调整学习方式或目录规则 | `learning-guide.md` | 是否引入第二套顺序或重复真源 |
| 编写概念篇 | `learning-guide.md` + course-writing skill | 是否讲清定义、区别和边界 |
| 编写机制篇 | `learning-guide.md` + course-writing skill | 是否讲清数据流、实验和失败 |
| 编写项目篇 | `strategy.md` + `learning-guide.md` | 是否服务当前 V0–V6 版本 |
| 实现代码 | `learning-guide.md` + `ai-coding-mastery.md` | 入口、真实调用、验证和所有权 |
| 代码审查 | `ai-coding-mastery.md` | 数据流、状态流、异常流和回归风险 |
| 设计平台能力 | `ai-application-platform.md` | 当前是否真的需要，边界是否过重 |

## 4. 处理文档任务

### 先找唯一真源

修改前先判断内容属于：

- 长期目标。
- 学习规范。
- 掌握标准。
- 远期平台能力。
- Agent 执行规则。
- 课程正文。
- 产品运行说明。

同一规则只在一个真源中详细维护，其他位置只保留必要链接。

### 避免过程文档

不要在长期文档中写：

- 当前迁移到了哪一步。
- 旧结构如何逐步废弃。
- 临时争论记录。
- 当前学习进度。
- 待办式重构计划。

长期文档只描述目标态和稳定规则。

### 避免机械套模板

“真实问题 → 原理 → 最小实现 → 框架 → 失败边界”是通用认知方法，不是所有正文的固定目录。

AI Agent 必须先识别当前文档是概念篇、机制篇还是项目篇，再执行对应规范。

### 文档不驱动无意义代码

- 概念篇通常可以没有代码。
- 机制篇只有在需要观察机制时才增加实验或实现。
- 项目篇组合已有能力，并按真实业务需要扩展。
- 不为每篇正文创建 package、demo 或 app。

## 5. 处理项目任务

需求评审助手只有一个产品真源，但有两个不同职责的项目相关目录：

```text
course/project/       项目篇教材
review_assistant/     可运行产品
```

AI Agent 必须遵守：

- 项目学习目标、设计题、失败题和版本验收写入 `course/project/`。
- 产品代码、测试、配置、API、安装和部署写入 `review_assistant/`。
- 通用能力实现写入 `source/packages/`。
- 机制实验写入 `source/demos/`。
- 项目篇引用产品入口，不复制产品 README。
- 产品 README 标明运行事实，不复制课程原理。

V0–V6 是唯一项目版本顺序。不得增加 M0–M6 或另一套同义里程碑。

## 6. 处理代码任务

### 代码组织

- 每个能力域只有一个 package 实例。
- demo、app 和产品通过 import 复用 package。
- 不为课程目录、文档类型或项目版本 copy 平行实现。
- 不预建空 package、空 demo、空 app、空产品目录或 `.gitkeep`。
- 新能力优先扩展已有职责边界清晰的 package。

### 真实调用

- LLM、RAG、Agent 和 Eval 主路径使用真实模型或真实服务。
- 缺少 key、鉴权失败、限流、超时和模型不支持必须清晰暴露。
- 不静默 fallback 到 fake 或 mock。
- Mock 只用于测试、离线排查、稳定故障复现或明确对照。

### 运行与验证

实现后至少确认：

- 真实入口是什么。
- 运行命令是什么。
- 需要哪些配置和服务。
- 输出在哪里观察。
- 失败信息是否可理解。
- 相关测试或评估是否通过。
- README 是否与真实代码一致。

### 代码所有权

AI Agent 不只交付生成结果，还应帮助用户理解：

- 为什么这样设计。
- 数据、状态和异常如何流动。
- 需求变化时改哪里。
- 如何主动制造失败。
- 如何通过测试、评估或 trace 验证修改。

实现 Agent、Tool、Workflow 或 Multi-Agent 时，必须先按
[learning-guide.md](learning-guide.md)「Agent、Workflow 与 Multi-Agent 工程规则」
检查结构选择、模型与应用控制边界、Tool 契约、停止条件、状态恢复、评估和人工确认。

## 7. 平台能力采用边界

参考 RAGFlow、MaxKB 或其他平台时，优先吸收：

- 领域对象边界。
- 主业务链路。
- 状态、任务和失败模型。
- 可观察与可评估设计。
- 简单应用向 Workflow 演进的方式。

不要默认复制：

- 完整多租户。
- 通用低代码画布。
- 连接器或工具市场。
- 企业权限中台。
- 大规模任务和部署体系。

任何平台能力进入当前项目，必须能说明当前版本的真实问题、最小实现、验证方式和明确非目标。

## 8. 禁止行为

- 建立第二套学习或项目顺序。
- 将 LLM、RAG、Agent 重新割裂为必须顺序毕业的课程。
- 重复维护多个与知识地图或标准学习路径竞争的完整课程规划。
- 机械执行“一篇文档对应一次代码变更”。
- 用伪代码冒充已实现项目能力。
- 用 Mock 结果冒充真实模型效果。
- 在真实调用失败后静默降级。
- 为展示复杂度提前引入 Multi-Agent 或平台基础设施。
- 在 `review_assistant/` 和 `source/apps/` 维护两份产品。
- 在 `course/project/` 和产品 README 重复维护运行手册。
- 主动扩展 `archive/`。
- 未经用户要求主动创建 Git commit。

## 9. 交付说明

完成任务后，AI Agent 应说明：

- 实际修改了什么。
- 哪些真源受到影响。
- 如何运行和验证。
- 测试或检查结果。
- 仍然存在的边界或未完成项。

输出先给结论，再给必要结构和细节，避免把工具执行过程当作主要交付内容。
