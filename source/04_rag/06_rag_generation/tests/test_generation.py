from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from generation_basics import (
    Chapter5DemoRetriever,
    MockLLMClient,
    NO_ANSWER_TEXT,
    RAG_SYSTEM_PROMPT,
    RagService,
    RetrievalResult,
    SourceChunk,
    build_messages,
    context_relevance_score,
    extract_source_labels,
    format_context,
)


def make_result(content: str, *, score: float, filename: str, chunk_index: int) -> RetrievalResult:
    char_count = len(content)
    return RetrievalResult(
        chunk=SourceChunk(
            chunk_id=f"{filename}:{chunk_index}",
            document_id=filename,
            content=content,
            metadata={
                "filename": filename,
                "source": f"data/{filename}",
                "suffix": ".md",
                "chunk_index": chunk_index,
                "char_start": 0,
                "char_end": char_count,
                "chunk_chars": char_count,
            },
        ),
        score=score,
    )


class GenerationTests(unittest.TestCase):
    def test_chapter5_demo_retriever_reuses_rich_retrieval_contract(self) -> None:
        results = Chapter5DemoRetriever().retrieve("退款规则是什么？", top_k=5)

        self.assertTrue(results)
        self.assertEqual(results[0].chunk.metadata["filename"], "refund_policy.md")
        self.assertIn("suffix", results[0].chunk.metadata)
        self.assertIn("char_start", results[0].chunk.metadata)
        self.assertIn("char_end", results[0].chunk.metadata)
        self.assertIn("chunk_chars", results[0].chunk.metadata)

    def test_format_context_includes_labels_and_scores(self) -> None:
        result = make_result(
            "回答里要带来源标签，例如 [S1]、[S2]，这样用户才能核对答案依据和引用位置。",
            score=0.843,
            filename="citation_rules.md",
            chunk_index=0,
        )

        context = format_context(
            "为什么回答里要带来源标签？",
            [result],
            max_chunks=1,
            max_chars_per_chunk=80,
        )

        self.assertIn("[S1]", context)
        self.assertIn("filename=citation_rules.md", context)
        self.assertIn("chunk=0", context)
        self.assertIn("retrieval_score=0.843", context)
        self.assertIn(
            f"context_score={context_relevance_score('为什么回答里要带来源标签？', result.chunk.content):.3f}",
            context,
        )

    def test_build_messages_carries_system_prompt_context_and_question(self) -> None:
        result = make_result(
            "回答里要带来源标签，例如 [S1]、[S2]，这样用户才能核对答案依据和引用位置。",
            score=0.843,
            filename="citation_rules.md",
            chunk_index=0,
        )

        messages = build_messages("为什么回答里要带来源标签？", [result])

        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[0]["content"], RAG_SYSTEM_PROMPT)
        self.assertEqual(messages[1]["role"], "user")
        self.assertIn("上下文：", messages[1]["content"])
        self.assertIn("问题：", messages[1]["content"])
        self.assertIn("为什么回答里要带来源标签？", messages[1]["content"])
        self.assertIn("[S1]", messages[1]["content"])

    def test_rag_service_refuses_when_no_result_passes_context_filter(self) -> None:
        service = RagService(
            retriever=Chapter5DemoRetriever(),
            llm=MockLLMClient(),
            min_context_score=0.35,
        )

        result = service.ask("火星首都是什么？", top_k=5)

        self.assertTrue(service.last_retrieved_results)
        self.assertEqual(result.answer, NO_ANSWER_TEXT)
        self.assertEqual(result.sources, [])
        self.assertEqual(service.last_messages, [])
        self.assertIsNone(service.last_generation_result)

    def test_rag_service_returns_answer_and_used_sources(self) -> None:
        service = RagService(
            retriever=Chapter5DemoRetriever(),
            llm=MockLLMClient(),
            min_context_score=0.35,
        )

        result = service.ask("为什么回答里要带来源标签？", top_k=5)

        self.assertTrue(result.sources)
        self.assertEqual(len(result.sources), 2)
        self.assertIn("[S1]", result.answer)
        self.assertEqual(
            [source.metadata["filename"] for source in result.sources],
            ["citation_rules.md", "metadata_rules.md"],
        )
        self.assertIsNotNone(service.last_generation_result)
        self.assertEqual(extract_source_labels(result.answer), ["S1", "S2"])

    def test_rag_service_sources_follow_prompt_labels_when_top_k_exceeds_max_chunks(self) -> None:
        service = RagService(
            retriever=Chapter5DemoRetriever(),
            llm=MockLLMClient(),
            min_context_score=0.0,
            max_chunks=2,
        )

        result = service.ask("为什么回答里要带来源标签？", top_k=5)

        self.assertEqual(len(service.last_retrieved_results), 5)
        self.assertEqual(len(service.last_accepted_results), 5)
        self.assertEqual(len(service.last_prompt_results), 2)
        self.assertEqual(len(result.sources), 2)
        self.assertEqual(extract_source_labels(result.answer), ["S1", "S2"])
        self.assertEqual(
            [source.metadata["filename"] for source in result.sources],
            [item.chunk.metadata["filename"] for item in service.last_prompt_results],
        )


if __name__ == "__main__":
    unittest.main()
