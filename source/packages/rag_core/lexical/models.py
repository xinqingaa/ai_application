"""Contracts for reproducible Chinese and technical-term lexical analysis."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum


class QueryOperator(str, Enum):
    OR = "or"
    AND = "and"


@dataclass(frozen=True)
class LexicalConfig:
    name: str = "jieba_search_simple"
    version: str = "1.0.0"
    postgres_config: str = "pg_catalog.simple"
    query_operator: QueryOperator = QueryOperator.OR
    domain_terms: tuple[str, ...] = (
        "售后",
        "逆向服务",
        "虚拟商品",
    )
    stop_terms: tuple[str, ...] = (
        "的",
        "了",
        "吗",
        "呢",
        "请问",
        "什么",
        "时候",
        "如何",
        "怎么",
        "是否",
    )

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("LexicalConfig.name 不能为空")
        if not self.version.strip():
            raise ValueError("LexicalConfig.version 不能为空")
        if not self.postgres_config.strip():
            raise ValueError("LexicalConfig.postgres_config 不能为空")
        if any(not term.strip() for term in self.domain_terms):
            raise ValueError("LexicalConfig.domain_terms 不能包含空词")
        if any(not term.strip() for term in self.stop_terms):
            raise ValueError("LexicalConfig.stop_terms 不能包含空词")

    @property
    def fingerprint(self) -> str:
        payload = {
            "name": self.name,
            "version": self.version,
            "postgres_config": self.postgres_config,
            "domain_terms": self.domain_terms,
            "stop_terms": self.stop_terms,
        }
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        return hashlib.sha256(encoded).hexdigest()[:16]

    @property
    def config_ref(self) -> str:
        return f"{self.name}@{self.version}:{self.fingerprint}"

    @property
    def retriever_config_ref(self) -> str:
        payload = {
            "lexical_config_ref": self.config_ref,
            "query_operator": self.query_operator.value,
            "rank_name": "postgresql_ts_rank",
        }
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        fingerprint = hashlib.sha256(encoded).hexdigest()[:16]
        return f"postgres_fts@1.0.0:{fingerprint}"


@dataclass(frozen=True)
class LexicalAnalysis:
    original_text: str
    normalized_text: str
    terms: tuple[str, ...]
    lexical_text: str
    config_ref: str
    postgres_config: str
    query_operator: QueryOperator | None = None
    websearch_query: str | None = None

    def __post_init__(self) -> None:
        if not self.original_text.strip():
            raise ValueError("LexicalAnalysis.original_text 不能为空")
        if not self.terms:
            raise ValueError("词法分析没有产生可检索词项")
        if not self.lexical_text.strip():
            raise ValueError("LexicalAnalysis.lexical_text 不能为空")
        if not self.config_ref.strip():
            raise ValueError("LexicalAnalysis.config_ref 不能为空")
        if self.query_operator is not None and not self.websearch_query:
            raise ValueError("查询分析必须生成 websearch_query")
