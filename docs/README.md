# docs

`docs/` 保存本仓库长期有效的战略与协作规范。

这里不保存课程正文、项目版本任务、产品运行手册、迁移计划或实时学习进度。

## 推荐阅读顺序

1. [strategy.md](strategy.md)：为什么学习、唯一主项目、两个阶段和 V0–V6。
2. [learning-guide.md](learning-guide.md)：如何学习、如何阅读、三类文档、代码与项目如何组织。
3. [ai-coding-mastery.md](ai-coding-mastery.md)：AI Coding 参与下怎样算真正掌握。
4. [agent-skill.md](agent-skill.md)：AI Agent 如何选择真源、执行任务和避免越界。
5. [ai-application-platform.md](ai-application-platform.md)：企业 AI 应用的远期能力地图，按需阅读。

## 文档职责

| 文档 | 负责 | 不负责 |
| --- | --- | --- |
| `strategy.md` | 职业定位、唯一目标、两个阶段、V0–V6、高层边界 | 课程模板、代码目录细节、单版本任务 |
| `learning-guide.md` | 学习方式、三类文档、阅读路径、知识清单、代码与运行规范 | 职业背景、具体专题清单、产品实现 |
| `ai-coding-mastery.md` | 掌握标准、代码所有权、调试与迁移能力 | 课程目录、工程依赖规则 |
| `agent-skill.md` | AI Agent 的读取路由、任务判断和执行边界 | 重复其他文档的完整规范 |
| `ai-application-platform.md` | 企业平台长期能力和采用边界 | 当前项目待办和验收清单 |

## 内容真源

| 内容 | 真源 |
| --- | --- |
| 长期目标和项目阶段 | `strategy.md` |
| 学习、文档、代码和运行规则 | `learning-guide.md` |
| AI Coding 掌握判断 | `ai-coding-mastery.md` |
| 企业平台远期能力 | `ai-application-platform.md` |
| AI Agent 执行路由 | `agent-skill.md` |
| 课程正文和知识清单 | `course/` |
| 项目篇教材 | `course/project/` |
| 通用能力代码 | `source/packages/` |
| 可运行产品 | `review_assistant/` |

## 冲突处理

- 长期目标冲突时，以 `strategy.md` 为准。
- 学习或代码组织冲突时，以 `learning-guide.md` 为准。
- 掌握标准冲突时，以 `ai-coding-mastery.md` 为准。
- `ai-application-platform.md` 不能扩大当前项目阶段。
- `agent-skill.md` 只负责执行路由，不能改写其他真源。
- 用户当前明确提出的目标和范围优先于仓库默认规则。

## 维护原则

- 同一规则只在一个文档中详细维护。
- 其他文档通过链接引用，不复制完整内容。
- 不记录迁移过程、实时进度和临时讨论。
- 不新增承担相同职责的规划文档。
- 课程和产品事实发生变化时，修改对应真源，而不是在 `docs/` 中增加补丁说明。
