# Project Dissection Skill

## 目标

把 AI 应用类开源项目拆解成可学习、可迁移、可复用的知识资产。

这个 skill 适用于：

- 学习一个 AI 应用项目的代码架构。
- 拆解 RAG、Agent、Workflow、LLMOps、数据连接器、模型编排等能力。
- 将项目作者的工程经验转化为自己的业务设计方法。
- 在 `ai_application/other/<project_name>/` 下形成长期归档。

## 输入

默认输入是项目名：

```text
project_name
```

例如：

```text
ragflow
```

## 路径解析规则

源码项目理论上与 `ai_application` 目录同级。

解析方式：

```text
workspace_root = parent(ai_application)
source_path = workspace_root / project_name
archive_path = ai_application / other / project_name
```

示例：

```text
ai_application_path = /ai_application
project_name = ragflow
source_path = /ragflow
archive_path = /ai_application/other/ragflow
```

## 失败规则

如果 `source_path` 不存在，必须直接停止并告知用户：

```text
项目路径找不到：<source_path>
```

禁止行为：

- 不要全局搜索。
- 不要递归扫描整个 workspace 来猜项目路径。
- 不要跨目录寻找同名项目。
- 不要自动改用其他路径。

用户明确提供新路径时，才可以使用用户指定路径。

## 阅读顺序

### 1. 文档层

先阅读：

- README
- docs
- quickstart
- architecture
- deployment
- examples
- release notes

目标：

- 理解项目定位。
- 找出核心功能。
- 识别作者强调的价值点。
- 判断项目主要面向哪些业务场景。

### 2. 目录层

梳理仓库目录：

- API / server
- service / domain
- model / schema
- worker / task
- pipeline / workflow
- agent / tools
- memory / connector
- frontend
- deployment
- tests

目标：

- 建立模块地图。
- 区分控制面和数据面。
- 找到主链路入口。

### 3. 领域模型层

阅读数据库模型、schema、核心 class。

重点识别：

- 租户/用户。
- 项目/应用/知识库。
- 文档/文件/任务。
- 会话/消息/引用。
- Workflow/Agent/Tool。
- 连接器/数据源。
- 模型 provider。
- 评测/观测。

目标：

- 知道项目用哪些对象承载业务状态。
- 理解对象之间的关系。

### 4. 主链路层

找到项目最核心的业务链路，并画出流程。

常见链路包括：

- 文档入库链路。
- 检索链路。
- 问答生成链路。
- Agent 工具调用链路。
- Workflow 执行链路。
- 任务调度链路。
- 数据源同步链路。

每条链路至少说明：

- 入口。
- 核心服务。
- 中间状态。
- 调用顺序。
- 输入输出。
- 失败处理。
- 可迁移设计。

### 5. Workflow / Agent 层

如果项目有 Workflow 或 Agent，重点阅读：

- DSL 格式。
- 组件注册机制。
- 变量系统。
- 节点调度。
- 事件流。
- Tool binding。
- MCP 或外部工具协议。
- Memory。
- 人工确认。
- 异常分支。

目标：

- 理解它如何把模型、知识、工具和业务流程组合起来。

### 6. 生产化层

关注项目如何处理真实上线问题：

- 异步任务。
- 队列。
- 重试。
- 取消。
- 幂等。
- 删除清理。
- 权限。
- 模型配置。
- 连接器同步。
- 观测。
- 评测。
- 成本控制。

目标：

- 提炼 demo 到 production 的关键经验。

### 7. 业务迁移层

最后回答：

- 这个项目适合什么业务？
- 能解决什么问题？
- 哪些设计可以直接学习？
- 哪些设计不要盲目照搬？
- 如果迁移到自己的业务，第一版应该做什么？
- 后续如何演进？

## 输出文档规范

默认输出 3 份 Markdown。

### 01 架构与领域模型

推荐文件名：

```text
01_<project_name>_architecture_and_domain_model.md
```

内容包括：

- 项目定位。
- 仓库目录职责。
- 分层架构图。
- 运行时组件。
- 核心领域对象。
- 控制面与数据面。
- 平台型设计。
- 业务价值与适用场景。
- 学习路线。
- 参考代码。

### 02 主链路源码级拆解

推荐文件名：

```text
02_<project_name>_core_pipeline.md
```

内容包括：

- 主链路总览。
- 请求时序图。
- 入口 API。
- Service 调用。
- Worker / Task / Queue。
- 数据处理流程。
- 检索或推理流程。
- 结果生成流程。
- 生产治理细节。
- 可迁移模式。
- 参考代码。

### 03 Workflow / Agent / 业务迁移

推荐文件名：

```text
03_<project_name>_workflow_agent_and_business_playbook.md
```

内容包括：

- Workflow / Agent 编排模型。
- DSL。
- 组件系统。
- 变量系统。
- 调度机制。
- Tool / MCP / Memory。
- 业务迁移路线。
- 业务蓝图。
- 常见反模式。
- 自己实现时可抽象的模块。
- 参考代码。

如果项目没有 Workflow / Agent，则第三份改为：

```text
03_<project_name>_business_adaptation_playbook.md
```

## 写作要求

- 用中文输出。
- 不要只写功能列表，要讲清逻辑链路。
- 不要逐行解释代码，要做源码级结构化拆解。
- 保留业务经验，但必须和代码设计对应。
- 每份文档都要有“参考代码”部分。
- Mermaid 图用于架构图、时序图、流程图。
- 表格用于模块职责、对象关系、输入输出、设计取舍。
- 文件名保持稳定、可归档。
- 如果重构已有文档，保留有价值内容并移动到更合适的位置。

## 质量检查

完成后检查：

- 是否覆盖架构、主链路、编排、业务迁移。
- 是否有明确源码参考。
- 是否保留了业务经验。
- 是否有图和表帮助阅读。
- 是否没有临时草稿语气。
- 是否没有 TODO、占位符、无意义空章节。
- 是否没有误导性的旧文件名。

## 异常处理

### 找不到项目路径

直接返回：

```text
项目路径找不到：<source_path>
```

然后停止。

### 项目没有文档

说明 README/docs 不足，然后直接从目录和代码入口拆解。

### 项目没有 Agent / Workflow

第三份文档改成业务迁移或二开路线，不强行套 Agent 结构。

### 代码量过大

优先主链路，不追求全量阅读：

1. 入口。
2. 数据模型。
3. 主服务。
4. Worker。
5. 编排。
6. 生产化。

## 已验证示例

RAGFlow 已按此方法归档在：

```text
ai_application/other/ragflow/
```

文档包括：

- `01_ragflow_architecture_and_domain_model.md`
- `02_ragflow_core_rag_pipeline.md`
- `03_ragflow_workflow_agent_and_business_playbook.md`
