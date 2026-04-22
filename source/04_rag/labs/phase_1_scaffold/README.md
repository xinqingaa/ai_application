# phase_1_scaffold - 旧版备份

> 迁移说明：第一章新的学习入口已经切换到 [source/04_rag/01_rag_basics/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/01_rag_basics/README.md)。这个目录目前只作为迁移期备份保留，等前六章替换完成后会删除。

> 下面内容保留原样，方便对照旧结构，不再推荐作为第一章主入口。

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

## 本章定位

- 对应章节：[01_rag_basics.md](/Users/linruiqiang/work/ai_application/docs/04_rag/01_rag_basics.md)
- 本章目标：建立项目骨架、固定核心对象、露出最小 RAG 链路形状
- 输入契约：无上一章输入，只使用最小样例文本和占位链路
- 输出契约：`SourceChunk`、`RetrievalResult`、`AnswerResult`、最小 `retriever -> prompt -> answer` 链路
- 本章新增：`app/config.py`、`app/schemas.py`、`app/retrievers/base.py`、`app/prompts/rag_prompt.py`、`app/chains/rag_chain.py`、`app/services/rag_service.py`、`scripts/query_demo.py`、`tests/test_scaffold.py`
- 本章可忽略：`embeddings/` 真实实现、`vectorstores/` 真实实现、真实 LLM 调用
- 第一命令：`python scripts/query_demo.py`

---

## 项目结构

```text
phase_1_scaffold/
├── README.md
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
python scripts/build_index.py
python scripts/inspect_chunks.py
python scripts/query_demo.py
python -m unittest discover -s tests
```

### 3. 先跑哪个

建议先跑：

```bash
python scripts/query_demo.py
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
python scripts/inspect_chunks.py
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

## 第 4 步：看脚本和测试如何验证骨架成立

**对应文件**：`scripts/build_index.py`、`tests/test_scaffold.py`、`app/evaluation/evaluator.py`

### 这一步要解决什么

第一章还没有复杂测试，但已经先把“可验证性”这件事引进来了。

### 重点观察

- 测试不是为了证明系统完整，而是在锁定：骨架存在、对象存在、最小链路存在
- `build_index.py` 明确告诉你第二章才开始实现真正 ingestion/indexing
- `summarize_samples()` 说明 Golden Set 不会被留到课程最后才补
- 测试至少保证默认配置和评估占位对象可用

### 运行建议

```bash
python scripts/build_index.py
python -m unittest discover -s tests
```

---

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

## 建议主动修改的地方

1. 调整 `app/config.py` 里的 `default_chunk_size` 和 `default_chunk_overlap`，再重新跑 `inspect_chunks.py`。
2. 在 `build_base_metadata()` 中新增 `category`、`language`、`tenant_id`，观察 `prepare_chunks()` 输出如何变化。
3. 改 `MockRetriever`，让 `query_demo.py` 返回两个 chunk，并给不同 `score`。
4. 在 `AnswerResult` 里新增 `debug_prompt` 或 `retrieval_count`，提前感受后续调试面。

## 学完这一章后你应该能回答

- 为什么第一章先做骨架，而不是直接做完整 RAG
- 为什么 `SourceChunk / RetrievalResult / AnswerResult` 要先定义
- 为什么 `embeddings/`、`vectorstores/` 这些目录位要提前出现
- 为什么现在已经有 `retriever -> prompt -> service` 的闭环，但还不应该接真实 LLM

## 当前真实进度和下一章

- 当前真实进度：`Phase 1` 已完成骨架，`Phase 2` 以后仍是后续章节任务
- 完成标准：能解释为什么第一章先做骨架，能说明三个核心对象职责，能看懂最小链路已经长出什么
- 下一章：把样例输入替换成真实 `.md / .txt` 文档，把 `SourceChunk[]` 生产链路做成真实实现
