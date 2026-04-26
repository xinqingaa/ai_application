from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class KnowledgeChunk:
    """第一章内存知识库里最小的可检索知识单元。"""

    chunk_id: str
    source: str
    title: str
    content: str
    keywords: tuple[str, ...]


@dataclass(frozen=True)
class RetrievalResult:
    """检索阶段的输出：命中了哪个 chunk、为什么命中、分数是多少。"""

    chunk: KnowledgeChunk
    score: float
    matched_keywords: tuple[str, ...]


@dataclass(frozen=True)
class AnswerResult:
    """回答阶段的结果，此时还没有附带路由信息。"""

    question: str
    answer: str
    sources: tuple[str, ...]
    used_rag: bool


@dataclass(frozen=True)
class RouteDecision:
    """路由器对“这道题应该怎么取知识”的判断结果。"""

    route: str
    reason: str


@dataclass(frozen=True)
class RoutedAnswerResult:
    """最终对外使用的结果对象，脚本打印和测试都会消费它。"""

    question: str
    route: str
    reason: str
    answer: str
    sources: tuple[str, ...]
    used_rag: bool


@dataclass(frozen=True)
class Scenario:
    """只用于教学演示的场景对象，用来做方案选择示例。"""

    name: str
    material_count: str
    has_existing_system: bool = False
    structured_data: bool = False
    needs_citations: bool = False
    knowledge_changes_often: bool = False
    needs_dynamic_routing: bool = False
    wants_behavior_change: bool = False
    needs_fast_validation: bool = False
    has_precise_keywords: bool = False


CHAPTER_KEY = "01_rag_basics"
DATA_DIR = Path(__file__).resolve().parent / "data"
MINIMUM_GOLDEN_SET_PATH = DATA_DIR / "minimum_golden_set.json"

# 第一章故意把“知识库”直接放在内存里，
# 让学习重点先落在路由、检索、上下文构造和带来源回答上。
COURSE_KNOWLEDGE_BASE = [
    KnowledgeChunk(
        chunk_id="kb-1",
        source="refund_policy.md",
        title="退款规则",
        content=(
            "Python 系统课购买后 7 天内且学习进度不超过 20%，"
            "可以申请全额退款。超过 7 天后按剩余未学习课时折算退款。"
        ),
        keywords=("退款", "退费", "学习进度", "课时"),
    ),
    KnowledgeChunk(
        chunk_id="kb-2",
        source="trial_class.md",
        title="试学规则",
        content="Python 系统课支持 1 次免费试学，时长 30 分钟，需要提前预约。",
        keywords=("试学", "免费", "预约", "30 分钟"),
    ),
    KnowledgeChunk(
        chunk_id="kb-3",
        source="support_hours.md",
        title="答疑时间",
        content="课程助教在工作日 10:00-18:00 提供在线答疑，周末只处理紧急问题。",
        keywords=("答疑", "工作日", "10:00", "18:00"),
    ),
]

# 这些模式用来模拟完全不需要私有检索的通用问题。
GENERAL_KNOWLEDGE_PATTERNS = [
    (("法国", "首都"), "法国首都是巴黎。"),
    (("水", "化学式"), "水的化学式是 H2O。"),
]

# 这些模式用来模拟更适合直接查现有系统的结构化问题。
STRUCTURED_SYSTEM_PATTERNS = [
    (
        ("订单", "1024", "状态"),
        "订单 1024 当前已支付，等待开课。",
        "orders_table",
    ),
]

# 这些关键词只是第一章路由器的粗粒度信号：
# “这题看起来像课程私有知识问题”。
# 它们只负责判断应不应该尝试 RAG，
# 不负责保证检索一定成功。
PRIVATE_KNOWLEDGE_HINTS = (
    "课程",
    "系统课",
    "退款",
    "退费",
    "退钱",
    "试学",
    "试听",
    "预约",
    "答疑",
    "助教",
    "课时",
)


def load_minimum_golden_set(path: Path | None = None) -> list[dict[str, object]]:
    """把课程共享样本从 JSON 读成 Python 对象。

    这里故意保持为 list[dict]，方便学习时直接把 JSON 字段
    和评估脚本后续消费的值一一对应起来。
    """

    target_path = path or MINIMUM_GOLDEN_SET_PATH
    with target_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, list):
        raise TypeError("minimum golden set must be a list of cases")
    return data


def get_chapter_expectation(
    case: dict[str, object],
    chapter_key: str = CHAPTER_KEY,
) -> dict[str, object]:
    """从一条课程共享样本里取出当前章节自己的预期配置。"""

    expectations = case.get("chapter_expectations")
    if not isinstance(expectations, dict):
        raise KeyError("case is missing chapter_expectations")

    expectation = expectations.get(chapter_key)
    if not isinstance(expectation, dict):
        raise KeyError(f"case is missing expectation for {chapter_key}")
    return expectation


def lookup_general_knowledge(question: str) -> str | None:
    """如果问题属于简单通用常识，就直接返回答案。"""

    for keywords, answer in GENERAL_KNOWLEDGE_PATTERNS:
        if all(keyword in question for keyword in keywords):
            return answer
    return None


def lookup_existing_system(question: str) -> AnswerResult | None:
    """如果问题属于结构化查询，就直接返回系统查询结果。"""

    for keywords, answer, source in STRUCTURED_SYSTEM_PATTERNS:
        if all(keyword in question for keyword in keywords):
            return AnswerResult(
                question=question,
                answer=answer,
                sources=(source,),
                used_rag=False,
            )
    return None


def is_private_knowledge_question(question: str) -> bool:
    """第一章用于判断“这题大概率依赖课程资料”的最小路由规则。"""

    return any(keyword in question for keyword in PRIVATE_KNOWLEDGE_HINTS)


def route_question(question: str) -> RouteDecision:
    """在真正检索前，先决定第一章应该走哪条知识访问路线。"""

    if lookup_general_knowledge(question) is not None:
        return RouteDecision(
            route="直接回答",
            reason="这是通用常识问题，当前不需要额外检索私有知识。",
        )

    if lookup_existing_system(question) is not None:
        return RouteDecision(
            route="直接查现有系统",
            reason="这是结构化查询，更适合直接读现成系统，而不是先走 RAG。",
        )

    if is_private_knowledge_question(question):
        return RouteDecision(
            route="固定 2-step RAG",
            reason="问题看起来依赖课程私有资料，应该先检索依据再回答。",
        )

    return RouteDecision(
        route="补充上下文",
        reason="当前既不像通用常识，也没有明显的结构化字段或课程知识线索。",
    )


def retrieve(
    question: str,
    knowledge_base: list[KnowledgeChunk] | None = None,
    top_k: int = 2,
) -> list[RetrievalResult]:
    """返回某个问题召回到的 top_k 个知识块。

    第一章故意使用关键词重叠，而不是 embedding，
    这样学习时可以直接看见“为什么这个 chunk 被召回了 / 没被召回”。

    这里不是模糊查询，也不是语义检索。
    当前判断规则非常直接：只看 question 里是否字面包含 chunk.keywords 里的词。
    """

    base = knowledge_base or COURSE_KNOWLEDGE_BASE
    scored_results: list[RetrievalResult] = []

    for chunk in base:
        # 例如 question="如何申请退款？" 时，
        # 如果 chunk.keywords 里有 "退款"，就会命中；
        # 如果只有同义词但没有字面重合，例如 "退钱" 没被写进 keywords，
        # 那当前第一章实现就不会召回。
        matched_keywords = tuple(keyword for keyword in chunk.keywords if keyword in question)
        if not matched_keywords:
            continue

        # 这个 toy score 只是教学信号：
        # 当前问题覆盖了这个 chunk 的多少关键词。
        score = len(matched_keywords) / len(chunk.keywords)
        scored_results.append(
            RetrievalResult(
                chunk=chunk,
                score=round(score, 2),
                matched_keywords=matched_keywords,
            )
        )

    scored_results.sort(
        key=lambda item: (item.score, len(item.matched_keywords), item.chunk.chunk_id),
        reverse=True,
    )
    return scored_results[:top_k]


def build_context(results: list[RetrievalResult]) -> str:
    """把检索结果整理成回答阶段可消费的上下文字符串。"""

    if not results:
        return "(empty)"

    lines = []
    for index, result in enumerate(results, start=1):
        # 这里的 [来源1]、[来源2] 是“本次检索结果里的临时来源编号”。
        # 它不是 KnowledgeChunk 自己的固定 ID，而是为了让回答阶段能清楚指向：
        # “当前这句话依据的是第几条检索结果”。
        lines.append(
            f"[来源{index}] source={result.chunk.source} title={result.chunk.title} "
            f"content={result.chunk.content}"
        )
    return "\n".join(lines)


def answer_without_rag(question: str) -> str:
    """提供一个不走 RAG 的基线回答，供 02_why_rag.py 对比使用。"""

    direct_answer = lookup_general_knowledge(question)
    if direct_answer is not None:
        return direct_answer

    return "我无法确定，因为单次调用里没有足够依据。这可能需要额外知识源或补充上下文。"


def answer_with_rag(question: str, top_k: int = 2) -> AnswerResult:
    """先检索，再生成一个最小的“带引用”回答。

    这里要特别注意：
    route="固定 2-step RAG" 不代表 used_rag 一定是 True。
    如果检索没有命中任何结果，这个函数会返回兜底回答，并把 used_rag
    设为 False，用来说明“路由判断成功”和“检索真的召回成功”是两件事。
    """

    results = retrieve(question, top_k=top_k)
    if not results:
        return AnswerResult(
            question=question,
            answer="我不知道，因为当前知识库里没有命中相关资料。",
            sources=(),
            used_rag=False,
        )

    # 第一章只把第一个结果当成主要证据，其余结果仅作为补充参考。
    # 后续章节会把这一步做得更接近真实系统。
    primary = results[0]
    # 这些 [来源1]、[来源2] 标签只在“当前这一次回答”里有效，
    # 用来把回答文本和本次检索结果逐条对齐。
    source_labels = [f"[来源{index}]" for index in range(1, len(results) + 1)]
    answer = f"根据 {source_labels[0]}，{primary.chunk.content}"
    if len(results) > 1:
        answer += f" 你还可以继续参考 {'、'.join(source_labels[1:])}。"

    return AnswerResult(
        question=question,
        answer=answer,
        sources=tuple(result.chunk.source for result in results),
        used_rag=True,
    )


def answer_question(question: str, top_k: int = 2) -> RoutedAnswerResult:
    """本章主入口函数。

    流程是：
    1. 先做路由判断。
    2. 再决定直接回答、查现有系统，还是进入 RAG。
    3. 最后返回一个脚本和测试都方便检查的统一结果对象。

    这个函数既会被在线演示脚本调用，也会被评估脚本调用：
    - 03_rag_pipeline.py 传入的是当前命令行问题
    - 01_minimum_eval.py 传入的是 JSON case 里的 question
    """

    decision = route_question(question)

    if decision.route == "直接回答":
        answer = lookup_general_knowledge(question)
        assert answer is not None
        return RoutedAnswerResult(
            question=question,
            route=decision.route,
            reason=decision.reason,
            answer=answer,
            sources=(),
            used_rag=False,
        )

    if decision.route == "直接查现有系统":
        result = lookup_existing_system(question)
        assert result is not None
        return RoutedAnswerResult(
            question=question,
            route=decision.route,
            reason=decision.reason,
            answer=result.answer,
            sources=result.sources,
            used_rag=False,
        )

    if decision.route == "固定 2-step RAG":
        # 这里包了一层 AnswerResult，用来保留“检索是否真的成功命中”的状态。
        result = answer_with_rag(question, top_k=top_k)
        return RoutedAnswerResult(
            question=question,
            route=decision.route,
            reason=decision.reason,
            answer=result.answer,
            sources=result.sources,
            used_rag=result.used_rag,
        )

    return RoutedAnswerResult(
        question=question,
        route=decision.route,
        reason=decision.reason,
        answer="我还不能稳定回答。请补充具体对象、来源，或把问题改写成更可检索的形式。",
        sources=(),
        used_rag=False,
    )


def recommend_solution(scenario: Scenario) -> tuple[str, str]:
    """为教学场景推荐一种知识接入方案。"""

    if scenario.wants_behavior_change and not scenario.knowledge_changes_often:
        return ("微调", "目标是学习稳定风格或行为，而不是频繁变化的外部知识。")

    if scenario.has_existing_system and scenario.structured_data:
        return ("直接查现有系统", "知识已经结构化并存在现成系统里，没必要先塞进向量库。")

    if (
        scenario.material_count == "few"
        and not scenario.needs_citations
        and not scenario.knowledge_changes_often
        and not scenario.needs_fast_validation
    ):
        return ("长上下文", "材料少且变化少，先直接把材料放进上下文更省事。")

    if (
        scenario.needs_fast_validation
        and not scenario.has_existing_system
        and not scenario.needs_dynamic_routing
    ):
        return ("Hosted File Search", "先快速验证价值，不必一开始就自建完整检索工程。")

    if scenario.needs_dynamic_routing:
        return ("Agentic RAG", "固定链路不够，需要动态决定查什么、查哪里、查几步。")

    if scenario.has_precise_keywords:
        return ("Hybrid RAG", "术语、编号和产品名很多时，需要关键词通道补足纯向量检索的漏召回。")

    if scenario.needs_citations or scenario.knowledge_changes_often:
        return ("固定 2-step RAG", "需要持续更新知识或显示来源时，先把固定检索链路做稳。")

    return ("固定 2-step RAG", "默认先做稳定的固定检索链路，再决定是否继续加复杂度。")


def default_scenarios() -> list[Scenario]:
    """提供 04_solution_decision.py 打印用的默认示例场景。"""

    return [
        Scenario(
            name="只分析 3 份短文档，一次性总结，不要求引用",
            material_count="few",
            needs_citations=False,
            knowledge_changes_often=False,
        ),
        Scenario(
            name="上传 10 份 PDF，想先做问答 Demo，不想先自建索引工程",
            material_count="many",
            needs_fast_validation=True,
            needs_citations=True,
        ),
        Scenario(
            name="FAQ 已经在 Elasticsearch 里，主要是查标准答案",
            material_count="many",
            has_existing_system=True,
            structured_data=True,
            needs_citations=True,
        ),
        Scenario(
            name="内部制度经常更新，还必须给出来源",
            material_count="many",
            needs_citations=True,
            knowledge_changes_often=True,
        ),
        Scenario(
            name="金融问答里有大量简称、代码和产品编号",
            material_count="many",
            needs_citations=True,
            knowledge_changes_often=True,
            has_precise_keywords=True,
        ),
        Scenario(
            name="想让模型长期学习固定写作风格",
            material_count="few",
            wants_behavior_change=True,
        ),
        Scenario(
            name="一个问题要在 FAQ、工单和数据库之间动态决策",
            material_count="many",
            needs_dynamic_routing=True,
            needs_citations=True,
        ),
    ]
