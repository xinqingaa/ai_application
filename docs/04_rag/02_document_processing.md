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

这里最该先记住的五个概念是：

- `raw text`
  从文件读出来的统一文本
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

### 3.3 为什么 PDF 可以进入第二章，但 OCR 不应该一起拉进来

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

### 3.4 Loader 不负责什么

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

### 4.1 Splitter 负责什么

Splitter 负责的是：

- 把长文本切成更小段
- 保留字符范围
- 控制 `chunk_size / chunk_overlap`
- 尽量避免在很差的位置生硬截断

它更像是在做：

> 从文本到“可索引片段”的第一次结构化。

### 4.2 为什么 Markdown 值得按标题切分

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

### 4.3 Metadata 负责什么

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

### 4.4 Stable ID 负责什么

稳定 ID 解决的是：

- 重复处理时能不能认出是同一份文档
- 更新时该替换哪些 chunk
- 删除时该清掉哪些索引和缓存

第二章里你至少要把两个层次区分清楚：

- `document_id`
  - 对应文件级身份
- `chunk_id`
  - 对应切分后片段级身份

### 4.5 Pipeline 负责什么

`DocumentPipeline` 负责的是把前面的分散动作收束成一个顺序闭环：

```text
discover -> load -> split -> enrich metadata -> assign ids -> output SourceChunk[]
```

这里最重要的不是“抽象名字变高级了”，而是：

- 你能一次看到 candidates / accepted / ignored
- 你能一次看到每份文档的 chunk 统计
- 你能把“治理入口”落到 `document_id / chunk_id`

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

### 5.3 哪些生产问题现在只建立意识，不展开

第二章现在只建立意识，不展开实现的包括：

- 增量更新
- 文档版本号
- ACL 和多租户
- OCR 解析链路
- 向量索引和缓存同步删除

原因不是这些不重要，而是：

> 第二章的任务是把治理的锚点立住，而不是把治理平台一次性做完。

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
└── tests/
```

第二章和第一章一样，保持平铺目录。

### 6.2 输入和输出

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

在 [document_processing.py](../../source/04_rag/02_document_processing/document_processing.py) 里，你最值得先看的是：

- `inspect_document_candidate()`
- `discover_documents()`
- `load_document_record()`
- `split_text()`
- `split_markdown_by_headers()`
- `split_document()`
- `build_base_metadata()`
- `build_chunk_metadata()`
- `stable_document_id()`
- `stable_chunk_id()`
- `run_document_pipeline()`

### 6.3 运行方式

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

### 6.4 你应该观察到什么

跑 [01_discover_and_load.py](../../source/04_rag/02_document_processing/01_discover_and_load.py) 时：

- 你会看到 `faq.txt`、`product_overview.md` 和 `course_policy.pdf` 被接受
- 你会看到 `README.md` 被忽略，因为它只是章节辅助文件
- 你会看到 `ignore.csv` 被忽略，因为当前阶段不支持这个后缀
- 你会看到 `course_policy.pdf` 使用的是 `pypdf.PdfReader`

跑 [02_split_and_inspect.py](../../source/04_rag/02_document_processing/02_split_and_inspect.py) 时：

- 你能看到 chunk 的字符范围
- 你能看到不同参数如何影响切分结果
- 你能看到切分不是单纯按固定长度硬截断
- 你能看到非法参数会被直接拒绝，而不是悄悄产生不稳定结果

跑 [03_build_chunks.py](../../source/04_rag/02_document_processing/03_build_chunks.py) 时：

- 你会看到每份文档产出多少个 chunk
- 你会看到 `document_id / chunk_id`
- 你会看到 `source / filename / suffix / loader`
- 你会看到 Markdown chunk 的 `header_path`
- 你会看到 PDF chunk 的 `page_count`

跑 [04_loader_extensions.py](../../source/04_rag/02_document_processing/04_loader_extensions.py) 时：

- 你会看到第二章的 loader 已经不再只是 `read_text()`
- 你会看到 Markdown 标题切分的 section 数和 header path
- 你会看到 PDF 已经能被真实解析
- 你会看到“扫描件/OCR 仍不在范围内”的明确边界

跑 [05_document_pipeline.py](../../source/04_rag/02_document_processing/05_document_pipeline.py) 时：

- 你会看到 `candidates / accepted / ignored / total_chunks`
- 你会看到每份文档的 `document_id`
- 你会看到为什么更新/删除要锚定 `document_id`
- 你会看到为什么 upsert 要锚定 `chunk_id`

### 6.5 第二章最小回归集

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

### 6.6 本章代码刻意简化了什么

这一章的实现刻意简化了五件事：

1. 只支持本地 `.md / .txt / .pdf`
2. PDF 只处理可直接提取文本的情况，不做 OCR
3. 不做复杂版式、表格和网页解析
4. 不接 embedding 和向量库
5. 不做真实生产环境的同步、权限、版本平台

这是故意的。

因为本章要先把下面这件事学会：

> 文档处理的目标不是“支持最多格式”，而是“先稳定地产出可用 chunk，并把治理锚点立住”。

---

## 7. 本章学完后你应该能回答

- 为什么文档处理是知识输入层，而不是附属功能
- `loader / splitter / metadata / stable id / pipeline` 各自负责什么
- 为什么第二章真正交付的是稳定 `SourceChunk[]`
- 为什么字符范围和稳定 ID 从第二章就应该存在
- 为什么 Markdown 值得做标题感知切分
- 为什么真实 PDF 解析可以进第二章，但 OCR 还不该一起拉进来
- 为什么 `document_id / chunk_id` 会直接影响后面的更新、删除和治理

---

## 8. 下一章

第三章开始，你才会进入向量化问题：

- chunk 怎么变成向量
- 向量相似度在做什么
- 为什么向量化只是给 chunk 再包一层表示

也就是说，第三章处理的是“这些稳定 chunk 如何变成可检索向量”。
