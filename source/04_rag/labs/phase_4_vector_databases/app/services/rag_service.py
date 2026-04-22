from dataclasses import dataclass

from app.chains.rag_chain import build_prompt
from app.retrievers.base import Retriever
from app.schemas import AnswerResult


@dataclass(slots=True)
class RagService:
    """Unified entry point that now uses real retrieval but placeholder generation."""

    retriever: Retriever

    def ask(self, question: str, top_k: int = 5) -> AnswerResult:
        results = self.retriever.retrieve(question=question, top_k=top_k)
        prompt = build_prompt(question=question, results=results)
        return AnswerResult(
            answer=(
                "Phase 4 now retrieves real chunks from Chroma. Answer generation "
                "is still a placeholder until later phases.\n\nPrompt preview:\n"
                f"{prompt}"
            ),
            sources=[item.chunk for item in results],
        )
