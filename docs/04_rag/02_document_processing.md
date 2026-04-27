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

### 本章学习地图

建议按下面这条主线阅读本章，而不是一开始就陷入某个函数或参数：

```text
先看完整流程
-> 再看 Loader 如何把不同文件变成统一文本
-> 再看 Splitter 如何把统一文本切成可检索片段
-> 再看 ChunkDraft 如何被补齐成 SourceChunk
-> 最后看 Pipeline 如何把单文档逻辑扩展到目录级处理
```

本章后面的设问和排错内容，主要用于复习和查漏补缺。初学时更推荐先顺着流程读一遍，再回头看“为什么”类问题。

---

## 2. 文档处理的完整流程 📌

这一章可以先不要从“某个类是什么意思”开始，而是先建立一条完整主线。

文档处理做的是把本地原始文件加工成后续 RAG 系统可以稳定消费的标准输入：

```text
原始文件
-> 发现文件，判断是否应该进入系统
-> 根据文件类型选择 Loader
-> Loader 把文件读取成统一文本
-> 对文本做最小规范化
-> 根据文档类型选择切分策略
-> 得到切分阶段的中间结果
-> 补齐 metadata
-> 生成稳定 document_id / chunk_id
-> 输出 SourceChunk[]
```

这条链路里每一步都有明确输入和输出：

| 阶段 | 输入 | 输出 | 对应代码 |
|------|------|------|----------|
| 文件发现 | 目录或文件路径 | `DocumentCandidate` | `inspect_document_candidate()` / `discover_documents()` |
| 文件加载 | 已接受的路径 | `LoadedDocument` | `load_document_record()` |
| 文本规范化 | loader 读出的文本 | 统一换行和空白后的文本 | `normalize_text()` |
| 文本切分 | 统一文本 | `TextChunk` / `MarkdownSection` / `ChunkDraft` | `split_text()` / `split_markdown_by_headers()` / `split_document()` |
| 字段补齐 | `ChunkDraft[]` | `SourceChunk[]` | `prepare_chunks()` |
| 目录汇总 | 文档目录 | `DocumentPipelineResult` | `run_document_pipeline()` |

初学时可以先记住一个判断标准：

> Loader 解决“文件怎么读”，Splitter 解决“文本怎么切”，Metadata 和 Stable ID 解决“切完以后怎么追踪”，Pipeline 解决“如何把整条链路稳定跑完”。

后面的章节会按这条主线展开：先讲 Loader，再讲 Splitter，再讲 `SourceChunk`，最后讲 Pipeline 和治理。

---

## 3. 主流程拆解：从文件到 SourceChunk[] 📌

### 3.1 文档进入系统的含义

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

### 3.2 第二章交付的标准接口

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

### 3.3 文档处理是 RAG 的知识输入层

如果第二章没有先把文档输入层做稳，后面很快就会出现问题：

- 相同文档每次生成的 chunk 不一致
- embedding 阶段无法判断“这是谁的向量”
- 删除和增量更新没有稳定身份
- 调试时无法确认是内容变了还是 ID 漂了

所以第二章并不是“还没到检索前的准备工作”，而是：

> 在给后面的向量化、向量存储、检索和评估打地基。

### 3.4 先稳定输入层，再进入 Embedding

如果这一步还没把 `SourceChunk[]` 做稳，就急着进第三章，问题只会被推迟，不会消失。

比如：

- 你会在第三章才发现 chunk 边界根本不合理
- 你会在第四章才发现不知道该删哪个向量
- 你会在第五章才发现 metadata 根本不够做过滤和引用

所以第二章最重要的价值不是“离 embedding 更近了一步”，而是：

> 先把知识输入层做成一个稳定的、可重复的标准接口。

### 3.5 第二章的运行时主链路

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

### 3.6 稳定输入层的工程价值

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

## 4. Loader：不同文件如何变成统一文本 📌

### 4.1 真实 Loader 进入第二章的原因

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

### 4.2 三种输入的职责分工

| 输入 | 当前做法 | 第二章想让你看到什么 |
|------|----------|----------------------|
| `.txt` | 直接读取后规范化 | 最简单的基线输入 |
| `.md` | 读取后按标题感知切分 | 文档结构本身可以指导 chunk 设计 |
| `.pdf` | 用 `pypdf.PdfReader` 抽取文本 | 同样是“文件”，loader 复杂度也不一样 |

第二章不是要把所有格式都一次性讲完，而是要让你看到：

> loader 选择本身就是输入层设计的一部分。

### 4.3 文件发现阶段：`inspect_document_candidate()`

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

### 4.4 文件加载阶段：`choose_loader_name()` 和 `load_document_record()`

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

### 4.5 PDF 文本提取与 OCR 边界

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

### 4.6 文本规范化：`normalize_text()`

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

### 4.7 Loader 的职责边界

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

## 5. Splitter：统一文本如何变成可检索片段 📌

Loader 结束后，系统已经拿到统一文本。接下来要解决的是：这段文本怎样变成后续检索更容易命中的片段。

这一节先讲切片逻辑，再讲不同文档类型的切分策略，最后再进入标准 chunk 的封装。

### 5.1 切片的目标：短、集中、不断裂、可追溯

切片不是为了把文本变短这么简单，而是为了同时满足后续 RAG 的几个约束。

第一，embedding 模型和检索系统更适合处理较短、主题相对集中的文本片段。如果一整篇文档直接向量化，用户问一个很细的问题时，相关信息会被大量无关内容稀释。

第二，chunk 不能太短。太短会丢上下文，比如只剩一句“可以退款”，但不知道是在说课程、订单还是会员权益。

第三，chunk 也不能太长。太长会混入多个主题，检索命中后交给 LLM 的上下文噪声会变多。

第四，相邻 chunk 之间需要少量 `overlap`。这是因为有些语义会跨越切分边界，例如上一段提出概念，下一段才解释细节。如果完全无重叠，检索时可能只命中半段信息。

第五，切分边界要尽量自然。代码里的 `_choose_breakpoint()` 会优先找段落、换行、句号、空格等位置，而不是永远按固定字符数硬切。这样得到的 chunk 更像“可阅读片段”，而不是“被截断的字符串”。

所以可以把切片目标总结成一句话：

> 尽量让每个 chunk 足够小、主题集中、上下文不断裂，并且还能追溯回原文位置。

这也是为什么 `TextChunk / ChunkDraft` 都要保留 `start_index / end_index`。这些字符范围不是为了切分本身好看，而是为了后面能回答：

- 这个 chunk 来自原文哪里
- 引用时应该指向哪个位置
- chunk 边界变化时如何调试
- metadata 里的 `char_start / char_end` 应该怎么生成


### 5.2 Splitter 的职责

Splitter 负责的是：

- 把长文本切成更小段
- 保留字符范围
- 控制 `chunk_size / chunk_overlap`
- 尽量避免在很差的位置生硬截断

它更像是在做：

> 从文本到“可索引片段”的第一次结构化。


### 5.3 通用文本切分：`split_text()`

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


### 5.4 切分配置：`SplitterConfig`

`chunk_overlap >= chunk_size` 这种配置看起来只是参数问题，但本质上会让切分行为变得不稳定甚至无意义。

所以 `SplitterConfig` 一开始就显式校验：

- `chunk_size > 0`
- `chunk_overlap >= 0`
- `chunk_overlap < chunk_size`

这一点的教学意义是：

> 输入层配置错误，应该尽早失败，而不是把坏状态悄悄带到后面。


### 5.5 Markdown 标题感知切分

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


### 5.6 Markdown 结构信息：`split_markdown_by_headers()`

`split_markdown_by_headers()` 返回的不是最终 `SourceChunk`，而是 `MarkdownSection`。

它补的是两个非常关键的结构信息：

- `section_title`
- `header_path`

例如：

```text
Product Overview > Ingestion Policy
```

这类信息非常重要，因为后面即使 chunk 被进一步切小，你仍然知道它原来属于哪一段结构路径。


### 5.7 不同文档类型的切分差异

不同文档不会完全按照同一个逻辑切片。

更准确地说，第二章采用的是：

```text
不同文档类型先走各自更合适的切分策略
最后统一收束成同一种 SourceChunk
```

例如：

| 文档类型 | 切分策略 | 原因 |
|----------|----------|------|
| `.txt` | 直接走 `split_text()` | 纯文本没有明显结构，只能按自然断点和窗口大小切 |
| `.pdf` | 先由 loader 提取文本，再走 `split_text()` | 当前章节只处理 PDF 文本抽取，不处理复杂版面结构 |
| `.md` | 先按标题切成 `MarkdownSection`，再对每个 section 走 `split_text()` | Markdown 标题本身就是强结构信号，应该尽量保留 |

也就是说，差异发生在 `split_document()` 这一层；统一发生在 `prepare_chunks()` 这一层。

这是一种很常见的工程模式：

```text
输入格式可以不同
解析和切分策略可以不同
但输出契约必须相同
```

后面的 embedding 和向量库不应该关心“这个 chunk 原来是 Markdown、TXT 还是 PDF”。它们只需要看到稳定的：

```text
SourceChunk(
  chunk_id=...,     # 片段身份
  document_id=...,  # 文档身份
  content=...,      # 要向量化的文本
  metadata=...,     # 来源、位置、结构信息
)
```

所以第二章的设计不是“所有文档用同一把刀切”，而是：

> 前面尊重不同文档的结构，后面统一成同一种标准 chunk。


## 6. 从切分结果到标准 SourceChunk 📌

切分完成后，系统还不能直接进入 embedding。因为切出来的文本片段还缺少身份、来源、位置和结构字段。

这一节讲的就是：怎样把切分阶段的中间结果收束成后续章节统一消费的 `SourceChunk[]`。

### 6.1 第二章的运行时对象

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


### 6.2 `TextChunk / MarkdownSection / ChunkDraft / SourceChunk` 的区别

如果你在 [03_build_chunks.py](../../source/04_rag/02_document_processing/03_build_chunks.py) 里看到 `ChunkDraft` 和 `SourceChunk` 有点混乱，可以先把它们理解成同一条加工流水线里的不同阶段。

它们不是在表达“不同种类的 chunk”，而是在表达：

> 一段文本从“刚被切出来”到“可以交给后续 RAG 系统消费”之间，信息逐步补齐的过程。

可以用下面这张表来区分：

| 类型 | 出现阶段 | 解决的问题 | 是否最终产物 |
|------|----------|------------|--------------|
| `TextChunk` | 通用纯文本切分之后 | 只有内容和字符范围，回答“这段文本从哪里切出来” | 否 |
| `MarkdownSection` | Markdown 标题感知切分之后 | 保留标题层级，回答“这段内容属于哪个标题路径” | 否 |
| `ChunkDraft` | 文档类型切分策略统一之后 | 把不同文档切分结果统一成“待加工 chunk” | 否 |
| `SourceChunk` | metadata 和 stable id 补齐之后 | 后续 embedding、向量库、检索统一消费的标准对象 | 是 |

所以 `ChunkDraft` 和 `SourceChunk` 的核心区别是：

- `ChunkDraft` 是“切分阶段的草稿”，只关心内容、字符范围，以及切分时顺手得到的结构信息
- `SourceChunk` 是“系统标准输入”，必须带上 `document_id / chunk_id / metadata`

如果直接从 `text -> SourceChunk[]`，短期看代码更少，但会把两件事混在一起：

1. 这份文档应该怎么切
2. 切完以后怎样补齐身份、来源、位置和结构信息

第二章故意拆成 `ChunkDraft -> SourceChunk`，是为了让职责更清楚：

```text
split_document()
只负责：根据文档类型切出 ChunkDraft[]

prepare_chunks()
只负责：把 ChunkDraft[] 补齐成 SourceChunk[]
```

这也是 [03_build_chunks.py](../../source/04_rag/02_document_processing/03_build_chunks.py) 想让你观察的重点：不是“多包了一层类型”，而是把“切分策略”和“标准输出格式”分开。


### 6.3 Metadata 的职责

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


### 6.4 `base metadata` 和 `chunk metadata` 的分层

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


### 6.5 Metadata schema 收束函数

这两个函数看起来很朴素，但它们其实在做 schema 收束。

也就是说，第二章不是让 metadata 到处临时拼出来，而是要通过统一函数把字段规范下来。

这会直接影响后面：

- 向量库存什么
- 引用时展示什么
- 删除和过滤按什么字段做
- golden set 在回归什么


### 6.6 Stable ID 的职责

稳定 ID 解决的是：

- 重复处理时能不能认出是同一份文档
- 更新时该替换哪些 chunk
- 删除时该清掉哪些索引和缓存

第二章里你至少要把两个层次区分清楚：

- `document_id`
  对应文件级身份
- `chunk_id`
  对应切分后片段级身份


### 6.7 `stable_document_id()` 和 `stable_chunk_id()` 的稳定性

当前实现里：

- `stable_document_id()` 以文档路径为基础生成稳定身份
- `stable_chunk_id()` 结合 `document_id + chunk_index + content digest` 生成 chunk 身份

这一步不是为了“哈希更酷”，而是为了让下面这些动作有锚点：

- 同一路径文档重复处理时，文档身份不漂移
- 相同 chunk 再次生成时，ID 尽量保持一致
- 更新或 upsert 时，系统知道自己在替换什么


### 6.8 核心收束点：`prepare_chunks()`

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


## 7. DocumentPipeline：把单文档逻辑扩展到目录级处理 📌

前面几节讲的是单文档如何进入系统。真实知识库通常处理的是目录或文件集合，所以还需要一个总入口把发现、加载、切分、补字段和汇总结果串起来。

### 7.1 Pipeline 的职责

`DocumentPipeline` 负责的是把前面的分散动作收束成一个顺序闭环：

```text
discover -> load -> split -> enrich metadata -> assign ids -> output SourceChunk[]
```

这里最重要的不是“抽象名字变高级了”，而是：

- 你能一次看到 candidates / accepted / ignored
- 你能一次看到每份文档的 chunk 统计
- 你能把“治理入口”落到 `document_id / chunk_id`


### 7.2 总入口：`run_document_pipeline()`

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

如果你想看“单个文件到底按什么顺序变成 `SourceChunk[]`”，直接看 `document_processing.py` 里这条函数链路即可：

```text
inspect_document_candidate()
-> discover_documents()
-> load_document_record()
-> split_document()
-> prepare_chunks()
-> SourceChunk[]
-> run_document_pipeline()
```

也就是说：

- 前半段更适合理解单文档的流转过程
- `run_document_pipeline()` 更适合理解目录级批处理和总结果收束

---


## 8. 数据生命周期与知识库治理的最小落点 📌

### 8.1 第二章建立治理视角的原因

很多人会把治理理解成“后面做平台时再说”。

但如果第二章连下面这些最小锚点都没有：

- `document_id`
- `chunk_id`
- `source`
- `loader`
- `page_count / header_path`

那你后面其实没有东西可以治理。

所以第二章现在不做后台平台，但必须建立最小治理落点。

### 8.2 第二章最重要的治理锚点

当前这一章最重要的三个锚点是：

1. 删除和更新要先锚定 `document_id`
2. upsert 要锚定 `chunk_id`
3. 来源追溯要锚定 `source + metadata`

换句话说：

- 文档级动作看 `document_id`
- 片段级动作看 `chunk_id`
- 调试和引用看 metadata

### 8.3 治理锚点缺失后的连锁问题

问题不会马上爆炸，但会在后面章节逐步显现：

- 第三章做 embedding 时，不知道哪些向量属于同一文档
- 第四章进向量库时，不知道 upsert 和 delete 该按什么键执行
- 第五章做检索时，拿到结果却无法稳定显示来源
- 做回归时，很难判断是文本变了还是 ID / metadata 漂了

所以第二章最重要的治理价值不是“平台化”，而是：

> 给后续工程留下足够稳定的锚点。

### 8.4 最小治理与企业级治理的边界

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

### 8.5 输入层 golden set 的价值

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

## 9. 代码实践：按流程阅读第二章
这一节建议当作复习路径使用。前面已经按概念讲完了完整流程，这里再回到代码目录，把每个脚本对应到流程中的一个阶段。

推荐阅读顺序是：

```text
01_discover_and_load.py
-> 02_split_and_inspect.py
-> 03_build_chunks.py
-> 04_loader_extensions.py
-> 05_document_pipeline.py
-> tests/test_document_processing.py
```

这样读的好处是：你不是在记脚本编号，而是在复盘“文件如何一步步变成 SourceChunk[]”。

### 9.1 目录结构

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

### 9.2 第二章的输入和输出

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

### 9.3 本章最值得先看的对象和函数

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

### 9.4 运行方式

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

这里的 `python -m pip install -r requirements.txt` 安装的是本章运行依赖；当前 `requirements.txt` 里声明的就是 `pypdf>=6,<7`。

也就是说：

- 文档里反复写 `python -m pip install -r requirements.txt`，本质上就是在安装 `pypdf`
- 不需要再额外执行一遍 `python -m pip install pypdf`
- 如果 `from pypdf import PdfReader` 仍然报“无法解析导入”，通常不是文档没写清楚，而是编辑器没切到安装依赖的 Python 解释器

### 9.5 推荐运行顺序

建议先跑：

```bash
python 01_discover_and_load.py
```

你最先要建立的直觉是：

- 不是所有文件都应该进入系统
- 即使都是“文件”，也应该按格式选不同 loader
- 第二章真正交付的不是“能读文件”，而是“稳定输入层”

### 9.6 第一步：`01_discover_and_load.py`

对应文件：

- [01_discover_and_load.py](../../source/04_rag/02_document_processing/01_discover_and_load.py)

这个脚本会把文件发现和 loader 结果直接打印出来。

它对应的主链路前半段是：

```text
inspect_document_candidate()
-> discover_documents()
-> load_document_record()
```

重点观察：

- `faq.txt`、`product_overview.md` 和 `course_policy.pdf` 为什么会被接受
- `README.md` 为什么会被忽略
- `ignore.csv` 为什么不会进入系统
- `course_policy.pdf` 为什么会显示 `loader=pypdf.PdfReader` 和 `pages=2`

这里最重要的不是接受了多少文件，而是：

> 输入层一开始就应该告诉你自己为什么接受、为什么忽略。

### 9.7 第二步：`02_split_and_inspect.py`

对应文件：

- [02_split_and_inspect.py](../../source/04_rag/02_document_processing/02_split_and_inspect.py)

这一节是在看：

```text
统一文本 -> TextChunk[]
```

对应到代码里，就是：

```text
load_document()
-> split_text()
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

### 9.8 第三步：`03_build_chunks.py`

对应文件：

- [03_build_chunks.py](../../source/04_rag/02_document_processing/03_build_chunks.py)

第二章真正的闭环是：

```text
path -> text -> TextChunk[] -> metadata -> stable ids -> SourceChunk[]
```

对应到代码里，重点是：

```text
load_and_prepare_chunks()
-> prepare_chunks()
```

如果你现在看这段代码容易晕，先不要直接扎进实现细节。

这里最重要的是先建立一个判断：

> `03_build_chunks.py` 不是在演示“怎么切文本”，而是在演示“怎么把切分结果收束成标准 `SourceChunk[]`”。

### 9.8.1 先记住这 4 个步骤

先把 `prepare_chunks()` 理解成固定 4 步：

```text
1. 先生成 document_id
2. 再生成 base metadata
3. 再执行 split_document() 得到 ChunkDraft[]
4. 最后把每个 ChunkDraft 变成 SourceChunk
```

这 4 步分别解决：

- “这是哪一篇文档”
- “这篇文档有哪些公共字段”
- “这篇文档具体怎么切”
- “后续系统统一消费什么格式”

### 9.8.2 `text -> SourceChunk[]` 中间需要分层

这里故意拆成两层，不是为了把代码写复杂，而是为了把职责拆清楚：

- `split_document()`
  只管“怎么切”
- `prepare_chunks()`
  只管“切完以后怎么补齐标准身份和 metadata”

中间多出的 `ChunkDraft`，就是这两层之间的过渡对象。

这样拆开以后，你调试时会清楚很多：

- 如果 chunk 边界不对，就看 `split_document()`
- 如果 `header_path / page_count / char_start` 不对，就看 metadata
- 如果更新、删除、upsert 对不上，就看 `document_id / chunk_id`

### 9.8.3 推荐阅读顺序

如果你想把这段代码真正看懂，建议按下面顺序看，而不是先看脚本打印：

1. `load_and_prepare_chunks()`
   看单文档入口
2. `prepare_chunks()`
   看主收束函数
3. `split_document()`
   看切分阶段怎样产出 `ChunkDraft[]`
4. `03_build_chunks.py`
   回来看它为什么要打印这些字段

### 9.8.4 阅读时真正要观察的问题

这一节最值得带着 4 个问题去看：

1. 为什么这里要先有 `ChunkDraft`，再有 `SourceChunk`
2. 哪些字段属于整篇文档，哪些字段属于单个 chunk
3. 为什么 `document_id` 和 `chunk_id` 都需要存在
4. 为什么这里打印的不是“回答效果”，而是“输入层结构是否稳定”

重点观察：

- `document_id`
- `chunk_id`
- `source / filename / suffix / loader`
- `chunk_index`
- `char_start / char_end / chunk_chars`
- Markdown chunk 的 `header_path`
- PDF chunk 的 `page_count`

这一步最重要的是把“能切 chunk”升级成“能稳定地产出标准 chunk”。

### 9.9 第四步：`04_loader_extensions.py`

对应文件：

- [04_loader_extensions.py](../../source/04_rag/02_document_processing/04_loader_extensions.py)

这一节不是要把第二章做成企业级 ingestion 平台，而是要把扩展方向讲清楚。

重点观察：

- 为什么 `.md / .txt / .pdf` 需要不同 loader
- 为什么 PDF 现在可以进入系统，但扫描件/OCR 还要延后
- 为什么 Markdown 可以先按标题切分，再继续做 chunk 切分
- 为什么目录批量扫描和 loader 选择本身就是输入层的一部分

### 9.10 第五步：`05_document_pipeline.py`

对应文件：

- [05_document_pipeline.py](../../source/04_rag/02_document_processing/05_document_pipeline.py)

这一节是把整个第二章从分散步骤收束成一个可观察结果。

它直接对应目录级总入口：

```text
run_document_pipeline()
```

重点观察：

- `candidates / accepted / ignored / total_chunks`
- 每份文档的 `document_id`
- 每份文档的 chunk 数
- sample `chunk_id`
- 为什么更新/删除应该锚定 `document_id`
- 为什么 upsert 应该锚定 `chunk_id`

这一步不是在做后台平台，而是在把治理意识落到可运行对象上。

### 9.11 测试：`tests/test_document_processing.py`

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

### 9.12 第二章最小回归集

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

### 9.13 本章代码刻意简化的范围

这一章的实现刻意简化了五件事：

1. 只支持本地 `.md / .txt / .pdf`
2. PDF 只处理可直接提取文本的情况，不做 OCR
3. 不做复杂版式、表格和网页解析
4. 不接 embedding 和向量库
5. 不做真实生产环境的同步、权限、版本平台

这是故意的。

因为本章要先把下面这件事学会：

> 文档处理的目标不是“支持最多格式”，而是“先稳定地产出可用 chunk，并把治理锚点立住”。

### 9.14 第二章最值得刻意观察的失败案例

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

### 9.15 建议你主动改的地方

如果你想把第二章真正学扎实，建议主动改三类地方再跑一遍：

1. 修改 `chunk_size / chunk_overlap`，观察 chunk 边界和 chunk 数如何变化
2. 在 Markdown 样例里改一个标题，观察 `header_path` 如何变化
3. 新增一个不支持的文件类型，观察 candidate 判断和 pipeline 汇总如何变化

这样你会真正把“文件类型、切分策略、metadata、ID、回归行为”连在一起。

---

## 10. 常见疑惑与复盘问题

这一节把前面分散出现的“为什么”集中起来，适合在读完代码以后回头复盘。

### 10.1 文档处理到底是不是文本预处理

不是。文本预处理通常只关心“把文本清洗干净”。本章的文档处理更像 RAG 的知识输入层，它不仅要读取和清洗文本，还要决定哪些文件能进系统、怎样切分、怎样补 metadata、怎样生成稳定 ID，以及怎样把结果收束成后续统一消费的 `SourceChunk[]`。

### 10.2 为什么不直接从 `text` 生成 `SourceChunk[]`

因为“怎么切”和“切完后怎么补齐标准字段”是两件事。

`split_document()` 适合专注处理文档类型差异，例如 Markdown 先按标题切，TXT 和 PDF 走通用文本切分。`prepare_chunks()` 再统一补齐 `document_id / chunk_id / metadata`。

如果直接 `text -> SourceChunk[]`，代码短期看起来更直接，但后面新增 HTML、网页、表格、按页 PDF 或更复杂 Markdown 策略时，很容易把切分策略和标准输出逻辑混在一起。

### 10.3 不同文档都是按照一个逻辑切片吗

不是。更准确地说：

```text
前面按文档类型选择不同切分策略
后面统一输出同一种 SourceChunk
```

`.txt` 和当前的 `.pdf` 主要走通用文本切分；`.md` 会先利用标题结构生成 `MarkdownSection`，再对 section 内文本继续切分。这样既保留不同文档的结构差异，又让后续 embedding、向量库和检索只需要面对统一对象。

### 10.4 `ChunkDraft` 和 `SourceChunk` 最容易混淆在哪里

最容易混淆的是：它们看起来都像 chunk，但职责不同。

`ChunkDraft` 是切分阶段的临时结果，表示“这段内容已经被切出来了，并且知道它在原文中的范围”。`SourceChunk` 是后续系统的标准输入，除了内容和范围，还必须具备稳定身份和完整 metadata。

可以简单记成：

```text
ChunkDraft = 切分草稿
SourceChunk = 可进入后续 RAG 链路的标准 chunk
```

### 10.5 chunk 切得不好会影响哪里

会影响后面的检索、引用和调试。

chunk 太长，容易混入多个主题，检索命中后噪声变多。chunk 太短，容易丢上下文。没有 overlap，跨边界语义可能断开。没有字符范围，后面很难解释 chunk 来自原文哪里。没有稳定 ID，更新、删除和回归测试都会变困难。

### 10.6 第二章为什么暂时不接 Embedding 和向量库

因为在 `SourceChunk[]` 稳定之前，过早接 embedding 只会把输入层问题推迟到后面暴露。

第二章先锁定的是：文件能稳定进入系统，文本能稳定切分，metadata 和 ID 能稳定生成，pipeline 能稳定复跑。第三章再处理“这些 chunk 如何变成向量”。

---

## 11. 本章学完后你应该能回答

- 为什么文档处理是知识输入层，而不是附属功能
- `loader / splitter / metadata / stable id / pipeline` 各自负责什么
- 为什么第二章真正交付的是稳定 `SourceChunk[]`
- 为什么字符范围和稳定 ID 从第二章就应该存在
- 为什么 Markdown 值得做标题感知切分
- 为什么真实 PDF 解析可以进第二章，但 OCR 还不该一起拉进来
- 为什么 `document_id / chunk_id` 会直接影响后面的更新、删除和治理
- 为什么第二章的 golden set 锁定的是输入层稳定性，而不是回答质量

---

## 12. 下一章

第三章开始，你才会进入向量化问题：

- chunk 怎么变成向量
- 向量相似度在做什么
- 为什么向量化只是给 chunk 再包一层表示

也就是说，第三章处理的是“这些稳定 chunk 如何变成可检索向量”。

所以第二章和第三章之间最重要的接口关系是：

> 第二章负责稳定地产出 `SourceChunk[]`，第三章负责把这些稳定 chunk 变成向量表示。
