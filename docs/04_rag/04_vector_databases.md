# 04. 向量存储

> 本节目标：理解为什么第三章的 `EmbeddedChunk[]` 还不等于可用检索系统，跑通一个最小的“写入、查询、filename 过滤、按文档替换、删除、持久化”闭环，并建立“向量存储层”和“Retriever 策略层”之间的边界。

---

## 1. 概述

### 学习目标

- 理解为什么只有向量还不够，系统还需要持久化、一致性和删除能力
- 理解第四章为什么只先做存储层，不提前混入 Retriever 策略
- 看懂第四章如何沿用第三章的 `SourceChunk / EmbeddedChunk / provider/model/dimensions` 契约
- 能运行第四章脚本，并解释 `upsert()`、`replace_document()`、`similarity_search()`、`delete_by_document_id()` 各自负责什么
- 能说明为什么 `document_id` 和 metadata 会在这一章变成真实职责

### 预计学习时间

- 向量存储职责和边界：30-40 分钟
- 写入 / 查询 / 删除 / 替换：40-60 分钟
- 第四章代码实践：40-60 分钟

### 本章在 RAG 工程中的重要性

| 场景 | 第四章先解决什么 |
|------|------------------|
| 离线索引 | `EmbeddedChunk[]` 如何真正落盘 |
| 在线检索 | query vector 如何在同一向量空间里查回 chunk |
| 文档更新 | 为什么要区分 chunk 级 `upsert()` 和文档级 `replace_document()` |
| 数据一致性 | 为什么删除和更新必须围绕 `document_id` |
| 进入 Retriever 前 | 为什么存储层先要把 provider/model/dimensions 契约立住 |

### 本章与前后章节的关系

第三章已经解决：

1. `SourceChunk[] -> EmbeddedChunk[]`
2. query/document 两条向量化路径
3. provider/model/dimensions 的最小契约

第四章接着解决：

1. 向量怎样真正写入持久化存储
2. 查询怎样把结果重新还原成标准 chunk
3. `document_id` 删除和文档级替换怎样建立
4. metadata 怎样参与真实查询路径

第五章会继续建立在这里之上：

1. 把当前最小查询能力抽象成 Retriever
2. 开始比较 `top_k / threshold / MMR` 等策略
3. 讨论“怎么查得更好”，而不是“能不能查”

### 第四章与第三章的连续性

第四章目录里仍然保留一份独立、可单章运行的实现，但它必须继续沿用第三章已经建立好的对象和契约：

- `SourceChunk`
- `EmbeddedChunk`
- `provider_name / model_name / dimensions`
- `source / filename / suffix / char_start / char_end / chunk_chars`

也就是说，第四章不是另起一套旧版 embedding 逻辑，而是：

> 在第三章的稳定对象之上，再增加最小持久化存储。

### 本章代码入口

本章对应的代码目录是：

- [../../source/04_rag/04_vector_databases/README.md](../../source/04_rag/04_vector_databases/README.md)
- [../../source/04_rag/04_vector_databases/vector_store_basics.py](../../source/04_rag/04_vector_databases/vector_store_basics.py)
- [../../source/04_rag/04_vector_databases/01_index_store.py](../../source/04_rag/04_vector_databases/01_index_store.py)
- [../../source/04_rag/04_vector_databases/02_search_store.py](../../source/04_rag/04_vector_databases/02_search_store.py)
- [../../source/04_rag/04_vector_databases/03_delete_document.py](../../source/04_rag/04_vector_databases/03_delete_document.py)

### 本章边界

本章重点解决：

1. 向量存储层的职责
2. 持久化写入、相似度查询、最小过滤、删除和文档级替换
3. 单一 embedding space 的一致性约束
4. 为什么第四章只做到存储层

本章不系统展开：

- MMR、Multi-query、HyDE 等策略优化
- Rerank 和混合检索
- 通用 metadata DSL 或复杂过滤表达式
- 真实云向量库的产品差异
- ANN 底层算法细节

这一章故意继续使用一个本地 JSON 持久化的最小向量存储。

目的不是替代真实向量库，而是先把下面这几件事讲清楚：

- 向量怎么存
- 向量怎么查
- 文档怎么替换
- 向量空间怎么保持一致

---

## 2. 为什么只有向量还不够 📌

### 2.1 `EmbeddedChunk[]` 还不是可用检索系统

第三章已经让系统拥有：

- chunk 身份
- metadata
- 向量表示

但在线系统还必须回答这些问题：

- 这些向量放在哪里
- 重启后还能不能查
- 同一个 `document_id` 怎样删除和重建
- query 和存量向量是不是同一个 provider/model/dimensions 空间
- metadata 到底能不能进入真实查询路径

如果这些问题没有先解决，后面的 Retriever 和生成链路都会建立在不稳定底座上。

### 2.2 向量存储到底负责什么

向量存储负责的是：

1. 存向量
2. 查向量
3. 保留向量和 chunk / metadata 的对应关系
4. 提供后续 Retriever 可复用的查询入口
5. 对 embedding space 和删除语义做最小约束

它不负责：

- 重新切分文档
- 重新生成向量
- 优化召回策略
- 组织 Prompt
- 调模型回答

所以这一层更准确的定位是：

> 向量层和 Retriever 之间的持久化基础设施。

### 2.3 为什么第四章继续用最小本地存储

第四章当前的目标不是做供应商横评，而是先把心智模型做稳。

本地 JSON 持久化实现有三个好处：

1. 没有外部依赖，学习成本低
2. 可以直接看到写入、替换、过滤、删除和落盘行为
3. 更容易把注意力放在职责边界，而不是库 API

这一章的重要性不在于“会不会背某个向量库名字”，而在于：

> 你第一次用真实持久化行为，去验证前三章建立的数据契约是否真的够用。

---

## 3. 第四章真正新增了什么 📌

### 3.1 新增的核心数据流

第四章沿用第三章的对象契约，新增的是存储层数据流：

```text
EmbeddedChunk[]
-> replace_document()
-> persistent store
-> similarity_search(query_vector, provider=...)
-> RetrievalResult[]
```

如果只想做底层 chunk 覆盖，也可以使用：

```text
EmbeddedChunk[]
-> upsert()
-> overwrite by chunk_id
```

### 3.2 当前最小向量存储交付了什么

[vector_store_basics.py](../../source/04_rag/04_vector_databases/vector_store_basics.py) 当前主要交付这些能力：

1. `VectorStoreConfig`
   负责持久化文件路径
2. `PersistentVectorStore.upsert()`
   低层原语，只按 `chunk_id` 覆盖记录
3. `PersistentVectorStore.replace_document()`
   本章推荐的文档级更新入口，会先删同 `document_id` 的旧 chunk，再写入新 chunk
4. `PersistentVectorStore.load_chunks()`
   把存储层数据重新还原成标准 `EmbeddedChunk`
5. `PersistentVectorStore.similarity_search()`
   对 query vector 做最小 Top-K 查询，并校验 query 和 store 是否属于同一 embedding space
6. `PersistentVectorStore.delete_by_document_id()`
   建立最小删除入口

### 3.3 第四章新增的存储层契约

第四章不是“多一个 JSON 文件”这么简单，它还要守住这些契约：

1. 同一个 store 只能保存一个 provider/model/dimensions 空间
2. query 和 stored vectors 必须来自同一个 provider/model 空间
3. 反序列化时不能信任磁盘数据，必须校验 record 形状和向量维度
4. `upsert()` 和 `replace_document()` 的语义必须明确区分

如果这些边界不立住，第五章的 Retriever 就会建立在模糊接口之上。

### 3.4 为什么 metadata 必须一起写入

第四章的关键点之一是：

> metadata 不再只是“方便调试看看”，而是会进入真实查询和删除路径。

这一章的 demo 至少会保留这些字段：

- `source`
- `filename`
- `suffix`
- `chunk_index`
- `char_start / char_end / chunk_chars`

当前代码里：

- `filename` 真的会进入过滤条件
- `source / chunk_index / range` 会进入调试输出
- `document_id` 会进入替换和删除逻辑

如果写入时把这些字段丢掉，后面就会出现两个典型问题：

1. 查到了内容，但解释不了来源
2. 文档更新时，不知道该删哪批旧 chunk

### 3.5 为什么 `document_id` 在这一章变得特别重要

第二章里 stable id 还是“结构上应该有”。

到了第四章，`document_id` 已经开始承担真实职责：

- 作为删除入口
- 作为文档级替换入口
- 作为一致性锚点
- 作为后续增量更新的基础

这就是为什么第二章的 stable id 不是“形式正确”，而是后面真的会被用到。

### 3.6 `upsert()` 和 `replace_document()` 应该怎么理解

这是第四章最容易被说混的一点。

`upsert()` 的真实语义是：

- 只按 `chunk_id` 覆盖
- 适合底层写入原语
- 不负责清理同文档的旧 chunk

`replace_document()` 的真实语义是：

- 先删当前批次里同 `document_id` 的旧 chunk
- 再写入新的 `EmbeddedChunk[]`
- 适合第四章当前“文档重建后重新入库”的更新路径

所以第四章现在应该教你的不是“更新就是 upsert”，而是：

> chunk 级写入和文档级一致性不是一回事。

### 3.7 当前过滤边界是什么

第四章现在确实支持过滤，但要说准确：

> 当前最小实现只支持 `filename` 过滤，不是通用 metadata 过滤 DSL。

这样设计是为了先把过滤路径跑通，而不是提前做复杂接口。

真实向量数据库通常会支持更通用的 metadata filter，但那已经超出这一章重点。

---

## 4. 第四章如何分层 📌

### 4.1 当前课程建议的分层

| 层 | 当前章节 | 解决什么问题 |
|----|----------|--------------|
| 文档输入层 | 第二章 | 文件怎样进入系统 |
| 向量化层 | 第三章 | chunk 怎样变成向量 |
| 向量存储层 | 第四章 | 向量怎样真正存、查、替换、删 |
| Retriever 层 | 第五章 | 怎样查得更好 |

### 4.2 为什么第四章和第五章还要拆开

很多初学者会觉得：

> “既然现在都能查 Top-K 了，这不就是 Retriever 了吗？”

还不是。

第四章当前的能力更接近：

- 给你一个 query vector
- 校验它和存储是否在同一 embedding space
- 返回最相近的 chunk
- 支持最小 `filename` 过滤和按 `document_id` 删除 / 替换

而第五章会继续在这里之上做：

- 更明确的 Retriever 抽象
- `top_k / threshold / MMR` 等策略选择
- 召回质量比较和坏案例分析

所以拆开的意义在于：

- 第四章先把存储基础设施做稳
- 第五章再把“怎么查得更好”做成策略问题

---

## 5. 第四章实践：独立向量存储闭环

### 5.1 目录结构

```text
source/04_rag/04_vector_databases/
├── README.md
├── vector_store_basics.py
├── 01_index_store.py
├── 02_search_store.py
├── 03_delete_document.py
├── store/
└── tests/
```

这一章和前几章一样，保持平铺目录。

这里不做：

- 外部库依赖
- 通用向量数据库适配层
- Retriever 策略层

### 5.2 输入和输出

本章代码的输入是：

- 一组固定样例 `EmbeddedChunk[]`
- 一个 query vector
- query 所属的 provider
- 可选 `filename` 过滤

本章代码的输出是：

- 持久化存储文件
- `RetrievalResult[]`
- 删除或替换后的剩余文档状态

在 [vector_store_basics.py](../../source/04_rag/04_vector_databases/vector_store_basics.py) 里，你最值得先看的是：

- `demo_chunk_metadata()`
- `demo_embedded_chunks()`
- `upsert()`
- `replace_document()`
- `similarity_search()`
- `delete_by_document_id()`

### 5.3 运行方式

```bash
cd source/04_rag/04_vector_databases

python 01_index_store.py --reset
python 02_search_store.py
python 02_search_store.py "为什么 metadata 很重要？" --filename metadata_rules.md
python 03_delete_document.py trial
python -m unittest discover -s tests
```

其中测试命令不是这一章重点，但可以作为辅助验证。

### 5.4 你应该观察到什么

跑 [01_index_store.py](../../source/04_rag/04_vector_databases/01_index_store.py) 时：

- 存储文件真正被创建
- 脚本会打印当前 embedding space
- demo index 会按文档级 `replace_document()` 写入
- 当前有哪些 `document_id`

跑 [02_search_store.py](../../source/04_rag/04_vector_databases/02_search_store.py) 时：

- query 会先变成 query vector
- store 会校验 query 和 stored vectors 是否属于同一 embedding space
- store 会按相似度排序
- 返回结果仍然保留 `chunk_id / document_id / metadata`
- 带 `--filename` 时，结果范围会明显缩小

跑 [03_delete_document.py](../../source/04_rag/04_vector_databases/03_delete_document.py) 时：

- 删除是围绕 `document_id` 做的
- 删除后 count 会下降
- 剩余 document ids 会变化
- 命令输出会提醒你：文档更新要用 `replace_document()`，不是只做 chunk 级 `upsert()`

### 5.5 本章代码刻意简化了什么

这一章的实现刻意简化了五件事：

1. 只用本地 JSON 持久化文件
2. 不接真实向量数据库产品
3. 只做最小相似度查询
4. 过滤只支持 `filename`
5. 不做 Retriever 策略层

这是故意的。

因为本章真正要先学会的是：

> 第四章解决的是“向量怎么存、怎么查、怎么替换、怎么删”，不是“怎么把召回调到最好”。

### 5.6 这一章值得刻意观察的失败案例

第四章至少要刻意观察三类失败：

1. store 混入不同 embedding space

如果一个 store 里混入不同 provider/model/dimensions 的向量，系统应该直接拒绝，而不是继续查。

2. query 和 store 不在同一向量空间

如果 query vector 的 provider/model 和 store 不一致，系统也应该拒绝比较。

3. 文档更新只做 chunk 级覆盖

如果你只做 `upsert()`，但不清理同一 `document_id` 的旧 chunk，就会留下陈旧数据。

这些失败都不是“实现细节”，而是第五章前必须先立住的工程边界。

---

## 6. 本章学完后你应该能回答

- 为什么 `EmbeddedChunk[]` 还不等于可用检索系统
- 为什么向量存储要负责持久化、查询、最小过滤、删除和替换
- 为什么同一个 store 只能保留一个 embedding space
- 为什么 `upsert()` 和 `replace_document()` 不能混成一个模糊概念
- 为什么第四章现在只支持 `filename` 过滤
- 为什么第四章现在还不应该把 Retriever 策略混进来

---

## 7. 下一章

第五章开始，你才会进入 Retriever 策略问题：

- `top_k` 怎么设
- `threshold` 有什么边界
- `MMR` 在解决什么问题

也就是说，第五章处理的是“查得更好”，不是“能不能查”。

第四章先把“能存、能查、能替换、能删、能保持向量空间一致”立住，就够了。
