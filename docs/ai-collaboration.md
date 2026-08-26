# AI 协作指南

本文只规定 AI Agent 怎样选择真源和避免越界，不重复课程写作或工程规范。

## 真源顺序

1. 用户当前明确目标。
2. 根 `AGENTS.md`。
3. `SPEC.md`、`PLAN.md` 与 `docs/strategy.md`。
4. `docs/learning-guide.md` 和任务对应的课程、代码 README。
5. `docs/ai-coding-mastery.md` 与远期平台参考。

## 任务路由

| 任务 | 首要真源 |
| --- | --- |
| 产品范围或行为 | `SPEC.md` |
| 工程结构与实现顺序 | `PLAN.md` |
| 学习方式或文档职责 | `docs/learning-guide.md` |
| 课程正文 | `skills/course-writing/SKILL.md` |
| 阅读顺序 | `course/learning-path.md` |
| 知识完整性 | `course/knowledge-map.md` |
| 产品运行 | `source/apps/review_assistant/README.md` |
| 代码掌握与审查 | `docs/ai-coding-mastery.md` |

## 执行边界

- 先找到唯一真源，再修改引用处。
- 不把迁移过程、实时进度和临时争论写入长期文档。
- 不为同一能力创建平行 package、demo 或产品。
- 不用 Mock 冒充真实模型、检索或 Agent 结果。
- 不让平台远期能力扩大当前 SPEC。
- 默认不读取或扩展 `archive/`。
- 未经用户要求不创建 commit 或 tag。

交付时说明修改、真源、验证和仍存在的边界。
