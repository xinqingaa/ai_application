from pathlib import Path
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from generation_basics import (
    DemoRetriever,
    MockLLMClient,
    NO_ANSWER_TEXT,
    RAG_SYSTEM_PROMPT,
    RagService,
    RetrievalResult,
    SourceChunk,
    build_messages,
    extract_source_labels,
    format_context,
)


def make_result(content: str, *, score: float, filename: str, chunk_index: int) -> RetrievalResult:
    return RetrievalResult(
        chunk=SourceChunk(
            chunk_id=f"{filename}:{chunk_index}",
            document_id=filename,
            content=content,
            metadata={
                "filename": filename,
                "source": f"data/{filename}",
                "chunk_index": chunk_index,
            },
        ),
        score=score,
    )


class GenerationTests(unittest.TestCase):
    def test_demo_retriever_returns_refund_chunk(self) -> None:
        results = DemoRetriever().retrieve("退款规则是什么？", top_k=3)

        self.assertTrue(results)
        self.assertEqual(results[0].chunk.metadata["filename"], "refund_policy.md")
        self.assertGreaterEqual(results[0].score, 0.70)

    def test_format_context_includes_labels_metadata_and_score(self) -> None:
        result = make_result(
            "每个 chunk 应保留 source、filename 和 chunk_index，方便后续引用和调试。",
            score=0.812,
            filename="metadata_rules.md",
            chunk_index=0,
        )

        context = format_context([result], max_chunks=1, max_chars_per_chunk=80)

        self.assertIn("[S1]", context)
        self.assertIn("filename=metadata_rules.md", context)
        self.assertIn("chunk=0", context)
        self.assertIn("score=0.812", context)

    def test_build_messages_carries_system_prompt_context_and_question(self) -> None:
        result = make_result(
            "生成答案时应在关键结论后标注 [S1] 这样的来源标签。",
            score=0.805,
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

    def test_rag_service_refuses_when_no_result_passes_score_filter(self) -> None:
        service = RagService(
            retriever=DemoRetriever(),
            llm=MockLLMClient(),
            min_source_score=0.35,
        )

        result = service.ask("火星首都是什么？")

        self.assertEqual(result.answer, NO_ANSWER_TEXT)
        self.assertEqual(result.sources, [])
        self.assertEqual(service.last_messages, [])
        self.assertIsNone(service.last_generation_result)

    def test_rag_service_returns_answer_and_sources(self) -> None:
        service = RagService(
            retriever=DemoRetriever(),
            llm=MockLLMClient(),
            min_source_score=0.35,
        )

        result = service.ask("为什么回答里要带来源标签？")

        self.assertTrue(result.sources)
        self.assertEqual(len(result.sources), 2)
        self.assertIn("[S1]", result.answer)
        self.assertEqual(result.sources[0].metadata["filename"], "citation_rules.md")
        self.assertIsNotNone(service.last_generation_result)
        self.assertEqual(extract_source_labels(result.answer), ["S1", "S2"])


if __name__ == "__main__":
    unittest.main()
