from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
from typing import Callable, Sequence

from retrieval_basics import RetrievalResult


CHAPTER_ROOT = Path(__file__).resolve().parent
DEFAULT_RETRIEVAL_EVAL_PATH = CHAPTER_ROOT / "evals" / "retrieval_eval_cases.json"


@dataclass(frozen=True)
class RetrievalEvalCase:
    case_id: str
    question: str
    expected_chunk_ids: tuple[str, ...]
    filename_filter: str | None = None


@dataclass(frozen=True)
class RetrievalCaseMetrics:
    case_id: str
    retrieved_chunk_ids: tuple[str, ...]
    recall: float
    reciprocal_rank: float
    hit_rate: float


@dataclass(frozen=True)
class RetrievalEvaluationReport:
    recall: float
    mrr: float
    hit_rate: float
    case_count: int
    cases: tuple[RetrievalCaseMetrics, ...]


def recall_at_k(
    results: Sequence[RetrievalResult],
    expected_chunk_ids: Sequence[str],
) -> float:
    expected_ids = {str(chunk_id) for chunk_id in expected_chunk_ids}
    if not expected_ids:
        return 0.0

    actual_ids = {result.chunk.chunk_id for result in results}
    return len(actual_ids & expected_ids) / len(expected_ids)


def reciprocal_rank(
    results: Sequence[RetrievalResult],
    expected_chunk_ids: Sequence[str],
) -> float:
    expected_ids = {str(chunk_id) for chunk_id in expected_chunk_ids}
    if not expected_ids:
        return 0.0

    for rank, result in enumerate(results, start=1):
        if result.chunk.chunk_id in expected_ids:
            return 1.0 / rank
    return 0.0


def hit_rate(
    results: Sequence[RetrievalResult],
    expected_chunk_ids: Sequence[str],
) -> float:
    return 1.0 if reciprocal_rank(results, expected_chunk_ids) > 0.0 else 0.0


def load_eval_cases(path: Path = DEFAULT_RETRIEVAL_EVAL_PATH) -> list[RetrievalEvalCase]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Evaluation cases payload must be a list.")

    cases: list[RetrievalEvalCase] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("Each evaluation case must be an object.")

        expected_chunk_ids = item.get("expected_chunk_ids")
        if not isinstance(expected_chunk_ids, list) or not expected_chunk_ids:
            raise ValueError("Each evaluation case must have a non-empty expected_chunk_ids list.")

        filename_filter = item.get("filename_filter")
        cases.append(
            RetrievalEvalCase(
                case_id=str(item["case_id"]),
                question=str(item["question"]),
                expected_chunk_ids=tuple(str(chunk_id) for chunk_id in expected_chunk_ids),
                filename_filter=str(filename_filter) if filename_filter else None,
            )
        )
    return cases


def evaluate_retrieval_cases(
    cases: Sequence[RetrievalEvalCase],
    retrieve_fn: Callable[[RetrievalEvalCase], Sequence[RetrievalResult]],
) -> RetrievalEvaluationReport:
    if not cases:
        raise ValueError("At least one evaluation case is required.")

    case_metrics: list[RetrievalCaseMetrics] = []
    for case in cases:
        results = list(retrieve_fn(case))
        case_metrics.append(
            RetrievalCaseMetrics(
                case_id=case.case_id,
                retrieved_chunk_ids=tuple(result.chunk.chunk_id for result in results),
                recall=recall_at_k(results, case.expected_chunk_ids),
                reciprocal_rank=reciprocal_rank(results, case.expected_chunk_ids),
                hit_rate=hit_rate(results, case.expected_chunk_ids),
            )
        )

    total_cases = len(case_metrics)
    return RetrievalEvaluationReport(
        recall=sum(item.recall for item in case_metrics) / total_cases,
        mrr=sum(item.reciprocal_rank for item in case_metrics) / total_cases,
        hit_rate=sum(item.hit_rate for item in case_metrics) / total_cases,
        case_count=total_cases,
        cases=tuple(case_metrics),
    )
