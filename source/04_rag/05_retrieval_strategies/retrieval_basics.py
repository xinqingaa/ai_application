from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import math
import re
import sys
from typing import Literal


CHAPTER_ROOT = Path(__file__).resolve().parent
CHAPTER4_ROOT = CHAPTER_ROOT.parent / "04_vector_databases"
DEFAULT_JSON_STORE_PATH = CHAPTER_ROOT / "store" / "demo_retrieval_store.json"
DEFAULT_CHROMA_DIR = CHAPTER_ROOT / "store" / "chroma"
DEFAULT_BAD_CASES_PATH = CHAPTER_ROOT / "evals" / "retrieval_bad_cases.json"
DEFAULT_TOP_K = 3
DEFAULT_CANDIDATE_K = 4
DEFAULT_SCORE_THRESHOLD = 0.80
DEFAULT_MMR_LAMBDA = 0.35
DEFAULT_HYBRID_ALPHA = 0.5
SUPPORTED_STRATEGIES = {"similarity", "threshold", "mmr", "hybrid"}
SUPPORTED_BACKENDS = ("json", "chroma")

if str(CHAPTER4_ROOT) not in sys.path:
    sys.path.insert(0, str(CHAPTER4_ROOT))

from chroma_store import (  # noqa: E402
    ChromaVectorStore,
    ChromaVectorStoreConfig,
    chromadb_is_available,
)
from vector_store_basics import (  # noqa: E402
    EmbeddedChunk,
    EmbeddingProvider,
    LocalKeywordEmbeddingProvider,
    PersistentVectorStore,
    RetrievalResult,
    SourceChunk,
    VectorStoreConfig,
    cosine_similarity,
    demo_chunk_metadata,
    embed_chunks,
    embedding_space_from_provider,
    ensure_same_embedding_space,
    ensure_vector_dimensions,
)

BackendName = Literal["json", "chroma"]


@dataclass(frozen=True)
class RetrievalStrategyConfig:
    strategy_name: str
    top_k: int = DEFAULT_TOP_K
    candidate_k: int = DEFAULT_CANDIDATE_K
    score_threshold: float = DEFAULT_SCORE_THRESHOLD
    mmr_lambda: float = DEFAULT_MMR_LAMBDA
    filename_filter: str | None = None

    def __post_init__(self) -> None:
        if self.strategy_name not in SUPPORTED_STRATEGIES:
            raise ValueError(f"Unsupported strategy: {self.strategy_name}")
        if self.top_k <= 0:
            raise ValueError("top_k must be positive.")
        if self.candidate_k < self.top_k:
            raise ValueError("candidate_k must be greater than or equal to top_k.")
        if not 0.0 <= self.score_threshold <= 1.0:
            raise ValueError("score_threshold must be between 0.0 and 1.0.")
        if not 0.0 <= self.mmr_lambda <= 1.0:
            raise ValueError("mmr_lambda must be between 0.0 and 1.0.")


@dataclass(frozen=True)
class SearchHit:
    embedded_chunk: EmbeddedChunk
    similarity_score: float


@dataclass(frozen=True)
class BadCaseEvaluation:
    strategy_name: str
    status: str
    messages: tuple[str, ...]


def demo_source_chunks() -> list[SourceChunk]:
    refund_policy = "退款规则：购买后 7 天内且学习进度不超过 20%，可以申请全额退款。"
    refund_summary = "退款政策摘要：7 天内且学习进度不超过 20%，支持全额退费。"
    refund_duplicate = "退款说明：购买后 7 天内且学习进度不超过 20%，支持全额退款。"
    refund_process = "退费申请流程：在学习后台提交退款申请，审核通过后原路退回。"
    trial_policy = "课程支持一次 30 分钟免费试学，需要提前预约。"
    metadata_rules = (
        "每个 chunk 应保留 source、filename、suffix、char_start、char_end 和 "
        "chunk_chars，方便过滤、引用和调试。"
    )
    support_hours = "课程助教在工作日提供答疑支持，周末只处理紧急问题。"
    embedding_notes = "Embedding 会把文本映射成向量，检索时通过相似度找到相关 chunk。"

    return [
        SourceChunk(
            chunk_id="refund_policy:0",
            document_id="refund_policy",
            content=refund_policy,
            metadata=demo_chunk_metadata("data/refund_policy.md", refund_policy),
        ),
        SourceChunk(
            chunk_id="refund_summary:0",
            document_id="refund_summary",
            content=refund_summary,
            metadata=demo_chunk_metadata("data/refund_summary.md", refund_summary),
        ),
        SourceChunk(
            chunk_id="refund_duplicate:0",
            document_id="refund_duplicate",
            content=refund_duplicate,
            metadata=demo_chunk_metadata("data/refund_duplicate.md", refund_duplicate),
        ),
        SourceChunk(
            chunk_id="refund_process:0",
            document_id="refund_process",
            content=refund_process,
            metadata=demo_chunk_metadata("data/refund_process.md", refund_process),
        ),
        SourceChunk(
            chunk_id="trial:0",
            document_id="trial",
            content=trial_policy,
            metadata=demo_chunk_metadata("data/trial_policy.md", trial_policy),
        ),
        SourceChunk(
            chunk_id="metadata:0",
            document_id="metadata",
            content=metadata_rules,
            metadata=demo_chunk_metadata("data/metadata_rules.md", metadata_rules),
        ),
        SourceChunk(
            chunk_id="support:0",
            document_id="support",
            content=support_hours,
            metadata=demo_chunk_metadata("data/support_hours.md", support_hours),
        ),
        SourceChunk(
            chunk_id="embedding:0",
            document_id="embedding",
            content=embedding_notes,
            metadata=demo_chunk_metadata("data/embedding_notes.md", embedding_notes),
        ),
    ]


def demo_embedded_chunks(
    provider: EmbeddingProvider | None = None,
) -> list[EmbeddedChunk]:
    embedding_provider = provider or LocalKeywordEmbeddingProvider()
    return embed_chunks(demo_source_chunks(), embedding_provider)


def index_demo_chunks(
    store: PersistentVectorStore,
    provider: EmbeddingProvider,
    reset_store: bool = False,
) -> int:
    expected_space = embedding_space_from_provider(provider)
    expected_doc_ids = {chunk.document_id for chunk in demo_source_chunks()}
    should_reset = reset_store

    if not should_reset:
        try:
            current_space = store.embedding_space()
            current_doc_ids = set(store.list_document_ids())
        except ValueError:
            should_reset = True
        else:
            if current_space is not None and current_space != expected_space:
                should_reset = True
            if current_doc_ids and current_doc_ids != expected_doc_ids:
                should_reset = True

    if should_reset:
        store.reset()

    return store.replace_document(demo_embedded_chunks(provider))


def build_demo_json_store(
    provider: EmbeddingProvider | None = None,
    store_path: Path = DEFAULT_JSON_STORE_PATH,
    reset_store: bool = False,
) -> PersistentVectorStore:
    embedding_provider = provider or LocalKeywordEmbeddingProvider()
    store = PersistentVectorStore(VectorStoreConfig(store_path=store_path))
    index_demo_chunks(store, embedding_provider, reset_store=reset_store)
    return store


def build_demo_store(
    provider: EmbeddingProvider | None = None,
    store_path: Path = DEFAULT_JSON_STORE_PATH,
    reset_store: bool = False,
) -> PersistentVectorStore:
    return build_demo_json_store(
        provider=provider,
        store_path=store_path,
        reset_store=reset_store,
    )


def index_demo_chroma_chunks(
    store: ChromaVectorStore,
    provider: EmbeddingProvider,
    reset_store: bool = False,
) -> int:
    expected_space = embedding_space_from_provider(provider)
    expected_doc_ids = {chunk.document_id for chunk in demo_source_chunks()}
    should_reset = reset_store

    if not should_reset:
        try:
            current_space = store.embedding_space()
            current_doc_ids = set(store.list_document_ids())
        except ValueError:
            should_reset = True
        else:
            if current_space is not None and current_space != expected_space:
                should_reset = True
            if current_doc_ids and current_doc_ids != expected_doc_ids:
                should_reset = True

    if should_reset:
        store.reset()

    return store.replace_document(demo_embedded_chunks(provider))


def build_demo_chroma_store(
    provider: EmbeddingProvider | None = None,
    persist_directory: Path = DEFAULT_CHROMA_DIR,
    collection_name: str = "chapter5_retrieval_chunks",
    reset_store: bool = False,
) -> ChromaVectorStore:
    if not chromadb_is_available():
        raise RuntimeError(
            "Real Chroma support requires the `chromadb` package. "
            "Run `python -m pip install -r requirements.txt` in this chapter directory."
        )

    embedding_provider = provider or LocalKeywordEmbeddingProvider()
    store = ChromaVectorStore(
        ChromaVectorStoreConfig(
            persist_directory=persist_directory,
            collection_name=collection_name,
        )
    )
    index_demo_chroma_chunks(store, embedding_provider, reset_store=reset_store)
    return store


def build_demo_retriever(
    backend: BackendName,
    provider: EmbeddingProvider | None = None,
    *,
    reset_store: bool = False,
    json_store_path: Path = DEFAULT_JSON_STORE_PATH,
    chroma_persist_directory: Path = DEFAULT_CHROMA_DIR,
):
    embedding_provider = provider or LocalKeywordEmbeddingProvider()
    if backend == "json":
        store = build_demo_json_store(
            provider=embedding_provider,
            store_path=json_store_path,
            reset_store=reset_store,
        )
        return SimpleRetriever(store=store, provider=embedding_provider), store

    if backend == "chroma":
        from chroma_retriever import ChromaRetriever

        store = build_demo_chroma_store(
            provider=embedding_provider,
            persist_directory=chroma_persist_directory,
            reset_store=reset_store,
        )
        return ChromaRetriever(store=store, provider=embedding_provider), store

    raise ValueError(f"Unsupported backend: {backend}")


def strategy_from_case(
    case: dict[str, object],
    strategy_name: str,
) -> RetrievalStrategyConfig:
    values: dict[str, object] = {
        "strategy_name": strategy_name,
        "top_k": DEFAULT_TOP_K,
        "candidate_k": DEFAULT_CANDIDATE_K,
        "score_threshold": DEFAULT_SCORE_THRESHOLD,
        "mmr_lambda": DEFAULT_MMR_LAMBDA,
        "filename_filter": case.get("filename_filter"),
    }

    strategy_configs = case.get("strategy_configs")
    if isinstance(strategy_configs, dict):
        overrides = strategy_configs.get(strategy_name)
        if isinstance(overrides, dict):
            for key in (
                "top_k",
                "candidate_k",
                "score_threshold",
                "mmr_lambda",
                "filename_filter",
            ):
                if key in overrides:
                    values[key] = overrides[key]

    filename_filter = values["filename_filter"]
    return RetrievalStrategyConfig(
        strategy_name=str(values["strategy_name"]),
        top_k=int(values["top_k"]),
        candidate_k=int(values["candidate_k"]),
        score_threshold=float(values["score_threshold"]),
        mmr_lambda=float(values["mmr_lambda"]),
        filename_filter=str(filename_filter) if filename_filter else None,
    )


def select_search_hits(
    query_vector: list[float],
    candidates: list[SearchHit],
    strategy: RetrievalStrategyConfig,
) -> list[SearchHit]:
    if strategy.strategy_name == "similarity":
        return candidates[: strategy.top_k]

    if strategy.strategy_name == "threshold":
        return [
            item for item in candidates if item.similarity_score >= strategy.score_threshold
        ][: strategy.top_k]

    if strategy.strategy_name == "mmr":
        return maximal_marginal_relevance(
            query_vector=query_vector,
            candidates=candidates,
            top_k=strategy.top_k,
            lambda_mult=strategy.mmr_lambda,
        )

    raise ValueError(f"Unsupported strategy: {strategy.strategy_name}")


def hits_to_results(hits: list[SearchHit]) -> list[RetrievalResult]:
    return [
        RetrievalResult(chunk=item.embedded_chunk.chunk, score=item.similarity_score)
        for item in hits
    ]


class SimpleRetriever:
    def __init__(
        self,
        store: PersistentVectorStore,
        provider: EmbeddingProvider,
    ) -> None:
        self.store = store
        self.provider = provider

    def retrieve(
        self,
        question: str,
        strategy: RetrievalStrategyConfig,
    ) -> list[RetrievalResult]:
        query_vector = self.provider.embed_query(question)
        candidates = self._search_candidates(
            query_vector=query_vector,
            candidate_k=strategy.candidate_k,
            filename_filter=strategy.filename_filter,
        )
        return hits_to_results(select_search_hits(query_vector, candidates, strategy))

    def _search_candidates(
        self,
        query_vector: list[float],
        candidate_k: int,
        filename_filter: str | None = None,
    ) -> list[SearchHit]:
        ensure_vector_dimensions(query_vector, self.provider.dimensions, context="query vector")
        embedded_chunks = self.store.load_chunks()
        for chunk in embedded_chunks:
            ensure_same_embedding_space(chunk, self.provider)

        if filename_filter is not None:
            embedded_chunks = [
                chunk
                for chunk in embedded_chunks
                if chunk.chunk.metadata.get("filename") == filename_filter
            ]

        hits = [
            SearchHit(
                embedded_chunk=chunk,
                similarity_score=cosine_similarity(query_vector, chunk.vector),
            )
            for chunk in embedded_chunks
        ]
        hits.sort(key=lambda item: item.similarity_score, reverse=True)
        return hits[:candidate_k]


def maximal_marginal_relevance(
    query_vector: list[float],
    candidates: list[SearchHit],
    top_k: int,
    lambda_mult: float,
) -> list[SearchHit]:
    if not candidates:
        return []

    remaining = candidates[:]
    selected: list[SearchHit] = []

    while remaining and len(selected) < top_k:
        if not selected:
            selected.append(remaining.pop(0))
            continue

        best_index = 0
        best_score = float("-inf")
        for index, candidate in enumerate(remaining):
            redundancy = max(
                cosine_similarity(candidate.embedded_chunk.vector, chosen.embedded_chunk.vector)
                for chosen in selected
            )
            mmr_score = (
                lambda_mult * candidate.similarity_score
                - (1.0 - lambda_mult) * redundancy
            )
            if mmr_score > best_score:
                best_score = mmr_score
                best_index = index

        selected.append(remaining.pop(best_index))

    return selected


def average_redundancy(
    results: list[RetrievalResult],
    provider: EmbeddingProvider,
) -> float:
    if len(results) < 2:
        return 0.0

    embedded = provider.embed_documents([result.chunk.content for result in results])
    pair_scores: list[float] = []
    for index, left in enumerate(embedded):
        for right in embedded[index + 1 :]:
            pair_scores.append(cosine_similarity(left, right))
    return sum(pair_scores) / len(pair_scores)


def load_bad_cases(path: Path = DEFAULT_BAD_CASES_PATH) -> list[dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Bad cases payload must be a list.")
    return [dict(case) for case in payload]


def evaluate_bad_case(
    case: dict[str, object],
    strategy_name: str,
    results: list[RetrievalResult],
    provider: EmbeddingProvider,
) -> BadCaseEvaluation:
    expectations = case.get("expectations")
    if not isinstance(expectations, dict):
        return BadCaseEvaluation(
            strategy_name=strategy_name,
            status="info",
            messages=("no machine-checkable expectations",),
        )

    strategy_expectation = expectations.get(strategy_name)
    if not isinstance(strategy_expectation, dict):
        return BadCaseEvaluation(
            strategy_name=strategy_name,
            status="info",
            messages=("no machine-checkable expectations for this strategy",),
        )

    observed_messages = [
        f"top={results[0].chunk.chunk_id if results else 'none'}",
        f"count={len(results)}",
        f"redundancy={average_redundancy(results, provider):.3f}",
    ]
    failures: list[str] = []

    expected_top_chunk = strategy_expectation.get("top_chunk_id")
    if expected_top_chunk is not None:
        top_chunk = results[0].chunk.chunk_id if results else "none"
        if top_chunk != expected_top_chunk:
            failures.append(
                f"expected top_chunk_id={expected_top_chunk}, got {top_chunk}"
            )

    expected_count = strategy_expectation.get("count")
    if expected_count is not None:
        if not isinstance(expected_count, int) or isinstance(expected_count, bool):
            raise ValueError("Bad case expectation count must be an integer.")
        if len(results) != expected_count:
            failures.append(f"expected count={expected_count}, got {len(results)}")

    expected_empty = strategy_expectation.get("empty")
    if expected_empty is not None:
        if not isinstance(expected_empty, bool):
            raise ValueError("Bad case expectation empty must be a boolean.")
        if expected_empty and results:
            failures.append("expected no results, but retriever returned hits")
        if not expected_empty and not results:
            failures.append("expected non-empty results, but retriever returned none")

    expected_filename = strategy_expectation.get("filename")
    if expected_filename is not None:
        filenames = {result.chunk.metadata.get("filename") for result in results}
        if filenames != {expected_filename}:
            failures.append(
                f"expected all filenames={expected_filename}, got {sorted(filenames)}"
            )

    required_chunk_ids = strategy_expectation.get("must_include_chunk_ids")
    if required_chunk_ids is not None:
        if not isinstance(required_chunk_ids, list):
            raise ValueError("Bad case expectation must_include_chunk_ids must be a list.")
        actual_chunk_ids = {result.chunk.chunk_id for result in results}
        missing = [
            str(chunk_id)
            for chunk_id in required_chunk_ids
            if str(chunk_id) not in actual_chunk_ids
        ]
        if missing:
            failures.append(f"missing required chunk ids: {missing}")

    max_redundancy = strategy_expectation.get("max_redundancy")
    if max_redundancy is not None:
        if not isinstance(max_redundancy, (int, float)) or isinstance(max_redundancy, bool):
            raise ValueError("Bad case expectation max_redundancy must be numeric.")
        redundancy = average_redundancy(results, provider)
        if redundancy > float(max_redundancy):
            failures.append(
                f"expected redundancy <= {float(max_redundancy):.3f}, got {redundancy:.3f}"
            )

    if failures:
        return BadCaseEvaluation(
            strategy_name=strategy_name,
            status="fail",
            messages=tuple(observed_messages + failures),
        )

    return BadCaseEvaluation(
        strategy_name=strategy_name,
        status="pass",
        messages=tuple(observed_messages),
    )


# ---------------------------------------------------------------------------
# BM25 scorer — 最小自实现，不依赖外部库
# ---------------------------------------------------------------------------
# 教学目标：让学员看清 TF-IDF + 文档长度归一化在做什么。
# 生产环境应使用 jieba 分词 + rank_bm25 或 Elasticsearch BM25。
# 这里用字符 bigram + 单字作为 tokenizer，对中文短文本 demo 语料够用。
# ---------------------------------------------------------------------------

_PUNCTUATION = re.compile(r"[\s\u3000-\u303f\uff00-\uffef，。！？、；：""''（）【】]+")


def _simple_tokenize(text: str) -> list[str]:
    """字符 bigram + 单字 tokenizer，适用于中文短文本 demo。

    不引入 jieba 或其他分词库，保持零额外依赖。
    """
    cleaned = _PUNCTUATION.sub("", text.lower())
    tokens: list[str] = list(cleaned)  # 单字
    for i in range(len(cleaned) - 1):  # bigram
        tokens.append(cleaned[i : i + 2])
    return tokens


class SimpleBM25Scorer:
    """最小 BM25 实现，只服务于教学。

    标准 BM25 公式:
      score(q, d) = Σ IDF(t) * (tf(t,d) * (k1 + 1)) / (tf(t,d) + k1 * (1 - b + b * |d| / avgdl))

    其中:
      - IDF(t) = log((N - df(t) + 0.5) / (df(t) + 0.5) + 1)
      - tf(t, d) = term frequency of t in document d
      - |d| = document length in tokens
      - avgdl = average document length
      - k1, b = tuning parameters (defaults: 1.5, 0.75)
    """

    def __init__(
        self,
        corpus: list[SourceChunk],
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        self.corpus = corpus
        self.k1 = k1
        self.b = b

        self._doc_tokens: list[list[str]] = [
            _simple_tokenize(chunk.content) for chunk in corpus
        ]
        self._doc_lens = [len(tokens) for tokens in self._doc_tokens]
        self._avgdl = sum(self._doc_lens) / max(len(self._doc_lens), 1)
        self._n = len(corpus)

        # document frequency: term -> number of documents containing it
        self._df: dict[str, int] = {}
        for tokens in self._doc_tokens:
            for term in set(tokens):
                self._df[term] = self._df.get(term, 0) + 1

    def _idf(self, term: str) -> float:
        df = self._df.get(term, 0)
        return math.log((self._n - df + 0.5) / (df + 0.5) + 1.0)

    def score(self, query: str) -> list[tuple[SourceChunk, float]]:
        """返回 (chunk, bm25_score) 列表，按 score 降序排列。"""
        query_tokens = _simple_tokenize(query)
        scores: list[tuple[SourceChunk, float]] = []

        for idx, chunk in enumerate(self.corpus):
            doc_tokens = self._doc_tokens[idx]
            doc_len = self._doc_lens[idx]
            tf_map: dict[str, int] = {}
            for t in doc_tokens:
                tf_map[t] = tf_map.get(t, 0) + 1

            total = 0.0
            for qt in query_tokens:
                tf = tf_map.get(qt, 0)
                if tf == 0:
                    continue
                idf = self._idf(qt)
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self._avgdl)
                total += idf * numerator / denominator

            scores.append((chunk, total))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores


# ---------------------------------------------------------------------------
# 混合检索 — 向量 + BM25 加权融合
# ---------------------------------------------------------------------------


def _min_max_normalize(scores: list[float]) -> list[float]:
    """将分数归一化到 [0, 1] 区间。"""
    if not scores:
        return []
    lo, hi = min(scores), max(scores)
    span = hi - lo
    if span == 0:
        return [1.0] * len(scores)
    return [(s - lo) / span for s in scores]


def hybrid_search(
    query: str,
    vector_results: list[RetrievalResult],
    bm25_scorer: SimpleBM25Scorer,
    alpha: float = DEFAULT_HYBRID_ALPHA,
    top_k: int = DEFAULT_TOP_K,
) -> list[RetrievalResult]:
    """向量分数 + BM25 分数加权融合。

    hybrid_score = alpha * norm(vector_score) + (1 - alpha) * norm(bm25_score)

    alpha 越大越偏向语义相似度，越小越偏向关键词匹配。
    """
    bm25_all = bm25_scorer.score(query)
    bm25_by_id: dict[str, float] = {chunk.chunk_id: score for chunk, score in bm25_all}

    # 收集所有出现过的 chunk（两路取并集）
    chunk_by_id: dict[str, SourceChunk] = {}
    vector_by_id: dict[str, float] = {}
    for result in vector_results:
        chunk_by_id[result.chunk.chunk_id] = result.chunk
        vector_by_id[result.chunk.chunk_id] = result.score
    for chunk, _ in bm25_all:
        chunk_by_id.setdefault(chunk.chunk_id, chunk)

    all_ids = list(chunk_by_id.keys())

    raw_vector = [vector_by_id.get(cid, 0.0) for cid in all_ids]
    raw_bm25 = [bm25_by_id.get(cid, 0.0) for cid in all_ids]

    norm_vector = _min_max_normalize(raw_vector)
    norm_bm25 = _min_max_normalize(raw_bm25)

    combined: list[tuple[str, float]] = []
    for i, cid in enumerate(all_ids):
        hybrid_score = alpha * norm_vector[i] + (1 - alpha) * norm_bm25[i]
        combined.append((cid, hybrid_score))
    combined.sort(key=lambda x: x[1], reverse=True)

    return [
        RetrievalResult(chunk=chunk_by_id[cid], score=score)
        for cid, score in combined[:top_k]
    ]


# ---------------------------------------------------------------------------
# 两阶段检索 — toy Reranker
# ---------------------------------------------------------------------------
# 教学目标：看清"先粗筛再精排"的两阶段架构。
# 真实 Reranker 使用 cross-encoder 模型（如 Cohere Rerank、BGE Reranker），
# 效果远强于关键词匹配，但原理相同：对 query-document pair 重新打分。
# ---------------------------------------------------------------------------


class SimpleCrossReranker:
    """最小关键词交叉打分 reranker，只用于教学演示。

    对每个 candidate 计算 query 和 document 之间的词级 F1：
      precision = |query_tokens ∩ doc_tokens| / |query_tokens|
      recall    = |query_tokens ∩ doc_tokens| / |doc_tokens|
      f1        = 2 * precision * recall / (precision + recall)

    真实 Reranker 用 cross-encoder（如 BAAI/bge-reranker-large），效果远强于此。
    """

    def rerank(
        self,
        query: str,
        candidates: list[RetrievalResult],
        top_n: int | None = None,
    ) -> list[RetrievalResult]:
        """返回按 rerank_score 降序的结果。"""
        query_tokens = set(_simple_tokenize(query))
        if not query_tokens:
            return candidates[:top_n]

        scored: list[tuple[RetrievalResult, float]] = []
        for result in candidates:
            doc_tokens = set(_simple_tokenize(result.chunk.content))
            if not doc_tokens:
                scored.append((result, 0.0))
                continue
            overlap = len(query_tokens & doc_tokens)
            precision = overlap / len(query_tokens)
            recall = overlap / len(doc_tokens)
            f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
            scored.append((result, f1))

        scored.sort(key=lambda x: x[1], reverse=True)
        limit = top_n if top_n is not None else len(scored)
        return [
            RetrievalResult(chunk=result.chunk, score=rerank_score)
            for result, rerank_score in scored[:limit]
        ]
