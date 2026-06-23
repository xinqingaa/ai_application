# AI Application Project Study Archive

## 目录定位

`other` 用来归档 AI 应用类开源项目的源码拆解、架构学习和业务迁移材料。

每个被拆解项目都应该在本目录下有一个独立子目录，例如：

```text
ai_application/other/ragflow/
```

这里的文档目标不是简单总结项目功能，而是把一个项目拆成可学习、可复用、可迁移的知识资产。

## 项目路径约定

源码项目理论上都与 `ai_application` 目录同级。

路径规则：

```text
workspace_root/
  ai_application/
    other/
      <project_name>/
  <project_name>/
```

例如当前归档目录为：

```text
/Users/lrq/work/agent_study/ai_application/other/ragflow
```

则源码项目默认路径为：

```text
/Users/lrq/work/agent_study/ragflow
```

## 项目查找规则

拆解新项目时，只允许按下面的确定性规则查找源码路径：

1. 先定位 `ai_application` 所在目录。
2. 取 `ai_application` 的父目录作为 `workspace_root`。
3. 将项目名拼到 `workspace_root` 下：

```text
source_path = parent(ai_application) / <project_name>
archive_path = ai_application / other / <project_name>
```

如果 `source_path` 不存在，直接停止并报错：

```text
项目路径找不到：<source_path>
```

不要做这些事：

- 不要全局搜索。
- 不要跨 workspace 搜索。
- 不要用 `find /`、`mdfind` 或类似方式猜路径。
- 不要在找不到项目时自动改用其他同名目录。

## 拆解产物约定

每个项目默认输出 3 份主文档：

```text
ai_application/other/<project_name>/
  01_<project_name>_architecture_and_domain_model.md
  02_<project_name>_core_pipeline.md
  03_<project_name>_workflow_agent_and_business_playbook.md
```

如果项目没有 Workflow 或 Agent 能力，第三份可以调整为业务迁移手册、二开路线或生产化拆解。

可选扩展文档：

```text
04_<project_name>_deployment_and_operations.md
05_<project_name>_extension_and_secondary_development.md
06_<project_name>_source_reading_notes.md
```

## 文档内容要求

每次项目拆解至少覆盖：

- 项目定位和核心价值。
- 目录结构和模块职责。
- 核心领域模型。
- 主业务链路和数据流。
- 关键逻辑流程和调用关系。
- Workflow / Agent / Tool 编排，如果项目具备。
- 生产化能力：任务、队列、重试、取消、权限、观测、评测、部署。
- 可以迁移到自己业务的设计经验。
- 适合和不适合的业务场景。
- 参考代码位置。

## 新项目拆解流程

1. 确认项目名 `<project_name>`。
2. 根据路径规则校验源码目录是否存在。
3. 创建归档目录：

```text
ai_application/other/<project_name>/
```

4. 先读 README、docs、架构说明和部署文档。
5. 再读目录结构、数据模型、主入口和服务层。
6. 阅读主链路源码。
7. 阅读 Workflow、Agent、Tool、Memory、Connector 等编排扩展能力。
8. 提炼业务价值和可迁移经验。
9. 输出 3 份或更多 Markdown。
10. 更新本 README 的“已归档项目”。

## 已归档项目

| 项目 | 源码路径 | 归档目录 | 文档 |
| --- | --- | --- | --- |
| RAGFlow | `/ragflow` | `ai_application/other/ragflow` | [架构与领域模型](./ragflow/01_ragflow_architecture_and_domain_model.md), [RAG 主链路](./ragflow/02_ragflow_core_rag_pipeline.md), [Workflow / Agent / 业务迁移](./ragflow/03_ragflow_workflow_agent_and_business_playbook.md) |
| MaxKB | `/MaxKB` | `ai_application/other/MaxKB` | [架构与领域模型](./MaxKB/01_MaxKB_architecture_and_domain_model.md), [核心链路](./MaxKB/02_MaxKB_core_pipeline.md), [Workflow / Agent / 业务迁移](./MaxKB/03_MaxKB_workflow_agent_and_business_playbook.md) |

## 维护原则

- 文档优先服务学习，不追求复述全部代码。
- 主链路要比功能列表重要。
- 业务经验要保留，但必须和源码设计对应起来。
- 参考代码集中放在每篇文档末尾。
- 不要把临时讨论语气写进最终文档。
- 新项目归档时，保持命名和结构一致，便于长期积累。
