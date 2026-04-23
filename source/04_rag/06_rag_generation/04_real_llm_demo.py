import argparse
import json

from generation_basics import (
    Chapter5StrategyRetriever,
    RagService,
    context_relevance_score,
    create_generation_client,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Chapter 6 with a real OpenAI-compatible LLM or mock fallback.")
    parser.add_argument("question", nargs="?", default="购买后多久还能退款？")
    parser.add_argument("--provider", help="Provider key such as openai, bailian, deepseek, glm.")
    parser.add_argument("--backend", choices=("json", "chroma"), default="json")
    parser.add_argument("--strategy", choices=("similarity", "threshold", "mmr"), default="similarity")
    parser.add_argument("--top-k", type=int, default=4)
    parser.add_argument("--candidate-k", type=int, default=6)
    parser.add_argument("--threshold", type=float, default=0.80)
    parser.add_argument("--mmr-lambda", type=float, default=0.35)
    parser.add_argument("--filename", help="Optional filename filter from Chapter 5.")
    parser.add_argument("--min-context-score", "--min-score", dest="min_context_score", type=float, default=0.35)
    parser.add_argument("--max-chunks", type=int, default=3)
    parser.add_argument("--max-chars", type=int, default=120)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=280)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--reset", action="store_true", help="Reset Chapter 5 backend store before querying.")
    args = parser.parse_args()

    retriever = Chapter5StrategyRetriever(
        backend=args.backend,
        strategy_name=args.strategy,
        candidate_k=args.candidate_k,
        score_threshold=args.threshold,
        mmr_lambda=args.mmr_lambda,
        filename_filter=args.filename,
        reset_store=args.reset,
    )
    llm = create_generation_client(
        provider=args.provider,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        timeout=args.timeout,
    )
    service = RagService(
        retriever=retriever,
        llm=llm,
        min_context_score=args.min_context_score,
        max_chunks=args.max_chunks,
        max_chars_per_chunk=args.max_chars,
    )
    result = service.ask(args.question, top_k=args.top_k)

    print("LLM:")
    print(json.dumps(llm.describe(), ensure_ascii=False, indent=2))
    print()
    print(f"Question: {args.question}")
    print(f"Backend: {args.backend}")
    print(f"Strategy: {args.strategy}")
    if args.filename:
        print(f"Filename filter: {args.filename}")
    print(f"Retrieved: {len(service.last_retrieved_results)}")
    for item in service.last_retrieved_results:
        context_score = context_relevance_score(args.question, item.chunk.content)
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
