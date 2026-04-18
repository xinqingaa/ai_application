# 01. RAG 基础概念

> 本节目标：先把 RAG 解决什么问题、默认应该怎么做架构判断、以及这门课为什么先从项目骨架开始讲清楚。

---

## 1. 概述

### 学习目标

完成本章后，你应该能够：

- 能解释 RAG 解决什么问题，以及它不解决什么问题
- 能区分长上下文、直接查现有知识系统、固定 `2-step RAG` 和 `Agentic RAG`
- 能画出最小 `2-step RAG` 数据流，并说明每一步在做什么
- 能运行第一章的主示例脚本，并读懂输出表达的链路形状
- 能说明 `SourceChunk / RetrievalResult / AnswerResult` 这三个核心对象的职责
- 能解释为什么第一章先做骨架，而不是直接实现完整问答系统

### 本章在 `04_rag` 中的位置

第一章是 `04_rag` 的入口章，负责先建立三件事：

1. 方案判断力
2. 系统形状感
3. 项目骨架感

后续章节会沿着这条主线继续长：

- 第二章：把“原始文件”变成稳定 `SourceChunk`
- 第三章：把 `SourceChunk` 变成 `EmbeddedChunk`
- 第四章：把向量写入存储并做最小检索
- 第五章：围绕召回效果继续调策略
- 第六章：把检索结果接成真正回答

### 学习前提

建议你至少已经具备下面这些基础：

- 已完成 [02_llm/outline.md](/Users/linruiqiang/work/ai_application/docs/02_llm/outline.md) 的主线内容
- 已理解 [03_foundation/outline.md](/Users/linruiqiang/work/ai_application/docs/03_foundation/outline.md) 中的 `Document / Retriever / Runnable`
- 已知道 Prompt、上下文窗口、结构化输出、成本和错误处理这些概念

### 本章边界

本章重点解决的是：

1. 什么是 RAG
2. 什么情况下应该先考虑 RAG
3. 为什么课程主线默认是固定 `2-step RAG`
4. 为什么第一章先做骨架，而不是直接写完整系统

本章不展开：

- 真实文档加载和切分
- 真实 Embedding 模型接入
- 真实向量数据库
- 混合检索、Rerank、HyDE、多查询
- 完整 RAG Chain、API 服务、流式输出
- `Agentic RAG` 的实现

### 第一入口

本章有两个入口，职责不同：

- 第一阅读入口：
  [phase_1_scaffold/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/README.md)
- 第一运行入口：
  [scripts/query_demo.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/scripts/query_demo.py)

为什么这样安排：

- `README` 先帮你建立目录职责和阅读顺序
- `query_demo.py` 先让你看到“retriever -> prompt -> answer”这条最小闭环

---

## 2. 这一章真正要解决什么问题 📌

### 2.1 什么是 RAG

一句话说：

> RAG 是把“知识检索”接到“模型生成”前面的系统链路。

最小流程长这样：

```text
文档 -> 切分 -> 索引
用户问题 -> 检索 -> 上下文 -> LLM -> 答案
```

它重要的原因不是“又多了一个步骤”，而是：

- 知识可以更新
- 回答可以引用来源
- 不必把所有知识都塞进模型参数里
- 能把“知识问题”和“模型能力问题”拆开看

### 2.2 RAG 解决什么，不解决什么

RAG 重点解决的是下面这四类问题：

1. 知识更新问题
   文档变了，不应该靠重新训练模型才能生效。
2. 来源追溯问题
   真实业务里，很多回答必须知道“答案来自哪里”。
3. 幻觉控制问题
   模型在没有依据时容易自由发挥，RAG 至少能先给它一个受约束的上下文。
4. 知识规模问题
   文档一多，就不可能长期靠手工复制进 Prompt。

但 RAG 不直接解决这些问题：

- 模型本身推理能力不足
- 业务规则本身定义不清
- 输入文档质量很差
- 根本没有可用知识源

### 2.3 什么情况下该用什么方案

| 方案 | 更适合什么情况 | 不适合什么情况 |
|------|----------------|----------------|
| 长上下文 | 材料少、问题少、一次性分析 | 文档多、更新频繁、要长期维护 |
| 直接查现有系统 | FAQ、SQL、Elasticsearch、CMS 已经存在 | 明显以非结构化文档为主的场景 |
| 固定 `2-step RAG` | 有文档库、要引用来源、要持续更新 | 结构化查询明显更合适的场景 |
| 微调 | 想学风格、格式、行为模式 | 希望频繁更新外部知识 |
| `Agentic RAG` | 固定链路明显不够，需要动态检索决策 | 还没把基础 RAG 做稳 |

这一章最重要的判断不是“哪个方案最强”，而是：

> 先用问题类型判断方案，再选技术，而不是先选技术再给它找问题。

### 2.4 为什么本课程先做固定 `2-step RAG`

因为这门课当前主线不是“动态决策”，而是“把固定链路做稳”。

默认决策顺序应该是：

1. 先判断能不能直接用长上下文
2. 再判断能不能直接查现有系统
3. 默认先把固定 `2-step RAG` 做稳
4. 检索不稳时再加混合检索、Rerank、查询变换
5. 只有固定链路明显不够时，才升级到 `Agentic RAG`

这也是为什么第一章只做概念和骨架，不做复杂编排。

### 2.5 为什么第一章先做骨架

如果第一章一开始就接：

- 真实 loader
- 真实 embedding
- 真实向量库
- 真实 LLM

读者只会看到一堆组件，很难看清主线。

第一章真正要先稳定的是：

- 配置入口
- 公共数据结构
- 最小 chunk 准备链路
- retriever 协议
- prompt 组织入口
- service 入口

先把“系统形状”立住，后面每一章才知道该往哪里继续长。

---

## 3. 第一章的代码设计与目录规划 📌

### 3.1 为什么项目目录要这样规划

第一章的目录规划不是为了“看起来像正式项目”，而是在提前回答两个问题：

1. 哪些东西应该先稳定下来
2. 哪些东西应该留作后续章节的扩展点

`phase_1_scaffold/` 顶层目录这样拆，核心是为了先把职责分开：

| 目录 | 为什么单独存在 | 当前角色 |
|------|----------------|----------|
| `app/` | 放项目内核，后续真正会持续长大的代码都应该落在这里 | 当前骨架主体 |
| `scripts/` | 放第一运行入口和调试入口 | 当前观察和验证入口 |
| `tests/` | 放最小验收 | 当前保证骨架不是死文件 |
| `evals/` | 提前为 Golden Set 和实验资产留位置 | 当前占位扩展点 |
| `data/` | 放样例输入和本地文档 | 当前样例输入位 |

如果把这些内容全堆在一个脚本里，第一章虽然也能跑，但后续章节会立刻遇到：

- 入口和内核混在一起
- 脚本和服务逻辑混在一起
- 测试和调试没有明确边界
- 评估资产没有固定落位

### 3.2 `app/` 里的分层在保护什么

`app/` 继续拆分，是为了让不同层次的变化互不污染。

| 模块 | 当前职责 | 为什么单独一层 |
|------|----------|----------------|
| `config.py` | 放默认目录、chunk 参数、top_k 等全局配置 | 配置会跨模块复用，不应该散在脚本里 |
| `schemas.py` | 放公共对象 | 后续所有模块都要围绕同一数据结构协作 |
| `ingestion/` | 处理“文件 -> 文本”这条链路 | 文档进入系统应和检索、生成解耦 |
| `indexing/` | 处理 chunk、metadata、稳定 ID | 把原始输入收束成标准 chunk 入口 |
| `embeddings/` | 预留向量化接口 | 模型以后可以替换，但接口位先稳定 |
| `vectorstores/` | 预留向量存储抽象 | 存储层不该写死在服务入口里 |
| `retrievers/` | 定义检索协议 | 先把检索输入输出固定下来 |
| `prompts/` | 放 Prompt 资产 | Prompt 不应长期散落在脚本和服务入口里 |
| `chains/` | 组合上下文和 Prompt | 让“检索结果 -> 模型输入”成为单独层 |
| `services/` | 对外收束统一入口 | CLI、API、脚本未来都应复用这一层 |

从代码设计角度看，这套分层在保护四件事：

1. 稳定对象先于复杂实现
2. 中间流程先于外部入口
3. 基础设施和业务主线分离
4. 学习入口和项目内核分离

### 3.3 第一章最重要的三个对象

第一章最值得先看懂的是：

| 对象 | 在哪里定义 | 作用 |
|------|------------|------|
| `SourceChunk` | [app/schemas.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/schemas.py) | 标准 chunk 对象，后续章节都围绕它继续长 |
| `RetrievalResult` | [app/schemas.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/schemas.py) | 检索结果对象，说明召回结果不只是文本 |
| `AnswerResult` | [app/schemas.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/schemas.py) | 服务层返回对象，说明最终输出不是单纯字符串 |

这三个对象的重要性在于：

- 第二章会继续产出 `SourceChunk`
- 第三章会继续复用 `SourceChunk`
- 第六章以后 `RetrievalResult` 和 `AnswerResult` 会重新变成主角

---

## 4. 推荐阅读与运行顺序 📌

### 第一步：先打开第一阅读入口

读：

- [phase_1_scaffold/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/README.md)

这一步先解决三个问题：

1. 当前目录有哪些部分
2. 当前能运行什么
3. 第一章为什么只是骨架

### 第二步：先跑主示例文件

运行：

```bash
cd source/04_rag/labs/phase_1_scaffold
python3 scripts/query_demo.py
```

当前输出会先让你看到：

```text
Phase 1 scaffold only. Replace this placeholder with a real LLM call in Phase 4.
```

你此时最该观察的是：

- retriever 已经出现
- prompt 已经出现
- answer 结构已经出现
- 但 LLM 调用仍然是占位

### 第三步：再跑 chunk 观察脚本

运行：

```bash
python3 scripts/inspect_chunks.py
```

当前输出会先让你看到：

```text
Prepared 1 chunk(s).
df01139fe9617e6a9d81a290ba2eb4c0d726b727:0:a3c96f83edae {'source': 'data/sample.md', 'filename': 'sample.md', 'suffix': '.md', 'chunk_index': 0}
```

这一步先建立两个直觉：

- `SourceChunk` 已经不是裸字符串
- `chunk_id` 和 metadata 的形状已经提前露出来了

### 第四步：再读核心实现文件

建议按这个顺序：

1. [app/config.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/config.py)
2. [app/schemas.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/schemas.py)
3. [app/retrievers/base.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/retrievers/base.py)
4. [app/indexing/index_manager.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/indexing/index_manager.py)
5. [app/chains/rag_chain.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/chains/rag_chain.py)
6. [app/services/rag_service.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/services/rag_service.py)

### 第五步：最后跑测试

运行：

```bash
python3 -m unittest discover -s tests
```

这一步的目的不是凑测试数量，而是确认：

- 配置入口存在
- 评估占位模块存在
- 第一章骨架不是“只有目录，没有最小闭环”

### 卡住时先回看哪里

如果中途卡住，先回看这三个位置：

1. [phase_1_scaffold/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/README.md)
2. 本章的“代码映射表”
3. [tests/test_scaffold.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/tests/test_scaffold.py)

---

## 5. 本章实施步骤应该怎么理解 📌

第一章的正确实施顺序，不是“尽快接更多外部组件”，而是：

| 步骤 | 先做什么 | 主要落在哪些模块 | 这一步在解决什么 |
|------|----------|------------------|------------------|
| 1 | 固定全局配置和目录位置 | `app/config.py` | 让后续代码有共同默认参数和路径 |
| 2 | 固定公共对象 | `app/schemas.py` | 让后续模块围绕同一对象协作 |
| 3 | 暴露最小 chunk 准备链路 | `ingestion/`、`indexing/` | 先让系统知道 chunk 长什么样 |
| 4 | 固定 retriever / prompt / service 入口 | `retrievers/`、`chains/`、`services/` | 让最小 RAG 链路形状先出现 |
| 5 | 留出测试和评估位置 | `tests/`、`evals/` | 避免后面只能凭感觉推进 |

这一章故意不做真实实现，不是偷懒，而是为了让后续章节始终沿同一套骨架继续长。

---

## 6. 本章代码映射表

| 文档部分 | 对应代码/文档 | 角色 | 说明 |
|----------|---------------|------|------|
| 本章第一阅读入口 | [phase_1_scaffold/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/README.md) | 主入口 | 先理解目录职责、运行方式和阅读顺序 |
| 最小 RAG 闭环 | [scripts/query_demo.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/scripts/query_demo.py) | 主示例文件 | 先看到 `retriever -> prompt -> answer` 的占位闭环 |
| chunk 形状 | [scripts/inspect_chunks.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/scripts/inspect_chunks.py) | 扩展示例 | 先看到 `SourceChunk`、`chunk_id` 和 metadata 长什么样 |
| 配置入口 | [app/config.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/config.py) | 核心配置 | 定义目录、chunk 参数和默认检索参数 |
| 核心对象 | [app/schemas.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/schemas.py) | 核心数据结构 | 定义 `SourceChunk / RetrievalResult / AnswerResult / EvalSample` |
| chunk 收口 | [app/indexing/index_manager.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/indexing/index_manager.py) | 核心流程 | 把文本、metadata 和稳定 ID 合并成标准 chunk |
| 服务入口 | [app/services/rag_service.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/services/rag_service.py) | 项目入口 | 收束 retriever 和回答结构，形成 `ask()` 入口 |
| 最小验证 | [tests/test_scaffold.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/tests/test_scaffold.py) | 验收入口 | 保证配置和评估占位模块不是死文件 |

---

## 7. 实践任务

1. 用自己的话画出最小 `2-step RAG` 数据流，不要直接抄定义。
2. 对照 [app/schemas.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/schemas.py)，解释为什么服务层返回 `AnswerResult` 而不是字符串。
3. 跑一次 [scripts/query_demo.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/scripts/query_demo.py) 和 [scripts/inspect_chunks.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/scripts/inspect_chunks.py)，说清这两个脚本分别在提前暴露什么接口。
4. 看 [app/indexing/index_manager.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/indexing/index_manager.py)，解释为什么第一章就先把 chunk 准备链路露出来。

---

## 8. 完成标准

完成这一章后，至少应满足：

- 能解释什么是 RAG，以及什么情况下不该优先做 RAG
- 能说明为什么课程主线默认是固定 `2-step RAG`
- 能运行第一章主示例脚本并读懂输出
- 能解释 `SourceChunk / RetrievalResult / AnswerResult` 的职责
- 能说明第一章为什么先做骨架，而不是直接接完整外部组件
