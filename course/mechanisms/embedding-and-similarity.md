# Embedding 表示与向量相似度

> 机制篇：理解文本怎样变成可比较的向量，以及相似度分数能说明什么、不能说明什么。
>
> 课程位置：[标准学习路径](../learning-path.md) V0 第十步。必要前置是 [RAG 与外部知识的边界](../concepts/rag-and-external-knowledge.md) 和 [Chunking](chunking-and-metadata.md)；后者已经建立在文档加载之上。本文交付真实 Embedding 调用与成对相似度观察；分数只说明表示空间中的接近程度，不证明事实正确，也不代替后续的匹配、排名与证据判断。

## 第九步已经有 Chunk，为什么还不够

第九步已经把售后规则组织成可回查的 Chunk。例如，Markdown 路径会得到类似下面的检索单元素材：

```text
仅已支付且已完成的订单可申请售后。
虚拟商品不进入售后流程。
售后接口 v2 必须提供 source_channel。
Flutter 客户端必须使用相同的入口可见性规则。
```

如果下一步只做字符串包含或关键词相等，立刻会碰到真实查询：

| 用户说法 | 资料写法 | 纯字符串会怎样 |
| --- | --- | --- |
| “哪些订单可以发起逆向服务？” | “申请售后” | 词面不同，容易漏 |
| “`source_channel` 什么时候必填？” | 整句接口约束 | 可能命中，也可能被同义噪音淹没 |
| “虚拟商品能不能走售后？” | “虚拟商品不进入售后流程” | 可能命中，但“近”不等于“可直接当支持证据” |

这里出现了两类相反的风险：

1. **表示太死**：只认字面，同义改写失败。
2. **表示太漂**：只认“向量很近”，把例外、否定和无关近邻一起抬进来。

第十步要解决的不是“把 Chunk 再切短一点”，而是：

> 文本怎样进入一个可比较的表示空间？得到的分数能说明接近程度，却不能自动证明事实正确或证据充分。

## 简单方案为什么不够

### 只比较字符串

```text
if "申请售后" in chunk_text: ...
```

它确定性高、可解释，但会漏掉“发起逆向服务”“售后入口”“退货申请”等同义或近义表达。需求评审助手面对的是产品和研发的自然语言，不是固定枚举值。

### 只调用一个黑盒“相似度 API”并取最高分

这种做法会把关键工程问题一起藏起来：

- 分数越大越好，还是越小越好？
- 用的是哪个模型、多少维？
- query 和 document 是否同一表示空间？
- 失败时是限流、鉴权，还是端点不存在？
- 高分对里是否包含否定与例外？

需求评审助手需要的是可观察契约：

```text
texts + EmbeddingConfig
→ 真实 Embedding Provider
→ vectors + provider / config / model / dimensions / usage / latency
→ 同一 Embedding 空间下的相似度观察
```

## 向量直觉：先看方向和长度，再谈高维

先暂时把 Embedding 想成只输出两个数。下面的数字不是模型真实语义，也不表示“横轴是售后、纵轴是接口”；它只用来建立比较方向的直觉：

```text
“申请售后”       → [1.0, 0.0]
“发起逆向服务”   → [0.9, 0.1]
“售前活动规则”   → [0.0, 1.0]
```

前两个向量指向接近的方向，第三个方向明显不同。向量的**方向**来自各维度之间的相对关系；向量的**长度**也叫范数，可以先把它理解为从原点到该点的距离。`[1.0, 0.0]` 与 `[2.0, 0.0]` 方向相同、长度不同，这正是后面要区分 cosine 和 dot 的原因。

真实模型输出通常是成百上千维的稠密向量，不能肉眼画图，但阅读时仍沿用这个直觉。先抓住三件事：

1. **比较的是表示，不是原文本身。**  
   Embedding 模型把文本压进一个固定维度的空间。空间结构由训练数据和模型决定，不是业务规则表。
2. **接近不等于同义，更不等于可替换。**  
   “可申请售后”和“不进入售后流程”都在谈售后资格，方向可能接近，业务上却不能互换。
3. **维度是契约的一部分。**  
   1536 维的向量和 1024 维的向量不能直接算距离；换模型通常意味着旧向量失效。

不需要在本篇推导矩阵公式。需要建立的工程直觉是：

```text
文本
→ Embedding 模型
→ 固定长度的浮点数组
→ 只有在兼容的 Provider、配置、模型、维度和预处理空间下才可比较
```

## 三种度量：数值和方向必须一起保存

当前实现支持三种度量：

| 度量 | 直观含义 | `higher_is_closer` | 常见误用 |
| --- | --- | --- | --- |
| cosine | 比较夹角，主要关注方向 | 是 | 把未说明的分数默认当成 cosine |
| dot | 方向和长度共同影响的点积 | 是 | 忽略向量范数差异 |
| euclidean | 两点之间的直线距离 | 否 | 按“越大越好”排序，结果完全反转 |

为什么必须同时保存分数值和方向？因为以后只要用这些数字做比较或排序，方向错了，结果就会整体反转，而且表面上仍然“跑通了”。

**单位化**指把每个向量缩放到长度为 1，不改变方向。完成单位化后，dot 与 cosine 的数值相等；Euclidean 仍是距离而不是相似度，但它给出的远近次序会与 cosine 一致。下面的公式只记录这个关系，不要求手算：

```text
若向量已单位化（长度都为 1）
→ cosine 与 dot 相等（忽略浮点误差）
→ squared Euclidean distance = 2 - 2 × cosine
→ cosine 与 Euclidean 会给出相同的远近次序

若向量未单位化
→ dot 同时受方向和长度影响
→ 向量范数较大的表示会影响点积，不能把它简单归因于原文更长
```

当前 `rag_core.embedding` 按原始返回向量计算，不偷偷做未声明的二次归一化。实验时若切换 `--metric`，应先问“更好”的方向有没有变，而不是只看数字变大还是变小。

更重要的不变量：

```text
高相似 ≠ 事实正确
高相似 ≠ 相关到足以进入模型上下文
高相似 ≠ 足以支撑评审结论
高相似 ≠ 词面命中
```

## 再把表示放回完整检索链

有了“文本先进入同一向量空间、分数还要带方向”的直觉，再固定候选形成链：

```text
query + visible Chunk pool
→ 表示 query 与 Chunk
→ 按规则匹配
→ 产生原生分数和排名
→ 过滤不可见或不合格候选
→ 按需要融合多路排名
→ 返回候选证据
```

这些步骤不能互相冒充：

| 操作 | 回答的问题 | 本篇是否深入 |
| --- | --- | --- |
| 表示 | 文本在什么空间里可比？ | 是 |
| 匹配 | 哪些候选进入比较范围？ | 否，仅概念定位 |
| 原生分数 | 这一对有多近？方向如何读？ | 是，成对观察 |
| 排名 / top-k | 谁排前面？ | 否，留给 Dense Retrieval |
| 过滤 | 旧版本、不可见、不合格是否剔除？ | 否 |
| 融合 | 多路结果如何合并？ | 否 |
| 证据判断 | 候选能否支撑结论？ | 否 |

两条常见表示路线也要先分开：

| 路线 | 表示什么 | 擅长 | 弱项 |
| --- | --- | --- | --- |
| 词面表示 | 词项、字面 | 精确字段名、状态码、接口标识 | 同义改写 |
| 向量表示 | Embedding 空间 | 同义、换说法 | 精确标识、否定与例外 |

相似、相关和“能够支撑结论”不是同一件事。后面即使出现高分候选，也只说明表示空间里更近，不代替上下文选择和生成约束。

## 四个对象承担不同责任

上述心智模型进入代码后，会落成四个对象：

| 对象 | 主要责任 |
| --- | --- |
| `EmbeddingResponse` | `llm_core` 对一次真实 Embedding 调用的统一响应：向量序列、维度、usage、latency、model |
| `EmbeddingRecord` | RAG 侧一条可比较记录：原文、向量、Provider、配置、模型、维度、预处理版本与可选 `text_id` |
| `SimilarityMetric` | cosine / dot / euclidean，以及“越大越近还是越小越近” |
| `SimilarityObservation` | 一对文本的观察结果：分数、方向与本轮 Embedding 空间身份 |

它们不能互相替代：

- `EmbeddingResponse` 回答“这次服务调用返回了什么”。
- `EmbeddingRecord` 回答“哪段业务文本对应哪个向量”。
- `SimilarityObservation` 回答“在同一表示空间里，这两段文本有多近”。

完整位置关系是：

```text
Chunk.text / probe.text / query.text
→ LLMClient.embed
→ EmbeddingResponse
→ EmbeddingRecord[]
→ pairwise_similarity
→ SimilarityObservation[]
```

本篇停在 `SimilarityObservation`：先学会读一对文本的分数。把向量存起来、对一整库候选做匹配和排名，是后话；现在不必提前展开那些机制。

## Embedding 空间一致性是硬约束，不是配置洁癖

向量表示有一个和词面比较很不一样的地方：它依赖一个外部模型定义的空间。

因此至少有四条工程约束：

1. **query 与 document 必须属于同一 Embedding 空间。**
   当前最小身份由 Provider、配置引用、模型名、维度和预处理版本共同表达。
2. **换模型通常要重建。**  
   旧向量属于旧空间；把新旧向量放进同一张相似度表，得到的是不可解释的噪声。
3. **预处理版本也是语义的一部分。**  
   若未来对 Chunk 做了截断、拼接标题前缀或清洗策略变更，仅复用旧向量会让“文本”和“表示”脱节。
4. **Chat 模型不能冒充 Embedding 模型。**  
   Chat 回答问题和 Embedding 生成向量走不同 API、不同配置角色。

当前代码把这些约束落成早失败：

- [`LLMClient.embed`](../../source/packages/llm_core/client/service.py) 要求 `role == "embedding"`。
- [`embed_texts`](../../source/packages/rag_core/embedding/models.py) 为记录保存 `provider`、`config_ref`、`model`、`dimensions` 与 `preprocessing_version`。
- [`pairwise_similarity`](../../source/packages/rag_core/embedding/models.py) 拒绝上述空间身份任一部分不一致的记录。

这比事后看到一个“看起来还行”的错误分数更安全。

当前空间身份仍是应用契约，不是供应商给出的全球唯一模型版本。若同一个 `config_ref` 背后的 endpoint 或模型实现发生不兼容变化，调用方必须升级配置或预处理版本并重建向量，不能仅因名称相同就复用旧记录。

## 公共入口与核心调用链

### `llm_core` 负责真实调用

```python
from llm_core import LLMClient

response = LLMClient.from_default_config().embed(
    ["申请售后", "发起逆向服务"],
    "embedding.default_embed",
)
```

[`LLMClient.embed`](../../source/packages/llm_core/client/service.py) 的关键步骤：

1. 用 `config_ref` 取出配置，确认 `role == "embedding"`。
2. 规范化输入：单字符串变成列表。
3. 拒绝空列表、空字符串或仅空白文本。
4. 调用 [`OpenAICompatProvider.embed`](../../source/packages/llm_core/providers/openai_compat.py)。
5. 通过 `embeddings.create` 访问真实服务。
6. 校验返回条数与输入一致、维度非空且一致。
7. 返回 `EmbeddingResponse`：按输入顺序的向量、维度、usage、latency、model、provider。

Chat 配置不能拿去 embed；Embedding 配置也不能拿去 chat。这是能力守卫，避免请求发出后才遇到难懂的供应商错误。

### `rag_core.embedding` 负责 RAG 侧记录与比较

```python
from rag_core import SimilarityMetric, embed_texts, pairwise_similarity

batch = embed_texts(
    ["申请售后", "发起逆向服务", "售前活动规则"],
    text_ids=["synonym_a", "synonym_b", "noise"],
    preprocessing_version="raw-v1",
)
for item in pairwise_similarity(batch.records, metric=SimilarityMetric.COSINE):
    print(item.left_id, item.right_id, round(item.score, 4))
```

[`embed_texts`](../../source/packages/rag_core/embedding/models.py) 不重新发明 Provider，只是把 `EmbeddingResponse` 整理成带可选 `text_id` 的 `EmbeddingRecord`。  
[`pairwise_similarity`](../../source/packages/rag_core/embedding/models.py) 产出全部无序对观察，并带上 `higher_is_closer`。

这样分工的原因：

| 包 | 该管什么 | 不该管什么 |
| --- | --- | --- |
| `llm_core` | API key、base_url、role、HTTP、usage、供应商错误 | Chunk 身份、业务探针、检索策略 |
| `rag_core.embedding` | 表示记录、成对相似度、Embedding 空间一致性 | 自己再维护一套 Provider 配置 |

### 配置为什么要和 Chat 分开

`models.yaml` 里 Embedding 使用独立环境变量：

```text
OPENAI_EMBEDDING_API_KEY
OPENAI_EMBEDDING_BASE_URL
OPENAI_EMBEDDING_MODEL
```

这不是多余配置。一个常见真实边界是：

```text
Chat：DeepSeek / 其他仅聊天兼容平台
Embedding：需要支持 /embeddings 的平台
```

若把 chat 的 `OPENAI_BASE_URL` 直接拿去 embed，常见结果是 `404`。本仓库选择让 Embedding **默认不继承** chat base URL，逼着配置显式化，而不是静默打到错误端点后再把问题误判成“向量效果差”。

默认配置要求显式提供 `OPENAI_EMBEDDING_API_KEY`，不自动复用 chat 的 `OPENAI_API_KEY`。即使两端都使用 OpenAI，也应显式声明 Embedding 凭证；这样 chat 切换供应商时不会把另一家服务的 key 误发到默认 Embedding endpoint。

### 批量调用不是无限输入

当前公共入口可以一次传入多条文本，但这只表示 Provider API 支持批量输入，不表示调用方可以无限堆积 Chunk：

- 单条文本和整批请求的 Token、条数与载荷限制由真实 Provider 和模型决定。
- 当前实现按调用方提供的列表发起一次请求，不自动拆批，也不静默截断超长文本。
- 超过真实服务限制时应保留 Provider 错误；后续入库链路若需要自动拆批，必须显式记录批次、重试和部分失败，而不是藏在本篇成对观察中。

## 用售后探针理解分数边界

实验探针继续使用“售后入口与订单状态”域，固定几类对照：

| 探针对 | 想观察什么 |
| --- | --- |
| 申请售后 ↔ 发起逆向服务 | 同义改写是否靠近 |
| 已支付可申请 ↔ 虚拟商品除外 | 相关但约束相反时，高分意味着什么 |
| `source_channel` 资料句 ↔ 字段提问 | 精确标识在向量空间里是否足够稳 |
| 申请售后 ↔ 售前活动规则 | 无关噪声是否明显更远 |

这些对照形成四类受控观察：

1. **同义成功**：说明向量表示有价值。  
2. **例外仍近**：说明不能把高分直接当证据。  
3. **精确字段**：提示仅靠向量接近可能不够稳，词面信息仍重要。  
4. **噪声更远**：说明表示空间至少能分开明显无关内容。

真实链路中，第九步的 `Chunk.text` 会成为 `embed_texts` 的输入，用户 query 也会用同一空间表示。这里的规则句来自前面 ingestion fixtures 的 canonical facts，查询改写和噪声句是为隔离表示变量补充的有效业务表达。本篇直接读取探针文本，不重新运行 Loader 或 Chunker；这是为了只观察 Embedding 表示，不是用手写字符串替代后续真实知识库链路。第十二步建立 Dense Retrieval 时，才会把 query 与一组真实 Chunk 一起用于候选匹配和排名。

注意：本篇比较的是探针句子之间的距离，不是“拿一个问题去整库候选里做检索排序”。后者会把匹配、排名和过滤一起卷进来，超出本篇要观察的变化。

## 运行实验时先预测，再看分数

共享实验位于 [`rag_retrieval_lab`](../../source/demos/rag_retrieval_lab/)。

```bash
uv run python source/demos/rag_retrieval_lab/inspect_embedding.py
```

运行前先写下预测：

1. “申请售后”和“发起逆向服务”会不会明显高于无关售前规则？
2. “已支付可申请”和“虚拟商品除外”会不会仍然较高？若较高，你的产品结论应该是什么？
3. 带 `source_channel` 的资料句和字段提问，分数能证明什么、不能证明什么？
4. 换用 `--metric euclidean` 后，数值变了，远近关系应如何阅读？
5. 若 chat 已配置 DeepSeek，而 `OPENAI_EMBEDDING_API_KEY` 未配置，你预期错误发生在调用链哪一层？

默认输出展示：

- Provider、模型、维度、预处理版本、latency、usage
- 探针及其分组
- focus pairs 的分数与预期说明

使用 `--verbose` 可查看全部成对分数。完整参数、JSON Lines 和读码顺序由 [demo README](../../source/demos/rag_retrieval_lab/README.md) 维护。

解读时遵守：

```text
这些是表示空间观察
≠ 检索已经做对
≠ 某策略已经适合上线
≠ 可以忽略词面信息
```

如果同义对很高、噪声对很低，只说明当前模型在这组受控句子上区分了大方向。  
如果例外对也很高，不要立刻改模型；先承认这是向量表示的自然边界——接近主题不等于可替换约束。后面还要用匹配范围、过滤、上下文选择和证据规则来补齐，而不是要求 Embedding“理解业务法条”。

## 将自然边界、输入错误和真实服务故障分开

主路径缺少密钥、鉴权失败、限流、超时、404 端点或供应商异常时，应看到清晰的 `LLMError`，而不是空向量或本地假分数。

建议按调用链定位：

| 现象 | 优先检查 |
| --- | --- |
| `INPUT_VALIDATION` | 是否传入空列表、空字符串或仅空白文本；请求尚未到 Provider |
| `AUTH` | `OPENAI_EMBEDDING_API_KEY` 是否配置、是否属于当前 Embedding 服务、供应商权限 |
| `404` / `PROVIDER_ERROR` | 是否把仅聊天平台的 base URL 当成 Embedding 地址；Embedding 模型名是否存在 |
| `RATE_LIMIT` / `TIMEOUT` | 限流、网络、是否应在外层重试 |
| `CAPABILITY_MISMATCH` | 是否误把 chat 配置传给 embed |
| Embedding 空间不一致 | Provider、配置、模型、维度或预处理版本是否混用 |
| 语义很近但约束相反 | 表示边界，不是程序异常 |

一个应被当作教学边界而不是“修好就消失”的例子：

```text
表现：已支付规则 与 虚拟商品例外 的 cosine 仍然较高
原因假设：二者都在描述售后资格，表示空间抓住了主题接近
验证：查看 focus pair；确认文本确实表达相反约束
处理：承认表示边界；后续用词面信息、过滤、上下文选择和证据判断补齐，而不是要求 Embedding“理解法律逻辑”
```

前三类服务错误用于验证真实异常流；输入校验和空间不一致由确定性测试固化；“语义很近但约束相反”是有效业务输入产生的表示边界。它们承担不同证据责任，不需要在每次学习时全部主动触发。

Mock 只用于单元测试中的批量顺序、输入校验、返回契约、空间一致性和错误映射，不能作为真实 Embedding 效果的主要证据。

## Provider 封装了什么，没有解决什么

OpenAI-compatible Embedding API 封装了：

- 鉴权与 HTTP 传输
- 文本批量转向量
- 基本 usage 与模型回传

它没有替应用解决：

- query 与 document 是否属于兼容的 Provider、配置、模型、维度和预处理空间
- 分数方向如何解释和保存
- 向量如何绑定 Chunk 身份，并在文档更新后重建
- 何时应更多依赖词面信息，或合并多路结果
- 高分候选能否进入模型上下文并支撑结论
- chat 兼容平台是否真的提供 Embedding 端点

框架只提供表示能力。应用仍要建立契约、诊断和产品边界。

## 本节交付与边界

本节真实交付：

```text
texts + EmbeddingConfig
→ EmbeddingResponse
→ EmbeddingRecord[]
→ SimilarityObservation[]
```

读完应能独立说明：文本如何变成向量，一对分数如何阅读，以及高相似为什么仍可能不能当证据。

本文不声称：

- 某个相似度阈值是全局正确答案
- 完成了“对知识库做检索并选出候选”的整条链路
- 高相似句子可以直接作为评审证据
- 受控探针能代表全部生产查询分布
- 所有 chat 兼容平台都提供可用 Embedding

## 判断是否已经掌握

1. 为什么第九步的 Chunk 仍不能直接解决同义改写问题？
2. 表示、匹配、排名、过滤和融合分别处于检索链的哪一段？本篇停在哪里？
3. `EmbeddingResponse`、`EmbeddingRecord` 和 `SimilarityObservation` 的责任有何不同？
4. cosine 与 euclidean 的“更好”方向有什么不同？为什么必须保存 `higher_is_closer`？
5. 为什么高相似不能等同于“能支撑结论”？用售后例外对解释一次。
6. `LLMClient.embed` 为什么拒绝 chat 配置和空文本？
7. 哪些字段共同表达当前最小 Embedding 空间？任一字段变化后旧向量应怎样处理？
8. 为什么 Embedding 配置不应默认继承 chat 的 `OPENAI_BASE_URL` 和 `OPENAI_API_KEY`？
9. `llm_core` 与 `rag_core.embedding` 的分工是什么？若在 `rag_core` 再写一套 Provider 会有什么问题？
10. 运行 focus pairs 后，你能否解释同义对、例外对、精确字段对和噪声对各自说明了什么？

完成后回到 [标准学习路径](../learning-path.md)，由唯一课表决定后续内容。
