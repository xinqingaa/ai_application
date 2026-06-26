from __future__ import annotations

import argparse
import json
from pathlib import Path

from optimization_basics import (
    DEFAULT_EXPERIMENT_CONFIG_PATH,
    DEFAULT_GOLDEN_SET_PATH,
    DEFAULT_STORE_PATH,
    LLMRuntimeConfig,
    build_rag_service,
    evaluate_rag_cases,
    format_rag_report,
    load_experiment_configs,
    load_golden_set,
    resolve_prompt_variant,
)


def _select_config(config_id: str, config_path: Path):
    configs = load_experiment_configs(config_path)
    for config in configs:
        if config.config_id == config_id:
            return config
    raise ValueError(f"Unknown config id: {config_id}")


def _build_llm_runtime(args: argparse.Namespace) -> LLMRuntimeConfig:
    backend = args.llm_backend
    if args.provider:
        backend = "provider"
    return LLMRuntimeConfig(
        backend=backend,
        provider=args.provider,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        timeout=args.timeout,
        max_retries=args.max_retries,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="运行第七章生成评估")
    parser.add_argument("--config", default="baseline_similarity")
    parser.add_argument("--golden-set", default=str(DEFAULT_GOLDEN_SET_PATH))
    parser.add_argument("--config-path", default=str(DEFAULT_EXPERIMENT_CONFIG_PATH))
    parser.add_argument("--store-path", default=str(DEFAULT_STORE_PATH))
    parser.add_argument("--llm-backend", choices=("policy_mock", "provider"), default="policy_mock")
    parser.add_argument("--provider", help="Provider key such as openai, bailian, deepseek, glm.")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=280)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--max-retries", type=int, default=0)
    args = parser.parse_args()

    experiment = _select_config(args.config, Path(args.config_path))
    prompt_variant = resolve_prompt_variant(experiment.prompt_variant)
    cases = load_golden_set(Path(args.golden_set))
    llm_runtime = _build_llm_runtime(args)
    service, _, _ = build_rag_service(
        experiment,
        store_path=Path(args.store_path),
        llm_runtime=llm_runtime,
        reset_store=True,
    )
    report = evaluate_rag_cases(
        cases,
        service,
        top_k=experiment.retrieval.top_k,
    )

    print(f"Config: {experiment.config_id} | {experiment.label}")
    print(f"Prompt variant: {prompt_variant.key} | {prompt_variant.label}")
    print("LLM:")
    print(json.dumps(service.llm.describe(), ensure_ascii=False, indent=2))
    print(format_rag_report(report))
    print()

    for case in report.cases:
        print(f"- {case.case_id}: stage={case.failure_stage} passed={case.passed}")
        print(f"  answer={case.answer}")
        print(f"  sources={list(case.source_filenames)} labels={list(case.labels_in_answer)}")
        if case.missing_answer_points:
            print(f"  missing_answer_points={list(case.missing_answer_points)}")
        if case.missing_sources:
            print(f"  missing_sources={list(case.missing_sources)}")


if __name__ == "__main__":
    main()
