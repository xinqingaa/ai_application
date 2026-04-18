# phase_1_scaffold - 实践指南

> 本文档说明如何跟着 [学习文档](/Users/linruiqiang/work/ai_application/docs/04_rag/01_rag_basics.md) 阅读第一章代码快照。

---

## 核心原则

```text
先理解骨架为什么这样分层 -> 再看核心对象 -> 再跑最小链路 -> 最后确认这一章还没有实现什么
```

- 在 `source/04_rag/labs/phase_1_scaffold/` 目录下操作
- 这一章的重点不是功能完整，而是系统骨架清楚
- 没有 API Key 也可以完整学习这一章
- 先看结构，再看细节，不要一上来逐目录平均用力

---

## 项目结构

```text
phase_1_scaffold/
├── README.md
├── PHASE_CARD.md
├── app/
│   ├── config.py
│   ├── schemas.py
│   ├── ingestion/
│   ├── indexing/
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

第一轮只需要抓住三条主线：

1. `config.py + schemas.py`
2. `ingestion/ + indexing/`
3. `prompts/ + chains/ + services/`

---

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

### 3. 先跑哪个

建议先跑：

```bash
python3 scripts/query_demo.py
```

这一步最重要的不是答案内容，而是看见：

- retriever 已经出现
- prompt 已经出现
- `AnswerResult` 已经出现
- 真实 LLM 仍然是占位

---

## 第 1 步：看项目级配置和公共对象

**对应文件**：`app/config.py`、`app/schemas.py`、`app/retrievers/base.py`

### 这一步要解决什么

- 项目级默认参数有哪些
- 为什么 chunk 不是裸字符串
- 为什么检索先抽象成协议

### 重点观察

- `Settings`
- `SourceChunk`
- `RetrievalResult`
- `AnswerResult`

### 建议主动修改

- 改 `default_chunk_size`
- 给 `SourceChunk` 新增一个临时字段，再看看影响面

---

## 第 2 步：看最小 chunk 链路

**对应文件**：`app/ingestion/metadata.py`、`app/ingestion/splitters.py`、`app/indexing/id_generator.py`、`app/indexing/index_manager.py`

### 这一步要解决什么

虽然第二章才会正式讲文档处理，但第一章已经先露出了：

```text
raw text -> split_text() -> stable ids -> SourceChunk
```

### 重点观察

- `build_base_metadata()`
- `SplitterConfig`
- `stable_document_id()` 和 `stable_chunk_id()`
- `prepare_chunks()`

### 建议先跑

```bash
python3 scripts/inspect_chunks.py
```

---

## 第 3 步：看最小 RAG 链路

**对应文件**：`app/prompts/rag_prompt.py`、`app/chains/rag_chain.py`、`app/services/rag_service.py`、`scripts/query_demo.py`

### 这一步要解决什么

这一章虽然还没有真实 LLM 调用，但最小服务链路已经出现：

```text
retriever.retrieve() -> build_prompt() -> AnswerResult
```

### 重点观察

- `RAG_SYSTEM_PROMPT`
- `format_context()`
- `build_prompt()`
- `answer_question()`

### 建议主动修改

- 改 `RAG_SYSTEM_PROMPT` 的措辞
- 改占位回答文案
- 改 `query_demo.py` 里的示例问题

---

## 第 4 步：最后看测试在锁定什么

**对应文件**：`tests/test_scaffold.py`

### 重点观察

- 测试不是为了证明系统完整
- 测试是在锁定：骨架存在、对象存在、最小链路存在

---

## 学完这一章后你应该能回答

- 为什么第一章先做骨架，而不是直接做完整 RAG
- 为什么 `SourceChunk / RetrievalResult / AnswerResult` 要先定义
- 为什么 `embeddings/`、`vectorstores/` 这些目录位要提前出现
- 第一章已经长出了什么，明确还没长出什么
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
