import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from optimization_basics import (
    DEFAULT_EXPERIMENT_CONFIG_PATH,
    DEFAULT_GOLDEN_SET_PATH,
    DEFAULT_STORE_PATH,
    LLMRuntimeConfig,
    build_rag_service,
    compare_experiments,
    evaluate_rag_cases,
    evaluate_retrieval_from_golden_set,
    load_experiment_configs,
    load_golden_set,
    summarize_golden_set,
)


class OptimizationTests(unittest.TestCase):
    def test_golden_set_summary(self) -> None:
        cases = load_golden_set(DEFAULT_GOLDEN_SET_PATH)

        summary = summarize_golden_set(cases)

        self.assertEqual(summary["total_cases"], 7)
        self.assertEqual(summary["retrieval_cases"], 6)
        self.assertEqual(summary["answerable_cases"], 6)
        self.assertEqual(summary["refusal_cases"], 1)

    def test_baseline_retrieval_metrics_are_non_zero(self) -> None:
        cases = load_golden_set(DEFAULT_GOLDEN_SET_PATH)
        experiment = next(
            item
            for item in load_experiment_configs(DEFAULT_EXPERIMENT_CONFIG_PATH)
            if item.config_id == "baseline_similarity"
        )
        service, engine, _ = build_rag_service(
            experiment,
            store_path=DEFAULT_STORE_PATH,
            reset_store=True,
        )

        retrieval_report = evaluate_retrieval_from_golden_set(cases, engine, experiment.retrieval)
        rag_report = evaluate_rag_cases(cases, service, top_k=experiment.retrieval.top_k)

        self.assertGreater(retrieval_report.recall, 0.0)
        self.assertGreater(retrieval_report.hit_rate, 0.0)
        self.assertGreater(rag_report.answer_point_recall, 0.0)
        self.assertGreater(rag_report.source_hit_rate, 0.0)

    def test_strict_prompt_beats_loose_prompt_on_citation_support(self) -> None:
        cases = load_golden_set(DEFAULT_GOLDEN_SET_PATH)
        experiments = load_experiment_configs(DEFAULT_EXPERIMENT_CONFIG_PATH)
        strict_experiment = next(item for item in experiments if item.config_id == "strict_threshold")
        loose_experiment = next(item for item in experiments if item.config_id == "loose_prompt_similarity")

        strict_service, _, _ = build_rag_service(
            strict_experiment,
            store_path=DEFAULT_STORE_PATH,
            reset_store=True,
        )
        loose_service, _, _ = build_rag_service(
            loose_experiment,
            store_path=DEFAULT_STORE_PATH,
            reset_store=False,
        )

        strict_report = evaluate_rag_cases(cases, strict_service, top_k=strict_experiment.retrieval.top_k)
        loose_report = evaluate_rag_cases(cases, loose_service, top_k=loose_experiment.retrieval.top_k)

        self.assertGreaterEqual(strict_report.citation_support_rate, loose_report.citation_support_rate)
        self.assertGreaterEqual(strict_report.refusal_accuracy, loose_report.refusal_accuracy)

    def test_compare_experiments_returns_ranked_rows(self) -> None:
        cases = load_golden_set(DEFAULT_GOLDEN_SET_PATH)
        experiments = load_experiment_configs(DEFAULT_EXPERIMENT_CONFIG_PATH)

        rows = compare_experiments(cases, experiments, store_path=DEFAULT_STORE_PATH)

        self.assertEqual(len(rows), len(experiments))
        self.assertGreaterEqual(rows[0].composite_score, rows[-1].composite_score)

    def test_provider_runtime_falls_back_to_mock_when_env_missing(self) -> None:
        experiment = next(
            item
            for item in load_experiment_configs(DEFAULT_EXPERIMENT_CONFIG_PATH)
            if item.config_id == "baseline_similarity"
        )

        with patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "",
                "OPENAI_BASE_URL": "",
                "OPENAI_MODEL": "",
            },
            clear=False,
        ):
            service, _, _ = build_rag_service(
                experiment,
                store_path=DEFAULT_STORE_PATH,
                llm_runtime=LLMRuntimeConfig(backend="provider", provider="openai"),
                reset_store=True,
            )
            result = service.ask("为什么回答里要带来源标签？", top_k=experiment.retrieval.top_k)

        self.assertIn("来源标签", result.answer)
        self.assertIsNotNone(service.last_generation_result)
        self.assertTrue(service.last_generation_result.mocked)
        self.assertEqual(service.last_generation_result.provider, "openai")


if __name__ == "__main__":
    unittest.main()
