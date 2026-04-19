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

### 本章在 AI 应用中的重要性

| 场景 | 本章先解决什么 |
|------|----------------|
| 知识库接入 | 哪些文件该进系统，哪些不该进 |
| 文本标准化 | 不同文件输入怎样收束成统一文本 |
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

第三章会继续建立在这里之上：

1. 直接消费稳定的 `SourceChunk[]`
2. 把 chunk 再变成向量表示

第四章会继续依赖这里：

1. 让向量库知道“自己在存哪份文档、哪个 chunk”
2. 让后续删除、更新和回填有稳定锚点

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
- 完整 ingestion 平台或企业级同步系统

这里故意只保留：

- `.md / .txt`
- 本地样例文件
- 平铺代码目录

目的不是追求格式覆盖最全，而是先把文档处理主线讲清楚。

但第二章仍然会保留一个最小回归集，避免你改 loader、splitter 或 metadata 后，不知道是否偏离教学主线。

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
-> 切成 TextChunk[]
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

### 2.4 为什么第二章不该急着接 Embedding

如果这一步还没把 `SourceChunk[]` 做稳，就急着进第三章，问题只会被推迟，不会消失。

比如：

- 你会在第三章才发现 chunk 边界根本不合理
- 你会在第四章才发现不知道该删哪个向量
- 你会在第五章才发现 metadata 根本不够做过滤和引用

所以第二章最重要的价值不是“离 embedding 更近了一步”，而是：

> 先把知识输入层做成一个稳定的、可重复的标准接口。

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

### 3.5 第二章最小输入输出清单

可以把本章的职责收成下面这张表：

| 模块 | 输入 | 输出 | 不负责什么 |
|------|------|------|-----------|
| Loader | `Path` | 规范化后的 `text` | 切分、chunk metadata、稳定 ID |
| Splitter | `text + config` | `TextChunk[]` | 来源字段、文档身份 |
| Metadata Builder | 文档信息 + chunk 范围 | metadata 字典 | 切分边界、向量化 |
| ID Builder | `source / document_id / chunk content` | `document_id / chunk_id` | 检索排序、回答生成 |
| Final Builder | `Path + text + config` | `SourceChunk[]` | Embedding、Vector DB |

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

### 4.4 非法参数为什么应该尽早失败

第二章不是“先随便切，后面再调”，而是要从一开始就把边界条件立住。

例如：

- `chunk_size <= 0` 没有意义
- `chunk_overlap < 0` 没有意义
- `chunk_overlap >= chunk_size` 会让切分策略失去正常含义

这也是为什么第二章代码里 `SplitterConfig` 会直接拒绝非法参数。

### 4.5 稳定 ID 不等于“永远不变”

这里的“稳定”要理解准确。

它的意思是：

- 同一份源文件
- 同一套切分配置
- 同一份 chunk 内容

重复处理时，ID 应该保持一致。

但如果下面这些东西变了，ID 变化通常是合理的：

- 文件路径变了
- 文档内容变了
- 切分配置变了
- chunk 边界变了

所以第二章追求的是“可重复的身份锚点”，不是“无论发生什么都强行不变”。

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

- `inspect_document_candidate()`
- `inspect_document_candidates()`
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

你还可以额外运行一个失败案例：

```bash
python 02_split_and_inspect.py data/faq.txt --chunk-size 120 --chunk-overlap 120
```

### 5.4 你应该观察到什么

跑 [01_discover_and_load.py](/Users/linruiqiang/work/ai_application/source/04_rag/02_document_processing/01_discover_and_load.py) 时：

- 你会看到 `faq.txt` 和 `product_overview.md` 被接受
- 你会看到 `README.md` 被忽略，因为它只是章节辅助文件
- 你会看到 `ignore.csv` 被忽略，因为当前阶段不支持这个后缀
- 文本进入系统前会先做最小规范化

跑 [02_split_and_inspect.py](/Users/linruiqiang/work/ai_application/source/04_rag/02_document_processing/02_split_and_inspect.py) 时：

- 你能看到 chunk 的字符范围
- 你能看到不同参数如何影响切分结果
- 你能看到切分不是单纯按固定长度硬截断
- 你能看到非法参数会被直接拒绝，而不是悄悄产生不稳定结果

跑 [03_build_chunks.py](/Users/linruiqiang/work/ai_application/source/04_rag/02_document_processing/03_build_chunks.py) 时：

- 你会看到每份文档产出多少个 chunk
- 你会看到 `document_id / chunk_id`
- 你会看到 `source / filename / suffix / chunk_index`
- 你会看到 `char_start / char_end / chunk_chars`
- 你会看到相同文档重复处理时，chunk ID 会保持稳定

### 5.5 第二章最小回归集

第二章不做完整评估系统，但应该从一开始就保留一个最小回归集。

因为你后面会不断改：

- 文档发现规则
- 文本规范化逻辑
- 切分配置
- metadata 字段
- 稳定 ID 逻辑

如果没有最小回归样本，很容易出现这样的情况：

- 文档还在讲“稳定输入层”
- 代码却已经让 chunk 数、metadata 或 ID 漂了
- 你自己还没发现

这一章最小回归集只需要锁定两个样例文档：

```python
mini_golden_set = [
    {
        "filename": "faq.txt",
        "expected_chunk_count": 3,
        "expected_source": "data/faq.txt",
    },
    {
        "filename": "product_overview.md",
        "expected_chunk_count": 9,
        "expected_source": "data/product_overview.md",
    },
]
```

这不是完整评估体系，但已经足够回答：

1. 发现逻辑有没有跑偏
2. 默认参数下的切分结果有没有大幅漂移
3. `source` 和 metadata 是否还稳定
4. 章节 demo 是否仍然可重复

### 5.6 本章代码刻意简化了什么

这一章的实现刻意简化了五件事：

1. 只支持 `.md / .txt`
2. 不接 PDF / OCR
3. 不做复杂版式解析
4. 不接 embedding 和向量库
5. 不做真实生产环境的同步、权限、版本治理

这是故意的。

因为本章要先把下面这件事学会：

> 文档处理的目标不是“支持最多格式”，而是“先稳定地产出可用 chunk”。

---

## 6. 本章学完后你应该能回答

- 为什么文档处理是知识输入层，而不是附属功能
- `loader / splitter / metadata / stable id` 各自负责什么
- 为什么第二章真正交付的是稳定 `SourceChunk[]`
- 为什么字符范围和稳定 ID 从第二章就应该存在
- 为什么“稳定”意味着可重复，而不是无条件永远不变
- 为什么这一步会直接影响第三章和第四章

---

## 7. 下一章

第三章开始，你才会进入向量化问题：

- chunk 怎么变成向量
- 向量相似度在做什么
- 为什么向量化只是给 chunk 再包一层表示

也就是说，第三章处理的是“这些稳定 chunk 如何变成可检索向量”。

第二章先把“知识怎么进入系统”“哪些字段该从这里就稳定下来”立住，就够了。
