# 需求评审助手

`review_assistant/` 是需求评审助手的可运行产品真源，从阶段一 V0 开始逐步演进。

它负责产品代码、API、测试、配置、运行和部署，不承担课程概念教学。

## 产品目标

需求评审助手围绕 PRD、业务规则、接口文档、客户端规则和历史评审记录，逐步完成：

```text
真实文档解析与 PostgreSQL FTS / pgvector 检索
→ 应用侧 RRF 多路召回与 Retrieval 诊断
→ 最小评审工作台
→ 结构化评审与证据引用
→ 可信证据界面
→ 评估、bad case 和质量工作台
→ 经评估达到准入门槛的检索增强
→ 带短期记忆和用户确认偏好/约束长期记忆的单 Agent 补检索、追问和运行界面
→ Workflow 与人工审核
→ 多 Agent 协作
→ 工作台整合、部署与产品化
```

两个阶段怎样进入学习与项目实现，见 [标准学习路径](../course/learning-path.md)。

这里的“检索增强”不预设额外技术栈。V0 固定采用 PostgreSQL 全文检索、pgvector 和应用侧 RRF；Reranker 等候选能力只有在固定评估集上证明收益大于延迟、成本和维护复杂度后，才进入后续产品版本。

## 与课程的边界

```text
course/project/       项目篇教材：组合任务、设计选择、失败题和版本验收
review_assistant/     产品真源：代码、API、测试、配置、运行和部署
```

本 README 只维护产品事实：

- 如何安装和配置。
- 如何启动产品。
- 如何运行测试和评估。
- 产品入口、模块和依赖是什么。
- 当前实现具备哪些实际能力。
- 常见运行失败如何排查。

课程原理、设计题和学习自检不在这里重复维护；学习者从 [课程首页](../course/README.md) 进入。

## 代码关系

- 通用 LLM、RAG、Agent 和 Eval 能力来自 `source/packages/`。
- 产品通过根 `pyproject.toml` 的 editable package 配置 import 复用。
- 不在本目录 copy 平行 `*_core`。
- `source/apps/` 可以用于学习期组合实验，但不与本目录长期维护两份产品。

## 目标职责

产品按真实版本需要逐步形成以下职责：

```text
review_assistant/
├── app/            # FastAPI、业务服务和运行时
├── workbench/      # AI Native Web 工作台
├── tests/          # 产品级测试
├── fixtures/       # 固定业务资料和评估样例
└── infra/          # 数据库、迁移、Docker 与部署
```

这是一张职责地图，不授权预建空目录。只有对应版本的文档、代码和运行入口同时落地时才创建实际目录。

当前产品只维护 Web 工作台，不建设或并行维护 Flutter App。课程中的 Flutter 仍可作为业务影响范围和学习者既有经验出现，但不是 V0–V6 的产品入口或验收项。

## 当前已落地的运行能力

当前目录尚未形成完整 Review API 和 Web 产品入口，但 V0 的真实资料 fixture、PostgreSQL FTS 与 pgvector 基础设施已经开始落地。已有通用能力和学习期实验分别位于：

- `source/packages/llm_core/`
- `source/packages/rag_core/`（当前已实现文档加载、Chunking、Embedding 表示实验、中文词法分析、PostgreSQL FTS、pgvector 持久化与 Dense Retrieval）
- `source/demos/`
- `source/apps/llm_streaming_api/`

V0 受控格式对照 fixtures 已经位于 `fixtures/v0/ingestion/`，供 `rag_ingestion_lab` 观察 TXT、Markdown、DOCX、文本型 PDF、当前支持边界和确定性错误契约。这些是模拟业务内容和真实文件格式，不是生产资料；资料存在也不表示产品入库、检索 API 或工作台已经完成。

步骤 11 使用真实 PostgreSQL 保存 Chunk 并运行 FTS；步骤 12 使用真实 Embedding 和 pgvector 运行 Dense Retrieval，并可为当前 Embedding 空间建立 HNSW 索引；步骤 13 在应用侧按稳定 `chunk_id` 运行 RRF 并保留两路贡献；步骤 14 固定 Metadata pre-filter、每路候选和阈值、RRF、`final_top_k` 的顺序并返回诊断报告；步骤 15 把最终候选连同文档版本、locator 和路线诊断接入共享 Context Builder；步骤 16 调用真实模型生成结构化风险并检查 claimed source ID 是否属于本轮 Citation Candidate。当前这些仍是共享 package 与机制实验入口，不表示产品已经提供资料管理 API、后台入库任务或 Review API；Citation 内容支持性、Refusal 和证据充分性仍未实现。

## PostgreSQL 本地准备

**正在学习课程第 11 步（按词检索）时，不要从本节开始。** 从空库到第一次 FTS 查询，只走：

> [第 11 步实验准备](../source/demos/rag_retrieval_lab/docs/11-lexical-retrieval.md)

本节保留产品级安装：Role、两个 Database、`0001` 与 `0002`、测试库，以及第 12 步起需要的 pgvector。不自动安装 PostgreSQL、GUI 或系统服务。当前 macOS 学习主路径推荐 [Postgres.app](https://postgresapp.com/)，因为安装简单、包含 `psql`，并预装后续步骤需要的 pgvector；PostgreSQL 官方也在 [macOS packages](https://www.postgresql.org/download/macosx/) 页面列出了 Postgres.app、EDB installer 和 Homebrew 等方式。

推荐使用一个受支持的 PostgreSQL 大版本，并固定记录本地真实版本。当前课程代码不依赖 PostgreSQL 18 独有语法；后续 pgvector 版本仍以实际锁定的运行环境为准。

### 1. 安装并暴露 `psql`

安装 Postgres.app 后启动一个本地 Server。若终端找不到 `psql`，按 [Postgres.app CLI 文档](https://postgresapp.com/documentation/cli-tools.html) 将其 binary 目录加入 `PATH`，然后重新打开终端：

```bash
psql --version
pg_isready -h 127.0.0.1 -p 5432
```

也可以使用 Homebrew、EDB installer 或已有远程 PostgreSQL；只要后面的数据库、Role、migration 和 `DATABASE_URL` 契约一致，应用代码不需要变化。

### 2. 创建应用 Role 和 Database

不要让应用长期使用 `postgres` 等超级用户。下面命令由本地管理员执行，密码由你在交互提示中输入：

```bash
createuser --pwprompt review_assistant_app
createdb --owner=review_assistant_app review_assistant
createdb --owner=review_assistant_app review_assistant_test
```

如果 Role 没有创建 Database 的权限，使用本地管理员连接 `psql` 后执行等价 SQL。课程正文解释 `CREATE ROLE`、`CREATE DATABASE` 和权限含义；本 README 只维护可运行命令。

### 3. 配置连接

复制根目录 `.env.example` 为未提交的 `.env`，填写真实密码：

```dotenv
DATABASE_URL=postgresql://review_assistant_app:真实密码@127.0.0.1:5432/review_assistant
TEST_DATABASE_URL=postgresql://review_assistant_app:真实密码@127.0.0.1:5432/review_assistant_test
```

连接串包含特殊字符时需要进行 URL encoding。不要把真实密码写入代码、README、fixture、测试输出或 Git。

先验证身份和目标 Database：

```bash
psql "$DATABASE_URL" -c "SELECT current_database(), current_user, version();"
```

### 4. 执行 migration

当前采用编号原生 SQL migration，使第 11–12 节可以直接看到真实表、约束、生成列、GIN 和 pgvector 对象，不引入 ORM 或 migration framework。按编号顺序执行：

```bash
psql "$DATABASE_URL" \
  -v ON_ERROR_STOP=1 \
  -f review_assistant/infra/migrations/0001_create_rag_chunks.sql

psql "$DATABASE_URL" \
  -v ON_ERROR_STOP=1 \
  -f review_assistant/infra/migrations/0002_add_pgvector_embeddings.sql
```

检查结果：

```bash
psql "$DATABASE_URL" -c "\d+ review_assistant.rag_chunks"
psql "$DATABASE_URL" -c "\d+ review_assistant.rag_chunk_embeddings"
psql "$DATABASE_URL" -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
psql "$DATABASE_URL" -c "SELECT indexname, indexdef FROM pg_indexes WHERE schemaname = 'review_assistant';"
```

`search_vector` 是由 `lexical_text` 生成的 `tsvector`；`rag_chunks_search_vector_gin_idx` 是词面候选匹配索引。`0002` 启用 pgvector 并创建向量表；具体 HNSW 索引依赖真实 Provider 返回的模型、维度和预处理空间，由步骤 12 入库后按当前 `embedding_space_ref` 建立，不在 migration 中假定所有服务都是固定 1536 维。

若应用 Role 没有安装 extension 的权限，由本地数据库管理员只执行 `CREATE EXTENSION vector`，再由应用 Role 执行 migration。不要为了绕过权限让应用长期使用超级用户。

### 5. 可选 GUI

如果希望通过图形界面查看 Server、Schema、Table、数据和 Query Plan，可安装 [pgAdmin 4](https://www.pgadmin.org/download/)。本地连接填写：

```text
Host: 127.0.0.1
Port: 5432
Maintenance database: review_assistant
Username: review_assistant_app
Password: 与本地 .env 一致
```

Postgres.app 的窗口主要负责本地 Server 生命周期；pgAdmin 才是完整的数据库对象浏览和 SQL GUI。课程的 migration、测试与验收仍以命令行为准，GUI 只是观察入口。

## 运行 PostgreSQL FTS 实验

第 11 步课程实验的命令、写入说明和输出解读见 [第 11 步实验准备](../source/demos/rag_retrieval_lab/docs/11-lexical-retrieval.md)。

产品侧可选集成测试：

```bash
uv run pytest source/packages/rag_core/tests/test_postgres_fts.py -q -m integration
```

默认实验会幂等写入固定 fixture 的 Chunk。它不会清空表，也不会自动执行 migration；数据库连接、权限或表结构失败会作为结构化错误暴露。不要回退到 SQLite、Mock 或 Python 内存检索。

## 运行 pgvector Dense Retrieval 实验

完成两条 migration，并配置真实 Embedding 服务后运行：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_dense_retrieval.py
```

查看 exact / HNSW 候选、可见数量与查询计划：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_dense_retrieval.py --verbose
```

只运行 exact 正确性基线：

```bash
uv run python source/demos/rag_retrieval_lab/inspect_dense_retrieval.py --search-mode exact
```

离线测试不调用真实模型，只验证 Chunk/向量绑定、空间身份、维度和结果契约；它不能证明 Dense Retrieval 质量。真实机制实验必须使用上面的真实 Embedding 路径。

## 运行 RRF 多路召回实验

```bash
uv run python source/demos/rag_retrieval_lab/inspect_rrf_retrieval.py --verbose
```

该入口继续调用真实 FTS、真实 Embedding 和 pgvector。它不会把两路原始分数归一化相加；步骤 13 的参数和输出解读由 [`docs/13-rrf.md`](../source/demos/rag_retrieval_lab/docs/13-rrf.md) 维护。

## PostgreSQL 常见排查

| 表现 | 优先检查 |
| --- | --- |
| `connection_failed` | Postgres.app Server 是否运行、host、port、database、网络 |
| `auth_failed` | Role、密码、连接串特殊字符编码 |
| `migration_required` | 是否对当前 `DATABASE_URL` 指向的 Database 按顺序执行了 `0001`、`0002` migration |
| `permission_denied` | 表和 Schema owner、Role 的连接与写入权限 |
| 查询成功但无结果 | query terms、`tsquery`、`lexical_config_ref`、资料是否真的包含相同词面 |
| 修改词法配置后旧数据消失 | 新旧 `lexical_config_ref` 不再兼容，需要重新 upsert Chunk |
| Dense 查询为 0 条 | 当前空间是否已有 Chunk 向量、`knowledge_scope` 是否排除了全部 Chunk；不要先判断为数据库故障 |
| 向量维度不一致 | query 与 Chunk 是否使用同一 Provider、配置、模型、维度和预处理版本 |
| HNSW 已创建但 `index_used=false` | 小数据集下 Planner 可能认为顺序扫描更便宜；查看 plan，不要把未选择误判成索引损坏 |

不要把连接失败转换成空候选，也不要在实验中回退到 SQLite、Mock 或 Python 内存检索。

产品入口落地后，本节应替换为真实的安装、配置、启动、测试和验证命令，不保留占位命令或模拟成功结果。

## 真实调用规则

- 产品主路径使用真实模型和真实外部服务。
- 缺少 key、供应商失败和模型能力不支持应清晰暴露。
- 不允许静默降级到 Mock。
- Mock 只用于产品单元测试、离线排查或明确标注的稳定失败复现。
