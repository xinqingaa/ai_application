# 02. 文档处理 - 实践指南

> 本文档说明如何跟着 [学习文档](../../../docs/04_rag/02_document_processing.md) 学完第二章，并在不依赖第三章以后的前提下，把本地 `.txt / .md / .pdf` 稳定转换成标准 `SourceChunk[]`。

---

## 核心原则

```text
先判断哪些文件应该进入系统 -> 再选合适 loader -> 再决定怎么切分 -> 最后把 metadata 和 stable id 收束成稳定输入层
```

- 在 `source/04_rag/02_document_processing/` 目录下操作
- 本章只讲知识如何进入系统，不讲 embedding、向量库、检索和生成
- 第二章现在支持真实 PDF 文本提取，但只处理可直接抽取文本的 PDF
- 扫描件、OCR、复杂表格、网页抓取仍然不在本章范围内
- 本章输出只有一个重点：稳定、可重复的 `SourceChunk[]`

---

## 项目结构

```text
02_document_processing/
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

- `document_processing.py`
  放本章对象、文件发现、真实 PDF 读取、Markdown 标题切分、metadata、stable id 和 pipeline 逻辑
- `document_processing_golden_set.json`
  锁定第二章默认输入层行为，避免 loader、splitter 和 metadata 漂移
- `01_discover_and_load.py`
  看哪些文件会被接受、各自使用什么 loader、文本会不会被规范化
- `02_split_and_inspect.py`
  看文本怎么切成 `TextChunk`，以及参数如何影响边界
- `03_build_chunks.py`
  看 `path -> text -> TextChunk[] -> metadata -> stable ids -> SourceChunk[]`
- `04_loader_extensions.py`
  看真实 PDF loader、目录扫描和 Markdown 按标题切分
- `05_document_pipeline.py`
  看通用 `DocumentPipeline` 视角和最小治理落点
- `tests/test_document_processing.py`
  把第二章最重要的输入层行为正式锁进测试

---

## 前置准备

### 1. 运行目录

```bash
cd source/04_rag/02_document_processing
```

### 2. 安装依赖

```bash
python -m pip install -r requirements.txt
```

这里的 `requirements.txt` 就是在安装本章依赖。

当前这个文件里声明的是：

```text
pypdf>=6,<7
```

因此：

- `python -m pip install -r requirements.txt` 会把 `pypdf` 一起安装
- 不需要再单独执行一次 `python -m pip install pypdf`
- 如果编辑器仍然提示 `from pypdf import PdfReader` 无法解析，通常是解释器没有切到你安装依赖的那个 Python 环境

### 3. 当前命令

```bash
python 01_discover_and_load.py
python 02_split_and_inspect.py
python 02_split_and_inspect.py data/faq.txt --chunk-size 140 --chunk-overlap 20
python 03_build_chunks.py
python 04_loader_extensions.py
python 05_document_pipeline.py
python -m unittest discover -s tests
```

### 4. 先跑哪个

建议先跑：

```bash
python 01_discover_and_load.py
```

你最先要建立的直觉是：

- 不是所有文件都应该进入系统
- 即使都是“文件”，也应该按格式选不同 loader
- 第二章真正交付的不是“能读文件”，而是“稳定输入层”

---

## 主链路怎么跑

第二章最核心的代码流转不需要额外脚本，直接看 [document_processing.py](./document_processing.py) 里的函数链路即可：

```text
path
-> inspect_document_candidate()
-> discover_documents()
-> load_document_record()
-> split_document()
-> prepare_chunks()
-> SourceChunk[]
-> run_document_pipeline()
```

你可以配合现有脚本按这个顺序看：

- `01_discover_and_load.py`
  观察 `inspect_document_candidate() -> discover_documents() -> load_document_record()`
- `02_split_and_inspect.py`
  观察 `load_document() -> split_text()`
- `03_build_chunks.py`
  观察 `load_and_prepare_chunks() -> prepare_chunks()`
- `05_document_pipeline.py`
  观察 `run_document_pipeline()` 如何把整条链路收束成总结果

### 1. 为什么这里要区分 `ChunkDraft` 和 `SourceChunk`

这里故意把切分结果和最终输出拆成两层：

- `ChunkDraft`
  只关心切分结果、字符范围和局部 metadata
- `SourceChunk`
  再补齐 `document_id / chunk_id / base metadata`

这样更容易把“切分过程”和“标准输出接口”区分开。

---

## 先怎么读代码

### 1. 第一遍只看对象

先打开 [document_processing.py](./document_processing.py)，只看这些数据对象：

- `DocumentCandidate`
- `LoadedDocument`
- `TextChunk`
- `MarkdownSection`
- `ChunkDraft`
- `SourceChunk`
- `SplitterConfig`
- `DocumentPipelineResult`

这一遍的目标不是理解所有逻辑，而是先知道：

- 系统里有哪些最小运行时对象
- 每个对象分别描述哪一层状态
- 为什么第二章不是直接返回一个字符串列表
- 为什么单文档处理和目录级 pipeline 是两个不同观察视角

### 2. 第二遍只看主流程

然后再看这些函数：

- `inspect_document_candidate()`
- `inspect_document_candidates()`
- `discover_documents()`
- `load_document_record()`
- `split_text()`
- `split_markdown_by_headers()`
- `split_document()`
- `prepare_chunks()`
- `run_document_pipeline()`

这一遍只回答一个问题：

```text
一个文件进入系统以后，到底按什么顺序变成 SourceChunk[]？
```

### 3. 第三遍再看 metadata、ID 和回归

最后再看：

- `build_base_metadata()`
- `build_chunk_metadata()`
- `stable_document_id()`
- `stable_chunk_id()`
- `document_processing_golden_set.json`

这样读会比一开始从头到尾顺着扫更容易建立结构感。

---

## 第 1 步：看文件如何进入系统

**对应文件**：`01_discover_and_load.py`

这个脚本会把文件发现和 loader 结果直接打印出来。

重点观察：

- `faq.txt`、`product_overview.md` 和 `course_policy.pdf` 为什么会被接受
- `README.md` 为什么会被忽略
- `ignore.csv` 为什么不会进入系统
- `course_policy.pdf` 为什么会显示 `loader=pypdf.PdfReader` 和 `pages=2`

这里最重要的不是接受了多少文件，而是：

> 输入层一开始就应该告诉你自己为什么接受、为什么忽略。

如果你想真正吃透这一步，不要只看 `accepted / ignored`，还要一起看：

- 文件名
- 接受或忽略理由
- 对应 loader
- 读取后的首行预览

---

## 第 2 步：看文本如何被切成 chunk

**对应文件**：`02_split_and_inspect.py`

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

这里最值得建立的直觉不是“默认参数是多少”，而是：

> 切分器不是文本裁纸刀，而是在定义后续索引片段的边界。

---

## 第 3 步：看标准 `SourceChunk[]`

**对应文件**：`03_build_chunks.py`

第二章真正的闭环是：

```text
path -> text -> TextChunk[] -> metadata -> stable ids -> SourceChunk[]
```

如果你现在直接看代码会晕，最重要的是先把下面这件事想清楚：

> 这一节不是“把文本切开”这么简单，而是在把“切分结果”收束成“后续章节可稳定消费的标准对象”。

### 第 3 步到底在做什么

先不要盯着代码细节，先记住 `03_build_chunks.py` 背后的 4 个固定步骤：

```text
1. 先读取文档全文
2. 再切出中间结果 ChunkDraft[]
3. 再补齐 metadata 和 stable id
4. 最后收束成标准 SourceChunk[]
```

也可以写成：

```text
load
-> split_document()
-> ChunkDraft[]
-> prepare_chunks()
-> SourceChunk[]
```

### 为什么不直接 `text -> SourceChunk[]`

这是很多人第一次看这里会困惑的点。

原因是这里其实有两种不同职责：

- `split_document()`
  只负责回答“这篇文档应该怎么切”
- `prepare_chunks()`
  负责回答“切完以后，怎样补齐标准身份和 metadata”

也就是说，第二章故意把它拆成两层：

- `ChunkDraft`
  是“切分阶段”的结果
- `SourceChunk`
  是“标准输出阶段”的结果

这样拆开以后，你调试时就能更容易判断问题出在哪一层：

- 是 chunk 边界切错了
- 还是 metadata 没补全
- 还是 stable id 生成方式不稳定

### 你应该按什么顺序看代码

建议不要一上来就看 `03_build_chunks.py` 里的打印逻辑，而是按这个顺序读：

1. 先看 `load_and_prepare_chunks()`
   这是单文档入口
2. 再看 `prepare_chunks()`
   这是真正把中间结果收束成标准 chunk 的核心函数
3. 再看 `split_document()`
   看它到底怎样产出 `ChunkDraft[]`
4. 最后回来看 `03_build_chunks.py`
   这时你再看打印内容，就会知道它为什么展示这些字段

### 看 `prepare_chunks()` 时只抓 4 个动作

你可以把 `prepare_chunks()` 简化成下面这 4 步：

```text
1. 先生成 document_id
2. 再生成 base metadata
3. 再执行 split_document() 得到 ChunkDraft[]
4. 最后把每个 ChunkDraft 变成 SourceChunk
```

这 4 步分别在解决不同问题：

- `document_id`
  解决“这是谁的文档”
- `base metadata`
  解决“这份文档的公共信息是什么”
- `ChunkDraft[]`
  解决“文本具体怎么切”
- `SourceChunk`
  解决“后续系统统一消费什么格式”

重点观察：

- `document_id`
- `chunk_id`
- `source / filename / suffix / loader`
- `chunk_index`
- `char_start / char_end / chunk_chars`
- Markdown chunk 的 `header_path`
- PDF chunk 的 `page_count`

这一节真正要看的不是“打印了很多字段”，而是：

- 哪些字段属于文档级
- 哪些字段属于 chunk 级
- 为什么 `document_id` 和 `chunk_id` 都需要存在

---

## 第 4 步：看更真实的 Loader 扩展

**对应文件**：`04_loader_extensions.py`

这一节不是要把第二章做成企业级 ingestion 平台，而是要把扩展方向讲清楚。

重点观察：

- 为什么 `.md / .txt / .pdf` 需要不同 loader
- 为什么 PDF 现在可以进入系统，但扫描件/OCR 还要延后
- 为什么 Markdown 可以先按标题切分，再继续做 chunk 切分
- 为什么目录批量扫描和 loader 选择本身就是输入层的一部分

如果你看这一节时只记住“PDF 可以读了”，那还不够。

更重要的是你要建立这个判断：

```text
同样是文件，进入文本世界之前的复杂度可能完全不同
```

---

## 第 5 步：看文档处理流水线和最小治理落点

**对应文件**：`05_document_pipeline.py`

这一节是把整个第二章从分散步骤收束成一个可观察结果。

重点观察：

- `DocumentPipeline` 视角下的 `candidates / accepted / ignored / total_chunks`
- 每份文档的 `document_id`
- 每份文档的 chunk 数
- sample `chunk_id`
- 为什么更新/删除应该锚定 `document_id`
- 为什么 upsert 应该锚定 `chunk_id`

这一步不是在做后台平台，而是在把治理意识落到可运行对象上。

如果你只看最终 `total_chunks`，会错过这一节最重要的意义。

真正应该看的，是：

- pipeline 怎么把分散动作收束起来
- 为什么治理锚点从第二章就开始出现

---

## 第 6 步：最后看测试在锁定什么

**对应文件**：`tests/test_document_processing.py`

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

---

## 建议学习顺序

1. 先读 [02_document_processing.md](../../../docs/04_rag/02_document_processing.md)
2. 跑 `python -m pip install -r requirements.txt`
3. 跑 `python 01_discover_and_load.py`
4. 跑 `python 02_split_and_inspect.py`
5. 跑 `python 03_build_chunks.py`
6. 跑 `python 04_loader_extensions.py`
7. 跑 `python 05_document_pipeline.py`
8. 如果你想看边界被正式固定，再看 `tests/test_document_processing.py`

---

## 第二章最小回归集

第二章除了继续服务课程主线，还要单独锁定自己的输入层行为。

本章的 regression 文件是：

- `document_processing_golden_set.json`

它至少固定三类样本：

- 纯文本 loader：`faq.txt`
- Markdown 标题切分：`product_overview.md`
- 真实 PDF 解析：`course_policy.pdf`

这份 golden set 主要回答四个问题：

- 发现逻辑有没有跑偏
- 默认参数下的 chunk 结果有没有大幅漂移
- `source / loader / page_count / header_path` 是否还稳定
- `DocumentPipeline` 的默认演示是否仍然成立

这里最重要的直觉是：

> 第二章回归的重点不是“回答质量”，而是“输入层稳定性”。

---

## 失败案例也要刻意观察

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

---

## 建议主动修改的地方

如果你只阅读不改动，很容易停留在“看懂了”的错觉里。

建议主动试三类小改动：

1. 修改 `chunk_size / chunk_overlap`，观察 chunk 边界和 chunk 数如何变化
2. 在 Markdown 样例里改一个标题，观察 `header_path` 如何变化
3. 新增一个不支持的文件类型，观察 candidate 判断和 pipeline 汇总如何变化

每次只改一处，这样你才能看清楚：

- 哪个规则影响了哪个输入层行为
- 哪个字段在支撑后续治理
- 哪种变化属于“接口设计变化”，哪种只是“样例内容变化”

---

## 学完这一章后你应该能回答

- 为什么文档处理是知识输入层，而不是附属功能
- `loader / splitter / metadata / stable id / pipeline` 各自负责什么
- 为什么第二章真正交付的是稳定的 `SourceChunk[]`
- 为什么 Markdown 会值得做标题感知切分
- 为什么真实 PDF 解析能进第二章，但 OCR 还不该一起拉进来
- 为什么 `document_id / chunk_id` 会直接影响后面的更新、删除和治理
- 为什么第二章的 golden set 锁定的是输入层稳定性，而不是回答质量

---

## 当前真实进度和下一章

- 当前真实进度：第二章已经补上真实 PDF loader、Markdown 标题切分和最小 pipeline
- 完成标准：能跑通 `path -> SourceChunk[]`，并理解 loader 扩展和治理锚点为什么重要
- 下一章：进入 [03_embeddings](../03_embeddings/README.md)，只讲 chunk 如何变成向量表示，不再重讲输入层
