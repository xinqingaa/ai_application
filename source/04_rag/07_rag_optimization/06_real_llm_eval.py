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
    load_experiment_configs,
    load_golden_set,
    resolve_prompt_variant,
)
from generation_basics import context_relevance_score


def _select_config(config_id: str, config_path: Path):
    configs = load_experiment_configs(config_path)
    for config in configs:
        if config.config_id == config_id:
            return config
    raise ValueError(f"Unknown config id: {config_id}")


def _select_case(case_id: str, golden_set_path: Path):
    cases = load_golden_set(golden_set_path)
    for case in cases:
        if case.case_id == case_id:
            return case
    raise ValueError(f"Unknown case id: {case_id}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Chapter 7 with a real OpenAI-compatible LLM or mock fallback."
    )
    parser.add_argument("--config", default="baseline_similarity")
    parser.add_argument("--case-id", default="citation_rules")
    parser.add_argument("--golden-set", default=str(DEFAULT_GOLDEN_SET_PATH))
    parser.add_argument("--config-path", default=str(DEFAULT_EXPERIMENT_CONFIG_PATH))
    parser.add_argument("--store-path", default=str(DEFAULT_STORE_PATH))
    parser.add_argument("--provider", help="Provider key such as openai, bailian, deepseek, glm.")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=280)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--max-retries", type=int, default=0)
    args = parser.parse_args()

    experiment = _select_config(args.config, Path(args.config_path))
    case = _select_case(args.case_id, Path(args.golden_set))
    prompt_variant = resolve_prompt_variant(experiment.prompt_variant)
    runtime = LLMRuntimeConfig(
        backend="provider",
        provider=args.provider,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        timeout=args.timeout,
        max_retries=args.max_retries,
    )
    service, _, _ = build_rag_service(
        experiment,
        store_path=Path(args.store_path),
        llm_runtime=runtime,
        reset_store=True,
    )
    result = service.ask(case.question, top_k=experiment.retrieval.top_k)

    print("LLM:")
    print(json.dumps(service.llm.describe(), ensure_ascii=False, indent=2))
    print()
    print(f"Config: {experiment.config_id} | {experiment.label}")
    print(f"Prompt variant: {prompt_variant.key} | {prompt_variant.label}")
    print(f"Case: {case.case_id}")
    print(f"Question: {case.question}")
    print(f"Expected sources: {list(case.expected_sources)}")
    print(f"Expected answer points: {list(case.expected_answer_points)}")
    print()
    print(f"Retrieved: {len(service.last_retrieved_results)}")
    for item in service.last_retrieved_results:
        context_score = context_relevance_score(case.question, item.chunk.content)
        print(
            f"- retrieval_score={item.score:.3f} "
            f"context_score={context_score:.3f} "
            f"filename={item.chunk.metadata['filename']} "
            f"chunk={item.chunk.metadata['chunk_index']}"
        )

    print()
    print(f"Accepted: {len(service.last_accepted_results)}")
    print(f"Prompt chunks: {len(service.last_prompt_results)}")

    if service.last_generation_result is not None:
        print()
        print("Generation:")
        print(
            json.dumps(
                {
                    "provider": service.last_generation_result.provider,
                    "model": service.last_generation_result.model,
                    "mocked": service.last_generation_result.mocked,
                    "finish_reason": service.last_generation_result.finish_reason,
                    "error": service.last_generation_result.error,
                    "usage": (
                        None
                        if service.last_generation_result.usage is None
                        else {
                            "prompt_tokens": service.last_generation_result.usage.prompt_tokens,
                            "completion_tokens": service.last_generation_result.usage.completion_tokens,
                            "total_tokens": service.last_generation_result.usage.total_tokens,
                        }
                    ),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        if service.last_generation_result.request_preview is not None:
            print()
            print("Request Preview:")
            print(json.dumps(service.last_generation_result.request_preview, ensure_ascii=False, indent=2))
        if service.last_generation_result.raw_response_preview is not None:
            print()
            print("Response Preview:")
            print(json.dumps(service.last_generation_result.raw_response_preview, ensure_ascii=False, indent=2))

    print()
    print("Answer:")
    print(result.answer)
    print()
    print("Sources:")
    if not result.sources:
        print("- none")
    for source in result.sources:
        print(
            f"- filename={source.metadata['filename']} "
            f"source={source.metadata['source']} "
            f"chunk={source.metadata['chunk_index']}"
        )


if __name__ == "__main__":
    main()
