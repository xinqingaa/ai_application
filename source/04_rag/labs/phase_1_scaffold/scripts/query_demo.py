from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.schemas import RetrievalResult, SourceChunk
from app.services.rag_service import RagService


class MockRetriever:
    def retrieve(self, question: str, top_k: int = 5) -> list[RetrievalResult]:
        chunk = SourceChunk(
            chunk_id="demo:0",
            document_id="demo",
            content=f"Mock context for question: {question}",
            metadata={"source": "demo"},
        )
        return [RetrievalResult(chunk=chunk, score=1.0)]


def main() -> None:
    service = RagService(retriever=MockRetriever())
    result = service.ask("What should be implemented next?")
    print(result.answer)
    print(f"Sources: {[item.metadata.get('source') for item in result.sources]}")


if __name__ == "__main__":
    main()
