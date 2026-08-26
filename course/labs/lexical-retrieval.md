# Lexical Retrieval：从空库到第一次按词检索

> 这是 Lexical Retrieval 的实验篇，和机制篇成对，不讲按词检索的原理。
>
> - 机制：[Lexical Retrieval、BM25 边界与 PostgreSQL 全文检索](../mechanisms/lexical-retrieval.md)
> - 课表：[标准学习路径](../learning-path.md)第一阶段第 11 节
> - 数据库概念不够时，按需阅读 [PostgreSQL 零基础](../concepts/postgresql-for-ai-applications.md)

本文只回答：

> 怎样从本地 PostgreSQL 已安装，到 Server、Database、migration、固定资料入库和第一次按词查询全部就绪？

本文是可重复的课程操作手册，不讲词面检索原理。先读机制篇开头的“按词找候选”问题，再按本文操作；不要在 GUI 里手工插入课文。

这里写入的是 `source/apps/review_assistant/fixtures/rag/ingestion/order_rules.md` 生成的固定 Chunk，用来观察机制，不是产品用户资料管理，也不是已经存在的入库 API。

第 12 步才需要 pgvector 和 `0002` migration。本节**只做 `0001` 和词面检索实验**。

## 0. 安装并确认 Server 在跑

课程推荐 macOS 使用 [Postgres.app](https://postgresapp.com/)，也可以使用 Homebrew、EDB installer 或已有远程 PostgreSQL。安装方式不是本实验的变量；只要能提供 PostgreSQL Server、`psql` 和后续连接参数即可。产品级安装说明和运行边界见 [`source/apps/review_assistant/README.md`](../../source/apps/review_assistant/README.md#postgresql-本地准备)。

Postgres.app 窗口应显示 PostgreSQL **Running**，端口一般为 `5432`。窗口里可能已有 `lrq`、`postgres`、`template1` 等默认库，那是安装自带的，**课程不用它们**。不要改 `template1`。

终端里执行：

```bash
export PATH="/Applications/Postgres.app/Contents/Versions/latest/bin:$PATH"
psql --version
pg_isready -h 127.0.0.1 -p 5432
```

应看到版本号以及 `accepting connections`。若找不到 `psql`，先按安装方式把 CLI 加入 `PATH`，再继续；不要在 `psql` 不可用时跳过检查。

**检查点 A：** `psql --version` 成功，且 `pg_isready` 报告 Server 正在接受连接。

## 1. 创建应用用户和数据库

不要用超级用户跑 Python 实验。在任意目录执行，密码在提示里输入并自己记住：

```bash
createuser --pwprompt review_assistant_app
createdb --owner=review_assistant_app review_assistant
createdb --owner=review_assistant_app review_assistant_test
```

`review_assistant` 是日常学习和第 11 步实验用的库；`review_assistant_test` 给集成测试，避免冲掉学习数据。

**检查点 B：** 目标 Role、学习库和测试库都已创建；不要使用 `template1`，也不要让 Python 实验长期使用超级用户。

若 `createuser` 失败，用本机超级用户进入 `psql`（Postgres.app 下通常是你的 macOS 用户名，例如 `psql -d lrq`），执行：

```sql
CREATE ROLE review_assistant_app LOGIN PASSWORD '你的密码';
CREATE DATABASE review_assistant OWNER review_assistant_app;
CREATE DATABASE review_assistant_test OWNER review_assistant_app;
```

然后 `\q` 退出。

## 2. 写入 `.env`

在仓库根目录打开 `.env`（若还没有，从 `.env.example` 复制）。追加或取消注释：

```dotenv
DATABASE_URL=postgresql://review_assistant_app:真实密码@127.0.0.1:5432/review_assistant
TEST_DATABASE_URL=postgresql://review_assistant_app:真实密码@127.0.0.1:5432/review_assistant_test
```

密码里若有 `@`、`#`、`/`、`%`，需要做 URL 编码。不要把真实密码提交到 Git。

在仓库根目录验证：

```bash
set -a && source .env && set +a
psql "$DATABASE_URL" -c "SELECT current_database(), current_user;"
```

应显示 `review_assistant` 和 `review_assistant_app`。

**检查点 C：** 连接串指向目标 Database，当前用户是 `review_assistant_app`。如果这里失败，不要继续执行 migration。

## 3. 建表（第 11 步只要 `0001`）

仍在仓库根目录，且已 `source .env`：

```bash
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 \
  -f source/apps/review_assistant/infra/migrations/0001_create_rag_chunks.sql
```

检查：

```bash
psql "$DATABASE_URL" -c "\dt review_assistant.*"
```

应看到 `rag_chunks`。此时表可以是空的：migration 只搭结构，不写入售后规则。

若要跑集成测试，对 `TEST_DATABASE_URL` 再执行同一条 `0001`。

第 12 步 Dense Retrieval 才执行产品 README 中的 `0002`；本步骤不安装或启用 pgvector。

**检查点 D：** `\dt review_assistant.*` 能看到 `rag_chunks`，并且当前 Database 与第 2 步相同。

## 4. 写入固定资料并查询

实验不会自动装库、不会自动建表，也不会在失败后改用 SQLite。在仓库根目录：

```bash
uv sync
uv run python source/demos/rag_retrieval_lab/inspect_lexical_retrieval.py --verbose
```

它会：

1. 用第 8 步 Loader 读取 `order_rules.md`。
2. 用第 9 步 structure-aware 策略生成 Chunk。
3. 用同一套词法分析处理 Chunk 和查询。
4. 幂等写入 `review_assistant.rag_chunks`（重复运行会更新，不会无限复制）。这一步是固定 fixture 入库，不是用户资料 API。
5. 对一组业务问题做 PostgreSQL 全文检索。

看诊断、命中词和每个候选，用上面的 `--verbose`。比较「有一个词就算」和「必须全有」：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_lexical_retrieval.py --query-operator and --verbose
```

JSON Lines：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_lexical_retrieval.py --log-format json
```

默认输出里应能看到：原始查询、应用拆出的词、PostgreSQL 查询词和 `tsquery`、命中数、`chunk_id`、`fts_rank`、匹配词。若出现 `connection_failed`、`auth_failed`、`migration_required` 等，先看本文第 6 节，不要当成「资料里没有答案」。

探针问题在 [`retrieval_queries.json`](../../source/apps/review_assistant/fixtures/rag/retrieval/retrieval_queries.json)。它们用来观察机制，不是冻结的第一阶段验收集。

**检查点 E：** 输出显示 `Chunk 已写入 PostgreSQL FTS`，并能在查询表中看到命中数量和 `postgresql_ts_rank`。

### 4.1 先看懂一次命令做了什么

上面的 Python 命令不是只执行一条 SQL。它完整走过这条链路：

```text
读取固定 fixture
→ Loader 读取文档
→ Chunker 生成 Chunk
→ LexicalAnalyzer 给资料和 Query 拆词
→ 写入 PostgreSQL
→ FTS 用 @@ 判断匹配
→ ts_rank 排序
→ 输出候选和诊断
```

因此，Python 命令适合观察**完整应用链路**：应用到底拆出了什么词、传给 PostgreSQL 什么查询、返回了哪些 Chunk、候选上限是否生效，以及失败发生在哪一层。它不会在 PostgreSQL 失败后偷偷改用 SQLite 或内存结果。

### 4.2 终端日志逐字段阅读

先关注标题中的三个变量：

```text
dataset=rag-retrieval-exploration-1.0.0 · operator=or · candidate_k=5
```

| 字段 | 含义 |
| --- | --- |
| `dataset` | 本次使用的固定资料和 Query 探针版本 |
| `operator` | Query 词项如何组合：`or` 或 `and` |
| `candidate_k` | 每个 Query 最多返回多少个候选，不是最终答案数量 |

接着看入库信息：

```text
indexed=2 · lexical_config=... · index_latency=34.4 ms
```

| 字段 | 含义 |
| --- | --- |
| `indexed=2` | 本次写入或更新了两个 Chunk |
| `lexical_config` | 当前词法规则的版本身份；规则变更后不能和旧词空间混用 |
| `index_latency` | 入库耗时，只说明速度，不说明检索质量 |

查询汇总表按下面顺序阅读：

| 字段 | 含义 |
| --- | --- |
| `Query` | 原始用户问题 |
| `Group` | 这个探针被归入的观察场景，不是 PostgreSQL 条件 |
| `Terms` | 应用拆出的词项；先检查它是否包含你预期的词 |
| `Hits` | 本次实际返回的候选数 |
| `Top rank` | 返回候选中第一名的 `ts_rank`；越大越靠前，但不是答案正确率 |
| `Expectation` | 教学实验的预期现象，不是程序自动判定的通过结论 |

使用 `--verbose` 后，每个 Query 下面还会有：

| 字段 | 含义 |
| --- | --- |
| `tsquery` | PostgreSQL 最终执行的查询条件；看其中是 `&` 还是 `|` |
| `postgres terms` | PostgreSQL 实际收到的词项；和 `Terms` 对照可发现词在哪一层变化 |
| `Matched` | 该 Chunk 与 Query 共同出现的词 |
| `Chunk` | 命中 Chunk 的稳定 ID |
| `Content` | 命中 Chunk 的原文摘要 |
| `FTS rank` | PostgreSQL `ts_rank` 的原始分数 |

可以按这条路径读一组结果：

```text
Query
→ Terms
→ postgres terms
→ tsquery
→ Matched
→ FTS rank / Content
```

例如有 `tsquery` 但 `Hits=0`，通常是词面没有对上，或 AND 要求的词太多；这不是数据库连接失败。出现 `connection_failed`、`auth_failed`、`migration_required`、`permission_denied` 时，才应先排查依赖或表结构。

### 4.3 做对照：一次只改变一个变量

每次运行前先预测，再只改一个参数。

**对照一：OR 与 AND**

```bash
uv run python source/demos/rag_retrieval_lab/inspect_lexical_retrieval.py \
  --query-operator or --verbose

uv run python source/demos/rag_retrieval_lab/inspect_lexical_retrieval.py \
  --query-operator and --verbose
```

只改变 `query-operator`。先看 `tsquery` 中的 `|` / `&`，再比较 `Hits` 和哪些 Query 从命中变成 0。OR 允许任意词命中，通常更宽；AND 要求所有词出现，通常更窄。资料已经入库，不需要重新执行 migration。

**对照二：`candidate_k`**

```bash
uv run python source/demos/rag_retrieval_lab/inspect_lexical_retrieval.py \
  --query-operator or --candidate-k 1 --verbose

uv run python source/demos/rag_retrieval_lab/inspect_lexical_retrieval.py \
  --query-operator or --candidate-k 5 --verbose
```

只改变 `candidate_k`。如果某个 Query 实际匹配多个 Chunk，匹配总数可能不变，但返回数量会受 `candidate_k` 限制；排名靠后的候选可能不再显示。要精确比较 `matched_chunk_count` 和 `returned_chunk_count`，再运行 JSON 诊断：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_lexical_retrieval.py \
  --query-operator or --candidate-k 1 --log-format json
```

JSON 中每个 `lexical.query_observed` 事件的 `matched_chunks` 是匹配总数，`returned_chunks` 是实际返回数，`candidate_k` 是上限。普通 `--verbose` 更适合人眼阅读候选内容。

**对照三：倒排索引中的两个词**

在[调试 SQL 说明](../../source/demos/rag_retrieval_lab/sql/README.md#对照查询)中复制两条查询，分别查询 `售后` 和 `techidsourcechannel`。预测 `售后` 可以找到 Chunk A、B，而 `techidsourcechannel` 只能找到 Chunk A。这组对照观察的是“词 → Chunk”的映射，不是语义相似度。

**对照四：Python 命令和直接 SQL**

两者最终都可以调用 PostgreSQL FTS，但观察范围不同：

| 方式 | 能看到什么 |
| --- | --- |
| Python 命令 | Loader、Chunker、应用拆词、`tsquery`、候选、rank、配置版本、结构化错误和完整诊断 |
| 直接 SQL | 数据库保存的 `search_vector`、SQL 生成的 `tsquery`、`@@` 匹配行和 `ts_rank` |

所以 SQL 不是 Python 命令的完全替代品；SQL 适合孤立观察数据库层，Python 命令适合确认真实应用传入和接收了什么。如果两者结果不同，先对照 Python 输出中的 `postgres terms` 和 `tsquery`，不要直接把差异归因于 PostgreSQL。

## 5. 在 GUI 里核对三列

Cursor / VS Code 的 PostgreSQL 插件连接：

```text
Host: 127.0.0.1
Port: 5432
Database: review_assistant
User: review_assistant_app
Password: 与 .env 一致
SSL: 关闭
```

打开 schema `review_assistant`（不要只看 `public`），刷新 `rag_chunks`。跑过第 4 步后应有行。对照：

| 列 | 看什么 |
| --- | --- |
| `content` | 给人看的原文 |
| `lexical_text` | Python 拆好、空格分开的检索词 |
| `search_vector` | 数据库收下的词袋，不是第 10 步那种 Embedding 向量 |

不要把 `SELECT` 存成临时文件名再在终端里看宽表。调试 SQL 放在 [`sql/`](../../source/demos/rag_retrieval_lab/sql/README.md)：

```bash
psql "$DATABASE_URL" -f source/demos/rag_retrieval_lab/sql/list_chunk_previews.sql
psql "$DATABASE_URL" -f source/demos/rag_retrieval_lab/sql/inspect_rag_chunks.sql
```

前一条是窄表摘要；后一条会把 `content` / `lexical_text` / `search_vector` 逐列展开，避免挤成一团。

第一次查询前先预测：`source_channel` 应能命中接口规则；`发起逆向服务` 可能 0 条。0 条且没有报错，是词面检索的边界，到机制篇再解释。

## 6. 失败时查哪一层

| 表现 | 先做什么 |
| --- | --- |
| 找不到 `psql` / 连不上 5432 | 第 0 步：PATH、Postgres.app 是否 Running |
| `auth_failed` | Role、密码、`.env` 里特殊字符是否编码 |
| `migration_required` | 是否对当前 `DATABASE_URL` 执行了 `0001` |
| `permission_denied` | 是否用 `review_assistant_app` 连接它拥有的库 |
| 表在 `public` 里找不到 | 看 schema `review_assistant` |
| 查询成功但 0 行 | 先确认第 4 步已写入；再对照机制篇的词面边界 |
| Server / 表 / SQL 这些词仍陌生 | [PostgreSQL 零基础](../concepts/postgresql-for-ai-applications.md) |

产品级的第二条 migration、pgvector、测试库排障仍在 [产品 README](../../source/apps/review_assistant/README.md#postgresql-本地准备)。学第 11 步不必先做 `0002`。

集成测试（可选）：

```bash
uv run pytest source/packages/rag_core/tests/test_postgres_fts.py -q -m integration
```

## 7. 做完后去读机制篇

准备完成的标志：

- `psql "$DATABASE_URL"` 显示用户 `review_assistant_app`；
- `rag_chunks` 里已有实验写入的行；
- `--verbose` 跑完，能看到至少一次命中和一次可能的空结果。

然后打开 [机制正文](../mechanisms/lexical-retrieval.md)，从“先用两个 Chunk 预测结果”继续。需要对照命令或输出时再回到本页，不要重装数据库。

## 调用路径与读码顺序

```text
main
→ load_document
→ chunk_document
→ LexicalAnalyzer.analyze_document
→ PostgresFTSRetriever.upsert_chunks
→ PostgreSQL generated tsvector + GIN
→ LexicalAnalyzer.analyze_query
→ websearch_to_tsquery + @@ + ts_rank
→ LexicalSearchResult
```

1. [`inspect_lexical_retrieval.py`](../../source/demos/rag_retrieval_lab/inspect_lexical_retrieval.py)
2. [`lexical/analyzer.py`](../../source/packages/rag_core/lexical/analyzer.py)
3. [`retrieval/postgres_fts.py`](../../source/packages/rag_core/retrieval/postgres_fts.py)
4. [`0001_create_rag_chunks.sql`](../../source/apps/review_assistant/infra/migrations/0001_create_rag_chunks.sql)
5. [`test_lexical.py`](../../source/packages/rag_core/tests/test_lexical.py) 与 [`test_postgres_fts.py`](../../source/packages/rag_core/tests/test_postgres_fts.py)
