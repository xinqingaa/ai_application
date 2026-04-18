# 02. 文档处理

> 本节目标：理解 RAG 系统为什么必须先把“文件进入系统”这件事做稳，并能对着 `phase_2_document_processing` 的代码看懂文档加载、切分、metadata 和稳定 ID 是怎样一步步接起来的。

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
- 能说清第二章为什么要沿着第一章骨架继续实现，而不是另起一套结构

### 本章在 `04_rag` 中的位置

第二章是 `04_rag` 第一个真正把“数据进入系统”做成可运行实现的章节。

和第一章相比，这一章不再只是看骨架，而是开始稳定下面这条链路：

```text
文件 -> loader -> 统一文本 -> splitter -> chunk metadata -> stable ids -> SourceChunk
```

后续章节都会建立在这份输出之上：

- 第三章：把这些稳定 chunk 变成向量
- 第四章：把 chunk 和向量写入存储
- 第五章：围绕这些 chunk 做更好的召回
- 第六章：把召回结果接成真正的回答

如果第二章不稳，后面章节的所有优化都会失去基础。

### 学习前提

建议你至少已经具备下面这些基础：

- 已完成 [01_rag_basics.md](/Users/linruiqiang/work/ai_application/docs/04_rag/01_rag_basics.md)
- 已看过 [phase_1_scaffold/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/README.md)
- 已理解 [app/schemas.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_1_scaffold/app/schemas.py) 中 `SourceChunk` 的意义
- 已知道 LangChain 或同类框架里 `Document` 这类对象通常承担什么职责

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

如果第二章一开始就把所有输入格式和所有后续能力都塞进来，学习者只会看到更复杂的工程细节，而抓不住主线。

### 第一入口

本章有两个入口，职责不同：

- 第一阅读入口：
  [source/04_rag/labs/phase_2_document_processing/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/README.md)
- 第一运行入口：
  [scripts/build_index.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/scripts/build_index.py)

为什么这样安排：

- `README` 先帮你建立目录职责、代码阅读顺序和章节边界
- `build_index.py` 先让你看到系统到底发现了哪些真实文档，以及每份文档被切成几个 chunk

### 第二运行入口

真正理解第二章时，还要尽快跑：

- [scripts/inspect_chunks.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/scripts/inspect_chunks.py)

因为第二章最关键的学习对象不是抽象概念，而是：

- 一个 chunk 长什么样
- chunk 带了哪些 metadata
- `chunk_id` 和字符范围如何组织

---

## 2. 先回到大纲：这一章到底要回答什么 📌

这一章必须始终服从 [outline.md](/Users/linruiqiang/work/ai_application/docs/04_rag/outline.md) 的学习路线。

对照大纲，本章核心只回答三类问题：

1. 文档怎样进入系统
2. chunk 怎样被稳定生产出来
3. 为什么这些设计会直接影响后续阶段

### 2.1 什么叫“文档处理”

一句话说：

> 文档处理就是把原始文件整理成后续系统可稳定消费的 chunk 列表。

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

### 2.2 为什么文档处理不是小事

很多人在做 RAG 时，容易把注意力全放在：

- 选哪个 Embedding 模型
- 用哪种向量数据库
- 怎么调 top_k
- 要不要上 rerank

这些当然重要，但前提是：

> 你的输入数据必须先被稳定整理成系统能理解的 chunk。

如果这一层没做好，后面最常见的问题就是：

1. 文档其实根本没被正确读进来
2. 切分边界不稳定，导致召回结果漂移
3. metadata 不完整，后面无法做来源引用和过滤
4. ID 每次都变，导致重复索引和删除变得混乱

所以第二章真正解决的是：

> 让“原始文件”第一次变成“稳定系统对象”。

### 2.3 Loader、Splitter、Metadata、ID 各自负责什么

这四件事很容易被混在一起，但职责必须分清。

| 层 | 解决什么问题 | 不解决什么问题 |
|----|--------------|----------------|
| Loader | 文件怎么读进来、文本怎么规范化 | 不决定 chunk 怎么切 |
| Splitter | 文本如何切成多段 | 不决定来源字段和稳定 ID |
| Metadata | chunk 至少要带哪些描述信息 | 不负责文件解析 |
| Stable ID | 如何让文档和 chunk 可重复定位 | 不决定切分策略本身 |

你当前阶段最需要建立的判断不是“切分器越复杂越好”，而是：

> 每一层先解决一个清晰问题，再把结果交给下一层。

### 2.4 第二章最小主数据流

大纲里的第二章主线可以先压缩成这张图：

```text
data/*.md | data/*.txt
-> discover_documents()
-> load_document()
-> split_text()
-> build_base_metadata()
-> build_chunk_metadata()
-> stable_document_id() / stable_chunk_id()
-> SourceChunk[]
```

这里先记住四个最小对象或概念：

- `raw text`
  从文件读出的统一文本
- `TextChunk`
  splitter 返回的中间切分结果，包含内容和字符范围
- `SourceChunk`
  供后续阶段统一消费的标准 chunk 对象
- `document_id / chunk_id`
  保证重复处理时结果可追踪、可比较、可更新

### 2.5 为什么第二章不能直接跳到 Embedding

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

这也是为什么第二章在整门课里看起来“不是最炫的一章”，但工程上反而是基础章。

---

## 3. 第二章的代码设计与目录规划 📌

### 3.1 为什么第二章直接沿用第一章的骨架

第二章没有为“文档处理”重新起一套目录，而是直接在第一章骨架上继续长，这不是偷懒，而是在保护学习路径。

原因有三点：

1. 学习者需要看到“新增能力具体落在哪些既有目录里”
2. 文档处理本来就是 `ingestion/ + indexing/` 的职责，不应该临时塞到脚本里
3. 第三章以后还会继续沿这套边界扩展，不应该每章都改一次结构

这和第一章建立骨架的目的完全一致：

> 目录不是为了显得工程化，而是为了让后续章节知道应该往哪里继续补。

### 3.2 为什么 `data / ingestion / indexing / scripts / tests` 要这样拆

这一章最值得讲的，不只是“有哪些文件”，而是这些文件为什么要分开。

| 目录/模块 | 当前职责 | 为什么单独存在 |
|-----------|----------|----------------|
| `data/` | 放样例输入文档 | 第二章必须对真实文件进行观察，而不是继续用硬编码字符串 |
| `app/ingestion/loaders.py` | 发现文档、路由 loader、做最小文本规范化 | 读取文件的逻辑不该和切分、索引混写 |
| `app/ingestion/splitters.py` | 把文本切成带偏移范围的中间 chunk | 切分策略是独立变化点，后续最常被调 |
| `app/ingestion/metadata.py` | 定义基础 metadata 和 chunk metadata | metadata 设计会长期影响引用、过滤和调试 |
| `app/indexing/id_generator.py` | 生成稳定文档 ID 和 chunk ID | 稳定身份不该散落在脚本里临时拼接 |
| `app/indexing/index_manager.py` | 把前面几步收束成 `SourceChunk` 入口 | 第二章的真正收口点 |
| `scripts/` | 放第一运行入口和观察入口 | 让学习者先看到结果，再追代码 |
| `tests/` | 放最小稳定性验证 | 从第二章开始，就必须验证“重复运行是否稳定” |

如果不这样拆，最容易出现的问题是：

1. 文件读取、切分、metadata、ID 全混在一个脚本里
2. 后面 Embedding 章节必须反向重构第二章代码
3. 文档处理看似能跑，但没有稳定入口可复用

### 3.3 `ingestion` 和 `indexing` 的边界为什么重要

这是第二章最核心的代码设计点之一。

很多初学者会把“文档处理”和“索引准备”当成同一件事，但这里故意拆开，是为了保护边界：

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

1. 切分策略可以改，但 `SourceChunk` 入口不必跟着散掉
2. metadata 可以扩，但 loader 不必被迫承担后续逻辑
3. 第三章可以直接消费 `SourceChunk[]`，而不必关心文件读取细节

### 3.4 为什么稳定 ID 必须第二章就出现

这一点经常被低估。

如果没有稳定 `document_id / chunk_id`，后面很快就会出现这些问题：

- 同一份文档重复导入后无法判断是不是同一份数据
- 向量存储里难以做更新和删除
- 评估和调试时无法稳定定位坏 chunk
- 检索结果变化时，难以判断是内容变了还是 ID 漂了

所以第二章引入稳定 ID，不是“提前工程化”，而是：

> 从一开始就让后续阶段有可复用的身份锚点。

---

## 4. 第二章对应代码怎么读 📌

### 4.1 本章代码映射表

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

### 4.2 为什么这些文件值得先看

第二章真正的稳定接口，主要集中在四个位置：

- `load_document()`
  统一“路径检查 + 格式判断 + loader 路由”
- `split_text()`
  统一“切分策略 + overlap + 字符范围”
- `build_chunk_metadata()`
  统一“这个 chunk 至少要带哪些信息”
- `load_and_prepare_chunks()`
  统一“把文档转成标准 `SourceChunk[]`”

后续章节会不断围绕这几个入口继续扩展，而不是另起炉灶。

### 4.3 为什么 `scripts` 在这一章仍然很重要

很多人会觉得脚本只是临时工具，但在教学阶段它很重要，因为：

1. 先跑脚本能立刻看到真实输出
2. 输出能反向帮助你理解 chunk 是怎么形成的
3. 调整参数后，最容易先在脚本层观察变化

第二章推荐优先跑的不是未来的 API，而是：

- `build_index.py`
- `inspect_chunks.py`

因为这一章最该先建立的是输入直觉，而不是对外服务直觉。

---

## 5. 推荐学习顺序 📌

这部分是强制顺序，不建议跳着读。

### 第一步：先回看大纲和第一章边界

先读：

- [outline.md](/Users/linruiqiang/work/ai_application/docs/04_rag/outline.md) 中：
  `二、文档处理`
- [01_rag_basics.md](/Users/linruiqiang/work/ai_application/docs/04_rag/01_rag_basics.md) 中：
  第一章关于 `ingestion / indexing` 的预告部分

这一步的目的不是复述大纲，而是先知道：

- 第二章新增的到底是哪一层
- 为什么这一章不直接跳去做向量和检索

### 第二步：打开第一阅读入口

读：

- [phase_2_document_processing/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/README.md)

这一步先解决三个问题：

1. 第二章新增了哪些真实代码
2. 本章主入口为什么是 `build_index.py` 和 `inspect_chunks.py`
3. 哪些模块仍然只是沿用第一章的占位骨架

### 第三步：先跑文档发现入口

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

1. README 说明文件没有被当成真实文档
2. 同一个 chunk 配置下，不同类型文档会被切成不同数量的 chunk

### 第四步：再跑 chunk 观察脚本

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
    preview=# Product Overview  The support assistant answers questions about onboarding, de
```

第二份样例输出长这样：

```text
Inspecting: data/faq.txt
Prepared 3 chunk(s).
[0] b986b0425c61d1bcc7fa01351465bb41c924f547:0:52b4737568a8 chars=0:161 len=161
    source=data/faq.txt
    preview=FAQ  Q: Why do we create stable document IDs? A: Stable IDs make repeated indexi
```

这一步先看懂三件事：

- `chunk_id` 已经不再是临时字符串，而是稳定格式
- 每个 chunk 已经带了字符范围
- Markdown 和纯文本文档的切分形状确实不同

### 第五步：再读核心实现文件

建议按这个顺序：

1. [app/config.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/config.py)
2. [app/ingestion/loaders.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/ingestion/loaders.py)
3. [app/ingestion/splitters.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/ingestion/splitters.py)
4. [app/ingestion/metadata.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/ingestion/metadata.py)
5. [app/indexing/id_generator.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/indexing/id_generator.py)
6. [app/indexing/index_manager.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/indexing/index_manager.py)

### 第六步：最后跑测试

运行：

```bash
python3 -m unittest discover -s tests
```

当前输出：

```text
.....
----------------------------------------------------------------------
Ran 5 tests in 0.000s

OK
```

这一步的目的不是凑测试数量，而是确认：

- 第二章的文档发现逻辑可验证
- 切分结果不是裸字符串
- 稳定 ID 逻辑能重复通过

### 卡住时先回看哪里

如果中途卡住，先回看这三个位置：

1. [phase_2_document_processing/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/README.md)
2. 本章的“代码映射表”
3. [tests/test_document_processing.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/tests/test_document_processing.py)

### 最低通过标准

至少要做到：

1. 能跑通两个脚本和最小测试
2. 能解释 chunk overlap 和字符范围为什么存在
3. 能说清为什么 `README.md` 不该进入索引输入
4. 能说清 `loaders / splitters / metadata / indexing` 的边界差异

---

## 6. 这章的实施步骤应该怎么理解 📌

### 6.1 为什么实施顺序不能反过来

第二章很容易犯的错误是：

> 觉得只要先接一个 embedding 模型，后面问题再慢慢修。

这在实现上通常会很快失控。

因为如果顺序反了，常见问题会立刻出现：

- 还没决定输入边界，就开始做向量写入
- 还没稳定 chunk，就开始比较相似度结果
- 还没设计 metadata，就开始讨论过滤条件
- 还没引入稳定 ID，就开始想更新和删除逻辑

所以正确顺序不是“哪个看起来更高级先做哪个”，而是：

> 先把文档输入层做成稳定接口，再把它交给后面的向量和检索层。

### 6.2 第二章内部的建议实施顺序

可以把这一章的实施顺序理解成下面这张表：

| 步骤 | 先做什么 | 主要落在哪些模块 | 这一层解决什么问题 |
|------|----------|------------------|--------------------|
| 1 | 先确定支持哪些输入格式 | `app/config.py`、`data/` | 先固定当前章节边界，不假装支持所有格式 |
| 2 | 实现文档发现和文本加载 | `app/ingestion/loaders.py` | 让真实文件能稳定进入系统 |
| 3 | 实现切分逻辑 | `app/ingestion/splitters.py` | 让文本变成可检索的 chunk 片段 |
| 4 | 设计 metadata | `app/ingestion/metadata.py` | 让 chunk 从第一天就带上来源信息 |
| 5 | 设计稳定 ID | `app/indexing/id_generator.py` | 让重复处理和后续删除更新成为可能 |
| 6 | 收束成统一 chunk 入口 | `app/indexing/index_manager.py` | 把前面几步变成标准 `SourceChunk[]` |
| 7 | 用脚本和测试验证 | `scripts/`、`tests/` | 让第二章形成真实闭环，而不是停在代码片段 |

### 6.3 为什么第二章先支持 `.md / .txt`

这是一个很有代表性的边界判断。

第二章故意只支持 `.md / .txt`，是因为：

1. 这两种格式足够展示“发现文件 -> 读取文本 -> 切分 -> metadata -> ID”的完整主线
2. 不需要额外引入 PDF 解析或 OCR 依赖
3. 可以把教学焦点放在 chunk 生产链路，而不是格式兼容细节

这不是说 PDF 不重要，而是：

> 第二章要先把通用链路讲清楚，再在后续迭代里补更复杂格式。

### 6.4 如果你来继续实现，应该先补哪几层

如果你接着做 `Phase 3` 以后，建议按这个顺序推进：

1. 先确认第二章输出的 `SourceChunk[]` 已经稳定
2. 再让 `embeddings/` 直接消费这些 chunk
3. 再把向量和 metadata 写入存储层
4. 再在检索层比较不同召回策略

这也是为什么第二章写完后，最自然的下一步不是去改 Prompt，而是进入 Embedding 章节。

---

## 7. 建议主动修改的地方 📌

### 修改 1：改 chunk 参数

调整 [app/config.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/config.py) 里的：

- `default_chunk_size`
- `default_chunk_overlap`

然后重新跑：

```bash
python3 scripts/build_index.py
python3 scripts/inspect_chunks.py
```

重点观察：

- chunk 数量有没有明显变化
- preview 是否开始更碎或更长
- overlap 变大后，字符范围重叠是否更明显

### 修改 2：给 metadata 增加字段

在 [app/ingestion/metadata.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/ingestion/metadata.py) 中新增：

- `language`
- `category`
- `version`

然后重新观察 `inspect_chunks.py` 输出。

这会帮助你提前理解：

- metadata 为什么会长期影响引用、过滤和调试

### 修改 3：新增一份样例文档

在 [data/](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/data) 中新增一个 `.md` 或 `.txt` 文件，再重新跑：

```bash
python3 scripts/build_index.py
```

重点观察：

- `discover_documents()` 是否正确发现它
- chunk 总数是否随文档变化而变化
- 文档 ID 是否和文件路径稳定相关

### 修改 4：故意把 `chunk_overlap` 设错

把 `chunk_overlap` 改成大于等于 `chunk_size`，再运行测试或脚本。

这会帮助你理解：

- 为什么 `SplitterConfig.__post_init__()` 要提前校验参数，而不是等到出错时再查

---

## 8. 本章最容易出现的误区 📌

1. **把 loader 当成“只要能读出字符串就行”**
   错。loader 还决定了哪些文件会进入系统，以及最小规范化如何做。
2. **以为 chunk 只是简单切几段字符串**
   错。chunk 的边界、范围和 metadata 会长期影响检索和调试。
3. **以为 metadata 可以等检索或 API 章节再补**
   错。来源、文件名、范围这些信息应该在第二章就稳定下来。
4. **以为 stable ID 只是后期工程化问题**
   错。没有稳定 ID，后面几乎所有增量更新和坏案例定位都会变麻烦。
5. **看到脚本能跑，就以为这一章已经不需要测试**
   错。第二章开始就必须验证“重复运行是否稳定”。

---

## 9. 本章完成标准 📌

完成本章后，你至少应该能做到：

1. 能说清第二章解决的是哪一层问题，而不是笼统说“做了预处理”
2. 能运行第二章脚本并解释输出里的 chunk 数量、ID 和字符范围
3. 能说明 `loaders / splitters / metadata / index_manager` 分别负责什么
4. 能解释为什么 `document_id / chunk_id` 需要稳定
5. 能说清第三章为什么必须建立在第二章的输出之上

如果你现在还做不到这些，就说明第二章还没有真正学完。
