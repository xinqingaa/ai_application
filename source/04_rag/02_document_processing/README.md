# 02. 文档处理 - 实践指南

> 本文档说明如何跟着 [学习文档](/Users/linruiqiang/work/ai_application/docs/04_rag/02_document_processing.md) 学完第二章，并在不依赖第三章以后的前提下，把原始文件稳定转换成标准 chunk。

---

## 核心原则

```text
先看文件如何被发现和读取 -> 再看文本如何切分 -> 最后看 metadata 和稳定 ID 如何进入 chunk
```

- 在 `source/04_rag/02_document_processing/` 目录下操作
- 本章只讲知识如何进入系统，不讲 embedding、向量库、检索和生成
- 本章代码保持平铺，不做项目骨架
- 本章输出只有一个重点：稳定、可重复的 `SourceChunk[]`
- 旧的 `labs/phase_2_document_processing/` 只作为迁移期备份，不再是当前学习入口

---

## 项目结构

```text
02_document_processing/
├── README.md
├── document_processing.py
├── 01_discover_and_load.py
├── 02_split_and_inspect.py
├── 03_build_chunks.py
├── data/
│   ├── product_overview.md
│   ├── faq.txt
│   ├── README.md
│   └── ignore.csv
└── tests/
    └── test_document_processing.py
```

- `document_processing.py`
  放本章所有最小对象和文档处理逻辑
- `01_discover_and_load.py`
  看哪些文件会被发现、会不会被规范化
- `02_split_and_inspect.py`
  看文本怎么切成 `TextChunk`
- `03_build_chunks.py`
  看 `path -> text -> chunks -> metadata -> stable ids -> SourceChunk[]`

---

## 前置准备

### 1. 运行目录

```bash
cd source/04_rag/02_document_processing
```

### 2. 当前命令

```bash
python 01_discover_and_load.py
python 02_split_and_inspect.py
python 02_split_and_inspect.py data/faq.txt --chunk-size 140 --chunk-overlap 20
python 03_build_chunks.py
python -m unittest discover -s tests
```

### 3. 先跑哪个

建议先跑：

```bash
python 01_discover_and_load.py
```

你最先要建立的直觉是：

- 不是所有文件都应该进入系统
- 文本进入系统前通常要先做最小规范化
- 第二章真正交付的不是“能读文件”，而是“稳定输入”

---

## 第 1 步：看文件如何进入系统

**对应文件**：`01_discover_and_load.py`

重点观察：

- 哪些文件会被发现
- `README.md` 为什么会被忽略
- 不支持的后缀为什么不会进入系统
- 文本被加载后，字符数和行数会怎样变化

---

## 第 2 步：看文本如何被切成 chunk

**对应文件**：`02_split_and_inspect.py`

重点观察：

- `chunk_size` 和 `chunk_overlap` 会怎样影响结果
- 为什么 chunk 最好保留字符范围
- 为什么切分不应该只是机械定长截断

运行后重点看：

- `start_index / end_index`
- 每个 chunk 的预览文本
- 同一份文档在不同参数下的切分差异

---

## 第 3 步：看 metadata 和稳定 ID 如何进入系统

**对应文件**：`03_build_chunks.py`

第二章真正的闭环是：

```text
path -> text -> text chunks -> metadata -> stable ids -> SourceChunk[]
```

重点观察：

- `document_id`
- `chunk_id`
- `source / filename / suffix`
- `char_start / char_end / chunk_chars`

---

## 第 4 步：最后看测试在锁定什么

**对应文件**：`tests/test_document_processing.py`

测试只锁定本章最重要的几件事：

1. 文档发现逻辑正确
2. 文本规范化没有破坏结构
3. chunk 会带字符范围
4. 重复处理时 ID 保持稳定

---

## 建议学习顺序

1. 先读 [02_document_processing.md](/Users/linruiqiang/work/ai_application/docs/04_rag/02_document_processing.md)
2. 再跑 `python 01_discover_and_load.py`
3. 再跑 `python 02_split_and_inspect.py`
4. 最后跑 `python 03_build_chunks.py`

---

## 学完这一章后你应该能回答

- 为什么文档处理是知识输入层，而不是附属功能
- `loader / splitter / metadata / stable id` 各自负责什么
- 为什么第二章真正交付的是稳定的 `SourceChunk[]`
- 为什么第二章会直接影响第三章的 embedding 和第四章的向量存储

---

## 当前真实进度和下一章

- 当前真实进度：第二章已经改成独立学习单元
- 完成标准：能跑通 `path -> SourceChunk[]`，能解释每个字段为什么存在
- 下一章：进入 [source/04_rag/03_embeddings/README.md](/Users/linruiqiang/work/ai_application/source/04_rag/03_embeddings/README.md)，只讲 chunk 如何变成向量表示，不再要求继承第二章的项目结构
