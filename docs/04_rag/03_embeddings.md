# 03. 向量化

> 本章目标：先把“文本为什么要变成向量”讲清楚，建立 `SourceChunk -> EmbeddedChunk`、`embed_query / embed_documents` 和同一 embedding space 的最小心智模型，然后在同一章里补上真实 embeddings endpoint 的接入桥。

---

## 1. 概述

### 学习目标

- 理解为什么要把文本变成向量
- 理解 `SourceChunk -> EmbeddedChunk` 到底新增了什么
- 理解为什么 `embed_query / embed_documents` 不该混成一个模糊接口
- 理解为什么 query/document 必须落在同一 embedding space
- 理解为什么真实 embeddings endpoint 的关注点是维度、批量输入和契约稳定性
- 理解 toy provider 和真实 provider 在第三章里的关系
- 能看懂第三章代码里的最小语义排序闭环

### 预计学习时间

- 向量化原理：40 分钟
- provider 契约与 query/document：40 分钟
- 真实 embeddings endpoint 桥接：40-60 分钟
- 第三章代码实践：40-60 分钟

### 本章在 AI 应用中的重要性

| 场景 | 本章先解决什么 |
|------|----------------|
| 语义检索 | 文本怎样变成可以比较的向量 |
| provider 切换 | 模型变了以后，哪些契约必须保持 |
| 检索质量 | 为什么语义向量能补足纯关键词的局限 |
| 后续存储 | 向量进入第四章前应该长成什么样 |

### 学习前提

- 建议先完成第二章，已经理解稳定 `SourceChunk[]` 的意义
- 建议先完成 `02_llm/02_multi_provider`
- 你应该已经掌握真实 LLM / OpenAI-compatible 平台的基本调用方式

这一章不再重复讲：

- `api_key`
- `base_url`
- 统一客户端
- 多平台差异的通用抽象

第三章只关注 embedding-specific 的问题。

### 本章与前后章节的关系

第二章解决的是：

1. 原始文件怎样进入系统
2. 文本怎样变成稳定 `SourceChunk[]`
3. metadata 和稳定 ID 为什么必须尽早出现

第三章接着解决的是：

1. 稳定 chunk 怎样变成向量
2. query/document 为什么要保留两个入口
3. 为什么 provider 契约应该在这一章就立住
4. toy provider 怎样过渡到真实 embeddings endpoint

第四章会继续依赖这里：

1. 把 `EmbeddedChunk[]` 写进向量存储
2. 在存储层继续维护 provider/model space 的一致性

### 本章代码入口

本章对应的代码目录是：

- [README.md](../../source/04_rag/03_embeddings/README.md)
- [requirements.txt](../../source/04_rag/03_embeddings/requirements.txt)
- [embedding_basics.py](../../source/04_rag/03_embeddings/embedding_basics.py)
- [01_embed_chunks.py](../../source/04_rag/03_embeddings/01_embed_chunks.py)
- [02_compare_similarity.py](../../source/04_rag/03_embeddings/02_compare_similarity.py)
- [03_query_vs_document.py](../../source/04_rag/03_embeddings/03_query_vs_document.py)
- [04_real_embeddings.py](../../source/04_rag/03_embeddings/04_real_embeddings.py)
- [05_semantic_search.py](../../source/04_rag/03_embeddings/05_semantic_search.py)
- [data/source_chunks.json](../../source/04_rag/03_embeddings/data/source_chunks.json)
- [data/search_cases.json](../../source/04_rag/03_embeddings/data/search_cases.json)

### 本章边界

本章重点解决：

1. 向量化在做什么
2. `EmbeddedChunk` 为什么存在
3. `embed_query / embed_documents` 为什么要分开
4. provider 契约
5. 最小语义排序
6. 真实 embeddings endpoint 的桥接

本章不展开：

- 向量数据库
- metadata 过滤检索
- rerank
- hybrid retrieval
- 生成回答
- 第四章的存储层 API

---

## 2. 向量化到底在做什么 📌

### 2.1 为什么要把文本变成向量

如果系统只会做字符串匹配，很快会遇到两个问题：

- 同义表达容易漏召回
- 表面词很像但语义不相关的内容可能被误排前面

Embedding 的核心作用不是“把文本变高级”，而是：

> 把文本映射成一个可以计算相似度的表示空间。

### 2.2 第三章真正新增的是什么

第三章真正新增的不是新的一套输入层，而是：

```text
SourceChunk[] -> EmbeddedChunk[]
```

这里新增的核心字段只有几类：

- `vector`
- `provider_name`
- `model_name`
- `dimensions`

第二章留下来的这些字段仍然必须保留：

- `chunk_id`
- `document_id`
- `source`
- `filename`
- `suffix`
- `char_start / char_end`

所以你应该把 `EmbeddedChunk` 理解成：

> 保留原始 chunk 身份的向量增强版。

### 2.3 为什么 `EmbeddedChunk` 不是替代 `SourceChunk`

如果第三章直接把 chunk 内容和 metadata 丢掉，只留下向量，后面会立刻出问题：

- 第四章不知道自己在存哪一个 chunk
- 后续引用和删除没有稳定锚点
- 调试时也不知道是哪个原文片段得分高

所以第三章不是在“用向量替代文本”，而是在“给稳定 chunk 再包一层可比较表示”。

### 2.4 第三章到底继承了第二章什么

第三章默认直接消费第二章留下来的这些成果：

- 稳定 `SourceChunk[]`
- 稳定 `document_id / chunk_id`
- 稳定 metadata

也就是说，第三章本质上是在回答：

> 这些已经稳定下来的 chunk，怎样进入同一个可比较的语义空间？

---

## 3. 为什么 query 和 document 要分开向量化 📌

### 3.1 两者在系统里的角色不同

在检索系统里：

- document vector 代表“知识库里的候选依据”
- query vector 代表“用户此刻在找什么”

它们都属于同一个 embedding space，但在系统角色上不是同一件事。

### 3.2 为什么保留两个入口更稳妥

第三章要保留：

- `embed_query()`
- `embed_documents()`

不是因为所有真实 provider 都会给你两个完全不同的 API，而是因为：

1. 教学上，这能把 query/document 的角色差异显式暴露出来
2. 工程上，这给未来切换模型或 provider 留出了更稳的接口边界

### 3.3 为什么“分开”不等于“随便用不同空间”

这也是最容易误解的点。

保留两个入口，不代表你可以：

- query 用一个 provider
- documents 用另一个 provider
- 或者 query/document 用不同 model space

更准确的约束是：

> query/document 可以走不同的方法入口，但必须落在同一个 provider/model embedding space 里。

### 3.4 为什么 toy provider 先把这种差异显式化

第三章当前的 `LocalKeywordEmbeddingProvider` 会刻意把 query/document 差异显式做出来。

它的作用不是模拟真实模型细节，而是为了让你先看清这层契约：

- query/document 可以不同
- 但它们仍然必须可比较

这是一种教学放大镜。

---

## 4. provider 契约为什么要在第三章就立住 📌

### 4.1 什么叫最小 provider 契约

这一章里最小 provider 契约至少包含：

- `provider_name`
- `model_name`
- `dimensions`
- `embed_query()`
- `embed_documents()`

这个契约的价值在于：

- 你可以换实现
- 但后面的排序逻辑不用跟着改

### 4.2 为什么错误应该尽早失败

第三章有几类错误必须尽早失败，而不是传到第四章以后再爆：

- 返回向量数量不对
- 返回维度不对
- query/document 不在同一 provider/model space

这类错误如果在第三章不拦住，后面就会变成更难排查的“检索效果很怪”。

### 4.3 零向量和空输入怎么理解

第三章还要建立一个很重要的习惯：

- 空输入要有明确边界
- 零向量要有明确处理方式

因为后面相似度、排序、存储都会建立在这些细节之上。

---

## 5. 真实 embeddings endpoint 的桥接 📌

### 5.1 为什么第三章现在还要补真实 provider

如果第三章永远只停留在 toy provider，你会少掉三种现实感知：

1. 真实 embedding model 会有真实维度
2. 真实 endpoint 天然支持批量输入
3. 真实语义空间会补足 toy provider 的语义缺口

所以第三章现在要补的不是“真实调用入门”，而是：

> embedding-specific 的真实接入桥。

### 5.2 为什么这里不再重复 `02_llm/02_multi_provider`

你已经在 `02_llm/02_multi_provider` 学过：

- OpenAI-compatible 平台怎么配
- `api_key / base_url / model` 怎么切
- 为什么要做统一抽象

所以第三章不再重讲这些内容。

第三章只关心：

- 真实 embeddings endpoint 长什么样
- 维度怎样确定
- 批量输入怎样处理
- 为什么仍然要保留 `embed_query / embed_documents` 接口

### 5.3 为什么真实 embeddings 和 chat completions 虽然都走 OpenAI-compatible，但关注点完全不同

这两类接口虽然都可能使用 OpenAI-compatible SDK，但你在工程上关注的东西不同：

| 接口 | 更关心什么 |
|------|------------|
| `chat.completions` | messages、system、temperature、max_tokens |
| `embeddings` | dimensions、batch count、same space、向量稳定性 |

这就是第三章现在最重要的区分。

### 5.4 `embed_query / embed_documents` 在真实 provider 下怎么对应

对很多 OpenAI-compatible embeddings endpoint 来说：

- `embed_query()`
- `embed_documents()`

最终会映射到同一个 embeddings API。

这不代表接口分层没有意义。

恰恰相反，它说明：

> 接口语义和底层 endpoint 可以不是一一对应的。

第三章保留这两个方法，是为了保持语义边界，而不是强行追求“方法一定要调不同 API”。

### 5.5 模型切换时哪些契约必须保持

当你把模型从：

- toy provider
- 切到 OpenAI-compatible embedding model
- 或切到本地 HuggingFace / sentence-transformers

最关键要守住的是：

1. `dimensions` 要明确
2. query/document 要保持同一 space
3. 批量输出数量要和输入一致
4. `EmbeddedChunk` 不能丢失原始 chunk 身份

---

## 6. 第三章实践：独立向量化闭环

### 6.1 目录结构

本章代码目录是：

```text
source/04_rag/03_embeddings/
├── README.md
├── requirements.txt
├── embedding_basics.py
├── 01_embed_chunks.py
├── 02_compare_similarity.py
├── 03_query_vs_document.py
├── 04_real_embeddings.py
├── 05_semantic_search.py
├── data/
│   ├── source_chunks.json
│   └── search_cases.json
└── tests/
```

### 6.2 输入和输出

本章代码的输入是：

- 一组固定样例 `SourceChunk[]`
- 一个 toy provider 或真实 embedding provider
- 一个 query

本章代码的输出是：

- `EmbeddedChunk[]`
- query vector
- document vectors
- similarity scores
- toy vs semantic provider 的桥接现象

在 [embedding_basics.py](../../source/04_rag/03_embeddings/embedding_basics.py) 里，你最值得先看的是：

- `SourceChunk`
- `EmbeddedChunk`
- `EmbeddingProvider`
- `LocalKeywordEmbeddingProvider`
- `OpenAICompatibleEmbeddingProvider`
- `MockSemanticOpenAIClient`
- `demo_source_chunks()`
- `load_search_cases()`
- `embed_chunks()`
- `ensure_vector_dimensions()`
- `ensure_same_embedding_space()`
- `score_query_against_chunks()`

### 6.3 运行方式

```bash
cd source/04_rag/03_embeddings

python -m pip install -r requirements.txt
python 01_embed_chunks.py
python 02_compare_similarity.py
python 03_query_vs_document.py
python 04_real_embeddings.py
python 05_semantic_search.py
python -m unittest discover -s tests
```

### 6.4 你应该观察到什么

跑 [01_embed_chunks.py](../../source/04_rag/03_embeddings/01_embed_chunks.py) 时：

- `chunk_id / document_id / metadata` 被保留下来
- 第三章新增的是 `provider_name / model_name / dimensions / vector`
- `EmbeddedChunk` 看起来像“保留原始 chunk 的增强版”

跑 [02_compare_similarity.py](../../source/04_rag/03_embeddings/02_compare_similarity.py) 时：

- query 会先变成 query vector
- chunk 会先变成 document vectors
- 排序结果仍然保留 chunk 身份
- “如何申请退费？” 应该更接近退款规则 chunk

跑 [03_query_vs_document.py](../../source/04_rag/03_embeddings/03_query_vs_document.py) 时：

- toy provider 下，同一段文本走 query/document 两条路径时，结果可以不同
- 它们不同不代表不可比较
- query/document 的 mode buckets 可以不同
- 但它们仍然属于同一 provider/model 空间

跑 [04_real_embeddings.py](../../source/04_rag/03_embeddings/04_real_embeddings.py) 时：

- 你会看到真实或 mock embeddings endpoint 的 `provider / model / dimensions`
- 你会看到 `embed_query / embed_documents` 仍然保留两个接口
- 你会看到对真实 embeddings 来说，重点已经转成维度、批量和契约

跑 [05_semantic_search.py](../../source/04_rag/03_embeddings/05_semantic_search.py) 时：

- 你会看到一条 toy provider 的已知缺口
- 你会看到 semantic provider 更可能把它排到 metadata chunk
- 这正是第三章补真实 embedding 桥的理由

### 6.5 第三章最小回归集

第三章现在有两层回归样例：

1. [source_chunks.json](../../source/04_rag/03_embeddings/data/source_chunks.json)
2. [search_cases.json](../../source/04_rag/03_embeddings/data/search_cases.json)

其中 `search_cases.json` 里会保留一条明确的桥接坏例：

```json
{
  "question": "为什么文档块要记录出处？",
  "local_expected_top_chunk": "refund:0",
  "semantic_expected_top_chunk": "metadata:0"
}
```

这不是完整评估体系，但已经足够回答：

1. toy provider 的主线还在不在
2. 最小语义排序有没有明显跑偏
3. 真实 embedding adapter 有没有保持契约
4. 已知坏例有没有被明确保留下来

### 6.6 本章代码刻意简化了什么

这一章的实现刻意简化了五件事：

1. toy provider 仍然是本地最小实现
2. 真实 provider 只补 OpenAI-compatible embeddings 桥接
3. 向量比较只做最小 cosine similarity
4. 不写向量数据库
5. 不做复杂模型基准评测

这是故意的。

因为本章要先把下面这件事学会：

> 第三章解决的是“向量怎么来、怎么保持可比较”，不是“向量怎么存、怎么查、怎么维护”。

---

## 7. 本章学完后你应该能回答

- 为什么第三章只增加向量层，而不是重做输入管道
- 为什么 `EmbeddedChunk` 要保留 `SourceChunk`
- 为什么 `embed_query()` 和 `embed_documents()` 不应混成模糊接口
- 为什么 query/document 必须落在同一向量空间里
- 为什么真实 embeddings 和 chat completions 虽然都走 OpenAI-compatible，但关注点完全不同
- 为什么 provider 契约错误应该在第三章就直接失败
- 为什么 toy provider 和真实 provider 要在同一章里形成桥接，而不是互相替代

---

## 8. 下一章

第四章开始，你才会进入向量存储问题：

- 这些向量怎么写进去
- 怎么查 top-k
- 怎么做删除和过滤

也就是说，第四章处理的是“这些向量怎么存、怎么查、怎么维护”。
