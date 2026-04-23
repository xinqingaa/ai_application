# 01. RAG 基础概念 - 实践指南

> 本文档说明如何跟着 [学习文档](../../../docs/04_rag/01_rag_basics.md) 学完第一章，并在不依赖后续章节的前提下跑通最小 RAG 闭环，同时建立后续 `01-04` 共享的最小评估集。

---

## 核心原则

```text
先固定最小评估尺子 -> 再理解为什么需要 RAG -> 再看最小在线链路 -> 最后判断什么时候该用什么方案
```

- 在 `source/04_rag/01_rag_basics/` 目录下操作
- 本章不做项目骨架，不做多模块预埋，不接真实 Embedding / 向量库 / LLM
- 本章代码只保留四个目标：评估前置、问题意识、最小链路、方案边界
- 不需要 API Key
- `data/minimum_golden_set.json` 是课程共享样本资产，后续章节会继续复用

---

## 项目结构

```text
01_rag_basics/
├── README.md
├── rag_basics.py
├── 01_minimum_eval.py
├── 02_why_rag.py
├── 03_rag_pipeline.py
├── 04_solution_decision.py
├── data/
│   └── minimum_golden_set.json
└── tests/
    └── test_rag_basics.py
```

- `rag_basics.py`
  放本章所有最小对象、问题路由、内存知识库、关键词检索、回答生成、方案判断，以及 golden set 加载逻辑
- `01_minimum_eval.py`
  运行课程共享最小评估集，并按第一章边界打印 pass/fail
- `02_why_rag.py`
  对比“只做单次模型调用”和“先判断再选方案”面对同一个问题时的差异
- `03_rag_pipeline.py`
  逐步打印 `先路由 -> 再决定是否进入 RAG -> 检索 -> 上下文 -> 回答 + 来源`
- `04_solution_decision.py`
  把“什么时候该用长上下文 / 现有系统 / Hosted File Search / 固定 RAG / Hybrid RAG / Agentic RAG”变成可执行的判断示例
- `data/minimum_golden_set.json`
  课程共享最小样本，既保留课程目标，也保留第一章当前预期
- `tests/test_rag_basics.py`
  把第一章最重要的样本和边界正式锁进测试

---

## 前置准备

### 1. 运行目录

```bash
cd source/04_rag/01_rag_basics
```

### 2. 当前命令

```bash
python 01_minimum_eval.py
python 02_why_rag.py
python 03_rag_pipeline.py
python 04_solution_decision.py
python -m unittest discover -s tests
```

### 3. 先跑哪个

建议先跑：

```bash
python 01_minimum_eval.py
```

你最先要建立的直觉是：

- 第一章从一开始就要固定实验尺子，而不是改完再凭感觉判断
- 这份样本不仅服务第一章，也会继续服务后续 `01-04`
- 第一章当前只验证最小路由、最小来源和 toy RAG 边界

---

## 先怎么读代码

### 1. 第一遍只看对象

先打开 [rag_basics.py](./rag_basics.py)，只看这些数据对象：

- `KnowledgeChunk`
- `RetrievalResult`
- `AnswerResult`
- `RouteDecision`
- `RoutedAnswerResult`
- `Scenario`

这一遍的目标不是理解所有逻辑，而是先知道：

- 系统里有哪些最小运行时对象
- 每个对象分别描述哪一层状态
- 为什么第一章不是直接返回一个字符串

### 2. 第二遍只看主流程

然后再看这些函数：

- `route_question()`
- `retrieve()`
- `build_context()`
- `answer_with_rag()`
- `answer_question()`

这一遍只回答一个问题：

```text
一个问题进来以后，系统到底按什么顺序做事？
```

### 3. 第三遍再看评估和方案判断

最后再看：

- `load_minimum_golden_set()`
- `get_chapter_expectation()`
- `recommend_solution()`

这样读会比一开始从头到尾顺着扫更容易建立结构感。

---

## 第 0 步：先看课程共享最小评估集

**对应文件**：`01_minimum_eval.py`、`data/minimum_golden_set.json`

这一步不是完整评估平台，而是课程级最小起点。

重点观察：

- 样本里同时存在通用常识、结构化查询、私有知识和已知失败样本
- `course_target` 描述的是整门课最终想达到的方向
- `chapter_expectations.01_rag_basics` 锁定的是第一章今天真正能承诺什么
- `Python 系统课可以退钱吗？` 会被保留为已知缺口，后续章节继续复用

这里最重要的不是输出了多少 `PASS`，而是你要知道：

> 第一章在用什么尺子看系统行为。

---

## 第 1 步：再看为什么需要 RAG

**对应文件**：`02_why_rag.py`

这个脚本会打印三类问题：

1. 课程私有知识问题
2. 通用常识问题
3. 结构化系统查询

重点观察：

- 为什么私有知识问题应该先检索再回答
- 为什么通用常识并不天然需要 RAG
- 为什么结构化查询更适合直接查现有系统，而不是先塞进 RAG
- 为什么“只做单次模型调用”和“先分流再回答”会产生不同结果

如果你想真正吃透这一节，不要只看最终答案，要把下面四行一起看：

- `只做单次模型调用`
- `系统路由`
- `路由理由`
- `来源`

---

## 第 2 步：看最小 RAG 数据流

**对应文件**：`03_rag_pipeline.py`

这一章真正要看的链路是：

```text
先路由 -> 如果需要再进入：问题 -> 检索 -> 上下文 -> 回答 + 来源
```

重点观察：

- `route_question()`
- `retrieve()`
- `build_context()`
- `answer_question()`

运行后重点看：

- 为什么有些问题根本不会进入 RAG
- 哪些关键词触发了召回
- 为什么检索结果先变成上下文，再进入回答阶段
- 最终输出为什么不是单纯字符串，而是 `answer + sources`
- 为什么 `Python 系统课可以退钱吗？` 这种问题路由正确，但 toy 检索仍然会漏召回

### 一个最值得看的反例

运行下面这条命令：

```bash
python 03_rag_pipeline.py "Python 系统课可以退钱吗？"
```

你会看到：

- 路由判断会认为这题应该走 `固定 2-step RAG`
- 但关键词检索不会命中 `退款 / 退费`
- 最终返回“当前知识库里没有命中相关资料”

这个反例非常重要，因为它正好说明：

> 第一章先建立“该不该走 RAG”的直觉；后续章节才去解决“走了 RAG 但为什么没召回好”的工程问题。

---

## 第 3 步：看什么时候该用什么方案

**对应文件**：`04_solution_decision.py`

这一章不只讲“RAG 是什么”，还要讲“什么时候不用它”。

重点观察：

- 长上下文适合什么情况
- 直接查现有系统适合什么情况
- `Hosted File Search` 适合什么阶段
- 固定 `2-step RAG` 为什么是默认主线
- `Hybrid RAG` 什么时候值得加
- 为什么 `Agentic RAG` 不该在第一章出现

这里最值得学的不是“记答案”，而是感受这个顺序：

```text
先判断问题约束，再决定技术方案
```

---

## 第 4 步：最后看测试在锁定什么

**对应文件**：`tests/test_rag_basics.py`

测试直接读取 `data/minimum_golden_set.json`，只锁定第一章最重要的几件事：

1. 通用常识问题不会误走 RAG
2. 结构化查询会直接查现有系统
3. 私有知识精确表达能检索到正确来源
4. 同义表达样本会以“已知缺口”形式保留下来
5. 方案判断顺序符合课程主线

这一章看测试，重点不是学 `unittest`，而是理解：

- 文档里的教学边界应该能落成代码检查
- 失败案例也可以是课程资产
- “目前做不到”也应该被正式记录

---

## 建议学习顺序

1. 先读 [01_rag_basics.md](../../../docs/04_rag/01_rag_basics.md)
2. 跑 `python 01_minimum_eval.py`
3. 再跑 `python 02_why_rag.py`
4. 再跑 `python 03_rag_pipeline.py`
5. 最后跑 `python 04_solution_decision.py`
6. 如果你想看边界被正式固定，再看 `tests/test_rag_basics.py`

---

## 第一章共享样本长什么样

`data/minimum_golden_set.json` 里每条样本至少包含：

- `case_id`
- `question`
- `course_target.reference_answer_points`
- `course_target.reference_sources`
- `chapter_expectations.01_rag_basics`
- `tags`

这份文件不是只给第一章看的本地测试夹带数据，而是后续章节可以继续复用的最小公共资产。

---

## 建议主动修改的地方

如果你只阅读不改动，很容易停留在“看懂了”的错觉里。

建议主动试三类小改动：

1. 给某个 `KnowledgeChunk` 多加一个关键词，观察召回是否变化
2. 在 `minimum_golden_set.json` 里加一条新问题，观察路由是否符合预期
3. 改一个 `Scenario` 的条件，观察推荐方案为什么会变化

每次只改一处，这样你才能看清楚：

- 哪个规则影响了哪种系统行为
- 哪个样本在帮你暴露边界
- 哪种变化属于“能力变强”，哪种只是“规则被改了”

---

## 学完这一章后你应该能回答

- RAG 到底在解决什么问题
- 为什么不是所有问题都该上 RAG
- 为什么应该先判断问题类型，再决定是否进入 RAG
- 最小 `2-step RAG` 在线链路长什么样
- 为什么第一章就应该固定共享最小评估样本
- 为什么第一章先做独立闭环，而不是先搭完整项目工程
- 为什么“路由正确”和“召回成功”不是同一件事

---

## 当前真实进度和下一章

- 当前真实进度：第一章已经补上课程级最小评估前置
- 完成标准：能跑通最小闭环，能解释路由、输入输出和来源，能理解共享 golden set 的作用
- 下一章：进入 [02_document_processing](../02_document_processing/README.md)，只处理文档加载、切分、metadata 和 chunk 输出
