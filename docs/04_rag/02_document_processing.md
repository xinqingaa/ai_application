# 02. 文档处理

> 本章目标：把“原始文件进入系统”这件事讲清楚，理解文档发现、真实 Loader、文本规范化、切分、metadata、稳定 ID 和最小 `DocumentPipeline` 为什么必须尽早确定，并把它们收束成稳定、可重复的 `SourceChunk[]`。

---

## 1. 概述

### 学习目标

- 理解为什么文档处理是 RAG 的知识入口，而不是附属功能
- 理解 `loader / splitter / metadata / stable id / pipeline` 各自负责什么
- 理解 `chunk_size / chunk_overlap` 为什么会直接影响后续检索效果
- 能区分 `base metadata` 和 `chunk metadata` 的职责
- 理解为什么 `document_id / chunk_id` 必须从第二章就稳定下来
- 能说明为什么 Markdown 适合按标题感知切分
- 能说明为什么真实 PDF 解析可以进入第二章，而 OCR 仍应留在后面
- 能对着第二章代码看懂 `path -> SourceChunk[]` 的完整过程

### 预计学习时间

- 文档输入层理解：40 分钟
- Loader 扩展与切分策略：40-60 分钟
- metadata、稳定 ID 与 pipeline：40-60 分钟
- 第二章代码实践：40-60 分钟

### 本章在 AI 应用中的重要性

| 场景 | 本章先解决什么 |
|------|----------------|
| 知识库接入 | 哪些文件该进系统，哪些不该进 |
| 多格式输入 | `.txt / .md / .pdf` 应该怎样选择不同 loader |
| 检索工程 | chunk 到底该长什么样，才能被后面稳定向量化 |
| 长期维护 | 更新、删除、调试和引用为什么都依赖稳定 ID 和 metadata |

### 学习前提

- 建议先完成第一章，理解“不是所有问题都该先进 RAG”
- 建议先完成 `02_llm` 的上下文、结构化输出和错误处理部分
- 如果已经理解 `Document / Retriever` 这些基础抽象，后面会更顺畅
- 但第二章本身不要求你先懂 LangChain、Embedding 或向量数据库

### 本章与前后章节的关系

第一章解决的是：

1. 为什么要做 RAG
2. 最小 `2-step RAG` 在线链路长什么样
3. 什么情况下该用什么方案

第二章接着解决的是：

1. 原始文件怎样进入系统
2. 文本怎样变成标准 chunk
3. metadata 和稳定 ID 为什么必须尽早出现
4. 为什么输入层需要最小 pipeline 和治理视角

第三章会继续建立在这里之上：

1. 直接消费稳定的 `SourceChunk[]`
2. 把 chunk 再变成向量表示

第四章会继续依赖这里：

1. 让向量库知道“自己在存哪份文档、哪个 chunk”
2. 让后续删除、更新和回填有稳定锚点

### 本章代码入口

本章对应的代码目录是：

- [README.md](../../source/04_rag/02_document_processing/README.md)
- [requirements.txt](../../source/04_rag/02_document_processing/requirements.txt)
- [document_processing.py](../../source/04_rag/02_document_processing/document_processing.py)
- [document_processing_golden_set.json](../../source/04_rag/02_document_processing/document_processing_golden_set.json)
- [01_discover_and_load.py](../../source/04_rag/02_document_processing/01_discover_and_load.py)
- [02_split_and_inspect.py](../../source/04_rag/02_document_processing/02_split_and_inspect.py)
- [03_build_chunks.py](../../source/04_rag/02_document_processing/03_build_chunks.py)
- [04_loader_extensions.py](../../source/04_rag/02_document_processing/04_loader_extensions.py)
- [05_document_pipeline.py](../../source/04_rag/02_document_processing/05_document_pipeline.py)
- [tests/test_document_processing.py](../../source/04_rag/02_document_processing/tests/test_document_processing.py)

### 本章边界

本章重点解决：

1. 文档发现和读取
2. 真实 PDF 文本提取
3. 文本规范化
4. 切分策略
5. Markdown 标题感知切分
6. metadata 设计
7. 稳定 ID
8. 最小 `DocumentPipeline`

本章不展开：

- OCR
- 扫描件 PDF
- 复杂表格解析
- 网页抓取和知识库同步
- 真实 Embedding
- 真实向量数据库
- 检索排序和 Rerank
- 完整 RAG 问答生成
- 完整 ingestion 平台或企业级同步系统

这里故意只保留：

- `.md / .txt / .pdf`
- 本地样例文件
- 平铺代码目录
- 一条最小输入层 pipeline

目的不是追求格式覆盖最全，而是先把文档处理主线讲清楚。

---

## 2. 文档处理到底在做什么 📌

### 2.1 什么叫“文档进入系统”

很多人一提文档处理，就会马上把注意力放在“切分器参数怎么调”。

但更完整的视角应该是：

```text
文件
-> 判断是否支持
-> 选择 loader
-> 读取文本
-> 做最小规范化
-> 按文档类型选择切分策略
-> 注入 metadata
-> 生成稳定 document_id / chunk_id
-> 产出 SourceChunk[]
```

也就是说，第二章不是在做一个单独的“文本预处理工具”，而是在做：

> RAG 系统的知识输入层。

### 2.2 第二章真正交付的是什么

第二章真正交付的不是“能读 Markdown”或“能把文本切开”，而是：

```text
path -> text -> TextChunk[] -> metadata -> stable ids -> SourceChunk[]
```

这里最该先记住的六个概念是：

- `DocumentCandidate`
  表示一个文件是否应该进入系统
- `LoadedDocument`
  表示文件已经被 loader 读成统一文本
- `TextChunk`
  splitter 返回的中间对象，包含内容和字符范围
- `SourceChunk`
  后续阶段统一消费的标准 chunk 对象
- `document_id / chunk_id`
  用来保证重复处理、更新、删除和调试都有稳定锚点
- `DocumentPipeline`
  把这一整套动作收束成可观察、可复跑的输入层闭环

### 2.3 为什么文档处理不能被当成附属功能

如果第二章没有先把文档输入层做稳，后面很快就会出现问题：

- 相同文档每次生成的 chunk 不一致
- embedding 阶段无法判断“这是谁的向量”
- 删除和增量更新没有稳定身份
- 调试时无法确认是内容变了还是 ID 漂了

所以第二章并不是“还没到检索前的准备工作”，而是：

> 在给后面的向量化、向量存储、检索和评估打地基。

### 2.4 为什么第二章不该急着接 Embedding

如果这一步还没把 `SourceChunk[]` 做稳，就急着进第三章，问题只会被推迟，不会消失。

比如：

- 你会在第三章才发现 chunk 边界根本不合理
- 你会在第四章才发现不知道该删哪个向量
- 你会在第五章才发现 metadata 根本不够做过滤和引用

所以第二章最重要的价值不是“离 embedding 更近了一步”，而是：

> 先把知识输入层做成一个稳定的、可重复的标准接口。

### 2.5 第二章的运行时主链路

这一章最值得先建立手感的，不是某个具体参数，而是一条完整的运行时链路：

```text
Path
-> DocumentCandidate
-> LoadedDocument
-> TextChunk / MarkdownSection / ChunkDraft
-> SourceChunk
-> DocumentPipelineResult
```

如果你能把这条链路讲清楚，第二章的大部分内容就已经真正掌握了。

### 2.6 为什么第二章交付的是“稳定输入层”

很多学习资料会把第二章讲成：

- 读取文件
- 文本切分
- 结束

这种讲法不够。

更准确的说法是：

> 第二章在定义后续章节要消费的标准输入接口。

后面的 embedding、向量库、检索和引用，默认都要建立在这一章的输出之上。

所以这里的重点不是“先凑合切一下”，而是：

- 输出结构要统一
- 字段要够用
- ID 要稳定
- 行为要能回归

---

## 3. 更真实的 Loader 认知 📌

### 3.1 为什么第二章现在要补真实 Loader

如果第二章永远只保留 `.md / .txt` 的 toy 输入，你会很容易误以为：

- loader 只是 `Path.read_text()`
- 所有文档都能天然得到干净文本
- 输入层复杂度主要都在 splitter

这不对。

真实系统里，loader 本身就是输入层的一大块复杂度来源。

所以第二章现在要至少把三类现实拉进来：

- 纯文本 loader
- Markdown loader
- 真实 PDF 文本提取

### 3.2 三种输入分别在解决什么

| 输入 | 当前做法 | 第二章想让你看到什么 |
|------|----------|----------------------|
| `.txt` | 直接读取后规范化 | 最简单的基线输入 |
| `.md` | 读取后按标题感知切分 | 文档结构本身可以指导 chunk 设计 |
| `.pdf` | 用 `pypdf.PdfReader` 抽取文本 | 同样是“文件”，loader 复杂度也不一样 |

第二章不是要把所有格式都一次性讲完，而是要让你看到：

> loader 选择本身就是输入层设计的一部分。

### 3.3 `inspect_document_candidate()` 在做什么

这一步很多人会忽略，但它其实是输入层的第一道边界。

`inspect_document_candidate()` 负责回答：

- 这是不是文件
- 这是不是知识源
- 当前后缀是否支持
- 如果支持，预计会走哪个 loader

它返回的不是裸布尔值，而是 `DocumentCandidate`：

- `accepted`
- `reason`

这个设计的教学意义非常强，因为它会迫使你从一开始就把“为什么接受 / 为什么忽略”显式化。

### 3.4 `choose_loader_name()` 和 `load_document_record()` 在做什么

`choose_loader_name()` 只是最小路由器。

它按后缀返回：

- `.md -> markdown_loader`
- `.txt -> text_loader`
- `.pdf -> pypdf.PdfReader`

`load_document_record()` 才是真正把文件读进来的统一入口。

它输出的是 `LoadedDocument`，也就是：

- `path`
- `content`
- `metadata`

你可以把它理解成：

```text
文件系统世界 -> 文本世界
```

### 3.5 为什么 PDF 可以进入第二章，但 OCR 不应该一起拉进来

真实 PDF 解析进入第二章是合理的，因为它仍然属于：

- 文档发现
- 文本提取
- metadata 注入

但扫描件 OCR 会额外引入：

- 图像处理
- OCR 质量问题
- 版面重建
- 表格/图片理解

这会让第二章的重点从“稳定输入层”滑到“复杂解析工程”。

所以当前边界是：

- 可提取文本的 PDF：进第二章
- 扫描件/OCR：明确留给后面

### 3.6 `normalize_text()` 为什么也属于输入层核心动作

如果你忽略文本规范化，后面很多现象会莫名其妙：

- 同一份文件在不同平台换行符不一致
- chunk 字符范围不稳定
- 行数、字符数、切分边界会漂移

`normalize_text()` 虽然看起来只是小动作，但它在做的是：

- 去掉 BOM
- 统一换行符
- 去掉每行尾部多余空格
- 保持后续切分更稳定

这也是为什么第二章不能把 loader 简化成“读完就完了”。

### 3.7 Loader 不负责什么

Loader 负责的是：

- 发现哪些文件应该进入系统
- 判断格式是否支持
- 把文件读取成统一文本
- 提供与文档类型相关的基础元信息

Loader 不负责：

- chunk 怎么切
- metadata 怎么设计完整 schema
- stable id 怎么生成
- 向量化和检索

它的职责是“让文件可读”，不是“决定知识如何回答”。

---

## 4. Splitter、Metadata、ID、Pipeline 各自负责什么 📌

### 4.1 第二章最值得先看的运行时对象

在 [document_processing.py](../../source/04_rag/02_document_processing/document_processing.py) 里，最值得先建立手感的不是“函数很多”，而是对象已经很清楚。

你可以先把这些对象看成第二章输入层的运行时骨架：

| 对象 | 作用 |
|------|------|
| `TextChunk` | 最基础的文本切片，带字符范围 |
| `SourceChunk` | 后续系统真正消费的标准 chunk |
| `DocumentCandidate` | 文件发现阶段的判断结果 |
| `LoadedDocument` | loader 已经成功读取后的统一文档对象 |
| `MarkdownSection` | Markdown 按标题切分后的中间对象 |
| `ChunkDraft` | 从文档切分走向标准 chunk 之前的临时对象 |
| `SplitterConfig` | 控制 `chunk_size / chunk_overlap` 的最小配置 |
| `DocumentPipelineResult` | 整条输入层流水线的汇总结果 |

这和第一章先看 `RouteDecision / RetrievalResult / AnswerResult` 是同一类学习方式：

> 先看清运行时对象，再看函数如何把它们串起来。

### 4.2 Splitter 负责什么

Splitter 负责的是：

- 把长文本切成更小段
- 保留字符范围
- 控制 `chunk_size / chunk_overlap`
- 尽量避免在很差的位置生硬截断

它更像是在做：

> 从文本到“可索引片段”的第一次结构化。

### 4.3 `split_text()` 到底做了什么

很多人第一次看 splitter 时，只会注意 `chunk_size`。

但第二章真正想让你看见的是：

1. 它不是一刀切定长截断
2. 它会尽量找相对更自然的断点
3. 它会保留 `start_index / end_index`
4. 它会通过 overlap 保留跨 chunk 的最小上下文连续性

也就是说，这一步不只是“切短”，而是在做：

```text
长文本 -> 更适合后续索引和引用的片段
```

### 4.4 为什么 `SplitterConfig` 要显式校验

`chunk_overlap >= chunk_size` 这种配置看起来只是参数问题，但本质上会让切分行为变得不稳定甚至无意义。

所以 `SplitterConfig` 一开始就显式校验：

- `chunk_size > 0`
- `chunk_overlap >= 0`
- `chunk_overlap < chunk_size`

这一点的教学意义是：

> 输入层配置错误，应该尽早失败，而不是把坏状态悄悄带到后面。

### 4.5 为什么 Markdown 值得按标题切分

Markdown 文档天然带有结构信号：

- `#` 标题
- `##` 小节
- `###` 更细分层

如果忽略这些结构，只做纯定长切分，会出现两个问题：

- 不同主题内容更容易被混在一个 chunk 里
- 后续很难把 chunk 和“原来属于哪个小节”重新对应上

所以第二章现在会对 Markdown 先做标题感知切分，再继续做字符级切分。

这一步要建立的直觉是：

> 结构化切分不是“更复杂的版本”，而是“更符合原文组织方式的版本”。

### 4.6 `split_markdown_by_headers()` 在补什么能力

`split_markdown_by_headers()` 返回的不是最终 `SourceChunk`，而是 `MarkdownSection`。

它补的是两个非常关键的结构信息：

- `section_title`
- `header_path`

例如：

```text
Product Overview > Ingestion Policy
```

这类信息非常重要，因为后面即使 chunk 被进一步切小，你仍然知道它原来属于哪一段结构路径。

### 4.7 Metadata 负责什么

Metadata 负责的是：

- 说明 chunk 从哪里来
- 说明 chunk 在文档什么位置
- 给后面的过滤、引用、删除和调试留锚点

第二章现在至少要保留这些字段：

- `source`
- `filename`
- `suffix`
- `loader`
- `chunk_index`
- `char_start`
- `char_end`
- `chunk_chars`

某些文档类型还会再带：

- `page_count`
- `section_title`
- `header_path`
- `header_level`

### 4.8 为什么要区分 `base metadata` 和 `chunk metadata`

这一点非常重要。

并不是所有 metadata 都属于同一层。

更合理的划分是：

`base metadata`：

- `source`
- `filename`
- `suffix`
- `char_count`
- `line_count`
- `loader`
- `page_count`

`chunk metadata`：

- `chunk_index`
- `char_start`
- `char_end`
- `chunk_chars`
- `section_title`
- `header_path`
- `header_level`

这样做的好处是：

- 文档级信息只算一次
- chunk 级信息只在片段层补充
- 字段来源更清楚
- 更新和调试更容易定位

### 4.9 `build_base_metadata()` 和 `build_chunk_metadata()` 的意义

这两个函数看起来很朴素，但它们其实在做 schema 收束。

也就是说，第二章不是让 metadata 到处临时拼出来，而是要通过统一函数把字段规范下来。

这会直接影响后面：

- 向量库存什么
- 引用时展示什么
- 删除和过滤按什么字段做
- golden set 在回归什么

### 4.10 Stable ID 负责什么

稳定 ID 解决的是：

- 重复处理时能不能认出是同一份文档
- 更新时该替换哪些 chunk
- 删除时该清掉哪些索引和缓存

第二章里你至少要把两个层次区分清楚：

- `document_id`
  对应文件级身份
- `chunk_id`
  对应切分后片段级身份

### 4.11 `stable_document_id()` 和 `stable_chunk_id()` 到底在保什么稳定

当前实现里：

- `stable_document_id()` 以文档路径为基础生成稳定身份
- `stable_chunk_id()` 结合 `document_id + chunk_index + content digest` 生成 chunk 身份

这一步不是为了“哈希更酷”，而是为了让下面这些动作有锚点：

- 同一路径文档重复处理时，文档身份不漂移
- 相同 chunk 再次生成时，ID 尽量保持一致
- 更新或 upsert 时，系统知道自己在替换什么

### 4.12 `prepare_chunks()` 才是第二章真正的核心收束点

如果只看 loader、splitter、metadata 各自都很碎。

`prepare_chunks()` 的价值就在于，它把这些动作串成了一个最小闭环：

```text
path + text
-> document_id
-> base metadata
-> split_document()
-> chunk metadata
-> chunk_id
-> SourceChunk[]
```

你可以把它理解成：

```text
文档输入层的最小编排器
```

### 4.13 Pipeline 负责什么

`DocumentPipeline` 负责的是把前面的分散动作收束成一个顺序闭环：

```text
discover -> load -> split -> enrich metadata -> assign ids -> output SourceChunk[]
```

这里最重要的不是“抽象名字变高级了”，而是：

- 你能一次看到 candidates / accepted / ignored
- 你能一次看到每份文档的 chunk 统计
- 你能把“治理入口”落到 `document_id / chunk_id`

### 4.14 `run_document_pipeline()` 为什么是第二章的总入口

`run_document_pipeline()` 会把：

- 候选文件
- 已接受文档
- 全部标准 chunks
- splitter 配置

收束成 `DocumentPipelineResult`。

这一步的意义是：

- 让输入层行为能被整体观察
- 让回归测试可以直接锁定总结果
- 让后面章节不必重新拼一遍“文档如何进入系统”

---

## 5. 数据生命周期与知识库治理的最小落点 📌

### 5.1 为什么第二章就要开始有治理视角

很多人会把治理理解成“后面做平台时再说”。

但如果第二章连下面这些最小锚点都没有：

- `document_id`
- `chunk_id`
- `source`
- `loader`
- `page_count / header_path`

那你后面其实没有东西可以治理。

所以第二章现在不做后台平台，但必须建立最小治理落点。

### 5.2 第二章里最重要的治理锚点是什么

当前这一章最重要的三个锚点是：

1. 删除和更新要先锚定 `document_id`
2. upsert 要锚定 `chunk_id`
3. 来源追溯要锚定 `source + metadata`

换句话说：

- 文档级动作看 `document_id`
- 片段级动作看 `chunk_id`
- 调试和引用看 metadata

### 5.3 如果第二章不把这些锚点立住，后面会发生什么

问题不会马上爆炸，但会在后面章节逐步显现：

- 第三章做 embedding 时，不知道哪些向量属于同一文档
- 第四章进向量库时，不知道 upsert 和 delete 该按什么键执行
- 第五章做检索时，拿到结果却无法稳定显示来源
- 做回归时，很难判断是文本变了还是 ID / metadata 漂了

所以第二章最重要的治理价值不是“平台化”，而是：

> 给后续工程留下足够稳定的锚点。

### 5.4 第二章里最小治理并不等于企业级治理

这里要区分两层：

第二章现在真的在做的：

- 稳定身份
- 基础来源字段
- 基础结构字段
- 最小 pipeline 汇总

第二章现在只建立意识、不展开实现的：

- 增量更新
- 文档版本号
- ACL 和多租户
- OCR 解析链路
- 向量索引和缓存同步删除

原因不是这些不重要，而是：

> 第二章的任务是把治理的锚点立住，而不是把治理平台一次性做完。

### 5.5 第二章为什么要有 golden set

第一章的 golden set 主要是系统行为边界。

第二章的 golden set 更偏向输入层稳定性。

它要锁定的不是“回答得好不好”，而是：

- 发现逻辑有没有变
- loader 选择有没有漂
- chunk 数量有没有大幅变化
- 关键 metadata 有没有丢

也就是说，这一章的回归重点是：

> 输入层行为是否仍然稳定。

---

## 6. 第二章实践：独立文档处理闭环

### 6.1 目录结构

本章代码目录是：

```text
source/04_rag/02_document_processing/
├── README.md
├── requirements.txt
├── document_processing.py
├── document_processing_golden_set.json
├── 01_discover_and_load.py
├── 02_split_and_inspect.py
├── 03_build_chunks.py
├── 04_loader_extensions.py
├── 05_document_pipeline.py
├── data/
│   ├── product_overview.md
│   ├── faq.txt
│   ├── course_policy.pdf
│   ├── README.md
│   └── ignore.csv
└── tests/
    └── test_document_processing.py
```

第二章和第一章一样，保持平铺目录。

### 6.2 第二章的输入和输出

本章代码的输入是：

- 本地 `.md / .txt / .pdf` 文件
- `chunk_size / chunk_overlap`

本章代码的输出是：

- `TextChunk[]`
- `SourceChunk[]`
- `document_id`
- `chunk_id`
- `base metadata + chunk metadata`
- `DocumentPipeline` 统计信息

这一步最重要的感觉是：

> 第二章不是在做“能读几种文件”的演示，而是在做“后续章节的稳定输入接口”。

### 6.3 本章最值得先看的对象和函数

在 [document_processing.py](../../source/04_rag/02_document_processing/document_processing.py) 里，你最值得先看的是：

- `DocumentCandidate`
- `LoadedDocument`
- `TextChunk`
- `MarkdownSection`
- `ChunkDraft`
- `SourceChunk`
- `SplitterConfig`
- `DocumentPipelineResult`
- `inspect_document_candidate()`
- `inspect_document_candidates()`
- `discover_documents()`
- `load_document_record()`
- `split_text()`
- `split_markdown_by_headers()`
- `split_document()`
- `build_base_metadata()`
- `build_chunk_metadata()`
- `stable_document_id()`
- `stable_chunk_id()`
- `prepare_chunks()`
- `run_document_pipeline()`

推荐阅读顺序不是从上到下死读，而是：

1. 先看对象
2. 再看 discover / load
3. 再看 split
4. 再看 metadata / ID
5. 最后看 pipeline

### 6.4 运行方式

```bash
cd source/04_rag/02_document_processing

python -m pip install -r requirements.txt
python 01_discover_and_load.py
python 02_split_and_inspect.py
python 02_split_and_inspect.py data/faq.txt --chunk-size 140 --chunk-overlap 20
python 03_build_chunks.py
python 04_loader_extensions.py
python 05_document_pipeline.py
python -m unittest discover -s tests
```

### 6.5 先跑哪个

建议先跑：

```bash
python 01_discover_and_load.py
```

你最先要建立的直觉是：

- 不是所有文件都应该进入系统
- 即使都是“文件”，也应该按格式选不同 loader
- 第二章真正交付的不是“能读文件”，而是“稳定输入层”

### 6.6 `01_discover_and_load.py` 在看什么

对应文件：

- [01_discover_and_load.py](../../source/04_rag/02_document_processing/01_discover_and_load.py)

这个脚本会把文件发现和 loader 结果直接打印出来。

重点观察：

- `faq.txt`、`product_overview.md` 和 `course_policy.pdf` 为什么会被接受
- `README.md` 为什么会被忽略
- `ignore.csv` 为什么不会进入系统
- `course_policy.pdf` 为什么会显示 `loader=pypdf.PdfReader` 和 `pages=2`

这里最重要的不是接受了多少文件，而是：

> 输入层一开始就应该告诉你自己为什么接受、为什么忽略。

### 6.7 `02_split_and_inspect.py` 在看什么

对应文件：

- [02_split_and_inspect.py](../../source/04_rag/02_document_processing/02_split_and_inspect.py)

这一节是在看：

```text
统一文本 -> TextChunk[]
```

重点观察：

- `chunk_size` 和 `chunk_overlap` 会怎样影响结果
- 为什么 chunk 最好保留字符范围
- 为什么切分不应该只是机械定长截断
- 为什么非法参数应该尽早失败

你还可以故意跑一个非法配置：

```bash
python 02_split_and_inspect.py data/faq.txt --chunk-size 120 --chunk-overlap 120
```

你会看到脚本直接拒绝这组参数，因为 `chunk_overlap` 不能大于等于 `chunk_size`。

### 6.8 `03_build_chunks.py` 在看什么

对应文件：

- [03_build_chunks.py](../../source/04_rag/02_document_processing/03_build_chunks.py)

第二章真正的闭环是：

```text
path -> text -> TextChunk[] -> metadata -> stable ids -> SourceChunk[]
```

重点观察：

- `document_id`
- `chunk_id`
- `source / filename / suffix / loader`
- `chunk_index`
- `char_start / char_end / chunk_chars`
- Markdown chunk 的 `header_path`
- PDF chunk 的 `page_count`

这一步最重要的是把“能切 chunk”升级成“能稳定地产出标准 chunk”。

### 6.9 `04_loader_extensions.py` 在看什么

对应文件：

- [04_loader_extensions.py](../../source/04_rag/02_document_processing/04_loader_extensions.py)

这一节不是要把第二章做成企业级 ingestion 平台，而是要把扩展方向讲清楚。

重点观察：

- 为什么 `.md / .txt / .pdf` 需要不同 loader
- 为什么 PDF 现在可以进入系统，但扫描件/OCR 还要延后
- 为什么 Markdown 可以先按标题切分，再继续做 chunk 切分
- 为什么目录批量扫描和 loader 选择本身就是输入层的一部分

### 6.10 `05_document_pipeline.py` 在看什么

对应文件：

- [05_document_pipeline.py](../../source/04_rag/02_document_processing/05_document_pipeline.py)

这一节是把整个第二章从分散步骤收束成一个可观察结果。

重点观察：

- `candidates / accepted / ignored / total_chunks`
- 每份文档的 `document_id`
- 每份文档的 chunk 数
- sample `chunk_id`
- 为什么更新/删除应该锚定 `document_id`
- 为什么 upsert 应该锚定 `chunk_id`

这一步不是在做后台平台，而是在把治理意识落到可运行对象上。

### 6.11 `tests/test_document_processing.py` 在锁定什么

对应文件：

- [tests/test_document_processing.py](../../source/04_rag/02_document_processing/tests/test_document_processing.py)

测试会锁定第二章最重要的几件事：

1. 文档发现逻辑正确
2. PDF 真的能被解析，并记录页数
3. Markdown 标题切分能保留 `header_path`
4. chunk 会带字符范围
5. `base metadata / chunk metadata` 字段完整
6. 重复处理时 ID 保持稳定
7. 默认参数下的 golden set 仍然成立

这一章看测试，重点不是学 `unittest`，而是理解：

- 输入层行为也需要被正式回归
- metadata 丢失也是回归问题
- “稳定 ID” 应该通过测试体现，而不是只写在文档里

### 6.12 第二章最小回归集

第二章除了继续服务课程主线，还要单独锁定自己的输入层行为。

本章回归文件是：

- [document_processing_golden_set.json](../../source/04_rag/02_document_processing/document_processing_golden_set.json)

它至少锁定三类样本：

```json
[
  {
    "filename": "faq.txt",
    "expected_loader": "text_loader"
  },
  {
    "filename": "product_overview.md",
    "expected_loader": "markdown_loader"
  },
  {
    "filename": "course_policy.pdf",
    "expected_loader": "pypdf.PdfReader"
  }
]
```

这不是完整评估体系，但已经足够回答：

1. 发现逻辑有没有跑偏
2. 默认参数下的 chunk 结果有没有大幅漂移
3. `source / loader / page_count / header_path` 是否还稳定
4. 默认 pipeline 演示是否仍然成立

### 6.13 本章代码刻意简化了什么

这一章的实现刻意简化了五件事：

1. 只支持本地 `.md / .txt / .pdf`
2. PDF 只处理可直接提取文本的情况，不做 OCR
3. 不做复杂版式、表格和网页解析
4. 不接 embedding 和向量库
5. 不做真实生产环境的同步、权限、版本平台

这是故意的。

因为本章要先把下面这件事学会：

> 文档处理的目标不是“支持最多格式”，而是“先稳定地产出可用 chunk，并把治理锚点立住”。

### 6.14 第二章最值得刻意观察的失败案例

第二章至少要刻意看四类失败：

1. 文件发现失败
   - `README.md` 会被忽略
   - `ignore.csv` 会被忽略

2. splitter 参数失败

```bash
python 02_split_and_inspect.py data/faq.txt --chunk-size 120 --chunk-overlap 120
```

3. PDF 边界失败
   - 如果 PDF 没有可提取文本，当前 loader 会直接报错
   - 这代表“扫描件/OCR 仍然超出第二章边界”

4. 输入层回归失败
   - 如果你改了 chunk 参数、loader 逻辑或 metadata 字段
   - golden set 和测试结果就可能变化

这些失败案例很重要，因为它们会帮你分清：

- 哪些是章节边界
- 哪些是输入层不变量
- 哪些变化会影响后续章节

### 6.15 建议你主动改的地方

如果你想把第二章真正学扎实，建议主动改三类地方再跑一遍：

1. 修改 `chunk_size / chunk_overlap`，观察 chunk 边界和 chunk 数如何变化
2. 在 Markdown 样例里改一个标题，观察 `header_path` 如何变化
3. 新增一个不支持的文件类型，观察 candidate 判断和 pipeline 汇总如何变化

这样你会真正把“文件类型、切分策略、metadata、ID、回归行为”连在一起。

---

## 7. 本章学完后你应该能回答

- 为什么文档处理是知识输入层，而不是附属功能
- `loader / splitter / metadata / stable id / pipeline` 各自负责什么
- 为什么第二章真正交付的是稳定 `SourceChunk[]`
- 为什么字符范围和稳定 ID 从第二章就应该存在
- 为什么 Markdown 值得做标题感知切分
- 为什么真实 PDF 解析可以进第二章，但 OCR 还不该一起拉进来
- 为什么 `document_id / chunk_id` 会直接影响后面的更新、删除和治理
- 为什么第二章的 golden set 锁定的是输入层稳定性，而不是回答质量

---

## 8. 下一章

第三章开始，你才会进入向量化问题：

- chunk 怎么变成向量
- 向量相似度在做什么
- 为什么向量化只是给 chunk 再包一层表示

也就是说，第三章处理的是“这些稳定 chunk 如何变成可检索向量”。

所以第二章和第三章之间最重要的接口关系是：

> 第二章负责稳定地产出 `SourceChunk[]`，第三章负责把这些稳定 chunk 变成向量表示。
