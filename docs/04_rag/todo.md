# 综合 RAG 项目 Todo

> 目标：基于当前已经掌握的 `02_llm + 04_rag` 能力，做一个可运行、可评估、可视化操作的综合 RAG 项目。
> 当前版本不做企业知识库产品，但项目架构、模块边界和演进方向要向企业级知识库对齐，保证后续扩展时核心 RAG 模块可以复用。

---

## 一、项目定位

- 这是一个**固定 RAG 主链路项目**
- 这是一个**教学型、可落地、可扩展的项目**
- 这不是：
  - Agent 项目
  - LangGraph 项目
  - 企业后台管理系统
  - 多租户知识平台
  - 重型工程框架演示

这个项目的核心价值不是“功能堆得多”，而是：

- 用当前已经掌握的知识，把 `LLM -> RAG -> API -> UI` 串成一条完整主线
- 把模块边界设计清楚，避免后续一扩展就推倒重来
- 让当前实现保持克制，但让未来升级方向明确

---

## 二、项目总目标

### 1. 当前的目标

- 跑通完整固定 RAG 主链路
- 自然复用 `02_llm` 的真实模型调用能力
- 保持 `04_rag` 各章节已经建立的对象边界
- 提供一层 `FastAPI` 接口
- 提供一个 `Vite + React` 的可视化操作台
- 让用户可以图形化观察和操作 RAG 的关键步骤
- 保留最小评估闭环，而不是只做一个“能回答”的 demo

### 2. 架构的目标

- 当前实现轻量
- 核心 RAG 模块可复用
- API 层足够支持业务
- 前端只负责交互与可视化，不承载 RAG 核心逻辑
- 将来向企业级知识库扩展时，只需要补充相关技术栈和外围基础设施

---

## 三、项目设计原则

- **主链路优先**：先保证 `document -> chunk -> embedding -> store -> retrieval -> context -> llm -> answer + sources` 完整成立
- **边界优先**：先把对象、模块、输入输出契约设计清楚，再考虑增加功能
- **复用优先**：尽量复用 `02_llm` 和 `04_rag` 已有心智模型，不额外引入过重概念
- **可扩展优先**：当前不实现的企业能力，要在结构上预留扩展点
- **可观察优先**：前端不只是“聊天框”，而是要能看到文档、chunk、检索结果、来源和评估

---

## 四、当前版本范围

### 1. 必做

- 文档接入：支持 `.md / .txt / .pdf`
- 文档切分与 `metadata`
- `stable document_id / chunk_id`
- `embedding` 生成
- 向量存储
- 基础检索
- context selection
- RAG prompt 组织
- 真实 LLM 生成
- `answer + sources`
- refusal
- 最小 golden set
- 最小 retrieval / end-to-end eval
- `FastAPI` 后端接口
- `Vite + React` 可视化前端

### 2. 可选，建议加上

- `threshold`
- `mmr`
- `hybrid` 作为实验性保留项
- mock / real LLM 双路径
- 普通问答接口和流式问答接口

### 3. `V1` 明确不做

- Agent
- LangGraph
- GraphRAG
- 多租户
- ACL 权限控制
- 审计系统
- 异步任务编排平台
- 对象存储接入
- 数据库持久化治理体系
- 企业级监控告警
- 复杂前端后台系统

---

## 五、项目主链路

项目必须围绕下面这条固定链路展开：

```text
document
-> load
-> normalize
-> split
-> metadata + stable ids
-> embed_documents
-> vector store
-> retrieve
-> context selection
-> prompt
-> llm
-> answer + sources
-> eval
```

这条链路里：

- `02_llm` 主要贡献：
  - provider config
  - OpenAI-compatible client
  - messages 组织
  - prompt 工程能力
  - 结构化输出认知
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

## 六、后端架构规划

后端固定使用：

- `Python`
- `FastAPI`

后端目标不是把所有逻辑塞进路由，而是做成“可复用 RAG 内核 + 薄 API 壳”。

### 1. 建议目录结构

```text
rag_lab/
├── README.md
├── app/
│   ├── config/
│   ├── schemas/
│   ├── llm/
│   ├── ingestion/
│   ├── embeddings/
│   ├── store/
│   ├── retrieval/
│   ├── generation/
│   ├── evals/
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
- 尽量复用当前课程已经建立的对象边界
- 项目内任何模块通信都尽量先过 schema

建议重点统一：

- `SourceDocument`
- `SourceChunk`
- `EmbeddedChunk`
- `RetrievalResult`
- `RagAnswer`
- `SourceCitation`
- `GoldenSetCase`
- `ExperimentConfig`

#### `llm/`

- 复用 `02_llm` 的最小真实调用能力
- 收敛 provider config 和 client 初始化
- 统一普通生成和流式生成入口
- 保留 mock fallback 的扩展位

最小职责：

- `create_client()`
- `chat()`
- `chat_stream()`
- generation result normalize

#### `ingestion/`

- 处理文档进入系统的完整输入层
- 保持对 `loader / splitter / metadata / stable id` 的独立封装

最小职责：

- discover
- load
- normalize
- split
- build metadata
- build stable ids

#### `embeddings/`

- 保持 `embed_documents / embed_query` 的区分
- 明确 embedding space 一致性

最小职责：

- documents embedding
- query embedding
- provider/model/dimensions 校验

#### `store/`

- 提供最小存储层契约
- 保证后续替换存储实现时，上层 retrieval 不被迫重写

最小职责：

- `upsert`
- `replace_document`
- `delete_document`
- `similarity_search`
- metadata filter 扩展位

#### `retrieval/`

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

#### `generation/`

- 负责从 `RetrievalResult[]` 到最终 `answer + sources`
- 明确生成层和检索层是两个不同责任区域

最小职责：

- context selection
- context formatter
- prompt builder
- refusal policy
- `answer + sources`

#### `evals/`

- 负责最小评估闭环
- 保证这个项目不仅“能回答”，还“能回归”

最小职责：

- golden set
- retrieval eval
- end-to-end rag eval
- bad case review

#### `services/`

- 项目级编排层
- 负责串接 ingestion、store、retrieval、generation、evals
- 保证 CLI、API、前端都复用同一套服务层能力

建议拆成：

- `DocumentService`
- `IndexService`
- `RagQueryService`
- `EvaluationService`

#### `api/`

- `FastAPI` 薄路由层
- 只做请求校验、调用 service、返回响应
- 不在这里写 RAG 细节

---

## 七、前端规划

前端固定使用：

- `Vite`
- `React`

前端定位不是“企业知识库前台”，而是：

> 一个用于图形化操作和观察 RAG 主链路的工作台。

### 1. 前端必须解决什么

- 用户可以导入文档
- 用户可以看到文档被切成什么样
- 用户可以看到当前检索策略和检索结果
- 用户可以看到哪些 chunk 被送进上下文
- 用户可以看到最终答案和来源
- 用户可以看到最小评估结果

### 2. 建议页面/面板

#### 文档面板

- 上传文档
- 文档列表
- 文档基础信息
- 当前索引状态

#### Chunk 面板

- 展示 chunk 列表
- 展示 chunk metadata
- 展示 `document_id / chunk_id`

#### 检索面板

- 输入 query
- 选择检索策略
- 设置 `top_k / threshold / mmr` 等参数
- 查看召回结果与分数

#### 生成面板

- 查看被选中的 context
- 查看最终 answer
- 查看 refusal
- 查看 sources

#### 评估面板

- 运行最小 golden set
- 展示 retrieval 指标
- 展示 end-to-end 结果
- 展示 bad cases

### 3. 前端边界

- 前端不直接承载检索和生成逻辑
- 前端不引入复杂状态机
- 前端不提前做后台系统能力
- 前端只围绕观察、操作、验证 RAG 主链路服务

---

## 八、API 规划

API 以项目演示和前端对接为目标，不追求完整企业接口体系。

### 1. 文档相关

- 上传文档
- 查看文档列表
- 查看单文档详情
- 删除文档
- 触发索引构建 / 重建

### 2. 检索与问答相关

- 检索预览接口
- RAG 问答接口
- 可选流式问答接口

### 3. 评估相关

- 查看 golden set
- 运行 retrieval eval
- 运行 rag eval
- 查看最近评估结果

### 4. API 原则

- 路由薄
- 请求响应对象清楚
- 统一复用 service
- 统一复用 schema

---

## 九、企业级对齐的扩展预留

当前版本不实现下面这些能力，但项目设计必须向这些方向对齐。

### 1. 多知识库 / namespace

当前可以先做单知识库。

但结构上要预留：

- `knowledge_base_id`
- namespace
- 按知识库隔离索引和文档

这样未来扩展多知识库时，核心 ingestion / retrieval / generation 不需要重写。

### 2. 文档版本与删除一致性

当前先做最小 `replace_document / delete_document`。

但结构上要对齐未来需求：

- 文档版本
- 增量更新
- 删除一致性
- 重新索引

### 3. metadata filter 向 ACL 演进

当前 `V1` 只做基础 metadata filter。

但未来可以向下扩展：

- 文档范围过滤
- 部门过滤
- 用户权限过滤
- ACL 规则映射

也就是说，当前 retrieval 设计不能把 filter 写死成只能按文件名过滤。

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
- hosted search / 混合索引

所以 retrieval 层要是“策略层”，而不是单函数脚本。

### 5. 同步索引向异步任务扩展

当前可以同步构建索引。

但未来企业级方向通常需要：

- 异步 ingestion
- 任务队列
- 任务状态跟踪
- 批量导入

所以服务层和 API 层需要为异步化留出演进空间。

### 6. 本地存储向对象存储扩展

当前可以用本地文件。

未来可以扩展到：

- OSS / S3
- 文档归档
- 预处理缓存

因此文档输入层应该尽量保持“文件来源抽象”，不要把路径逻辑写死到业务层。

### 7. 单机配置向多环境配置扩展

当前只需要最小配置管理。

未来可以扩展：

- dev / test / prod
- provider 切换
- embedding model 切换
- store backend 切换

因此配置层需要从一开始就独立。

### 8. 最小评估向企业观测扩展

当前只做：

- golden set
- retrieval eval
- rag eval
- bad cases

未来才扩展：

- 日志观测
- trace
- 线上反馈回流
- 回归报告

这意味着现在就要把评估当成独立模块，而不是散落脚本。

---

## 十、项目阶段规划

### Phase 1：先定项目骨架

- [ ] 明确项目名称
- [ ] 明确最终目录结构
- [ ] 设计项目级 schemas
- [ ] 明确服务层划分
- [ ] 明确 API 边界
- [ ] 明确前端页面结构

### Phase 2：打通知识接入链路

- [ ] 支持 `.md / .txt / .pdf`
- [ ] 完成 load / normalize / split
- [ ] 完成 metadata
- [ ] 完成 stable ids
- [ ] 完成文档入库前检查

### Phase 3：打通索引链路

- [ ] 完成 `embed_documents`
- [ ] 完成 store `upsert`
- [ ] 完成文档替换与删除的最小能力
- [ ] 完成单知识库索引构建

### Phase 4：打通检索与生成链路

- [ ] 完成 `embed_query`
- [ ] 完成基础 retrieval
- [ ] 完成 context selection
- [ ] 完成 prompt builder
- [ ] 接入真实 LLM
- [ ] 返回 `answer + sources`
- [ ] 完成 refusal

### Phase 5：补 API

- [ ] 文档管理接口
- [ ] 检索预览接口
- [ ] 问答接口
- [ ] 可选流式问答接口
- [ ] 评估接口

### Phase 6：补前端工作台

- [ ] 文档面板
- [ ] chunk 面板
- [ ] 检索实验面板
- [ ] 生成结果面板
- [ ] 评估结果面板

### Phase 7：补最小评估闭环

- [ ] 固定 golden set
- [ ] retrieval eval
- [ ] end-to-end rag eval
- [ ] bad case review

### Phase 8：补项目说明与演进路线

- [ ] README
- [ ] 运行方式
- [ ] 评估方式
- [ ] 当前支持什么
- [ ] 当前不支持什么
- [ ] 后续向企业知识库扩展的演进说明

---

## 十一、项目完成标准

项目完成后，至少应该满足：

- 能清楚展示完整 RAG 数据流
- 能自然体现 `02_llm + 04_rag` 的衔接
- 能通过前端图形化操作主链路
- 能通过 API 复用同一套 RAG 内核
- 能输出稳定的 `answer + sources`
- 能对无答案问题拒答
- 能运行最小评估闭环
- 核心模块能作为未来企业知识库底座复用

---

## 十二、最终判断

这个项目的正确方向不是：

- 为了像企业产品而过早堆复杂度

而是：

- 用当前已经掌握的知识，把固定 RAG 做成一个架构清楚、边界清楚、可视化清楚、未来可扩展的项目

当前版本的正确目标是：

> 做一个轻量实现、企业级演进对齐的综合 RAG 项目。

