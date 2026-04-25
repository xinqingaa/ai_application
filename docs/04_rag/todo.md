# 企业内部需求提效评审助手 Todo

> 目标：基于当前已经掌握的 `02_llm + 04_rag` 能力，做一个可运行、可评估、可视化操作的综合 RAG 项目。
> 当前版本聚焦“企业内部需求提效评审”这一真实场景：接收需求相关文档，生成带依据的评审问答与结构化评审结果。
> 项目当前不做完整需求管理系统，但架构要向企业级演进对齐，保证后续扩展多模态、原型生成、代码生成时，核心 `LLM / RAG / Backend` 模块仍然可复用。

---

## 一、项目定位

- 这是一个**固定 RAG 主链路项目**
- 这是一个**面向企业内部需求提效评审的业务助手**
- 这是一个**教学型、可落地、可扩展的项目**

这个项目服务的典型角色包括：

- 产品经理
- 研发负责人 / 架构师
- 测试 / QA
- PMO / 评审参与者

它要解决的问题不是“随便回答问题”，而是：

- 接收 `PRD / 流程说明 / 业务规则 / 接口文档 / 会议纪要 / 历史评审记录`
- 在企业内部知识范围内，对需求做**理解、检索、引用、评审**
- 输出**带依据的回答**和**结构化评审结果**

这个项目的核心业务输出不是普通聊天，而是：

- 需求解读
- 评审问题补全
- 缺失信息提示
- 风险点提示
- 边界条件提示
- 影响范围提示
- 验收标准检查
- 来源引用与拒答

这不是：

- 完整需求管理系统
- BPM / 审批流平台
- Agent 工作流项目
- LangGraph 项目
- 原型设计平台
- 代码自动生成平台
- 企业后台管理系统

这个项目当前的价值是：

- 用当前已经掌握的知识，把 `LLM -> RAG -> API -> UI` 串成一条真实业务主线
- 把 `LLM 内核`、`RAG 内核`、`领域规则`、`后端壳`、`前端工作台` 的边界设计清楚
- 让当前版本聚焦需求评审，但未来可以自然演进到多模态原型理解、需求实现辅助和代码生成

---

## 二、为什么这个方向适合 LLM + RAG

需求评审是一个很适合 `LLM + RAG` 的企业内部场景，因为它同时满足下面几个条件：

- **知识密集**：需求评审依赖大量制度、规则、历史案例和上下游文档
- **不能乱编**：评审建议必须能回到文档依据，不能只靠模型自由发挥
- **输出适合结构化**：评审结果天然可以组织成 `摘要 / 风险 / 缺失信息 / 待确认问题 / 影响范围 / 来源`
- **适合做可视化工作台**：文档、chunk、检索结果、上下文和最终结论都可以展示
- **适合做评估闭环**：可以用固定需求案例和预期评审结果做 `golden set`
- **演进路径自然**：后续可以接入原型图、流程图、页面截图、生成原型和生成代码

所以这个项目既能体现你前面课程的能力，又不会为了“像企业产品”而过早堆复杂度。

---

## 三、项目总目标

### 1. 当前版本目标

- 跑通完整固定 RAG 主链路
- 自然复用 `02_llm` 的真实模型调用能力
- 保持 `04_rag` 各章节已经建立的对象边界
- 让系统能接收需求相关文档并构建索引
- 让系统能对需求文档做问答和评审
- 输出 `answer + sources`
- 输出结构化 `review report`
- 对证据不足的问题做拒答或提示待补充信息
- 提供一层 `FastAPI` 接口
- 提供一个 `Vite + React` 的评审工作台
- 保留最小评估闭环，而不是只做一个“能回答”的 demo

### 2. 架构目标

- 当前实现轻量
- 核心 `RAG` 模块可复用
- 领域规则与通用 RAG 内核分离
- API 层足够支持业务
- 前端只负责交互与可视化，不承载 RAG 核心逻辑
- 将来向多模态需求理解、原型辅助、代码生成演进时，只需要补充新的能力层，而不是推倒整个项目

### 3. 当前版本最重要的业务结果

V1 必须明确支持两类能力：

- **评审问答**
  - 用户问一个具体问题，系统给出带依据的回答
  - 例如：这个需求是否写清了边界条件？退款规则和现有制度是否冲突？

- **结构化评审**
  - 用户选择一批文档，系统输出结构化评审报告
  - 例如：需求摘要、关键风险、缺失信息、待确认问题、影响模块、建议补充项、来源引用

---

## 四、项目设计原则

- **主链路优先**：先保证 `document -> chunk -> embedding -> store -> retrieval -> context -> llm -> answer/review + sources` 完整成立
- **业务壳清楚**：项目必须明确围绕“企业内部需求提效评审助手”，不是泛化聊天机器人
- **边界优先**：先把对象、模块、输入输出契约设计清楚，再考虑增加功能
- **解耦优先**：`LLM`、`RAG`、`领域规则`、`服务编排`、`前端工作台` 尽量解耦
- **复用优先**：尽量复用 `02_llm` 和 `04_rag` 已有心智模型，不额外引入过重概念
- **可观察优先**：前端不只是“聊天框”，而是要能看到文档、chunk、检索结果、上下文和评审输出
- **可追溯优先**：评审结果必须能回溯到知识源和片段
- **可扩展优先**：当前不实现的多模态、原型、代码生成能力，要在结构上预留扩展点

---

## 五、当前版本范围

### 1. 必做

- 文档接入：支持 `.md / .txt / .pdf / .docx`
- `.doc` 作为兼容保留项，必要时通过转换链路接入
- 支持需求相关知识源：
  - `PRD`
  - 流程说明
  - 业务规则
  - 接口文档
  - 会议纪要
  - 历史评审记录
- 文档切分与 `metadata`
- `stable document_id / chunk_id`
- `embedding` 生成
- 向量存储
- 基础检索
- `threshold`
- 可选 `mmr`
- context selection
- 评审问答 prompt 组织
- 结构化评审 prompt 组织
- 真实 LLM 生成
- `answer + sources`
- `review_report + sources`
- refusal
- 最小 golden set
- 最小 retrieval / end-to-end eval
- `FastAPI` 后端接口
- `Vite + React` 评审工作台

### 2. 可选，建议加上

- `hybrid` 作为实验性保留项
- mock / real LLM 双路径
- 普通问答接口和流式问答接口
- 普通评审接口和流式评审接口
- 需求文档版本差异对比的保留位
- review checklist 模板配置化

### 3. 明确不做

- Agent
- LangGraph
- GraphRAG
- 多租户
- ACL 权限控制
- 完整审批流
- 审计系统
- 异步任务编排平台
- 对象存储接入
- 数据库持久化治理体系
- 企业级监控告警
- 多模态原型理解
- 自动画原型图
- 自动生成前后端代码
- 完整需求管理后台系统

---

## 六、业务主链路

项目必须围绕下面这条固定链路展开：

```text
需求相关文档
-> load
-> normalize
-> split
-> metadata + stable ids
-> embed_documents
-> vector store
-> retrieve
-> context selection
-> prompt / structured output schema
-> llm
-> answer / review report + sources
-> eval
```

从业务上看，主流程可以理解为：

```text
产品提交需求材料
-> 系统解析并入库
-> 用户发起评审问题或评审任务
-> 系统按知识源检索依据
-> 组织评审上下文
-> LLM 生成回答或结构化评审报告
-> 返回来源引用、待确认问题、风险项
-> 进入评估与 bad case 回看
```

这条链路里：

- `02_llm` 主要贡献：
  - provider config
  - OpenAI-compatible client
  - messages 组织
  - prompt 工程能力
  - 结构化输出能力
  - 流式输出与 API 经验
  - 错误处理、成本、安全的服务层意识

- `04_rag` 主要贡献：
  - 文档处理
  - chunk / metadata / stable id
  - embedding 契约
  - vector store
  - retrieval 策略
  - generation 链路
  - `answer + sources`
  - refusal
  - 评估闭环

---

## 七、后端架构规划

后端固定使用：

- `Python`
- `FastAPI`

后端目标不是把所有逻辑塞进路由，而是做成：

> 可复用 `LLM / RAG` 内核 + 需求评审领域层 + 薄 API 壳

### 1. 建议目录结构

```text
rag_review_lab/
├── README.md
├── app/
│   ├── config/
│   ├── schemas/
│   ├── core/
│   │   ├── llm/
│   │   ├── ingestion/
│   │   ├── embeddings/
│   │   ├── store/
│   │   ├── retrieval/
│   │   ├── generation/
│   │   └── evals/
│   ├── domain/
│   │   └── requirement_review/
│   │       ├── prompts/
│   │       ├── checklists/
│   │       ├── policies/
│   │       └── datasets/
│   ├── services/
│   └── api/
├── data/
├── scripts/
├── tests/
└── frontend/
```

### 2. 模块职责

#### `schemas/`

- 统一项目级对象契约
- 通用对象和领域对象都先走 schema
- 项目内任何模块通信都尽量先过 schema

建议重点统一：

- `SourceDocument`
- `SourceChunk`
- `EmbeddedChunk`
- `RetrievalResult`
- `SourceCitation`
- `RagAnswer`
- `ReviewFinding`
- `ReviewChecklistItem`
- `RequirementReviewReport`
- `GoldenSetCase`
- `ExperimentConfig`

#### `core/llm/`

- 复用 `02_llm` 的最小真实调用能力
- 收敛 provider config 和 client 初始化
- 统一普通生成和流式生成入口
- 保留 mock fallback 的扩展位

最小职责：

- `create_client()`
- `chat()`
- `chat_stream()`
- generation result normalize
- structured output validate / retry 保留位

#### `core/ingestion/`

- 处理文档进入系统的完整输入层
- 保持对 `loader / splitter / metadata / stable id` 的独立封装
- 不把文档类型判断散落到 API 和前端

最小职责：

- discover
- load
- normalize
- split
- build metadata
- build stable ids
- document type detect

#### `core/embeddings/`

- 保持 `embed_documents / embed_query` 的区分
- 明确 embedding space 一致性

最小职责：

- documents embedding
- query embedding
- provider/model/dimensions 校验

#### `core/store/`

- 提供最小存储层契约
- 保证后续替换存储实现时，上层 retrieval 不被迫重写

最小职责：

- `upsert`
- `replace_document`
- `delete_document`
- `similarity_search`
- metadata filter 扩展位

#### `core/retrieval/`

- 负责把底层查询能力组织成稳定检索层
- 当前实现保持固定 RAG 可控策略

最小职责：

- `similarity`
- `threshold`
- `mmr`
- 可选 `hybrid`

设计要求：

- 检索参数显式化
- 检索输出统一为 `RetrievalResult[]`
- 不把检索策略散落进 API 和前端
- 支持按知识源类型过滤，如 `prd / rule / api / meeting_note / review_case`

#### `core/generation/`

- 负责从 `RetrievalResult[]` 到最终 `answer + sources`
- 明确生成层和检索层是两个不同责任区域
- 不把业务规则写死到通用生成模块

最小职责：

- context selection
- context formatter
- prompt builder
- refusal policy
- `answer + sources`

#### `core/evals/`

- 负责最小评估闭环
- 保证这个项目不仅“能回答”，还“能回归”

最小职责：

- golden set
- retrieval eval
- review output eval
- end-to-end rag eval
- bad case review

#### `domain/requirement_review/`

- 承载“需求提效评审”这个业务壳
- 把通用 RAG 和具体场景规则隔离开
- 这里负责需求评审的知识建模，而不是重写底层 RAG

建议放这里的内容：

- 知识源分类
- 文档类型与 metadata 规范
- 评审维度
- 评审输出 schema
- 评审 prompt 模板
- review checklist
- refusal / 兜底策略
- golden set 数据集

建议优先定义的评审维度：

- 完整性
- 清晰性
- 一致性
- 边界条件
- 异常处理
- 依赖影响
- 验收标准
- 风险与待确认问题

#### `services/`

- 项目级编排层
- 负责串接 core 和 domain
- 保证 CLI、API、前端都复用同一套服务层能力

建议拆成：

- `DocumentService`
- `IndexService`
- `ReviewQueryService`
- `ReviewReportService`
- `EvaluationService`

#### `api/`

- `FastAPI` 薄路由层
- 只做请求校验、调用 service、返回响应
- 不在这里写 RAG 和评审细节

---

## 八、前端规划

前端固定使用：

- `Vite`
- `React`

前端定位不是“企业需求管理系统”，而是：

> 一个用于图形化操作和观察“需求评审 RAG 主链路”的工作台

### 1. 前端必须解决什么

- 用户可以导入需求相关文档
- 用户可以看到文档类型、版本和基础 metadata
- 用户可以看到文档被切成什么样
- 用户可以看到当前检索策略和检索结果
- 用户可以看到哪些 chunk 被送进上下文
- 用户可以发起单问题评审问答
- 用户可以发起结构化评审任务
- 用户可以看到最终评审结果和来源
- 用户可以看到最小评估结果

### 2. 建议页面 / 面板

#### 文档面板

- 上传文档
- 选择文档类型
- 文档列表
- 文档基础信息
- 当前索引状态

#### Chunk 面板

- 展示 chunk 列表
- 展示 chunk metadata
- 展示 `document_id / chunk_id`
- 展示文档类型和版本信息

#### 检索面板

- 输入 query
- 选择检索策略
- 设置 `top_k / threshold / mmr`
- 指定知识源类型
- 查看召回结果与分数

#### 评审问答面板

- 输入一个具体评审问题
- 查看回答
- 查看依据摘要
- 查看 refusal
- 查看 sources

#### 结构化评审面板

- 选择待评审文档
- 选择评审维度
- 生成结构化评审报告
- 展示摘要、风险、缺失信息、待确认问题、影响范围、建议补充项
- 展示每条 finding 的依据来源

#### 评估面板

- 运行最小 golden set
- 展示 retrieval 指标
- 展示 review 输出结果
- 展示 end-to-end 结果
- 展示 bad cases

### 3. 前端边界

- 前端不直接承载检索和生成逻辑
- 前端不引入复杂状态机
- 前端不提前做完整后台系统能力
- 前端只围绕观察、操作、验证 RAG 主链路服务
- 业务工作台和调试实验台可以共存，但都必须复用同一后端内核

---

## 九、API 规划

API 以项目演示和前端对接为目标，不追求完整企业接口体系。

### 1. 文档相关

- 上传文档
- 查看文档列表
- 查看单文档详情
- 删除文档
- 触发索引构建 / 重建

### 2. 检索与问答相关

- 检索预览接口
- 评审问答接口
- 可选流式问答接口

### 3. 结构化评审相关

- 发起评审任务
- 生成结构化评审报告
- 可选流式评审接口
- 指定评审维度

### 4. 评估相关

- 查看 golden set
- 运行 retrieval eval
- 运行 review eval
- 运行 rag eval
- 查看最近评估结果

### 5. API 原则

- 路由薄
- 请求响应对象清楚
- 统一复用 service
- 统一复用 schema
- 业务问答接口和结构化评审接口明确区分

---

## 十、企业级对齐的扩展预留

当前版本不实现下面这些能力，但项目设计必须向这些方向对齐。

### 1. 多知识库 / namespace

当前可以先做单知识库。

但结构上要预留：

- `knowledge_base_id`
- namespace
- 按知识库隔离索引和文档

未来就可以把“产品需求评审”“运营规则评审”“技术方案评审”拆到不同知识域，而不重写核心链路。

### 2. 文档版本与差异分析

当前先做最小 `replace_document / delete_document`。

但结构上要对齐未来需求：

- 文档版本
- 增量更新
- 版本对比
- 删除一致性
- 重新索引

需求评审场景里，版本变化非常常见，所以这里必须从一开始就预留。

### 3. metadata filter 向角色与流程过滤演进

当前 `V1` 只做基础 metadata filter。

但未来可以向下扩展：

- 按部门过滤
- 按角色过滤
- 按项目过滤
- 按阶段过滤
- 按评审轮次过滤

也就是说，retrieval 设计不能把 filter 写死成只能按文件名过滤。

### 4. 检索策略升级

当前以固定 RAG 为主：

- `similarity`
- `threshold`
- `mmr`
- 可选 `hybrid`

未来扩展方向：

- rerank
- query rewrite
- 多路检索融合
- 面向评审维度的专用检索
- hosted search / 混合索引

所以 retrieval 层要是“策略层”，而不是单函数脚本。

### 5. 同步索引向异步任务扩展

当前可以同步构建索引。

但未来企业级方向通常需要：

- 异步 ingestion
- 任务队列
- 任务状态跟踪
- 批量导入
- 大文档处理流水线

所以服务层和 API 层需要为异步化留出演进空间。

### 6. 本地存储向数据库 / 对象存储扩展

当前可以用本地文件。

未来可以扩展到：

- MySQL / PostgreSQL
- Redis
- OSS / S3 / MinIO
- 文档归档
- 预处理缓存

因此文档输入层应该尽量保持“文件来源抽象”，不要把路径逻辑写死到业务层。

### 7. 多模态需求理解扩展

当前版本不做多模态。

但未来你明确要走这条路线，所以结构上要预留：

- 原型图截图理解
- 流程图理解
- 页面草图理解
- PDF 页面截图解析
- 图文联合检索与生成

这部分后续更适合放到学完多模态和 Agent 后再接入。

### 8. 从评审助手向原型与代码生成演进

当前版本不直接生成原型和代码。

但未来可以向下扩展：

- 基于需求文档生成页面草案
- 基于评审结果补全原型说明
- 基于需求与接口文档生成代码骨架
- 基于评审报告生成开发任务拆分

这意味着当前的输出 schema 设计要尽量标准化，为后续“需求理解 -> 原型 -> 代码”的链路打基础。

### 9. 单机配置向多环境配置扩展

当前只需要最小配置管理。

未来可以扩展：

- dev / test / prod
- provider 切换
- embedding model 切换
- store backend 切换
- model route / fallback

因此配置层需要从一开始就独立。

### 10. 最小评估向企业观测扩展

当前只做：

- golden set
- retrieval eval
- review eval
- rag eval
- bad cases

未来才扩展：

- 日志观测
- trace
- 线上反馈回流
- 回归报告
- 成本与性能指标

这意味着现在就要把评估当成独立模块，而不是散落脚本。

---

## 十一、项目阶段规划

### Phase 0：先定业务壳

- [ ] 明确项目名称
- [ ] 明确核心用户角色
- [ ] 明确知识源类型
- [ ] 明确评审维度
- [ ] 明确结构化评审输出 schema
- [ ] 准备最小演示数据集
- [ ] 起草最小 golden set

### Phase 1：先定项目骨架

- [ ] 明确最终目录结构
- [ ] 明确 `core / domain / services / api` 分层
- [ ] 设计项目级 schemas
- [ ] 设计领域级 schemas
- [ ] 明确服务层划分
- [ ] 明确 API 边界
- [ ] 明确前端页面结构

### Phase 2：打通知识接入链路

- [ ] 支持 `.md / .txt / .pdf / .docx`
- [ ] 完成 load / normalize / split
- [ ] 完成 metadata
- [ ] 完成 stable ids
- [ ] 完成文档入库前检查
- [ ] 完成文档类型识别

### Phase 3：打通索引链路

- [ ] 完成 `embed_documents`
- [ ] 完成 store `upsert`
- [ ] 完成文档替换与删除的最小能力
- [ ] 完成单知识库索引构建
- [ ] 补充按知识源类型过滤的保留位

### Phase 4：打通检索与生成链路

- [ ] 完成 `embed_query`
- [ ] 完成基础 retrieval
- [ ] 完成 `threshold`
- [ ] 可选完成 `mmr`
- [ ] 完成 context selection
- [ ] 完成评审问答 prompt builder
- [ ] 完成结构化评审 prompt builder
- [ ] 接入真实 LLM
- [ ] 返回 `answer + sources`
- [ ] 返回 `review_report + sources`
- [ ] 完成 refusal

### Phase 5：补 API

- [ ] 文档管理接口
- [ ] 检索预览接口
- [ ] 评审问答接口
- [ ] 结构化评审接口
- [ ] 可选流式接口
- [ ] 评估接口

### Phase 6：补前端工作台

- [ ] 文档面板
- [ ] chunk 面板
- [ ] 检索实验面板
- [ ] 评审问答面板
- [ ] 结构化评审面板
- [ ] 评估结果面板

### Phase 7：补最小评估闭环

- [ ] 固定 golden set
- [ ] retrieval eval
- [ ] review output eval
- [ ] end-to-end rag eval
- [ ] bad case review

### Phase 8：补项目说明与演进路线

- [ ] README
- [ ] 运行方式
- [ ] 评估方式
- [ ] 当前支持什么
- [ ] 当前不支持什么
- [ ] 后续向多模态需求理解、原型辅助、代码生成扩展的演进说明

---

## 十二、项目完成标准

项目完成后，至少应该满足：

- 能清楚展示完整 RAG 数据流
- 能自然体现 `02_llm + 04_rag` 的衔接
- 能通过前端图形化操作主链路
- 能通过 API 复用同一套 RAG 内核
- 能对需求相关问题输出稳定的 `answer + sources`
- 能生成结构化评审报告
- 能对证据不足的问题拒答或给出待补充信息提示
- 能运行最小评估闭环
- 核心模块能作为未来“需求理解底座”复用
- 后续接入多模态、原型、代码生成时，不需要推倒核心 RAG 模块

---

## 十三、最终判断

这个项目的正确方向不是：

- 为了像企业产品而过早堆复杂度
- 一上来就做审批流、权限系统、任务编排、原型生成和代码生成

而是：

- 用当前已经掌握的知识，把“企业内部需求提效评审”这个真实场景做成一个架构清楚、边界清楚、可视化清楚、未来可扩展的项目

当前版本的正确目标是：

> 做一个轻量实现、企业级演进对齐的“企业内部需求提效评审助手”。

这个定位能自然承接你后面的学习路线：

- 现在：先把 `LLM + RAG + API + UI + Eval` 做扎实
- 后面：再把多模态、Agent、原型辅助、代码生成逐步接进来
