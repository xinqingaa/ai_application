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
class Scenario:
    name: str
    material_count: str
    has_existing_system: bool = False
    structured_data: bool = False
    needs_citations: bool = False
    knowledge_changes_often: bool = False
    needs_dynamic_routing: bool = False
    wants_behavior_change: bool = False


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
    for keywords, answer in GENERAL_KNOWLEDGE_PATTERNS:
        if all(keyword in question for keyword in keywords):
            return answer

    return "我无法确定，因为这个问题依赖课程私有资料，而我现在没有检索到这些资料。"


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


def recommend_solution(scenario: Scenario) -> tuple[str, str]:
    if scenario.wants_behavior_change and not scenario.knowledge_changes_often:
        return ("微调", "目标是学习稳定风格或行为，而不是频繁变化的外部知识。")

    if scenario.has_existing_system and scenario.structured_data:
        return ("直接查现有系统", "知识已经结构化并存在现成系统里，没必要先塞进向量库。")

    if (
        scenario.material_count == "few"
        and not scenario.needs_citations
        and not scenario.knowledge_changes_often
    ):
        return ("长上下文", "材料少且变化少，先直接把材料放进上下文更省事。")

    if scenario.needs_dynamic_routing:
        return ("Agentic RAG", "固定链路不够，需要动态决定查什么、查哪里、查几步。")

    if scenario.needs_citations or scenario.knowledge_changes_often:
        return ("固定 2-step RAG", "需要持续更新知识或显示来源时，先把固定检索链路做稳。")

    return ("固定 2-step RAG", "默认先做稳定的固定检索链路，再决定是否继续加复杂度。")


def default_scenarios() -> list[Scenario]:
    return [
        Scenario(
            name="上传 10 份 PDF，想快速做问答验证",
            material_count="few",
            needs_citations=False,
            knowledge_changes_often=False,
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
