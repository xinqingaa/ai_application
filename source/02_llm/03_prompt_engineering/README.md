# 03. Prompt Engineering - 实践指南

> 本文档说明如何跟着 [学习文档](../../../docs/02_llm/03_prompt_engineering.md) 一步步完成第三章实践

---

## 核心原则

```text
先定义任务 -> 再设计 Prompt -> 再做小样本评估 -> 再模板化 -> 最后沉淀可复用资产
```

- 在 `source/02_llm/03_prompt_engineering/` 目录下操作
- 第三章的重点不是“写一句更像 AI 的话”，而是把 Prompt 当成任务接口来设计
- 没有 API Key 时，也能完成大部分学习：看 Prompt 结构、做变量校验、做评估设计、跑 mock
- 有真实模型时，优先使用百炼 / 通义、DeepSeek、GLM 这些 OpenAI-compatible 平台做实验
- 这章必须反复改 Prompt，不能只运行一次脚本就结束

---

## 项目结构

```text
03_prompt_engineering/
├── README.md                      ← 你正在读的这个文件
├── .env.example                   ← 第三章环境变量模板
├── prompt_utils.py                ← 公共工具：配置、Prompt 审计、模板校验、真实/Mock 调用
├── 01_prompt_basics.py            ← 第 1 步：Prompt 结构、失败模式、基础调试
├── 02_few_shot.py                 ← 第 2 步：Zero-shot / 坏 Few-shot / 好 Few-shot 对比
├── 03_task_decomposition.py       ← 第 3 步：复杂任务拆解
├── 04_prompt_templates.py         ← 第 4 步：模板库、变量校验与渲染导出
├── prompts/
│   ├── requirement_summary_v1.txt
│   ├── requirement_summary_v2.txt
│   ├── sentiment_zero_shot.txt
│   ├── sentiment_few_shot.txt
│   ├── support_analysis.txt
│   └── support_reply.txt
├── data/
│   ├── reviews.json               ← 情感分类评估样例
│   └── support_tickets.json       ← 工单拆解样例
└── exports/                       ← 脚本运行时自动导出的模板预览
```

---

## 前置准备

### 1. 安装依赖

推荐先进入虚拟环境，再安装：

```bash
pip install openai python-dotenv tiktoken
```

依赖说明：

- `openai`：用于调用 OpenAI-compatible 平台
- `python-dotenv`：从 `.env` 自动加载环境变量
- `tiktoken`：估算 Prompt 大小，观察 Few-shot 带来的上下文成本

### 2. 配置环境变量

把 `.env.example` 复制为 `.env`，按你当前可用的平台填写。

这一章建议优先做两类练习：

1. 用国内低成本平台做真实 Prompt 对比实验
2. 用 mock 和本地模板渲染完成工程化练习

### 3. 运行方式

```bash
cd source/02_llm/03_prompt_engineering

python 01_prompt_basics.py
python 02_few_shot.py
python 03_task_decomposition.py
python 04_prompt_templates.py
```

---

## 第 1 步：Prompt 结构、失败模式与基础调试（文档第 2-4 章）

**对应文件**：`01_prompt_basics.py`  
**对应文档**：第 2 章「Prompt 不是聊天话术，而是任务接口」+ 第 3 章「常见失败模式」+ 第 4 章「稳定 Prompt 的结构」

### 这一步要解决什么

很多人一开始会把 Prompt 优化理解成“把话说漂亮一点”。这一步要纠正这个习惯，建立三个更重要的判断标准：

1. 任务边界清不清楚
2. 输出格式稳不稳定
3. 失败时能不能定位问题出在哪

### 操作流程

1. 先读文档第 2-4 章。
2. 打开 `01_prompt_basics.py`，重点看三个 Prompt 版本：
   - `build_vague_prompt()`
   - `build_conflicted_prompt()`
   - `build_structured_prompt()`
3. 再看 `print_result_detail()`，理解脚本如何从角色、任务、上下文、约束、输出格式等维度做 Prompt 审计。
4. 运行：

```bash
python 01_prompt_basics.py
```

### 重点观察

- 三个 Prompt 的 `score` 差异
- `estimated_tokens` 会不会随着你补充约束明显上升
- 为什么“目标冲突”的 Prompt 往往比“信息少”的 Prompt 更难调
- 如果没有配置 API，mock 输出是不是仍然能帮助你判断 Prompt 是否完整

### 建议主动修改

- 给坏 Prompt 增加一个清晰输出格式，看看审计分如何变化
- 删掉好 Prompt 里的负向限制，观察结构分变化
- 把“面向前端开发者”改成“面向产品经理”，再看输出是否偏向变化
- 把字数约束改成更小的值，观察模型是否更容易遗漏字段

### 学完这一步后你应该能回答

- 为什么 Prompt 的问题不只是“内容太短”
- 为什么“先补结构，再调措辞”是更高效的调试顺序
- 什么叫 Prompt 失败的可定位性

---

## 第 2 步：Few-shot 评估与示例设计（文档第 5 章）

**对应文件**：`02_few_shot.py`  
**对应文档**：第 5 章「Few-shot：用示例对齐边界」

### 这一步要解决什么

很多同学知道 Few-shot 能提升稳定性，但常犯两个错误：

1. 把示例写成“看起来像例子”而不是“真正约束边界的样本”
2. 只看单条效果，不做小样本评估

这一节就是要把 Few-shot 从“感觉更稳”变成“能评估、能解释”的工程动作。

### 操作流程

1. 先读文档第 5 章，理解：
   - Zero-shot / One-shot / Few-shot 的区别
   - 什么叫高质量示例
   - 为什么标签一致性很重要
2. 打开 `data/reviews.json`，看样本是如何设计的。
3. 打开 `02_few_shot.py`，不要只看三个 Prompt 字符串，按下面顺序读：
   - `build_zero_shot_prompt()`
   - `build_bad_few_shot_prompt()`
   - `build_good_few_shot_prompt()`
   - `build_strategy_catalog()`
   - `evaluate_case()`
   - `evaluate_strategy()`
4. 运行：

```bash
python 02_few_shot.py
```

### 代码执行流程

```text
load_cases()
-> build_strategy_catalog()
-> evaluate_strategy(strategy)
-> evaluate_case(case)
-> strategy.prompt_builder(text)
-> run_chat()
-> normalize_label()
-> 对比 expected / predicted
-> 打印总览和详情
```

你可以把这段脚本理解成“一个最小评估器”，而不是“三个零散函数”。

- 外层循环：`evaluate_strategy()` 逐个比较 Zero-shot、坏 Few-shot、好 Few-shot
- 内层循环：`evaluate_case()` 用同一批样本测试当前策略
- 核心目标：看哪种策略在同一批数据上更稳定，而不是看哪一条输出最顺眼

### 运行后先看哪里

1. 先看“脚本执行流程”和“数据集概览”，搞清楚评估对象是什么。
2. 再看“三种策略总览”，理解三类 Prompt 各自扮演什么角色。
3. 再看“评估结果总览”，比较 token 成本、准确率和 mock 情况。
4. 最后再看每个策略的“Prompt 预览”“逐条样本结果”“首条样本 debug_info”。

### 重点观察

- 坏 Few-shot 为什么会出现标签体系不一致的问题
- 好 Few-shot 里为什么专门加入“有好有坏”的中性样本
- Prompt token 数量增加了多少
- 如果配置了真实模型，`accuracy@N` 的差异是否明显

### 建议主动修改

- 把 `reviews.json` 再加 3 条你的真实业务样本
- 把好 Few-shot 的其中一个中性示例删掉，再观察表现
- 故意把一个示例标签写错，看模型会不会被带偏
- 把 `temperature` 改成 `0.3` 或 `0.5`，看看分类是否更飘
- 把 `DEFAULT_MAX_CASES` 改大一点，再观察三种策略的整体趋势是否一致

### 学完这一步后你应该能回答

- 为什么 Few-shot 不是“示例越多越好”
- 为什么示例的标签、格式、粒度必须统一
- 为什么分类任务最好配一个小评估集，而不是靠肉眼感觉

---

## 第 3 步：复杂任务拆解（文档第 6 章）

**对应文件**：`03_task_decomposition.py`  
**对应文档**：第 6 章「复杂任务要拆成步骤，而不是继续堆 Prompt」

### 这一步要解决什么

复杂 Prompt 常见的失败点不是模型不会回答，而是它在同一个回合里同时做太多事：

- 提取事实
- 判断优先级
- 生成回复
- 控制语气

一旦结果不理想，你很难判断到底是哪一层出了问题。拆解就是为了解决这个问题。

### 操作流程

1. 先读文档第 6 章。
2. 打开 `data/support_tickets.json`，理解练习任务。
3. 打开 `03_task_decomposition.py`，重点看：
   - `build_single_step_prompt()`
   - `build_analysis_prompt()`
   - `build_reply_prompt()`
4. 运行：

```bash
python 03_task_decomposition.py
```

### 重点观察

- 单步 Prompt 的输出有没有把分析、结论、回复混在一起
- 拆解步骤 1 的中间结果是否足够清晰，能不能被人类审阅
- 步骤 2 是否因为依赖了分析结果而更稳定
- 如果回复阶段跑偏，你能不能直接回到分析阶段排查，而不用重写所有 Prompt

### 建议主动修改

- 自己新增一条工单，把问题类型换成“功能找不到入口”
- 在分析 Prompt 里补一个“风险等级”字段，再看回复是否更克制
- 故意删掉“不要承诺恢复时间”，观察回复会不会乱承诺
- 试着把单步 Prompt 写得更长，再和拆解版比较

### 学完这一步后你应该能回答

- 什么时候该拆 Prompt，什么时候不需要
- 为什么中间结果要显式化
- 为什么拆解不是“把一次调用变复杂”，而是“把错误变可定位”

---

## 第 4 步：Prompt 模板库、变量校验与渲染导出（文档第 7 章）

**对应文件**：`04_prompt_templates.py`  
**对应文档**：第 7 章「Prompt 模板工程化」

### 这一步要解决什么

当 Prompt 开始进入真实项目后，最大的风险不是“写不出来”，而是：

- 字符串散落在代码里
- 每个人都在偷偷改 Prompt
- 改了以后没有变量校验
- 不知道当前线上到底用的是哪个版本

这一节会把 Prompt 从“脚本里的字符串”升级成“能被管理的模板资产”。

### 操作流程

1. 先读文档第 7 章。
2. 打开 `prompts/` 目录，看模板命名和分类方式。
3. 打开 `04_prompt_templates.py`，重点看：
   - `PromptLibrary`
   - `describe()`
   - `render()`
   - `write_json_export()`
4. 运行：

```bash
python 04_prompt_templates.py
```

### 重点观察

- 每个模板有哪些变量
- `missing_variables` 和 `unused_variables` 是否能帮你提前发现错误
- `requirement_summary_v1.txt` 与 `requirement_summary_v2.txt` 的工程价值差异
- 导出的 `exports/template_preview_*.json` 能不能作为评审资料或回归对照

### 建议主动修改

- 新增一个 `prompts/translate_basic.txt`
- 故意少传一个变量，观察校验结果
- 把 `support_reply.txt` 改成更严格的输出格式
- 给模板加版本号后缀，自己设计一套命名规范

### 学完这一步后你应该能回答

- Prompt 为什么应该文件化、模板化、版本化
- 为什么渲染前校验变量是必须的
- 为什么模板预览导出能帮助评审和回归

---

## 文档章节与文件对应表

| 文档章节 | 核心内容 | 对应文件 |
|---------|---------|---------|
| 第 2-4 章 | Prompt 结构、失败模式、调试顺序 | `01_prompt_basics.py`, `prompt_utils.py` |
| 第 5 章 | Few-shot 设计、样本评估、标签一致性 | `02_few_shot.py`, `data/reviews.json` |
| 第 6 章 | 复杂任务拆解、分阶段 Prompt | `03_task_decomposition.py`, `data/support_tickets.json` |
| 第 7 章 | 模板化、变量校验、渲染导出 | `04_prompt_templates.py`, `prompts/`, `prompt_utils.py` |

---

## 建议的学习顺序

1. 先跑 `01_prompt_basics.py`
2. 再跑 `02_few_shot.py`
3. 然后跑 `03_task_decomposition.py`
4. 最后跑 `04_prompt_templates.py`

这个顺序分别对应四个能力：

1. 会判断 Prompt 是否完整
2. 会用示例稳定边界任务
3. 会把复杂任务拆开
4. 会把 Prompt 做成能管理的资产

---

## 常见问题

### 1. Prompt 是不是越长越好？

不是。长 Prompt 只能说明你写了很多字，不能说明任务边界更清楚。只要复杂到难以稳定完成，就应该考虑拆解，而不是盲目加字。

### 2. Few-shot 是不是一定比 Zero-shot 好？

不是。对于边界清晰、格式简单的任务，Zero-shot 已经够用。Few-shot 更适合分类、抽取、格式对齐这类任务。

### 3. 第三章为什么不直接追求“万能 Prompt”？

因为真实项目里不存在万能 Prompt。你真正需要的是：

- 明确任务边界
- 建立评估样本
- 快速迭代
- 做好模板管理

### 4. 没有 API Key 能不能学完这一章？

可以学完大部分内容。你至少可以完成：

- Prompt 结构审计
- Few-shot 数据集设计
- 任务拆解练习
- 模板变量校验和导出

真正需要 API 的部分主要是效果对比和小样本验证。

---

## 建议你自己追加的练习

1. 选一个你自己的业务场景，写 3 个版本的 Prompt，并自己做结构审计。
2. 给分类任务准备 10 条真实样本，做一次 Zero-shot vs Few-shot 的小评估。
3. 找一个复杂任务，强制拆成“分析阶段”和“生成阶段”两步。
4. 在 `prompts/` 目录里建立你自己的命名规范，例如 `task_name__v1.txt`。
5. 每次改 Prompt 都记录“改了什么、预期改善什么、实际有没有改善”。

如果你把这五件事做完，第三章就不是“看过了”，而是真的开始具备 Prompt 工程能力。
