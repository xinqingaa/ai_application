# 02. 文档处理

> 本节目标：把“原始文件进入系统”这件事讲清楚，理解文档发现、文本规范化、切分、metadata 和稳定 ID 为什么必须在早期就设计好，并把它们收束成标准 `SourceChunk[]`。

---

## 1. 概述

### 学习目标

- 理解为什么文档处理是 RAG 的知识入口，而不是附属功能
- 理解 `loader / splitter / metadata / stable id` 各自负责什么
- 理解 `chunk_size / chunk_overlap` 为什么会直接影响后续检索效果
- 能区分 `base metadata` 和 `chunk metadata` 的职责
- 理解为什么 `document_id / chunk_id` 必须从第二章就稳定下来
- 能对着第二章代码快照看懂 `path -> SourceChunk[]` 的完整过程

### 预计学习时间

- 文档处理链路理解：1 小时
- chunk 设计与 metadata 设计：1-1.5 小时
- 第二章代码快照阅读：1-1.5 小时

### 本节在 AI 应用中的重要性

| 场景 | 相关知识 |
|------|---------|
| 知识库导入 | 文件发现、格式判断、文本统一 |
| 文档问答 | chunk 设计、metadata、来源追溯 |
| 向量索引 | 稳定输入、稳定 ID、可复用对象 |
| 增量更新 / 删除 | `document_id / chunk_id` 稳定性 |
| 调试和评估 | chunk 预览、字符范围、来源字段 |

> **第二章真正的完成物不是“能读文件”，而是让后续系统有一份稳定、可追踪、可重复的 `SourceChunk[]` 输入。**

### 本章与前后章节的关系

第一章解决的是：

1. 为什么要做 RAG
2. 为什么默认先做固定 `2-step RAG`
3. 为什么项目先从骨架和对象开始

第二章接着解决的是：

1. 原始文件怎样进入系统
2. 文本怎样变成标准 chunk
3. metadata 和稳定 ID 为什么必须尽早出现

第三章会继续建立在这里之上：

1. 直接消费 `SourceChunk[]`
2. 把稳定 chunk 变成 `EmbeddedChunk[]`

### 本章的学习边界

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

### 当前代码快照

本章对应的代码快照是：

- [phase_2_document_processing/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/README.md)
- [scripts/build_index.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/scripts/build_index.py)
- [scripts/inspect_chunks.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/scripts/inspect_chunks.py)

---

## 2. 文档处理到底在做什么 📌

### 2.1 什么叫“文档进入系统”

很多人理解文档处理时，会把注意力放在“切分器参数怎么调”。

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

### 2.2 第二章真正的完成物是什么

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

如果第二章没有先把文档输入层做稳，后面会立刻出现问题：

- 相同文档每次生成的 chunk 不一致
- 后续 embedding 无法判断“这是谁的向量”
- 删除和增量更新没有稳定身份
- 检索结果变化后，无法判断是内容变了还是 ID 漂了

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

也就是说，Loader 的职责是“让文件可读”，不是“决定知识如何索引”。

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
- 说明 chunk 处在文档什么位置
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
- 向量存储里难以做更新和删除
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

- 可以快速定位原文位置
- 可以帮助判断切分点是否合理
- 可以支持更好的来源展示
- 可以在坏案例分析时快速回溯

这也是为什么第二章的中间对象 `TextChunk` 会保留：

- `start_index`
- `end_index`

---

## 5. 第二章应该怎么学

### 5.1 推荐顺序

建议按这个顺序进入：

1. 先读 [phase_2_document_processing/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/README.md)
2. 再看 [data/product_overview.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/data/product_overview.md) 和 [data/faq.txt](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/data/faq.txt)
3. 再看 [app/ingestion/loaders.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/ingestion/loaders.py)
4. 再看 [app/ingestion/splitters.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/ingestion/splitters.py)
5. 再看 [app/indexing/index_manager.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/indexing/index_manager.py)

### 5.2 建议先跑的命令

```bash
cd source/04_rag/labs/phase_2_document_processing

python scripts/build_index.py
python scripts/inspect_chunks.py
python scripts/inspect_chunks.py data/faq.txt
python -m unittest discover -s tests
```

### 5.3 跑完后重点观察什么

这些命令最该帮你建立的直觉是：

1. `README.md` 这类说明文件不会被当成真实输入
2. 同一套 chunk 配置下，不同文档会被切成不同数量的 chunk
3. `chunk_id` 已经不是临时字符串，而是稳定格式
4. 每个 chunk 已经带了来源和字符范围

### 5.4 改参数时应该看什么

如果你修改 `chunk_size` 或 `chunk_overlap`，建议立刻重跑：

```bash
python scripts/inspect_chunks.py
python scripts/inspect_chunks.py data/faq.txt
```

重点观察：

- chunk 数量是变多还是变少
- `char_start / char_end` 是否覆盖得更密或更疏
- 同一条 FAQ 是否被切得更碎
- overlap 增大后，边界内容是否更连续

### 5.5 卡住时先回看哪里

如果中途卡住，先回看这三个位置：

1. [phase_2_document_processing/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/README.md)
2. 本章的“代码映射表”
3. [tests/test_document_processing.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/tests/test_document_processing.py)

---

## 6. 综合案例：为产品帮助中心设计文档输入层

```python
# 你要为一个产品帮助中心做 RAG：
#
# 当前文档类型：
# 1. FAQ 文本
# 2. 产品说明 Markdown
# 3. 后续可能增加 PDF
#
# 请回答：
# 1. 第二章当前最小支持哪些格式更合适？
# 2. base metadata 至少应该包含哪些字段？
# 3. chunk metadata 至少应该包含哪些字段？
# 4. 为什么第二章就要引入 stable_document_id() 和 stable_chunk_id()？
```

当你能清楚回答这 4 个问题时，第二章的主线就真正建立起来了。

---

## 7. 本章实施步骤应该怎么理解 📌

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

## 8. 本章代码映射表

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

## 9. 实践任务

1. 解释为什么第二章真正交付的是 `SourceChunk[]`，而不是“能加载文件”。
2. 对照 [loaders.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/ingestion/loaders.py) 和 [splitters.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/app/ingestion/splitters.py)，说清 loader 和 splitter 的职责边界。
3. 跑一次 [scripts/inspect_chunks.py](/Users/linruiqiang/work/ai_application/source/04_rag/labs/phase_2_document_processing/scripts/inspect_chunks.py)，解释 `char_start / char_end / chunk_chars` 为什么重要。
4. 修改 `chunk_size` 或 `chunk_overlap`，重新运行脚本，观察 chunk 数量和字符范围如何变化。

---

## 10. 完成标准

完成这一章后，至少应满足：

- 能解释为什么文档处理是 RAG 的知识入口
- 能说明 `loaders / splitters / metadata / indexing` 的边界差异
- 能运行第二章脚本和测试，并读懂输出
- 能解释为什么 `document_id / chunk_id` 必须尽早稳定
- 能说明第二章为什么要先把 `SourceChunk` 做稳，再进入 Embedding 和检索
