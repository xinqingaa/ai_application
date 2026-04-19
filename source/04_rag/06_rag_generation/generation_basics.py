from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Protocol


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
class SourceChunk:
    chunk_id: str
    document_id: str
    content: str
    metadata: dict[str, str | int | float | bool]


@dataclass(frozen=True)
class RetrievalResult:
    chunk: SourceChunk
    score: float


@dataclass(frozen=True)
class GenerationResult:
    content: str
    mocked: bool = True
    used_labels: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AnswerResult:
    answer: str
    sources: list[SourceChunk]


@dataclass(frozen=True)
class PromptInspection:
    retrieved_results: list[RetrievalResult]
    accepted_results: list[RetrievalResult]
    context: str
    messages: list[dict[str, str]]
    prompt_preview: str


class Retriever(Protocol):
    def retrieve(self, question: str, top_k: int = 3) -> list[RetrievalResult]:
        ...


def demo_source_chunks() -> list[SourceChunk]:
    return [
        SourceChunk(
            chunk_id="refund_policy:0",
            document_id="refund_policy",
            content="退款规则：购买后 7 天内且学习进度不超过 20%，可以申请全额退款。",
            metadata={
                "filename": "refund_policy.md",
                "source": "data/refund_policy.md",
                "chunk_index": 0,
            },
        ),
        SourceChunk(
            chunk_id="refund_process:0",
            document_id="refund_process",
            content="退款流程：在学习后台提交申请，审核通过后 3 到 5 个工作日原路退回。",
            metadata={
                "filename": "refund_process.md",
                "source": "data/refund_process.md",
                "chunk_index": 0,
            },
        ),
        SourceChunk(
            chunk_id="metadata_rules:0",
            document_id="metadata_rules",
            content="每个 chunk 应保留 source、filename 和 chunk_index，方便后续引用和调试。",
            metadata={
                "filename": "metadata_rules.md",
                "source": "data/metadata_rules.md",
                "chunk_index": 0,
            },
        ),
        SourceChunk(
            chunk_id="citation_rules:0",
            document_id="citation_rules",
            content="生成答案时应在关键结论后标注 [S1] 这样的来源标签，方便用户核对依据。",
            metadata={
                "filename": "citation_rules.md",
                "source": "data/citation_rules.md",
                "chunk_index": 0,
            },
        ),
        SourceChunk(
            chunk_id="prompt_boundary:0",
            document_id="prompt_boundary",
            content="RAG Prompt 必须要求模型只依据上下文回答，没依据时直接说我不知道。",
            metadata={
                "filename": "prompt_boundary.md",
                "source": "data/prompt_boundary.md",
                "chunk_index": 0,
            },
        ),
        SourceChunk(
            chunk_id="support_hours:0",
            document_id="support_hours",
            content="课程助教在工作日提供答疑支持，周末只处理紧急问题。",
            metadata={
                "filename": "support_hours.md",
                "source": "data/support_hours.md",
                "chunk_index": 0,
            },
        ),
    ]


class DemoRetriever:
    def __init__(self, chunks: list[SourceChunk] | None = None) -> None:
        self._chunks = chunks or demo_source_chunks()

    def retrieve(self, question: str, top_k: int = 3) -> list[RetrievalResult]:
        scored = [
            RetrievalResult(chunk=chunk, score=score_question_against_chunk(question, chunk.content))
            for chunk in self._chunks
        ]
        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:top_k]


class MockLLMClient:
    def generate(self, messages: list[dict[str, str]]) -> GenerationResult:
        user_content = messages[-1]["content"] if messages else ""
        question = _extract_section(user_content, "问题：", "回答要求：") or ""
        context = _extract_section(user_content, "上下文：", "问题：") or ""
        answer, labels = _build_mock_answer(question=question, context=context)
        return GenerationResult(content=answer, mocked=True, used_labels=labels)


@dataclass
class RagService:
    retriever: Retriever
    llm: MockLLMClient
    min_source_score: float = 0.35
    last_retrieved_results: list[RetrievalResult] = field(default_factory=list)
    last_accepted_results: list[RetrievalResult] = field(default_factory=list)
    last_messages: list[dict[str, str]] = field(default_factory=list)
    last_generation_result: GenerationResult | None = None

    def ask(self, question: str, top_k: int = 3) -> AnswerResult:
        retrieved = self.retriever.retrieve(question=question, top_k=top_k)
        accepted = filter_retrieval_results(retrieved, min_score=self.min_source_score)
        self.last_retrieved_results = retrieved
        self.last_accepted_results = accepted

        if not accepted:
            self.last_messages = []
            self.last_generation_result = None
            return AnswerResult(answer=NO_ANSWER_TEXT, sources=[])

        messages = build_messages(question=question, results=accepted)
        generation = self.llm.generate(messages)
        self.last_messages = messages
        self.last_generation_result = generation
        answer = generation.content.strip() or NO_ANSWER_TEXT
        return AnswerResult(answer=answer, sources=[item.chunk for item in accepted])


def score_question_against_chunk(question: str, chunk_content: str) -> float:
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


def filter_retrieval_results(
    results: list[RetrievalResult],
    min_score: float,
) -> list[RetrievalResult]:
    return [item for item in results if item.score >= min_score]


def format_context(
    results: list[RetrievalResult],
    max_chunks: int = 3,
    max_chars_per_chunk: int = 90,
) -> str:
    lines: list[str] = []
    for index, item in enumerate(results[:max_chunks], start=1):
        filename = item.chunk.metadata.get("filename", "unknown")
        chunk_index = item.chunk.metadata.get("chunk_index", "unknown")
        content = _truncate_content(item.chunk.content, max_chars_per_chunk)
        lines.append(
            f"[S{index}] filename={filename} chunk={chunk_index} score={item.score:.3f}\n{content}"
        )
    return "\n\n".join(lines)


def build_user_prompt(
    question: str,
    results: list[RetrievalResult],
    max_chunks: int = 3,
    max_chars_per_chunk: int = 90,
) -> str:
    context = format_context(
        results,
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
    top_k: int = 3,
    min_score: float = 0.35,
    max_chunks: int = 3,
    max_chars_per_chunk: int = 90,
) -> PromptInspection:
    retrieved = retriever.retrieve(question=question, top_k=top_k)
    accepted = filter_retrieval_results(retrieved, min_score=min_score)
    context = format_context(
        accepted,
        max_chunks=max_chunks,
        max_chars_per_chunk=max_chars_per_chunk,
    )
    messages = build_messages(
        question=question,
        results=accepted,
        max_chunks=max_chunks,
        max_chars_per_chunk=max_chars_per_chunk,
    )
    prompt_preview = build_prompt_preview(
        question=question,
        results=accepted,
        max_chunks=max_chunks,
        max_chars_per_chunk=max_chars_per_chunk,
    )
    return PromptInspection(
        retrieved_results=retrieved,
        accepted_results=accepted,
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
