# 01. RAG 基础概念

> 本节目标：先建立 RAG 的问题意识、架构判断和系统骨架感，明确这门课为什么默认从固定 `2-step RAG` 和项目骨架开始，而不是一上来就做完整知识库。

---

## 1. 概述

### 学习目标

- 理解 RAG 解决什么问题，以及它不解决什么问题
- 能区分长上下文、直接查现有知识系统、固定 `2-step RAG`、微调和 `Agentic RAG`
- 能画出最小 `2-step RAG` 数据流，并说明每一步在做什么
- 理解为什么 `04_rag` 第一章先建立项目骨架和核心对象
- 能读懂 `SourceChunk / RetrievalResult / AnswerResult` 这三个核心对象的职责
- 能运行第一章代码快照，并看出当前系统“已经长出什么，还没长出什么”

### 预计学习时间

- RAG 问题意识与方案判断：1 小时
- 最小数据流与系统骨架：1 小时
- 第一章代码快照阅读：1-1.5 小时

### 本节在 AI 应用中的重要性

| 场景 | 相关知识 |
|------|---------|
| 企业知识库问答 | 检索、引用、知识更新 |
| 文档问答 | 文档进入系统、上下文拼装 |
| 客服 / 规则问答 | 来源追溯、拒答边界 |
| 架构选型 | 长上下文、RAG、微调、Agentic RAG 的边界 |
| 后续工程实现 | chunk、向量、检索、生成、评估的主线 |

> **第一章的重点不是“把 RAG 做完”，而是先判断为什么要做、该做到哪一层，以及这套系统应该长成什么形状。**

### 本章与前后章节的关系

前面的 `02_llm` 解决的是：

1. 怎么稳定调用模型
2. 怎么管理消息和上下文
3. 怎么做结构化输出、成本控制和错误处理

`04_rag` 第一章接着解决的是：

1. 为什么单次模型调用不够
2. 什么情况下需要 RAG
3. 为什么默认先把固定链路做稳
4. 为什么项目要先从骨架和对象开始

后续章节会沿这条主线继续展开：

- 第二章：把原始文件整理成稳定 `SourceChunk`
- 第三章：把 `SourceChunk` 变成 `EmbeddedChunk`
- 第四章：把向量写进存储并支持最小检索
- 第五章：围绕召回质量调检索策略
- 第六章：把检索结果接成真正回答

### 本章的学习边界

本章重点解决：

1. RAG 的定义和适用边界
2. 常见方案梯度和默认决策顺序
3. 为什么课程主线先从固定 `2-step RAG` 开始
4. 为什么第一章先做骨架，而不是直接做完整问答系统

本章不展开：

- 真实文档加载和切分
- 真实 Embedding 模型接入
- 真实向量数据库
- 混合检索、Rerank、HyDE、多查询
- 完整 RAG Chain 和 API 服务
- `Agentic RAG` 的完整实现

### 当前代码快照

本章对应的代码快照是：

- [phase_1_scaffold/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/README.md)
- [scripts/query_demo.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/scripts/query_demo.py)

第一章的代码重点不是模型效果，而是系统骨架、对象和最小链路。

---

## 2. 为什么会需要 RAG 📌

### 2.1 单次模型调用为什么不够

在 `02_llm` 里，你已经学过如何稳定发出一次请求。

但真实业务很快会遇到一个问题：

> 模型本身并不知道你的私有知识，也不会随着文档更新自动学会新内容。

如果一个系统需要回答：

- 公司内部制度
- 产品帮助文档
- 课程资料
- 运营规则
- 法规和手册

只靠模型参数，通常会遇到四类问题：

1. 知识过时
2. 来源不可追溯
3. 文档太多，无法长期手工塞进 Prompt
4. 没有依据时容易自由发挥

RAG 就是在解决这件事：

> 先把相关知识找出来，再把它们连同问题一起交给模型生成答案。

### 2.2 RAG 的最小数据流

一个最小 `2-step RAG` 数据流可以压缩成两段：

```text
离线阶段：
文档 -> 切分 -> 向量化 -> 向量存储

在线阶段：
问题 -> 检索 -> 上下文 -> LLM -> 答案 + 来源
```

这条链路里，每一层都只解决一个清晰问题：

- 文档处理：把文件变成稳定 chunk
- 向量化：把 chunk 变成可比较向量
- 向量存储：让向量可写入、可查询、可删除
- 检索：从知识库里找出当前问题最相关的上下文
- 生成：让模型基于上下文回答，而不是自由发挥

### 2.3 RAG 解决什么，不解决什么

RAG 重点解决的是：

1. 知识更新问题
2. 来源追溯问题
3. 上下文受控问题
4. 私有文档接入问题

但 RAG 不直接解决：

- 模型本身推理能力不足
- 业务规则定义不清
- 输入文档本身质量很差
- 根本没有可用知识源

这也是为什么你不能把所有回答质量问题都归结为“RAG 没调好”。

---

## 3. 什么情况下该选什么方案 📌

### 3.1 常见方案梯度

很多人在做 AI 应用时，会先问“要不要上 RAG”。更准确的问法其实是：

> 当前这个问题，最合适的知识接入方案是什么？

常见方案梯度如下：

| 方案 | 更适合什么情况 | 不适合什么情况 |
|------|----------------|----------------|
| 长上下文 | 材料少、问题少、一次性分析 | 文档多、更新频繁、要长期维护 |
| 直接查现有系统 | 已有 SQL、Elasticsearch、CMS、FAQ 系统 | 以非结构化文档为主的场景 |
| 固定 `2-step RAG` | 要引用来源、要持续更新知识 | 明显更适合结构化查询的场景 |
| 微调 | 学习风格、格式、行为模式 | 希望频繁更新外部知识 |
| `Agentic RAG` | 固定链路明显不够，需要动态检索决策 | 基础 RAG 还没做稳 |

### 3.2 默认决策顺序

这门课推荐的默认决策顺序是：

1. 先判断能不能直接用长上下文解决
2. 再判断能不能直接查现有知识系统
3. 默认优先做稳定的 `2-step RAG`
4. 固定检索不稳时，再加混合检索、Rerank、查询变换
5. 只有固定链路明显不够时，才升级到 `Agentic RAG`

这里最重要的判断不是“哪个方案最强”，而是：

> 先用问题类型判断方案，再选技术，而不是先选技术再给它找问题。

### 3.3 为什么这门课先做固定 `2-step RAG`

因为这门课当前主线不是“复杂动态决策”，而是“把固定链路做稳”。

固定 `2-step RAG` 的价值在于：

- 数据流清晰
- 边界清晰
- 便于分阶段学习
- 便于判断问题到底出在文档、检索还是生成

如果第一章就直接做复杂 Agent 工作流，学习者很容易：

- 分不清问题到底出在哪一层
- 把所有效果问题都混成“模型不稳定”
- 还没做稳基础系统，就引入过多动态行为

---

## 4. 为什么第一章先做项目骨架 📌

### 4.1 为什么不一开始就接真实组件

如果第一章一开始就把这些全接上：

- 真实 loader
- 真实 Embedding
- 真实向量库
- 真实 LLM

读者看到的会是一堆组件，但很难看清主线。

第一章真正要先稳定的是：

1. 配置入口
2. 公共数据结构
3. 最小 chunk 准备链路
4. retriever 协议
5. prompt 入口
6. service 入口

先把“系统形状”立住，后面的每一章才知道该往哪里继续长。

### 4.2 第一章最重要的三个对象

这一章最值得先看懂的是：

| 对象 | 作用 |
|------|------|
| `SourceChunk` | 标准 chunk 对象，后续文档处理和向量化都围绕它继续长 |
| `RetrievalResult` | 检索结果对象，说明召回结果不只是字符串 |
| `AnswerResult` | 服务层返回对象，说明最终输出不是单纯文本 |

这三个对象的重要性在于：

- 第二章继续产出 `SourceChunk`
- 第三章继续复用 `SourceChunk`
- 第六章以后 `RetrievalResult` 和 `AnswerResult` 会重新变成主角

### 4.3 第一章的代码骨架在保护什么

`phase_1_scaffold` 里的分层不是为了“看起来像正式项目”，而是在保护四件事：

1. 稳定对象先于复杂实现
2. 中间流程先于外部入口
3. 基础设施和业务主线分离
4. 学习入口和项目内核分离

所以你会看到：

- `app/` 放项目内核
- `scripts/` 放运行和观察入口
- `tests/` 放最小验收
- `evals/` 提前留出评估资产位置
- `data/` 放本地样例输入

这也是为什么第一章看起来“实现不多”，但结构信息其实很关键。

---

## 5. 第一章应该怎么学

### 5.1 推荐顺序

建议按这个顺序进入：

1. 先读 [phase_1_scaffold/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/README.md)
2. 再看 [app/config.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/config.py)
3. 再看 [app/schemas.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/schemas.py)
4. 再看 [app/indexing/index_manager.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/indexing/index_manager.py)
5. 最后看 [scripts/query_demo.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/scripts/query_demo.py)

### 5.2 建议先跑的命令

```bash
cd source/04_rag/labs/phase_1_scaffold

python scripts/query_demo.py
python scripts/inspect_chunks.py
python -m unittest discover -s tests
```

你现在最该观察的是：

- retriever 已经出现
- prompt 已经出现
- answer 结构已经出现
- 但真实 LLM 和真实向量检索还没有接入

也就是说：

> 第一章是在建立“系统形状感”，不是在追求最终答案质量。

---

## 综合案例：为课程资料问答选择合适方案

```python
# 你要做一个课程资料问答系统：
#
# 需求：
# 1. 资料会持续更新
# 2. 需要显示答案来源
# 3. 资料量会逐步变大
# 4. 用户会问细节规则和章节内容
#
# 请判断：
# 1. 直接长上下文是否足够？
# 2. 是否应该优先做固定 2-step RAG？
# 3. 为什么不应该一开始就上 Agentic RAG？
# 4. 第一章如果要建立项目骨架，最先固定哪些对象？
```

当你能用自己的话回答这 4 个问题时，第一章就真正学会了。
python scripts/inspect_chunks.py
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
python -m unittest discover -s tests
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
