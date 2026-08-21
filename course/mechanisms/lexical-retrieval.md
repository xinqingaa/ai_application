# Lexical Retrieval、BM25 边界与 PostgreSQL 全文检索

> 机制篇：第 8–9 步已经把资料切成带稳定身份的 Chunk，第 10 步观察过句子在向量空间里近不近。本节第一次回答：用户一句话过来，怎样从这批 Chunk 里按**词**找出候选。
>
> 课程位置：[标准学习路径](../learning-path.md) V0 第十一步。本文交付词面匹配、排序和可诊断的 lexical 候选；不实现向量检索、RRF、Context 或 Citation 校验。安装、写入和运行命令由 [产品 README](../../review_assistant/README.md#postgresql-本地准备) 与 [lab README](../../source/demos/rag_retrieval_lab/README.md#步骤-11postgresql-fts-lexical-retrieval) 维护。

第 8–9 步已经有可回查的 Chunk。本节的机制是：

> 把资料和问题拆成词，看有没有相同的词或相同的字段名；有共同词的 Chunk 才能进候选，再在候选里排序。

这叫 lexical retrieval，直观说法就是**按词查找**。它能命中 `source_channel` 这种原样出现的标识，也能命中「申请售后」这种两边都写了的词。它不会因为「逆向服务」和「申请售后」意思接近就自动命中——那是后续 Dense Retrieval 要观察的机制，不是本节的任务。

读完后，你应该能够：

- 用售后例子说明：查询拆成哪些词、哪些词被丢掉、字段名怎样保住。
- 区分切开的碎片、应用决定留下的词、数据库最终收下的词。
- 说明匹配、排序和证据判断分别回答什么问题。
- 解释 PostgreSQL 词袋、查询条件、`@@` 和 `ts_rank` 各自做什么，以及为什么 `ts_rank` 不能叫 BM25。
- 把「查询成功但 0 条」和「数据库执行失败」分成两类结果。

要在真实 PostgreSQL 上观察这些机制，按 [lab README 步骤 11](../../source/demos/rag_retrieval_lab/README.md#步骤-11postgresql-fts-lexical-retrieval) 运行实验。阅读本文不要求先通过数据库测验；实验失败时再去产品 README 或 [PostgreSQL 零基础](../concepts/postgresql-for-ai-applications.md)。

## 先看两个 Chunk，按词会发生什么

假设知识库里有：

```text
A：售后接口 v2 必须提供 source_channel。
B：仅已支付且已完成的订单可申请售后。
```

用户问：

```text
source_channel 什么时候必填？
```

普通数据库当然可以保存 A 和 B。「保存下来」并没有自动回答：查询该拆成哪些词、「什么时候」有没有检索价值、`source_channel` 会不会被拆碎、谁进候选、谁排前面。按词查找要显式做这些决定。

### 查询先被拆成有用的词

人说话时会带填充词。当前策略把问句里的「什么」「时候」丢掉，因为它们几乎出现在所有问法里，帮不上「找哪一条规则」。

留下的检索词大致是：

```text
source_channel
必填
```

资料 A 写的是「必须提供」，不是「必填」。按词找时，**「必填」对不上「必须提供」**。两边意思接近，但词面不同，这一节就当它们不是同一个检索单位。

### 字段名要当成一整块，并做一个备份词

`source_channel` 是接口字段名，应当整块保留。如果后面的数据库按标点或下划线把它拆成 `source` 和 `channel`，这两个词太普通，检索会飘。

所以应用在留下 `source_channel` 的同时，再做一个不含下划线的备份词：去掉符号，前面加上 `techid`。

```text
source_channel  →  sourcechannel  →  techidsourcechannel
```

`techidsourcechannel` 不是知识库里另写的一句话，而是从 `source_channel` 派生的稳定标识。资料和查询只要经过同一套规则，两边都会有这张「身份证」。Chunk A 因此同时带有：

```text
source_channel
techidsourcechannel
售后 / 接口 / v2 / 必须 / 提供
```

查询侧同样会为 `source_channel` 生成备份词。真正把 A 拉进候选的，通常是这个字段名及其备份，不是「必填」理解了「必须提供」。

### 没有共同词，就可以是 0 条

若用户改问「发起逆向服务」，资料写的是「申请售后」，两边拆完可能对不上同一个词。按词查找可以合法返回 0 条。这不是数据库坏了，而是当前机制只认词面。数据库连接或 SQL 真正失败时，代码必须返回明确错误，不能装成 0 条候选。

### 三件不要混在一起

```text
匹配：谁有资格进名单
排序：名单里谁更靠前
证据：这段文字能不能支持最终风险结论
```

A 因字段名进了名单，只说明词面对上了。它排第一，也不等于已经证明需求缺了 `source_channel` 就违规——那要等上下文、生成和后续校验。

## 资料和问题必须用同一套拆词

如果资料把「售后」切成一个词，查询却切成别的碎片，共同词就对不上。所以文档和查询走同一套规则：先规范化（全角/半角、大小写），再切中文、保留技术标识、丢掉填充词。

同一段文字会经过三个车间。名字不同，是为了排查时看清卡在哪一层：

| 人话 | 常见叫法 | 这个查询里 |
| --- | --- | --- |
| 刚切开的碎片，还没决定去留 | token | 「什么时候」、`source_channel`、「必填」 |
| 应用决定留下、必要时补上备份的检索词 | term | `source_channel`、`techidsourcechannel`、「必填」；「什么」「时候」已被丢掉 |
| 数据库最终写入词袋或查询条件的词 | lexeme | 常常长得和 term 一样，例如 `'techidsourcechannel'` |

中文没有天然空格，PostgreSQL 默认不一定按「售后」「虚拟商品」这种业务词来切。本项目先在 Python 里切好，再交给 PostgreSQL 的 `simple` 配方：几乎原样收下已经用空格排开的词，不做英语那种 `running → run` 的词形还原。这是当前可解释的工程取舍，不是中文检索的唯一答案。

## 倒排：从「词找到哪些 Chunk」

若每次查询都把全部 Chunk 扫一遍，数据变大后会越来越慢。倒排把方向反过来，先记「某个词出现在哪些 Chunk」：

```text
售后                  → Chunk A, Chunk B
techidsourcechannel   → Chunk A
必填                  → （没有文档用这个词）
```

查询带着 `source_channel` / `techidsourcechannel` / 「必填」到来时，先按这些词取出较小的集合。默认 OR：三个词有一个对上就进候选，A 能进。若改成 AND：三个词都必须出现；资料没有「必填」，A 可能被扔掉。

PostgreSQL 里，加快「按词找行」的索引叫 **GIN**。它加速符合形态的词面匹配，不定义查询该用 AND 还是 OR，不产生更正确的业务排序，也不理解同义词和否定。

## 刚才那件事，实现上叫什么

下面不是另一套机制，只是把第 2–4 节已经发生的事标上代码和数据库里的名字。

资料侧：

```text
Chunk 原文
→ 应用拆词
→ lexical_text（空格分开的检索词）
   + lexical_config_ref（用的是哪套拆词规则）
→ PostgreSQL 收成 search_vector（类型是 tsvector，一篇文档的词袋）
→ GIN 倒排索引加快按词找行
```

查询侧：

```text
用户问句
→ 同一套应用拆词
→ websearch query（词之间是「有一个就算」还是「必须全有」）
→ PostgreSQL 编译成 tsquery（查询条件）
→ search_vector @@ tsquery（是否匹配，答案只有是或否）
→ ts_rank 在已匹配的行里排序
→ LexicalHit[] + LexicalDiagnostics
```

对照：

| 刚才的人话 | 实现名 |
| --- | --- |
| 拆好的检索词串 | `lexical_text` |
| 哪套拆词规则 | `lexical_config_ref` |
| 这篇文档有哪些词 | `search_vector` / `tsvector` |
| 查询条件 | `tsquery` |
| 满不满足 | `@@` |
| 候选之间谁靠前 | `ts_rank`（结果字段 `fts_rank`） |

表 `review_assistant.rag_chunks` 里，`content` 仍是给人看的原文；`lexical_text` 是应用拆好的词；`search_vector` 是数据库词袋。三列同时存在，是因为原文不能从词袋反推，词袋也不能替代来源位置。

数据库负责可靠存储、按已有词匹配和排序。应用仍负责 Chunk 身份、怎样拆词、AND 还是 OR、参数绑定，以及失败时不能把连接错误说成「没有候选」。

本节使用 PostgreSQL 内置全文检索，不需要额外 Extension。写入走参数化 upsert，一组 Chunk 要么整批提交，要么整批回滚。

## 从原文到数据库里的词袋

### `tsvector` 不是 Embedding vector

名字里都有 vector，保存的东西完全不同：

| 对象 | 保存什么 | 主要比较方式 |
| --- | --- | --- |
| `tsvector` | 词、位置和权重 | 词是否匹配 `tsquery` |
| Embedding vector | 一串浮点数 | cosine、inner product、L2 等 |

`tsvector` 看起来可能像：

```text
'source':3 'channel':4 '售后':1 '接口':2
```

它不是原文，也不是第 10 步那种语义向量。原文继续在 `content` 里。

### 为什么先写成 `lexical_text` 再生成词袋

PostgreSQL 自己也能切词，但中文业务词边界不稳定，`source_channel` 还可能被拆开。当前路径是：

```text
原文
→ Unicode NFKC + casefold
→ jieba 搜索模式（HMM=False）
→ 过滤少量问句填充词
→ 为技术标识增加备份词
→ 空格分隔 lexical_text
→ to_tsvector('pg_catalog.simple', lexical_text)
```

这不是语言真理：jieba 词典会变；别的业务里「什么时候」可能有信息量；备份词提高字段稳定性，也增加词的数量。V0 要的是一条可解释、可版本化、安装成本可控的词面基线。

### 拆词规则也是索引空间身份

向量模型变了要重建向量；拆词规则变了，已经写入的词袋同样不能和新查询混用。

[`LexicalConfig`](../../source/packages/rag_core/lexical/models.py) 的身份包含名称、版本、PostgreSQL text search config、领域词、停用词，以及由这些字段算出的 fingerprint，形成：

```text
jieba_search_simple@1.0.0:<fingerprint>
```

文档行和查询必须带同一 `lexical_config_ref`。代码会过滤不兼容行，而不是把新查询静默打到旧词上。策略改了却「突然没有结果」，应先检查身份并重新写入，而不是先怪数据库或降低阈值。

AND / OR 只改变已有词怎样组成查询，不改变文档和查询的共同词空间，因此进独立的 `retriever_config_ref`。切换 operator 要记录 Retriever 配置，不必重建文档词袋。

### 生成列让词袋跟着 `lexical_text` 走

migration 中的定义是：

```sql
search_vector TSVECTOR GENERATED ALWAYS AS (
    to_tsvector('pg_catalog.simple', lexical_text)
) STORED
```

应用写 `lexical_text`；PostgreSQL 计算 `search_vector`；更新词串时自动重算；应用不能直接改生成列。配方显式写成 `pg_catalog.simple`，不依赖会变化的会话默认值。文档端和查询端若预处理不同，即使都叫 `simple` 也可能对不上。数据库只执行拿到的词，不能替应用发现版本混用。

## 查询条件怎样决定谁进名单

文档端：

```sql
to_tsvector('pg_catalog.simple', lexical_text)
```

查询端：

```sql
websearch_to_tsquery('pg_catalog.simple', websearch_query)
```

匹配：

```sql
search_vector @@ ts_query
```

`@@` 只回答是或否，不回答谁更相关。

查询词仍是：

```text
source_channel / techidsourcechannel / 必填
```

AND 要求全部出现：

```text
source_channel & techidsourcechannel & 必填
```

资料写「必须提供」而不是「必填」时，AND 可能扔掉本来有用的接口规则。

OR 允许任一词命中：

```text
source_channel | techidsourcechannel | 必填
```

它提高召回，也可能放进只沾上通用词的噪声。当前实验默认 OR，作为召回型词面基线，并可用 `--query-operator and` 做对照。这不是永久认定 OR 更好；operator、词项、`candidate_k` 和后续阈值都属于 Retriever 配置。

[`PostgresFTSRetriever.search`](../../source/packages/rag_core/retrieval/postgres_fts.py) 的核心 SQL 可以简化为：

```sql
WITH query_input AS (
    SELECT websearch_to_tsquery(
        %(postgres_config)s::regconfig,
        %(websearch_query)s
    ) AS ts_query
)
SELECT
    chunk.chunk_id,
    ts_rank(chunk.search_vector, query_input.ts_query) AS fts_rank
FROM review_assistant.rag_chunks AS chunk
CROSS JOIN query_input
WHERE chunk.lexical_config_ref = %(lexical_config_ref)s
  AND chunk.search_vector @@ query_input.ts_query
ORDER BY fts_rank DESC, chunk.chunk_id ASC
LIMIT %(candidate_k)s;
```

各层责任：

- `query_input` 只编译一次查询对象。
- `lexical_config_ref` 阻止混用拆词空间。
- `@@` 形成候选。
- `ts_rank` 给出 PostgreSQL 原生 rank，`DESC` 表示越大越靠前。
- `chunk_id ASC` 稳定处理并列。
- `LIMIT` 截取本路候选。

真实 SQL 还会返回 query lexeme、命中词、总匹配数量和空结果诊断。参数绑定把 SQL 结构和外部字符串分开，查询内容不能拼进语句里。

## 排序不是匹配，rank 也不是正确性

假设两行都含「售后」：

```text
A：仅已支付且已完成的订单可申请售后。
B：虚拟商品不进入售后流程。
```

查询「虚拟商品 售后」时，两行都可能进名单，但 B 含有更多查询词，通常应排得更高。匹配已经结束；`ts_rank` 只在已匹配的行里比先后。

`ts_rank` 会用词频、位置和权重。`ts_rank_cd` 还强调匹配词在文档中靠得近不近。具体数字只在同一查询、同一函数、同一配置下可比较。

公共结果明确写成：

```text
rank_name = postgresql_ts_rank
fts_rank = ...
higher_is_better = true
```

不用含糊的 `score`，也不把这个值与 Dense Retrieval 的 cosine distance 直接相加。

高 rank 只能说明：按当前词面排序函数，它更靠前。它不能证明句子仍有效、属于允许的知识范围、不是历史材料、正确表达了否定，或足以支持最终评审结论。那些判断要由过滤、融合、Context 和后续校验继续做。

## BM25 为什么必须单独命名

BM25 是一种具体的词项排序方法，核心直觉包括：

1. **IDF**：越少见的词通常越有区分度。
2. **TF 饱和**：重复出现有帮助，但第 20 次不会比第 1 次多 20 倍价值。
3. **文档长度归一化**：长文档天然含词更多，需要校正。

常见形式可以写成：

```text
BM25(q, d)
= Σ IDF(term)
  × TF(term, d) × (k1 + 1)
    / (TF(term, d) + k1 × (1 - b + b × |d| / avgdl))
```

理解公式是为了能预测：稀有接口名通常比「规则」更有区分力；堆砌关键词不应线性提高相关性；同一词频在很短和很长的 Chunk 中意义不同。不必手算分数。

PostgreSQL 内置 `ts_rank` / `ts_rank_cd` 是它自己的全文排序函数，不等于 BM25。两者都属于 lexical ranking，不能互换名字。

| 判断 | 是否正确 |
| --- | --- |
| PostgreSQL FTS 是 Lexical Retrieval | 是 |
| 所有 Lexical Retrieval 都使用 BM25 | 否 |
| `ts_rank_cd` 是 cover-density rank | 是 |
| 可以把 `fts_rank` 输出成 `bm25_score` | 否 |
| 可以在未来用固定评估比较 BM25 extension 与当前 rank | 可以，但要作为新实验 |

V0 不在 Python 里再维护一套产品 BM25，也不为了这个名称引入数据库 extension。当前目标是先建立一条真实、可诊断的 PostgreSQL FTS 基线。

## 真实代码怎样守住边界

[`PostgresFTSRetriever`](../../source/packages/rag_core/retrieval/postgres_fts.py) 当前三个公共动作：

```python
retriever.upsert_chunks(chunks)
retriever.search(query, candidate_k=5)
retriever.delete_chunks(chunk_ids)
```

它接收第 9 步真实 `Chunk`，不是另造一份只有文本的对象。写入时继续保存 `chunk_id`、文档身份和版本、parent、文件格式、source role、evidence eligibility、source spans、business metadata、原文和 token count。

`search` 返回：

```text
LexicalSearchResult
├── hits: LexicalHit[]
└── diagnostics: LexicalDiagnostics
```

`LexicalHit` 是词面候选，不是最终 Context Source，也不是 Citation。

核心调用链：

```text
inspect_lexical_retrieval.main
→ load_document(order_rules.md)
→ chunk_document(structure-aware)
→ PostgresFTSRetriever.upsert_chunks
   → LexicalAnalyzer.analyze_document
   → Psycopg executemany
   → INSERT ... ON CONFLICT DO UPDATE
   → transaction commit / rollback
→ PostgresFTSRetriever.search
   → LexicalAnalyzer.analyze_query
   → websearch_to_tsquery
   → @@ candidate match
   → ts_rank + stable ordering
   → LexicalHit + LexicalDiagnostics
```

Loader 和 Chunker 的输出在这里第一次进入可搜索存储。demo 没有另写一份手搓 Chunk 列表。

「没有相同词面」应返回成功的空名单：

```text
hits = []
matched_chunk_count = 0
tsquery = 可观察
```

「数据库连接失败」不能伪装成空名单。当前错误层包括：

| code | 含义 |
| --- | --- |
| `connection_failed` | 服务、host、port、database 或网络不可用 |
| `auth_failed` | Role 或密码错误 |
| `migration_required` | 当前 Database 没有目标表 |
| `permission_denied` | Role 无权执行操作 |
| `database_error` | 其他真实 PostgreSQL 执行错误 |

错误还带 `stage`：connection、indexing、query 或 deletion。应用不会在这些失败后改用 SQLite、Mock 或 Python `in` 返回伪成功。

跑实验时若落到这些错误，再检查产品 README 的连接与 migration，或按需阅读 [PostgreSQL 零基础](../concepts/postgresql-for-ai-applications.md)。需要能分清的基础包括：Server / Database / Schema / Table、主键与 upsert、事务、参数化 SQL，以及连接失败和成功空结果不是一回事。读机制本身不要求先背这些条目。

## 用实验观察机制，不把实验手册写进本节

真实运行入口是 [`inspect_lexical_retrieval.py`](../../source/demos/rag_retrieval_lab/inspect_lexical_retrieval.py)。命令、参数和排障以 [lab README 步骤 11](../../source/demos/rag_retrieval_lab/README.md#步骤-11postgresql-fts-lexical-retrieval) 为准。

实验把第 8 步 Loader、第 9 步 structure-aware Chunking、真实 `rag_chunks` 和 PostgreSQL FTS 接在同一条链上，并用共享 [`retrieval_queries.json`](../../review_assistant/fixtures/v0/retrieval/retrieval_queries.json) 提问。这些问题用来观察机制，不是冻结的 V0 验收集。

运行前先预测：

| 问题 | 预测 |
| --- | --- |
| `source_channel` | 精确技术标识应命中接口约束 |
| `售后接口 v2` | 中英混合词项共同贡献 rank |
| `申请售后` | 词面一致应能命中 |
| `source_channel 什么时候必填？` | 填充词被过滤，标识仍能召回 |
| `发起逆向服务` | 资料无相同词面时可能无结果 |
| `虚拟商品 售后` | 能命中否定规则，但 rank 不理解否定 |
| `售前活动入口` | 可能无结果，也可能因通用词产生噪声 |

重点不是让每个问题都成功，而是解释结果为什么符合或违反当前机制。

观察 OR 与 AND 时，只改 query operator。比较：应用词有没有变、`tsquery` 怎样变、命中数怎样变、带「必填」的问句会不会被 AND 淘汰、噪声是否减少。不要同时换 fixture、切分策略或停用词。

词面检索比字符串包含多控制了「词」和「排序」。对照时可以先按原文包含查找，再看拆词结果和词袋：

```sql
SELECT chunk_id, content
FROM review_assistant.rag_chunks
WHERE content LIKE '%source_channel%';

SELECT chunk_id, lexical_text, search_vector
FROM review_assistant.rag_chunks
ORDER BY chunk_id;
```

这是在对比两种查找机制，不是在教如何把表用起来。`LIKE` 确认原文里有没有这段字符串；FTS 多出了检索词、词袋、查询条件和原生 rank。

GIN 是否被查询计划选中，可以用 `EXPLAIN` 观察。小 fixture 走顺序扫描往往是成本选择，不要写成索引坏了。评估索引收益需要更有代表性的数据量和单独实验；本节只确认索引定义、查询形态和可诊断性。

## 三种现象要用不同证据解释

### 同义改写无结果：词面机制的边界

```text
查询：发起逆向服务
资料：申请售后
```

可能得到空候选。排查顺序：应用查询词 → PostgreSQL 查询词和 `tsquery` → 资料的 `lexical_text` 与 `search_vector` → 确认没有共同词 → 记为 lexical 自然边界。

不要把空结果说成 PostgreSQL 故障，不要为了让案例成功把「逆向服务」改成「售后」，也不要立刻给全库加同义词并宣称质量提高。后续 Dense Retrieval 会在同一问题上观察语义表示能否补回候选；收益仍要固定评估证明。

### 否定规则 rank 高：匹配成功但还没有理解规则

「虚拟商品不进入售后流程」可能因为同时命中「虚拟商品」和「售后」而排第一。词面对了，否定没有被推理成业务逻辑。

```text
召回正确候选
≠ 已经完成规则推理
≠ 已经证明最终回答正确
```

应把原文和来源交给后续 Context 与模型，不能因为 rank 高就当成确定结论。

### 数据库不可用：依赖失败，不是词面 0 条

连接、鉴权、权限或缺表时，按产品 README 定位。它验证的是错误可见，不证明检索效果。离线测试里的空输入、fingerprint 和参数校验也不能代替真实 FTS 运行。

## Psycopg 和 GUI 封装了什么

Psycopg 封装连接、参数绑定、事务和 PostgreSQL 错误到 Python 异常的映射。它没有决定 Chunk 身份、中文怎么拆、AND 还是 OR、rank 是否等于业务质量、哪些来源有证据资格。

图形客户端方便看对象和跑 SQL，同样不替代 migration、参数化查询、错误契约和检索评估。可重复的命令与代码仍是实验真源。

## 修改题：让新枚举成为稳定精确标识

接口新增枚举 `AFTER_SALE_V3`，资料和查询都可能大小写不同。先预测：规范化会怎样处理、技术标识规则是否把它当成一块、会生成哪个备份词、文档和查询能否得到相同检索词、改规则会不会改变 `lexical_config_ref`、需要补哪些测试和重新写入。

完成后至少验证：

1. `AFTER_SALE_V3` 与 `after_sale_v3` 分析结果兼容。
2. 普通中文词没有被破坏。
3. 有效策略改变时配置身份同步变化。
4. 真实 PostgreSQL 查询仍返回原生 `fts_rank`。

不要只改 fixture 让测试通过；词法规则、配置身份、测试和已写入数据必须一致。

## 学完后应能解释什么

不看代码注释，尝试回答：

1. 按词查找解决什么问题？它为什么不负责「逆向服务 ≈ 申请售后」？
2. `techidsourcechannel` 从哪来？为什么不只保留 `source_channel`？
3. 切开的碎片、应用留下的词、数据库收下的词，为什么要分成三层？
4. 匹配、排序和证据判断分别回答什么？
5. `content`、`lexical_text` 和 `search_vector` 为什么要同时存在？
6. 文档和查询为什么必须使用同一个 `lexical_config_ref`？AND / OR 为什么不进这个身份？
7. `tsquery` 与 `@@` 分别做什么？
8. OR 为什么提高召回，也可能增加噪声？
9. GIN 加速了什么，又没有解决什么？
10. `ts_rank` 为什么不能和 cosine similarity 相加，也不能叫 BM25？
11. 同义改写得到 0 条时，怎样证明这是词面边界而不是数据库失败？
12. 为什么高 rank 不能直接当作证据充分？
13. 拆词规则变了，为什么要重新写入？
14. 成功空名单和连接失败，为什么必须是不同结果？

若能用售后例子讲清从原文到词面候选的变化，读懂生成列与核心查询，在实验里解释一次 OR/AND 和一次 0 条结果，并完成精确标识修改题，就已经达到本节对 Lexical Retrieval 与 PostgreSQL FTS 的要求。

## 本节边界

本节建立的是：可版本化的中文与技术标识拆词、真实 PostgreSQL 词袋与 GIN、参数化写入和查询、原生 `fts_rank`、可观察的空结果与数据库错误。

本节没有建立：向量检索、ANN、RRF、完整过滤与阈值诊断、Context、可信生成，以及产品 Review API。按词找到的候选还不是经过校验的引用。

正文读完后返回 [标准学习路径](../learning-path.md)；标准顺序不由本文页尾或代码目录推断。

## 官方参考

- [PostgreSQL：Full Text Search](https://www.postgresql.org/docs/current/textsearch.html)
- [PostgreSQL：Text Search Functions and Operators](https://www.postgresql.org/docs/current/functions-textsearch.html)
- [PostgreSQL：Tables and Indexes](https://www.postgresql.org/docs/current/textsearch-tables.html)
- [PostgreSQL：GIN Indexes](https://www.postgresql.org/docs/current/gin.html)
- [Psycopg 3：Basic module usage](https://www.psycopg.org/psycopg3/docs/basic/usage.html)
- [jieba：中文分词与搜索引擎模式](https://github.com/fxsjy/jieba)
