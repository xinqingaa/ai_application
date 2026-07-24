# LLM 在 AI 应用中的位置与边界

> 概念篇：从「LLM 是什么」出发，理解需求评审助手为什么需要模型，以及模型、RAG、Agent、Workflow 与普通程序分别负责什么。

---

## 为什么聊天能力还不是 AI 应用

本篇是模型能力的概念入口。如果你已经用过 ChatGPT 网页版或调通过 API，你会熟悉「问一句、答一句」；如果你主要做前端或客户端，可能还不清楚：**把 LLM 接进一个真实产品，和「打开聊天网页」差在哪里**。下面分三层说明「真实问题」——先说你作为学习者为什么要读这一篇，再说产品为什么需要 LLM 层，最后说工程上会踩哪些坑。

### 学习者真实问题：我遇到的困惑

- **LLM 到底是什么？** 是一个网站、一个 API、还是一个可以部署的模型文件？和我写的 Python / Flutter 代码是什么关系？
- **为什么需求评审助手要用 LLM？** 不能像传统软件一样写死规则「如果 PRD 里没有验收标准就报错」吗？
- **ChatGPT 已经能评审需求了，为什么还要学一门「LLM 课」？** 网页聊天和「需求评审助手」是一回事吗？
- **后面会学的 RAG、Agent 和 LLM 是什么关系？** 会不会重复学很多东西？

读完全篇，你应能回答：LLM 在本项目里是**生成与推理引擎**；RAG / Agent 是在 LLM 之上叠加**知识**与**行动**；模型调用层负责把引擎用得**稳定、可配置、可观测**，不负责知识库和工具执行。

### 产品真实问题：需求评审助手里发生什么

下面是一段**连续业务场景**（虚构但贴近真实研发流程）：

产品同学小周提交一份 PRD 片段：「订单详情页新增『申请售后』按钮，点击后进入售后申请流程，需对接售后接口 v2。」评审负责人希望助手帮忙：**列出潜在风险、说明依据、输出能进评审会议的结构化结论**。

若团队第一次做 AI 功能，最容易的做法是：把 PRD 全文复制到 ChatGPT，粘贴一句「请评审这份需求」。短期内「看起来能用」，但很快会遇到：

1. **小周第二次提交相似需求，风险列表和上次完全不一样**——会议里无法对比「这次比上次多发现了什么」。
2. **助手说「可能与支付模块冲突」**，问依据是哪一段，回答模糊或引用不存在——**无法用于正式评审**。
3. **PRD 很长，还希望带上接口文档、历史评审**，一次性粘贴超过模型上下文或中间段落被模型忽略。
4. **前端要把「风险等级、分类、建议」展示成卡片**，模型返回一大段 Markdown，**程序无法稳定解析**。
5. **开发阶段用便宜模型、演示用强模型**，代码里写死一个模型名，**换供应商要改很多文件**。
6. **用户只看到转圈 30 秒**，不知道是在「读文档」「查知识库」还是「已经失败」——体验像黑盒。

这些痛点**不全是「模型不够聪明」**。很多是：**没有把 LLM 当作应用系统里的一层来设计**——缺少统一的调用方式、任务描述（Prompt）、输出格式（Schema）、日志与成本记录。这就是「LLM 应用工程」要解决的问题；相关机制统一沉淀为 `llm_core` 包。

### 工程真实问题：只调一次 API 为什么不够

当需求评审助手从 Demo 走向可迭代产品时，工程上必须提前考虑：

| 工程问题 | 若只「调一次 API」会怎样 | 对应机制 |
| --- | --- | --- |
| 输出不稳定 | 无法回归对比，改 Prompt 不知好坏 | Harness 样例 + 版本记录（调用 Harness） |
| 上下文超限 | 长 PRD 被截断或漏看中间段 | Context 预算；RAG 按需检索 |
| 不可解析 | 前端 / DB / Workflow 接不住 | Structured Outputs（结构化输出机制） |
| 成本不可控 | 多轮、多 Agent 后账单失控 | usage 记录 + 成本基线（成本、延迟与缓存机制） |
| 供应商绑定 | 换模型改遍业务代码 | Provider 抽象（模型 API 与 Provider 抽象） |
| 失败不可观测 | 不知超时是网络还是模型 | 统一错误类型 + 日志（可靠调用机制） |
| 体验黑盒 | 用户只能干等 | 流式事件（流式与对话机制）；检索态由 RAG + 前端展示 |

注意：**检索是否命中、引用是否正确、工具是否越权**——LLM 层单独解决不了，需要 RAG、Agent 与评估观测共同完成。本篇只建立边界，避免把模型调用误当成完整 AI 应用。

### 和「打开 ChatGPT 网页」的对比

| | ChatGPT 网页 | 需求评审助手（AI 应用） |
| --- | --- | --- |
| 谁组织上下文 | 产品方 + 用户手动粘贴 | 应用：PRD、检索片段、历史摘要 |
| 谁规定输出格式 | 用户每次口头要求 | 应用：Schema + Prompt 模板 |
| 谁保证有依据 | 无强制 | 应用 + RAG：引用、拒答（V1 起） |
| 谁记录每次调用 | 平台内部 | 你的服务：usage、latency、版本 |
| 谁对结果负责 | 用户自己判断 | 团队：eval、bad case、人工确认 |

---

## 模型层的最小心智模型

### LLM 是什么（应用开发者版）

**LLM（Large Language Model，大语言模型）** 是一个通过海量文本训练得到的**文本生成模型**。你给它一段输入（通常叫 **Prompt** 或 **上下文**），它**逐 token（词元）预测下一个最可能出现的 token**，直到结束。

关键直觉（不需要会推公式）：

- 它**不是在数据库里查标准答案**，而是根据读过的模式「续写」看起来合理的文本。
- 所以同一问题**可能答对，也可能编造**——尤其当材料里没有依据时。
- **温度（temperature）** 等参数控制随机性：越低越稳定，越高越发散。

在本项目里，LLM 的**输入**通常是：系统指令 + 用户问题 +（可选）PRD 片段 / 检索到的证据。  
**输出**通常是：自然语言，或按 Schema 生成的 JSON（结构化输出机制）。

**和已有概念的区别：**

| 概念 | 做什么 | 和 LLM 的分工 |
| --- | --- | --- |
| 传统程序 / 规则引擎 | 按 if-else 执行确定逻辑 | 适合硬规则；不适合开放式「读 PRD 找风险」 |
| 搜索引擎 | 关键词匹配文档 | 返回链接，不帮你写评审结论 |
| 数据库 | 存取结构化数据 | 存评审结果；不生成分析 |
| LLM | 读文本、生成文本 / 结构化内容 | 需求理解、风险描述、报告草稿 |
| RAG（后续课） | 先检索再生成 | 解决「模型不知道公司内部文档」 |
| Agent（后续课） | 多步决策 + 调工具 | 解决「需要查系统、走流程」 |

需求评审助手**需要 LLM**，是因为评审内容大量是**非结构化文本**（PRD、规则、会议纪要），要产出**自然语言 + 结构化字段**的混合结果；纯规则难以覆盖「这份 PRD 在弱网场景有没有风险」这类开放问题。

### LLM 在需求评审助手中的位置

```text
用户 / 前端
    ↓ 提交 PRD、提问
API 服务（FastAPI，可靠调用 / 调用 Harness）
    ↓
llm_core                    ← 本篇定义的「模型层」
    · 选哪个模型、怎么调
    · 用什么 Prompt、什么 Schema
    · 记录 usage / 错误
    ↓
（可选）rag_core 提供 evidence   ← RAG 机制
（可选）agent_core 多步执行       ← Agent 机制
    ↓
评审结论、报告、引用展示          ← AI Native 交互与项目篇
```

**模型调用层不负责：** 文档上传与向量索引、检索策略、工具执行、人工审批流程、完整质量平台。  
**模型调用层负责：** 无论上层是固定 RAG 还是多 Agent，都通过**同一套** `LLMClient`、Prompt 集、Schema 去调用模型。

### 四要素：为什么「看起来能答」却不可信

一次 LLM 调用是否可用于评审，取决于四要素是否一起设计：

```text
Prompt（任务协议：你是谁、要做什么、不能做什么）
+ 模型与参数（用哪个 model、temperature、max_tokens）
+ 上下文（PRD 片段、检索证据、历史摘要——放进 Prompt 的材料）
+ 输出 Schema（ReviewRisk、ReviewReport 等字段契约）
→ 应用校验后的结果（才能进 DB / 前端 / eval）
```

**反例：** 只写好 Prompt「请输出 JSON 风险列表」，没有 Schema 校验——模型可能 JSON 语法对，但字段缺失或 `source_id` 造假。  
**反例：** 上下文塞进 10 万字 PRD，没有裁剪——模型可能忽略中间的接口约束段落。

### 应用侧必须承担的职责

| 职责 | 通俗解释 | 在本项目的落点 |
| --- | --- | --- |
| 上下文管理 | 什么材料进 Prompt、多长、如何编号引用 | 上下文工程 context；RAG context builder |
| 约束与校验 | 输出是否符合 schema、引用是否存在于材料中 | 结构化输出 schema；RAG citation checker |
| 回归与对比 | 改 Prompt / 换模型后，同一批问题结果是否变好 | 调用回归机制；评估观测 |
| 观测 | 花了多少 token、多久、失败原因 | Provider 调用层 LLMResponse；可靠调用 reliability |

**常见误区：**

- **误区 1：**「Prompt 写得好就不会胡说」——没有外部知识时，模型仍会编造；需要 RAG 或拒答。
- **误区 2：**「用最强模型就不用工程化」——强模型也会超限、也会 JSON 格式错误、也更贵。
- **误区 3：**「LLM 课学完就能做完整助手」——助手 = LLM + 知识 + 流程 + 前端 + eval。
- **误区 4：**「网页聊天体验 = 产品体验」——产品要状态、引用、权限、日志，网页不负责这些。

更底层的「下一个 token 预测 / Transformer」属于按需补充的原理知识，不是当前项目主链路的前置要求。

---

## 观察一次真实模型调用

目标：**亲手看清一次调用里有什么**，建立「模型返回的不是魔法，是一串可记录的响应」的直觉。  
实现见 [`source/demos/02_llm_basics/`](../../source/demos/02_llm_basics/)。

### 前置

- 根目录 uv 环境已同步：`uv sync`。
- 复制 [`.env.example`](../../.env.example) 为 `.env` 并填写 `OPENAI_API_KEY`（本 demo **必须**有真实 Key，不做 mock）。
  ```bash
  cp .env.example .env
  # OPENAI_API_KEY=sk-...
  # OPENAI_BASE_URL=https://...   # OpenAI 兼容平台时可选
  # OPENAI_MODEL=gpt-4o-mini
  ```

### 一次 Chat 调用里有什么

HTTP 层面：你的 Python 程序 `POST` 到 `/v1/chat/completions`（或兼容地址），Body 核心是 **messages** 数组：

```json
[
  {"role": "system", "content": "你是需求评审助手，只基于用户提供的材料回答。"},
  {"role": "user", "content": "【PRD 片段】... 请列出 3 条潜在风险。"}
]
```

响应里你至少要会找：

- `choices[0].message.content` —— 模型生成的文本
- `usage.prompt_tokens` / `usage.completion_tokens` —— 计费用
- `model` —— 实际使用的模型 id

### 第一次调用（`02_llm_basics`）

入口：[`source/demos/02_llm_basics/first_chat.py`](../../source/demos/02_llm_basics/first_chat.py)。  
Provider 抽象与切换对比见模型 API 与 Provider 抽象（[`02_model_contracts`](../../source/demos/02_model_contracts/)）。

核心调用逻辑（节选）：

```python
t0 = time.perf_counter()
resp = client.chat.completions.create(
    model=model,
    messages=messages,
    temperature=args.temperature,
)
latency_ms = (time.perf_counter() - t0) * 1000
# 打印 resp.model、resp.usage、latency_ms、content 前 300 字
```

样例 S1–S5 定义在 [`samples.json`](../../source/demos/02_llm_basics/samples.json)，默认跑 S2（售后 PRD 风险识别）。

### 运行与观察

```bash
cd source/demos/02_llm_basics
uv run python first_chat.py
uv run python first_chat.py --temperature 0.7
uv run python first_chat.py --sample S4
```

应看到：`sample`、`model`、`usage`（prompt/completion tokens）、`latency_ms`、`content preview`。详见 [demo README](../../source/demos/02_llm_basics/README.md)。

### 建议做的两个对比实验

用**同一条 user 消息**：

1. **`temperature=0` vs `0.7`** —— 观察风险表述是否更「飘」、是否出现材料里没有的模块名。
2. **换 model**（如 `gpt-4o-mini` vs 更强模型）—— 观察 `usage`、`latency_ms`、风险是否更贴材料。

记录到一个简单表格（笔记本或 CSV 即可），字段：`model`, `temperature`, `prompt_tokens`, `completion_tokens`, `latency_ms`, `notes`。这就是调用 Harness harness 的雏形。

### 观察重点（写进实验笔记）

- 材料里**没写**的内容，模型是否**仍然断言**（例如「需要兼容 iOS 12」）—— 体会「概率生成 ≠ 有依据」。
- `prompt_tokens` 如何随 PRD 变长而增加—— 体会后面为什么要 context 预算和 RAG。
- 要求「只输出 JSON」时，是否仍夹带 Markdown 说明—— 体会为什么要 Schema + 校验（结构化输出机制）。

---

## SDK、兼容接口与框架怎样分工

| 方式 | 是什么 | 在本项目中的位置 |
| --- | --- | --- |
| **OpenAI SDK** | 官方 Python 客户端，也支持 `base_url` 对接兼容 API | M1 起封装进 `llm_core`（模型 API 与 Provider 抽象） |
| **OpenAI 兼容 HTTP** | 同一 JSON 格式，换 base_url / key | 国内多数平台；由 Provider 适配 |
| **LangChain ChatModel** | 框架对 Chat API 的再封装 | RAG 组合链仍读 `llm_core` 配置，避免两套 model 名 |
| **LangGraph** | 带状态的图执行 | Agent / Workflow 节点内调用 `LLMClient` |

原则：**业务代码只依赖 `llm_core`，不 scattered 地 `OpenAI(...)`**。这样换供应商、记日志、统一错误类型只需改一处。

---

## 模型层的失败与责任边界

### 在本场景下常见的「看起来能用其实不行」

| 现象 | 可能原因 | 谁来解决 |
| --- | --- | --- |
| 风险列表每次不同 | 概率生成 + 参数 | temperature、固定 Prompt、eval 回归 |
| 编造接口/规则 | 材料未提供 | RAG + 拒答（V1） |
| 回答变短、漏后半段 PRD | 上下文截断 | Context 工程；RAG 只检索相关 chunk |
| 前端接不住结果 | 自由文本 | Schema（V1） |
| 429 / 超时 | 平台限流、网络 | 错误分类、fallback（可靠调用机制） |

### LLM 层**单独**无法可靠负责的 5 类事

1. **企业内部知识从哪来、是否最新** → RAG 知识库与入库  
2. **答案是否有依据、引用是否真实** → RAG 检索 + citation checker（V1）  
3. **查工单、调接口、多步流程** → Agent / Workflow  
4. **改 Prompt 后是否真的变好** → golden set / bad case 评估  
5. **用户看到进度、人工确认** → AI Native 工作台  

### 不在本篇展开

- RAG 主链路、LangChain Document / Retriever  
- FastAPI、SSE、Docker  
- 项目版本与交付顺序 → [集中知识地图](../knowledge-map.md)  

---

## 从第一次调用开始留下事实

从**第一次**调用开始就养成记录习惯；**SDK 最小调用 的 demo 在终端打印** `usage` 与 `latency_ms`，完整字段表与结构化落盘在 **Provider 调用层**（`LLMResponse`）与 **调用 Harness**（harness）实现。

### 最小日志字段（全课目标；SDK 最小调用 仅部分在终端可见）

| 字段 | 用途 | SDK 最小调用 demo |
| --- | --- | --- |
| `timestamp` | 对比不同天的实验 | 手工记笔记 |
| `model` / `provider` | 选型 | 终端打印 `model` |
| `temperature` 等 | 复现 | 终端打印 / CLI 参数 |
| `usage.prompt_tokens` / `completion_tokens` | 成本 | 终端打印 `usage` |
| `latency_ms` | 体验 | 终端打印 |
| `input_summary` | 样例标识 | `sample` id（如 S2） |
| `output_preview` | 人工回看 | `content preview`（前 300 字） |
| `notes` | 是否编造、是否可用 | 建议手写对比实验笔记 |

### 最小调用样例集（S1–S5 种子；批量回归在 调用 Harness）

样例数据在 [`samples.json`](../../source/demos/02_llm_basics/samples.json)；默认跑 S2。完整批量对比由 Calling Harness 承担，最小调用 demo 不实现 JSONL 或自动跑批。

---

## 在需求评审助手中落位

为**需求评审助手**定义 LLM 层职责边界（本专题不写代码实现，只定契约）：

| 任务 | LLM 层做什么 | LLM 层不做什么 |
| --- | --- | --- |
| 需求摘要 | 压缩 PRD、提取目标与范围 | 不补充材料里没有的功能 |
| 风险识别 | 按 Prompt 维度描述风险 | 不做最终过会结论 |
| 结构化输出 | 按 Schema 填字段 | 不跳过 Pydantic 校验 |
| 引用说明 | 在 Prompt 要求下绑定 source_id | 不验证 id 真假（校验在 RAG/应用） |
| 拒答建议 | 输出「证据不足」类结论 | 无依据时不强答 |

### 与项目版本

| 版本 | LLM 层支撑 |
| --- | --- |
| **V0** | 能调模型 + 固定 Prompt 生成（配合 RAG 检索上下文） |
| **V1** | + Schema 评审报告 + 拒答结构（Prompt 工程、结构化输出） |

---

## 模型层交给后续能力的契约

### 能力边界总表

| 能力 | 模型调用层 | 下游 |
| --- | --- | --- |
| 统一模型调用 | Provider 调用层–10 `llm_core` | — |
| Prompt 任务协议 | Prompt 工程 | — |
| Structured Output | 结构化输出 | — |
| 流式 / 上下文 / 可靠性 / harness | 流式机制–调用 Harness | — |
| 检索 / 引用 / 拒答逻辑 | 概念 | RAG |
| Tool / Agent / Workflow | 认知 | Agent / Workflow |
| 系统化 eval / trace | 铺垫 | 评估观测 |
| 运行态 UI | 事件格式铺垫 | AI Native 交互 |

### `llm_core` 目标结构（设计输入）

```text
source/packages/llm_core/
├── client.py           # LLMClient（Provider 调用层）
├── providers/          # 多供应商（Provider 调用层）
├── prompts/            # 模板 registry（Prompt 工程）
├── schemas/            # Pydantic（结构化输出）
├── context/            # 上下文构造（上下文工程）
├── streaming/          # 事件（流式机制）
├── reliability/        # 错误与降级（可靠调用）
└── harness/            # 回归样例（调用 Harness）
```

### 交给模型 API 与 Provider 抽象–结构化输出 的设计清单

1. `LLMResponse` 统一响应 + 错误枚举  
2. `models.yaml`：Chat / Embedding / Rerank 分角色  
3. 命名 Prompt：`requirement_summary`、`risk_review` 等  
4. 核心 Schema：`ReviewRisk`、`ReviewReport`、`Citation`、`RefusalResponse`  
5. 上文 5 条样例集（[`samples.json`](../../source/demos/02_llm_basics/samples.json)）+ 日志字段约定  

---

## 读完后应该能做什么

- **能解释**：LLM 是什么（应用开发者版）；它和规则程序、搜索、数据库的分工。  
- **能解释**：为什么需求评审助手不能只做「复制 PRD 到 ChatGPT」。  
- **能讲述**：小周提交售后 PRD 时，只做一次 API 调用会在产品/工程上出哪些问题（至少 3 点）。  
- **能画出**：用户 → API → `llm_core` →（RAG / Agent）→ 报告 的数据流。  
- **能运行**：[`02_llm_basics`](../../source/demos/02_llm_basics/README.md) 最小 chat，并解读 `usage` 与 `latency_ms`。  
- **能列举**：5 类 LLM 层无法单独解决的事及对应课程/模块。  

### 自检题（不看正文能否答）

1. LLM 的「生成」和数据库「查询」本质区别是什么？  
2. 为什么 `temperature=0` 仍然可能产生与材料不符的风险描述？  
3. 需求评审助手里，模型调用层和 RAG 各解决哪一类问题？  

---

## 继续学习

- 模型调用入口：[模型 API 与 Provider 抽象](../mechanisms/llm/model-api-and-provider.md)  
- 输入输出契约：[Prompt、Schema 与 Context](model-input-output-contracts.md)  
- 集中路线与知识清单：[knowledge-map.md](../knowledge-map.md)  
- 当前项目闭环：[V0 固定知识 RAG](../project/stage-1-single-agent-rag/v0-fixed-rag.md)  
