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
- 最小排序与回归边界：30-40 分钟
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
- [tests/test_embeddings.py](../../source/04_rag/03_embeddings/tests/test_embeddings.py)

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

这里故意只保留：

- 一组固定样例 `SourceChunk[]`
- 一个 toy provider
- 一个 OpenAI-compatible embeddings provider
- 一个最小 cosine similarity 排序
- 一组显式保留的坏例和契约失败样本

目的不是追求“模型覆盖最多”，而是先把向量层主线讲清楚。

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

### 2.5 第三章的运行时主链路

这一章最值得先建立手感的，不是某个模型名，而是一条完整的运行时链路：

```text
SourceChunk
-> provider.embed_documents()
-> EmbeddedChunk
-> provider.embed_query()
-> cosine_similarity()
-> ranked results
```

如果你能把这条链路讲清楚，第三章的大部分内容就已经真正掌握了。

### 2.6 为什么第三章交付的是“稳定向量层”

很多学习资料会把第三章讲成：

- 调一下 embeddings API
- 拿回一组浮点数
- 结束

这种讲法不够。

更准确的说法是：

> 第三章在定义后续章节要消费的标准向量接口。

后面的向量存储、检索过滤、删除和评估，默认都要建立在这里的输出之上。

所以这里的重点不是“先拿到一组向量”，而是：

- 向量维度要稳定
- chunk 身份不能丢
- provider/model space 要显式
- query/document 要能稳定比较
- 错误要能尽早失败

### 2.7 向量化不负责什么

向量化负责的是：

- 把文本映射成可比较表示
- 保留 chunk 身份
- 给排序和存储提供稳定契约

向量化不负责：

- top-k 存储结构怎么设计
- metadata 过滤怎么执行
- rerank 怎么补精排
- 最终回答怎么生成

它的职责是“让 chunk 可比较”，不是“替整个 RAG 做决定”。

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

### 3.5 `LocalKeywordEmbeddingProvider` 在教学上到底放大了什么

这个 toy provider 不是“随便写个假向量”。

它刻意保留了三层信号：

1. `CONCEPT_GROUPS`
   - 把退款、试学、metadata、stable id、embedding、similarity 这些概念组显式暴露出来
2. `HASH_BUCKETS`
   - 让不在概念组里的 token 也有最小分布能力
3. `MODE_BUCKETS`
   - 用尾部两个 bucket 把 query/document 路径差异显式写进向量

所以它真正要教你的不是“怎样造假向量”，而是：

> 向量空间的比较性，依赖共享语义基底和一致契约，而不是依赖接口长得一样。

### 3.6 同一段文本为什么走 query/document 两条路径还能比较

在 `03_query_vs_document.py` 里，同一段文本会分别走：

- `embed_query(text)`
- `embed_documents([text])`

结果会不同，但不会完全失去可比性。

这是因为：

- 共享概念组还在
- 共享 hash buckets 还在
- 只是在 mode buckets 上刻意留出角色差异

它想让你建立的直觉是：

> “不完全相同” 和 “不可比较” 不是一回事。

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

### 4.2 第三章最值得先看的运行时对象

在 [embedding_basics.py](../../source/04_rag/03_embeddings/embedding_basics.py) 里，最值得先建立手感的不是“函数很多”，而是对象已经很清楚。

你可以先把这些对象看成第三章向量层的运行时骨架：

| 对象 | 作用 |
|------|------|
| `SourceChunk` | 第二章留下来的标准 chunk 输入 |
| `EmbeddedChunk` | 保留 chunk 身份的向量增强对象 |
| `EmbeddingProvider` | query/document 向量化的最小契约 |
| `LocalKeywordEmbeddingProvider` | 把 query/document 差异显式做出来的 toy provider |
| `OpenAICompatibleEmbeddingProvider` | 第三章真实 embeddings endpoint 的最小桥接实现 |
| `MockSemanticOpenAIClient` | 没配真实环境变量时的语义桥接替身 |
| `MockEmbeddingResponse` | 模拟真实 embeddings 响应形状的最小对象 |

这和第二章先看 `DocumentCandidate / LoadedDocument / SourceChunk` 是同一类学习方式：

> 先看清运行时对象，再看函数如何把它们串起来。

### 4.3 `embed_chunks()` 和 `score_query_against_chunks()` 到底在做什么

很多人第一次看第三章时，只会注意“拿到了向量”。

但真正要看的其实是两条收束函数：

`embed_chunks()` 在做：

```text
SourceChunk[] -> provider.embed_documents() -> EmbeddedChunk[]
```

`score_query_against_chunks()` 在做：

```text
question -> provider.embed_query() -> cosine_similarity(query, chunk.vector) -> ranking
```

也就是说，第三章真正交付的不是“一个 embeddings demo”，而是：

> 一组稳定的 document vectors，加上一套稳定的 query-vs-document 比较方式。

### 4.4 为什么错误应该尽早失败

第三章有几类错误必须尽早失败，而不是传到第四章以后再爆：

- 返回向量数量不对
- 返回维度不对
- query/document 不在同一 provider/model space

这类错误如果在第三章不拦住，后面就会变成更难排查的“检索效果很怪”。

### 4.5 `ensure_vector_dimensions()` 在保什么

这一层很多人会低估。

如果一个 provider 声称自己是固定维度空间，但返回的向量长度时长时短，后面的排序和存储都不成立。

`ensure_vector_dimensions()` 的作用就是把这种漂移尽早拦住。

它不是“额外的防御性代码”，而是在保护：

- 当前 provider 的维度承诺
- 当前模型空间的稳定性
- 后续 cosine similarity 和向量存储的前提

### 4.6 `ensure_same_embedding_space()` 在保什么

这个函数最重要的作用不是比较浮点数，而是比较身份：

- `provider_name`
- `model_name`
- `dimensions`

也就是说，它在防止的不是“相似度计算报错”而已，而是：

> 你以为自己在比较 query 和 chunk，实际上却把两个不同空间的向量混在了一起。

### 4.7 零向量和空输入怎么理解

第三章还要建立一个很重要的习惯：

- 空输入要有明确边界
- 零向量要有明确处理方式

当前代码里：

- `embed_chunks([])` 会直接返回空列表
- `score_query_against_chunks(..., [])` 会直接返回空列表
- `cosine_similarity()` 遇到零向量时会返回 `0.0`

因为后面相似度、排序、存储都会建立在这些细节之上。

---

## 5. 语义排序与最小回归的治理锚点 📌

### 5.1 为什么第三章就要开始有回归视角

很多人会以为“回归和评估”要等到完整 RAG 才开始。

其实第三章就已经需要最小回归了，因为这里已经有三类会漂移的东西：

- chunk 资产本身
- provider 契约
- 排序结果

如果这里不先锁住，第四章以后你会很难判断：

- 是存储层有问题
- 是检索层有问题
- 还是第三章的向量空间已经悄悄变了

### 5.2 第三章最重要的治理锚点是什么

这一章里最值得先立住的锚点至少有四个：

1. `chunk_id / document_id`
2. `provider_name / model_name / dimensions`
3. `data/source_chunks.json`
4. `data/search_cases.json`

它们共同回答的是：

- 当前是谁的向量
- 当前属于哪个空间
- 当前排序是在拿什么资产做比较
- 当前已知坏例有没有被明确保留

### 5.3 `source_chunks.json` 在锁什么

`source_chunks.json` 锁住的是本章统一 chunk 资产。

它不是完整的知识库，而是第三章最小可重复输入集。

它的价值在于：

- 所有 demo 脚本都在消费同一批 chunk
- `EmbeddedChunk` 的来源稳定
- 你能把“向量漂移”和“样例内容变化”区分开

### 5.4 `search_cases.json` 在锁什么

`search_cases.json` 锁住的不是“真实世界最优检索结果”，而是当前课程主线下最小可观测行为。

它至少在锁四类现象：

1. local provider 的默认排序结果
2. 一条显式保留的 known gap
3. semantic provider 对这条 known gap 的修正方向
4. 第三章桥接层仍然成立

### 5.5 为什么要故意保留 known gap

第三章里有一条非常重要的坏例：

```json
{
  "question": "为什么文档块要记录出处？",
  "local_expected_top_chunk": "refund:0",
  "semantic_expected_top_chunk": "metadata:0"
}
```

这条样本的价值不在于“证明 toy provider 不够强”，而在于：

> 它明确告诉你，toy provider 和 semantic provider 在第三章是桥接关系，不是互相替代关系。

如果把这类坏例删掉，第三章就会变成“只保留能说明自己正确的样例”，教学价值反而下降。

### 5.6 如果第三章不把这些锚点立住，后面会发生什么

如果这些锚点没有先立住，后面很快会出现问题：

- 你不知道一条向量到底是哪个 chunk 的
- 你不知道不同 provider 的结果是不是混在了一起
- 你不知道排序变化来自模型切换还是样例漂移
- 你不知道 known gap 是被修正了，还是被悄悄删掉了

所以第三章的“治理视角”不是企业级平台治理，而是：

> 先把向量层最小不变量立住。

---

## 6. 真实 embeddings endpoint 的桥接 📌

### 6.1 为什么第三章现在还要补真实 provider

如果第三章永远只停留在 toy provider，你会少掉三种现实感知：

1. 真实 embedding model 会有真实维度
2. 真实 endpoint 天然支持批量输入
3. 真实语义空间会补足 toy provider 的语义缺口

所以第三章现在要补的不是“真实调用入门”，而是：

> embedding-specific 的真实接入桥。

### 6.2 为什么这里不再重复 `02_llm/02_multi_provider`

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

### 6.3 为什么真实 embeddings 和 chat completions 虽然都走 OpenAI-compatible，但关注点完全不同

这两类接口虽然都可能使用 OpenAI-compatible SDK，但你在工程上关注的东西不同：

| 接口 | 更关心什么 |
|------|------------|
| `chat.completions` | messages、system、temperature、max_tokens |
| `embeddings` | dimensions、batch count、same space、向量稳定性 |

这就是第三章现在最重要的区分。

### 6.4 `embed_query / embed_documents` 在真实 provider 下怎么对应

对很多 OpenAI-compatible embeddings endpoint 来说：

- `embed_query()`
- `embed_documents()`

最终会映射到同一个 embeddings API。

这不代表接口分层没有意义。

恰恰相反，它说明：

> 接口语义和底层 endpoint 可以不是一一对应的。

第三章保留这两个方法，是为了保持语义边界，而不是强行追求“方法一定要调不同 API”。

### 6.5 `OpenAICompatibleEmbeddingProvider` 真正在补什么能力

这个 provider 在第三章里真正补的是四类能力：

1. 从环境变量或显式参数构造真实 provider
2. 统一处理批量输入
3. 记录并校验返回维度
4. 在没配置真实环境时回退到 `MockSemanticOpenAIClient`

所以它不是“完整生产封装”，而是：

> 一个足够真实、但仍然围绕教学主线收敛的 embeddings bridge。

### 6.6 模型切换时哪些契约必须保持

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

## 7. 第三章实践：独立向量化闭环

### 7.1 目录结构

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
    └── test_embeddings.py
```

### 7.2 输入和输出

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

### 7.3 本章最值得先看的对象和函数

在 [embedding_basics.py](../../source/04_rag/03_embeddings/embedding_basics.py) 里，你最值得先看的是：

- `SourceChunk`
- `EmbeddedChunk`
- `EmbeddingProvider`
- `LocalKeywordEmbeddingProvider`
- `OpenAICompatibleEmbeddingProvider`
- `MockSemanticOpenAIClient`
- `demo_source_chunks()`
- `load_search_cases()`
- `build_openai_provider_or_mock()`
- `embed_chunks()`
- `ensure_vector_dimensions()`
- `ensure_same_embedding_space()`
- `score_query_against_chunks()`
- `cosine_similarity()`

### 7.4 运行方式

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

### 7.5 先跑哪个

建议先跑：

```bash
python 01_embed_chunks.py
```

你最先要建立的直觉是：

- `EmbeddedChunk` 不是替代 `SourceChunk`
- 第三章先讲向量契约，再讲真实 endpoint
- 真实 embeddings 接入不是为了替换 toy provider，而是为了补桥接层

### 7.6 `01_embed_chunks.py` 在看什么

跑 [01_embed_chunks.py](../../source/04_rag/03_embeddings/01_embed_chunks.py) 时：

- `chunk_id / document_id / metadata` 被保留下来
- 第三章新增的是 `provider_name / model_name / dimensions / vector`
- `EmbeddedChunk` 看起来像“保留原始 chunk 的增强版”

这一节真正要看的不是“打印了几个浮点数”，而是：

- 哪些字段是第二章继承来的
- 哪些字段是第三章新增的
- 为什么第三章的输出已经可以直接为第四章做准备

### 7.7 `02_compare_similarity.py` 在看什么

跑 [02_compare_similarity.py](../../source/04_rag/03_embeddings/02_compare_similarity.py) 时：

- query 会先变成 query vector
- chunk 会先变成 document vectors
- 排序结果仍然保留 chunk 身份
- “如何申请退费？” 应该更接近退款规则 chunk

这里最该建立的直觉不是“相似度分数是多少”，而是：

> 第三章的排序是拿 query vector 和 document vectors 做比较，而不是直接拿原文字符串做比较。

### 7.8 `03_query_vs_document.py` 在看什么

跑 [03_query_vs_document.py](../../source/04_rag/03_embeddings/03_query_vs_document.py) 时：

- toy provider 下，同一段文本走 query/document 两条路径时，结果可以不同
- 它们不同不代表不可比较
- query/document 的 mode buckets 可以不同
- 但它们仍然属于同一 provider/model 空间

### 7.9 `04_real_embeddings.py` 在看什么

跑 [04_real_embeddings.py](../../source/04_rag/03_embeddings/04_real_embeddings.py) 时：

- 你会看到真实或 mock embeddings endpoint 的 `provider / model / dimensions`
- 你会看到 `embed_query / embed_documents` 仍然保留两个接口
- 你会看到对真实 embeddings 来说，重点已经转成维度、批量和契约
- 你会看到没配环境变量时会自动回退到 mock semantic client

### 7.10 `05_semantic_search.py` 在看什么

跑 [05_semantic_search.py](../../source/04_rag/03_embeddings/05_semantic_search.py) 时：

- 你会看到一条 toy provider 的已知缺口
- 你会看到 semantic provider 更可能把它排到 metadata chunk
- 你会看到桥接案例不是为了否定 toy provider，而是为了说明真实语义空间的增量价值

### 7.11 `tests/test_embeddings.py` 在锁定什么

测试会锁定第三章最重要的几件事：

1. demo chunks 仍然保留第二章风格的 metadata
2. toy provider 维度固定
3. query/document 两条路径在 toy provider 下不同但可比较
4. `EmbeddedChunk` 保留原始 chunk 身份
5. local search cases 仍然稳定
6. semantic provider 能修正显式保留的 known gap
7. fake client 能走通 OpenAI-compatible provider
8. 错误响应形态、错误数量、维度漂移会直接失败
9. 空输入和零向量边界有明确行为

### 7.12 第三章最小回归集

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

### 7.13 本章代码刻意简化了什么

这一章的实现刻意简化了五件事：

1. toy provider 仍然是本地最小实现
2. 真实 provider 只补 OpenAI-compatible embeddings 桥接
3. 向量比较只做最小 cosine similarity
4. 不写向量数据库
5. 不做复杂模型基准评测

这是故意的。

因为本章要先把下面这件事学会：

> 第三章解决的是“向量怎么来、怎么保持可比较”，不是“向量怎么存、怎么查、怎么维护”。

### 7.14 第三章最值得刻意观察的失败案例

第三章至少要刻意看四类失败：

1. provider 契约失败
   - 向量数量和输入数量不匹配
   - 响应形状不符合预期

2. 维度漂移失败
   - query vector 维度不对
   - document vectors 前后维度不一致

3. 向量空间混用失败
   - query 和 document 向量不是同一个 provider/model 空间

4. toy provider 语义缺口
   - `为什么文档块要记录出处？` 在 local provider 下会先命中错误 chunk
   - 这不是 bug 修完就结束，而是第三章真实 embedding 桥接存在的理由

这些失败案例很重要，因为它们会帮你分清：

- 哪些是章节边界
- 哪些是向量层不变量
- 哪些变化会直接影响后续章节

### 7.15 建议你主动改的地方

如果你想把第三章真正学扎实，建议主动改三类地方再跑一遍：

1. 修改 `CONCEPT_GROUPS` 或 `STOPWORDS`，观察 local provider 排序如何变化
2. 改一个 `search_cases.json` 样例问题，观察 local/semantic top result 如何变化
3. 故意制造一个维度或 provider 空间不一致的 provider，观察测试如何直接失败

这样你会真正把“chunk 资产、provider 契约、排序结果、桥接坏例”连在一起。

---

## 8. 本章学完后你应该能回答

- 为什么第三章只增加向量层，而不是重做输入管道
- 为什么 `EmbeddedChunk` 要保留 `SourceChunk`
- 为什么 `embed_query()` 和 `embed_documents()` 不应混成模糊接口
- 为什么 query/document 必须落在同一向量空间里
- 为什么真实 embeddings 和 chat completions 虽然都走 OpenAI-compatible，但关注点完全不同
- 为什么 provider 契约错误应该在第三章就直接失败
- 为什么第三章就要开始有最小回归和 known gap 视角
- 为什么 toy provider 和真实 provider 要在同一章里形成桥接，而不是互相替代

---

## 9. 下一章

第四章开始，你才会进入向量存储问题：

- 这些向量怎么写进去
- 怎么查 top-k
- 怎么做删除和过滤

也就是说，第四章处理的是“这些向量怎么存、怎么查、怎么维护”。
