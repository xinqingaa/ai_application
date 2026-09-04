# PostgreSQL 零基础：读懂 AI 应用中的项目数据库

> 这是一篇不占课程序号的必备基础补充。如果你在 Lexical Retrieval 中遇到 Database、Schema、Table、SQL、事务、索引或 migration 等陌生概念，可以先用本文补齐，再按 [Lexical Retrieval 实验](011.lexical-retrieval.lab.md) 完成环境操作，最后回到机制篇。

很多前端或客户端应用只需要调用远程 API，数据怎样落盘、怎样约束、怎样被多个请求安全地读写，通常由服务端隐藏。需求评审助手开始建立真实知识库后，这层不能再完全隐藏：Chunk 要长期保存，重复入库不能产生无穷副本，检索要在大量记录中形成候选，连接和权限失败也不能伪装成“没有结果”。

本文只回答一个问题：

> 一个完全没有数据库基础的应用开发者，需要建立哪些 PostgreSQL 心智模型，才能读懂本项目的表、migration 和 Python 数据访问代码，并安全完成日常查询与排查？

先建立本项目的对象关系：

```text
PostgreSQL Server
└── Database: review_assistant
    └── Schema: review_assistant
        └── Table: rag_chunks
            ├── content / Metadata / chunk_id
            ├── FTS: lexical_text → generated tsvector + GIN
            └── Dense: pgvector extension → vector + distance/index
```

这里的 PostgreSQL 是关系数据库；全文检索是它内置的 FTS 能力；`pgvector` 是安装在 PostgreSQL 中的扩展，不是另一个独立数据库。Lexical Retrieval 只需要 FTS，Dense Retrieval 才启用 pgvector。

读完后，你应该能够：

- 解释 PostgreSQL、关系数据库、表、行和列分别是什么。
- 找到 Server、Database、Schema、Table 与 Role 在一次连接中的位置。
- 读懂本项目 migration 中常见的数据类型、主键、非空和检查约束。
- 使用基本 `SELECT`、`INSERT`、`UPDATE`、`DELETE`、JOIN 和聚合表达数据操作。
- 解释 upsert、事务、索引、migration 和参数绑定为什么存在。
- 看懂 Psycopg 怎样把 Python 数据交给 PostgreSQL，并区分连接失败、鉴权失败、缺表、权限不足与成功空结果。
- 知道什么时候应该回到数据库基础排查，什么时候问题其实属于全文检索、向量检索或证据判断。

本文不会把你训练成 DBA，也不展开高可用、复制、备份恢复、分区、锁竞争、隔离级别调优、执行器实现或大规模性能治理。PostgreSQL 的安装、环境变量、migration 命令和可选 GUI 由[产品 README](../../source/apps/review_assistant/README.md#postgresql-本地准备)维护；固定资料入库和查询由[实验篇](011.lexical-retrieval.lab.md)维护。本文解释概念，不复制运行手册。

## 先理解数据库在应用里解决什么

假设 Python 程序已经得到三个 Chunk：

```text
chunk-001：仅已支付且已完成的订单可申请售后。
chunk-002：虚拟商品不进入售后流程。
chunk-003：售后接口 v2 必须提供 source_channel。
```

把它们放进一个 Python 列表可以完成一次临时实验，但程序退出后列表消失；启动两个 API 进程时，它们也不会天然共享同一个列表。应用还需要回答：

- 下一次启动怎样找回这些 Chunk？
- 怎样保证同一个 `chunk_id` 只代表一条记录？
- 多个写入动作中途失败时，怎样避免只保存一半？
- 怎样只读取满足条件的行，而不是每次把全部数据搬回 Python？
- 怎样让不同应用进程看到同一份已提交数据？
- 怎样限制应用身份能做什么，并让失败原因可观察？

数据库是专门管理持久数据的软件系统。它接收结构化读写请求，按照预先定义的结构和约束保存数据，再返回查询结果或明确错误。

可以先把最小数据流记成：

```text
应用中的对象
→ SQL + 参数
→ PostgreSQL 校验、读写和提交
→ 行集合或数据库错误
→ 应用重新组装为业务对象
```

PostgreSQL 是一个关系数据库管理系统。这里的“关系”不是泛指两件事有关，而是数据主要以具有明确列定义的表来组织，表与表之间可以通过共同身份建立关联。

数据库能够可靠保存和查询数据，但不会自动理解业务语义。它可以保证 `chunk_id` 唯一，却不能判断一个 Chunk 是否足以支持某条风险结论；可以执行全文匹配，却不能自动理解否定、例外和资料有效期。

## 从表格直觉进入关系模型

第一次接触关系数据库时，可以先把 Table 想成一个受到严格约束的表格：

```text
rag_chunks
┌───────────┬─────────────────┬──────────┬────────────────────┐
│ chunk_id  │ document_id     │ ordinal  │ content            │
├───────────┼─────────────────┼──────────┼────────────────────┤
│ chunk-001 │ KR-ORDER-STATE  │ 1        │ 仅已支付且已完成…  │
│ chunk-002 │ KR-ORDER-STATE  │ 2        │ 虚拟商品不进入…    │
└───────────┴─────────────────┴──────────┴────────────────────┘
```

- **Table** 定义一类数据采用什么结构。
- **Column** 定义一个字段的名称、类型和约束。
- **Row** 是一条符合该结构的记录。
- **Cell** 是某行某列的一个值，但 SQL 通常围绕行和列思考，而不是围绕界面单元格思考。

表与普通电子表格仍有重要区别：

- 数据类型和约束由数据库执行，不只是表头提示。
- 查询不依赖肉眼筛选，而由 SQL 描述需要哪些行和列。
- 多个客户端可以连接同一个数据库，并通过事务看到一致的已提交结果。
- 索引、权限、查询计划和错误都属于数据库运行行为。

关系模型鼓励把身份、事实和关联明确表达出来。它不要求把任何信息都拆成很多表，也不禁止 JSON；真正的判断是哪些字段需要稳定约束、过滤、关联和索引，哪些内容更适合保留为灵活结构。

## 一次 PostgreSQL 连接会经过哪些对象

先用下面的层级定位项目对象：

```text
PostgreSQL Server
└── Database: review_assistant
    └── Schema: review_assistant
        └── Table: rag_chunks
```

### Server：实际运行的数据库服务

Server 是正在运行并监听连接的 PostgreSQL 服务。应用连接的 host 和 port 用来找到它。本地 Server 没有启动、地址错误或网络不可达时，请求还没有进入任何业务表，通常会表现为连接失败。

### Database：连接时选择的数据集合

一个 Server 可以管理多个 Database。建立连接时必须选定其中一个；普通 SQL 不会跨 Database 随意 JOIN。项目把学习数据库和测试数据库分开，是为了避免集成测试误操作日常学习数据。

### Schema：Database 内的命名空间

Schema 用来在一个 Database 内组织和隔离对象。项目使用完整表名：

```sql
review_assistant.rag_chunks
```

前半部分 `review_assistant` 是 Schema，后半部分 `rag_chunks` 是 Table。始终写全名可以减少 `search_path` 变化带来的歧义。

### Table：保存同一结构的记录

Table 位于 Schema 中。当前 migration 只创建真实需要的 `rag_chunks`，没有为了教学提前创建文档表、运行表或评估表。

### Role：连接身份与权限

PostgreSQL 使用 Role 表达身份和权限。拥有登录能力的 Role 可以作为应用用户使用。一次应用连接至少要回答：

```text
连接哪台 Server？
进入哪个 Database？
以哪个 Role 登录？
这个 Role 能否访问目标 Schema 和 Table？
```

连接 URL 把这些信息组合起来：

```text
postgresql://role:password@host:port/database
```

连接成功只说明应用已经进入目标 Database，不说明 migration 已经执行，也不说明当前 Role 对目标表拥有读写权限。应用不应长期使用超级用户；最小权限能减少配置错误或代码缺陷的影响范围。

## 用真实 migration 认识列、类型和约束

本项目当前表结构的真源是 [`0001_create_rag_chunks.sql`](../../source/apps/review_assistant/infra/migrations/0001_create_rag_chunks.sql)。migration 中的一部分可以简化为：

```sql
CREATE TABLE review_assistant.rag_chunks (
    chunk_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL CHECK (ordinal > 0),
    content TEXT NOT NULL CHECK (length(btrim(content)) > 0),
    business_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    search_vector TSVECTOR GENERATED ALWAYS AS (...) STORED,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

这段定义同时表达了数据形状和不允许出现的状态。

### 当前项目会遇到的数据类型

| 类型 | 保存什么 | 项目示例 |
| --- | --- | --- |
| `TEXT` | 可变长度文本 | ID、原文、配置引用 |
| `INTEGER` | 整数 | Chunk 顺序、Token 数量 |
| `JSONB` | 可查询的 JSON 二进制表示 | 来源跨度、业务 Metadata |
| `TIMESTAMPTZ` | 带时区语义的时间点 | 创建、更新时间 |
| `TSVECTOR` | PostgreSQL 全文检索词项表示 | `search_vector` |

类型不是为了让表结构看起来正式。它决定数据库允许什么值、支持什么运算，以及驱动怎样把结果转换回 Python。

`JSONB` 适合结构可能扩展、但仍需作为一个整体跟随 Chunk 保存的 Metadata。它不表示所有字段都应该塞进 JSON：需要稳定唯一性、频繁过滤、排序或关联的核心身份仍应成为明确列。

### 主键：一行怎样被稳定识别

```sql
chunk_id TEXT PRIMARY KEY
```

`PRIMARY KEY` 要求值唯一且非空，并建立支持身份查找的唯一索引。它不是“第一列”的装饰，而是在回答：数据库用什么区分两行。

当前项目已经在 Chunking 阶段生成稳定 `chunk_id`。数据库不能用一个新的自增数字替代业务身份，否则入库前后的 Chunk、来源与后续 Citation Candidate 会失去稳定关联。

### 非空、默认值和检查约束

```sql
document_id TEXT NOT NULL
ordinal INTEGER NOT NULL CHECK (ordinal > 0)
business_metadata JSONB NOT NULL DEFAULT '{}'::jsonb
```

- `NOT NULL`：这一列不能缺失。
- `DEFAULT`：写入时没有提供值，由数据库补入默认值。
- `CHECK`：值还必须满足额外条件。

应用侧校验可以更早返回友好错误，数据库约束则保护所有写入路径。两层校验承担的位置不同，不是无意义重复。

### 外键：一行怎样引用另一行

如果未来出现文档表：

```text
knowledge_documents(document_id, document_version, title)
rag_chunks(chunk_id, document_id, document_version, content)
```

`rag_chunks` 可以用外键要求它引用的文档版本真实存在。外键约束的是引用完整性，不自动决定删除文档时应该禁止、级联还是保留历史。

当前 migration 尚未创建独立文档表，因此没有为了讲解而加入虚假的外键。理解外键是为了以后读懂真实关系，而不是假装当前项目已经实现知识生命周期。

## `NULL` 表示缺失，不是空字符串

SQL 中 `NULL` 表示未知或缺失，不等于 `''`、`0` 或 `false`。

判断 `NULL` 不能写：

```sql
parent_chunk_id = NULL
```

应写成：

```sql
parent_chunk_id IS NULL
parent_chunk_id IS NOT NULL
```

当前项目允许独立 Chunk 的 `parent_chunk_id` 为 `NULL`，因为它确实没有父 Chunk；但不允许 `content` 为空。是否允许缺失应来自字段语义，而不是统一禁止或统一放开。

常见误区是把所有空白状态都存成空字符串。这会让“未知”“不适用”“确实是空文本”混成同一个值，也会使查询和约束更难解释。

## SQL 是应用向数据库表达意图的语言

SQL 描述“想取得或改变什么”，数据库负责验证并执行。先掌握项目中最常见的四类动作即可。

### `SELECT`：读取需要的行和列

```sql
SELECT chunk_id, document_id, content
FROM review_assistant.rag_chunks
WHERE document_id = 'KR-ORDER-STATE'
ORDER BY chunk_id ASC
LIMIT 10;
```

可以先按这个逻辑理解：

1. `FROM`：数据来自哪张表。
2. `WHERE`：哪些行符合条件。
3. `SELECT`：结果需要哪些列。
4. `ORDER BY`：结果怎样排序。
5. `LIMIT`：最多返回多少行。

不要长期依赖 `SELECT *`。调用者应明确需要什么；表以后增加大字段时，读取全部列会增加传输，也会形成不必要的结构依赖。

字符串包含查询：

```sql
SELECT chunk_id, content
FROM review_assistant.rag_chunks
WHERE content LIKE '%source_channel%';
```

它适合确认原文是否包含某段字符串，但不等于完整全文检索。它没有统一词法表示、倒排候选和相关性排序。

### `INSERT`：创建新行

教学上的最小形式是：

```sql
INSERT INTO example_chunks (chunk_id, content)
VALUES ('chunk-001', '售后接口必须提供 source_channel。');
```

真实 `rag_chunks` 还有其他必填字段，实际写入由 [`PostgresFTSRetriever.upsert_chunks`](../../source/packages/rag_core/retrieval/postgres_fts.py) 完成。读 SQL 时要同时检查列清单和值或参数清单是否一一对应。

### `UPDATE`：修改已有行

```sql
UPDATE review_assistant.rag_chunks
SET content = '新的规则文本',
    updated_at = CURRENT_TIMESTAMP
WHERE chunk_id = 'chunk-001';
```

忘记 `WHERE` 会修改整张表。安全习惯是先用同一条件执行 `SELECT`，确认目标行，再在事务中修改并检查影响行数。

### `DELETE`：删除行

```sql
DELETE FROM review_assistant.rag_chunks
WHERE chunk_id = 'chunk-001';
```

`DELETE` 删除行；`UPDATE content = ''` 只是把字段变成空字符串，而且会违反当前内容约束。删除是否允许、是否同时清理关联记录、旧 Citation 是否失效，属于知识生命周期设计，不由一条 `DELETE` 自动决定。

### Upsert：不存在就插入，存在就更新

项目需要重复运行同一 fixture，而不能每次复制一批 Chunk。真实写入采用：

```sql
INSERT INTO ...
ON CONFLICT (chunk_id) DO UPDATE SET
    content = EXCLUDED.content,
    lexical_text = EXCLUDED.lexical_text,
    lexical_config_ref = EXCLUDED.lexical_config_ref;
```

当主键不存在时插入；当 `chunk_id` 已存在时，用本轮数据更新指定列。Upsert 解决的是明确冲突键下的重复写入行为，不代表所有写操作都天然幂等：如果业务身份选错，稳定地覆盖错误行同样是错误。

## JOIN：根据完整身份组合不同表

当数据职责增加时，所有字段不应该永远堆在一张表里。假设以后真实存在：

```text
knowledge_documents(document_id, document_version, title)
rag_chunks(chunk_id, document_id, document_version, content)
```

读取 Chunk 及对应文档标题：

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

JOIN 的关键不是背语法，而是确认关联身份完整。这里只按 `document_id` 连接，会把不同版本交叉组合，产生错误来源。

- `INNER JOIN`：两侧都存在匹配行才返回。
- `LEFT JOIN`：保留左侧行；右侧没有匹配时，对应列为 `NULL`。

这两张表的关系只是用于建立心智模型；当前项目尚未落地 `knowledge_documents` 表，不能把示例当作已实现能力。

## 聚合：把多行压缩为统计结果

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
- `GROUP BY` 决定哪些行属于同一组。
- 没有被聚合的普通输出列通常必须出现在 `GROUP BY` 中。

只保留 Chunk 数量大于 2 的分组：

```sql
SELECT document_id, document_version, COUNT(*) AS chunk_count
FROM review_assistant.rag_chunks
GROUP BY document_id, document_version
HAVING COUNT(*) > 2;
```

`WHERE` 在分组前过滤单行，`HAVING` 在分组后过滤聚合结果。聚合能帮助观察数据分布，但平均 Chunk 长度不能证明检索质量。

## 事务：让一组写入形成一个结果

事务的最小形式是：

```sql
BEGIN;

INSERT INTO ...;
UPDATE ...;

COMMIT;
```

如果中途发现问题：

```sql
ROLLBACK;
```

- `COMMIT` 让本次事务的修改正式提交。
- `ROLLBACK` 撤销当前事务尚未提交的修改。
- 一个事务中的操作要么共同形成已提交结果，要么在失败时共同回滚，这就是当前最需要理解的原子性。

本项目批量写入多个 Chunk 时，不应该出现“前三条已经提交、第四条失败、数据库只剩半份文档”。Psycopg 的 connection context 承担这一事务边界：

```python
with psycopg.connect(dsn) as connection:
    with connection.cursor() as cursor:
        cursor.executemany(sql, rows)
```

- 代码块正常结束时提交。
- 抛出异常时回滚。
- 退出后关闭连接。

事务不能修复错误的 Chunk、词法策略或业务身份，也不能证明检索质量。它只保证这组数据库修改以怎样的整体状态出现。

真实系统还会遇到并发修改、锁和隔离级别，但在当前项目代码没有出现对应问题前，不需要先展开完整并发控制课程。

## 索引：为特定查询建立更快的入口

没有合适索引时，数据库可能逐行检查；有合适索引时，可以先定位较小的候选范围。索引用额外存储和写入维护成本换取特定查询形态的读取效率。

索引不是越多越好：

- 每个索引都会占用空间。
- 插入和更新数据时还要同步维护索引。
- 一个索引只对匹配的查询条件和运算类型有用。
- 查询规划器仍会根据数据量与成本决定是否使用它。

当前 migration 中可以看到：

```sql
-- 主键隐含的 B-tree 唯一索引
PRIMARY KEY (chunk_id)

-- 文档版本定位使用 B-tree
CREATE INDEX ... ON ... (document_id, document_version);

-- 全文词项包含关系使用 GIN
CREATE INDEX ... ON ... USING GIN (search_vector);
```

- B-tree 常用于等值、范围和有序定位。
- GIN 适合查询一个复合值包含哪些 key；在这里是 `tsvector` 包含哪些 lexeme。

GIN 加速符合形态的全文匹配，不负责生成更好的 rank，也不理解同义词和否定关系。

`EXPLAIN` 可以显示数据库准备采用的查询计划。小型 fixture 只有几行时，顺序扫描可能比走索引更便宜，因此“计划没有使用索引”不自动等于索引坏了。是否有性能收益要用有代表性的数据量和独立性能实验验证。

## Migration：让表结构变化可以重复执行和追踪

数据库结构也会随产品演进：新增表、列、约束或索引，修改已有类型，启用扩展。这些变化不能依靠某个人在 GUI 中临时点击后口头通知其他人。

Migration 是受版本控制的数据库结构变更。项目当前使用编号原生 SQL：

```text
source/apps/review_assistant/infra/migrations/0001_create_rag_chunks.sql
```

它的责任是：

- 明确要创建或修改哪些数据库对象。
- 让新环境能够按相同方式建立结构。
- 让应用代码与预期表结构具有可追踪关系。
- 执行失败时清晰停止，而不是假装表已经可用。

“应用能连接 Database”与“目标 migration 已完成”是两件事。当前代码收到 `UndefinedTable` 时返回 `migration_required`，就是为了保留这层区别。

本文不展开复杂 migration 工具、在线无锁变更或回滚策略；当前先能读懂并执行项目真实 migration。

## Extension：安装在 PostgreSQL 里的能力

Python package 安装在应用运行环境；PostgreSQL Extension 安装在数据库 Server 一侧，并且通常还要在目标 Database 中显式启用。

```sql
CREATE EXTENSION vector;
```

这不是 Python `import`，也不是每次业务查询都执行的语句。Lexical Retrieval 使用 PostgreSQL 内置全文检索，不需要额外 Extension；后续 pgvector 会增加 `vector` 类型和向量运算符。

Extension 能增加数据库类型、函数或索引能力，但不会替应用解决 Embedding 空间身份、重建策略、检索质量和证据判断。

## 参数绑定：把 SQL 结构与外部数据分开

不要把用户或文件内容直接拼进 SQL：

```python
# 错误方向：query 可以改变 SQL 结构
sql = f"SELECT * FROM chunks WHERE content = '{query}'"
```

引号、转义字符和恶意输入都可能改变语句含义。真实实现使用 Psycopg 参数：

```python
connection.execute(sql, {"query": query})
```

参数绑定负责把固定 SQL 结构和动态数据值分开。它既避免手工转义错误，也防止数据被当作 SQL 指令执行。

表名、列名和排序方向等 SQL 结构不能作为普通值参数传入。当前项目的 Schema、Table 和列名写在受控 SQL 中，不允许用户动态指定。

参数化查询解决的是安全传值，不会自动保证：

- 业务条件正确。
- 查询具有合适索引。
- 返回结果足以支持业务结论。
- 当前 Role 拥有执行权限。

## Psycopg 在 Python 与 PostgreSQL 之间负责什么

Psycopg 是 Python 的 PostgreSQL 驱动。它主要负责：

- 建立和关闭连接。
- 发送 SQL 与参数。
- 适配常见 Python/PostgreSQL 类型。
- 管理 cursor 和 transaction context。
- 将 PostgreSQL 错误暴露为 Python 异常。

它不负责决定：

- Chunk 身份和文档版本。
- 应该保存哪些业务字段。
- 哪些来源有证据资格。
- 全文检索怎样分词和排序。
- 数据库错误应该怎样成为产品错误契约。

当前 [`PostgresFTSRetriever`](../../source/packages/rag_core/retrieval/postgres_fts.py) 把这些责任组合成三个公共动作：

```python
retriever.upsert_chunks(chunks)
retriever.search(query, candidate_k=5)
retriever.delete_chunks(chunk_ids)
```

读取代码时可以沿着下面的数据流：

```text
Chunk / query
→ Python 校验与词法分析
→ 参数化 SQL
→ PostgreSQL 约束、事务、匹配和排序
→ 行结果或 psycopg.Error
→ LexicalSearchResult 或 RetrievalError
```

这里最重要的边界是：驱动让 Python 能够调用 PostgreSQL，但数据库契约和业务契约仍由应用显式建立。

## 五类数据库结果不要混为一谈

| 表现 | 说明 | 优先检查 |
| --- | --- | --- |
| 无法建立连接 | 请求没有进入目标 Database | Server、host、port、database、网络 |
| 鉴权失败 | Role 或密码不被接受 | Role、密码、连接 URL 编码 |
| 缺少目标表 | 已连接，但预期 migration 未完成 | 当前 Database、migration 执行结果 |
| 权限不足 | 身份存在，但无权执行当前动作 | Schema/Table owner 与 Role 权限 |
| 查询成功但返回零行 | SQL 已成功执行，没有行满足条件 | 查询条件、当前数据和检索表示 |

成功空结果不是数据库故障；连接失败也不能被转换成空列表。否则上层会把“系统不可用”误判成“资料里没有答案”。

数据库报错也不自动等于 PostgreSQL 本身有缺陷。错误可能来自地址、身份、权限、未执行 migration、违反约束或应用生成了错误 SQL。排查时先确定失败层，再决定改配置、结构、数据还是代码。

## PostgreSQL 基础与检索机制的边界

掌握数据库基础后，还不能直接声称已经完成 RAG。几层能力必须分开：

| 层次 | 回答的问题 |
| --- | --- |
| 关系存储与 SQL | 数据怎样可靠保存、约束、读取和修改？ |
| PostgreSQL FTS | 哪些记录具有共同词项，怎样形成 lexical 排名？ |
| pgvector Dense Retrieval | 哪些向量在同一空间里更接近？ |
| RRF 与过滤 | 多路候选怎样融合、过滤和诊断？ |
| Context 与证据校验 | 哪些候选真正进入模型并支持最终结论？ |

反例：某个 Chunk 在 PostgreSQL 中成功写入、有合法主键，并且全文 rank 很高。这只能说明存储、约束和当前词项排序完成了各自工作，不能证明这条资料是现行版本，也不能证明它支持最终风险结论。

数据库是可信应用的基础设施之一，不是业务正确性的自动证明器。

## 在需求评审助手中需要达到什么程度

本项目要求的是应用开发所需的 PostgreSQL 所有权，而不是数据库专家能力。你应该能够：

1. 打开真实 migration，指出表、列、类型、主键、约束和索引。
2. 看懂连接 URL 中各部分对应什么，并知道密码不能进入代码或 Git。
3. 用 `SELECT` 检查目标行和派生字段，不依赖 GUI 猜测。
4. 阅读参数化写入、upsert、查询和删除 SQL。
5. 解释批量写入为什么需要事务。
6. 区分 B-tree、GIN 和后续向量索引服务的查询类型。
7. 区分成功空结果、连接失败、鉴权失败、缺表和权限不足。
8. 知道 PostgreSQL 不能替应用完成词法策略、Embedding 身份、证据判断和评估。

从空库到第一次按词查询，按照 [实验篇](011.lexical-retrieval.lab.md) 操作。产品级两条 migration、测试库和 pgvector 见 [产品 README 的 PostgreSQL 本地准备](../../source/apps/review_assistant/README.md#postgresql-本地准备)。命令、参数和排障以这些文档为真源。

## 掌握检查

不看正文，尝试回答：

1. Python 列表与 PostgreSQL 持久存储分别解决什么问题？
2. Server、Database、Schema 和 Table 是什么层级关系？
3. Role 在一次连接中负责什么？连接成功为什么不等于表已经存在？
4. Table、Row、Column、数据类型和约束分别表达什么？
5. `PRIMARY KEY` 为什么不是“第一列”的装饰？
6. `NULL` 与空字符串有什么区别？
7. `SELECT`、`INSERT`、`UPDATE` 和 `DELETE` 分别改变什么？
8. Upsert 解决什么问题？为什么它不自动保证业务幂等？
9. JOIN 时为什么必须使用完整业务身份？
10. `WHERE` 和 `HAVING` 分别在哪个阶段过滤？
11. 事务怎样避免批量写入只完成一半？
12. 索引为什么不是越多越好？B-tree 与 GIN 当前分别服务什么查询？
13. Migration 与普通业务查询有什么区别？
14. PostgreSQL Extension 为什么不是 Python package？
15. 参数绑定解决什么问题？哪些 SQL 结构不能作为普通值参数传入？
16. Psycopg 封装了什么，又没有替应用决定什么？
17. 怎样区分连接失败、鉴权失败、缺表、权限不足和成功空结果？
18. 为什么“成功写入并得到高 rank”仍不能证明最终评审结论正确？

如果这些问题大部分能够独立回答，就已经具备本项目当前需要的 PostgreSQL 基础。操作仍走 [实验篇](011.lexical-retrieval.lab.md)，概念补齐后回到 [机制正文](011.lexical-retrieval.mechanism.md)；标准课程顺序仍只由 [学习路径](../learning-path.md) 维护。

## 官方参考

- [PostgreSQL：Getting Started](https://www.postgresql.org/docs/current/tutorial-start.html)
- [PostgreSQL：The SQL Language](https://www.postgresql.org/docs/current/tutorial-sql.html)
- [PostgreSQL：Data Definition](https://www.postgresql.org/docs/current/ddl.html)
- [PostgreSQL：Data Manipulation](https://www.postgresql.org/docs/current/dml.html)
- [PostgreSQL：Queries](https://www.postgresql.org/docs/current/queries.html)
- [PostgreSQL：Indexes](https://www.postgresql.org/docs/current/indexes.html)
- [PostgreSQL：Concurrency Control](https://www.postgresql.org/docs/current/mvcc.html)
- [Psycopg 3：Basic module usage](https://www.psycopg.org/psycopg3/docs/basic/usage.html)
