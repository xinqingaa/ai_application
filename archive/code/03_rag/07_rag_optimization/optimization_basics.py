from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
import json
import re
import sys
from typing import Any, Sequence


CHAPTER_ROOT = Path(__file__).resolve().parent
CHAPTER5_ROOT = CHAPTER_ROOT.parent / "05_retrieval_strategies"
CHAPTER6_ROOT = CHAPTER_ROOT.parent / "06_rag_generation"
DEFAULT_STORE_PATH = CHAPTER_ROOT / "store" / "demo_optimization_store.json"
DEFAULT_GOLDEN_SET_PATH = CHAPTER_ROOT / "evals" / "golden_set.json"
DEFAULT_EXPERIMENT_CONFIG_PATH = CHAPTER_ROOT / "evals" / "experiment_configs.json"

if str(CHAPTER5_ROOT) not in sys.path:
    sys.path.insert(0, str(CHAPTER5_ROOT))
if str(CHAPTER6_ROOT) not in sys.path:
    sys.path.insert(0, str(CHAPTER6_ROOT))

from generation_basics import (  # noqa: E402
    NO_ANSWER_TEXT,
    RAG_SYSTEM_PROMPT,
    RAG_USER_TEMPLATE,
    MockLLMClient,
    RagService,
    build_generation_demo_store,
    create_generation_client,
    extract_source_labels,
    generation_demo_source_chunks,
)
from llm_utils import GenerationResult, LLMClient  # noqa: E402
from retrieval_basics import LocalKeywordEmbeddingProvider, RetrievalResult, SimpleRetriever  # noqa: E402
from retrieval_metrics import (  # noqa: E402
    RetrievalEvalCase,
    RetrievalEvaluationReport,
    evaluate_retrieval_cases,
    hit_rate,
    recall_at_k,
    reciprocal_rank,
)
from smart_retrieval_engine import SmartRetrievalConfig, SmartRetrievalEngine  # noqa: E402


STRICT_CITATION_SYSTEM_PROMPT = """
你是一个基于检索上下文回答问题的助手。
你只能复述上下文中已经出现的事实，不要补充常识推断。
每个关键结论后都必须标注来源标签，例如 [S1]、[S2]。
如果上下文证据不足，唯一允许的回答是“我不知道”。
""".strip()

LOOSE_SYSTEM_PROMPT = """
你是课程助手。请根据给定内容自然回答问题，优先保证可读性。
""".strip()

STRICT_CITATION_USER_TEMPLATE = """
请只依据下面的检索上下文回答问题。

上下文：
{context}

问题：
{question}

回答要求：
1. 只能使用上下文中的事实，不要引入额外知识。
2. 每个关键结论后都必须标注来源标签，例如 [S1]。
3. 如果证据不足，只能回答“我不知道”。
4. 不要省略来源标签。
""".strip()

LOOSE_USER_TEMPLATE = """
请根据下面的上下文回答问题。

上下文：
{context}

问题：
{question}

回答要求：
1. 尽量自然作答。
2. 如果需要，可以补一句解释帮助用户理解。
""".strip()


@dataclass(frozen=True)
class PromptVariant:
    key: str
    label: str
    system_prompt: str
    user_template: str
    note: str


PROMPT_VARIANTS: dict[str, PromptVariant] = {
    "baseline": PromptVariant(
        key="baseline",
        label="Baseline Prompt",
        system_prompt=RAG_SYSTEM_PROMPT,
        user_template=RAG_USER_TEMPLATE,
        note="延续第六章默认 Prompt，显式要求引用和拒答。",
    ),
    "strict_citation": PromptVariant(
        key="strict_citation",
        label="Strict Citation Prompt",
        system_prompt=STRICT_CITATION_SYSTEM_PROMPT,
        user_template=STRICT_CITATION_USER_TEMPLATE,
        note="更强地约束引用和拒答边界，优先保护可追溯性。",
    ),
    "loose_answer": PromptVariant(
        key="loose_answer",
        label="Loose Answer Prompt",
        system_prompt=LOOSE_SYSTEM_PROMPT,
        user_template=LOOSE_USER_TEMPLATE,
        note="故意弱化引用约束，用来观察生成质量退化。",
    ),
}


@dataclass(frozen=True)
class GoldenSetCase:
    case_id: str
    question: str
    expected_answer: str
    expected_answer_points: tuple[str, ...]
    expected_sources: tuple[str, ...]
    retrieval_expected_chunk_ids: tuple[str, ...]
    should_refuse: bool = False
    tags: tuple[str, ...] = ()
    filename_filter: str | None = None
    notes: str | None = None


@dataclass(frozen=True)
class ExperimentConfig:
    config_id: str
    label: str
    retrieval: SmartRetrievalConfig
    min_context_score: float = 0.35
    max_chunks: int = 3
    max_chars_per_chunk: int = 90
    prompt_variant: str = "baseline"
    notes: str | None = None


@dataclass(frozen=True)
class LLMRuntimeConfig:
    backend: str = "policy_mock"
    provider: str | None = None
    temperature: float = 0.0
    max_tokens: int = 280
    timeout: float = 20.0
    max_retries: int = 0

    def __post_init__(self) -> None:
        if self.backend not in {"policy_mock", "provider"}:
            raise ValueError(f"Unsupported llm backend: {self.backend}")
        if self.timeout <= 0:
            raise ValueError("timeout must be positive.")
        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive.")
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative.")


@dataclass(frozen=True)
class RagCaseMetrics:
    case_id: str
    question: str
    answer: str
    source_filenames: tuple[str, ...]
    retrieved_chunk_ids: tuple[str, ...]
    prompt_chunk_ids: tuple[str, ...]
    has_retrieval_target: bool
    retrieval_recall: float
    retrieval_rr: float
    retrieval_hit_rate: float
    answer_point_recall: float | None
    source_hit_rate: float | None
    citation_support: float
    refusal_correct: bool
    passed: bool
    failure_stage: str
    missing_answer_points: tuple[str, ...]
    missing_sources: tuple[str, ...]
    labels_in_answer: tuple[str, ...]


@dataclass(frozen=True)
class RagEvaluationReport:
    retrieval_recall: float
    retrieval_mrr: float
    retrieval_hit_rate: float
    answer_point_recall: float
    source_hit_rate: float
    citation_support_rate: float
    refusal_accuracy: float
    pass_rate: float
    case_count: int
    answerable_case_count: int
    refusal_case_count: int
    cases: tuple[RagCaseMetrics, ...]


@dataclass(frozen=True)
class ExperimentComparisonRow:
    config_id: str
    label: str
    prompt_variant: str
    retrieval_strategy: str
    retrieval_recall: float
    retrieval_mrr: float
    answer_point_recall: float
    source_hit_rate: float
    citation_support_rate: float
    refusal_accuracy: float
    pass_rate: float
    composite_score: float
    notes: str | None = None


@dataclass(frozen=True)
class BadCaseRecord:
    case_id: str
    question: str
    failure_stage: str
    summary: str
    retrieved_chunk_ids: tuple[str, ...]
    prompt_chunk_ids: tuple[str, ...]
    answer: str


class PolicyAwareMockLLMClient:
    def __init__(self) -> None:
        self._baseline = MockLLMClient(provider_name="mock_policy", model_name="mock-policy-rag-v1")

    def describe(self) -> dict[str, Any]:
        return {
            "provider": "mock_policy",
            "model": "mock-policy-rag-v1",
            "mocked": True,
            "policy_aware": True,
        }

    def generate(self, messages: list[dict[str, str]]) -> GenerationResult:
        baseline = self._baseline.generate(messages)
        answer = baseline.content.strip() or NO_ANSWER_TEXT
        labels = list(baseline.used_labels)
        prompt_text = "\n".join(message.get("content", "") for message in messages)
        prompt_lower = prompt_text.lower()

        strict_citation = ("来源标签" in prompt_text or "must" in prompt_lower) and "[s1]" in prompt_lower
        loose_answer = "自然作答" in prompt_text or "优先保证可读性" in prompt_text

        if answer != NO_ANSWER_TEXT and loose_answer:
            answer = re.sub(r"\s*\[S\d+\]", "", answer).strip()
            labels = []
            if not answer.endswith("。"):
                answer += "。"
            answer += " 如需进一步确认，建议结合完整课程说明继续判断。"

        if answer != NO_ANSWER_TEXT and strict_citation and not labels:
            labels = extract_source_labels(answer)

        return GenerationResult(
            provider="mock_policy",
            model="mock-policy-rag-v1",
            content=answer,
            finish_reason="mock_policy_stop",
            request_preview={"messages": messages},
            raw_response_preview={
                "answer_preview": answer[:200],
                "strict_citation": strict_citation,
                "loose_answer": loose_answer,
            },
            mocked=True,
            used_labels=labels,
        )


def default_llm_runtime() -> LLMRuntimeConfig:
    return LLMRuntimeConfig()


def build_llm_client(runtime: LLMRuntimeConfig | None = None) -> LLMClient:
    active_runtime = runtime or default_llm_runtime()
    if active_runtime.backend == "policy_mock":
        return PolicyAwareMockLLMClient()
    return create_generation_client(
        provider=active_runtime.provider,
        temperature=active_runtime.temperature,
        max_tokens=active_runtime.max_tokens,
        timeout=active_runtime.timeout,
        max_retries=active_runtime.max_retries,
    )


class SmartEngineRetrieverAdapter:
    def __init__(self, engine: SmartRetrievalEngine, config: SmartRetrievalConfig) -> None:
        self.engine = engine
        self.config = config

    def retrieve(self, question: str, top_k: int = 5) -> list[RetrievalResult]:
        rerank_top_n = self.config.rerank_top_n
        if self.config.rerank and rerank_top_n is not None:
            rerank_top_n = max(rerank_top_n, top_k)

        runtime_config = replace(
            self.config,
            top_k=top_k,
            candidate_k=max(self.config.candidate_k, top_k),
            rerank_top_n=rerank_top_n,
        )
        return list(self.engine.retrieve(question, runtime_config))


def resolve_prompt_variant(key: str) -> PromptVariant:
    variant = PROMPT_VARIANTS.get(key)
    if variant is None:
        raise ValueError(f"Unknown prompt variant: {key}")
    return variant


def load_golden_set(path: Path = DEFAULT_GOLDEN_SET_PATH) -> list[GoldenSetCase]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Golden set payload must be a list.")

    cases: list[GoldenSetCase] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("Each golden set case must be an object.")

        cases.append(
            GoldenSetCase(
                case_id=str(item["case_id"]),
                question=str(item["question"]),
                expected_answer=str(item.get("expected_answer", "")),
                expected_answer_points=_as_string_tuple(item.get("expected_answer_points")),
                expected_sources=_as_string_tuple(item.get("expected_sources")),
                retrieval_expected_chunk_ids=_as_string_tuple(item.get("retrieval_expected_chunk_ids")),
                should_refuse=bool(item.get("should_refuse", False)),
                tags=_as_string_tuple(item.get("tags")),
                filename_filter=_as_optional_string(item.get("filename_filter")),
                notes=_as_optional_string(item.get("notes")),
            )
        )
    return cases


def load_experiment_configs(path: Path = DEFAULT_EXPERIMENT_CONFIG_PATH) -> list[ExperimentConfig]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Experiment config payload must be a list.")

    configs: list[ExperimentConfig] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("Each experiment config must be an object.")

        retrieval = SmartRetrievalConfig(
            strategy=str(item.get("strategy", "similarity")),
            top_k=int(item.get("top_k", 3)),
            candidate_k=int(item.get("candidate_k", 4)),
            score_threshold=float(item.get("score_threshold", 0.80)),
            mmr_lambda=float(item.get("mmr_lambda", 0.35)),
            hybrid_alpha=float(item.get("hybrid_alpha", 0.5)),
            filename_filter=_as_optional_string(item.get("filename_filter")),
            rerank=bool(item.get("rerank", False)),
            fetch_k=_as_optional_int(item.get("fetch_k")),
            rerank_top_n=_as_optional_int(item.get("rerank_top_n")),
        )
        prompt_variant = str(item.get("prompt_variant", "baseline"))
        resolve_prompt_variant(prompt_variant)
        configs.append(
            ExperimentConfig(
                config_id=str(item["config_id"]),
                label=str(item["label"]),
                retrieval=retrieval,
                min_context_score=float(item.get("min_context_score", 0.35)),
                max_chunks=int(item.get("max_chunks", 3)),
                max_chars_per_chunk=int(item.get("max_chars_per_chunk", 90)),
                prompt_variant=prompt_variant,
                notes=_as_optional_string(item.get("notes")),
            )
        )
    return configs


def build_generation_smart_engine(
    store_path: Path = DEFAULT_STORE_PATH,
    reset_store: bool = False,
) -> tuple[SmartRetrievalEngine, Any]:
    store_path.parent.mkdir(parents=True, exist_ok=True)
    provider = LocalKeywordEmbeddingProvider()
    store = build_generation_demo_store(
        provider=provider,
        store_path=store_path,
        reset_store=reset_store,
    )
    retriever = SimpleRetriever(store=store, provider=provider)
    engine = SmartRetrievalEngine(retriever, corpus=generation_demo_source_chunks())
    return engine, store


def build_rag_service(
    experiment: ExperimentConfig,
    *,
    store_path: Path = DEFAULT_STORE_PATH,
    llm: LLMClient | None = None,
    llm_runtime: LLMRuntimeConfig | None = None,
    reset_store: bool = False,
) -> tuple[RagService, SmartRetrievalEngine, Any]:
    engine, store = build_generation_smart_engine(
        store_path=store_path,
        reset_store=reset_store,
    )
    prompt_variant = resolve_prompt_variant(experiment.prompt_variant)
    service = RagService(
        retriever=SmartEngineRetrieverAdapter(engine, experiment.retrieval),
        llm=llm or build_llm_client(llm_runtime),
        min_context_score=experiment.min_context_score,
        max_chunks=experiment.max_chunks,
        max_chars_per_chunk=experiment.max_chars_per_chunk,
        system_prompt=prompt_variant.system_prompt,
        user_template=prompt_variant.user_template,
    )
    return service, engine, store


def golden_cases_with_retrieval_targets(cases: Sequence[GoldenSetCase]) -> list[GoldenSetCase]:
    return [case for case in cases if case.retrieval_expected_chunk_ids]


def golden_cases_to_retrieval_eval_cases(cases: Sequence[GoldenSetCase]) -> list[RetrievalEvalCase]:
    return [
        RetrievalEvalCase(
            case_id=case.case_id,
            question=case.question,
            expected_chunk_ids=case.retrieval_expected_chunk_ids,
            filename_filter=case.filename_filter,
        )
        for case in golden_cases_with_retrieval_targets(cases)
    ]


def evaluate_retrieval_from_golden_set(
    cases: Sequence[GoldenSetCase],
    engine: SmartRetrievalEngine,
    config: SmartRetrievalConfig,
) -> RetrievalEvaluationReport:
    retrieval_cases = golden_cases_to_retrieval_eval_cases(cases)
    if not retrieval_cases:
        raise ValueError("Golden set has no retrieval cases.")

    return evaluate_retrieval_cases(
        retrieval_cases,
        lambda case: engine.retrieve(
            case.question,
            replace(
                config,
                filename_filter=case.filename_filter or config.filename_filter,
            ),
        ),
    )


def evaluate_rag_cases(
    cases: Sequence[GoldenSetCase],
    service: RagService,
    *,
    top_k: int,
) -> RagEvaluationReport:
    case_metrics: list[RagCaseMetrics] = []
    answerable_cases = 0
    refusal_cases = 0

    for case in cases:
        result = service.ask(case.question, top_k=top_k)
        source_filenames = tuple(_source_filenames(result.sources))
        retrieved_chunk_ids = tuple(item.chunk.chunk_id for item in service.last_retrieved_results)
        prompt_chunk_ids = tuple(item.chunk.chunk_id for item in service.last_prompt_results)
        labels = tuple(extract_source_labels(result.answer))

        retrieval_recall = 0.0
        retrieval_rr = 0.0
        retrieval_hit = 0.0
        if case.retrieval_expected_chunk_ids:
            retrieval_recall = recall_at_k(service.last_retrieved_results, case.retrieval_expected_chunk_ids)
            retrieval_rr = reciprocal_rank(service.last_retrieved_results, case.retrieval_expected_chunk_ids)
            retrieval_hit = hit_rate(service.last_retrieved_results, case.retrieval_expected_chunk_ids)

        if case.should_refuse:
            refusal_cases += 1
            refusal_correct = result.answer.strip() == NO_ANSWER_TEXT
            answer_point_recall = None
            source_hit_rate = None
            citation_support = 1.0 if refusal_correct and not labels and not source_filenames else 0.0
            missing_points: tuple[str, ...] = ()
            missing_sources: tuple[str, ...] = ()
        else:
            answerable_cases += 1
            refusal_correct = result.answer.strip() != NO_ANSWER_TEXT
            missing_points = tuple(
                point
                for point in case.expected_answer_points
                if _normalize(point) not in _normalize(result.answer)
            )
            missing_sources = tuple(
                source
                for source in case.expected_sources
                if source not in source_filenames
            )
            answer_point_recall = _expected_subset_recall(case.expected_answer_points, result.answer)
            source_hit_rate = _expected_source_recall(case.expected_sources, source_filenames)
            citation_support = 1.0 if labels and not missing_sources else 0.0

        failure_stage = _classify_failure_stage(
            case=case,
            refusal_correct=refusal_correct,
            retrieval_hit=retrieval_hit,
            answer_point_recall=answer_point_recall,
            source_hit_rate=source_hit_rate,
            labels=labels,
        )
        passed = failure_stage == "pass"

        case_metrics.append(
            RagCaseMetrics(
                case_id=case.case_id,
                question=case.question,
                answer=result.answer,
                source_filenames=source_filenames,
                retrieved_chunk_ids=retrieved_chunk_ids,
                prompt_chunk_ids=prompt_chunk_ids,
                has_retrieval_target=bool(case.retrieval_expected_chunk_ids),
                retrieval_recall=retrieval_recall,
                retrieval_rr=retrieval_rr,
                retrieval_hit_rate=retrieval_hit,
                answer_point_recall=answer_point_recall,
                source_hit_rate=source_hit_rate,
                citation_support=citation_support,
                refusal_correct=refusal_correct,
                passed=passed,
                failure_stage=failure_stage,
                missing_answer_points=missing_points,
                missing_sources=missing_sources,
                labels_in_answer=labels,
            )
        )

    retrieval_cases = [case for case in case_metrics if case.has_retrieval_target]
    answerable_metrics = [case for case in case_metrics if case.answer_point_recall is not None]
    refusal_metrics = [case for case in case_metrics if case.answer_point_recall is None]

    return RagEvaluationReport(
        retrieval_recall=_mean(case.retrieval_recall for case in retrieval_cases),
        retrieval_mrr=_mean(case.retrieval_rr for case in retrieval_cases),
        retrieval_hit_rate=_mean(case.retrieval_hit_rate for case in retrieval_cases),
        answer_point_recall=_mean(
            case.answer_point_recall for case in answerable_metrics if case.answer_point_recall is not None
        ),
        source_hit_rate=_mean(
            case.source_hit_rate for case in answerable_metrics if case.source_hit_rate is not None
        ),
        citation_support_rate=_mean(case.citation_support for case in answerable_metrics),
        refusal_accuracy=_mean(1.0 if case.refusal_correct else 0.0 for case in refusal_metrics),
        pass_rate=_mean(1.0 if case.passed else 0.0 for case in case_metrics),
        case_count=len(case_metrics),
        answerable_case_count=answerable_cases,
        refusal_case_count=refusal_cases,
        cases=tuple(case_metrics),
    )


def compare_experiments(
    cases: Sequence[GoldenSetCase],
    experiments: Sequence[ExperimentConfig],
    *,
    store_path: Path = DEFAULT_STORE_PATH,
    llm_runtime: LLMRuntimeConfig | None = None,
) -> list[ExperimentComparisonRow]:
    rows: list[ExperimentComparisonRow] = []
    for index, experiment in enumerate(experiments):
        service, engine, _ = build_rag_service(
            experiment,
            store_path=store_path,
            llm_runtime=llm_runtime,
            reset_store=index == 0,
        )
        retrieval_report = evaluate_retrieval_from_golden_set(cases, engine, experiment.retrieval)
        rag_report = evaluate_rag_cases(
            cases,
            service,
            top_k=experiment.retrieval.top_k,
        )
        composite_score = (
            retrieval_report.recall * 0.20
            + retrieval_report.mrr * 0.10
            + rag_report.answer_point_recall * 0.20
            + rag_report.source_hit_rate * 0.15
            + rag_report.citation_support_rate * 0.15
            + rag_report.refusal_accuracy * 0.10
            + rag_report.pass_rate * 0.10
        )
        rows.append(
            ExperimentComparisonRow(
                config_id=experiment.config_id,
                label=experiment.label,
                prompt_variant=experiment.prompt_variant,
                retrieval_strategy=experiment.retrieval.strategy,
                retrieval_recall=retrieval_report.recall,
                retrieval_mrr=retrieval_report.mrr,
                answer_point_recall=rag_report.answer_point_recall,
                source_hit_rate=rag_report.source_hit_rate,
                citation_support_rate=rag_report.citation_support_rate,
                refusal_accuracy=rag_report.refusal_accuracy,
                pass_rate=rag_report.pass_rate,
                composite_score=composite_score,
                notes=experiment.notes,
            )
        )
    return sorted(rows, key=lambda item: (item.composite_score, item.pass_rate), reverse=True)


def collect_bad_cases(report: RagEvaluationReport) -> list[BadCaseRecord]:
    bad_cases: list[BadCaseRecord] = []
    for case in report.cases:
        if case.passed:
            continue
        bad_cases.append(
            BadCaseRecord(
                case_id=case.case_id,
                question=case.question,
                failure_stage=case.failure_stage,
                summary=_summarize_failure(case),
                retrieved_chunk_ids=case.retrieved_chunk_ids,
                prompt_chunk_ids=case.prompt_chunk_ids,
                answer=case.answer,
            )
        )
    return bad_cases


def summarize_golden_set(cases: Sequence[GoldenSetCase]) -> dict[str, int]:
    return {
        "total_cases": len(cases),
        "retrieval_cases": sum(1 for case in cases if case.retrieval_expected_chunk_ids),
        "answerable_cases": sum(1 for case in cases if not case.should_refuse),
        "refusal_cases": sum(1 for case in cases if case.should_refuse),
        "cases_with_expected_sources": sum(1 for case in cases if case.expected_sources),
    }


def format_retrieval_report(report: RetrievalEvaluationReport) -> str:
    lines = [
        f"cases={report.case_count}",
        f"recall={report.recall:.3f}",
        f"mrr={report.mrr:.3f}",
        f"hit_rate={report.hit_rate:.3f}",
    ]
    return " | ".join(lines)


def format_rag_report(report: RagEvaluationReport) -> str:
    lines = [
        f"cases={report.case_count}",
        f"retrieval_recall={report.retrieval_recall:.3f}",
        f"retrieval_mrr={report.retrieval_mrr:.3f}",
        f"answer_point_recall={report.answer_point_recall:.3f}",
        f"source_hit_rate={report.source_hit_rate:.3f}",
        f"citation_support={report.citation_support_rate:.3f}",
        f"refusal_accuracy={report.refusal_accuracy:.3f}",
        f"pass_rate={report.pass_rate:.3f}",
    ]
    return " | ".join(lines)


def _as_string_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError("Expected a list of strings.")
    return tuple(str(item) for item in value)


def _as_optional_string(value: object) -> str | None:
    if value is None or value == "":
        return None
    return str(value)


def _as_optional_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", "", text).lower()


def _source_filenames(sources: Sequence[Any]) -> list[str]:
    filenames: list[str] = []
    for source in sources:
        filename = source.metadata.get("filename", "unknown")
        filenames.append(str(filename))
    return filenames


def _expected_subset_recall(expected_points: Sequence[str], answer: str) -> float:
    if not expected_points:
        return 1.0
    normalized_answer = _normalize(answer)
    matched = sum(1 for point in expected_points if _normalize(point) in normalized_answer)
    return matched / len(expected_points)


def _expected_source_recall(expected_sources: Sequence[str], actual_sources: Sequence[str]) -> float:
    if not expected_sources:
        return 1.0
    actual = set(actual_sources)
    matched = sum(1 for source in expected_sources if source in actual)
    return matched / len(expected_sources)


def _classify_failure_stage(
    *,
    case: GoldenSetCase,
    refusal_correct: bool,
    retrieval_hit: float,
    answer_point_recall: float | None,
    source_hit_rate: float | None,
    labels: Sequence[str],
) -> str:
    if not refusal_correct:
        return "refusal_boundary"
    if case.should_refuse:
        return "pass"
    if case.retrieval_expected_chunk_ids and retrieval_hit == 0.0:
        return "retrieval"
    if source_hit_rate is not None and source_hit_rate < 1.0:
        return "citation_alignment"
    if not labels:
        return "citation_format"
    if answer_point_recall is not None and answer_point_recall < 1.0:
        return "answer_quality"
    return "pass"


def _summarize_failure(case: RagCaseMetrics) -> str:
    if case.failure_stage == "retrieval":
        return "未召回预期 chunk，先回看 top_k / candidate_k / hybrid / rerank。"
    if case.failure_stage == "citation_alignment":
        return "答案缺少预期来源，先检查 Prompt 引用要求和 sources 对齐逻辑。"
    if case.failure_stage == "citation_format":
        return "答案缺少来源标签，优先加强 Prompt 的 citation 约束。"
    if case.failure_stage == "refusal_boundary":
        return "拒答边界错误，优先检查 min_context_score 和 refusal 指令。"
    if case.failure_stage == "answer_quality":
        return "答案没有覆盖预期要点，先检查上下文裁剪和回答模板。"
    return "已通过。"


def _mean(values: Sequence[float] | Any) -> float:
    values = list(values)
    if not values:
        return 0.0
    return sum(values) / len(values)
