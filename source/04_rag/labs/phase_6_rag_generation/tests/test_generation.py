from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.chains.rag_chain import build_messages, format_context
from app.llms.providers import (
    GenerationProviderConfig,
    MockLLMClient,
    create_generation_client,
)
from app.prompts.rag_prompt import NO_ANSWER_TEXT, RAG_SYSTEM_PROMPT
from app.schemas import RetrievalResult, SourceChunk
from app.services.rag_service import RagService


class StaticRetriever:
    def __init__(self, results: list[RetrievalResult]) -> None:
        self.results = results

    def retrieve(self, question: str, top_k: int = 5) -> list[RetrievalResult]:
        del question
        return self.results[:top_k]


def make_result(content: str, *, score: float | None, filename: str, chunk_index: int) -> RetrievalResult:
    return RetrievalResult(
        chunk=SourceChunk(
            chunk_id=f"{filename}-{chunk_index}",
            document_id=filename,
            content=content,
            metadata={
                "filename": filename,
                "chunk_index": chunk_index,
                "source": f"data/{filename}",
            },
        ),
        score=score,
    )


class GenerationChainTests(unittest.TestCase):
    def test_format_context_includes_labels_metadata_and_score(self) -> None:
        result = make_result(
            "Source path and chunk index metadata are stored in SourceChunk.metadata.",
            score=0.812,
            filename="product_overview.md",
            chunk_index=2,
        )

        context = format_context([result], max_chunks=1, max_chars_per_chunk=120)

        self.assertIn("[S1]", context)
        self.assertIn("filename=product_overview.md", context)
        self.assertIn("chunk=2", context)
        self.assertIn("score=0.812", context)
        self.assertIn("SourceChunk.metadata", context)

    def test_build_messages_carries_system_prompt_context_and_question(self) -> None:
        result = make_result(
            "Chunk metadata keeps filename, source path and chunk index.",
            score=0.801,
            filename="product_overview.md",
            chunk_index=1,
        )

        messages = build_messages(
            question="Where do we keep source path metadata?",
            results=[result],
        )

        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[0]["content"], RAG_SYSTEM_PROMPT)
        self.assertEqual(messages[1]["role"], "user")
        self.assertIn("上下文：", messages[1]["content"])
        self.assertIn("问题：", messages[1]["content"])
        self.assertIn("Where do we keep source path metadata?", messages[1]["content"])
        self.assertIn("[S1]", messages[1]["content"])

    def test_rag_service_returns_no_answer_when_retriever_returns_nothing(self) -> None:
        llm = MockLLMClient(
            config=GenerationProviderConfig(
                provider_name="mock",
                model_name="mock-rag-answer-v1",
            )
        )
        service = RagService(retriever=StaticRetriever([]), llm=llm)

        result = service.ask("What is the capital of Mars?")

        self.assertEqual(result.answer, NO_ANSWER_TEXT)
        self.assertEqual(result.sources, [])
        self.assertEqual(service.last_messages, [])
        self.assertIsNone(service.last_generation_result)

    def test_rag_service_filters_out_low_score_results_before_generation(self) -> None:
        llm = MockLLMClient(
            config=GenerationProviderConfig(
                provider_name="mock",
                model_name="mock-rag-answer-v1",
            )
        )
        low_score = make_result(
            "This chunk is only weakly related to the question.",
            score=0.59,
            filename="faq.txt",
            chunk_index=0,
        )
        service = RagService(
            retriever=StaticRetriever([low_score]),
            llm=llm,
            min_source_score=0.60,
        )

        result = service.ask("What is the capital of Mars?")

        self.assertEqual(result.answer, NO_ANSWER_TEXT)
        self.assertEqual(result.sources, [])
        self.assertEqual(service.last_retrieval_results, [])
        self.assertIsNone(service.last_generation_result)

    def test_rag_service_returns_answer_and_sources_with_mock_llm(self) -> None:
        llm = MockLLMClient(
            config=GenerationProviderConfig(
                provider_name="mock",
                model_name="mock-rag-answer-v1",
            )
        )
        result_item = make_result(
            "Source path and chunk index metadata are stored in the SourceChunk metadata dictionary.",
            score=0.81,
            filename="product_overview.md",
            chunk_index=1,
        )
        service = RagService(
            retriever=StaticRetriever([result_item]),
            llm=llm,
        )

        result = service.ask("Where do we keep source path and chunk index metadata?")

        self.assertIn("[S1]", result.answer)
        self.assertEqual(len(result.sources), 1)
        self.assertEqual(result.sources[0].metadata["filename"], "product_overview.md")
        self.assertIsNotNone(service.last_generation_result)
        self.assertTrue(service.last_generation_result.mocked)

    def test_create_generation_client_falls_back_to_mock_when_api_key_missing(self) -> None:
        client = create_generation_client(
            GenerationProviderConfig(
                provider_name="openai_compatible",
                model_name="gpt-4o-mini",
                api_key_env="PHASE6_TEST_MISSING_API_KEY",
            )
        )

        self.assertIsInstance(client, MockLLMClient)


if __name__ == "__main__":
    unittest.main()
