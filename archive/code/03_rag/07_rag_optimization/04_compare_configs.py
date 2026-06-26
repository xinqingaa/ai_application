from __future__ import annotations

import argparse
import json
from pathlib import Path

from optimization_basics import (
    DEFAULT_EXPERIMENT_CONFIG_PATH,
    DEFAULT_GOLDEN_SET_PATH,
    DEFAULT_STORE_PATH,
    LLMRuntimeConfig,
    build_llm_client,
    compare_experiments,
    load_experiment_configs,
    load_golden_set,
)


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
    parser = argparse.ArgumentParser(description="比较第七章实验配置")
    parser.add_argument("--golden-set", default=str(DEFAULT_GOLDEN_SET_PATH))
    parser.add_argument("--config-path", default=str(DEFAULT_EXPERIMENT_CONFIG_PATH))
    parser.add_argument("--store-path", default=str(DEFAULT_STORE_PATH))
    parser.add_argument("--config", action="append", help="Optional config id filter, may repeat.")
    parser.add_argument("--llm-backend", choices=("policy_mock", "provider"), default="policy_mock")
    parser.add_argument("--provider", help="Provider key such as openai, bailian, deepseek, glm.")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=280)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--max-retries", type=int, default=0)
    args = parser.parse_args()

    cases = load_golden_set(Path(args.golden_set))
    experiments = load_experiment_configs(Path(args.config_path))
    if args.config:
        allowed = set(args.config)
        experiments = [item for item in experiments if item.config_id in allowed]
    llm_runtime = _build_llm_runtime(args)
    llm = build_llm_client(llm_runtime)

    print("LLM:")
    print(json.dumps(llm.describe(), ensure_ascii=False, indent=2))
    if llm_runtime.backend == "provider":
        print("Note: compare_experiments with a real provider will incur cost and may show nondeterministic differences.")
    print()

    rows = compare_experiments(
        cases,
        experiments,
        store_path=Path(args.store_path),
        llm_runtime=llm_runtime,
    )

    for index, row in enumerate(rows, start=1):
        print(
            f"{index}. {row.config_id} | score={row.composite_score:.3f} "
            f"pass={row.pass_rate:.3f} retrieval_recall={row.retrieval_recall:.3f} "
            f"answer_point={row.answer_point_recall:.3f} citation={row.citation_support_rate:.3f} "
            f"refusal={row.refusal_accuracy:.3f} prompt={row.prompt_variant} "
            f"strategy={row.retrieval_strategy}"
        )
        if row.notes:
            print(f"   notes={row.notes}")


if __name__ == "__main__":
    main()
