from generation_basics import GenerationDemoRetriever, MockLLMClient, RagService


QUESTIONS = [
    "退款规则是什么？",
    "为什么回答里要带来源标签？",
    "火星首都是什么？",
]


def main() -> None:
    service = RagService(
        retriever=GenerationDemoRetriever(),
        llm=MockLLMClient(),
        min_context_score=0.35,
    )

    for index, question in enumerate(QUESTIONS, start=1):
        if index > 1:
            print("-" * 80)
        result = service.ask(question)
        print(f"Question: {question}")
        print(f"Accepted sources: {len(result.sources)}")
        print(f"Answer: {result.answer}")


if __name__ == "__main__":
    main()
