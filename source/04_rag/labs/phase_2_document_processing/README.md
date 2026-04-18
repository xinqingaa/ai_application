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

## 本章定位

- 对应章节：[02_document_processing.md](/Users/linruiqiang/work/ai_application/docs/04_rag/02_document_processing.md)
- 本章目标：让文件真正进入系统，把文本稳定整理成 `SourceChunk[]`，固定 metadata 和 stable id
- 上一章输入契约：第一章已定义 `SourceChunk`，也已定义 `ingestion / indexing` 目录位
- 输出契约：`SourceChunk[]`、`document_id`、`chunk_id`、`base metadata + chunk metadata`
- 本章新增：真实 `.md / .txt` 加载、`discover_documents()`、`normalize_text()`、`TextChunk`、更完整的 metadata、稳定 ID 规则、文档处理测试
- 本章关键文件：`app/ingestion/loaders.py`、`app/ingestion/splitters.py`、`app/ingestion/metadata.py`、`app/indexing/id_generator.py`、`app/indexing/index_manager.py`
- 第一命令：`python scripts/build_index.py`

---

## 项目结构

```text
phase_2_document_processing/
├── README.md
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
python scripts/build_index.py
python scripts/inspect_chunks.py
python scripts/inspect_chunks.py data/faq.txt
python -m unittest discover -s tests
```

### 3. 先跑哪个

建议先跑：

```bash
python scripts/build_index.py
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
python scripts/inspect_chunks.py
python scripts/inspect_chunks.py data/faq.txt
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

## 第 5 步：看测试如何验证第二章不是“看起来能跑”

**对应文件**：`tests/test_document_processing.py`

### 这一步要解决什么

第二章开始，测试的作用已经不只是“目录存在”，而是要验证：

- 文档发现逻辑是否正确
- 文本是否被规范化
- 切分结果是否带偏移范围
- 重复运行时 ID 是否稳定

### 重点观察

- `test_discover_documents_filters_supported_files()`
- `test_split_text_returns_chunk_offsets()`
- `test_load_and_prepare_chunks_is_stable()`

---

## 推荐完整阅读顺序

如果你是第一次读这一章，建议严格按这个顺序：

1. `data/product_overview.md`
2. `data/faq.txt`
3. `app/config.py`
4. `app/ingestion/loaders.py`
5. `app/ingestion/splitters.py`
6. `app/ingestion/metadata.py`
7. `app/indexing/id_generator.py`
8. `app/indexing/index_manager.py`
9. `scripts/build_index.py`
10. `scripts/inspect_chunks.py`
11. `tests/test_document_processing.py`

## 如果继续实现这套快照，建议按这个顺序

1. 先补更多输入格式，例如 PDF，但前提是先把 `.md / .txt` 的边界讲清楚。
2. 再补更细的 metadata，例如 `category / language / tenant_id / version`。
3. 再接 Embedding，只有稳定 chunk 列表出现后，向量化才有意义。
4. 再接 Vector Store，只有向量化稳定后，存储和检索参数才值得调。

这个顺序不能反过来。否则最典型的问题是：

- 还没稳定 chunk，就开始调向量库参数
- 还没决定 metadata，后面过滤条件就会反复返工
- 还没确认输入边界，就假装系统已经支持所有格式

## 学完这一章后你应该能回答

- 为什么文档处理是知识输入层，而不是附属功能
- `loader / splitter / metadata / stable id` 各自负责什么
- 为什么第二章一定要把 `SourceChunk[]` 做稳
- 为什么这一步会直接影响第三章和第四章

## 当前真实进度和下一章

- 当前真实进度：`Phase 1` 的骨架已经继承下来，`Phase 2` 的文档处理主链路已经有真实实现，生成、向量化、检索仍然是后续章节任务
- 完成标准：能解释 `loader / splitter / metadata / stable id` 各自职责，能说明为什么 `SourceChunk[]` 是第三章的真实输入，能看懂 `chunk_id` 和字符范围
- 下一章：在 `SourceChunk[]` 外再加一层向量表示，引入 `EmbeddingProvider`，产出 `EmbeddedChunk[]`
