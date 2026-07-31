"""Application-side lexical analysis before PostgreSQL ``simple`` FTS."""

from __future__ import annotations

import logging
import re
import unicodedata

import jieba

from rag_core.lexical.models import LexicalAnalysis, LexicalConfig, QueryOperator

_SEGMENT_PATTERN = re.compile(
    r"[A-Za-z][A-Za-z0-9_./:+#%-]*|\d+(?:\.\d+)*|[\u3400-\u4dbf\u4e00-\u9fff]+"
)
_TECHNICAL_PATTERN = re.compile(
    r"^(?:[a-z][a-z0-9]*(?:[_.:/+#%-][a-z0-9]+)+|[a-z]+\d+|\d{3,})$"
)
_ALNUM_PATTERN = re.compile(r"[^a-z0-9]+")


class LexicalAnalyzer:
    """Produce the same versioned lexemes for documents and queries."""

    def __init__(self, config: LexicalConfig | None = None) -> None:
        self.config = config or LexicalConfig()
        jieba.setLogLevel(logging.ERROR)
        self._tokenizer = jieba.Tokenizer()
        for term in self.config.domain_terms:
            self._tokenizer.add_word(term)
        self._stop_terms = frozenset(self.config.stop_terms)

    def analyze_document(self, text: str) -> LexicalAnalysis:
        normalized = self._normalize(text)
        terms = self._terms(normalized, unique=False)
        return LexicalAnalysis(
            original_text=text,
            normalized_text=normalized,
            terms=terms,
            lexical_text=" ".join(terms),
            config_ref=self.config.config_ref,
            postgres_config=self.config.postgres_config,
        )

    def analyze_query(self, text: str) -> LexicalAnalysis:
        normalized = self._normalize(text)
        terms = self._terms(normalized, unique=True)
        if self.config.query_operator is QueryOperator.OR:
            query = " OR ".join(_quote_websearch_term(term) for term in terms)
        else:
            query = " ".join(_quote_websearch_term(term) for term in terms)
        return LexicalAnalysis(
            original_text=text,
            normalized_text=normalized,
            terms=terms,
            lexical_text=" ".join(terms),
            config_ref=self.config.config_ref,
            postgres_config=self.config.postgres_config,
            query_operator=self.config.query_operator,
            websearch_query=query,
        )

    def _terms(self, normalized: str, *, unique: bool) -> tuple[str, ...]:
        terms: list[str] = []
        for segment in _SEGMENT_PATTERN.findall(normalized):
            if _is_cjk(segment):
                for term in self._tokenizer.cut_for_search(segment, HMM=False):
                    cleaned = term.strip()
                    if cleaned and cleaned not in self._stop_terms:
                        terms.append(cleaned)
                continue

            technical = segment.casefold()
            if technical not in self._stop_terms:
                terms.append(technical)
            if _TECHNICAL_PATTERN.fullmatch(technical):
                terms.append(_technical_sentinel(technical))

        if unique:
            terms = list(dict.fromkeys(terms))
        if not terms:
            raise ValueError("文本没有产生可检索词项")
        return tuple(terms)

    @staticmethod
    def _normalize(text: str) -> str:
        if not text.strip():
            raise ValueError("待分析文本不能为空")
        return unicodedata.normalize("NFKC", text).casefold().strip()


def _is_cjk(text: str) -> bool:
    return bool(text) and all(
        "\u3400" <= character <= "\u4dbf"
        or "\u4e00" <= character <= "\u9fff"
        for character in text
    )


def _technical_sentinel(term: str) -> str:
    compact = _ALNUM_PATTERN.sub("", term)
    return f"techid{compact}"


def _quote_websearch_term(term: str) -> str:
    # Analyzer terms never contain quotes. Quoting also prevents the literal word
    # "or" or a leading dash from becoming websearch syntax.
    return f'"{term}"'
