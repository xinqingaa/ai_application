# Lexical Retrieval、BM25 边界与 PostgreSQL 全文检索

前面的课程已经把真实资料变成了可回查的 Chunk，也观察了文本怎样进入 Embedding 空间。现在需要第一次回答“怎样从一批 Chunk 中找出候选”。

本节只解决一个核心问题：

> 一个带稳定身份和来源的 Chunk，怎样进入真实 PostgreSQL，变成可检索词项，并根据用户查询形成可解释、可排序、可诊断的 lexical candidates？

本文不要求你已经使用过其他关系数据库，但会把 PostgreSQL 基础与全文检索机制分开：已经能读懂表、基本 SQL、事务、索引和 migration，可以直接继续；还不确定时，先完成下方的按需自检和补充阅读。

读完后，你应该能够：

- 读懂本节使用的 `rag_chunks` 全文检索列和索引。
- 解释 `tsvector`、`tsquery`、`@@`、GIN 和 `ts_rank` 分别负责什么。
- 解释中文词项和 `source_channel` 等技术标识怎样进入索引。
- 区分字符串包含、候选匹配、候选排序和最终证据判断。
- 说明 PostgreSQL 原生 rank 为什么不能叫 BM25 score。
- 运行真实 PostgreSQL 实验，并根据词项、查询、索引和错误层定位问题。

本文不重新教授通用关系模型、SQL、JOIN 和聚合，也不展开 PostgreSQL 运维、高可用、复制、分区、VACUUM 调优或完整权限体系；不实现 pgvector、Dense Retrieval、RRF、统一阈值和最终 Context。PostgreSQL 安装、环境变量、migration 命令和可选 GUI 统一由 [产品 README](../../review_assistant/README.md#postgresql-本地准备) 维护，正文不复制运行手册。

## 先看这一节为什么不是“数据库换皮”

假设知识库里有两个 Chunk：

```text
A：售后接口 v2 必须提供 source_channel。
B：仅已支付且已完成的订单可申请售后。
```

用户查询：

```text
source_channel 什么时候必填？
```

普通数据库当然可以保存 A 和 B，但“保存下来”没有自动回答这些问题：

- 查询应该拆成哪些词？
- “什么时候”是不是有检索价值的词？
- `source_channel` 能否作为完整技术标识保留？
- 哪些行进入候选？
- 两行都匹配时谁排前面？
- 没有相同词面时，是数据库坏了还是 lexical 的正常边界？
- 排名高的 Chunk 是否真的能支持最终风险结论？

因此本节的数据流不是简单的“把文本存进表”：

```text
Chunk.text
→ 应用侧词法分析
→ lexical_text + lexical_config_ref
→ PostgreSQL tsvector
→ GIN 倒排索引

用户查询
→ 同一词法分析
→ websearch query
→ PostgreSQL tsquery

tsvector @@ tsquery
→ 匹配候选
→ ts_rank 排序
→ LexicalHit[] + LexicalDiagnostics
```

数据库负责可靠存储、匹配和排序执行；应用仍然要负责身份、词法策略、查询语义、参数绑定、结果契约和错误可见性。

## 先用一个不依赖 PostgreSQL 的例子理解词法检索

先不看 SQL，仍使用开头的两个 Chunk。应用对文本做规范化和分词后，可以暂时把结果想成下面这样：

```text
Chunk A：售后接口 v2 必须提供 source_channel
词项：售后 / 接口 / v2 / source_channel / techidsourcechannel / 必须 / 提供

Chunk B：仅已支付且已完成的订单可申请售后
词项：已支付 / 已完成 / 订单 / 申请 / 售后

查询：source_channel 什么时候必填
词项：source_channel / techidsourcechannel / 必填
```

这里会遇到三个相近但责任不同的词：

| 名称 | 本文中的含义 | 例子 |
| --- | --- | --- |
| 原始片段 / token | 分词器从原文本中识别出的表面片段，尚未必能进入检索 | `什么时候`、`source_channel` |
| 应用词项 / term | 应用规范化、过滤和补充后决定保留的检索单位 | `techidsourcechannel`、`必填` |
| PostgreSQL lexeme | PostgreSQL parser 和 dictionary 最终写入 `tsvector` 或 `tsquery` 的归一化单位 | 后文真实输出中的 `'售后'`、`'techidsourcechannel'` |

本项目先在应用侧处理中文和技术标识，再交给 PostgreSQL 的 `simple` 配置形成 lexeme。term 与 lexeme 经常长得相同，但它们位于不同处理层，排查时不能只看其中一个。

如果每次查询都逐行扫描所有 Chunk，再检查有没有共同词项，数据增大后成本会持续上升。倒排关系把方向反过来，记录“某个 lexeme 出现在哪些 Chunk 中”：

```text
售后                 → [Chunk A, Chunk B]
techidsourcechannel  → [Chunk A]
必填                 → []
```

查询到来时，系统先按 lexeme 找到较小的 Chunk 集合，再根据 AND / OR 组合候选。以 OR 为例，虽然资料写的是“必须提供”而查询写的是“必填”，共同的 `techidsourcechannel` 仍能让 Chunk A 进入候选；AND 则可能因为没有共同的“必填”而淘汰它。

候选形成后才进入排序。匹配回答“谁有资格参加”，rank 回答“候选之间谁更靠前”，最终证据判断还要继续检查版本、来源、否定和上下文：

```text
共同 lexeme + AND / OR
→ 候选集合
→ 词频、位置或权重等排序信号
→ 本路排名
→ 后续过滤、融合与证据判断
```

PostgreSQL 用 `tsvector` 保存文档 lexeme，用 `tsquery` 表达查询条件，用 `@@` 判断是否匹配。GIN 是帮助 PostgreSQL 从 lexeme 快速定位候选行的倒排索引；它加速符合形态的 `@@` 查询，但不定义查询语义、不产生更正确的 rank，也不理解同义词和否定。

## 进入 FTS 前，先判断数据库基础是否够用

本节会直接读取 migration、参数化 SQL 和 Psycopg 代码，不在主线中重新讲一遍通用数据库基础。继续之前，先判断自己能否大致回答：

1. Server、Database、Schema 和 Table 分别处于什么位置？
2. 主键、`NOT NULL`、`NULL`、基本 CRUD 和 upsert 表达什么？
3. 事务、索引和 migration 为什么存在？
4. 参数化 SQL 为什么不能用字符串拼接替代？
5. 连接成功、缺表、权限不足和成功空结果有什么区别？

不要求现在背出完整语法。只要其中任何一项仍然陌生，先阅读按需概念篇 [PostgreSQL 零基础：读懂并使用项目数据库](../concepts/postgresql-for-ai-applications.md)，再回到这里。它不属于标准学习路径的新步骤，也不会改变课程编号。

已经具备这些基础时，直接把当前数据库边界压缩成下面几条：

- 真实表是 [`review_assistant.rag_chunks`](../../review_assistant/infra/migrations/0001_create_rag_chunks.sql)，应用继续使用 Chunking 阶段产生的稳定 `chunk_id`。
- `PostgresFTSRetriever.upsert_chunks` 通过参数化 upsert 和事务批量保存 Chunk；失败时整组回滚，不留下半份文档。
- `search_vector` 是 PostgreSQL 根据 `lexical_text` 生成的全文检索列；GIN 只为符合形态的 `@@` 匹配提供候选入口。
- 连接、鉴权、migration、权限和查询错误属于不同失败层，不能统一伪装成空候选。
- 本节使用 PostgreSQL 内置 FTS，不需要额外 Extension；后续 pgvector 才会在数据库侧增加 `vector` 类型和运算符。

接下来只讨论这些数据库能力怎样承载 Lexical Retrieval，不再展开通用 SQL。

## 从原文到 PostgreSQL 可搜索对象

### `tsvector` 不是 Embedding vector

名字里都有 vector，但两者完全不同：

| 对象 | 保存什么 | 主要比较方式 |
| --- | --- | --- |
| `tsvector` | 归一化词项、位置和权重 | 词项是否匹配 `tsquery` |
| Embedding vector | 浮点维度组成的稠密表示 | cosine、inner product、L2 等 |

`tsvector` 示例形态可能是：

```text
'source':3 'channel':4 '售后':1 '接口':2
```

它不是原文，也不是语义向量。原文继续保存在 `content` 中，不能从 `tsvector` 反推完整句子和来源位置。

### 为什么单独保存 `lexical_text`

PostgreSQL 内置 parser 能识别 token 边界，dictionary 再把 token 归一化成 lexeme；但中文业务文本没有天然空格，默认边界不一定符合“售后”“虚拟商品”“逆向服务”等项目词义。

当前项目采用：

```text
原文
→ Unicode NFKC + casefold
→ jieba 搜索模式（HMM=False）
→ 过滤少量问句填充词
→ 为技术标识增加稳定哨兵词
→ 空格分隔 lexical_text
→ to_tsvector('pg_catalog.simple', lexical_text)
```

例如：

```text
原文：source_channel 什么时候必填？

应用查询词项：
source_channel / techidsourcechannel / 必填
```

`什么`、`时候` 被当前查询策略过滤；`source_channel` 在普通 parser 可能按标点拆开，因此额外加入全字母数字的 `techidsourcechannel` 哨兵。文档和查询看到同一技术标识时会产生相同哨兵，避免只靠 `source` 与 `channel` 两个通用部分。

这是当前项目的工程取舍，不是中文检索唯一标准答案：

- jieba 版本和字典不是语言真理。
- 问句停用词可能在其他业务中携带信息。
- 技术哨兵提高精确标识稳定性，也增加词项数量。
- 更复杂场景可以评估 PostgreSQL 中文 parser extension、专用搜索引擎或其他分析器。

V0 先要一条可解释、可版本化、安装成本可控的真实基线。

### 词法配置也是索引空间身份

Embedding 变化需要重建向量索引；lexical 分析策略变化同样需要重建 FTS 表示。

[`LexicalConfig`](../../source/packages/rag_core/lexical/models.py) 的身份包含：

- name
- version
- PostgreSQL text search config
- domain terms
- stop terms
- 所有字段计算出的 fingerprint

最终形成：

```text
jieba_search_simple@1.0.0:<fingerprint>
```

索引行和查询必须使用同一 `lexical_config_ref`。代码会过滤掉不兼容行，而不是把新查询静默打到旧词项上。改变策略后“突然没有结果”，应先检查身份和重建入库，不应立刻降低阈值或怪罪 PostgreSQL。

AND / OR 只改变已有词项怎样组成查询，不改变文档与查询的共同词项空间，因此它不进入 `lexical_config_ref`，而进入独立 `retriever_config_ref`。切换 operator 必须记录新的 Retriever 配置，但不需要重建文档索引。

### 生成列保证写入后表示同步

migration 中的真实定义是：

```sql
search_vector TSVECTOR GENERATED ALWAYS AS (
    to_tsvector('pg_catalog.simple', lexical_text)
) STORED
```

含义是：

- 应用写 `lexical_text`。
- PostgreSQL 计算 `search_vector`。
- 更新 `lexical_text` 时自动重算。
- 应用不能直接写生成列。
- text search config 显式写为 `pg_catalog.simple`，不依赖会变化的 session 默认值。

如果文档端和查询端使用不同预处理，即使两侧都调用 `simple` 也可能无法匹配。PostgreSQL 只能执行拿到的词项契约，不能替应用发现版本混用。

## `tsquery` 怎样决定候选

### 文档表示和查询表示必须分开

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

`@@` 只返回 true 或 false，用来决定候选资格。它不返回相关性高低。

### AND 与 OR 不是格式差异

查询有三个词项：

```text
source_channel / techidsourcechannel / 必填
```

AND 要求所有有效词项都出现：

```text
source_channel & techidsourcechannel & 必填
```

如果资料写的是“必须提供”而不是“必填”，AND 可能淘汰本来有用的接口规则。

OR 允许任一词项形成候选：

```text
source_channel | techidsourcechannel | 必填
```

它提高召回，也可能引入只匹配通用词的噪声。当前实验默认使用 OR 建立召回型 lexical baseline，同时允许 `--query-operator and` 做受控对照。

这不是永久认定 OR 更好。具体 operator、词项、`candidate_k` 和后续阈值都属于 Retriever 配置和实验变量；第 14 步会继续建立完整过滤与诊断契约。

### 参数化 SQL 没有把机制藏起来

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

这里每一层都有责任：

- `query_input` 只编译一次查询对象。
- `lexical_config_ref` 阻止混用词法空间。
- `@@` 形成候选。
- `ts_rank` 产生 PostgreSQL 原生 rank。
- `DESC` 表示越大越靠前。
- `chunk_id ASC` 稳定处理并列。
- `LIMIT` 截取本路候选。

真实 SQL还会返回 PostgreSQL query lexeme、matched terms、总匹配数量和空结果诊断。

## 排序不是匹配，rank 也不是正确性

假设两个 Chunk 都含有“售后”：

```text
A：仅已支付且已完成的订单可申请售后。
B：虚拟商品不进入售后流程。
```

查询“虚拟商品 售后”时，两行可能都成为候选，但 B 包含更多查询词，通常应排得更高。

PostgreSQL `ts_rank` 会利用 `tsvector` 中的词频、位置和权重信息计算相关性值。`ts_rank_cd` 还强调 cover density，也就是匹配词在文档中的接近程度。具体值只在同一查询、同一函数、同一配置下有比较意义。

当前公共结果明确写成：

```text
rank_name = postgresql_ts_rank
fts_rank = ...
higher_is_better = true
```

不使用含糊的 `score`，也不把这个值与下一节的 cosine distance 直接相加。

高 rank 只能说明词项匹配和当前排序函数认为它靠前，不能证明：

- 句子在当前版本仍然有效。
- 它属于允许的知识范围。
- 它不是 Historical Material。
- 它正确表达了否定关系。
- 它足以支持最终评审结论。

这些判断要由 Metadata Filter、RRF、Context、Citation 和证据校验继续完成。

## BM25 为什么必须单独命名

BM25 是一种具体的词项排序方法，核心直觉包括：

1. **IDF**：在所有文档中越少见的词，区分度通常越高。
2. **TF 饱和**：一个词重复出现有帮助，但第 20 次不会比第 1 次多 20 倍价值。
3. **文档长度归一化**：长文档天然含词更多，需要校正。

常见形式可以写成：

```text
BM25(q, d)
= Σ IDF(term)
  × TF(term, d) × (k1 + 1)
    / (TF(term, d) + k1 × (1 - b + b × |d| / avgdl))
```

- `q` 是查询。
- `d` 是文档。
- `|d| / avgdl` 表示相对文档长度。
- `k1` 控制词频饱和。
- `b` 控制长度归一化强度。

理解公式的目标不是手算分数，而是能够预测：

- 稀有接口名通常比“规则”更有区分力。
- 重复堆砌关键词不应线性提高相关性。
- 同一词频在很短和很长的 Chunk 中意义不同。

PostgreSQL 内置 `ts_rank` / `ts_rank_cd` 是 PostgreSQL 自己的全文排序函数，不等于 BM25。两者都属于 lexical ranking，不代表可以互换名字。

| 判断 | 是否正确 |
| --- | --- |
| PostgreSQL FTS 是 Lexical Retrieval | 是 |
| 所有 Lexical Retrieval 都使用 BM25 | 否 |
| `ts_rank_cd` 是 cover-density rank | 是 |
| 可以把 `fts_rank` 输出成 `bm25_score` | 否 |
| 可以在未来用固定评估比较 BM25 extension 与当前 rank | 可以，但要作为新实验 |

V0 不在 Python 内再维护一套产品 BM25，也不为了获得 BM25 名称引入数据库 extension。当前目标是先建立一条真实、可诊断的 PostgreSQL FTS baseline。

## 真实代码怎样守住边界

### 公共入口接收和返回什么

[`PostgresFTSRetriever`](../../source/packages/rag_core/retrieval/postgres_fts.py) 有三个当前公共动作：

```python
retriever.upsert_chunks(chunks)
retriever.search(query, candidate_k=5)
retriever.delete_chunks(chunk_ids)
```

它接收第 9 步真实 `Chunk`，不是另造一份只有文本的检索对象。写入时继续保存：

- `chunk_id`
- 文档身份和版本
- parent 关系
- 文件格式
- source role
- evidence eligibility
- source spans
- business metadata
- 原文和 token count

`search` 返回：

```text
LexicalSearchResult
├── hits: LexicalHit[]
└── diagnostics: LexicalDiagnostics
```

`LexicalHit` 是候选，不是最终 ContextSource，也不是 Citation。

### 核心调用链

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

这条链把此前课程能力真正接起来：Loader 和 Chunker 的输出第一次进入可搜索存储；demo 没有复制一份手写 Chunk 列表。

### 正常结果与错误怎样分开

“没有相同词面”应返回成功的空 `hits`：

```text
hits = []
matched_chunk_count = 0
tsquery = 可观察
```

“数据库连接失败”不能伪装成空结果。当前错误层包括：

| code | 含义 |
| --- | --- |
| `connection_failed` | 服务、host、port、database 或网络不可用 |
| `auth_failed` | Role 或密码错误 |
| `migration_required` | 当前 Database 没有目标表 |
| `permission_denied` | Role 无权执行操作 |
| `database_error` | 其他真实 PostgreSQL 执行错误 |

错误还带 `stage`：connection、indexing、query 或 deletion。应用不会在这些失败后改用 SQLite、Mock 或 Python `in` 返回伪成功。

## 运行实验前先明确观察问题

真实运行入口是 [`inspect_lexical_retrieval.py`](../../source/demos/rag_retrieval_lab/inspect_lexical_retrieval.py)，完整安装、migration、参数和命令见 [lab README](../../source/demos/rag_retrieval_lab/README.md#步骤-11postgresql-fts-lexical-retrieval)。

实验使用：

- 第 8 步的真实 Markdown Loader。
- 第 9 步的 structure-aware Chunking。
- `review_assistant.rag_chunks` 真实表。
- PostgreSQL 真实 `tsvector`、GIN、`tsquery` 和 rank。
- [`lexical_queries.json`](../../review_assistant/fixtures/v0/retrieval/lexical_queries.json) 中的有效业务问题。

这些问题是探索性机制材料，不是冻结的 V0 acceptance 集。运行前先预测：

| 问题 | 预测 |
| --- | --- |
| `source_channel` | 精确技术标识应命中接口约束 |
| `售后接口 v2` | 中英混合词项共同贡献 rank |
| `申请售后` | 词面一致规则应命中 |
| `source_channel 什么时候必填？` | 填充词被过滤，标识仍能召回 |
| `发起逆向服务` | 资料无相同词面时可能无结果 |
| `虚拟商品 售后` | 能命中否定规则，但 rank 不理解否定逻辑 |
| `售前活动入口` | 可能无结果，也可能因通用词产生噪声候选 |

重点不是让每个问题都成功，而是解释结果为什么符合或违反当前机制。

### OR 与 AND 对照

先运行默认 OR，再只改变 query operator 为 AND。比较：

- 应用产生的词项有没有变化？
- PostgreSQL `tsquery` 怎样变化？
- matched count 怎样变化？
- 精确字段问句是否被 AND 中的非同义词淘汰？
- 噪声候选是否减少？

除了 operator，不应同时更换 fixture、Chunk 策略或停用词，否则无法判断唯一变量。

### `LIKE` 与 FTS 对照

在 `psql` 或 GUI 中先用 `LIKE` 查原文，再运行 FTS：

```sql
SELECT chunk_id, content
FROM review_assistant.rag_chunks
WHERE content LIKE '%source_channel%';
```

然后检查生成对象：

```sql
SELECT chunk_id, lexical_text, search_vector
FROM review_assistant.rag_chunks
ORDER BY chunk_id;
```

需要观察的不是谁“语法更高级”，而是 FTS 多出了哪些可控制对象：词法文本、lexeme、`tsquery`、倒排匹配和原生 rank。

### GIN 与查询计划

可以使用：

```sql
EXPLAIN
SELECT chunk_id
FROM review_assistant.rag_chunks
WHERE search_vector @@ websearch_to_tsquery(
    'pg_catalog.simple',
    '"source_channel" OR "techidsourcechannel"'
);
```

如果小 fixture 选择顺序扫描，先解释成本选择，不把它改写成索引故障。要评估索引收益，需要更有代表性的数据规模和单独性能实验；本节只确认索引定义、查询形态和可诊断性正确。

## 三种现象要用不同证据解释

### 同义改写无结果：真实能力边界

表现：

```text
查询：发起逆向服务
资料：申请售后
```

可能结果是空候选。排查顺序：

1. 查看应用 `query_terms`。
2. 查看 PostgreSQL query lexeme 和 `tsquery`。
3. 查看资料 `lexical_text` 与 `search_vector`。
4. 确认两侧确实没有共同词项。
5. 将结论记录为 lexical 自然边界。

不应该：

- 把空结果说成 PostgreSQL 故障。
- 为了让案例成功把“逆向服务”偷偷改成“售后”。
- 直接给全库增加大量同义词并宣称质量提高。

后续 Dense Retrieval 机制会在同一问题上观察语义表示是否补回候选；最终收益仍需固定评估证明，具体阅读顺序仍以标准学习路径为准。

### 否定规则 rank 高：匹配成功但证据理解尚未完成

“虚拟商品不进入售后流程”可能因为同时命中“虚拟商品”和“售后”而排第一。FTS 做对了词面匹配，但它没有把“不”推理成业务逻辑。

这说明：

```text
召回正确候选
≠ 已经完成规则推理
≠ 已经证明最终回答正确
```

应该保留原文和来源，把候选交给后续 Context 与模型；不能因为 rank 高就把它转成确定结论。

### 数据库不可用：真实依赖故障

如果运行时真实出现连接、鉴权、权限或 migration 问题，使用产品 README 的检查顺序定位。它验证的是异常流和可观察性，不证明 lexical 检索效果。

离线测试中的空输入、配置 fingerprint 和参数校验属于确定性契约；它们也不能代替真实 PostgreSQL FTS 运行。

## Psycopg 和 GUI 封装了什么

Psycopg 封装：

- PostgreSQL wire protocol 和 Python 类型适配。
- connection、cursor 和参数绑定。
- transaction context。
- SQLSTATE 到 Python 异常类型的映射。

它没有决定：

- Chunk 身份。
- 中文词法策略。
- AND 还是 OR。
- rank 是否符合业务质量。
- 哪些来源有证据资格。
- 何时重建索引。

pgAdmin 等 GUI 封装对象浏览、SQL 编辑和结果展示；它也不会替应用建立 migration、参数化查询、错误契约或检索评估。因此本课程把 GUI 当作可选观察入口，把可重复命令和代码作为真源。

## 修改题：让新枚举成为稳定精确标识

需求变化：接口新增枚举 `AFTER_SALE_V3`，资料和查询都可能使用大小写不同的写法。

先预测：

- NFKC 和 casefold 会怎样处理它？
- 技术标识 regex 是否把它识别为一个整体？
- 会生成哪个哨兵词？
- 文档和查询能否产生相同词项？
- 修改 regex 是否会改变所有旧标识的 `lexical_config_ref`？
- 需要补哪些单元测试和重新入库动作？

完成修改后至少验证：

1. `AFTER_SALE_V3` 与 `after_sale_v3` 分析结果兼容。
2. 普通中文词项没有被破坏。
3. config 身份在有效策略改变时同步变化。
4. 真实 PostgreSQL 查询仍返回原生 `fts_rank`。

不要只修改 fixture 让测试通过；词法规则、配置身份、测试和入库数据必须一致。

## 掌握检查

不看代码解释，尝试回答：

1. 字符串包含、词项匹配、候选排序和最终证据判断分别回答什么问题？
2. `lexical_text`、`tsvector` 和原文为什么要同时存在？
3. 为什么文档和查询必须使用同一个 `lexical_config_ref`？
4. 查询 operator 为什么属于 Retriever 配置，而不属于词法空间身份？
5. `tsquery` 与 `@@` 分别做什么？
6. OR 为什么提高召回，也可能增加噪声？
7. GIN 加速了什么，又没有解决什么？
8. `ts_rank` 的值能否与 cosine similarity 直接相加？
9. PostgreSQL `ts_rank_cd` 为什么不能叫 BM25？
10. 同义改写无结果时，怎样证明这是词面边界而不是数据库失败？
11. 为什么高 rank 不能直接当作证据充分？
12. 词法配置变化后为什么需要重新入库？
13. 成功空候选与数据库连接失败为什么必须采用不同结果契约？
14. Psycopg 封装了哪些数据库交互，又没有替应用决定哪些检索策略？

如果你能画出从 `Chunk.text` 到 `LexicalHit` 的完整数据流，读懂 FTS migration 与核心查询，运行真实实验，解释 OR/AND 变化，并完成技术标识修改题，就已经达到本节需要的 Lexical Retrieval 与 PostgreSQL FTS 掌握程度。

## 当前交付与边界

本节已经交付：

- 可版本化的中文与技术标识词法分析。
- 真实 `rag_chunks` PostgreSQL migration。
- 生成 `tsvector` 列和 GIN 索引。
- 参数化 Chunk upsert、delete 和 FTS search。
- 原生 `fts_rank`、matched terms、`tsquery` 和结构化错误。
- 使用同一 Loader、Chunker 与固定业务材料的真实实验入口。
- 离线契约测试与显式真实 PostgreSQL 集成测试入口。

仍未交付：

- pgvector 与 Dense Retrieval。
- ANN 与向量索引。
- lexical / dense RRF。
- 完整 Metadata Filter、阈值和淘汰诊断。
- Context Construction 与可信生成组合。
- 产品 Review API 和 Web 工作台。

正文读完后返回 [标准学习路径](../learning-path.md)；标准顺序不由本文页尾或代码目录推断。

## 官方参考

- [PostgreSQL：Full Text Search](https://www.postgresql.org/docs/current/textsearch.html)
- [PostgreSQL：Text Search Functions and Operators](https://www.postgresql.org/docs/current/functions-textsearch.html)
- [PostgreSQL：Tables and Indexes](https://www.postgresql.org/docs/current/textsearch-tables.html)
- [PostgreSQL：GIN Indexes](https://www.postgresql.org/docs/current/gin.html)
- [Psycopg 3：Basic module usage](https://www.psycopg.org/psycopg3/docs/basic/usage.html)
- [jieba：中文分词与搜索引擎模式](https://github.com/fxsjy/jieba)
