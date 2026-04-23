from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
import sys
from typing import Any, Protocol


CHAPTER_ROOT = Path(__file__).resolve().parent
CHAPTER4_ROOT = CHAPTER_ROOT.parent / "04_vector_databases"
CHAPTER5_ROOT = CHAPTER_ROOT.parent / "05_retrieval_strategies"
DEFAULT_STORE_PATH = CHAPTER_ROOT / "store" / "demo_generation_store.json"

if str(CHAPTER4_ROOT) not in sys.path:
    sys.path.insert(0, str(CHAPTER4_ROOT))
if str(CHAPTER5_ROOT) not in sys.path:
    sys.path.insert(0, str(CHAPTER5_ROOT))

from langchain_adapter import langchain_vectorstore_is_available  # noqa: E402
from llm_utils import (  # noqa: E402
    GenerationProviderConfig,
    GenerationResult,
    LLMClient,
    OpenAICompatibleLLMClient,
    load_env_if_possible,
    load_generation_provider_config,
    missing_generation_fields,
)
from retrieval_basics import (  # noqa: E402
    EmbeddingProvider,
    LocalKeywordEmbeddingProvider,
    PersistentVectorStore,
    RetrievalResult,
    RetrievalStrategyConfig,
    SimpleRetriever,
    SourceChunk,
    VectorStoreConfig,
    build_demo_retriever,
    demo_chunk_metadata,
    embed_chunks,
)


NO_ANSWER_TEXT = "我不知道。当前检索到的内容不足以支持这个问题。"

RAG_SYSTEM_PROMPT = """
你是一个基于检索上下文回答问题的助手。
你只能依据提供的上下文回答，不要补充上下文之外的事实。
如果上下文没有足够依据，请明确回答“我不知道”。
回答要尽量简洁，并在关键结论后使用可见来源标签，例如 [S1]、[S2]。
""".strip()

RAG_USER_TEMPLATE = """
请仅依据下面的检索上下文回答问题。

上下文：
{context}

问题：
{question}

回答要求：
1. 先给出简洁结论，再补一句依据。
2. 如果上下文没有足够信息，直接回答“我不知道”，不要编造。
3. 如果使用了上下文，请在相关句子后标注来源标签，例如 [S1]。
""".strip()

TOKEN_PATTERN = re.compile(r"[a-z0-9]{3,}", re.IGNORECASE)
CONCEPT_GROUPS = [
    ("refund", ("退款", "退费", "refund")),
    ("policy", ("规则", "政策", "条件", "policy")),
    ("process", ("流程", "申请", "提交", "审核", "后台", "process")),
    ("metadata", ("metadata", "source", "filename", "chunk_index", "来源", "元数据")),
    ("citation", ("引用", "来源标签", "标签", "source label", "[s1]")),
    ("refusal", ("我不知道", "无答案", "没答案", "不足", "拒答")),
    ("prompt", ("prompt", "上下文", "context", "依据")),
    ("support", ("答疑", "助教", "support", "工作日")),
]


@dataclass(frozen=True)
class AnswerResult:
    answer: str
    sources: list[SourceChunk]


@dataclass(frozen=True)
class PromptInspection:
    retrieved_results: list[RetrievalResult]
    accepted_results: list[RetrievalResult]
    prompt_results: list[RetrievalResult]
    context_scores: dict[str, float]
    context: str
    messages: list[dict[str, str]]
    prompt_preview: str


class Retriever(Protocol):
    def retrieve(self, question: str, top_k: int = 5) -> list[RetrievalResult]:
        ...


def generation_demo_source_chunks() -> list[SourceChunk]:
    records = [
        (
            "refund_policy",
            "data/refund_policy.md",
            "退款规则：购买后 7 天内且学习进度不超过 20%，可以申请全额退款。",
        ),
        (
            "refund_process",
            "data/refund_process.md",
            "退款流程：在学习后台提交申请，审核通过后 3 到 5 个工作日原路退回。",
        ),
        (
            "metadata_rules",
            "data/metadata_rules.md",
            "每个 chunk 应保留 source、filename、suffix、char_start、char_end、chunk_chars 和 chunk_index，方便过滤、引用和调试。",
        ),
        (
            "citation_rules",
            "data/citation_rules.md",
            "回答里要带来源标签，例如 [S1]、[S2]，这样用户才能核对答案依据和引用位置。",
        ),
        (
            "prompt_boundary",
            "data/prompt_boundary.md",
            "RAG Prompt 必须要求模型只依据当前上下文回答；如果上下文没有足够依据，就直接回答我不知道。",
        ),
        (
            "support_hours",
            "data/support_hours.md",
            "课程助教在工作日提供答疑支持，周末只处理紧急问题。",
        ),
    ]

    chunks: list[SourceChunk] = []
    for document_id, source, content in records:
        chunks.append(
            SourceChunk(
                chunk_id=f"{document_id}:0",
                document_id=document_id,
                content=content,
                metadata=demo_chunk_metadata(source=source, content=content),
            )
        )
    return chunks


def build_generation_demo_store(
    provider: EmbeddingProvider | None = None,
    store_path: Path = DEFAULT_STORE_PATH,
    reset_store: bool = False,
) -> PersistentVectorStore:
    embedding_provider = provider or LocalKeywordEmbeddingProvider()
    store = PersistentVectorStore(VectorStoreConfig(store_path=store_path))
    if reset_store:
        store.reset()
    store.upsert(embed_chunks(generation_demo_source_chunks(), embedding_provider))
    return store


class GenerationDemoRetriever:
    def __init__(
        self,
        provider: EmbeddingProvider | None = None,
        store: PersistentVectorStore | None = None,
        store_path: Path = DEFAULT_STORE_PATH,
        reset_store: bool = True,
        filename_filter: str | None = None,
    ) -> None:
        self.provider = provider or LocalKeywordEmbeddingProvider()
        self.store = store or build_generation_demo_store(
            provider=self.provider,
            store_path=store_path,
            reset_store=reset_store,
        )
        self.retriever = SimpleRetriever(store=self.store, provider=self.provider)
        self.filename_filter = filename_filter

    def retrieve(self, question: str, top_k: int = 5) -> list[RetrievalResult]:
        strategy = RetrievalStrategyConfig(
            strategy_name="similarity",
            top_k=top_k,
            candidate_k=max(top_k, 6),
            filename_filter=self.filename_filter,
        )
        return self.retriever.retrieve(question=question, strategy=strategy)


# 兼容旧脚本和测试导入；教学文档改用 GenerationDemoRetriever 名称。
Chapter5DemoRetriever = GenerationDemoRetriever


@dataclass
class Chapter5StrategyRetriever:
    backend: str = "json"
    strategy_name: str = "similarity"
    provider: EmbeddingProvider | None = None
    candidate_k: int = 6
    score_threshold: float = 0.80
    mmr_lambda: float = 0.35
    filename_filter: str | None = None
    reset_store: bool = False

    def __post_init__(self) -> None:
        self.provider = self.provider or LocalKeywordEmbeddingProvider()
        self.retriever, self.store = build_demo_retriever(
            self.backend,
            provider=self.provider,
            reset_store=self.reset_store,
        )

    def retrieve(self, question: str, top_k: int = 5) -> list[RetrievalResult]:
        strategy = RetrievalStrategyConfig(
            strategy_name=self.strategy_name,
            top_k=top_k,
            candidate_k=max(top_k, self.candidate_k),
            score_threshold=self.score_threshold,
            mmr_lambda=self.mmr_lambda,
            filename_filter=self.filename_filter,
        )
        return self.retriever.retrieve(question, strategy)


@dataclass
class MockLLMClient:
    provider_name: str = "mock"
    model_name: str = "mock-rag-answer-v1"
    fallback_reason: str | None = None

    def describe(self) -> dict[str, Any]:
        return {
            "provider": self.provider_name,
            "model": self.model_name,
            "mocked": True,
            "ready": False,
            "error": self.fallback_reason,
        }

    def generate(self, messages: list[dict[str, str]]) -> GenerationResult:
        user_content = messages[-1]["content"] if messages else ""
        question = _extract_section(user_content, "问题：", "回答要求：") or ""
        context = _extract_section(user_content, "上下文：", "问题：") or ""
        answer, labels = _build_mock_answer(question=question, context=context)
        return GenerationResult(
            provider=self.provider_name,
            model=self.model_name,
            content=answer,
            finish_reason="mock_stop",
            request_preview={"messages": messages},
            raw_response_preview={"answer_preview": answer[:200]},
            mocked=True,
            error=self.fallback_reason,
            used_labels=labels,
        )


@dataclass
class ResilientGenerationClient:
    primary: LLMClient
    fallback_config: GenerationProviderConfig

    def describe(self) -> dict[str, Any]:
        description = dict(self.primary.describe())
        description["fallback_to_mock"] = True
        return description

    def generate(self, messages: list[dict[str, str]]) -> GenerationResult:
        try:
            return self.primary.generate(messages)
        except Exception as exc:
            fallback = MockLLMClient(
                provider_name=self.fallback_config.key,
                model_name=self.fallback_config.model,
                fallback_reason=f"{type(exc).__name__}: {exc}",
            )
            return fallback.generate(messages)


def create_generation_client(
    provider: str | None = None,
    *,
    temperature: float = 0.0,
    max_tokens: int = 280,
    timeout: float = 20.0,
    max_retries: int = 0,
) -> LLMClient:
    load_env_if_possible()
    config = load_generation_provider_config(
        provider,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    if not config.is_ready:
        missing = ",".join(missing_generation_fields(config))
        return MockLLMClient(
            provider_name=config.key,
            model_name=config.model,
            fallback_reason=f"missing_generation_env:{missing}",
        )
    primary = OpenAICompatibleLLMClient(
        config=config,
        timeout=timeout,
        max_retries=max_retries,
    )
    return ResilientGenerationClient(primary=primary, fallback_config=config)


@dataclass
class RagService:
    retriever: Retriever
    llm: LLMClient
    min_context_score: float = 0.35
    max_chunks: int = 3
    max_chars_per_chunk: int = 90
    last_retrieved_results: list[RetrievalResult] = field(default_factory=list)
    last_accepted_results: list[RetrievalResult] = field(default_factory=list)
    last_prompt_results: list[RetrievalResult] = field(default_factory=list)
    last_messages: list[dict[str, str]] = field(default_factory=list)
    last_generation_result: GenerationResult | None = None

    def ask(self, question: str, top_k: int = 5) -> AnswerResult:
        retrieved = self.retriever.retrieve(question=question, top_k=top_k)
        accepted = filter_retrieval_results(
            question=question,
            results=retrieved,
            min_context_score=self.min_context_score,
        )
        prompt_results = select_prompt_results(accepted, max_chunks=self.max_chunks)
        self.last_retrieved_results = retrieved
        self.last_accepted_results = accepted
        self.last_prompt_results = prompt_results

        if not prompt_results:
            self.last_messages = []
            self.last_generation_result = None
            return AnswerResult(answer=NO_ANSWER_TEXT, sources=[])

        messages = build_messages(
            question=question,
            results=prompt_results,
            max_chunks=self.max_chunks,
            max_chars_per_chunk=self.max_chars_per_chunk,
        )
        generation = self.llm.generate(messages)
        self.last_messages = messages
        self.last_generation_result = generation

        answer = generation.content.strip() or NO_ANSWER_TEXT
        if answer == NO_ANSWER_TEXT:
            return AnswerResult(answer=answer, sources=[])

        used_labels = generation.used_labels or extract_source_labels(answer)
        used_results = select_used_results(prompt_results, used_labels)
        return AnswerResult(answer=answer, sources=[item.chunk for item in used_results])


def context_relevance_score(question: str, chunk_content: str) -> float:
    question_text = _normalize(question)
    chunk_text = _normalize(chunk_content)
    if not question_text or not chunk_text:
        return 0.0

    active_groups = 0
    matched_groups = 0
    matched_keywords: set[str] = set()
    for _, keywords in CONCEPT_GROUPS:
        question_has = any(keyword in question_text for keyword in keywords)
        chunk_has = any(keyword in chunk_text for keyword in keywords)
        if question_has:
            active_groups += 1
            if chunk_has:
                matched_groups += 1
                for keyword in keywords:
                    if keyword in question_text and keyword in chunk_text:
                        matched_keywords.add(keyword)

    concept_score = matched_groups / active_groups if active_groups else 0.0
    lexical_score = _lexical_overlap(question_text, chunk_text)
    keyword_bonus = min(len(matched_keywords) * 0.08, 0.24)
    score = 0.55 * concept_score + 0.20 * lexical_score + keyword_bonus
    return round(min(score, 0.98), 3)


def score_question_against_chunk(question: str, chunk_content: str) -> float:
    return context_relevance_score(question, chunk_content)


def retrieval_context_scores(
    question: str,
    results: list[RetrievalResult],
) -> dict[str, float]:
    return {
        item.chunk.chunk_id: context_relevance_score(question, item.chunk.content)
        for item in results
    }


def filter_retrieval_results(
    question: str,
    results: list[RetrievalResult],
    min_context_score: float,
) -> list[RetrievalResult]:
    scores = retrieval_context_scores(question, results)
    return [
        item
        for item in results
        if scores.get(item.chunk.chunk_id, 0.0) >= min_context_score
    ]


def select_prompt_results(
    results: list[RetrievalResult],
    max_chunks: int,
) -> list[RetrievalResult]:
    return results[:max_chunks]


def select_used_results(
    prompt_results: list[RetrievalResult],
    used_labels: list[str],
) -> list[RetrievalResult]:
    label_to_result = {
        f"S{index}": item
        for index, item in enumerate(prompt_results, start=1)
    }
    selected = [label_to_result[label] for label in used_labels if label in label_to_result]
    return selected or prompt_results


def format_context(
    question: str,
    results: list[RetrievalResult],
    max_chunks: int = 3,
    max_chars_per_chunk: int = 90,
) -> str:
    lines: list[str] = []
    for index, item in enumerate(select_prompt_results(results, max_chunks=max_chunks), start=1):
        filename = item.chunk.metadata.get("filename", "unknown")
        chunk_index = item.chunk.metadata.get("chunk_index", "unknown")
        context_score = context_relevance_score(question, item.chunk.content)
        content = _truncate_content(item.chunk.content, max_chars_per_chunk)
        lines.append(
            (
                f"[S{index}] filename={filename} chunk={chunk_index} "
                f"retrieval_score={item.score:.3f} context_score={context_score:.3f}\n"
                f"{content}"
            )
        )
    return "\n\n".join(lines)


def build_user_prompt(
    question: str,
    results: list[RetrievalResult],
    max_chunks: int = 3,
    max_chars_per_chunk: int = 90,
) -> str:
    context = format_context(
        question=question,
        results=results,
        max_chunks=max_chunks,
        max_chars_per_chunk=max_chars_per_chunk,
    )
    return RAG_USER_TEMPLATE.format(context=context, question=question)


def build_messages(
    question: str,
    results: list[RetrievalResult],
    max_chunks: int = 3,
    max_chars_per_chunk: int = 90,
) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": RAG_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": build_user_prompt(
                question=question,
                results=results,
                max_chunks=max_chunks,
                max_chars_per_chunk=max_chars_per_chunk,
            ),
        },
    ]


def build_prompt_preview(
    question: str,
    results: list[RetrievalResult],
    max_chunks: int = 3,
    max_chars_per_chunk: int = 90,
) -> str:
    messages = build_messages(
        question=question,
        results=results,
        max_chunks=max_chunks,
        max_chars_per_chunk=max_chars_per_chunk,
    )
    return "\n\n".join(f"{message['role'].upper()}:\n{message['content']}" for message in messages)


def inspect_prompt(
    question: str,
    retriever: Retriever,
    top_k: int = 5,
    min_context_score: float = 0.35,
    max_chunks: int = 3,
    max_chars_per_chunk: int = 90,
) -> PromptInspection:
    retrieved = retriever.retrieve(question=question, top_k=top_k)
    accepted = filter_retrieval_results(
        question=question,
        results=retrieved,
        min_context_score=min_context_score,
    )
    prompt_results = select_prompt_results(accepted, max_chunks=max_chunks)
    scores = retrieval_context_scores(question, retrieved)
    context = format_context(
        question=question,
        results=prompt_results,
        max_chunks=max_chunks,
        max_chars_per_chunk=max_chars_per_chunk,
    )
    messages = build_messages(
        question=question,
        results=prompt_results,
        max_chunks=max_chunks,
        max_chars_per_chunk=max_chars_per_chunk,
    )
    prompt_preview = build_prompt_preview(
        question=question,
        results=prompt_results,
        max_chunks=max_chunks,
        max_chars_per_chunk=max_chars_per_chunk,
    )
    return PromptInspection(
        retrieved_results=retrieved,
        accepted_results=accepted,
        prompt_results=prompt_results,
        context_scores=scores,
        context=context,
        messages=messages,
        prompt_preview=prompt_preview,
    )


def extract_source_labels(text: str) -> list[str]:
    labels = re.findall(r"\[(S\d+)\]", text)
    seen: list[str] = []
    for label in labels:
        if label not in seen:
            seen.append(label)
    return seen


def lcel_runtime_is_available() -> bool:
    return langchain_vectorstore_is_available() or _langchain_core_is_available()


def _langchain_core_is_available() -> bool:
    try:
        import langchain_core  # noqa: F401
    except ImportError:
        return False
    return True


def _build_mock_answer(question: str, context: str) -> tuple[str, list[str]]:
    blocks = _parse_context_blocks(context)
    if not blocks:
        return NO_ANSWER_TEXT, []

    keywords = _question_keywords(question)
    candidates: list[tuple[int, str, str]] = []
    for label, content in blocks:
        for sentence in _split_sentences(content):
            overlap = sum(1 for keyword in keywords if keyword in _normalize(sentence))
            candidates.append((overlap, label, sentence))

    candidates.sort(key=lambda item: (item[0], len(item[2])), reverse=True)
    selected: list[tuple[str, str]] = []
    used_labels: list[str] = []
    for overlap, label, sentence in candidates:
        if overlap <= 0:
            continue
        if label not in used_labels:
            selected.append((label, sentence))
            used_labels.append(label)
        if len(selected) == 2:
            break

    if len(selected) < min(2, len(blocks)):
        for label, content in blocks[:2]:
            if label in used_labels:
                continue
            sentences = _split_sentences(content)
            if sentences:
                selected.append((label, sentences[0]))
                used_labels.append(label)
            if len(selected) == 2:
                break

    if not selected:
        for label, content in blocks[:2]:
            sentences = _split_sentences(content)
            if sentences:
                selected.append((label, sentences[0]))
                used_labels.append(label)
            if len(selected) == 2:
                break

    if not selected:
        return NO_ANSWER_TEXT, []

    if len(selected) == 1:
        label, sentence = selected[0]
        return f"根据检索到的内容，{sentence} [{label}]", [label]

    first_label, first_sentence = selected[0]
    second_label, second_sentence = selected[1]
    answer = (
        f"根据检索到的内容，{first_sentence} [{first_label}]；"
        f"补充信息：{second_sentence} [{second_label}]"
    )
    return answer, [first_label, second_label]


def _extract_section(text: str, start_marker: str, end_marker: str) -> str | None:
    start_index = text.find(start_marker)
    if start_index == -1:
        return None
    start_index += len(start_marker)
    end_index = text.find(end_marker, start_index)
    if end_index == -1:
        end_index = len(text)
    return text[start_index:end_index].strip()


def _parse_context_blocks(context: str) -> list[tuple[str, str]]:
    pattern = re.compile(r"(?ms)^\[(S\d+)\][^\n]*\n(.*?)(?=^\[S\d+\]|\Z)")
    return [(label, content.strip()) for label, content in pattern.findall(context)]


def _split_sentences(text: str) -> list[str]:
    return [item.strip() for item in re.split(r"(?<=[。！？.!?])\s+|\n+", text) if item.strip()]


def _question_keywords(question: str) -> list[str]:
    normalized = _normalize(question)
    keywords: list[str] = []
    for _, group_keywords in CONCEPT_GROUPS:
        for keyword in group_keywords:
            normalized_keyword = _normalize(keyword)
            if normalized_keyword and normalized_keyword in normalized and normalized_keyword not in keywords:
                keywords.append(normalized_keyword)
    for token in TOKEN_PATTERN.findall(normalized):
        if token not in keywords:
            keywords.append(token)
    return keywords


def _truncate_content(text: str, limit: int) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def _lexical_overlap(question_text: str, chunk_text: str) -> float:
    question_tokens = set(TOKEN_PATTERN.findall(question_text))
    if not question_tokens:
        return 0.0
    chunk_tokens = set(TOKEN_PATTERN.findall(chunk_text))
    overlap = question_tokens & chunk_tokens
    return len(overlap) / len(question_tokens)
