# phase_2_document_processing

> 第二章代码快照的任务，是把第一章里已经露出来的 `ingestion -> indexing` 链路真正做成可运行实现，让“文件进入系统”这件事先稳定下来。

---

## 核心原则

```text
先看样例文档 -> 再跑切分脚本 -> 再读 loaders / splitters / metadata / index_manager -> 最后用测试确认稳定性
```

这一章的重点不是“完整 RAG 已经做好”，而是：

- 文档如何被加载进来
- 文本如何被切成后续可检索的 chunk
- metadata 为什么必须从这一章开始设计
- `document_id / chunk_id` 为什么要在早期就稳定

- 你现在看到的是 `04_rag` 第二章的真实代码入口
- 这一章默认和 [docs/04_rag/02_document_processing.md](/Users/linruiqiang/work/ai_application/docs/04_rag/02_document_processing.md) 配套阅读
- 没有 API Key 也可以完整学习这一章，因为重点是文档入口和 chunk 生产链路，不是真实模型问答

## 当前目录在整门课里的角色

`phase_2_document_processing` 对应的是：

- 第二章：文档处理

和第一章相比，这一章新增的是：

- 真实的 `.md / .txt` 文档加载
- 更接近真实项目的切分逻辑
- 更完整的 chunk metadata
- 基于稳定源路径的 `document_id`
- 基于内容和序号的 `chunk_id`
- 面向真实样例文档的调试脚本和测试

它暂时仍然不负责：

- 真实 embedding
- 真实向量数据库
- 真实检索排序
- 真实 LLM 生成
- 真实评估回归

## 项目结构

```text
phase_2_document_processing/
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
│   ├── retrievers/
│   ├── prompts/
│   ├── chains/
│   ├── services/
│   ├── evaluation/
│   ├── api/
│   └── observability/
├── data/
│   ├── product_overview.md
│   └── faq.txt
├── scripts/
└── tests/
```

### 这一章最重要的阅读方式

不要被完整目录吓住。

第二章只需要先抓住四个点：

1. `data/`
   看这一章到底拿什么文档做样例输入。
2. `app/ingestion/`
   看文件如何被加载和切分。
3. `app/indexing/`
   看文本如何变成带稳定 ID 的标准 chunk。
4. `scripts/ + tests/`
   看这一章如何验证自己的结果不是凭感觉。

## 为什么第二章仍然沿用第一章的目录规划

第二章没有另起一套结构，而是直接继承第一章的项目骨架，原因很直接：

1. 读者需要看到“这一章到底是在上一章哪里继续长”
2. 文档处理本来就属于 `app/ingestion/` 和 `app/indexing/`，不应该临时新开平行目录
3. 后续 Embedding、Vector Store、Retriever 仍然会沿着这套边界继续补实现

如果第二章为了展示功能而临时把逻辑散落到脚本里，后面会立刻出现两个问题：

- 学习者不知道哪些文件属于项目内核，哪些只是调试入口
- 第三章以后需要再把逻辑搬回 `app/`，造成额外认知成本

### 这一章的目录设计在保护什么

| 目录 | 当前重点 | 为什么现在就要这样分 |
|------|----------|----------------------|
| `data/` | 放真实输入文档 | 文档处理必须从真实输入开始，而不是继续用硬编码字符串 |
| `app/ingestion/` | 负责“文件 -> 文本 -> 切分” | 这一层要和检索、生成解耦 |
| `app/indexing/` | 负责“文本 -> 标准 chunk” | 稳定 ID 和 chunk 组织应该集中处理 |
| `scripts/` | 放观察入口 | 学习者先看到输出，再读内核实现 |
| `tests/` | 放最小验收 | 第二章开始必须验证 ID 稳定和切分边界 |

更细一点看，`app/ingestion/` 和 `app/indexing/` 分开，是因为它们解决的问题不同：

- `loaders.py`
  负责把文件读成统一文本，不决定 chunk 长什么样
- `splitters.py`
  负责切分策略，不负责来源标识和对象封装
- `metadata.py`
  负责定义 chunk 必带信息，不负责文件读取
- `index_manager.py`
  负责把前面几步合并成标准 `SourceChunk`

这就是第二章最重要的代码设计意识：

> 先把“文件进入系统”的链路拆清楚，后面 Embedding 和检索层才能直接复用这份稳定输入。

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

### 3. 这一章运行命令的学习意义

- `build_index.py`
  先看到目录里到底发现了哪些真实文档，以及每份文档被切成几个 chunk。
- `inspect_chunks.py`
  先看到单个 chunk 的 `chunk_id`、字符范围和内容预览。
- `inspect_chunks.py data/faq.txt`
  对比 Markdown 和纯文本文档的切分结果差异。
- `unittest`
  验证文档发现、文本加载、切分偏移和稳定 ID 不是偶然成功。

## 第 1 步：先看输入文档和全局配置

**对应文件**：

- [data/product_overview.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/data/product_overview.md)
- [data/faq.txt](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/data/faq.txt)
- [app/config.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/config.py)

### 这一步要解决什么

第二章不是从抽象切分算法开始，而是先回答：

- 当前到底支持哪些输入格式
- 默认 `chunk_size / chunk_overlap` 设成多少
- 为什么要先拿两种简单格式做样例

### 重点观察

- `supported_suffixes`
  这一章只支持 `.md / .txt`，不假装已经完成 PDF。
- `default_chunk_size / default_chunk_overlap`
  这一章开始，chunk 参数已经进入统一配置，而不是散在脚本里。
- `data/` 下的两份样例
  一份用于观察 Markdown 结构，一份用于观察纯文本场景。

## 第 2 步：看文件如何进入系统

**对应文件**：

- [app/ingestion/loaders.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/ingestion/loaders.py)
- [scripts/build_index.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/scripts/build_index.py)

### 这一步要解决什么

真正的文档处理不是“拿一段字符串直接 split”。

先要解决的是：

- 哪些文件应该被发现
- README 这类说明文件为什么不该进入索引
- 文本进入系统前要做哪些最小规范化

### 重点观察

- `discover_documents()`
  只发现支持的真实输入文档，并排除 `README.md` 这种说明文件。
- `normalize_text()`
  统一换行和尾部空白，但不破坏 Markdown 标题和列表结构。
- `load_document()`
  把“路径存在性、格式支持、具体 loader 路由”统一收口成一个入口。

## 第 3 步：看文本如何被切成可检索 chunk

**对应文件**：

- [app/ingestion/splitters.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/ingestion/splitters.py)
- [scripts/inspect_chunks.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/scripts/inspect_chunks.py)

### 这一步要解决什么

第二章的重点不是“用最复杂的切分器”，而是先把下面几件事讲清楚：

- chunk 不是简单按固定长度生硬截断
- overlap 为什么存在
- chunk 为什么最好带字符范围

### 重点观察

- `TextChunk`
  说明切分层先返回中间对象，再由索引层统一封装成 `SourceChunk`。
- `SplitterConfig.__post_init__()`
  把 `chunk_size` 和 `chunk_overlap` 的合法性检查收进去。
- `_choose_breakpoint()`
  优先在段落、换行、句子或空格边界断开，避免切分点过于生硬。
- `split_text()`
  返回的不只是内容，还有 `start_index / end_index`。

## 第 4 步：看 metadata 和稳定 ID 如何进入 chunk

**对应文件**：

- [app/ingestion/metadata.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/ingestion/metadata.py)
- [app/indexing/id_generator.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/indexing/id_generator.py)
- [app/indexing/index_manager.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/indexing/index_manager.py)

### 这一步要解决什么

到了这一层，第二章真正要完成的事情才算闭环：

```text
path -> text -> text chunks -> metadata -> stable ids -> SourceChunk
```

### 重点观察

- `build_base_metadata()`
  把 `source / filename / suffix / char_count / line_count` 先立住。
- `build_chunk_metadata()`
  补上 `chunk_index / char_start / char_end / chunk_chars`。
- `stable_document_id()`
  用稳定源路径生成文档级 ID。
- `stable_chunk_id()`
  用文档 ID、chunk 序号和内容摘要生成 chunk 级 ID。
- `load_and_prepare_chunks()`
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
