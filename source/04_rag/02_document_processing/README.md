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

## 第 1 步：看文件如何进入系统

**对应文件**：`01_discover_and_load.py`

重点观察：

- `faq.txt`、`product_overview.md`、`course_policy.pdf` 为什么会被接受
- `README.md` 为什么会被忽略
- `ignore.csv` 为什么不会进入系统
- `course_policy.pdf` 为什么会显示 `loader=pypdf.PdfReader` 和 `pages=2`

---

## 第 2 步：看文本如何被切成 chunk

**对应文件**：`02_split_and_inspect.py`

重点观察：

- `chunk_size` 和 `chunk_overlap` 会怎样影响结果
- 为什么 chunk 最好保留字符范围
- 为什么切分不应该只是机械定长截断

你还可以故意跑一个非法配置：

```bash
python 02_split_and_inspect.py data/faq.txt --chunk-size 120 --chunk-overlap 120
```

你会看到脚本直接拒绝这组参数，因为 `chunk_overlap` 不能大于等于 `chunk_size`。

---

## 第 3 步：看标准 `SourceChunk[]`

**对应文件**：`03_build_chunks.py`

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

---

## 第 4 步：看更真实的 Loader 扩展

**对应文件**：`04_loader_extensions.py`

这一节不是要把第二章做成企业级 ingestion 平台，而是要把扩展方向讲清楚。

重点观察：

- 为什么 `.md / .txt / .pdf` 需要不同 loader
- 为什么 PDF 现在可以进入系统，但扫描件/OCR 还要延后
- 为什么 Markdown 可以先按标题切分，再继续做 chunk 切分
- 为什么目录批量扫描和 loader 选择本身就是输入层的一部分

---

## 第 5 步：看文档处理流水线和最小治理落点

**对应文件**：`05_document_pipeline.py`

重点观察：

- `DocumentPipeline` 视角下的 `candidates / accepted / ignored / chunks`
- 每份文档的 `document_id`
- 为什么更新/删除应该锚定 `document_id`
- 为什么 upsert 应该锚定 `chunk_id`

这一步不是在做后台平台，而是在把治理意识落到可运行对象上。

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

---

## 建议学习顺序

1. 先读 [02_document_processing.md](../../../docs/04_rag/02_document_processing.md)
2. 跑 `python -m pip install -r requirements.txt`
3. 跑 `python 01_discover_and_load.py`
4. 跑 `python 02_split_and_inspect.py`
5. 跑 `python 03_build_chunks.py`
6. 跑 `python 04_loader_extensions.py`
7. 最后跑 `python 05_document_pipeline.py`

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

---

## 失败案例也要刻意观察

第二章至少要刻意看三类失败：

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

---

## 学完这一章后你应该能回答

- 为什么文档处理是知识输入层，而不是附属功能
- `loader / splitter / metadata / stable id / pipeline` 各自负责什么
- 为什么第二章真正交付的是稳定的 `SourceChunk[]`
- 为什么 Markdown 会值得做标题感知切分
- 为什么真实 PDF 解析能进第二章，但 OCR 还不该一起拉进来
- 为什么 `document_id / chunk_id` 会直接影响后面的更新、删除和治理

---

## 当前真实进度和下一章

- 当前真实进度：第二章已经补上真实 PDF loader、Markdown 标题切分和最小 pipeline
- 完成标准：能跑通 `path -> SourceChunk[]`，并理解 loader 扩展和治理锚点为什么重要
- 下一章：进入 [03_embeddings](../03_embeddings/README.md)，只讲 chunk 如何变成向量表示，不再重讲输入层
