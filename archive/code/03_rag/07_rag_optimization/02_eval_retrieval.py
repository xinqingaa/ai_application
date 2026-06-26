from __future__ import annotations

import argparse
from pathlib import Path

from optimization_basics import (
    DEFAULT_EXPERIMENT_CONFIG_PATH,
    DEFAULT_GOLDEN_SET_PATH,
    DEFAULT_STORE_PATH,
    build_generation_smart_engine,
    evaluate_retrieval_from_golden_set,
    format_retrieval_report,
    load_experiment_configs,
    load_golden_set,
)


def _select_config(config_id: str, config_path: Path):
    configs = load_experiment_configs(config_path)
    for config in configs:
        if config.config_id == config_id:
            return config
    raise ValueError(f"Unknown config id: {config_id}")


def main() -> None:
    parser = argparse.ArgumentParser(description="运行第七章检索评估")
    parser.add_argument("--config", default="baseline_similarity")
    parser.add_argument("--golden-set", default=str(DEFAULT_GOLDEN_SET_PATH))
    parser.add_argument("--config-path", default=str(DEFAULT_EXPERIMENT_CONFIG_PATH))
    parser.add_argument("--store-path", default=str(DEFAULT_STORE_PATH))
    args = parser.parse_args()

    experiment = _select_config(args.config, Path(args.config_path))
    cases = load_golden_set(Path(args.golden_set))
    engine, _ = build_generation_smart_engine(
        store_path=Path(args.store_path),
        reset_store=True,
    )
    report = evaluate_retrieval_from_golden_set(cases, engine, experiment.retrieval)

    print(f"Config: {experiment.config_id} | {experiment.label}")
    print(
        f"Retrieval strategy: {experiment.retrieval.strategy} "
        f"top_k={experiment.retrieval.top_k} candidate_k={experiment.retrieval.candidate_k}"
    )
    print(format_retrieval_report(report))
    print()

    for case in report.cases:
        print(
            f"- {case.case_id}: recall={case.recall:.3f} "
            f"rr={case.reciprocal_rank:.3f} hit={case.hit_rate:.0f} "
            f"retrieved={list(case.retrieved_chunk_ids)}"
        )


if __name__ == "__main__":
    main()
