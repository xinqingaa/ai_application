# AI Application Learning Workspace

这是一个面向前端、Flutter 和跨端开发者的 AI 应用学习与项目实践仓库。

唯一主项目是“需求评审助手”——一个以需求基线为核心的需求定义、评审与交付工作台：第一阶段用固定 RAG 完成从结构化输入或已有 PRD 到可定位评审结论、人的逐项决策、人工批准基线与交付包的闭环；第二阶段在同一对象模型上演进为 Agent、Tools、Deep Research 与 Multi-Agent 协作系统，由 Agent 追问缺失信息、在用户裁决下推动需求收敛并分析变更影响。

## 入口

- [产品规格](SPEC.md)：最终产品必须做什么。
- [系统设计](SDD.md)：领域对象、状态、权限、证据与事务怎样协作。
- [工程方案](PLAN.md)：代码怎样在 `source/` 中组织和演进。
- [课程首页](course/README.md)：学习者入口。
- [标准学习路径](course/learning-path.md)：唯一课程顺序。
- [知识地图](course/knowledge-map.md)：完整能力范围。

## 学习方式

```text
项目愿景与阶段目标
→ 概念
→ 机制
→ 真实实验
→ 项目综合实践
→ 测试、评估和需求修改
```

课程分为概念篇、机制篇、实验篇和项目篇。机制篇解释原理和边界；实验篇负责代码初始化、运行、日志与调试；项目篇负责综合实践和学习验收。

## 目录

```text
docs/                           战略与规范
course/lessons/                 概念、机制、实验与项目篇
source/packages/                通用能力
source/demos/                   实验代码
source/apps/review_assistant/   唯一产品
source/python_base/             Python 基础练习
```

产品代码只在 `source/apps/review_assistant/` 组合，不在仓库根目录或学习 demo 中维护平行实现。

## 真实调用

LLM、RAG、Agent 和 Eval 主路径使用真实模型或真实外部服务。缺少配置或供应商失败时清晰报错，不静默返回 Mock。Mock 只用于确定性测试、离线排查和明确对照，不能证明真实质量。

## 维护者

长期定位见 [strategy.md](docs/strategy.md)，课程和代码规则见 [learning-guide.md](docs/learning-guide.md)，AI Coding 掌握标准见 [ai-coding-mastery.md](docs/ai-coding-mastery.md)。
