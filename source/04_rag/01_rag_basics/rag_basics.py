from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class KnowledgeChunk:
    chunk_id: str
    source: str
    title: str
    content: str
    keywords: tuple[str, ...]


@dataclass(frozen=True)
class RetrievalResult:
    chunk: KnowledgeChunk
    score: float
    matched_keywords: tuple[str, ...]


@dataclass(frozen=True)
class AnswerResult:
    question: str
    answer: str
    sources: tuple[str, ...]
    used_rag: bool


@dataclass(frozen=True)
class RouteDecision:
    route: str
    reason: str


@dataclass(frozen=True)
class RoutedAnswerResult:
    question: str
    route: str
    reason: str
    answer: str
    sources: tuple[str, ...]
    used_rag: bool


@dataclass(frozen=True)
class Scenario:
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

GENERAL_KNOWLEDGE_PATTERNS = [
    (("法国", "首都"), "法国首都是巴黎。"),
    (("水", "化学式"), "水的化学式是 H2O。"),
]

STRUCTURED_SYSTEM_PATTERNS = [
    (
        ("订单", "1024", "状态"),
        "订单 1024 当前已支付，等待开课。",
        "orders_table",
    ),
]

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


def lookup_general_knowledge(question: str) -> str | None:
    for keywords, answer in GENERAL_KNOWLEDGE_PATTERNS:
        if all(keyword in question for keyword in keywords):
            return answer
    return None


def lookup_existing_system(question: str) -> AnswerResult | None:
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
    return any(keyword in question for keyword in PRIVATE_KNOWLEDGE_HINTS)


def route_question(question: str) -> RouteDecision:
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
    base = knowledge_base or COURSE_KNOWLEDGE_BASE
    scored_results: list[RetrievalResult] = []

    for chunk in base:
        matched_keywords = tuple(keyword for keyword in chunk.keywords if keyword in question)
        if not matched_keywords:
            continue

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
    if not results:
        return "(empty)"

    lines = []
    for index, result in enumerate(results, start=1):
        lines.append(
            f"[S{index}] source={result.chunk.source} title={result.chunk.title} "
            f"content={result.chunk.content}"
        )
    return "\n".join(lines)


def answer_without_rag(question: str) -> str:
    direct_answer = lookup_general_knowledge(question)
    if direct_answer is not None:
        return direct_answer

    return "我无法确定，因为单次调用里没有足够依据。这可能需要额外知识源或补充上下文。"


def answer_with_rag(question: str, top_k: int = 2) -> AnswerResult:
    results = retrieve(question, top_k=top_k)
    if not results:
        return AnswerResult(
            question=question,
            answer="我不知道，因为当前知识库里没有命中相关资料。",
            sources=(),
            used_rag=False,
        )

    primary = results[0]
    citations = [f"[S{index}]" for index in range(1, len(results) + 1)]
    answer = f"根据 {citations[0]}，{primary.chunk.content}"
    if len(results) > 1:
        answer += f" 你还可以继续参考 {'、'.join(citations[1:])}。"

    return AnswerResult(
        question=question,
        answer=answer,
        sources=tuple(result.chunk.source for result in results),
        used_rag=True,
    )


def answer_question(question: str, top_k: int = 2) -> RoutedAnswerResult:
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
