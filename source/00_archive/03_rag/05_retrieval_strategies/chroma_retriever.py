"""Chroma 检索适配层。

这一层负责把第五章的策略语义映射到真实 Chroma backend：
先按 query embedding 取候选，再把过滤后的结果还原成 `EmbeddedChunk`，
最后复用 `select_search_hits()` 做策略选择。
"""

from __future__ import annotations

from retrieval_basics import (
    EmbeddingProvider,
    RetrievalStrategyConfig,
    SearchHit,
    hits_to_results,
    select_search_hits,
)
from chroma_store import ChromaVectorStore


class ChromaRetriever:
    def __init__(
        self,
        store: ChromaVectorStore,
        provider: EmbeddingProvider,
    ) -> None:
        self.store = store
        self.provider = provider

    def retrieve(
        self,
        question: str,
        strategy: RetrievalStrategyConfig,
    ):
        # query 仍然先进入同一个 embedding space，再交给真实 store 召回候选。
        query_vector = self.provider.embed_query(question)
        candidates = self._search_candidates(
            query_vector=query_vector,
            candidate_k=strategy.candidate_k,
            filename_filter=strategy.filename_filter,
        )
        # Chroma 只负责候选召回，最终选哪些结果仍然交给第五章的策略层。
        return hits_to_results(select_search_hits(query_vector, candidates, strategy))

    def _search_candidates(
        self,
        query_vector: list[float],
        candidate_k: int,
        filename_filter: str | None = None,
    ) -> list[SearchHit]:
        where = {"filename": filename_filter} if filename_filter else None
        # where 过滤进入数据库查询路径，先把候选范围缩窄，再取 top_k。
        raw_results = self.store.similarity_search(
            query_vector=query_vector,
            provider=self.provider,
            top_k=candidate_k,
            where=where,
        )
        if not raw_results:
            return []

        # similarity_search 返回的是“候选命中”，但教学层还需要完整 chunk 内容和 metadata，
        # 所以这里要再把 raw result rehydrate 回 EmbeddedChunk。
        embedded_chunks = self.store.load_chunks(where=where)
        chunk_by_id = {chunk.chunk.chunk_id: chunk for chunk in embedded_chunks}
        hits: list[SearchHit] = []
        for result in raw_results:
            embedded_chunk = chunk_by_id.get(result.chunk.chunk_id)
            if embedded_chunk is None:
                raise ValueError(
                    f"Chroma candidate {result.chunk.chunk_id} could not be rehydrated as an EmbeddedChunk."
                )
            hits.append(
                SearchHit(
                    embedded_chunk=embedded_chunk,
                    similarity_score=float(result.score),
                )
            )
        return hits
