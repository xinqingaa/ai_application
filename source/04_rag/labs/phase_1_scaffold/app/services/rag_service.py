from dataclasses import dataclass

from app.chains.rag_chain import build_prompt
from app.retrievers.base import Retriever
from app.schemas import AnswerResult


@dataclass(slots=True)
class RagService:
    """Unified entry point that will later orchestrate retrieval and generation."""

    retriever: Retriever

    def ask(self, question: str, top_k: int = 5) -> AnswerResult:
        results = self.retriever.retrieve(question=question, top_k=top_k)
        prompt = build_prompt(question=question, results=results)
        return AnswerResult(
            answer=(
                "Phase 1 scaffold only. Replace this placeholder with a real LLM call "
                "in Phase 4.\n\nPrompt preview:\n"
                f"{prompt}"
            ),
            sources=[item.chunk for item in results],
        )
