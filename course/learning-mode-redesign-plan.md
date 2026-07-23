# AI Agent 课程学习模式重设计方案

> 本文是课程学习方式的重设计方案与执行计划，不替代 [docs/learning-guide.md](../docs/learning-guide.md)，也不记录实时学习进度。
>
> 方案经过一个 RAG 概念链路和需求评审助手垂直切片试点后，再决定哪些规则合并进 `learning-guide.md`。

## 1. 设计背景

当前课程已经具备较完整的长期目标、能力路线、项目版本和代码组织规范：

- `02_llm`–`07_projects` 负责能力路线。
- 需求评审助手 V0–V6 负责项目版本。
- `source/packages/` 负责共享能力的唯一实现。
- `source/demos/` 负责关键机制观察。
- 课程主线围绕真实 AI 应用闭环，而不是多个孤立项目。

这些方向不需要推翻。

真正需要调整的是学习过程：当前代码组织虽然已经统一，但学习活动仍然接近“每篇文档对应一次实现和一次验收”。这使得课程没有真正摆脱旧版“章节 + 脚本”的学习体验。

## 2. 当前问题

### 2.1 代码组织变化了，学习单位没有变化

当前学习经常按下面的方式推进：

```text
阅读一篇专题
→ 扩展一次 package
→ 运行一个 demo 或测试
→ 完成本节自检
→ 进入下一篇专题
```

旧版是“一章文档 + 一组脚本”，新版是“一篇文档 + 一次 package 增量 + 一个 lab”。工程结构更好了，但学习过程依然被小节切割。

### 2.2 “一节一交付”被执行成硬约束

当前规范要求每篇正文和一次代码增量同步完成。这对 Provider、Prompt 这类较小能力可以工作，但不适合 RAG、Agent、Workflow 这种需要先建立整体模型、再拆解机制、最后组合链路的系统能力。

主要后果：

- 复杂概念被人为拆得过细。
- 学习者频繁在概念、代码、配置和验收之间切换。
- 每节都需要重新适应对象、文件和命名。
- 主线被单节完成标准打断。
- 课程完成容易变成连续勾选小任务。

### 2.3 正文很长，但原理解释仍然不够清晰

当前 LLM 正文普遍有 400–700 行，Structured Outputs 和 Context Engineering 的工程描述也并不缺少。

问题不是文字数量少，而是单篇正文同时承担太多职责：

- 概念教材。
- 项目架构设计。
- package API 说明。
- 源码和路径说明。
- demo 运行手册。
- 框架对比。
- 失败边界。
- 后续课程预告。
- 项目版本映射。
- 完成验收。

因此会出现：

```text
工程信息很多
≠
核心原理讲得清楚
```

常见的认知顺序变成：

```text
先出现对象名和字段
→ 再出现 package 结构
→ 再说明项目位置
→ 学习者反过来推测它解决什么问题
```

应当改为：

```text
具体问题
→ 现有方案为什么失败
→ 为什么需要新机制
→ 白话定义
→ 输入、处理、输出
→ 反例和边界
→ 对象名、字段和代码
```

### 2.4 RAG 仍然存在认知跳跃

当前 RAG 大纲在 Embedding 之前已经安排了：

- LangChain 抽象。
- Document、Loader、TextSplitter。
- 复杂文档处理。
- Chunk 和 Metadata。
- Knowledge Governance。
- 入库任务、权限和版本。

Embedding 到第 07 节才正式出现，并且和 Vector Store、pgvector、top-k、HNSW、Recall@k 放在一起。

这会导致：

```text
还不清楚文本为什么要变成向量
→ 已经开始配置向量库
→ 已经开始讨论索引、召回和工程指标
```

这并没有真正解决“还不懂向量化就开始做向量化”的问题。

### 2.5 参与感不足

当前文档通常已经提前决定：

- package 怎么拆。
- 对象如何命名。
- 字段如何设计。
- 策略有哪些。
- demo 使用哪些变量。
- 预期结果是什么。
- 哪些代码应该放在哪个模块。

学习者主要负责阅读、运行、观察和解释。

但代码所有权还应包含：

```text
判断
→ 设计
→ 实现
→ 修改
→ 调试
→ 迁移
→ 取舍
```

当前完成标准对“能解释、能运行”覆盖较多，对“能修改、能主动制造失败、能定位和迁移”覆盖不足。

## 3. 从旧版文档保留什么

旧版整体不能恢复为主线，因为旧版存在：

- 一章多个脚本。
- 章节之间代码重复。
- 入口分散。
- 代码目录和文档目录高度镜像。
- 缺少共享 package。
- 项目闭环较弱。

但旧版概念文档有值得恢复的教学方法。

### 3.1 先给目标、边界和阅读顺序

概念文档应先说明：

- 这一篇要解决什么。
- 不解决什么。
- 学到什么程度。
- 前置是什么。
- 后续会依赖什么。
- 当前是否需要代码。

### 3.2 每篇只承担一个核心问题

一篇文档不应同时讲完 Provider、Prompt、Schema、Context、Streaming、Reliability、Harness 和 Project。

### 3.3 先用自然语言建立主线

Embedding 可以先用下面一句话建立心智模型：

```text
把文档块变成向量
→ 把用户问题变成向量
→ 在同一个向量空间中比较
→ 得到相关文档排序
```

之后再引入 `SourceChunk`、`EmbeddedChunk`、`embed_query`、`embed_documents` 和 `cosine_similarity`。

### 3.4 先讲输入和输出，再讲实现

每个核心机制都应先明确：

| 阶段 | 输入 | 输出 |
| --- | --- | --- |
| 文档向量化 | 文档块 | 文档向量 |
| 查询向量化 | 用户问题 | 查询向量 |
| 相似度计算 | 查询向量 + 文档向量 | 相似度分数 |
| 排序 | 分数列表 | 相关文档 |

## 4. 总体重设计方向

课程仍然保留两个阶段：

```text
阶段一：AI 核心概念理解
阶段二：需求评审助手项目实战
```

但不是：

```text
先把全部理论读完
→ 再一次性开始做项目
```

而是：

```text
阶段一建立核心概念和机制地图
→ 阶段二用一个项目垂直切片组合这些机制
```

现有 `02`–`07` 大纲保留为：

```text
知识地图 / 能力清单 / 备课索引
```

实际学习顺序新增为：

```text
概念单元
→ 机制单元
→ 项目任务
→ 失败复盘
```

代码仍然保留单一 package 和 import 复用原则，但 package 不再要求每个知识点都同步增长。

## 5. 阶段一：AI 核心概念理解

阶段一的目标是建立一张可以解释后续工程选择的概念地图，而不是提前完成所有工程实现。

### 5.1 概念单元 0：AI 应用问题空间

需要区分：

- 传统程序。
- 搜索。
- 数据库。
- LLM。
- RAG。
- Tool。
- Agent。
- Workflow。

目标：看到一个需求时，能判断它主要是模型问题、知识问题、工具问题、流程问题还是产品体验问题。

### 5.2 概念单元 1：LLM 最小工作原理

需要讲清：

- Token。
- 下一个 Token 预测。
- 一次调用的输入、处理和输出。
- 模型为什么不是数据库。
- 模型为什么会幻觉。
- 上下文为什么影响成本、延迟和效果。
- 流式输出为什么是逐步生成的自然结果。

不在这里展开 Provider、LangChain、Multi-Agent 和完整 `llm_core` 架构。

### 5.3 概念单元 2：模型契约

集中理解：

```text
Prompt：任务协议
Schema：结果契约
Context：输入材料边界
```

认知递进：

```text
自由文本
→ Prompt 要求格式
→ JSON Mode
→ JSON Schema
→ Pydantic 校验
→ 业务只消费已校验结果
```

当前 Prompt、Structured Outputs 和 Context Engineering 的内容应围绕这条主线重组，而不是分别扩展三个 package 能力。

### 5.4 概念单元 3：RAG 完整故事

先回答：

> 为什么一个已经很强的模型，仍然不能直接完成企业需求评审？

使用同一个需求评审案例讲清：

```text
用户问题
→ 需要哪些外部知识
→ 如何找到相关知识
→ 如何把知识放入上下文
→ 如何生成带依据的回答
→ 证据不足时如何拒答或追问
```

这里先建立全貌，不急着进入 LangChain、Vector Store、pgvector 或 Knowledge Governance。

### 5.5 概念单元 4：检索机制

固定顺序：

```text
关键词匹配
→ 文本表示
→ Embedding
→ 相似度
→ 向量检索
→ Retriever
```

Embedding 必须单独解释：

- 为什么需要向量表示。
- 向量表示的目的是什么。
- query 和 document 为什么必须位于同一空间。
- 相似度比较什么。
- Embedding 能解决什么。
- Embedding 不能解决什么。
- 为什么精确接口名不一定适合只用向量检索。

Vector Store 另行解释：

- 存储和查询向量。
- 索引和 top-k。
- pgvector 的项目取舍。
- Vector Store 不等于知识库。
- Vector Store 不保证答案正确。

### 5.6 概念单元 5：可信 RAG

需要理解：

- Context Construction。
- Sources。
- Citation。
- Refusal。
- Structured RAG Output。
- Retrieval Quality。
- Generation Quality。
- Citation Quality。
- Bad Case。

完整链路：

```text
候选材料
→ 选择材料
→ 组织上下文
→ 生成结构化回答
→ 检查引用
→ 证据不足时拒答或追问
```

### 5.7 概念单元 6：Agent 和 Workflow

先区分：

| 结构 | 主要特征 |
| --- | --- |
| Chain | 步骤固定 |
| Workflow | 状态、分支、循环和人工节点可控 |
| Agent | 模型动态决定下一步 |
| Multi-Agent | 多个角色或能力协作 |

工具调用主线：

```text
模型决定是否调用工具
→ 应用校验参数
→ Runtime 执行工具
→ 工具结果回到上下文
→ 模型决定继续、停止、追问或转人工
```

必须明确 Tool Schema、Tool Runtime、Agent Loop 和 Workflow State 的区别。

### 5.8 概念单元 7：质量与 AI Native 体验

质量闭环：

```text
样例
→ 运行
→ 记录
→ 评估
→ bad case
→ 修改
→ 回归
```

AI Native 体验：

```text
输入
→ 流式状态
→ 检索依据
→ 工具过程
→ 人工确认
→ 最终结果
```

阶段一只需要理解 Golden Set、Trace、Bad Case、Cost、Latency、Event Stream、Task State 和 Human Review。

## 6. 阶段一的文档类型

### 6.1 概念篇

回答：

> 这个概念是什么，为什么需要它？

必须包含：

1. 一个真实场景。
2. 一句话定义。
3. 输入、处理、输出。
4. 最小数据流。
5. 一个完整小例子。
6. 与相近概念的区别。
7. 一个反例。
8. 能解决什么。
9. 不能解决什么。
10. 在需求评审助手中的位置。
11. 自检题。

概念篇可以没有代码。

### 6.2 机制篇

回答：

> 这个机制为什么有效，内部发生了什么？

必须包含：

1. 现有方案的问题。
2. 新机制解决什么。
3. 输入输出变化。
4. 机制数据流。
5. 从简单到复杂的递进。
6. 失败案例。
7. 最小实验。
8. 框架如何封装。
9. 验收题。

### 6.3 项目任务篇

回答：

> 这次项目要增加什么能力，学习者需要做哪些选择？

必须包含：

1. 业务目标。
2. 已有能力。
3. 本次新增能力。
4. 设计决策题。
5. AI Coding 边界。
6. 实现任务。
7. 运行观察。
8. 需求变更题。
9. bad case。
10. 验收标准。

项目任务篇不重新长篇讲基础原理。

### 6.4 框架映射篇

只回答：

- 原生机制是什么。
- 框架抽象了什么。
- 框架没有解决什么。
- 为什么使用框架。
- 什么时候不应该使用框架。

框架必须在原理之后出现。

## 7. 阶段二：需求评审助手项目实战

阶段二不创建第二个独立小项目，而使用需求评审助手中的一个固定垂直切片：

```text
一份售后入口 PRD
一份订单状态规则
一份售后接口文档
一份客户端展示规则
一份历史评审记录
```

整个阶段尽量使用同一组材料，避免每节更换案例导致上下文断裂。

### 7.1 M0：LLM 基线

```text
PRD
→ 直接调用模型
→ 输出风险列表
```

观察模型能力、不稳定性、幻觉、成本和延迟，写出至少三条失败或不确定现象。

### 7.2 M1：关键词检索版固定 RAG

```text
PRD
→ 关键词查找文档
→ 选出相关片段
→ 拼入上下文
→ 生成带来源的回答
```

先不用 Embedding，先理解召回、top-k、检索失败和生成失败的区别。

### 7.3 M2：Embedding 与语义检索

比较：

```text
关键词检索
vs
向量检索
```

至少准备：词面相同、同义改写、精确接口名三类问题，并观察向量检索的改善和缺陷。

### 7.4 M3：可信 RAG

加入 Context Construction、Structured Output、Sources、Citation 校验、Refusal 和最小 Golden Set。

必须制造：

1. 问题不在知识库。
2. 检索到了错误文档。
3. 模型生成不存在的 Citation。

### 7.5 M4：Single Agent RAG

加入 Query Rewrite、Source Routing、Retriever as Tool、检索质量判断和追问补全。

Agent 只解决一个问题：固定检索不足时，是否需要补查、换知识源或追问。

### 7.6 M5：Workflow 与人工审核

```text
接收需求
→ 检索证据
→ 风险分析
→ 判断证据是否充分
→ 人工确认
→ 生成评审报告
```

重点理解状态、分支、人工节点、中断、恢复和重试。

### 7.7 M6：选择性 Multi-Agent

只有 Single Agent 出现明确瓶颈时才拆分角色，并比较 Single Agent 与 Multi-Agent 的质量、成本、延迟、可解释性和失败定位难度。

## 8. 项目任务的参与机制

每个项目任务都必须经历：

```text
先判断
→ 再让 AI 实现
→ 解释数据流、状态流和异常流
→ 修改一个需求
→ 主动制造一个失败
→ 定位并修复
→ 迁移到另一个场景
```

设计前必须回答：

- 输入是什么。
- 输出是什么。
- 最可能失败在哪里。
- 哪些部分必须确定性。
- 哪些部分可以交给模型。
- 为什么不用更复杂方案。

## 9. 现有课程内容的处理方式

### 9.1 保留为工程材料

以下内容有工程价值，但不一定适合作为第一次概念学习入口：

- Provider 抽象。
- Structured Outputs 失败分层。
- Context 诊断字段。
- Harness 记录模型。
- Reliability。
- Cost / Latency。

### 9.2 优先重写为概念篇和机制篇

第一批试点内容：

```text
course/02_llm/00_llm_problem_space.md
course/02_llm/02_prompt_engineering_for_apps.md
course/02_llm/03_structured_outputs.md
course/02_llm/05_context_engineering.md
course/03_rag/00_rag_and_agent_problem_space.md
course/03_rag/07_embedding_and_vector_store.md
```

第一条试点链路：

```text
RAG 是什么
→ 关键词检索
→ Embedding 是什么
→ Vector Store 是什么
→ Retriever 是什么
```

### 9.3 延后到项目阶段

以下内容继续保留在大纲中，但按项目遇到的问题引入：

```text
Streaming 完整实现
Reliability
Harness
Cost / Latency / Caching
Knowledge Governance
Memory
LangGraph
Redis
Docker
AI Native 工作台
```

## 10. 执行计划

### 阶段 0：重新定义学习规则

暂时不继续扩展代码，先完成：

1. 将 `02`–`07` 大纲标记为知识清单。
2. 为主题标注前置依赖。
3. 标注主题属于概念篇、机制篇、框架映射篇还是项目任务篇。
4. 取消“一篇正文必须同步一次 package 增量”的硬约束。
5. 将交付单位改为“学习单元”。

新的学习单元交付：

```text
概念文档组
+ 机制实验
+ 项目任务
+ 失败复盘
```

### 阶段 1：RAG 概念链路试点

先不重写整门课程，只重写：

```text
RAG 问题空间
→ 关键词检索
→ Embedding
→ Vector Store
→ Retriever
```

试点验收：

- 能不用 LangChain 解释 RAG 主链路。
- 能分别解释 Embedding 和 Vector Store。
- 能画出 query 到 ranked results 的流程。
- 能说明关键词检索和向量检索的差异。
- 能说明每一层失败时应该先排查什么。

### 阶段 2：M0–M2 项目试点

实现：

```text
LLM 基线
→ 关键词 RAG
→ Embedding 语义检索
```

重点观察：

- 是否能解释每一步。
- 是否能区分检索失败和生成失败。
- 是否真正做过设计选择。
- 是否主动修改过一个需求。
- 是否制造并定位过一个 bad case。
- 是否仍然存在“代码能跑但不理解”的感觉。

### 阶段 3：根据试点修订规范

根据试点结果再调整：

- 概念篇深度。
- 机制篇深度。
- 框架引入时机。
- 代码交付频率。
- 自检题和修改题。
- 学习者参与方式。
- 文档与 package 的边界。

### 阶段 4：扩展可信 RAG 和 Agent

```text
Sources / Refusal
→ Structured RAG Output
→ RAG Evaluation
→ Query Rewrite
→ Source Routing
→ Retriever as Tool
→ Single Agent RAG
→ Workflow
→ Human-in-the-loop
→ 选择性 Multi-Agent
```

### 阶段 5：最后进行项目工程化

```text
Eval / Trace
→ Streaming UI
→ FastAPI
→ PostgreSQL / pgvector
→ Redis
→ Background Jobs
→ Docker
→ AI Native Workbench
→ Portfolio / Deployment
```

## 11. 阶段完成标准

### 11.1 阶段一完成标准

不要求完整产品，但必须能够：

- 解释 LLM、RAG、Agent、Workflow 的边界。
- 画出固定 RAG 的完整数据流。
- 分别解释 Chunk、Embedding、Vector Store、Retriever。
- 说明关键词检索和向量检索的优缺点。
- 解释 Sources、Refusal、Eval 的作用。
- 解释模型选择工具和应用执行工具的区别。
- 说明 Single Agent 什么时候足够。
- 说明 Multi-Agent 什么时候只是额外复杂度。

### 11.2 阶段二完成标准

不能只满足“项目可以运行”，还必须：

- 做过架构或数据契约选择。
- 修改过至少一个业务需求。
- 制造并定位过至少一个 bad case。
- 能解释数据流、状态流和异常流。
- 能从关键词 RAG 迁移到向量 RAG。
- 能从固定 RAG 迁移到 Single Agent。
- 能说明为什么没有继续复杂化。
- 能把方法迁移到另一个业务场景。

## 12. 下一步建议

当前不要继续直接扩展 LLM 后续专题，也不要马上进入完整 RAG 工程实现。

建议顺序：

```text
重新定义学习单元
→ 设计 RAG 概念试点
→ 重写 Embedding / Vector Store 概念链
→ 完成 M0–M2 项目试点
→ 根据实际学习体验修订规范
```

真正需要验收的不是文档长度、代码数量或 package 完整度，而是：

```text
读完后是否知道这个概念是什么？
是否知道它为什么存在？
是否知道它内部如何工作？
是否知道什么时候失败？
是否能自己做出设计选择？
是否能修改和调试系统？
```
