# phase_1_scaffold

> 第一章代码快照的任务不是实现完整 RAG，而是先把后续章节会反复扩展的项目骨架定下来。

---

## 核心原则

```text
先理解骨架为什么这样分层 -> 再看最小数据结构 -> 再看 chunk 准备链路 -> 再看占位 RAG 闭环
```

这一章的重点不是“功能多”，而是“结构清楚”。

- 你现在看到的是 `04_rag` 第一章的真实代码入口
- 这一章默认和 [docs/04_rag/01_rag_basics.md](/Users/linruiqiang/work/ai_application/docs/04_rag/01_rag_basics.md) 配套阅读
- 没有 API Key 也可以完整学习这一章，因为重点是骨架、对象和链路，不是真实模型效果

## 当前目录在整门课里的角色

`phase_1_scaffold` 对应的是：

- 第一章：RAG 基础概念

它负责先把这些东西立住：

- 项目目录结构
- 核心数据结构
- chunk 的最小准备链路
- retriever 协议
- prompt 构造入口
- service 入口
- 占位脚本和最小测试

它暂时不负责：

- 真实文档加载
- 真实 embedding
- 真实向量数据库
- 真实 RAG 问答
- 真实评估系统

## 项目结构

```text
phase_1_scaffold/
├── README.md
├── app/
│   ├── config.py
│   ├── schemas.py
│   ├── ingestion/
│   │   ├── loaders.py
│   │   ├── metadata.py
│   │   └── splitters.py
│   ├── indexing/
│   │   ├── id_generator.py
│   │   └── index_manager.py
│   ├── embeddings/
│   ├── vectorstores/
│   ├── retrievers/
│   ├── prompts/
│   ├── chains/
│   ├── services/
│   ├── evaluation/
│   ├── api/
│   └── observability/
├── scripts/
├── tests/
├── evals/
└── data/
```

### 这个结构最重要的阅读方式

不要逐目录平均用力。

第一轮只需要先建立三条主线：

1. `config.py + schemas.py`
   看系统有哪些稳定输入和对象。
2. `ingestion/ + indexing/`
   看文本如何被整理成标准 chunk。
3. `prompts/ + chains/ + services/`
   看检索结果最终怎样进入回答链路。

## 为什么项目目录这么拆

这一章的目录规划不是为了“看起来像正式项目”，而是在提前回答后续实现会遇到的两个问题：

1. 哪些东西应该先稳定下来
2. 哪些东西应该留作后续章节的扩展点

### 顶层目录为什么分开

| 目录 | 为什么单独存在 | 现在的角色 |
|------|----------------|------------|
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

### `app/` 里的分层在保护什么

`app/` 继续拆分，是为了让不同层次的变化互不污染。

| 模块 | 当前在做什么 | 为什么要单独一层 |
|------|--------------|------------------|
| `config.py` | 放全局默认配置 | 配置会跨模块复用，不应散在脚本里 |
| `schemas.py` | 放公共对象 | 后续所有模块都要围绕同一数据结构协作 |
| `ingestion/` | 处理“文件 -> 文本”这条链路 | 文档进入系统应和检索/生成解耦 |
| `indexing/` | 处理 chunk、metadata、稳定 ID | 把原始输入收束成标准 chunk 入口 |
| `embeddings/` | 预留向量化接口 | 未来模型可替换，但接口先稳定 |
| `vectorstores/` | 预留向量存储抽象 | 存储层不该写死在服务入口里 |
| `retrievers/` | 定义检索协议 | 先把检索输入输出固定下来 |
| `prompts/` | 放 Prompt 资产 | Prompt 不应长期散落在代码里 |
| `chains/` | 组合上下文和 Prompt | 让“检索结果 -> 模型输入”成为单独层 |
| `services/` | 对外收束统一入口 | CLI、API、脚本未来都应复用这一层 |
| `evaluation/` | 预留评估能力 | 评估必须从第一天有位置 |
| `api/` | 预留传输层入口 | API 应该建立在稳定内核之上 |
| `observability/` | 预留日志和观测 | 观测不应和主业务逻辑混写 |

这套设计本质上是在保护四件事：

1. 稳定对象先于复杂实现
2. 中间流程先于外部入口
3. 基础设施和业务主线分离
4. 学习入口和项目内核分离

## 前置准备

### 1. 运行目录

```bash
cd source/04_rag/labs/phase_1_scaffold
```

### 2. 当前命令

```bash
python3 scripts/build_index.py
python3 scripts/inspect_chunks.py
python3 scripts/query_demo.py
python3 -m unittest discover -s tests
```

### 3. 这一章运行命令的学习意义

- `build_index.py`
  先验证骨架目录和配置入口已经成立。
- `inspect_chunks.py`
  先看到 chunk 对象长什么样。
- `query_demo.py`
  先看到“retriever -> prompt -> answer result”的最小形状。
- `unittest`
  先验证最小测试闭环和评估占位模块存在。

## 第 1 步：先看项目级配置和公共对象

**对应文件**：

- [app/config.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/config.py)
- [app/schemas.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/schemas.py)
- [app/retrievers/base.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/retrievers/base.py)

### 这一步要解决什么

第一章最重要的不是“让模型回答正确”，而是先让后面所有模块共享同一套基础对象。

你要先看懂：

- 项目级默认参数有哪些
- chunk 对象为什么不是裸字符串
- retriever 为什么先抽象成协议

### 重点观察

- `Settings`
  提前定义了 `data_dir / evals_dir / vector_store_dir / default_chunk_size / default_top_k`
- `SourceChunk`
  统一了承载文本、ID 和 metadata 的最小对象
- `RetrievalResult`
  说明检索结果不是只有文本，还可能带分数
- `AnswerResult`
  说明服务层最终返回的也不是单纯字符串

## 第 2 步：看文本如何变成标准 chunk

**对应文件**：

- [app/ingestion/metadata.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/ingestion/metadata.py)
- [app/ingestion/splitters.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/ingestion/splitters.py)
- [app/indexing/id_generator.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/indexing/id_generator.py)
- [app/indexing/index_manager.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/indexing/index_manager.py)
- [scripts/inspect_chunks.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/scripts/inspect_chunks.py)

### 这一步要解决什么

虽然第二章才会正式讲文档处理，但第一章已经先把下面这条链路露出来了：

```text
raw text -> split_text() -> stable ids -> SourceChunk
```

这是后面所有检索能力的基础。

### 重点观察

- `build_base_metadata()`
  先把最基本的来源字段立住
- `SplitterConfig`
  说明 chunk 参数会成为全局可调配置
- `stable_document_id()` 和 `stable_chunk_id()`
  提前引入稳定 ID 的生产意识
- `prepare_chunks()`
  把文档切分、ID 生成和 metadata 合并成统一入口

### 运行建议

```bash
python3 scripts/inspect_chunks.py
```

运行后重点看：

- 输出有几个 chunk
- `chunk_id` 长什么样
- metadata 里有哪些字段

## 第 3 步：看最小 RAG 链路已经如何成形

**对应文件**：

- [app/prompts/rag_prompt.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/prompts/rag_prompt.py)
- [app/chains/rag_chain.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/chains/rag_chain.py)
- [app/services/rag_service.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/services/rag_service.py)
- [scripts/query_demo.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/scripts/query_demo.py)

### 这一步要解决什么

这一章虽然还没有真实 LLM 调用，但最小服务链路已经出现：

```text
retriever.retrieve() -> build_prompt() -> AnswerResult
```

### 重点观察

- `RAG_SYSTEM_PROMPT`
  已经把“不知道就说不知道”和“优先引用来源”写进系统约束
- `format_context()`
  把检索结果渲染成模型能读的上下文文本
- `build_prompt()`
  说明 Prompt 构造应该从服务层拆出来
- `RagService.ask()`
  先统一收束检索和回答入口，再等待后续章节补真实实现

### 运行建议

```bash
python3 scripts/query_demo.py
```

运行后重点看：

- `MockRetriever` 返回的结构
- 最终 answer 里为什么是 “Prompt preview”
- `sources` 为什么已经是标准化 chunk 列表

## 第 4 步：看脚本和测试如何验证骨架成立

**对应文件**：

- [scripts/build_index.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/scripts/build_index.py)
- [tests/test_scaffold.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/tests/test_scaffold.py)
- [app/evaluation/evaluator.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/evaluation/evaluator.py)

### 这一步要解决什么

第一章还没有复杂测试，但已经先把“可验证性”这件事引进来了。

### 重点观察

- `build_index.py` 明确告诉你第二章才开始实现真正 ingestion/indexing
- `summarize_samples()` 说明 Golden Set 不会被留到课程最后才补
- 测试至少保证默认配置和评估占位对象可用

### 运行建议

```bash
python3 scripts/build_index.py
python3 -m unittest discover -s tests
```

## 推荐完整阅读顺序

如果你是第一次读这一章，建议严格按这个顺序：

1. `app/config.py`
2. `app/schemas.py`
3. `app/retrievers/base.py`
4. `app/ingestion/metadata.py`
5. `app/ingestion/splitters.py`
6. `app/indexing/id_generator.py`
7. `app/indexing/index_manager.py`
8. `app/prompts/rag_prompt.py`
9. `app/chains/rag_chain.py`
10. `app/services/rag_service.py`
11. `scripts/inspect_chunks.py`
12. `scripts/query_demo.py`
13. `tests/test_scaffold.py`

## 如果继续实现这套骨架，建议按这个顺序

现在的 `phase_1_scaffold` 只是第一章骨架，但目录已经在暗示后续实施顺序。

建议按这个顺序继续长：

1. 先稳定 `config.py`、`schemas.py` 和 `retrievers/base.py`
   先把系统对象和协议固定下来。
2. 再实现 `ingestion/` 和 `indexing/`
   先把文档真正变成稳定 chunk 列表。
3. 然后补 `embeddings/` 和 `vectorstores/`
   让 chunk 可以向量化并进入存储。
4. 再完善 `retrievers/`
   让问题能够召回相关 chunk，而不是只靠 mock。
5. 再把 `prompts/`、`chains/`、`services/` 接到真实模型
   让系统从占位回答变成真正的“答案 + 来源”。
6. 然后补 `evaluation/` 和 `evals/`
   让后续优化变成可验证的回归，不是凭感觉调参。
7. 最后再补 `api/` 和 `observability/`
   因为传输层和观测层必须建立在稳定内核之上。

这个顺序不能反过来。否则最常见的问题是：

- 还没有稳定 chunk，就急着做向量库
- 还没有服务层边界，就急着做 API
- 还没有评估入口，就急着调检索参数

也就是说，第一章目录里很多模块现在还是占位，但它们已经把后续实施顺序提前固定下来了。

## 建议主动修改的地方

### 修改 1：改 chunk 参数

调整 `app/config.py` 里的：

- `default_chunk_size`
- `default_chunk_overlap`

然后重新跑 `inspect_chunks.py`。

### 修改 2：给 chunk metadata 增加字段

在 `build_base_metadata()` 中新增：

- `category`
- `language`
- `tenant_id`

观察 `prepare_chunks()` 输出如何变化。

### 修改 3：改 `MockRetriever`

让 `query_demo.py` 返回两个 chunk，并给不同 `score`。

这样你会更容易理解后面检索排序和重排的入口形状。

### 修改 4：自己把 `answer` 返回结构再扩一点

例如在 `AnswerResult` 里新增：

- `debug_prompt`
- `retrieval_count`

这会帮助你提前理解后面调试和观测为什么重要。

## 当前真实进度

这份目录当前代表的真实进度是：

- `Phase 1` 已完成骨架
- `Phase 2` 以后还没有真实实现

所以学完这里之后，正确动作不是继续在本目录里硬写完整 RAG，而是进入下一章对应的真实 Phase 实现。

## 这一章完成后你应该能做到什么

至少应该能做到：

- 说清为什么第一章先搭骨架
- 看懂一个 chunk 在系统里的最小结构
- 看懂 `retriever -> prompt -> service` 的最小占位闭环
- 说清第二章最自然应该往哪些模块继续扩展
