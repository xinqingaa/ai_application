# 02. 文档处理

> 本节目标：把“原始文件进入系统”这件事讲清楚，并能对着 `phase_2_document_processing` 的代码看懂文档发现、文本规范化、切分、metadata 和稳定 ID 是怎样收束成标准 `SourceChunk` 的。

---

## 1. 概述

### 学习目标

完成本章后，你应该能够：

- 能解释为什么文档处理是 RAG 的知识入口，而不是附属功能
- 能加载至少一种本地文档格式，并说明 loader 在系统里的边界
- 能解释 `chunk_size / chunk_overlap` 为什么会直接影响后续检索效果
- 能区分 `base metadata` 和 `chunk metadata` 的职责
- 能说明为什么 `document_id / chunk_id` 必须在早期就稳定
- 能运行第二章的脚本和测试，并读懂输出在表达什么
- 能解释第二章怎样把第一章骨架变成真实输入层

### 本章在 `04_rag` 中的位置

第二章是 `04_rag` 第一个真正把“数据进入系统”做成可运行实现的章节。

和第一章相比，这一章不再只看骨架，而是把下面这条链路做实：

```text
文件 -> loader -> 统一文本 -> splitter -> metadata -> stable ids -> SourceChunk
```

后续章节都会建立在这份输出之上：

- 第三章：把这些稳定 chunk 变成向量
- 第四章：把 chunk 和向量写入存储
- 第五章：围绕这些 chunk 做更好的召回
- 第六章：把召回结果接成真正的回答

### 学习前提

建议你至少已经具备下面这些基础：

- 已完成 [01_rag_basics.md](/Users/linruiqiang/work/ai_application/docs/04_rag/01_rag_basics.md)
- 已看过 [phase_1_scaffold/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/README.md)
- 已理解 [app/schemas.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/schemas.py) 中 `SourceChunk` 的意义

### 本章边界

本章重点解决的是：

1. 文档如何被发现和读取
2. 文本如何被规范化
3. 文本如何被切成后续可检索的 chunk
4. metadata 从哪一层开始设计
5. 稳定 ID 为什么必须提前出现

本章不展开：

- PDF / OCR / 复杂表格解析
- HTML、网页抓取、知识库同步
- 真实 Embedding
- 真实向量数据库
- 检索排序和 Rerank
- 完整 RAG 问答生成

### 第一入口

本章有两个入口，职责不同：

- 第一阅读入口：
  [phase_2_document_processing/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/README.md)
- 第一运行入口：
  [scripts/build_index.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/scripts/build_index.py)

为什么这样安排：

- `README` 先帮你建立目录职责、阅读顺序和当前章节边界
- `build_index.py` 先让你看到系统到底发现了哪些真实文档，以及每份文档被切成几个 chunk

### 第二运行入口

真正理解第二章时，还要尽快跑：

- [scripts/inspect_chunks.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/scripts/inspect_chunks.py)

因为第二章最关键的学习对象不是抽象概念，而是：

- 一个 chunk 长什么样
- chunk 带了哪些 metadata
- `chunk_id` 和字符范围如何组织

---

## 2. 这一章真正要解决什么问题 📌

### 2.1 什么叫“文档处理”

一句话说：

> 文档处理就是把原始文件整理成后续系统可稳定消费的 `SourceChunk[]`。

最小流程长这样：

```text
文件
-> 判断格式
-> 读取文本
-> 做最小规范化
-> 切成 chunks
-> 为每个 chunk 注入 metadata
-> 生成稳定 document_id / chunk_id
```

这件事重要的原因不是“多了几个预处理步骤”，而是：

- 后续向量化必须知道到底要对哪些 chunk 做 embedding
- 后续检索必须知道 chunk 从哪里来
- 后续删除和增量更新必须依赖稳定 ID
- 后续引用和调试必须依赖 metadata

### 2.2 第二章的核心完成物是什么

第二章的真正完成物不是“能读文件”，而是：

```text
path -> text -> text chunks -> metadata -> stable ids -> SourceChunk[]
```

这里最该先记住四个对象或概念：

- `raw text`
  从文件读出的统一文本
- `TextChunk`
  splitter 返回的中间切分结果，包含内容和字符范围
- `SourceChunk`
  后续阶段统一消费的标准 chunk 对象
- `document_id / chunk_id`
  保证重复处理时结果可追踪、可比较、可更新

### 2.3 为什么第二章不能直接跳到 Embedding

因为第三章真正需要的输入不是“文件”，而是：

```text
稳定的 chunk 列表
+ 每个 chunk 的来源信息
+ 可重复定位的稳定 ID
```

如果第二章没有先把这些内容固定下来，第三章会立刻出现几个问题：

- 相同文档每次 embedding 的输入不一致
- 后续向量写入无法知道文档和 chunk 的身份
- 删除、重建、重排都没有稳定锚点

### 2.4 Loader、Splitter、Metadata、ID 各自负责什么

这四件事很容易被混在一起，但职责必须分清。

| 层 | 解决什么问题 | 不解决什么问题 |
|----|--------------|----------------|
| Loader | 文件怎么读进来、文本怎么规范化 | 不决定 chunk 怎么切 |
| Splitter | 文本如何切成多段 | 不决定来源字段和稳定 ID |
| Metadata | chunk 至少要带哪些描述信息 | 不负责文件解析 |
| Stable ID | 如何让文档和 chunk 可重复定位 | 不决定切分策略本身 |

这一章最重要的判断不是“切分器越复杂越好”，而是：

> 每一层先解决一个清晰问题，再把结果交给下一层。

---

## 3. 第二章的代码设计与目录规划 📌

### 3.1 为什么第二章沿用第一章的骨架

第二章没有为“文档处理”重新起一套目录，而是直接在第一章骨架上继续长，原因很简单：

1. 学习者需要看到“新增能力具体落在哪些既有目录里”
2. 文档处理本来就是 `ingestion/ + indexing/` 的职责，不应该临时塞到脚本里
3. 后续 Embedding、Vector Store、Retriever 仍然会沿着这套边界继续补实现

### 3.2 为什么 `data / ingestion / indexing / scripts / tests` 要这样拆

| 目录/模块 | 当前职责 | 为什么单独存在 |
|-----------|----------|----------------|
| `data/` | 放样例输入文档 | 第二章必须从真实文件开始观察 |
| `app/ingestion/loaders.py` | 发现文档、路由 loader、做最小文本规范化 | 读取文件的逻辑不该和切分、索引混写 |
| `app/ingestion/splitters.py` | 把文本切成带偏移范围的中间 chunk | 切分策略是独立变化点，后续最常被调 |
| `app/ingestion/metadata.py` | 定义基础 metadata 和 chunk metadata | metadata 设计会长期影响引用、过滤和调试 |
| `app/indexing/id_generator.py` | 生成稳定文档 ID 和 chunk ID | 稳定身份不该散落在脚本里临时拼接 |
| `app/indexing/index_manager.py` | 把前面几步收束成 `SourceChunk` 入口 | 第二章真正的收口点 |
| `scripts/` | 放第一运行入口和观察入口 | 让学习者先看到结果，再追代码 |
| `tests/` | 放最小稳定性验证 | 第二章开始就必须验证重复运行是否稳定 |

### 3.3 `ingestion` 和 `indexing` 的边界为什么重要

这是第二章最重要的代码设计点。

这里故意把两层拆开，是为了保护边界：

- `ingestion`
  关注“文件和文本本身”
- `indexing`
  关注“怎样把文本收束成系统标准对象”

具体来说：

- `loaders.py`
  解决“读什么、怎么读、哪些文件该进系统”
- `splitters.py`
  解决“按什么策略切”
- `metadata.py`
  解决“chunk 至少带哪些说明信息”
- `index_manager.py`
  解决“如何组合前面结果，形成统一输出”

这套拆法的价值在于：

1. 切分策略可以改，但 `SourceChunk` 入口不必散掉
2. metadata 可以扩，但 loader 不必承担后续逻辑
3. 第三章可以直接消费 `SourceChunk[]`，而不必关心文件读取细节

### 3.4 为什么稳定 ID 必须第二章就出现

如果没有稳定 `document_id / chunk_id`，后面很快就会出现这些问题：

- 同一份文档重复导入后无法判断是不是同一份数据
- 向量存储里难以做更新和删除
- 评估和调试时无法稳定定位坏 chunk
- 检索结果变化时，难以判断是内容变了还是 ID 漂了

所以第二章引入稳定 ID，不是“提前工程化”，而是：

> 从一开始就让后续阶段有可复用的身份锚点。

---

## 4. 推荐阅读与运行顺序 📌

### 第一步：先打开第一阅读入口

读：

- [phase_2_document_processing/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/README.md)

这一步先解决三个问题：

1. 第二章新增了哪些真实代码
2. 本章主入口为什么是 `build_index.py` 和 `inspect_chunks.py`
3. 哪些模块仍然只是沿用第一章骨架

### 第二步：先跑文档发现入口

运行：

```bash
cd source/04_rag/labs/phase_2_document_processing
python3 scripts/build_index.py
```

当前你会看到：

```text
Discovered 2 document(s) under data.
- data/faq.txt: 3 chunk(s)
- data/product_overview.md: 5 chunk(s)
Chunk config: size=220, overlap=40
Prepared 8 chunk(s) in total.
```

先建立两个直觉：

1. `README.md` 说明文件没有被当成真实输入
2. 同一个 chunk 配置下，不同类型文档会被切成不同数量的 chunk

### 第三步：再跑 chunk 观察脚本

运行：

```bash
python3 scripts/inspect_chunks.py
python3 scripts/inspect_chunks.py data/faq.txt
```

当前第一份样例输出长这样：

```text
Inspecting: data/product_overview.md
Prepared 5 chunk(s).
[0] d35e967f489c37b830e4ceb98d39c727090934f6:0:8b0be613fb59 chars=0:207 len=207
    source=data/product_overview.md
```

这一组命令最该先看懂三件事：

- `chunk_id` 已经不是临时字符串，而是稳定格式
- 每个 chunk 已经带了字符范围
- Markdown 和纯文本文档的切分形状确实不同

### 第四步：再读核心实现文件

建议按这个顺序：

1. [app/config.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/config.py)
2. [app/ingestion/loaders.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/ingestion/loaders.py)
3. [app/ingestion/splitters.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/ingestion/splitters.py)
4. [app/ingestion/metadata.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/ingestion/metadata.py)
5. [app/indexing/id_generator.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/indexing/id_generator.py)
6. [app/indexing/index_manager.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/indexing/index_manager.py)

### 第五步：最后跑测试

运行：

```bash
python3 -m unittest discover -s tests
```

这一步的目的不是凑测试数量，而是确认：

- 文档发现逻辑可验证
- 切分结果不是裸字符串
- 稳定 ID 逻辑能重复通过

### 卡住时先回看哪里

如果中途卡住，先回看这三个位置：

1. [phase_2_document_processing/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/README.md)
2. 本章的“代码映射表”
3. [tests/test_document_processing.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/tests/test_document_processing.py)

---

## 5. 本章实施步骤应该怎么理解 📌

第二章的正确顺序不是“先接 embedding 再慢慢修输入”，而是：

| 步骤 | 先做什么 | 主要落在哪些模块 | 这一步在解决什么 |
|------|----------|------------------|------------------|
| 1 | 先确定支持哪些输入格式 | `app/config.py`、`data/` | 先固定当前章节边界，不假装支持所有格式 |
| 2 | 先把文件读进来并做最小规范化 | `app/ingestion/loaders.py` | 让系统拥有稳定文本输入 |
| 3 | 再把文本切成可检索 chunk | `app/ingestion/splitters.py` | 让后续阶段有明确检索单位 |
| 4 | 给 chunk 注入 metadata 和稳定 ID | `metadata.py`、`id_generator.py` | 让后续引用、过滤、更新都有锚点 |
| 5 | 收束成标准 `SourceChunk[]` | `app/indexing/index_manager.py` | 给第三章提供统一输入 |
| 6 | 用脚本和测试验证稳定性 | `scripts/`、`tests/` | 避免后续优化只能凭感觉推进 |

---

## 6. 本章代码映射表

| 文档部分 | 对应代码/文档 | 角色 | 说明 |
|----------|---------------|------|------|
| 本章第一阅读入口 | [phase_2_document_processing/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/README.md) | 主入口 | 先理解当前目录职责、运行方式和阅读顺序 |
| 样例输入 | [data/product_overview.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/data/product_overview.md) | 主示例 | 观察 Markdown 文档进入系统后的效果 |
| 样例输入 | [data/faq.txt](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/data/faq.txt) | 对照示例 | 观察纯文本文档的切分效果 |
| 文档发现和加载 | [app/ingestion/loaders.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/ingestion/loaders.py) | 核心流程 | 负责发现支持文档、规范化文本并路由 loader |
| metadata 设计 | [app/ingestion/metadata.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/ingestion/metadata.py) | 核心流程 | 定义基础 metadata 与 chunk metadata |
| 文本切分 | [app/ingestion/splitters.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/ingestion/splitters.py) | 核心流程 | 负责 chunk 切分和字符范围计算 |
| 稳定 ID | [app/indexing/id_generator.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/indexing/id_generator.py) | 核心工具 | 生成 `document_id / chunk_id` |
| chunk 收口 | [app/indexing/index_manager.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/indexing/index_manager.py) | 核心入口 | 把文档处理结果统一转换为 `SourceChunk` |
| 第一运行入口 | [scripts/build_index.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/scripts/build_index.py) | 主示例文件 | 先看到真实文档发现和 chunk 总量 |
| chunk 观察入口 | [scripts/inspect_chunks.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/scripts/inspect_chunks.py) | 扩展示例 | 先看到 chunk 预览、ID 和字符范围 |
| 最小验证 | [tests/test_document_processing.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/tests/test_document_processing.py) | 验收入口 | 验证文档发现、切分和稳定 ID |

---

## 7. 实践任务

1. 解释为什么第二章真正交付的是 `SourceChunk[]`，而不是“能加载文件”。
2. 对照 [loaders.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/ingestion/loaders.py) 和 [splitters.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/ingestion/splitters.py)，说清 loader 和 splitter 的职责边界。
3. 跑一次 [scripts/inspect_chunks.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/scripts/inspect_chunks.py)，解释 `char_start / char_end / chunk_chars` 为什么重要。
4. 修改 `chunk_size` 或 `chunk_overlap`，重新运行脚本，观察 chunk 数量和字符范围如何变化。

---

## 8. 完成标准

完成这一章后，至少应满足：

- 能解释为什么文档处理是 RAG 的知识入口
- 能说明 `loaders / splitters / metadata / indexing` 的边界差异
- 能运行第二章脚本和测试，并读懂输出
- 能解释为什么 `document_id / chunk_id` 必须尽早稳定
- 能说明第二章为什么要先把 `SourceChunk` 做稳，再进入 Embedding 和检索
