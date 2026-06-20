import argparse
import json

from generation_basics import (
    NO_ANSWER_TEXT,
    RAG_SYSTEM_PROMPT,
    RAG_USER_TEMPLATE,
    Chapter5StrategyRetriever,
    create_generation_client,
    inspect_prompt,
    lcel_runtime_is_available,
)


def _langchain_messages_to_dicts(messages) -> list[dict[str, str]]:
    role_map = {
        "system": "system",
        "human": "user",
        "ai": "assistant",
    }
    converted: list[dict[str, str]] = []
    for message in messages:
        converted.append(
            {
                "role": role_map.get(message.type, message.type),
                "content": message.content,
            }
        )
    return converted


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a minimal LCEL RAG chain for Chapter 6.")
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

    if not lcel_runtime_is_available():
        print("LCEL demo requires langchain-core. Run `python -m pip install -r requirements.txt` in this chapter directory.")
        return

    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.runnables import RunnableLambda, RunnablePassthrough

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
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", RAG_SYSTEM_PROMPT),
            ("user", RAG_USER_TEMPLATE),
        ]
    )
    inspection_cache: dict[str, object] = {}

    def retrieve_context(question: str) -> str:
        inspection = inspect_prompt(
            question=question,
            retriever=retriever,
            top_k=args.top_k,
            min_context_score=args.min_context_score,
            max_chunks=args.max_chunks,
            max_chars_per_chunk=args.max_chars,
        )
        inspection_cache[question] = inspection
        return inspection.context

    def call_generation(prompt_value) -> str:
        messages = _langchain_messages_to_dicts(prompt_value.to_messages())
        result = llm.generate(messages)
        return result.content.strip() or NO_ANSWER_TEXT

    rag_chain = (
        {
            "context": RunnableLambda(retrieve_context),
            "question": RunnablePassthrough(),
        }
        | prompt
        | RunnableLambda(call_generation)
        | StrOutputParser()
    )

    inspection = inspect_prompt(
        question=args.question,
        retriever=retriever,
        top_k=args.top_k,
        min_context_score=args.min_context_score,
        max_chunks=args.max_chunks,
        max_chars_per_chunk=args.max_chars,
    )
    inspection_cache[args.question] = inspection
    answer = NO_ANSWER_TEXT if not inspection.prompt_results else rag_chain.invoke(args.question)

    print("LCEL Chain:")
    print("retriever -> context -> ChatPromptTemplate -> LLMClient -> StrOutputParser")
    print()
    print("LLM:")
    print(json.dumps(llm.describe(), ensure_ascii=False, indent=2))
    print()
    print(f"Question: {args.question}")
    print(f"Backend: {args.backend}")
    print(f"Strategy: {args.strategy}")
    print()
    print("Context:")
    print(inspection.context or "（无可用上下文）")
    print()
    print("Prompt Preview:")
    print(inspection.prompt_preview)
    print()
    print("Answer:")
    print(answer)
    print()
    print("Prompt Sources:")
    if not inspection.prompt_results:
        print("- none")
    for item in inspection.prompt_results:
        print(
            f"- filename={item.chunk.metadata['filename']} "
            f"source={item.chunk.metadata['source']} "
            f"chunk={item.chunk.metadata['chunk_index']}"
        )


if __name__ == "__main__":
    main()
