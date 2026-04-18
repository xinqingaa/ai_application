# phase_2_document_processing - 实践指南

> 本文档说明如何跟着 [学习文档](/Users/linruiqiang/work/ai_application/docs/04_rag/02_document_processing.md) 阅读第二章代码快照。

---

## 核心原则

```text
先看样例文档 -> 再跑切分脚本 -> 再读 loaders / splitters / metadata / index_manager -> 最后用测试确认稳定性
```

- 在 `source/04_rag/labs/phase_2_document_processing/` 目录下操作
- 这一章的重点不是“完整 RAG 已经做好”，而是让文档输入层先稳定下来
- 没有 API Key 也可以完整学习这一章

---

## 项目结构

```text
phase_2_document_processing/
├── README.md
├── PHASE_CARD.md
├── app/
├── data/
│   ├── product_overview.md
│   └── faq.txt
├── scripts/
└── tests/
```

这一章第一轮只需要抓住四个点：

1. `data/`
2. `app/ingestion/`
3. `app/indexing/`
4. `scripts/ + tests/`

---

## 前置准备

### 1. 运行目录

```bash
cd source/04_rag/labs/phase_2_document_processing
```

### 2. 当前命令

```bash
python3 scripts/build_index.py
python3 scripts/inspect_chunks.py
python3 scripts/inspect_chunks.py data/faq.txt
python3 -m unittest discover -s tests
```

### 3. 先跑哪个

建议先跑：

```bash
python3 scripts/build_index.py
```

你现在最该先建立的直觉是：

- 哪些文件会被发现
- 每份文档会被切成几个 chunk
- 同一套 chunk 参数下，不同文档切分结果不同

---

## 第 1 步：先看输入文档和全局配置

**对应文件**：`data/product_overview.md`、`data/faq.txt`、`app/config.py`

### 这一步要解决什么

- 当前支持哪些输入格式
- 默认 `chunk_size / chunk_overlap` 是多少
- 为什么先拿 `.md / .txt` 两种简单格式做样例

### 重点观察

- `supported_suffixes`
- `default_chunk_size / default_chunk_overlap`
- 两份样例文档的内容结构差异

---

## 第 2 步：看文件如何进入系统

**对应文件**：`app/ingestion/loaders.py`、`scripts/build_index.py`

### 这一步要解决什么

- 哪些文件应该被发现
- `README.md` 为什么不会进入索引
- 文本进入系统前做了哪些最小规范化

### 重点观察

- `discover_documents()`
- `normalize_text()`
- `load_document()`

### 建议主动修改

- 在 `data/` 里加一个新的 `.txt` 文档
- 故意放一个 `README.md` 看是否会被排除

---

## 第 3 步：看文本如何被切成 chunk

**对应文件**：`app/ingestion/splitters.py`、`scripts/inspect_chunks.py`

### 这一步要解决什么

- 为什么 chunk 不是简单定长截断
- overlap 为什么存在
- 为什么 chunk 最好保留字符范围

### 重点观察

- `TextChunk`
- `SplitterConfig.__post_init__()`
- `_choose_breakpoint()`
- `split_text()`

### 建议先跑

```bash
python3 scripts/inspect_chunks.py
python3 scripts/inspect_chunks.py data/faq.txt
```

---

## 第 4 步：看 metadata 和 stable id 如何进入系统

**对应文件**：`app/ingestion/metadata.py`、`app/indexing/id_generator.py`、`app/indexing/index_manager.py`

### 这一步要解决什么

第二章真正的闭环是：

```text
path -> text -> text chunks -> metadata -> stable ids -> SourceChunk
```

### 重点观察

- `build_base_metadata()`
- `build_chunk_metadata()`
- `stable_document_id()`
- `stable_chunk_id()`
- `load_and_prepare_chunks()`

### 建议主动修改

- 调大或调小 `chunk_size`
- 看 `chunk_id` 是否仍保持稳定逻辑

---

## 第 5 步：最后看测试在锁定什么

**对应文件**：`tests/test_document_processing.py`

### 重点观察

- 文档发现是否稳定
- 文本加载是否稳定
- 切分偏移是否合理
- stable id 是否稳定

---

## 学完这一章后你应该能回答

- 为什么文档处理是知识输入层，而不是附属功能
- `loader / splitter / metadata / stable id` 各自负责什么
- 为什么第二章一定要把 `SourceChunk[]` 做稳
- 为什么这一步会直接影响第三章和第四章
  把第二章全部主线收束成一个统一入口。

## 第 5 步：看测试如何验证第二章不是“看起来能跑”

**对应文件**：

- [tests/test_document_processing.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/tests/test_document_processing.py)

### 这一步要解决什么

第二章开始，测试的作用已经不只是“目录存在”，而是要验证：

- 文档发现逻辑是否正确
- 文本是否被规范化
- 切分结果是否带偏移范围
- 重复运行时 ID 是否稳定

### 重点观察

- `test_discover_documents_filters_supported_files()`
  防止样例说明文件混进索引输入。
- `test_split_text_returns_chunk_offsets()`
  验证切分结果不只是裸字符串。
- `test_load_and_prepare_chunks_is_stable()`
  验证 repeated indexing 不会随意生成新 ID。

## 推荐完整阅读顺序

如果你是第一次读这一章，建议严格按这个顺序：

1. [data/product_overview.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/data/product_overview.md)
2. [data/faq.txt](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/data/faq.txt)
3. [app/config.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/config.py)
4. [app/ingestion/loaders.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/ingestion/loaders.py)
5. [app/ingestion/splitters.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/ingestion/splitters.py)
6. [app/ingestion/metadata.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/ingestion/metadata.py)
7. [app/indexing/id_generator.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/indexing/id_generator.py)
8. [app/indexing/index_manager.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/indexing/index_manager.py)
9. [scripts/build_index.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/scripts/build_index.py)
10. [scripts/inspect_chunks.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/scripts/inspect_chunks.py)
11. [tests/test_document_processing.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/tests/test_document_processing.py)

## 如果继续实现这套快照，建议按这个顺序

从第二章继续往后做，推荐的局部实施顺序是：

1. 先补更多输入格式
   例如 PDF，但前提是先把 `.md / .txt` 的边界讲清楚。
2. 再补更细的 metadata
   例如 `category / language / tenant_id / version`。
3. 再接 Embedding
   只有稳定 chunk 列表出现后，向量化才有意义。
4. 再接 Vector Store
   只有向量化稳定后，存储和检索参数才值得调。

这个顺序不能反过来。否则最典型的问题是：

- 还没稳定 chunk，就开始调向量库参数
- 还没决定 metadata，后面过滤条件就会反复返工
- 还没确认输入边界，就假装系统已经支持所有格式

## 当前真实进度

这份目录当前代表的真实进度是：

- `Phase 1` 的骨架已经继承下来
- `Phase 2` 的文档处理主链路已经有真实实现
- 生成、向量化、检索仍然是后续章节任务

所以学完这里之后，正确动作是：

1. 先把这一章的切分和 metadata 设计讲清楚
2. 再进入第三章做 Embedding

## 这一章完成后你应该能做到什么

至少应该能做到：

- 能加载 Markdown 和 TXT 文档
- 能解释 chunk overlap 为什么存在
- 能说清 `base metadata` 和 `chunk metadata` 的职责差异
- 能验证重复运行时 `document_id / chunk_id` 为什么稳定
- 能说清第三章为什么必须建立在第二章输出之上
