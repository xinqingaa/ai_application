# 01. RAG 基础概念

> 本章目标：先理解 RAG 在解决什么问题，跑通一个最小、独立、可重复的 RAG 闭环，并把课程共享的最小评估集正式放进学习入口。

---

## 1. 概述

### 学习目标

- 理解 RAG 解决什么问题，以及它不解决什么问题
- 理解为什么不是所有问题都应该直接进入 RAG
- 能区分长上下文、直接查现有系统、`Hosted File Search`、固定 `2-step RAG`、`Hybrid RAG`、微调和 `Agentic RAG`
- 能画出最小 `2-step RAG` 在线数据流，并说明每一步在做什么
- 能运行课程共享最小评估集，并理解后续章节如何复用
- 能运行一个不依赖后续章节的最小 RAG 示例
- 能说清本章输入、输出、现象和边界

### 预计学习时间

- 评估前置：20 分钟
- RAG 问题意识：40 分钟
- 最小数据流：40 分钟
- 第一章代码实践：40-60 分钟

### 本章在 AI 应用中的重要性

| 场景 | 本章帮你先判断什么 |
|------|-------------------|
| 私有知识问答 | 该不该先检索依据 |
| 通用常识问答 | 是否根本不需要 RAG |
| 结构化查询 | 是否更适合直接查现有系统 |
| 后续 RAG 学习 | 为什么要先把“实验尺子、路由和边界”立住，再做检索工程 |

### 学习前提

- 建议先完成 `02_llm` 里关于单次模型调用、上下文和错误处理的内容
- 如果已经理解 `Document / Retriever` 这些抽象，后面会更顺畅
- 但第一章本身不强依赖 LangChain、Embedding 或向量数据库经验

### 本章与前后章节的关系

前面的 `02_llm` 解决的是：

1. 怎么稳定调用模型
2. 怎么组织消息和上下文
3. 怎么处理结构化输出、成本和错误

`04_rag` 第一章接着解决的是：

1. 为什么单次模型调用不够
2. 什么情况下需要 RAG
3. 为什么要先判断“这题该不该走 RAG”
4. 为什么课程从第一章就要固定最小评估尺子
5. 最小 `2-step RAG` 在线链路长什么样
6. 为什么在第九章之前，每章都应该保持独立闭环

后续章节会继续分开处理：

- 第二章：只做文档加载、切分、metadata 和 chunk 输出
- 第三章：只做 embedding 和相似度
- 第四章：只做向量存储
- 第五章：只做检索策略
- 第六章：再把检索结果接成真正回答

### 本章代码入口

本章对应的代码目录是：

- [README.md](../../source/04_rag/01_rag_basics/README.md)
- [01_minimum_eval.py](../../source/04_rag/01_rag_basics/01_minimum_eval.py)
- [02_why_rag.py](../../source/04_rag/01_rag_basics/02_why_rag.py)
- [03_rag_pipeline.py](../../source/04_rag/01_rag_basics/03_rag_pipeline.py)
- [04_solution_decision.py](../../source/04_rag/01_rag_basics/04_solution_decision.py)
- [rag_basics.py](../../source/04_rag/01_rag_basics/rag_basics.py)
- [tests/test_rag_basics.py](../../source/04_rag/01_rag_basics/tests/test_rag_basics.py)
- [data/minimum_golden_set.json](../../source/04_rag/01_rag_basics/data/minimum_golden_set.json)

### 本章边界

本章只做这些事情：

1. 建立课程级最小评估前置
2. 理解问题意识
3. 跑通最小在线 RAG 闭环
4. 建立方案判断顺序
5. 建立“不是所有问题都该先进 RAG”的最小路由直觉

本章明确不做：

- 项目骨架
- 多模块拆分
- 真实文档加载
- 真实 Embedding
- 真实向量数据库
- 真实 LLM 调用
- API 服务
- 完整评估平台

这里故意只用“内存知识库 + 关键词检索 + 规则化回答 + 最小路由判断 + 最小 golden set”。

目的不是追求效果最强，而是先把 RAG 的问题、实验尺子、数据流和边界讲清楚。

---

## 2. 开始前：最小评估集 📌

### 2.1 为什么评估要前置

RAG 不是“换个 Prompt 看感觉”的练习，而是一个持续调参、持续对比的系统工程。

如果没有一套固定样本，后面你每改一次：

- `chunk_size`
- 切分规则
- Embedding
- 检索策略
- Prompt
- Rerank

都很难判断到底是变好了，还是只是换了一种失败方式。

所以这门课不把评估放在最后补，而是把它放进第一章开头，作为整个 `01-04` 的共享实验尺子。

### 2.2 第一章里保留什么程度的评估

第一章不会展开完整评估平台，也不会一上来就做复杂自动打分。

第一章只做最小、够用、可复跑的评估前置：

- 固定一份共享样本文件
- 让这份样本能被脚本直接跑起来
- 明确第一章当前真正能承诺的结果边界
- 把已知失败样本保留下来，方便后续章节继续收敛

这一步的重点不是“评估体系完整”，而是“课程主线从第一天起有统一尺子”。

### 2.3 课程共享样本长什么样

第一章现在使用的最小样本文件是：

- [data/minimum_golden_set.json](../../source/04_rag/01_rag_basics/data/minimum_golden_set.json)

每条样本至少包含：

- `case_id`
- `question`
- `course_target.reference_answer_points`
- `course_target.reference_sources`
- `chapter_expectations.01_rag_basics`
- `tags`

这里要区分两个层次：

1. `course_target`
2. `chapter_expectations.01_rag_basics`

`course_target` 代表整门课最终希望逼近的正确方向。

`chapter_expectations.01_rag_basics` 代表第一章今天真正会检查什么。

也就是说：

- 整门课最终想做到什么
- 第一章今天能做到什么

不是同一件事。

### 2.3.1 先把这份 JSON 当成“课程共享测试输入”

第一次看这个文件时，最容易卡住的点不是字段多，而是不知道：

- 这份 JSON 是谁读的
- 读出来以后变成什么
- 哪些字段会真的参与第一章判断

第一章里可以先把它理解成：

```text
minimum_golden_set.json
  -> load_minimum_golden_set() 读成 Python list[dict]
  -> 01_minimum_eval.py 逐条遍历 case
  -> get_chapter_expectation() 取出第一章自己的预期
  -> answer_question() 跑真实教学链路
  -> 对比 route / used_rag / sources / answer 是否符合预期
```

也就是说，这份 JSON 在第一章不是“放在那里参考一下”，而是会被脚本正式消费。

但要特别注意一件很容易混淆的事：

> 这份 JSON 是给评估脚本消费的，不是给 `03_rag_pipeline.py` 在线演示脚本拿来做检索匹配的。

也就是说：

- `01_minimum_eval.py` 会主动读取 `minimum_golden_set.json`
- `03_rag_pipeline.py` 不会读取这份 JSON
- `03_rag_pipeline.py` 只处理“你当前传进来的那个问题字符串”

如果你看到：

```bash
python 03_rag_pipeline.py
```

输出里出现的是：

```text
如何申请退款？
```

那是因为这个脚本自己定义了默认参数，不是因为它去 JSON 里“查到了最像的一条样本”。

### 2.3.2 一条样本在 JSON 里到底分几层

你可以把一条 case 看成四层：

1. `case_id`
   用来唯一标识样本，方便测试和定位问题
2. `question`
   真正送进 `answer_question()` 的输入问题
3. `course_target`
   课程长期目标，表示整门课最终希望答案接近什么
4. `chapter_expectations.01_rag_basics`
   第一章当前承诺的最小行为，用来做本章评估

一个最小思维模型可以写成：

```json
{
  "case_id": "private_refund_exact_match",
  "question": "Python 系统课可以退费吗？",
  "course_target": {
    "reference_answer_points": ["7 天内", "学习进度不超过 20%", "全额退款"],
    "reference_sources": ["refund_policy.md"]
  },
  "chapter_expectations": {
    "01_rag_basics": {
      "expected_route": "固定 2-step RAG",
      "expected_sources": ["refund_policy.md"],
      "expected_used_rag": true,
      "expected_answer_points": ["[来源1]", "7 天内", "全额退款"]
    }
  }
}
```

这里最值得盯住的是：

- `question` 是系统输入
- `expected_route` 是对路由层的检查
- `expected_used_rag` 是对“有没有真的走到检索回答链路”的检查
- `expected_sources` 是对来源边界的检查
- `expected_answer_points` 是对回答里最小关键信息的检查

### 2.3.3 为什么 `known_gap` 也要放进 JSON

像 `Python 系统课可以退钱吗？` 这种 case，会在第一章保留：

- 路由是对的
- 但关键词检索暂时召回不到

所以 JSON 里会写出 `known_gap`，明确说明：

```text
这不是样本写错了，而是第一章故意保留这个缺口，
让后续 embedding / hybrid retrieval / query rewrite 有明确改进目标。
```

这能防止你在学习时把“当前实现做不到”和“课程根本没定义目标”混为一谈。

### 2.3.4 在线演示链路和评估链路不是一回事

第一章里实际并行存在两条链路：

```text
链路 A：在线演示链路
命令行问题
  -> 03_rag_pipeline.py
  -> route_question()
  -> retrieve()
  -> build_context()
  -> answer_question()
  -> 打印 answer + sources

链路 B：评估链路
minimum_golden_set.json
  -> 01_minimum_eval.py
  -> 逐条读取 case["question"]
  -> answer_question(question)
  -> 对比 expected_route / expected_sources / expected_used_rag / expected_answer_points
```

这两条链路都会调用 `answer_question()`，但入口不一样：

- 在线演示链路的入口是“当前这次命令行传入的问题”
- 评估链路的入口是“JSON 里预先写好的固定样本”

所以你不能把下面两件事理解成同一件事：

1. `03_rag_pipeline.py` 打印出了 `refund_policy.md`
2. JSON 里有一条 `private_refund_exact_match`

第一件事说明：

```text
当前输入问题，经过路由和检索，在线链路召回了 refund_policy.md
```

第二件事说明：

```text
课程预先定义了一条评估样本，它要求这类问题应该命中 refund_policy.md
```

它们会相互印证，但不是“在线脚本拿 JSON 做模糊查询”的关系。

### 2.4 为什么第一章要保留失败样本

很多初学者会下意识把失败样本删掉，只保留“能跑通”的示例。

这会让你产生一个错觉：

> 代码一运行就很顺，RAG 好像只是把资料接上就结束了。

真实情况不是这样。

第一章就应该保留至少一种已知缺口，例如：

- `Python 系统课可以退费吗？`
  第一章应该能命中 `refund_policy.md`
- `Python 系统课可以退钱吗？`
  第一章要明确保留为已知缺口

这样你后面学 embedding、混合检索、query rewrite 时，才知道自己到底在修什么问题。

### 2.5 第一章怎么运行这套样本

对应脚本是：

- [01_minimum_eval.py](../../source/04_rag/01_rag_basics/01_minimum_eval.py)

运行方式：

```bash
cd source/04_rag/01_rag_basics
python 01_minimum_eval.py
```

你应该观察到：

- 通用常识样本不会误走 RAG
- 结构化查询样本会直接查现有系统
- 私有知识精确表达样本会命中 `refund_policy.md`
- 同义表达样本会被标记为第一章当前已知缺口

### 2.6 后续章节怎么复用

从第二章开始，这份样本不应该被丢掉，而应该继续复用。

复用方式不是“每章检查完全相同的指标”，而是：

- 第一章：看路由、toy RAG 行为、最小来源边界
- 第二章：看文档进入系统后，metadata 和稳定标识是否支撑这些样本
- 第三章：看 embedding 以后，同义表达类样本是否开始改善
- 第四章：看进入持久化存储后，召回结果和来源是否稳定

也就是说，同一份样本是共享的，但每章观察的维度可以不同。

### 2.7 第一章评估脚本到底在检查什么

`01_minimum_eval.py` 的逻辑非常简单，但教学意义很强。

它做的不是复杂评分，而是四类最小检查：

1. `route` 是否符合预期
2. `used_rag` 是否符合预期
3. `sources` 是否至少包含应该命中的来源
4. `answer` 是否包含第一章当前必须出现的关键信息

这里最值得建立的直觉是：

> 第一章评估不是在判断“回答像不像人”，而是在判断“系统行为有没有跑偏”。

---

## 3. 为什么会需要 RAG 📌

### 3.1 单次模型调用为什么不够

在 `02_llm` 里，你已经学会了如何稳定发出一次模型请求。

但真实业务很快会遇到一个问题：

> 模型并不知道你的私有知识，也不会随着你的文档更新自动学会新内容。

如果一个系统要回答下面这些问题：

- 公司内部制度
- 课程资料
- 产品帮助文档
- 运营规则
- 法规和手册

只靠模型参数，通常会遇到四类问题：

1. 知识过时
2. 来源不可追溯
3. 文档太多，不能一直手工塞进 Prompt
4. 没有依据时容易自由发挥

RAG 就是在解决这件事：

> 先把相关知识找出来，再把它们和问题一起交给模型回答。

### 3.2 一个最小例子

假设你现在有一套 Python 课程，它的退款规则写在私有文档里：

```text
Python 系统课购买后 7 天内且学习进度不超过 20%，可以申请全额退款。
```

如果用户问：

```text
Python 系统课可以退费吗？
```

只做单次模型调用时，模型并没有这份私有规则，最稳妥的行为只能是：

- 承认自己不知道
- 或者给出很泛的退款建议

接入 RAG 后，系统可以先把退款规则找出来，再基于它回答，并附上来源。

这就是第一章最想建立的直觉：

> RAG 的价值不是“让模型更聪明”，而是“让回答有依据”。

### 3.3 RAG 解决什么，不解决什么

RAG 重点解决的是：

1. 知识更新问题
2. 私有资料接入问题
3. 来源追溯问题
4. 上下文受控问题

但 RAG 不直接解决：

- 模型本身推理能力不够
- 业务规则定义不清
- 输入文档本身质量很差
- 根本没有可用知识源

所以你不能把所有回答质量问题都归结为“RAG 没调好”。

### 3.4 一个常见误区：把所有知识问题都叫做 RAG 问题

下面三类问题，看起来都像“问答”，但处理方式完全不同：

1. 通用常识
2. 结构化系统查询
3. 私有非结构化知识问答

例如：

- `法国首都是什么？`
  这更像通用常识，通常直接回答即可
- `订单 1024 的状态是什么？`
  这更像结构化查询，应该直接查现有系统
- `Python 系统课可以退费吗？`
  这才是第一章要处理的私有知识问答

也就是说，真正应该先问的不是“要不要上 RAG”，而是：

> 这题到底属于哪种知识访问问题？

### 3.5 为什么“有来源”比“像真话”更重要

在第一章里，你要刻意把注意力从“回答是否流畅”挪到“回答是否有依据”。

原因很简单：

- 流畅回答很容易伪装成正确回答
- 有来源的回答至少可以回查
- 没有来源时，你很难知道问题出在模型、检索、还是知识库

这也是为什么第一章最小返回结构里，不是只有 `answer`，而是：

```text
answer + sources
```

### 3.6 为什么第一章先讲问题意识，而不是先讲工程栈

如果你一上来就讲：

- 文档加载
- 切分
- embedding
- vector DB
- rerank
- router

初学者很容易只记住技术栈名词，却没建立真正的问题意识。

第一章先做的事是：

1. 先分辨问题类型
2. 先明确什么时候要依据
3. 先建立一条最小数据流
4. 先固定一把实验尺子

后面所有工程内容，都是在为这四件事服务。

---

## 4. 最小 `2-step RAG` 数据流 📌

### 4.1 最小在线链路

第一章只看在线部分，先不要背完整离线工程。

真正进入 RAG 之后的最小在线链路是：

```text
问题 -> 检索 -> 上下文 -> 回答 + 来源
```

每一步都只解决一个清晰问题：

- 问题：用户到底在问什么
- 检索：从知识库里找出最相关的内容
- 上下文：把命中的内容整理成回答阶段可消费的输入
- 回答：基于上下文生成答案，而不是自由发挥
- 来源：把答案对应的依据一起返回

### 4.2 进入 RAG 之前先做一次分流判断

第一章虽然重点在最小 `2-step RAG`，但不应该给你建立一个错误直觉：

> 不是所有问题都应该先进入 RAG。

更准确的最小判断顺序应该是：

```text
问题
  ├── 通用常识 -> 直接回答 / 长上下文
  ├── 结构化字段 -> 直接查现有系统
  └── 私有非结构化知识 -> 固定 2-step RAG
```

第一章代码里会用四种最小样例把这个习惯立住：

- `法国首都是什么？`：直接回答
- `订单 1024 的状态是什么？`：直接查现有系统
- `Python 系统课可以退费吗？`：固定 `2-step RAG`
- `Python 系统课可以退钱吗？`：路由正确，但当前召回仍有缺口

### 4.3 第一章的运行时对象

在 [rag_basics.py](../../source/04_rag/01_rag_basics/rag_basics.py) 里，最值得先建立手感的不是“函数很多”，而是“对象很清楚”。

你可以先把这些对象看成第一章最小 RAG 的运行时骨架：

| 对象 | 作用 |
|------|------|
| `KnowledgeChunk` | 一段可被检索的知识块 |
| `RetrievalResult` | 一次检索命中的结果，带 `score` 和关键词命中信息 |
| `AnswerResult` | 进入回答阶段后的最小结果 |
| `RouteDecision` | 这题该走哪条知识访问路线 |
| `RoutedAnswerResult` | 把路由信息和最终回答合在一起 |
| `Scenario` | 用来做方案判断示例的场景对象 |

这和 `02_llm` 第一章里先看 `client / messages / response / usage` 是同一类学习策略：

> 先看清运行时对象，再看函数怎么把它们串起来。

再进一步，你可以把这些对象看成是不同阶段的“数据形状”：

```text
用户问题: str
  -> RouteDecision
  -> RetrievalResult[]
  -> AnswerResult
  -> RoutedAnswerResult
```

也就是说，第一章不是“一个字符串进来，另一个字符串出去”，而是每走一步，都会产出一个更明确的中间结果。

### 4.3.1 这些对象的字段到底怎么读

| 对象 | 关键字段 | 字段在流程里的意义 |
|------|----------|-------------------|
| `KnowledgeChunk` | `chunk_id / source / title / content / keywords` | 描述一条可被检索的知识块，其中 `keywords` 是第一章 toy 检索真正会用到的召回线索 |
| `RetrievalResult` | `chunk / score / matched_keywords` | 表示某个 chunk 被召回了，以及它为什么被召回 |
| `AnswerResult` | `question / answer / sources / used_rag` | 表示“回答阶段”产出的最小结果，但还没有把路由信息带出去 |
| `RouteDecision` | `route / reason` | 表示系统先决定“这题该走哪条知识访问路线” |
| `RoutedAnswerResult` | `question / route / reason / answer / sources / used_rag` | 把路由层和回答层合并，成为最适合对外打印和评估的最终结果 |
| `Scenario` | 多个布尔条件 + `material_count` | 不用于在线问答，而用于方案选择教学示例 |

你可以特别注意两个看起来相似、但职责不同的对象：

- `AnswerResult`
  只关心“回答阶段”本身产出了什么
- `RoutedAnswerResult`
  关心“整条链路最终决定了什么，并给出了什么结果”

这也是为什么 `answer_question()` 最终返回的是 `RoutedAnswerResult`，而不是简单复用 `AnswerResult`。

### 4.3.2 用一张表先看清主要函数的输入输出

| 函数 | 输入 | 输出 | 它解决的问题 |
|------|------|------|-------------|
| `route_question(question)` | `str` | `RouteDecision` | 这题该走哪条知识访问路线 |
| `retrieve(question, top_k)` | `str` | `list[RetrievalResult]` | 如果要检索，哪些知识块被召回了 |
| `build_context(results)` | `list[RetrievalResult]` | `str` | 如何把召回结果整理成回答阶段可消费的上下文 |
| `answer_with_rag(question, top_k)` | `str` | `AnswerResult` | 已经确定走 RAG 后，如何生成带来源的回答 |
| `answer_question(question, top_k)` | `str` | `RoutedAnswerResult` | 作为总入口，负责先路由，再决定是否进入 RAG |

### 4.4 `retrieve()` 在第一章到底做了什么

很多人第一次看 toy RAG 代码时，会觉得关键词检索太“假”。

但第一章故意这样做，是为了让你把注意力放在检索动作本身，而不是被 embedding 细节分散注意力。

当前 `retrieve()` 做的事很简单：

1. 遍历知识块
2. 检查问题里是否出现 chunk 的关键词
3. 计算一个最小分数
4. 返回 `top_k` 个结果

也就是说，第一章并不追求最强召回，而是先让你真正看见：

```text
用户问题
-> 命中哪些关键词
-> 哪些 chunk 被召回
-> 为什么这个 chunk 排在前面
```

这里还要再明确一下：

> 第一章当前不是模糊查询，也不是 embedding 语义检索。

它的匹配方式更接近：

```text
问题字符串里是否直接包含某个关键词
```

所以第一章当前没有做这些事：

- 同义词扩展
- 语义相似度匹配
- query rewrite
- rerank
- 向量检索

这也是为什么：

- `退款` 能命中 `keywords=("退款", "退费", "学习进度", "课时")`
- `退费` 能命中
- `退钱` 在当前 chunk 关键词里没写进去时，就命中不了

也就是说，第一章召回是否成功，主要取决于：

1. 路由提示词里有没有出现这类表达
2. 对应知识块的 `keywords` 里有没有覆盖这类表达

在代码里，`retrieve()` 的返回值不是原始文本，而是 `RetrievalResult` 列表。每个元素至少告诉你三件事：

- 命中了哪个 `chunk`
- 这个 chunk 的 `score` 是多少
- 它到底命中了哪些 `matched_keywords`

这三项信息一起出现，才方便你判断：

```text
问题是没进 RAG？
还是进了 RAG 但没召回？
还是召回了，但排序不理想？
```

### 4.5 `build_context()` 在第一章的作用

很多人会把“检索完成”和“回答完成”混成一件事。

实际上，中间还有一个关键步骤：

> 把检索结果整理成可供回答阶段消费的上下文。

第一章里的 `build_context()` 很朴素，只是把每个结果整理成：

```text
[来源1] source=... title=... content=...
```

这里改成 `来源1` 而不是早先那种 `S1`，就是为了让含义更直白：

- `来源` 表示这是一条来源标签
- `1` 表示它是“当前这次检索结果里的第 1 条”

它不是全局固定 ID，也不是 JSON 里的索引，只是当前回答里临时生成的来源编号。

它的教学意义在于：

- 让你看到回答不是直接凭空生成
- 让你看到来源标签是怎么进入后续回答阶段的
- 让你理解“上下文构造”本身就是 RAG 工程的一部分

你可以把 `build_context()` 理解成一个“显示版 prompt 组装器”。

第一章没有真实 LLM 调用，所以它不会真的把字符串送给模型；但它仍然把检索结果先整理成这种格式：

```text
[来源1] source=refund_policy.md title=退款规则 content=...
```

这样做有两个教学目的：

1. 让你看到回答阶段理论上会消费什么输入
2. 让你看到 `sources` 和回答里的 `[来源1]` 引用标记是怎么对应起来的

### 4.6 `answer_question()` 的真正作用

`answer_question()` 不是单纯“返回答案”，它做的是最小系统编排。

它先调用：

- `route_question()`

然后再根据不同路由分别走：

- 直接回答
- 直接查现有系统
- 固定 `2-step RAG`
- 提示补充上下文

你可以把它理解成：

```text
最小知识访问总入口
```

如果把它展开成更具体的代码流，你会更容易读懂：

```text
question: str
  -> route_question(question)
      -> RouteDecision(route, reason)
  -> if route == "直接回答"
      -> lookup_general_knowledge(question)
      -> RoutedAnswerResult(..., used_rag=False)
  -> elif route == "直接查现有系统"
      -> lookup_existing_system(question)
      -> RoutedAnswerResult(..., used_rag=False)
  -> elif route == "固定 2-step RAG"
      -> answer_with_rag(question)
          -> retrieve(question)
          -> AnswerResult(answer, sources, used_rag)
      -> RoutedAnswerResult(..., used_rag=result.used_rag)
  -> else
      -> RoutedAnswerResult(提示补充上下文)
```

这里有一个很值得注意的细节：

> 路由决定“应该走 RAG”，并不等于最后 `used_rag` 一定是 `true`。

例如 `Python 系统课可以退钱吗？`：

- `route_question()` 会把它判成 `固定 2-step RAG`
- 但 `answer_with_rag()` 里如果 `retrieve()` 没有召回任何结果
- 返回的 `AnswerResult.used_rag` 仍然会是 `false`

这是第一章非常重要的教学点，因为它帮你把两件事分开：

1. 路由判断是否正确
2. 检索执行是否真的命中了资料

### 4.6.1 用“退费”和“退钱”两条样本看完整流转

先看精确表达样本：

```text
问题: Python 系统课可以退费吗？
  -> route_question(): 固定 2-step RAG
  -> retrieve(): 命中 refund_policy.md，因为问题里含有关键词“退费”
  -> build_context(): 生成 [来源1] source=refund_policy.md ...
  -> answer_with_rag(): 生成“根据 [来源1] ...”的回答
  -> sources: ("refund_policy.md",)
  -> used_rag: true
```

再看同义表达缺口样本：

```text
问题: Python 系统课可以退钱吗？
  -> route_question(): 固定 2-step RAG
  -> retrieve(): 无命中，因为当前关键词集合里没有“退钱”
  -> build_context(): 在 03_rag_pipeline.py 里会显示 (empty)
  -> answer_with_rag(): 返回“当前知识库里没有命中相关资料”
  -> sources: ()
  -> used_rag: false
```

这两个 case 只差一个词，但它们共同帮你看清三层不同问题：

- 路由层是否把题目分对了
- 检索层是否真的召回了正确 chunk
- 回答层是否把来源一起带回来了

### 4.6.2 为什么 `如何申请退款？` 不需要先去“匹配 JSON 样本”

很多人第一次同时看到：

- `03_rag_pipeline.py` 的默认问题 `如何申请退款？`
- `minimum_golden_set.json` 里的 `Python 系统课可以退费吗？`

会误以为系统内部在做类似“找最像的一条 JSON case”。

第一章当前完全不是这样。

`03_rag_pipeline.py` 的默认问题只是脚本入口默认值，它会直接走在线链路：

```text
如何申请退款？
  -> route_question()
  -> retrieve()
  -> answer_question()
```

它不会先去：

```text
在 JSON 里找最像的 case
-> 再决定用哪条样本
```

真正让 `如何申请退款？` 命中 `refund_policy.md` 的原因只有一个：

```text
问题里包含“退款”，而 refund_policy.md 对应 chunk 的 keywords 里也包含“退款”
```

所以当前第一章的命中逻辑不是：

```text
问题 -> 找最像的 JSON 样本 -> 找到对应答案
```

而是：

```text
问题 -> 路由规则 -> 检索关键词匹配 -> 找到知识块 -> 生成回答
```

### 4.6.3 如果换其他问法，第一章靠什么保证命中

第一章没有真正通用的“语义保证”，只能靠规则覆盖。

你可以把“保证命中”理解成三种最朴素的方法：

1. 扩充路由关键词
   让更多问法能先被判成私有知识问题
2. 扩充 chunk 的 `keywords`
   让更多表述能命中同一份知识块
3. 在进入路由和检索前先做问题归一化
   比如把 `退钱` 统一改写成 `退款`

例如当前如果想让下面这些问法都更稳地命中退款规则：

- `怎么退钱？`
- `退款怎么申请？`
- `可以申请退学费吗？`

你就需要在规则层主动补覆盖，而不是指望第一章的 toy 检索自动理解这些同义表达。

这也是为什么第一章虽然主题是 RAG，却仍然要讲“什么时候不进 RAG”。

### 4.7 为什么第一章只保留这条链路

因为你现在要学的是：

1. RAG 到底为什么存在
2. RAG 最小形态长什么样
3. 回答为什么必须带依据
4. 为什么实验尺子要先固定

你现在不需要一上来就理解：

- loader
- splitter
- embeddings
- vector DB
- API 服务
- 多模块目录

这些都是真实系统会出现的东西，但不应该压过第一章的学习目标。

### 4.8 为什么第一章不再先做项目骨架

在你的学习模式里，第九章之前每一章都应该是独立知识单元。

所以第一章不应该把重点放在：

- 项目目录怎么拆
- 模块怎么预留
- 抽象怎么为后面铺路

第一章应该先把最小闭环讲清楚。

等你到第九章再做完整项目工程，会更自然，因为那时你已经知道：

- 文档层在做什么
- 检索层在做什么
- 生成层在做什么
- 评估层在做什么

---

## 5. 什么情况下该选什么方案 📌

### 5.1 常见方案梯度

很多人在做 AI 应用时，会先问“要不要上 RAG”。

更准确的问法其实是：

> 当前这个问题，最合适的知识接入方案是什么？

常见方案梯度如下：

| 方案 | 更适合什么情况 | 不适合什么情况 |
|------|----------------|----------------|
| 长上下文 | 材料少、问题少、一次性分析 | 文档多、更新频繁、要长期维护 |
| 直接查现有系统 | 已有 SQL、Elasticsearch、CMS、FAQ 系统 | 以非结构化文档为主的场景 |
| `Hosted File Search` | 快速做 Demo、先验证产品价值、不想先搭检索工程 | 需要深度自定义检索和知识治理 |
| 固定 `2-step RAG` | 要引用来源、要持续更新知识 | 明显更适合结构化查询的场景 |
| `Hybrid RAG` | 编号、术语、产品名很多，纯向量检索容易漏召回 | 数据量很小、没有明显关键词召回问题 |
| 微调 | 学习风格、格式、行为模式 | 希望频繁更新外部知识 |
| `Agentic RAG` | 固定链路明显不够，需要动态检索决策 | 基础 RAG 还没做稳 |

### 5.2 默认决策顺序

这门课推荐的默认决策顺序是：

1. 先判断能不能直接回答，或者直接用长上下文解决
2. 再判断能不能直接查现有知识系统
3. 如果只是要快速验证价值，可以先用 `Hosted File Search`
4. 默认优先做稳定的 `2-step RAG`
5. 固定检索不稳、又有大量编号和术语时，再加 `Hybrid RAG`、Rerank、查询变换
6. 只有固定链路明显不够时，才升级到 `Agentic RAG`

这里最重要的判断不是“哪个方案最强”，而是：

> 先用问题类型判断方案，再选技术，而不是先选技术再给它找问题。

### 5.3 `recommend_solution()` 在教学上代表什么

[rag_basics.py](../../source/04_rag/01_rag_basics/rag_basics.py) 里的 `recommend_solution()` 不是真实企业决策器。

它在第一章里承担的是“把思路写成可执行规则”的作用。

它用 `Scenario` 对象描述场景，再按一组清晰条件做推荐。

这一步的意义是：

- 把“感觉上适合”变成“为什么适合”
- 把“RAG 好像应该上”变成“先按梯度判断”
- 把技术选型讨论从口号拉回到约束条件

### 5.4 第一章为什么只做固定 `2-step RAG` 的影子

因为第一章要先建立四个最重要的习惯：

1. 有问题先判断它属于哪类知识访问问题
2. 有回答先看依据是否存在
3. 有实验先看有没有固定样本
4. 有方案先按复杂度从低到高判断

这也是为什么第一章的代码会同时包含：

- 一个最小分流判断
- 一个最小问答闭环
- 一个“什么时候不用 RAG”的判断示例
- 一个课程共享的最小评估入口

### 5.5 为什么第一章不鼓励直接谈 `Agentic RAG`

如果固定链路都还没跑稳，就直接讨论动态检索、工具选择、多步计划，通常会同时放大三类问题：

1. 你不知道失败到底发生在检索、路由还是工具编排
2. 你没有稳定基线，很难判断复杂化是否真的有收益
3. 你会把“系统更复杂”误当成“系统更高级”

所以第一章对 `Agentic RAG` 的态度是：

> 先知道它存在，但不要过早把它当主线。

---

## 6. 第一章实践：独立最小闭环

### 6.1 目录结构

本章代码目录是：

```text
source/04_rag/01_rag_basics/
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

第一章只保留一个平铺目录，不做 `app/`、`services/`、`vectorstores/` 这种项目式拆分。

### 6.2 第一章的输入和输出

本章代码的输入是：

- 一个问题字符串
- 一组内存中的小知识块
- 一份课程共享的最小样本文件

本章代码的输出是：

- 路由判断
- 检索结果
- 最小上下文
- `answer + sources`
- 共享样本在第一章边界下的运行结果

这一步最重要的是建立一个感觉：

> 第一章不是在做“文档都准备好了的大系统”，而是在做“最小可解释系统”。

### 6.3 本章最值得先看的对象和函数

在 [rag_basics.py](../../source/04_rag/01_rag_basics/rag_basics.py) 里，你最值得先看的是：

- `KnowledgeChunk`
- `RetrievalResult`
- `AnswerResult`
- `RouteDecision`
- `RoutedAnswerResult`
- `Scenario`
- `load_minimum_golden_set()`
- `get_chapter_expectation()`
- `route_question()`
- `retrieve()`
- `build_context()`
- `answer_with_rag()`
- `answer_question()`
- `recommend_solution()`

推荐阅读顺序不是从上到下死读，而是：

1. 先看数据对象
2. 再看路由
3. 再看检索
4. 再看回答
5. 最后看方案推荐和评估入口

### 6.4 运行方式

```bash
cd source/04_rag/01_rag_basics

python 01_minimum_eval.py
python 02_why_rag.py
python 03_rag_pipeline.py
python 04_solution_decision.py
python -m unittest discover -s tests
```

### 6.5 先跑哪个

建议先跑：

```bash
python 01_minimum_eval.py
```

因为你最先要建立的不是“RAG 多厉害”，而是：

- 第一章从一开始就要固定实验尺子
- 这份样本不仅服务第一章，也会继续服务后续 `01-04`
- 第一章当前只验证最小路由、最小来源和 toy RAG 边界

### 6.6 `01_minimum_eval.py` 在看什么

对应文件：

- [01_minimum_eval.py](../../source/04_rag/01_rag_basics/01_minimum_eval.py)

这个脚本不是完整评估平台，而是课程级最小起点。

重点观察：

- 样本里同时存在通用常识、结构化查询、私有知识和已知失败样本
- `course_target` 描述的是整门课最终想达到的方向
- `chapter_expectations.01_rag_basics` 锁定的是第一章今天真正能承诺什么
- `Python 系统课可以退钱吗？` 会被保留为已知缺口，后续章节继续复用

你可以把它理解成：

```text
先把尺子放在桌上，再开始做系统
```

如果你想知道这段脚本到底怎么消费 JSON，可以按下面顺序读：

```text
load_minimum_golden_set()
  -> 读出 list[case]

for case in cases:
  question = case["question"]
  expectation = get_chapter_expectation(case, CHAPTER_KEY)
  result = answer_question(question)
  对比:
    - result.route vs expected_route
    - result.used_rag vs expected_used_rag
    - result.sources 是否包含 expected_sources
    - result.answer 是否包含 expected_answer_points
```

这里的重点不是复杂评分，而是把“系统行为”拆成几个最小可检查项。

### 6.6.1 `01_minimum_eval.py` 真正检查的是哪四件事

它逐条样本至少会检查：

1. `route`
   系统是否把问题分到正确的知识访问路线
2. `used_rag`
   系统是否真的进入了检索回答链路
3. `sources`
   如果应该命中某个资料，最终结果里有没有保留下来
4. `answer`
   回答里是否至少出现本章当前必须出现的关键信息

所以第一章评估关注的不是“回答好不好听”，而是：

```text
这条链路有没有按课程预期那样运转
```

### 6.7 `02_why_rag.py` 在看什么

对应文件：

- [02_why_rag.py](../../source/04_rag/01_rag_basics/02_why_rag.py)

这个脚本会打印三类问题：

1. 课程私有知识问题
2. 通用常识问题
3. 结构化系统查询

重点观察：

- 为什么私有知识问题应该先检索再回答
- 为什么通用常识并不天然需要 RAG
- 为什么结构化查询更适合直接查现有系统，而不是先塞进 RAG
- 为什么“只做单次模型调用”和“先判断再回答”会得出不同结果

### 6.8 `03_rag_pipeline.py` 在看什么

对应文件：

- [03_rag_pipeline.py](../../source/04_rag/01_rag_basics/03_rag_pipeline.py)

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

### 6.9 `04_solution_decision.py` 在看什么

对应文件：

- [04_solution_decision.py](../../source/04_rag/01_rag_basics/04_solution_decision.py)

这一章不只讲“RAG 是什么”，还要讲“什么时候不用它”。

重点观察：

- 长上下文适合什么情况
- 直接查现有系统适合什么情况
- `Hosted File Search` 适合什么阶段
- 固定 `2-step RAG` 为什么是默认主线
- `Hybrid RAG` 什么时候值得加
- 为什么 `Agentic RAG` 不该在第一章出现

### 6.10 `tests/test_rag_basics.py` 在锁定什么

对应文件：

- [tests/test_rag_basics.py](../../source/04_rag/01_rag_basics/tests/test_rag_basics.py)

测试直接读取 `data/minimum_golden_set.json`，只锁定第一章最重要的几件事：

1. 通用常识问题不会误走 RAG
2. 结构化查询会直接查现有系统
3. 私有知识精确表达能检索到正确来源
4. 同义表达样本会以“已知缺口”形式保留下来
5. 方案判断顺序符合课程主线

第一章里看测试，不是为了展示“工程完整”，而是为了强化一个习惯：

> 教学样本也应该被程序正式读取，而不是只写在文档里。

### 6.11 第一章共享最小评估集

样本文件里现在至少保留四类问题：

```json
[
  {
    "case_id": "general_knowledge_capital",
    "question": "法国首都是什么？"
  },
  {
    "case_id": "structured_order_status",
    "question": "订单 1024 的状态是什么？"
  },
  {
    "case_id": "private_refund_exact_match",
    "question": "Python 系统课可以退费吗？"
  },
  {
    "case_id": "private_refund_synonym_gap",
    "question": "Python 系统课可以退钱吗？"
  }
]
```

这不是完整评估体系，但已经足够回答：

1. 教学主线有没有跑偏
2. 来源有没有丢
3. 课程共享样本有没有被后续修改悄悄破坏

### 6.12 本章代码刻意简化了什么

这一章的实现非常刻意地简化了五件事：

1. 评估只是最小 golden set，不是完整评估平台
2. 检索只是关键词匹配，不是 embedding 检索
3. 回答只是最小规则化回答，不是真实 LLM
4. 知识库在内存里，不是向量数据库
5. 路由只是最小规则判断，不是真实线上 router

这是故意的，不是偷工减料。

因为本章要先把下面这件事学会：

> RAG 的本质是“先找依据，再回答”，并且整个过程需要有固定尺子来复跑。

### 6.13 第一章最值得刻意观察的失败案例

运行下面这条命令：

```bash
python 03_rag_pipeline.py "Python 系统课可以退钱吗？"
```

你会看到：

1. 路由判断认为这题应该走 `固定 2-step RAG`
2. 但 `退钱` 不会命中当前 toy 检索里的 `退款 / 退费`
3. 最终系统仍然拿不到来源

这个现象非常关键，因为它正好解释了后续章节为什么还要继续学：

- 更好的切分
- Embedding
- 向量存储
- 混合检索
- Rerank

它也顺带帮你分清两件不同的事：

1. 这题该不该进入 RAG
2. 进了 RAG 以后能不能召回好

### 6.14 建议你主动改的地方

如果你想把这一章真正学扎实，建议主动改三类地方再跑一遍：

1. 给某个知识块多加一个关键词，观察召回和样本结果怎么变
2. 自己加一条通用常识或结构化查询样本，观察路由有没有跑偏
3. 修改 `Scenario` 的条件，观察推荐方案为什么会变

这样你会真正把“规则、样本、系统行为”三者连接起来。

---

## 7. 本章学完后你应该能回答

- 为什么私有知识问题会需要 RAG
- 为什么不是所有问题都应该先进 RAG
- 最小 `2-step RAG` 在线链路长什么样
- 最小问题分流应该长什么样
- 为什么答案最好返回 `answer + sources`
- 为什么课程从第一章就要固定最小评估集
- 长上下文、直接查现有系统、`Hosted File Search`、固定 `2-step RAG`、`Hybrid RAG`、微调、`Agentic RAG` 各自适合什么情况
- 为什么第一章应该先做独立闭环，而不是先做完整工程骨架
- 为什么“路由正确”和“召回成功”不是同一件事

---

## 8. 下一章

第二章开始，你才会进入真正的文档处理问题：

- 文件怎么加载
- 文本怎么切分
- metadata 怎么保留
- chunk 怎么稳定输出

也就是说，第二章才开始处理“知识怎么进入系统”。

第一章先把“为什么要这么做”“最小闭环是什么”“为什么要先固定共享样本”“为什么不是所有问题都先上 RAG”立住，就够了。
