from dataclasses import dataclass, field

from app.chains.rag_chain import build_messages
from app.config import settings
from app.llms.providers import GenerationResult, LLMClient
from app.prompts.rag_prompt import NO_ANSWER_TEXT
from app.retrievers.base import Retriever
from app.schemas import AnswerResult, RetrievalResult


def filter_retrieval_results(
    results: list[RetrievalResult],
    min_score: float,
) -> list[RetrievalResult]:
    """Keep only chunks that are strong enough to enter the generation context."""

    accepted: list[RetrievalResult] = []
    for item in results:
        if item.score is None or item.score >= min_score:
            accepted.append(item)
    return accepted


@dataclass(slots=True)
class RagService:
    """Unified entry point that now orchestrates retrieval and answer generation."""

    retriever: Retriever
    llm: LLMClient
    min_source_score: float = settings.default_generation_min_score
    last_messages: list[dict[str, str]] = field(default_factory=list)
    last_generation_result: GenerationResult | None = None
    last_retrieval_results: list[RetrievalResult] = field(default_factory=list)

    def ask(self, question: str, top_k: int = settings.default_top_k) -> AnswerResult:
        retrieved = self.retriever.retrieve(question=question, top_k=top_k)
        accepted = filter_retrieval_results(retrieved, min_score=self.min_source_score)
        self.last_retrieval_results = accepted

        if not accepted:
            self.last_messages = []
            self.last_generation_result = None
            return AnswerResult(answer=NO_ANSWER_TEXT, sources=[])

        messages = build_messages(question=question, results=accepted)
        self.last_messages = messages
        generation = self.llm.generate(messages=messages)
        self.last_generation_result = generation
        answer = generation.content.strip() or NO_ANSWER_TEXT
        return AnswerResult(
            answer=answer,
            sources=[item.chunk for item in accepted],
        )
