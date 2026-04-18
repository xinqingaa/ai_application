# 01. RAG 基础概念

> 本节目标：理解 RAG 解决什么问题、默认应该如何做架构判断，并能对着 `phase_1_scaffold` 的骨架代码看懂这门课后续会如何展开。

---

## 1. 概述

### 学习目标

完成本章后，你应该能够：

- 能解释 RAG 解决什么问题，以及它不解决什么问题
- 能区分长上下文、直接查现有知识系统、固定 `2-step RAG` 和 `Agentic RAG`
- 能画出最小 `2-step RAG` 数据流，并说明每一步在做什么
- 能运行 `phase_1_scaffold` 的主示例脚本，并看懂输出在表达什么
- 能说明 `SourceChunk / RetrievalResult / AnswerResult` 这三个核心对象的职责
- 能说清第一章为什么先做项目骨架，而不是直接实现完整问答系统

### 本章在 `04_rag` 中的位置

本章是 `04_rag` 的入口章节，负责先建立三种能力：

1. 架构判断力
2. 学习路线感
3. 项目骨架感

后续章节会继续沿着这条主线展开：

- 第二章：文档如何进入系统
- 第三章：文本如何变成向量
- 第四章：向量如何进入存储和检索
- 第五章：检索效果不好时先调哪里
- 第六章：如何把检索结果接成真正的回答
- 第七章：如何评估链路变化是否真的变好

### 学习前提

建议你至少已经具备下面这些基础：

- 已完成 [02_llm/outline.md](/Users/linruiqiang/work/ai_application/docs/02_llm/outline.md) 的主线内容
- 已理解 [03_foundation/outline.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/outline.md) 中的 `Document / Retriever / Runnable`
- 已经知道 Prompt、上下文窗口、结构化输出、成本和错误处理这些概念

### 本章边界

本章重点解决的是：

1. 什么是 RAG
2. 什么情况下应该先考虑 RAG
3. 为什么本课程默认主线是固定 `2-step RAG`
4. 为什么第一章先搭骨架，而不是直接写完整系统

本章不展开：

- 真实向量数据库接入
- 真实 Embedding 模型接入
- 混合检索、Rerank、HyDE、多查询
- 完整 RAG Chain、API 服务、流式输出
- `Agentic RAG` 的实现

如果第一章就把这些内容全塞进来，读者只会看到一堆组件，而很难抓住主线。

### 第一入口

本章有两个入口，职责不同：

- 第一阅读入口：
  [source/04_rag/labs/phase_1_scaffold/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/README.md)
- 第一运行入口：
  [scripts/query_demo.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/scripts/query_demo.py)

为什么这样安排：

- `README` 先帮你建立目录职责和阅读顺序
- `query_demo.py` 先让你看到“retriever -> prompt -> answer”这条最小闭环

---

## 2. 先回到大纲：这一章到底要回答什么 📌

这一章必须始终服从 [outline.md](/Users/linruiqiang/work/ai_application/docs/04_rag/outline.md) 的学习路线。

对照大纲，本章核心只回答两类问题：

1. 什么是 RAG
2. 什么情况下该用什么方案

### 2.1 什么是 RAG

一句话说：

> RAG 是把“知识检索”接到“模型生成”前面的系统链路。

最小流程长这样：

```text
文档 -> 切分 -> 索引
用户问题 -> 检索 -> 上下文 -> LLM -> 答案
```

这件事重要的原因不是“又多了一个步骤”，而是：

- 知识可以更新
- 回答可以引用来源
- 不必把所有知识都塞进模型参数里
- 能把“知识问题”和“模型能力问题”分开处理

### 2.2 RAG 解决的到底是什么问题

RAG 重点解决的是下面这四类问题：

1. **知识更新问题**
   文档变了，不应该靠重新训练模型才能生效。
2. **来源追溯问题**
   真实业务里，很多回答必须知道“答案来自哪里”。
3. **幻觉控制问题**
   模型在没有依据时容易自由发挥，RAG 至少能给它一个受约束的上下文。
4. **知识规模问题**
   文档一多，就不可能长期靠手工复制进 Prompt。

但 RAG 也不解决这些问题：

- 模型本身推理能力不足
- 业务规则本身定义不清
- 输入文档质量很差
- 你根本没有可用知识源

### 2.3 RAG、长上下文和微调怎么区分

| 方案 | 更适合什么情况 | 不适合什么情况 |
|------|----------------|----------------|
| 长上下文 | 材料少、问题少、一次性分析 | 文档多、更新频繁、要长期维护 |
| 固定 `2-step RAG` | 有文档库、要引用来源、要持续更新 | 结构化数据查询明显更合适的场景 |
| 微调 | 想学风格、格式、行为模式 | 希望频繁更新外部知识 |

你当前阶段最需要建立的判断不是“哪种方案最强”，而是：

> 先用问题类型判断方案，再选技术，而不是先选技术再给它找问题。

### 2.4 一个最小 `2-step RAG` 数据流长什么样

大纲里的默认主线可以先压缩成这张图：

```text
原始文档
-> 切分为 chunks
-> 放入检索系统

用户问题
-> retriever 召回相关 chunks
-> 把 chunks 组织成上下文
-> LLM 基于上下文生成答案
```

这里先记住三个最小对象：

- `chunk`
  文档被切分后的最小检索单位
- `retrieval result`
  被召回的 chunk，以及它的分数等信息
- `answer result`
  最终返回给调用方的答案和来源

### 2.5 为什么第一章不直接做 `Agentic RAG`

因为这门课当前主线不是“动态决策”，而是“稳定固定链路”。

正确的默认顺序应该是：

1. 先判断能不能直接用长上下文
2. 再判断能不能直接查现有系统
3. 默认先把固定 `2-step RAG` 做稳
4. 检索不稳时再加混合检索、Rerank、查询变换
5. 只有固定链路明显不够时，才升级到 `Agentic RAG`

这也是本章为什么只做概念和骨架，不做复杂编排。

---

## 3. RAG 架构选型与边界判断 📌

这一节对应大纲里“RAG 架构选型与边界判断”的内容。

### 3.1 默认决策顺序

遇到一个知识型需求时，建议先按这个顺序判断：

1. **能不能直接用长上下文**
   如果材料很少，而且只是一次性分析，先别急着建索引。
2. **能不能直接查现有系统**
   如果 FAQ 已经在 Elasticsearch、SQL、CMS 里，优先复用已有系统。
3. **默认优先做固定 `2-step RAG`**
   这是本课程的主线，也是大多数场景最稳的起点。
4. **检索效果不稳时再加策略**
   例如混合检索、Rerank、多查询、上下文压缩。
5. **固定链路明显不够时再考虑 `Agentic RAG`**
   例如需要自动改写查询、拆分子问题、多知识源动态路由。

### 3.2 什么情况下先别做 RAG

下面这些场景，不应该一上来就做向量库：

- 用户只上传极少量文件，目的是快速做一次性问答 Demo
- 数据本来就是结构化查询问题
- 没有稳定文档来源，知识内容本身经常缺失或冲突
- 团队当前连最小评估集都还没有

### 3.3 什么情况下固定 `2-step RAG` 最适合

固定 `2-step RAG` 很适合下面这些场景：

- 企业知识库问答
- 产品手册问答
- 制度文档问答
- 需要“答案 + 来源”的引用式回答

这类场景的共同点通常是：

- 文档是主要知识源
- 文档会更新
- 需要明确来源
- 系统需要持续维护

### 3.4 本章最容易出现的判断误区

1. **把所有知识问题都理解成 RAG 问题**
   这是最常见的错误。很多时候直接查现有系统更好。
2. **还没把固定链路做稳，就急着上 Agent**
   这会把问题复杂化，而不是解决问题。
3. **只关心“能不能回答”，不关心“答案依据来自哪里”**
   这样会很快失去 RAG 的工程价值。
4. **没有最小评估集，却已经开始调 chunk 和检索参数**
   这会让后续优化全部变成“凭感觉”。

---

## 4. 第一章对应代码怎么读 📌

### 4.1 为什么第一章只有骨架代码

第一章的代码快照是：

- `source/04_rag/labs/phase_1_scaffold/`

它的作用不是实现完整 RAG，而是先把后续章节会不断扩展的接口面定下来。

第一章真正要先稳定的是：

- 配置入口
- 公共数据结构
- 最小 chunk 生产链路
- retriever 协议
- prompt 构造入口
- service 入口
- 最小测试和占位脚本

这和大纲中的学习路线是一致的：

> 先理解 RAG 的形状，再逐章补实现，而不是第一章就堆完整系统。

### 4.2 为什么项目目录要这样规划

这一章的代码不是随便把文件分散开，而是在提前回答一个项目设计问题：

> 一个最小 RAG 系统，哪些东西应该先稳定，哪些东西应该留成后续扩展点？

`phase_1_scaffold/` 顶层目录这样拆，核心是为了把职责先分开：

| 目录 | 为什么单独存在 | 后续会继续长成什么 |
|------|----------------|--------------------|
| `app/` | 放项目内核，承载后续真正会被复用的模块 | 最终会长成完整 RAG 内核 |
| `scripts/` | 放第一运行入口和调试入口，保证先有可观察输出 | 每章都可以继续补当前阶段脚本 |
| `tests/` | 放最小验收，避免骨架只是“看起来有结构” | 后续会继续补模块测试和回归测试 |
| `evals/` | 提前为 Golden Set 和实验资产留位置 | 第七章会真正用起来 |
| `data/` | 放样例输入和本地文档 | 第二章开始会真正消费文档数据 |

如果不这样拆，最容易出现两个问题：

1. 所有逻辑都堆进一个大脚本，第一章能跑，但后面很难扩展
2. 代码入口、调试脚本、服务逻辑和测试全混在一起，学习路径会立刻变乱

也就是说，这种目录规划不是为了“显得工程化”，而是为了：

- 先把可复用内核和一次性脚本分开
- 先把学习入口和未来扩展点分开
- 让后续章节知道应该往哪个目录继续长

### 4.3 代码设计层面怎么理解这些目录

更关键的是 `app/` 里的子目录为什么这样拆。

第一章虽然很多模块还是占位，但目录边界已经在告诉你：

- 哪些是稳定对象
- 哪些是中间流程
- 哪些是基础设施
- 哪些是对外入口

| 模块 | 当前职责 | 为什么单独一层 |
|------|----------|----------------|
| `config.py` | 放默认目录、chunk 参数、top_k 等全局配置 | 配置会跨模块复用，不应该散在脚本里 |
| `schemas.py` | 放 `SourceChunk / RetrievalResult / AnswerResult / EvalSample` | 数据结构一旦稳定，后续模块才能围绕同一对象协作 |
| `ingestion/` | 负责文件类型识别、文本切分、metadata 基础处理 | “文档进入系统”应该单独成层，避免和检索/生成耦合 |
| `indexing/` | 负责稳定 `document_id / chunk_id` 和 chunk 准备流程 | 这层把“原始文本”变成“标准 chunk 对象” |
| `embeddings/` | 负责 query/document embedding 抽象 | 后续模型可以替换，但外层接口应该先稳定 |
| `vectorstores/` | 负责向量存储和相似度搜索 | 向量库是基础设施层，不应直接写死在服务层 |
| `retrievers/` | 负责定义检索协议 | 先把检索输入输出形状固定下来，后续才能替换策略 |
| `prompts/` | 放 Prompt 资产 | Prompt 不应该长期写死在脚本和服务入口里 |
| `chains/` | 把检索结果组织成模型可消费链路 | 这一层是“上下文 -> Prompt -> 模型输入”的组合层 |
| `services/` | 对外收束成稳定调用入口 | 最终 CLI、API、任务脚本都应该复用服务层 |
| `evaluation/` | 放最小评估对象和方法 | 评估必须从第一天就有位置，不能最后再补 |
| `api/` | 预留传输层入口 | API 是对外壳层，必须晚于核心链路稳定 |
| `observability/` | 预留日志和观测 | 观测不该和业务逻辑混在一起 |

从代码设计角度看，这套分层实际在保护四件事：

1. **稳定对象先于复杂实现**
   先把配置、对象和协议定住，后续实现才不会反复推翻接口。
2. **中间流程先于外部入口**
   先有 `ingestion / indexing / retrievers / chains / services`，再谈 API、工作流和项目整合。
3. **基础设施和业务主线分离**
   向量存储、日志、API 都是基础设施，不应该抢走第一章主线。
4. **学习入口和实现内核分离**
   `scripts/` 是观察入口，`app/` 是真正要持续长大的内核。

这也是为什么第一章即使还没“做成”，目录设计本身仍然值得讲。

### 4.4 本章代码映射表

| 文档部分 | 对应代码/文档 | 角色 | 说明 |
|----------|---------------|------|------|
| 本章第一阅读入口 | [phase_1_scaffold/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/README.md) | 主入口 | 先理解目录职责、运行方式和阅读顺序 |
| 最小 RAG 闭环 | [scripts/query_demo.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/scripts/query_demo.py) | 主示例文件 | 先看到 `retriever -> prompt -> answer` 的占位闭环 |
| chunk 形状 | [scripts/inspect_chunks.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/scripts/inspect_chunks.py) | 扩展示例 | 先看到 `SourceChunk`、`chunk_id` 和 metadata 长什么样 |
| 配置入口 | [app/config.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/config.py) | 核心配置 | 提前定义 chunk 参数、目录和默认检索参数 |
| 核心对象 | [app/schemas.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/schemas.py) | 核心数据结构 | 定义 `SourceChunk / RetrievalResult / AnswerResult / EvalSample` |
| 检索抽象 | [app/retrievers/base.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/retrievers/base.py) | 接口定义 | 先把 retriever 的输入输出形状固定下来 |
| 文本转 chunk | [app/indexing/index_manager.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/indexing/index_manager.py) | 核心流程 | 把文本、metadata 和稳定 ID 合并成标准 chunk |
| Prompt 组织 | [app/chains/rag_chain.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/chains/rag_chain.py) | 核心流程 | 把检索结果渲染成模型可消费的上下文 |
| 服务入口 | [app/services/rag_service.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/services/rag_service.py) | 项目入口 | 收束 retriever 和回答结构，形成 `ask()` 入口 |
| 最小验证 | [tests/test_scaffold.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/tests/test_scaffold.py) | 验收入口 | 保证配置和评估占位模块不是死文件 |

### 4.5 为什么这些文件值得先看

先看它们，是因为这几类文件分别代表后续课程会不断扩展的稳定接口：

- `config.py`
  后续章节会继续增加模型、检索、评估等配置项
- `schemas.py`
  后续所有模块都会围绕这些对象交换数据
- `index_manager.py`
  第二章会沿着这里继续做真正的文档处理
- `rag_chain.py`
  第六章会沿着这里继续长成真正的 RAG Chain
- `rag_service.py`
  项目级入口最终一定会回到服务层

---

## 5. 推荐学习顺序 📌

这部分是强制顺序，不建议跳着读。

### 第一步：先回看大纲里的对应部分

先读：

- [outline.md](/Users/linruiqiang/work/ai_application/docs/04_rag/outline.md) 中：
  `开始前：先建立最小评估集`
- [outline.md](/Users/linruiqiang/work/ai_application/docs/04_rag/outline.md) 中：
  `一、RAG 基础概念`

这一步的目的不是背大纲，而是先知道：

- 本章在整门课里负责什么
- 为什么本课程默认主线是固定 `2-step RAG`

### 第二步：打开第一阅读入口

读：

- [phase_1_scaffold/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/README.md)

这一步先解决三个问题：

1. 目录有哪些部分
2. 当前能运行什么
3. 第一章为什么只是骨架

### 第三步：先跑主示例文件

运行：

```bash
cd source/04_rag/labs/phase_1_scaffold
python3 scripts/query_demo.py
```

先建立“最小 RAG 闭环”的直觉，再回头读代码。

### 第四步：再跑 chunk 检查脚本

运行：

```bash
python3 scripts/inspect_chunks.py
```

这一步先看到：

- 一个 chunk 到底长什么样
- `chunk_id` 和 metadata 怎么组织

### 第五步：再读核心文件

建议按这个顺序：

1. [app/config.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/config.py)
2. [app/schemas.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/schemas.py)
3. [app/retrievers/base.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/retrievers/base.py)
4. [app/indexing/index_manager.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/indexing/index_manager.py)
5. [app/chains/rag_chain.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/chains/rag_chain.py)
6. [app/services/rag_service.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/services/rag_service.py)

### 第六步：最后跑占位入口和测试

运行：

```bash
python3 scripts/build_index.py
python3 -m unittest discover -s tests
```

这一步的目的不是看功能，而是确认：

- 第一章骨架可运行
- 最小测试闭环存在
- 后续章节有明确扩展入口

### 卡住时先回看哪里

如果中途卡住，先回看这三个位置：

1. [outline.md](/Users/linruiqiang/work/ai_application/docs/04_rag/outline.md)
2. [phase_1_scaffold/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/README.md)
3. 本章的“代码映射表”和“第一运行入口”两节

### 最低通过标准

至少要做到：

1. 能跑通三个脚本和最小测试
2. 能说清主示例脚本在模拟什么链路
3. 能说清本章代码和后续章节的扩展关系

---

## 6. 这套骨架后续要按什么步骤实施 📌

### 6.1 为什么实施顺序不能反过来

这一章最容易低估的一点是：

> RAG 项目不是“把组件一个个装上去”就行，而是必须按依赖顺序长出来。

如果顺序反了，常见问题会非常多：

- 没有统一 `schemas` 就先做检索，后面对象形状会反复改
- 没有稳定 chunk 生产链路就先做 embedding，后面索引会失去一致性
- 没有服务层边界就先做 API，后面传输层会绑死内部实现
- 没有评估入口就先调检索，后面所有优化都无法验证

所以正确顺序不是“哪个看起来最酷先做哪个”，而是：

> 先把输入对象和中间层稳定下来，再补基础设施，最后补外部入口。

### 6.2 从骨架到完整 RAG 的建议实施顺序

可以把后续实施顺序理解成下面这张表：

| 步骤 | 先做什么 | 主要落在哪些模块 | 这一层解决什么问题 |
|------|----------|------------------|--------------------|
| 1 | 稳定配置、对象和协议 | `config.py`、`schemas.py`、`retrievers/base.py` | 先统一系统里“数据长什么样” |
| 2 | 实现文档进入系统 | `ingestion/`、`indexing/` | 把原始文件变成稳定 chunk 列表 |
| 3 | 接入 Embedding | `embeddings/` | 把文本和查询变成可比较的向量 |
| 4 | 接入向量存储 | `vectorstores/` | 把 chunk + vector 放进可检索存储 |
| 5 | 做基础检索和检索策略 | `retrievers/`、`vectorstores/` | 让问题能召回相关 chunk |
| 6 | 接上 Prompt、Chain 和 Service | `prompts/`、`chains/`、`services/` | 让检索结果真正变成“答案 + 来源” |
| 7 | 建立评估和回归 | `evaluation/`、`evals/` | 让链路变化可验证、可比较 |
| 8 | 再补 API 和观测 | `api/`、`observability/` | 把稳定内核暴露成服务，而不是反过来 |
| 9 | 做项目整合和最终收口 | `phase_9`、`rag_lab/` | 把前面各层收束成完整最小项目 |

### 6.3 为什么这些目录在第一章就先出现

第一章里你已经能看到：

- `embeddings/`
- `vectorstores/`
- `evaluation/`
- `api/`
- `observability/`

它们现在还不是完整实现，但先出现有两个好处：

1. **后续扩展方向提前可见**
   读者不会误以为第一章的骨架就是最终结构。
2. **边界先于实现**
   后面每一章只是在往既定边界里补真实能力，而不是重新改目录。

也就是说，这些目录现在更像“未来的插槽”，不是“已经完成的能力”。

### 6.4 如果你来继续实现，应该先补哪几层

如果你接着做 `Phase 2` 以后，建议按这个局部顺序推进：

1. 先把 `loaders.py` 真正实现起来
2. 再把 `splitters.py` 从占位逻辑升级为更真实的切分
3. 再把 `index_manager.py` 和 `id_generator.py` 变成稳定索引入口
4. 然后再接 `embeddings/` 和 `vectorstores/`
5. 检索通了以后，再让 `rag_chain.py` 和 `rag_service.py` 接真实模型
6. 最后再接 `evaluation/`、`api/` 和观测

这个顺序本质上是在遵守一条规则：

> 先把“文档如何进来”和“对象如何稳定”做对，再去做“模型怎么回答”。

---

## 7. 第一运行入口：先跑 `query_demo.py` 📌

### 7.1 运行前提

这一章不需要真实 API Key。

因为 `query_demo.py` 使用的是 `MockRetriever`，它的目的是先让你看懂最小数据流，而不是测试真实模型效果。

运行目录：

```bash
cd source/04_rag/labs/phase_1_scaffold
```

### 7.2 运行命令

```bash
python3 scripts/query_demo.py
```

### 7.3 预期输出

你应该看到类似下面的输出：

```text
Phase 1 scaffold only. Replace this placeholder with a real LLM call in Phase 4.

Prompt preview:
你是一个基于检索上下文回答问题的助手。
如果上下文中没有足够信息，请明确说不知道。
回答时优先引用可见来源，不要编造事实。

上下文：
[source=demo] Mock context for question: What should be implemented next?

问题：What should be implemented next?
Sources: ['demo']
```

### 7.4 第一次跑它时要重点观察什么

重点观察这四件事：

1. 现在还没有真实 LLM 调用
2. 但 `Prompt preview` 已经暴露了最终模型输入的形状
3. `Sources` 已经说明最终回答结构不只是一段文本
4. 整个流程已经有了 `retriever -> prompt -> answer` 的主链路

### 7.5 为什么它是第一运行入口

因为它最适合先建立整章直觉：

- `build_index.py` 太偏占位提示
- `inspect_chunks.py` 更偏数据结构观察
- `query_demo.py` 最接近真正的 RAG 主链路

所以第一章应该先用它建立整体感，再回头拆解代码。

### 7.6 再跑两个辅助脚本

#### `inspect_chunks.py`

运行：

```bash
python3 scripts/inspect_chunks.py
```

你会看到类似输出：

```text
Prepared 1 chunk(s).
df01139fe9617e6a9d81a290ba2eb4c0d726b727:0:a3c96f83edae {'source': 'data/sample.md', 'filename': 'sample.md', 'suffix': '.md', 'chunk_index': 0}
```

这里重点看：

- `chunk_id` 的形状
- metadata 至少包含哪些字段
- 为什么 chunk 不是一个裸字符串

#### `build_index.py`

运行：

```bash
python3 scripts/build_index.py
```

你会看到类似输出：

```text
Phase 1 scaffold ready.
Next step: implement ingestion and indexing in Phase 2.
Data directory: data
```

这里重点看：

- 第一章明确只验证骨架入口
- 第二章才开始真正实现文档处理和索引构建

---

## 8. 核心对象和最小链路应该怎么理解

### 8.1 `SourceChunk`

一句话说：

> `SourceChunk` 是文档进入 RAG 系统后的最小标准对象。

为什么重要：

- 检索系统最终不是在“查字符串”，而是在查 chunk 对象
- chunk 必须同时携带内容、来源和 ID
- 后续来源引用、删除一致性、增量更新都离不开它

最小字段：

- `chunk_id`
- `document_id`
- `content`
- `metadata`

常见误区：

- 把 chunk 只理解成一段文本
- 不关心 `document_id / chunk_id`
- 先做检索，再想 metadata 怎么补

与后续章节的关系：

- 第二章会继续扩展 chunk 的生成过程
- 第四章和第五章会继续消费这个对象做检索和排序

### 8.2 `RetrievalResult`

一句话说：

> `RetrievalResult` 表示“这次被召回的是哪个 chunk，以及它的检索分数是什么”。

为什么重要：

- 检索返回的不只是文本，还应保留排序和解释空间
- 后续检索调优、Rerank、阈值过滤都会依赖这个形状

第一章里先保留：

- `chunk`
- `score`

这正好足够支撑“最小检索 -> Prompt 拼装”的流程。

### 8.3 `AnswerResult`

一句话说：

> `AnswerResult` 是服务层最终对外返回的最小回答结构。

为什么重要：

- RAG 的返回不应该只是 `answer: str`
- 真实业务里还要知道 `sources`
- 后续评估和前端展示也需要这个形状

第一章先保留：

- `answer`
- `sources`

这是最小但稳定的项目接口面。

### 8.4 `prepare_chunks()`

一句话说：

> `prepare_chunks()` 把“文本切分、metadata 注入、稳定 ID 生成”先收束成了一个中间层。

为什么重要：

- 第二章不应该把逻辑散在多个脚本里
- 一个稳定中间层有利于后面替换真实 loader 和 splitter

它虽然只是骨架函数，但方向非常对：

```text
text -> split_text() -> build_base_metadata() -> stable ids -> SourceChunk list
```

### 8.5 `build_prompt()` 和 `RagService.ask()`

一句话说：

> 这两个入口提前把“Prompt 组织”和“服务调用”从零散脚本中分离出来了。

为什么重要：

- Prompt 不应该长期直接写死在入口脚本里
- 服务层最终一定要有统一入口，不能让 CLI、API、脚本各写一套链路

第一章还没有真实模型调用，但已经把形状先定住：

```text
retriever.retrieve()
-> build_prompt()
-> AnswerResult
```

这就是第一章最值得读的地方。

---

## 9. 实践任务

下面这三项任务建议你都做。

### 任务 1：画出最小 `2-step RAG` 数据流

输入：

- 本章“什么是 RAG”部分
- `query_demo.py` 的输出

输出：

- 一张你自己的数据流图，至少包含：
  `文档 / chunk / retriever / prompt / answer`

验收标准：

- 能说明每个节点在做什么
- 能解释为什么 RAG 不只是“多放一段上下文”

卡住时回看：

- 本章第 2 节
- 本章第 7 节

### 任务 2：对照代码解释三个核心对象

输入：

- [app/schemas.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/schemas.py)

输出：

- 用你自己的话解释：
  `SourceChunk / RetrievalResult / AnswerResult`

验收标准：

- 不能只重复字段名
- 必须说清它们分别服务哪一步链路

卡住时回看：

- 本章第 8 节
- `query_demo.py`
- `inspect_chunks.py`

### 任务 3：做一次方案判断

请判断下面四个场景分别更适合什么方案：

1. 用户上传 10 份 PDF，临时做问答 Demo
2. FAQ 已经在 Elasticsearch 里
3. 产品文档很多，而且必须显示来源
4. 复杂研究问题，需要反复改写查询和拆分子问题

输出：

- 每个场景写出你的方案选择和一句理由

验收标准：

- 不是只写“RAG / 微调 / Agent”
- 必须写出为什么

卡住时回看：

- 本章第 3 节

---

## 10. 常见误区

### 误区 1：第一章没有真实问答，所以没内容

错。

第一章真正教的是：

- 接口面
- 数据结构
- 项目骨架
- 学习路线

如果这一步没立住，后面所有章节都会变成临时拼装。

### 误区 2：`split_text()` 很简单，所以这一章代码没价值

错。

第一章里的 `split_text()` 是占位实现，它的价值在于先把“文本 -> chunk 列表”的接口稳定下来。第二章再替换成更真实的实现。

### 误区 3：既然是 RAG 课程，就应该马上接向量库

错。

如果第一章就把向量库、Embedding、检索策略、评估系统全塞进来，主线会立刻变散。

### 误区 4：`MockRetriever` 不真实，所以不值得看

错。

它正好让你先只理解服务层要消费什么结构，而不被真实检索细节干扰。

---

## 11. 完成标准

### 理解层

- 能用自己的话解释什么是 RAG
- 能说明 RAG、长上下文、微调和 `Agentic RAG` 的基本边界
- 能解释为什么第一章默认主线是固定 `2-step RAG`

### 操作层

- 能进入 `source/04_rag/labs/phase_1_scaffold/`
- 能跑通：
  `query_demo.py`、`inspect_chunks.py`、`build_index.py`
- 能跑通：
  `python3 -m unittest discover -s tests`

### 代码层

- 能解释 `SourceChunk / RetrievalResult / AnswerResult` 的职责
- 能说清 `prepare_chunks()`、`build_prompt()`、`RagService.ask()` 各负责哪一步
- 能指出第二章最自然的扩展点会落在哪些文件上

### 映射层

- 能说清本章文档对应的主示例文件是哪个
- 能说清为什么第一阅读入口是 `phase_1_scaffold/README.md`
- 能说清本章内容和大纲中“什么是 RAG”“RAG 架构选型与边界判断”的对应关系

如果这四层都达到了，第一章才算真正完成。
