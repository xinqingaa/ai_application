# 飞书知识库与 Agent 接入调研

## 文档定位

这是一份外部平台调研盘点，不是课程正文、不是 `docs/` 规范真源、也不是当前项目验收项。

用途：

- 回答「能否在飞书新建知识库，并把文档写进去」。
- 盘点开放平台、CLI、远程 MCP、本地 OpenAPI MCP、Channel SDK 各自能做什么。
- 给后续文档编排留底：以后再决定进入概念篇、机制篇、项目篇、知识地图，还是继续只作未来认知。

当前分级（按 [learning-guide.md](../../docs/learning-guide.md)「知识与功能的分级准入」）：**未来认知**。本仓库没有飞书集成代码；飞书 Wiki 也替代不了产品内的 RAG 知识库。

调研日期：2026-08-23。结论以当时官方文档为准，接入前应再核对链接。

## 结论

可以。飞书已支持完整链路：

```text
新建知识空间
→ 在空间中创建文档节点
→ 用云文档接口写入正文
```

对 Agent 来说，官方当前更推荐走 **飞书 CLI（执行层）**，而不是默认远程 MCP。

Channel SDK 和一键创建应用不能完成这件事：前者只负责会话收发，后者只负责拿凭据。

## 不要和本仓库的「知识库」混用

| 对象 | 是什么 | 本仓库现状 |
| --- | --- | --- |
| 飞书知识库（Wiki） | 面向组织的知识空间 + 节点树，页面可以是 docx / sheet / bitable 等 | 无集成 |
| RAG 知识库 | 文档、切块、索引、检索、引用 | 产品与课程主线 |
| RAGFlow / MaxKB 的 Knowledgebase | 平台型知识资产对象 | 见 `other/ragflow/`、`other/MaxKB/` |

后文「知识库」均指飞书 Wiki。

## 官方三层能力

来源：[飞书 Agent 集成能力概述](https://open.feishu.cn/document/mcp_open_tools/overview-of-lark-agent-integration-capabilities)

| 层 | 产品 | 形态 | 和本目标的关系 |
| --- | --- | --- | --- |
| 凭据层 | [一键创建飞书应用](https://open.larkoffice.com/document/mcp_open_tools/integrating-agents-with-feishu/overview) | Web 扫码 SDK（Node.js / Python / Java / Go） | 只拿 App ID、App Secret，并预置权限与事件订阅 |
| 交互层 | [Channel SDK](https://open.larkoffice.com/document/mcp_open_tools/integrating-agents-with-feishu/integrate-feishu-channel) | 通道 SDK | 群聊、单聊、文档评论里收发消息；不能建 Wiki、不能写正文 |
| 执行层 | [飞书 CLI](https://open.feishu.cn/document/mcp_open_tools/feishu-cli-let-ai-actually-do-your-work-in-feishu) | `npx @larksuite/cli@latest install` | **真正操作文档、知识库、日历、表格等业务对象** |

MCP 不是这三层里的第四层，而是另一套封装：

- 远程 MCP：官方托管工具，当前主要覆盖云文档。
- 本地 OpenAPI MCP：把开放平台 API 暴露给模型。

官方已写明：个人托管 MCP Token 后续将逐步下线，更推荐 CLI。见 [终端用户调用远程 MCP](https://open.feishu.cn/document/mcp_open_tools/end-user-call-remote-mcp-server?lang=zh-CN)。

## 核心对象模型

来源：[知识库概述](https://open.feishu.cn/document/server-docs/docs/wiki-v2/wiki-overview?lang=zh-CN)、[知识库常见问题](https://open.feishu.cn/document/server-docs/docs/wiki-v2/wiki-qa?lang=zh-CN)

```text
知识空间 space          ← 「新建知识库」对应这一层
  └── 节点 node           ← 目录树中的一页
        └── 真实文档 obj_token  ← 写正文必须用这个
```

| 字段 | 含义 |
| --- | --- |
| `space_id` | 知识空间唯一标识。管理员可从知识库设置页 URL 数字段复制，也可调列表接口获取 |
| `space_type` | `team` 团队空间；`person` 旧版个人空间已下线；`my_library` 我的文档库 |
| `node_token` | Wiki URL 路径里的 token，例如 `https://xxx.feishu.cn/wiki/<node_token>` |
| `obj_token` | 节点挂载的真实云文档 token。读/写正文用这个，不是 `node_token` |
| `obj_type` | `docx` / `sheet` / `bitable` / `file` / `slides` / `mindnote` 等。新建文档用 `docx`，旧版 `doc` 已下线 |

Wiki API 本身不负责写段落。写正文走云文档（Docx）接口。

## 路径对照

| 路径 | 新建知识空间 | 在空间里建文档页 | 写入正文 | 适合场景 |
| --- | --- | --- | --- | --- |
| 飞书 CLI | 能。`wiki +space-create`，仅用户身份 | 能。`wiki +node-create` | 能。`docs +create` / `docs +update` | Cursor / 本地 Agent 首选 |
| Wiki v2 + Docx OpenAPI | 能。`POST /wiki/v2/spaces`，仅 `user_access_token` | 能。`POST /wiki/v2/spaces/:space_id/nodes` | 能。先取 `obj_token`，再调 Docx | 产品后端、脚本、可重复集成 |
| 远程 MCP | **不能** | 部分能。`create-doc` 可在指定知识库节点下建文档 | 能。`create-doc` / `update-doc` | 往已有知识库写，不从零建空间 |
| 本地 OpenAPI MCP | 默认不能，需 `-t` 手动开写接口 | 默认不能 | 默认只能读纯文本、搜 Wiki | 不推荐作为主路径 |
| Channel SDK | 不能 | 不能 | 不能 | 只做会话入口 |
| 一键创建应用 | 不能 | 不能 | 不能 | 只做凭据 |

## 路径一：飞书 CLI

源码与 skill：[larksuite/cli](https://github.com/larksuite/cli)

CLI 覆盖知识空间、节点和文档。职责拆分：

- `lark-wiki`：管空间、成员、节点层级。**不负责编辑正文**。
- `lark-doc`：读、建、改 Docx / Wiki 正文。支持 `/wiki/` URL。

### 安装与授权

```bash
npx @larksuite/cli@latest install
lark-cli config init --new
lark-cli auth login --recommend
lark-cli auth status
```

Wiki 操作应显式 `--as user`。CLI 的 `--as` 默认是 `auto`，不带参数时经常被解析成 bot，列到的是应用可见空间，不是用户个人空间。

创建空间所需 scope 至少包括 `wiki:space:write_only`，或更宽的 `wiki:wiki`。缺权限时用 `lark-cli auth login --scope "<missing_scope>"`。

### 与目标对应的 shortcut

| 步骤 | 命令 | 约束 |
| --- | --- | --- |
| 新建知识空间 | `lark-cli wiki +space-create --name "..." [--description "..."] --as user` | 只接受用户身份；`--as bot` 会被拒绝 |
| 列出空间 | `lark-cli wiki +space-list --as user` | `space_id` 是数字 ID，不要把 URL 当 space_id |
| 在空间中建空文档页 | `lark-cli wiki +node-create --space-id <id> --title "..." --obj-type docx` | 也可传 `--parent-node-token`；user 身份下两者都省略时回退到 `my_library` |
| 直接带正文创建 | `lark-cli docs +create --parent-token <wiki节点> --doc-format markdown --content "..."` | `--parent-token` 可以是知识库节点；与 `--parent-position` 互斥 |
| 改已有 Wiki 页 | `lark-cli docs +update`，传入 wiki URL 或 `obj_token` | 写正文走 doc skill，不走 wiki skill |
| 已有云文档迁入 Wiki | `lark-cli wiki +move` | 对应 OpenAPI `move_docs_to_wiki`，可能是异步任务 |
| 删除空间 | `lark-cli wiki +delete-space --space-id <id> --yes` | 高风险；必须先解析真实 `space_id`，不能把名称或 URL 直接当 ID |

`wiki +space-create` 成功返回 `space_id`、`name`、`space_type` 等，**不返回 url**。底层接口：`POST /open-apis/wiki/v2/spaces`。

`docs +create` 还可使用 `--parent-position my_library`，把文档建到个人文档库。

### CLI 的三层调用

1. shortcut（`+` 前缀）：人机友好，优先用。
2. API 命令：与开放平台端点对应，例如 `lark-cli wiki spaces create`。
3. 通用调用：`lark-cli api POST /open-apis/wiki/v2/spaces ...`，覆盖全量 OpenAPI。

## 路径二：开放平台 Wiki v2 + Docx

来源：[知识库概述](https://open.feishu.cn/document/server-docs/docs/wiki-v2/wiki-overview?lang=zh-CN)、[创建知识空间](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/space/create)、[创建节点](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/space-node/create)

### 空间

| 接口 | 方法 | Token |
| --- | --- | --- |
| 创建知识空间 | `POST /open-apis/wiki/v2/spaces` | **仅 `user_access_token`** |
| 获取知识空间列表 | `GET /open-apis/wiki/v2/spaces` | user / tenant |
| 获取知识空间信息 | `GET /open-apis/wiki/v2/spaces/:space_id` | user / tenant |

创建空间请求体示例：

```json
{
  "name": "Knowledge space",
  "description": "Knowledge space description"
}
```

可选 `open_sharing`：`open` / `closed`。限流约 10 次/分钟。权限：`wiki:space:write_only` 或 `wiki:wiki`。

### 节点

| 接口 | 方法 | Token |
| --- | --- | --- |
| 创建节点 | `POST /open-apis/wiki/v2/spaces/:space_id/nodes` | user / tenant |
| 获取子节点列表 | `GET /open-apis/wiki/v2/spaces/:space_id/nodes` | user / tenant |
| 获取节点信息 | `GET /open-apis/wiki/v2/spaces/get_node` | user / tenant |
| 添加已有云文档至知识库 | `POST /open-apis/wiki/v2/spaces/:space_id/nodes/move_docs_to_wiki` | user / tenant，异步 |
| 空间内移动节点 | `POST /open-apis/wiki/v2/spaces/:space_id/nodes/:node_token/move` | user / tenant |

创建节点请求体要点：

- `obj_type`：新建文档用 `docx`
- `node_type`：实体用 `origin`，快捷方式用 `shortcut`
- `parent_node_token`：一级节点可省略
- `title`：节点标题

容量边界（接口文档）：

- 单空间节点总数不超过 40 万
- 目录树不超过 50 层
- 单层节点不超过 2000
- 单次移动节点（含子节点）不超过 2000

### 成员与设置

| 接口 | 作用 |
| --- | --- |
| `POST /open-apis/wiki/v2/spaces/:space_id/members` | 添加成员 |
| `DELETE /open-apis/wiki/v2/spaces/:space_id/members/:member_id` | 删除成员 |
| `PUT /open-apis/wiki/v2/spaces/:space_id/setting` | 更新空间设置 |

成员可以是用户、群、部门或应用。应用身份（bot / `tenant_access_token`）不能用部门 ID 添加成员。

### 写正文

Wiki FAQ 规定的步骤：

1. 从 URL 或节点列表拿到 `node_token`。
2. 调用获取节点信息，得到 `obj_token` 和 `obj_type`。
3. 按类型调用对应云文档接口：
   - 文档：Docx 纯文本 / 块接口
   - 表格：电子表格接口
   - 多维表格：Bitable 记录接口

本地文件进入知识库是两段式：先按 [导入流程](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/drive-v1/import_task/import-user-guide) 导入云空间，再 `move_docs_to_wiki`。该迁移接口可能返回 `task_id`，需 [获取任务结果](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/task/get)。

导出则相反：先取 `obj_token`，再走云文档导出。

## 路径三：远程 MCP

来源：[支持的 MCP 工具集](https://open.feishu.cn/document/mcp_open_tools/supported-tools)

当前只开放「云文档」和通用工具，持续扩展中。

| 工具 | 作用 | 对「新建知识库并写入」 |
| --- | --- | --- |
| `create-doc` | 在「我的文档库」或指定知识库节点下新建飞书文档 | 能写进**已有**节点；不能创建新的知识空间 |
| `update-doc` | 追加、替换、按位置插入 | 长文可分批写 |
| `fetch-doc` | 按链接读全文，超长可分页 | 读 |
| `search-doc` | 按关键词、创建者搜索 | 仅 doc / docx |
| `list-docs` | 列出某知识空间节点下的文档 | 浏览目录，子空间需自行遍历 |
| `get-comments` / `add-comments` | 读评论 / 添加全文评论 | 不写正文 |
| `search-user` / `get-user` / `fetch-file` | 通用工具 | 与建库无关 |

`create-doc` 的官方说明包含：可放到指定知识库节点下；超长内容可再调 `update-doc`。限制：不能插入已有 Base / Sheets / OKR / Tasks / Calendar 等；不能创建文档小组件、同步块、旧版流程图和旧版思维笔记。

## 路径四：本地 OpenAPI MCP

仓库：[larksuite/lark-openapi-mcp](https://github.com/larksuite/lark-openapi-mcp)

把飞书 OpenAPI 封装成 MCP 工具。用 `-t` 指定工具或预设；`-t` 是**全量覆盖**，不是追加。

默认 / `preset.doc.default` 里与 Wiki 相关的只有只读：

| MCP 工具名 | 接口 | 能力 |
| --- | --- | --- |
| `wiki.v2.space.getNode` | 获取知识空间节点信息 | 把 `node_token` 解析成 `obj_token` |
| `wiki.v1.node.search` | 搜索 Wiki | 搜索，不创建 |

创建空间、创建节点默认未开启。社区反馈：默认工具不能在指定 Wiki 目录下创建或搜索，见 [Issue #35](https://github.com/larksuite/lark-openapi-mcp/issues/35)。维护者建议手动加例如：

- `wiki.v2.spaceNode.list`
- `wiki.v2.spaceNode.moveDocsToWiki`

理论上可继续打开 `wiki.v2.space.create` 和创建节点类工具，但非预设 API 官方标明未做 Agent 兼容评测，模型调用成功率低于 CLI shortcut。

若坚持用这条路径，创建空间必须 `--token-mode user_access_token`（或 OAuth 用户登录）。应用身份会被该接口拒绝。

## 权限与失败点

### 两层权限

1. **API 权限（scope）**：应用在开发者后台申请并发布，例如 `wiki:wiki`、`wiki:wiki:readonly`、`wiki:space:write_only`、`wiki:node:create`。
2. **资源权限**：应用或用户必须是该空间的成员/管理员，或是目标文档的协作者。只有 scope、没有资源授权，会返回 `permission denied`。

Wiki FAQ：除「创建知识空间」和「搜索 Wiki」外，多数 Wiki API 可用 `tenant_access_token`。但应用访问具体空间前，仍要被授权。

给应用授权整个空间的常见做法：

- 把应用加进群，再把该群加为知识库管理员或可编辑成员。注意加的是应用机器人，不是自定义机器人。
- 用知识库管理员的 `user_access_token` 调添加成员接口，把应用 `open_id` 加成成员，`member_role` 控制角色。

只授权部分节点：把应用或含应用的群加成该节点云文档协作者。

### 常见失败

| 现象 | 原因 |
| --- | --- |
| 创建空间失败 / bot 被拒 | 该接口不接受 `tenant_access_token` |
| `wiki space permission denied` | 调用方不是空间成员或管理员 |
| `node permission denied` | 读需要节点阅读权，创建/移动需要容器编辑权 |
| CLI 列出的空间不是自己的 | 未加 `--as user`，落到了 bot 视角 |
| 把 wiki URL 当 `space_id` | `space_id` 是数字；URL 里是 `node_token` |
| 用 `node_token` 调 Docx 写接口 | 必须先换成 `obj_token` |
| 创建 `obj_type: doc` | 旧版文档创建已下线，用 `docx` |
| 企业后台拦截 scope | 需要管理员审批 Wiki 相关权限 |
| 「我的文档库」被当成云空间根目录 | `my_library` 是 Wiki 个人库，不是 Drive 根目录 |

### 权限语义（空间内部）

- 节点阅读权：可查看。
- 容器编辑权：可编辑文档，可增删子节点。空间管理员对所有节点有该权限且不可移除。
- 单页面编辑权：可编辑文档，不可增删子节点。
- 空间成员默认通常是阅读权，可在空间设置中修改。

## 推荐落地（尚未实施）

这些是调研建议，不是本仓库待办。

**个人或小团队，让 Cursor Agent 建库并灌文档**

1. 安装 CLI，用户身份登录。
2. `wiki +space-create` 建空间。
3. `docs +create --parent-token <根节点或子节点>` 直接写入；或先 `wiki +node-create` 再 `docs +update`。
4. 不要把远程 MCP 当主路径。

**产品里自动同步（例如评审报告写入飞书）**

1. 用用户身份建一次空间，或运维在飞书里建好。
2. 把应用加成该空间管理员或可编辑成员。
3. 后续用应用身份建节点、用 Docx 写正文。
4. 服务端走 OpenAPI；CLI 适合本地 Agent，不适合当服务端 SDK。

**只往已有知识库写，不新建空间**

远程 MCP 的 `create-doc` 勉强可用；更稳仍是 CLI `docs +create --parent-token`。

## 对本仓库的含义

- `review_assistant/`、`source/packages/` 当前都没有飞书实现。
- 若只是把课程或文档同步到飞书，用 CLI 做一次性操作即可，不必先做成产品能力。
- 若以后要把「评审结果写入飞书知识库」做成版本功能，再按 [ai-application-platform.md](../../docs/ai-application-platform.md) 的过滤器评估：当前版本真实问题、最小实现、验证方式、明确非目标。
- 飞书 Wiki 是协作文档容器，不是 RAG 的 Knowledgebase / Chunk / Retriever。

## 后续编排时可以考虑的问题

尚未决定，先记在这里，避免提前写进 `course/` 或 `docs/`：

1. 是否只作为未来认知，进入 `course/knowledge-map.md`，不写正文？
2. 若写概念篇，讲的是「Wiki 空间 / 节点 / 文档 token」还是更泛的「Agent 如何接入办公套件」？
3. 若写机制篇，最小实验是 CLI 建空间写一篇文档，还是 OpenAPI 的 token 换取与权限失败？
4. 是否与 Channel SDK、远程 MCP、CLI 三层能力做成一篇「Agent 集成飞书」概念，而不是单独讲 Wiki？
5. 产品侧要不要把飞书当作评审结果的导出通道；若要，属于哪个 V 版本，非目标是什么？
6. 本文是否继续留在 `other/feishu/`，还是拆成课程正文后把本盘点删减为索引？

## 主要来源

| 主题 | 链接 |
| --- | --- |
| Agent 集成总览 | https://open.feishu.cn/document/mcp_open_tools/overview-of-lark-agent-integration-capabilities |
| 飞书开放平台 | https://open.feishu.cn/ |
| 飞书 CLI 说明 | https://open.feishu.cn/document/mcp_open_tools/feishu-cli-let-ai-actually-do-your-work-in-feishu |
| CLI 源码与 skill | https://github.com/larksuite/cli |
| 知识库概述 | https://open.feishu.cn/document/server-docs/docs/wiki-v2/wiki-overview |
| 创建知识空间 | https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/space/create |
| 创建节点 | https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/space-node/create |
| 知识库 FAQ | https://open.feishu.cn/document/server-docs/docs/wiki-v2/wiki-qa |
| 远程 MCP 工具 | https://open.feishu.cn/document/mcp_open_tools/supported-tools |
| 远程 MCP 调用说明 | https://open.feishu.cn/document/mcp_open_tools/end-user-call-remote-mcp-server |
| 本地 OpenAPI MCP | https://github.com/larksuite/lark-openapi-mcp |
| MCP 高级配置 / 预设工具集 | https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/mcp_integration/advanced-configuration |
