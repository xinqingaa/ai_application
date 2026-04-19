# 02. 文档处理

> 本节目标：把“原始文件进入系统”这件事讲清楚，理解文档发现、文本规范化、切分、metadata 和稳定 ID 为什么必须尽早确定，并把它们收束成稳定、可重复的 `SourceChunk[]`。

---

## 1. 概述

### 学习目标

- 理解为什么文档处理是 RAG 的知识入口，而不是附属功能
- 理解 `loader / splitter / metadata / stable id` 各自负责什么
- 理解 `chunk_size / chunk_overlap` 为什么会直接影响后续检索效果
- 能区分 `base metadata` 和 `chunk metadata` 的职责
- 理解为什么 `document_id / chunk_id` 必须从第二章就稳定下来
- 能对着第二章代码看懂 `path -> SourceChunk[]` 的完整过程

### 预计学习时间

- 文档输入层理解：40 分钟
- chunk 设计与 metadata：40-60 分钟
- 第二章代码实践：40-60 分钟

### 本章与前后章节的关系

第一章解决的是：

1. 为什么要做 RAG
2. 最小 `2-step RAG` 在线链路长什么样
3. 什么情况下该用什么方案

第二章接着解决的是：

1. 原始文件怎样进入系统
2. 文本怎样变成标准 chunk
3. metadata 和稳定 ID 为什么必须尽早出现

第三章会继续建立在这里之上：

1. 直接消费稳定的 `SourceChunk[]`
2. 把 chunk 再变成向量表示

### 本章代码入口

本章对应的代码目录是：

- [source/04_rag/02_document_processing/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/02_document_processing/README.md)
- [document_processing.py](/Users/linruiqiang/work/ai_application/source/04_rag/02_document_processing/document_processing.py)
- [01_discover_and_load.py](/Users/linruiqiang/work/ai_application/source/04_rag/02_document_processing/01_discover_and_load.py)
- [02_split_and_inspect.py](/Users/linruiqiang/work/ai_application/source/04_rag/02_document_processing/02_split_and_inspect.py)
- [03_build_chunks.py](/Users/linruiqiang/work/ai_application/source/04_rag/02_document_processing/03_build_chunks.py)

### 本章边界

本章重点解决：

1. 文档发现和读取
2. 文本规范化
3. 切分策略
4. metadata 设计
5. 稳定 ID

本章不展开：

- PDF / OCR / 复杂表格解析
- HTML、网页抓取、知识库同步
- 真实 Embedding
- 真实向量数据库
- 检索排序和 Rerank
- 完整 RAG 问答生成

这里故意只保留：

- `.md / .txt`
- 本地样例文件
- 平铺代码目录

目的不是追求格式覆盖最全，而是先把文档处理主线讲清楚。

---

## 2. 文档处理到底在做什么 📌

### 2.1 什么叫“文档进入系统”

很多人一提文档处理，就会马上把注意力放在“切分器参数怎么调”。

但更完整的视角应该是：

```text
文件
-> 判断是否支持
-> 读取文本
-> 做最小规范化
-> 切成 text chunks
-> 注入 metadata
-> 生成稳定 document_id / chunk_id
-> 产出 SourceChunk[]
```

也就是说，第二章不是在做一个单独的“文本预处理工具”，而是在做：

> RAG 系统的知识输入层。

### 2.2 第二章真正交付的是什么

第二章真正交付的不是“能读 Markdown”或“能把文本切开”，而是：

```text
path -> text -> text chunks -> metadata -> stable ids -> SourceChunk[]
```

这里最该先记住的四个概念是：

- `raw text`
  从文件读出来的统一文本
- `TextChunk`
  splitter 返回的中间对象，包含内容和字符范围
- `SourceChunk`
  后续阶段统一消费的标准 chunk 对象
- `document_id / chunk_id`
  用来保证重复处理、更新、删除和调试都有稳定锚点

### 2.3 为什么文档处理不能被当成附属功能

如果第二章没有先把文档输入层做稳，后面很快就会出现问题：

- 相同文档每次生成的 chunk 不一致
- embedding 阶段无法判断“这是谁的向量”
- 删除和增量更新没有稳定身份
- 调试时无法确认是内容变了还是 ID 漂了

所以第二章并不是“还没到检索前的准备工作”，而是：

> 在给后面的向量化、向量存储、检索和评估打地基。

---

## 3. Loader、Splitter、Metadata、ID 各自负责什么 📌

### 3.1 Loader 负责什么

Loader 负责的是：

- 发现哪些文件应该进入系统
- 判断格式是否支持
- 把文件读取成统一文本
- 做最小文本规范化

Loader 不负责：

- chunk 怎么切
- metadata 怎么设计
- stable id 怎么生成

它的职责是“让文件可读”，不是“决定知识如何索引”。

### 3.2 Splitter 负责什么

Splitter 负责的是：

- 把长文本切成更小段
- 保留字符范围
- 控制 `chunk_size / chunk_overlap`
- 尽量避免在很差的位置生硬截断

Splitter 不负责：

- 来源字段
- 文件级身份
- 系统级标准对象

它更像是在做：

> 从文本到“可索引片段”的第一次结构化。

### 3.3 Metadata 负责什么

Metadata 负责的是：

- 说明 chunk 从哪里来
- 说明 chunk 在文档什么位置
- 为后续检索、过滤、引用和调试提供信息

一个最小 RAG 系统里，metadata 至少应该能回答：

- 来源文件是什么
- chunk 是第几个
- 覆盖了哪段字符范围
- 文档基本统计信息是什么

这也是为什么本章需要区分：

- `base metadata`
- `chunk metadata`

前者描述文档，后者描述当前 chunk。

### 3.4 Stable ID 负责什么

Stable ID 负责的是：

- 让文档可重复定位
- 让 chunk 可重复定位
- 让后续更新、删除、回归测试和坏案例定位成为可能

没有稳定 ID，后面很快就会遇到：

- 重复导入后无法确认是不是同一份数据
- 存储系统里难以做更新和删除
- 评估和调试时无法稳定定位坏 chunk

所以第二章引入稳定 ID，不是“过度工程化”，而是：

> 从一开始就让系统有长期可维护的身份锚点。

---

## 4. chunk 设计为什么会直接影响后续检索 📌

### 4.1 为什么不是切得越细越好

chunk 太小，常见问题是：

- 语义不完整
- 缺上下文
- 回答时证据过碎

chunk 太大，常见问题是：

- 混入太多无关信息
- 检索命中不够精确
- 上下文成本变高

所以 `chunk_size` 本质上不是“参数微调”，而是在平衡：

1. 语义完整性
2. 检索精度
3. 上下文成本

### 4.2 overlap 为什么存在

很多知识内容天然跨段落或跨句子。

如果完全不做 overlap，可能出现：

- 一个重要句子刚好被切断
- 实体和描述落在两个 chunk 里
- 查询时每个 chunk 单看都不够完整

所以 overlap 的目标不是“让 chunk 重复越多越稳”，而是：

> 在边界处保留一点连续性，减少关键内容被切断的概率。

### 4.3 为什么 chunk 最好保留字符范围

字符范围的意义不只在调试，也在后续工程里很重要：

- 你可以定位 chunk 覆盖了原文哪一段
- 你可以判断切分边界是否合理
- 你可以在引用展示时做高亮
- 你可以在坏案例分析时稳定回到原文位置

这也是为什么第二章的中间对象 `TextChunk` 会保留：

- `start_index`
- `end_index`

---

## 5. 第二章实践：独立文档处理闭环

### 5.1 目录结构

本章代码目录是：

```text
source/04_rag/02_document_processing/
├── README.md
├── document_processing.py
├── 01_discover_and_load.py
├── 02_split_and_inspect.py
├── 03_build_chunks.py
├── data/
└── tests/
```

第二章和第一章一样，保持平铺目录。

这里不做：

- `app/ingestion/`
- `app/indexing/`
- 多层包组织

因为本章重点是理解文档处理本身，不是理解工程分层。

### 5.2 输入和输出

本章代码的输入是：

- 本地 `.md / .txt` 文件
- `chunk_size / chunk_overlap`

本章代码的输出是：

- `TextChunk[]`
- `SourceChunk[]`
- `document_id`
- `chunk_id`
- `base metadata + chunk metadata`

在 [document_processing.py](/Users/linruiqiang/work/ai_application/source/04_rag/02_document_processing/document_processing.py) 里，你最值得先看的是：

- `discover_documents()`
- `load_document()`
- `split_text()`
- `build_base_metadata()`
- `build_chunk_metadata()`
- `stable_document_id()`
- `stable_chunk_id()`
- `load_and_prepare_chunks()`

### 5.3 运行方式

```bash
cd source/04_rag/02_document_processing

python 01_discover_and_load.py
python 02_split_and_inspect.py
python 02_split_and_inspect.py data/faq.txt --chunk-size 140 --chunk-overlap 20
python 03_build_chunks.py
python -m unittest discover -s tests
```

### 5.4 你应该观察到什么

跑 [01_discover_and_load.py](/Users/linruiqiang/work/ai_application/source/04_rag/02_document_processing/01_discover_and_load.py) 时：

- `.md / .txt` 会进入系统
- `README.md` 会被忽略
- `ignore.csv` 不会被当成支持格式
- 文本进入系统前会先做最小规范化

跑 [02_split_and_inspect.py](/Users/linruiqiang/work/ai_application/source/04_rag/02_document_processing/02_split_and_inspect.py) 时：

- 你能看到 chunk 的字符范围
- 你能看到不同参数如何影响切分结果
- 你能看到切分不是单纯按固定长度硬截断

跑 [03_build_chunks.py](/Users/linruiqiang/work/ai_application/source/04_rag/02_document_processing/03_build_chunks.py) 时：

- 你会看到每份文档产出多少个 chunk
- 你会看到 `document_id / chunk_id`
- 你会看到 metadata 如何跟着 chunk 一起进入系统

### 5.5 本章代码刻意简化了什么

这一章的实现刻意简化了四件事：

1. 只支持 `.md / .txt`
2. 不接 PDF / OCR
3. 不做复杂版式解析
4. 不接 embedding 和向量库

这是故意的。

因为本章要先把下面这件事学会：

> 文档处理的目标不是“支持最多格式”，而是“先稳定地产出可用 chunk”。

---

## 6. 本章学完后你应该能回答

- 为什么文档处理是知识输入层，而不是附属功能
- `loader / splitter / metadata / stable id` 各自负责什么
- 为什么第二章真正交付的是稳定 `SourceChunk[]`
- 为什么字符范围和稳定 ID 从第二章就应该存在
- 为什么这一步会直接影响第三章和第四章

---

## 7. 下一章

第三章开始，你才会进入向量化问题：

- chunk 怎么变成向量
- 向量相似度在做什么
- 为什么向量化只是给 chunk 再包一层表示

也就是说，第三章处理的是“这些稳定 chunk 如何变成可检索向量”。

第二章先把“知识怎么进入系统”立住，就够了。
