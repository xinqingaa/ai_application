# Lexical Retrieval、BM25 边界与 PostgreSQL 全文检索

前面的课程已经把真实资料变成了可回查的 Chunk，也观察了文本怎样进入 Embedding 空间。现在需要第一次回答“怎样从一批 Chunk 中找出候选”。

本节只解决一个核心问题：

> 一个带稳定身份和来源的 Chunk，怎样进入真实 PostgreSQL，变成可检索词项，并根据用户查询形成可解释、可排序、可诊断的 lexical candidates？

本文面向有过 MySQL 或 SQL 经验、但已经遗忘不少语法并且不熟悉 PostgreSQL 的学习者。因此会先恢复本节真正需要的 SQL、表、索引、CRUD、事务、JOIN 和聚合，再进入全文检索；这些基础不会扩展成独立 DBA 课程。

读完后，你应该能够：

- 读懂并修改本节 `rag_chunks` migration。
- 使用 `SELECT`、CRUD、事务、JOIN 和聚合检查检索数据。
- 解释 `tsvector`、`tsquery`、`@@`、GIN 和 `ts_rank` 分别负责什么。
- 解释中文词项和 `source_channel` 等技术标识怎样进入索引。
- 区分字符串包含、候选匹配、候选排序和最终证据判断。
- 说明 PostgreSQL 原生 rank 为什么不能叫 BM25 score。
- 运行真实 PostgreSQL 实验，并根据词项、查询、索引和错误层定位问题。

本文不教授 PostgreSQL 运维、高可用、复制、分区、VACUUM 调优或完整权限体系；不实现 pgvector、Dense Retrieval、RRF、统一阈值和最终 Context。PostgreSQL 安装、环境变量、migration 命令和可选 GUI 统一由 [产品 README](../../review_assistant/README.md#postgresql-本地准备) 维护，正文不复制运行手册。

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

## 用已有 MySQL 经验重新建立 PostgreSQL 地图

### Server、Database、Schema 和 Table

先用四层结构定位对象：

```text
PostgreSQL Server
└── Database: review_assistant
    └── Schema: review_assistant
        └── Table: rag_chunks
```

- **Server** 是正在运行的 PostgreSQL 服务进程。
- **Database** 是一组相互隔离的数据库对象；连接建立时就要选定一个 Database。
- **Schema** 是 Database 内的命名空间。
- **Table** 位于某个 Schema 中。

MySQL 日常使用中的 `database` 经常同时承担 PostgreSQL `database` 与 `schema` 的部分认知，所以刚迁移时容易忽略 Schema。本文始终写全名：

```sql
review_assistant.rag_chunks
```

这里前一个 `review_assistant` 是 Schema，后一个 `rag_chunks` 是 Table。即使 `search_path` 变化，SQL 仍然指向同一对象。

### Role、User 和连接身份

PostgreSQL 使用 Role 表达身份与权限。带登录能力的 Role 可以当作用户使用。应用连接至少要回答：

```text
连接哪台 Server？
连接哪个 Database？
以哪个 Role 登录？
这个 Role 能否使用目标 Schema 和 Table？
```

`DATABASE_URL` 将这些信息组合起来：

```text
postgresql://role:password@host:port/database
```

连接成功只证明身份可以进入 Database，不等于已经执行 migration，也不等于 Role 有目标表的读写权限。因此代码将连接失败、鉴权失败、缺表和权限不足分成不同错误。

### Extension 为什么与普通依赖不同

Python package 安装在应用环境中；PostgreSQL extension 安装在数据库 Server 侧，并且通常还要在每个 Database 中显式启用。

第 11 节使用 PostgreSQL 内置 FTS，不需要额外 extension。第 12 节的 pgvector 会新增 `vector` 类型和向量操作符，因此需要理解：

```sql
CREATE EXTENSION vector;
```

这行 SQL 不是 Python `import`，也不是每次启动应用都执行的普通查询。本文只建立这个边界，不提前实现向量列。

## 用 `rag_chunks` 恢复 SQL 基础

本节所有 SQL 都围绕真实 migration：[`0001_create_rag_chunks.sql`](../../review_assistant/infra/migrations/0001_create_rag_chunks.sql)。先理解关系数据，再理解全文搜索类型。

### 表、行、列和约束

表可以先理解为一组满足同一结构约束的行：

| 列 | 一行中表达什么 |
| --- | --- |
| `chunk_id` | Chunk 的稳定身份 |
| `document_id` / `document_version` | 属于哪个业务文档版本 |
| `content` | 可回查原文 |
| `source_role` | 现行参考知识还是历史材料 |
| `business_metadata` | `knowledge_scope` 等业务过滤字段 |
| `lexical_text` | 词法分析后的派生文本 |
| `lexical_config_ref` | 产生词项的完整策略身份 |
| `search_vector` | PostgreSQL 生成的全文检索表示 |

建表语句的最小骨架是：

```sql
CREATE TABLE review_assistant.rag_chunks (
    chunk_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    content TEXT NOT NULL
);
```

三个关键词承担不同契约：

- `TEXT` 是列的数据类型。
- `NOT NULL` 禁止缺失值。
- `PRIMARY KEY` 同时要求唯一且非空，并建立用于身份查找的唯一索引。

`PRIMARY KEY` 不是“第一列”的装饰。它说明每一行如何被稳定识别。当前项目已经在 Chunking 阶段生成稳定 `chunk_id`，数据库不能再用自增 ID 替代它，否则入库前后的知识身份会断裂。

migration 还有这样的检查约束：

```sql
token_count INTEGER NOT NULL CHECK (token_count > 0)
```

它让无效状态无法进入表。应用侧校验能提前给出友好错误，数据库约束则守住所有写入路径；两者不是重复浪费。

### `NULL` 不是空字符串

SQL 中 `NULL` 表示未知或缺失，不等于 `''`、`0` 或 `false`。判断时不能写：

```sql
parent_chunk_id = NULL
```

正确写法是：

```sql
parent_chunk_id IS NULL
parent_chunk_id IS NOT NULL
```

本节允许独立 Chunk 的 `parent_chunk_id` 为 `NULL`，但不允许 `content` 或 `lexical_text` 为空。是否允许空值必须来自业务语义，而不是统一禁止或统一放开。

### `SELECT`：读取你真正需要的列

读取接口约束 Chunk：

```sql
SELECT chunk_id, document_id, content
FROM review_assistant.rag_chunks
WHERE content LIKE '%source_channel%'
ORDER BY chunk_id ASC
LIMIT 10;
```

执行顺序可以先这样理解：

1. `FROM` 确定数据来源。
2. `WHERE` 过滤行。
3. `SELECT` 决定输出列。
4. `ORDER BY` 决定顺序。
5. `LIMIT` 截取数量。

不要长期依赖 `SELECT *`。当表在第 12 节增加大向量列时，读取全部列会带来不必要的数据传输，也让调用者无意依赖表的全部结构。

`LIKE '%source_channel%'` 能用于快速检查原文是否含有字符串，但它不是完整 Lexical Retrieval：它没有统一词法分析、`tsquery`、倒排候选和相关性排序。

### `INSERT`：创建一行

最小插入形式是：

```sql
INSERT INTO review_assistant.rag_chunks (
    chunk_id,
    document_id,
    document_version,
    content
) VALUES (
    'chunk-001',
    'KR-ORDER-STATE',
    '1.0.0',
    '售后接口 v2 必须提供 source_channel。'
);
```

真实表还有其他必填字段，因此这段教学缩写不能直接通过当前 migration。真实写入由 [`PostgresFTSRetriever.upsert_chunks`](../../source/packages/rag_core/retrieval/postgres_fts.py) 完成。

应用代码不能把用户输入直接拼进 SQL：

```python
# 错误方向：query 可以改变 SQL 结构
sql = f"SELECT * FROM chunks WHERE content = '{query}'"
```

真实实现使用 Psycopg 命名参数：

```python
connection.execute(sql, {"query": query})
```

参数绑定负责把“SQL 结构”和“数据值”分开，既避免引号转义错误，也防止 SQL injection。表名、列名等 SQL 标识符不能作为普通值参数传入；本项目表名固定在受控 SQL 中，不接受用户动态指定。

### `UPDATE`：修改已有行

普通更新：

```sql
UPDATE review_assistant.rag_chunks
SET content = '新的规则文本',
    updated_at = CURRENT_TIMESTAMP
WHERE chunk_id = 'chunk-001';
```

最危险的遗忘是漏掉 `WHERE`，这会更新整张表。因此修改前可以先用同一条件 `SELECT`，事务中修改后再检查影响行数。

当前代码不单独发 `UPDATE`，而使用 upsert：

```sql
INSERT INTO ...
ON CONFLICT (chunk_id) DO UPDATE SET
    content = EXCLUDED.content,
    lexical_text = EXCLUDED.lexical_text,
    lexical_config_ref = EXCLUDED.lexical_config_ref;
```

含义是：主键不存在时插入，主键已存在时用本轮值更新。重复运行同一 fixture 不会无限复制行。

### `DELETE`：删除而不是清空字段

按稳定 ID 删除：

```sql
DELETE FROM review_assistant.rag_chunks
WHERE chunk_id = 'chunk-001';
```

删除文档版本时需要显式使用复合条件：

```sql
DELETE FROM review_assistant.rag_chunks
WHERE document_id = 'KR-ORDER-STATE'
  AND document_version = '1.0.0';
```

`DELETE` 删除行；`UPDATE content = ''` 只是把字段改为空，而且会违反当前表约束。真实的知识更新、旧版本清理和 Citation 失效要到知识生命周期课程继续处理，本节只建立 CRUD 语义。

### 事务：一组操作要么一起成功，要么一起失败

事务的最小形态：

```sql
BEGIN;

INSERT INTO ...;
UPDATE ...;

COMMIT;
```

如果中间检查发现问题：

```sql
ROLLBACK;
```

本节批量写入多个 Chunk 时，不应该出现“前三条已经提交、第四条失败、数据库只剩半个文档”的状态。Psycopg connection context 承担事务边界：

```python
with psycopg.connect(dsn) as connection:
    with connection.cursor() as cursor:
        cursor.executemany(sql, rows)
```

- 代码块正常结束时提交。
- 抛出异常时回滚。
- 退出后关闭连接。

事务不能修复错误词法策略，也不能保证检索质量；它只保证这一组数据库写入的原子性。

### 索引：用额外存储换取特定查询速度

没有索引时，数据库可能逐行检查；有合适索引时，可以先定位较小的候选范围。索引不是越多越好：

- 会占用存储。
- 写入时还要维护索引。
- 只对匹配的查询形态有效。
- 查询规划器仍会根据数据量和成本决定是否使用。

当前 migration 有三类索引：

```sql
-- PRIMARY KEY 隐含的 B-tree 唯一索引
PRIMARY KEY (chunk_id)

-- 文档版本定位使用 B-tree
CREATE INDEX ... ON ... (document_id, document_version);

-- 全文词项包含关系使用 GIN
CREATE INDEX ... ON ... USING GIN (search_vector);
```

B-tree 适合等值、范围和有序定位；GIN 适合一个复合值中包含哪些 key，例如一个 `tsvector` 包含哪些 lexeme。GIN 加速 `@@` 匹配，不自动产生更好的 rank，也不理解同义词。

小型 fixture 只有几行时，`EXPLAIN` 可能显示顺序扫描，因为直接读几行比走索引更便宜。不能通过强制关闭顺序扫描伪装“索引已经在真实规模上证明收益”。

### JOIN：把相关表按条件组合

当前步骤只需要一张真实表，但必须恢复 JOIN 心智模型，因为后续运行记录、文档版本和评估 Case 不会永远塞进 `rag_chunks`。

假设未来有文档表：

```text
knowledge_documents(document_id, document_version, title)
rag_chunks(chunk_id, document_id, document_version, content)
```

查出 Chunk 及文档标题：

```sql
SELECT
    chunk.chunk_id,
    document.title,
    chunk.content
FROM review_assistant.rag_chunks AS chunk
JOIN review_assistant.knowledge_documents AS document
  ON document.document_id = chunk.document_id
 AND document.document_version = chunk.document_version;
```

JOIN 的关键不是背 `JOIN` 单词，而是确认关联条件完整。这里只按 `document_id` 连接会把不同版本交叉组合，形成错误来源。

常见语义：

- `INNER JOIN`：两侧都存在才返回。
- `LEFT JOIN`：保留左表行，右表没有时对应列为 `NULL`。

本节 migration 没有为了讲 JOIN 创建无业务需要的第二张表；上例只用于恢复关系判断，不冒充当前实现。

### 聚合：把多行压缩成统计事实

统计每个文档版本有多少 Chunk：

```sql
SELECT
    document_id,
    document_version,
    COUNT(*) AS chunk_count,
    AVG(token_count) AS average_tokens,
    MAX(token_count) AS max_tokens
FROM review_assistant.rag_chunks
GROUP BY document_id, document_version
ORDER BY document_id, document_version;
```

- `COUNT`、`AVG`、`MAX` 是聚合函数。
- `GROUP BY` 定义哪些行属于同一组。
- `SELECT` 中没有被聚合的普通列通常必须出现在 `GROUP BY`。

只保留 Chunk 数量大于 2 的文档：

```sql
SELECT document_id, document_version, COUNT(*) AS chunk_count
FROM review_assistant.rag_chunks
GROUP BY document_id, document_version
HAVING COUNT(*) > 2;
```

`WHERE` 在分组前过滤单行，`HAVING` 在分组后过滤聚合结果。聚合可以诊断数据分布，但平均 Chunk 长度不能证明检索质量。

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

下一节 Dense Retrieval 会在同一问题上观察语义表示是否补回候选；最终收益仍需固定评估证明。

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

1. PostgreSQL Database 与 Schema 有什么区别？
2. 为什么应用 Role 不应该直接使用超级用户？
3. `PRIMARY KEY` 在本表中守住什么业务身份？
4. `NULL` 与空字符串有什么区别？
5. `WHERE` 和 `HAVING` 分别在哪个阶段过滤？
6. 为什么 JOIN 文档版本时不能只连接 `document_id`？
7. upsert 与普通 `UPDATE` 有什么区别？
8. Psycopg connection context 怎样处理 commit 和 rollback？
9. B-tree 与 GIN 分别服务哪类查询？
10. `lexical_text`、`tsvector` 和原文为什么要同时存在？
11. `tsquery` 与 `@@` 分别做什么？
12. OR 为什么提高召回，也可能增加噪声？
13. `ts_rank` 的值能否与 cosine similarity 直接相加？
14. PostgreSQL `ts_rank_cd` 为什么不能叫 BM25？
15. 同义改写无结果时，怎样证明这是词面边界而不是数据库失败？
16. 为什么高 rank 不能直接当作证据充分？
17. 词法配置变化后为什么需要重新入库？
18. 数据库连接失败时为什么不能返回空候选？

如果你能画出完整数据流、读懂 migration、运行真实实验、解释 OR/AND 变化，并能完成技术标识修改题，就已经达到本节需要的 PostgreSQL 与 Lexical Retrieval 掌握程度。

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
