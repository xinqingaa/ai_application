# Lexical Retrieval、BM25 边界与 PostgreSQL 全文检索

> 机制篇：解释固定 RAG 中“按词找候选”这一条路线。第 8–9 步已经产生带稳定身份的 Chunk；第 10 步观察了 Embedding 表示。本节只回答：词面候选怎样产生、怎样排序、怎样诊断。
>
> 课程位置：[标准学习路径](../learning-path.md) V0 第 11 步。数据库基础、安装和启动见 [PostgreSQL 零基础](../concepts/postgresql-for-ai-applications.md) 与 [第 11 步实验准备](../../source/demos/rag_retrieval_lab/docs/11-lexical-retrieval.md)。

## 先看这张图

固定 RAG 的完整链路如下，本节只深入左侧的 Lexical route：

```text
Reference Files
    |
    v
Loader / Chunker
    |
    v
Chunk + Metadata
    +------------------------------+
    |                              |
    v                              v
Lexical route                    Dense route (第 12 步)
    |                              |
词项分析                         Embedding
    |                              |
lexical_text                     vector
    |                              |
tsvector + GIN                   pgvector
    |                              |
tsquery + @@                    DenseHit
    |
ts_rank
    |
LexicalHit
    +--------------+---------------+
                   v
                RRF (第 13 步)
                   |
                Context
                   |
                  LLM
```

PostgreSQL 在这里不是“另一个向量数据库”：它本身提供关系存储和内置 FTS；后续 `pgvector` 是安装在 PostgreSQL 中的扩展，为另一条 Dense route 增加向量类型和运算。

## 本节要建立的判断

读完并完成实验后，应能回答：

- 查询和 Chunk 怎样使用同一套词项规则？
- `content`、`lexical_text` 和 `search_vector` 为什么同时存在？
- `@@` 怎样决定候选资格，`ts_rank` 怎样决定候选顺序？
- BM25 与 PostgreSQL `ts_rank` 都属于词面排序，但为什么不能互换名称？
- 成功的空结果、数据库连接失败、缺少 migration 和权限错误怎样区分？
- 词面候选为什么不是最终 Context，也不是 Citation？

## 1. 先用两个 Chunk 预测结果

假设知识库中有：

```text
A：售后接口 v2 必须提供 source_channel。
B：仅已支付且已完成的订单可申请售后。
```

查询：

```text
source_channel 什么时候必填？
```

当前应用规则会保留 `source_channel` 和 `必填`，过滤常见填充词。A 通常会因为字段标识命中；“必填”和“必须提供”意思接近，但不是同一个词面，因此不能假定它们一定匹配。

查询“发起逆向服务”时，如果资料只出现“申请售后”，可以成功返回 0 条。这是词面机制的自然边界，不是数据库故障。

必须分开三件事：

```text
匹配：谁有资格进入候选名单？
排序：候选名单中谁更靠前？
证据：候选内容是否足以支持最终业务结论？
```

高 rank 只回答第二个问题。

## 2. 文档和查询经过同一套词项处理

中文没有天然空格，技术标识又不能随意拆散。因此当前实现由应用侧先做可版本化的分析，再交给 PostgreSQL 的 `simple` text search config：

```text
原文
→ NFKC + casefold
→ jieba 搜索模式
→ 过滤少量填充词
→ 保留技术标识，并为其生成稳定备份词
→ 空格分隔 lexical_text
→ PostgreSQL 生成 tsvector
```

例如：

```text
source_channel → sourcechannel → techidsourcechannel
```

备份词不是新资料，只是让字段名在下划线被切分时仍有一个稳定的匹配单位。

需要区分三层对象：

| 层 | 含义 | 当前例子 |
| --- | --- | --- |
| token | 刚切开的碎片，尚未决定是否保留 | `什么时候`、`source_channel`、`必填` |
| term | 应用决定写入或查询的词项 | `source_channel`、`techidsourcechannel`、`必填` |
| lexeme | PostgreSQL 词袋最终保存或查询的词 | 通常与 term 接近 |

`LexicalConfig` 的 fingerprint 会记录词法配置、停用词、领域词和 PostgreSQL 配方。文档端和查询端必须使用相同的 `lexical_config_ref`；规则变化后，旧词袋不能和新查询空间混用，需要重新写入。

### 倒排索引解决什么问题

如果每次查询都把全部 Chunk 拉回 Python 再逐行比较，数据变大后成本会随记录数增长。倒排索引把方向反过来，先记录“某个词出现在哪些 Chunk”：

```text
售后                  → Chunk A, Chunk B
techidsourcechannel   → Chunk A
必填                  → （当前资料没有）
```

PostgreSQL 的 GIN 索引加速这类词面候选查找。它不决定查询使用 AND 还是 OR，不产生更正确的业务排序，也不理解同义词和否定。

## 3. PostgreSQL FTS 做了什么

在 `review_assistant.rag_chunks` 中：

| 字段 | 责任 |
| --- | --- |
| `content` | 给人阅读、回源和后续 Context 使用的原文 |
| `lexical_text` | 应用拆好、空格分隔的词项 |
| `search_vector` | PostgreSQL 生成的 `tsvector` 词袋 |
| `lexical_config_ref` | 词法空间身份 |

`tsvector` 不是第 10 步的 Embedding vector：

| 对象 | 保存什么 | 主要比较方式 |
| --- | --- | --- |
| `tsvector` | 词、位置和权重 | 与 `tsquery` 匹配 |
| Embedding vector | 一串浮点数 | cosine、inner product 或 L2 |

原文不能从 `tsvector` 反推，所以 `content` 仍必须保留；词袋也不能替代来源定位和 Metadata。

migration 使用生成列：

```sql
search_vector TSVECTOR GENERATED ALWAYS AS (
    to_tsvector('pg_catalog.simple', lexical_text)
) STORED
```

GIN 索引加速“某个词出现在哪些行”的查找，但不决定应用应该使用 AND 还是 OR，也不理解同义词、否定或证据充分性。

查询侧的核心数据流是：

```text
用户问题
→ LexicalAnalyzer.analyze_query
→ websearch_to_tsquery
→ search_vector @@ tsquery
→ ts_rank
→ 稳定排序 + candidate_k
→ LexicalHit[] + LexicalDiagnostics
```

`@@` 只有匹配/不匹配语义；`ts_rank` 只在匹配行中排序。当前默认 OR，任一词命中即可进入候选；AND 要求所有词都存在，通常召回更窄。两者是 Retriever 配置，不是词袋空间身份。

核心 SQL 可简化为：

```sql
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

真实实现还会返回 query lexeme、命中词、可见数量、匹配总数和延迟，便于判断“没有候选”发生在哪一层。

查询端使用 `websearch_to_tsquery`。默认 OR 时，`source_channel`、`techidsourcechannel`、`必填` 任一词命中即可进入候选；AND 时，三个词都要出现，资料使用“必须提供”而不是“必填”时，A 可能被淘汰。切换 operator 只改变查询条件，不改变已经写入的词袋，因此它记录在独立的 `retriever_config_ref` 中。

同一个查询可以形成两种条件：

```text
OR: source_channel | techidsourcechannel | 必填
AND: source_channel & techidsourcechannel & 必填
```

OR 是当前召回型基线，可能带来只命中通用词的噪声；AND 可能提高精确性，却把“必须提供/必填”这类词面不同但有用的候选淘汰。哪种更好必须由固定样例和指标验证。

生成列会随 `lexical_text` 更新自动重算，应用不能直接写 `search_vector`。配方显式使用 `pg_catalog.simple`，不依赖会话默认值；但数据库不会替应用发现文档端和查询端预处理版本不一致。

## 4. 排序不是匹配，rank 也不是正确性

假设 A、B 都包含“售后”，查询是“虚拟商品 售后”。B 同时命中两个词，通常会排在 A 前面；这只说明当前排序函数认为 B 更相关。

当前实现的公共诊断是：

```text
rank_name = postgresql_ts_rank
fts_rank = ...
higher_is_better = true
```

`ts_rank` 使用词频、位置和权重；`ts_rank_cd` 还会考虑匹配词在文档中是否靠近。具体数字只应在相同查询、相同函数和相同配置下比较，不能直接与 cosine distance 相加，也不能把高 rank 当成证据充分。

## 5. BM25 与 `ts_rank` 的边界

BM25 是一种具体的词项排序方法，通常考虑：

- 稀有词的 IDF 区分度。
- 词频增加的饱和效应。
- 文档长度归一化。

常见形式可以写成：

```text
BM25(q, d)
= Σ IDF(term)
  × TF(term, d) × (k1 + 1)
    / (TF(term, d) + k1 × (1 - b + b × |d| / avgdl))
```

不需要手算这个分数，但应能预测：稀有接口名通常比“规则”更有区分度；重复堆词不会线性增加价值；同样的词频在长、短 Chunk 中意义不同。

它和 `ts_rank` 都属于 lexical ranking，但不是同一个算法。当前产品明确使用 PostgreSQL 原生 `ts_rank`，公共结果名为 `postgresql_ts_rank`，不能输出成 `bm25_score`。

| 判断 | 结论 |
| --- | --- |
| PostgreSQL FTS 属于 Lexical Retrieval | 正确 |
| 所有 Lexical Retrieval 都是 BM25 | 错误 |
| `ts_rank` 可以直接称作 BM25 | 错误 |
| 以后可以用固定评估比较 BM25 与 `ts_rank` | 可以，但属于新实验 |

本项目 V0 不在 Python 中维护第二套 BM25，也不为名称引入额外数据库扩展。

## 6. 真实代码的责任边界

公共入口是 [`PostgresFTSRetriever`](../../source/packages/rag_core/retrieval/postgres_fts.py)：

```python
retriever.upsert_chunks(chunks)
retriever.search(query, candidate_k=5)
retriever.delete_chunks(chunk_ids)
```

实际调用链：

```text
inspect_lexical_retrieval.main
→ load_document(order_rules.md)
→ chunk_document
→ PostgresFTSRetriever.upsert_chunks
→ 参数化 upsert + transaction
→ PostgresFTSRetriever.search
→ LexicalSearchResult
```

`LexicalHit` 保留 `chunk_id`、文档版本、原文、来源角色、Metadata、命中词和原生 rank。它是候选，不是最终 Context Source，也不是 Citation。

写入链还要守住几个应用不变量：

- `chunk_id`、`document_id`、`document_version` 和来源定位一起保存，不能只写一段文本。
- `lexical_text` 由应用分析器产生，`search_vector` 是数据库生成列，应用不能直接伪造后者。
- 批量 upsert 使用参数化 SQL 和事务；整批成功才提交，中途失败则回滚，不能留下半批 Chunk。
- 重复运行同一 fixture 是幂等更新，不应不断生成新的匿名记录。

核心操作可以概括为：

```text
Chunk[]
→ analyze_document
→ parameterized INSERT ... ON CONFLICT DO UPDATE
→ commit / rollback

query
→ analyze_query
→ parameterized FTS SELECT
→ rows / psycopg.Error
→ LexicalSearchResult / RetrievalError
```

应用代码负责词法策略、Chunk 身份、配置身份、过滤条件、参数绑定和错误映射；PostgreSQL 负责存储、约束、词袋匹配和排序。缺少数据库、表或权限时，代码返回结构化错误，不改用 SQLite、Mock 或 Python 内存检索。

当前错误至少分为：

| code | 含义 | stage 示例 |
| --- | --- | --- |
| `connection_failed` | Server、host、port、Database 或网络不可用 | connection |
| `auth_failed` | Role 或密码错误 | connection |
| `migration_required` | 已连接但目标表不存在 | indexing / query |
| `permission_denied` | Role 无权执行当前动作 | indexing / query / deletion |
| `database_error` | 其他真实 PostgreSQL 错误 | 对应执行阶段 |

成功空结果必须保留 `tsquery` 和 `matched_chunk_count=0`；这些错误不能被转换成空列表。

### Psycopg 和 GUI 的边界

Psycopg 负责建立连接、发送 SQL 与参数、管理事务上下文，以及把 PostgreSQL 错误暴露为 Python 异常。它不决定中文怎样切词、AND 还是 OR、rank 是否代表业务正确性，也不决定哪些来源有证据资格。

GUI 适合观察 Schema、Table、`content`、`lexical_text` 和 `search_vector`，但不能替代 migration、参数化查询、可重复命令和错误契约。实验手册中的窄表 SQL 是观察入口，数据库结构和写入真源仍是 migration 与 package。

## 7. 实验怎么观察

操作命令和环境准备见 [第 11 步实验准备](../../source/demos/rag_retrieval_lab/docs/11-lexical-retrieval.md)。真实入口是 [`inspect_lexical_retrieval.py`](../../source/demos/rag_retrieval_lab/inspect_lexical_retrieval.py)。

实验使用固定 fixture，不代表产品已经提供用户资料管理或后台入库 API。运行前先预测：

| 查询 | 预期观察 |
| --- | --- |
| `source_channel` | 技术标识命中接口规则 |
| `申请售后` | 共同词面产生候选 |
| `发起逆向服务` | 可能成功返回 0 条 |
| `虚拟商品 售后` | 可能命中否定规则，但 rank 不理解否定 |

至少观察三类结果：

1. 命中：能在 `content`、`lexical_text`、`search_vector` 和诊断中找到对应词。
2. 成功空结果：有 `tsquery`，但 `hits=[]`，属于词面边界。
3. 真实依赖失败：`connection_failed`、`auth_failed`、`migration_required` 或 `permission_denied`，不能解释成“资料没有答案”。

建议一次只改变一个变量：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_lexical_retrieval.py --query-operator and --verbose
uv run python source/demos/rag_retrieval_lab/inspect_lexical_retrieval.py --candidate-k 2 --verbose
uv run python source/demos/rag_retrieval_lab/inspect_lexical_retrieval.py --log-format json
```

观察 OR/AND 时比较应用词、PostgreSQL query terms、`tsquery`、命中数和噪声，不要同时改变 fixture、切分策略或停用词。GIN 是否被查询计划选中可以用 `EXPLAIN` 检查；小 fixture 选择顺序扫描可能只是成本选择，不代表索引损坏。

三个典型边界应按不同证据解释：

- 同义改写无结果：依次检查应用词、PostgreSQL 词、`lexical_text`、`search_vector`，确认没有共同词后记录为 lexical 边界。
- 否定规则 rank 高：词面匹配成功，但模型和后续证据逻辑尚未理解否定。
- 数据库不可用：按连接、鉴权、migration、权限顺序排查，不能称为“没有候选”。

## 8. 学完后的修改题

接口新增枚举 `AFTER_SALE_V3`，资料和查询大小写可能不同。修改词法规则和测试，验证：

1. 大小写变化仍得到兼容的分析结果。
2. 技术标识仍被当成一个稳定单位。
3. 配置变化会更新 `lexical_config_ref`。
4. 真实 PostgreSQL 查询仍返回 `postgresql_ts_rank`，不是伪造的 BM25。

## 掌握检查

尝试独立回答：

1. Lexical Retrieval 为什么不能自动理解“逆向服务”和“申请售后”的同义关系？
2. `techidsourcechannel` 从哪里来？
3. token、term、lexeme 为什么要分开？
4. `content`、`lexical_text`、`search_vector` 各自服务什么？
5. `tsquery`、`@@`、`ts_rank` 分别回答什么问题？
6. OR 为什么通常提高召回，也可能引入噪声？
7. 为什么 AND/OR 不需要重建词袋？
8. GIN 加速了什么，又没有解决什么？
9. `ts_rank` 为什么不能叫 BM25，也不能和 cosine distance 直接相加？
10. 词法规则变化后为什么需要重新入库？
11. 成功空结果和 `migration_required` 如何区分？
12. 高 rank 为什么不能直接作为业务证据？

如果能用固定售后资料画出 `Chunk → lexical_text → tsvector → @@ → ts_rank → LexicalHit`，并解释一次 OR/AND、一次自然空结果和一次真实依赖错误，就达到本节机制掌握要求。

## 本节边界

本节建立词面候选、PostgreSQL FTS、GIN、原生 rank 和可诊断错误；不建立 Dense Retrieval、pgvector、RRF、Context、可信 Citation 或产品 Review API。

读完后返回 [标准学习路径](../learning-path.md)，继续第 12 步。

## 官方参考

- [PostgreSQL：Full Text Search](https://www.postgresql.org/docs/current/textsearch.html)
- [PostgreSQL：Text Search Functions and Operators](https://www.postgresql.org/docs/current/functions-textsearch.html)
- [PostgreSQL：GIN Indexes](https://www.postgresql.org/docs/current/gin.html)
- [Psycopg 3：Basic module usage](https://www.psycopg.org/psycopg3/docs/basic/usage.html)
- [jieba：中文分词与搜索引擎模式](https://github.com/fxsjy/jieba)
