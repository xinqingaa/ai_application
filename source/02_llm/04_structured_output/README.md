# 04. 结构化输出 - 实践指南

> 本文档说明如何跟着 [学习文档](../../../docs/02_llm/04_structured_output.md) 一步步完成第四章实践

---

## 核心原则

```text
先让模型输出可解析 JSON -> 再用 Schema 验证 -> 再做重试修复 -> 最后封装成可复用提取器
```

- 在 `source/02_llm/04_structured_output/` 目录下操作
- 这一章的重点不是“让模型看起来像返回 JSON”，而是让结果真的能被程序稳定消费
- 没有 API Key 时，也可以完成大部分学习：看请求预览、跑 mock、理解解析与校验流程
- 有真实模型时，优先用百炼 / 通义、DeepSeek、GLM 做实验，感受不同 provider 对结构化输出约束的差异
- 如果某个平台原生 JSON Mode 或 Structured Outputs 支持不稳定，不要硬绑，直接退回 `Prompt JSON + Pydantic 验证`

---

## 项目结构

```text
04_structured_output/
├── README.md                   ← 你正在读的这个文件
├── .env.example                ← 第四章环境变量模板
├── structured_utils.py         ← 公共工具：配置、JSON 解析、Schema 校验、导出
├── 01_json_output.py           ← 第 1 步：自由文本 vs JSON 输出（文档第 2-3 章）
├── 02_pydantic_schema.py       ← 第 2 步：Pydantic Schema 与结构验证（文档第 4 章）
├── 03_retry_validation.py      ← 第 3 步：校验失败后的修复与重试（文档第 5 章）
├── 04_extractor.py             ← 第 4 步：通用结构化数据提取器（文档第 6 章）
├── data/
│   └── customer_notes.json     ← 批量提取练习样本
└── exports/                    ← 脚本运行时导出的提取报告
```

---

## 前置准备

### 1. 安装依赖

推荐先进入虚拟环境，再安装：

```bash
pip install openai python-dotenv pydantic
```

如果你想更准确地做 Token 或成本统计，可以额外装：

```bash
pip install tiktoken
```

### 2. 配置环境变量

把 `.env.example` 复制为 `.env`，按你当前可用的平台填写。

第四章建议优先完成两类实验：

1. 用国内 OpenAI-compatible 平台验证 JSON 输出和结构化提取
2. 用 mock 模式练习解析、校验和重试流程

### 3. 运行方式

```bash
cd source/02_llm/04_structured_output

python 01_json_output.py
python 02_pydantic_schema.py
python 03_retry_validation.py
python 04_extractor.py
```

---

## 第 1 步：自由文本 vs JSON 输出（文档第 2-3 章）

**对应文件**：`01_json_output.py`  
**对应文档**：第 2 章「为什么结构化输出是应用开发必修课」+ 第 3 章「从 Prompt JSON 到 JSON Mode」

### 这一步要解决什么

很多初学者知道“最好让模型返回 JSON”，但并没有真正建立下面这个差异感：

1. 对人类可读，不等于对程序可用
2. “看起来像 JSON”，不等于“真的能稳定解析”
3. Prompt 指定格式和接口级约束不是一回事

### 操作流程

1. 先读文档第 2-3 章。
2. 打开 `01_json_output.py`，重点看：
   - `build_free_text_prompt()`
   - `build_json_prompt()`
   - `parse_json_output()`
3. 运行：

```bash
python 01_json_output.py
```

### 重点观察

- 自由文本输出为什么对程序不稳定
- `JSON Prompt` 的输出能不能被 `parse_json_output()` 正常提取
- `response_format={"type": "json_object"}` 的请求预览长什么样
- 为什么课程里把 JSON Mode 当成“更强约束”，但仍然不把它当成唯一方案

### 建议主动修改

- 把样本文本换成你自己的业务文本
- 故意让 Prompt 没有“只输出 JSON”，观察解析结果
- 把字段示例删掉，看模型是否更容易漏字段
- 尝试给不同 provider 跑真实输出，比较差异

---

## 第 2 步：Pydantic Schema 与结构验证（文档第 4 章）

**对应文件**：`02_pydantic_schema.py`  
**对应文档**：第 4 章「为什么 JSON 还不够，必须有 Schema」

### 这一步要解决什么

即使模型返回了合法 JSON，也不代表它真的符合你的程序预期。你还需要校验：

- 字段是否齐全
- 类型是否正确
- 枚举值是否合法
- 嵌套对象是否符合约束

### 操作流程

1. 先读文档第 4 章。
2. 打开 `02_pydantic_schema.py`，重点看：
   - `LeadRecord`
   - `ContactChannel`
   - `schema_to_prompt_description()`
   - `model_validate()`
3. 运行：

```bash
python 02_pydantic_schema.py
```

### 重点观察

- `LeadRecord` 的 JSON Schema 长什么样
- Schema 描述是如何被拼进 Prompt 的
- 模型输出即使能 `json.loads()`，为什么还要再过一次 Pydantic
- 嵌套字段、可选字段、枚举字段分别怎么表达

### 建议主动修改

- 给 `LeadRecord` 增加一个 `phone` 字段
- 把 `intent_level` 改成更严格的枚举集合
- 增加 `team_size` 的上下界约束
- 看 Schema 一变，Prompt 描述和校验结果会如何联动变化

---

## 第 3 步：校验失败后的修复与重试（文档第 5 章）

**对应文件**：`03_retry_validation.py`  
**对应文档**：第 5 章「输出校验、错误反馈与重试」

### 这一步要解决什么

第四章最重要的工程意识之一是：

> 结构化输出失败，不应该只重跑原 Prompt。

你需要把错误显式反馈给模型，让它知道：

- 哪个字段错了
- 错在什么地方
- 下一次应该怎么修

### 操作流程

1. 先读文档第 5 章。
2. 打开 `03_retry_validation.py`，重点看：
   - `TicketExtraction`
   - `RobustStructuredClient`
   - `build_json_fix_prompt()`
3. 运行：

```bash
python 03_retry_validation.py
```

### 重点观察

- 第一次失败到底是 parse 错误还是 validate 错误
- 修复 Prompt 是如何把错误信息拼回去的
- 为什么 mock 模式里先故意返回错误结构
- 成功重试后，最终对象是如何被规范化的

### 建议主动修改

- 故意让 mock 第一次返回缺字段的 JSON
- 把 `priority` 的枚举改得更严格
- 调低或调高 `max_retries`
- 想一想：什么时候应该停止重试，改成人工检查

---

## 第 4 步：通用结构化数据提取器（文档第 6 章）

**对应文件**：`04_extractor.py`  
**对应文档**：第 6 章「从单次提取走向通用提取器」

### 这一步要解决什么

前面 3 个脚本解决的是结构化输出链路上的单点问题。第四步要把它们收束成一个更像真实项目的能力：

- 接收一批非结构化文本
- 根据 Schema 自动生成 Prompt
- 调用模型提取
- 自动校验
- 汇总成功 / 失败情况
- 导出结果报告

### 操作流程

1. 先读文档第 6 章。
2. 打开 `data/customer_notes.json`，看批量样本。
3. 打开 `04_extractor.py`，重点看：
   - `SalesLead`
   - `StructuredExtractor`
   - `extract_one()`
   - `extract_batch()`
4. 运行：

```bash
python 04_extractor.py
```

### 重点观察

- `StructuredExtractor` 真正复用的是什么
- 为什么 parse 错误和 validate 错误要分开统计
- 批量报告里哪些信息对后续调 Prompt 最有价值
- 导出的 `exports/extractor_report_*.json` 能如何帮助回归

### 建议主动修改

- 在 `customer_notes.json` 再加 3 条你自己的销售记录
- 给 `SalesLead` 增加一个 `need_demo` 布尔字段
- 把 `next_action` 改成更短、更明确的约束
- 尝试把 SalesLead 换成你自己的业务 Schema，比如工单提取或简历提取

---

## 文档章节与文件对应表

| 文档章节 | 核心内容 | 对应文件 |
|---------|---------|---------|
| 第 2-3 章 | JSON 输出、JSON Mode、解析问题 | `01_json_output.py`, `structured_utils.py` |
| 第 4 章 | Pydantic Schema、字段约束、嵌套对象 | `02_pydantic_schema.py`, `structured_utils.py` |
| 第 5 章 | 校验失败、修复 Prompt、重试策略 | `03_retry_validation.py`, `structured_utils.py` |
| 第 6 章 | 通用提取器、批量处理、报告导出 | `04_extractor.py`, `data/customer_notes.json`, `structured_utils.py` |

---

## 建议的学习顺序

1. 先跑 `01_json_output.py`
2. 再跑 `02_pydantic_schema.py`
3. 然后跑 `03_retry_validation.py`
4. 最后跑 `04_extractor.py`

这个顺序对应的能力递进是：

1. 先理解为什么要结构化
2. 再理解怎么定义结构
3. 再理解结构出错后怎么修
4. 最后理解怎么把这条链路做成可复用能力

---

## 常见问题

### 1. 第四章是不是一定要依赖某个平台的原生 Structured Outputs？

不是。原生能力当然更好，但不同平台支持差异很大。课程主线更强调你要掌握一套平台无关的最低可行方案：

- Prompt 指定 JSON
- JSON 解析
- Pydantic 验证
- 校验失败重试

### 2. 为什么已经返回 JSON 了，还要上 Pydantic？

因为 JSON 只能证明“格式像对象”，不能证明：

- 字段一定齐
- 类型一定对
- 值一定合法

Pydantic 才是把这些要求真正变成程序规则的那一层。

### 3. 重试是不是越多越好？

不是。重试会增加成本和延迟。一般 2-3 次足够，多了往往说明问题不在“偶发失败”，而在 Prompt、Schema 或模型能力本身。

### 4. 没有 API Key 能不能学完第四章？

可以学完绝大部分内容。你仍然可以完成：

- 请求预览理解
- JSON 解析流程
- Pydantic Schema 设计
- 修复 Prompt 设计
- 批量提取与导出流程

真正需要真实 API 的部分，主要是观察不同 provider 的真实输出差异。

---

## 建议你自己追加的练习

1. 选一个你自己的业务场景，定义一个 Pydantic Schema。
2. 准备 5 条非结构化文本，做一次批量结构化提取。
3. 故意制造 3 种错误：无效 JSON、缺字段、错误枚举值，观察修复流程。
4. 给提取器增加成功率统计和失败样本导出。
5. 比较 `Prompt JSON` 和某个 provider 原生 JSON 能力的稳定性差异。

如果你把这五件事做完，第四章就不只是“知道结构化输出是什么”，而是真正具备把模型输出接进程序的能力。
