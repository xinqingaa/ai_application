from __future__ import annotations

from dataclasses import dataclass, field
from math import sqrt
from pathlib import Path
import hashlib
import json
import os
import re
from typing import Any, Protocol


CHAPTER_ROOT = Path(__file__).resolve().parent
DATA_DIR = CHAPTER_ROOT / "data"
SOURCE_CHUNKS_PATH = DATA_DIR / "source_chunks.json"
SEARCH_CASES_PATH = DATA_DIR / "search_cases.json"

TOKEN_PATTERN = re.compile(r"[a-z0-9]+|[\u4e00-\u9fff]", re.IGNORECASE)
STOPWORDS = {"the", "a", "an", "is", "are", "to", "of", "and", "how", "why", "do"}
CONCEPT_GROUPS = [
    ("refund", ("退款", "退费", "refund")),
    ("trial", ("试学", "预约", "trial")),
    ("metadata", ("metadata", "source", "filename", "来源")),
    ("stable_id", ("stable", "id", "document_id", "chunk_id", "稳定")),
    ("embedding", ("embedding", "向量", "vector")),
    ("similarity", ("similarity", "相似度", "检索", "retrieve")),
    ("support", ("答疑", "support", "工作日")),
]
HASH_BUCKETS = 4
MODE_BUCKETS = 2
DEFAULT_DIMENSIONS = len(CONCEPT_GROUPS) + HASH_BUCKETS + MODE_BUCKETS

SEMANTIC_CONCEPT_GROUPS = [
    ("refund", ("退款", "退费", "退钱", "退回来", "refund")),
    ("trial", ("试学", "预约", "trial")),
    ("metadata", ("metadata", "source", "filename", "header_path", "来源", "出处", "引用", "出处字段")),
    ("stable_id", ("stable", "id", "document_id", "chunk_id", "更新", "删除", "稳定")),
    ("embedding", ("embedding", "向量", "向量化")),
    ("similarity", ("similarity", "相似度", "检索", "召回")),
    ("support", ("答疑", "support", "工作日", "助教")),
]
SEMANTIC_DIMENSIONS = len(SEMANTIC_CONCEPT_GROUPS)
EMBEDDING_API_KEY_ENV_KEYS = ("EMBEDDING_API_KEY", "OPENAI_API_KEY")
EMBEDDING_BASE_URL_ENV_KEYS = ("EMBEDDING_BASE_URL", "OPENAI_BASE_URL")
EMBEDDING_MODEL_ENV_KEYS = ("EMBEDDING_MODEL", "OPENAI_EMBEDDING_MODEL")


@dataclass(frozen=True)
class SourceChunk:
    """向量化前的稳定文档块。

    字段说明：
        chunk_id: chunk 的稳定 id，用来追踪排序结果来自哪一块。
        document_id: 原始文档 id，多块 chunk 可以属于同一文档。
        content: 进入 embedding provider 的正文文本。
        metadata: 第二章保留下来的来源、文件名、切分范围等辅助信息。
    """

    chunk_id: str
    document_id: str
    content: str
    metadata: dict[str, str | int | float | bool] = field(default_factory=dict)


@dataclass(frozen=True)
class EmbeddedChunk:
    """向量化后的文档块。

    字段说明：
        chunk: 原始 SourceChunk，保证向量结果不丢来源和正文。
        vector: document path 生成的向量。
        provider_name: 生成该向量的 provider 名称。
        model_name: 生成该向量的模型名称。
        dimensions: 向量维度，用于后续空间一致性校验。
    """

    chunk: SourceChunk
    vector: list[float]
    provider_name: str
    model_name: str
    dimensions: int


@dataclass(frozen=True)
class MockEmbeddingData:
    """模拟 OpenAI embeddings response 中的单条 data 元素。"""

    index: int
    embedding: list[float]


@dataclass(frozen=True)
class MockEmbeddingResponse:
    """模拟 OpenAI embeddings API 的最小响应对象。"""

    data: list[MockEmbeddingData]
    model: str


class EmbeddingProvider(Protocol):
    """本章所有 embedding provider 必须满足的最小契约。"""

    provider_name: str
    model_name: str
    dimensions: int

    def embed_query(self, text: str) -> list[float]:
        """把用户查询文本转换为 query vector。"""
        ...

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """把一批文档文本转换为 document vectors。"""
        ...


class LocalKeywordEmbeddingProvider:
    """本章教学用的本地关键词向量 provider。

    作用：
        不依赖外部模型，通过概念词命中、hash buckets 和 mode buckets
        构造可解释的小维度向量，用来讲清 embedding space、query/document
        契约和相似度排序。
    """

    def __init__(
        self,
        model_name: str = "concept-space-v1",
        dimensions: int = DEFAULT_DIMENSIONS,
    ) -> None:
        """初始化本地 toy provider。

        入参：
            model_name: provider 暴露给外部的模型名，用于同空间校验。
            dimensions: 向量维度，必须等于 DEFAULT_DIMENSIONS。
        流程：
            1. 校验传入维度是否符合本地 provider 的固定设计。
            2. 写入 provider_name、model_name、dimensions 三个身份字段。
        """
        if dimensions != DEFAULT_DIMENSIONS:
            raise ValueError(
                f"LocalKeywordEmbeddingProvider expects dimensions={DEFAULT_DIMENSIONS}."
            )

        self.provider_name = "local_keyword"
        self.model_name = model_name
        self.dimensions = dimensions

    def embed_query(self, text: str) -> list[float]:
        """把查询文本转换为 query vector。

        入参：
            text: 用户问题或检索查询文本。
        流程：
            直接委托给 _embed(text, kind="query")，由 _embed 写入 query
            专属 mode bucket。
        """
        return self._embed(text, kind="query")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """把文档文本批量转换为 document vectors。

        入参：
            texts: 文档 chunk 正文列表，顺序会和返回向量一一对应。
        流程：
            逐条调用 _embed(text, kind="document")，由 _embed 写入 document
            专属 mode bucket。
        """
        return [self._embed(text, kind="document") for text in texts]

    def _embed(self, text: str, kind: str) -> list[float]:
        """执行 toy provider 的实际向量构造。

        入参：
            text: 需要向量化的文本。
            kind: "query" 或 "document"，决定尾部 mode bucket 的写入位置。
        流程：
            1. 归一化文本大小写和空白。
            2. 根据 CONCEPT_GROUPS 统计概念词命中次数。
            3. 把概念组外的 token 落入 hash buckets，保留弱分布信号。
            4. 根据 kind 写入 query/document 角色 bucket。
            5. 调用 normalize() 返回单位向量。
        """
        normalized = " ".join(text.lower().split())
        vector = [0.0] * self.dimensions

        # 先写入共享概念信号，让 query/document 至少共享一套可比较的语义基底。
        for index, (_, keywords) in enumerate(CONCEPT_GROUPS):
            hits = sum(1 for keyword in keywords if keyword in normalized)
            vector[index] = float(hits)

        hash_offset = len(CONCEPT_GROUPS)
        # 概念组外的 token 不直接丢弃，而是落到 hash buckets 保留最小分布能力。
        for token in TOKEN_PATTERN.findall(normalized):
            if token in STOPWORDS:
                continue
            bucket = int(hashlib.sha1(token.encode("utf-8")).hexdigest(), 16) % HASH_BUCKETS
            vector[hash_offset + bucket] += 0.25

        query_mode_index = self.dimensions - 2
        document_mode_index = self.dimensions - 1
        # 尾部两个 bucket 刻意把 query/document 角色差异显式写进向量。
        if kind == "query":
            vector[query_mode_index] = 0.30
        else:
            vector[document_mode_index] = 0.30

        return normalize(vector)


class OpenAICompatibleEmbeddingProvider:
    """OpenAI-compatible embeddings endpoint 的适配器。

    作用：
        把真实或 fake OpenAI-compatible client 包装成本章统一的
        EmbeddingProvider 契约，同时负责维度记录、批量数量校验和响应形态校验。
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model_name: str = "text-embedding-3-small",
        expected_dimensions: int | None = None,
        client: Any | None = None,
    ) -> None:
        """初始化 OpenAI-compatible provider。

        入参：
            api_key: 真实 endpoint 的 API key；传入 client 时可以为空。
            base_url: OpenAI-compatible 服务地址；为空时使用 SDK 默认地址。
            model_name: embeddings 模型名称。
            expected_dimensions: 预期向量维度；为空时由第一次响应自动记录。
            client: 注入的真实或测试 client，必须暴露 embeddings.create()。
        流程：
            记录 provider 身份、连接配置和可选 client；真正创建 SDK client
            会延迟到 _ensure_client()。
        """
        self.provider_name = "openai_compatible"
        self.model_name = model_name
        self.dimensions = expected_dimensions or 0
        self.api_key = api_key
        self.base_url = base_url
        self._client = client

    @classmethod
    def from_env(
        cls,
        *,
        model_name: str | None = None,
        expected_dimensions: int | None = None,
        client: Any | None = None,
    ) -> OpenAICompatibleEmbeddingProvider:
        """从环境变量构造 OpenAI-compatible provider。

        入参：
            model_name: 显式模型名；为空时读取 EMBEDDING_MODEL 或 OPENAI_EMBEDDING_MODEL。
            expected_dimensions: 显式维度；为空时尝试读取 EMBEDDING_DIMENSIONS。
            client: 可选注入 client，通常用于测试或 mock。
        流程：
            1. 读取可选维度环境变量。
            2. 按优先级读取 API key、base url 和模型名。
            3. 调用构造函数返回 provider。
        """
        configured_dimensions = expected_dimensions
        dimensions_text = os.getenv("EMBEDDING_DIMENSIONS")
        if configured_dimensions is None and dimensions_text:
            configured_dimensions = int(dimensions_text)

        return cls(
            api_key=first_env(*EMBEDDING_API_KEY_ENV_KEYS),
            base_url=first_env(*EMBEDDING_BASE_URL_ENV_KEYS),
            model_name=(
                model_name
                or first_env(*EMBEDDING_MODEL_ENV_KEYS)
                or "text-embedding-3-small"
            ),
            expected_dimensions=configured_dimensions,
            client=client,
        )

    @property
    def is_ready(self) -> bool:
        """判断 provider 是否具备发起 embedding 请求的条件。

        入参：
            无。
        流程：
            如果已注入 client，或存在 api_key，就认为可以继续调用。
        """
        return self._client is not None or bool(self.api_key)

    def describe(self) -> dict[str, str | int | bool | None]:
        """返回 provider 的可打印诊断信息。

        入参：
            无。
        流程：
            汇总 provider/model/base_url/dimensions/ready/client_type，
            供 04_real_embeddings.py 展示真实或 mock provider 状态。
        """
        return {
            "provider_name": self.provider_name,
            "model_name": self.model_name,
            "base_url": self.base_url,
            "dimensions": self.dimensions or None,
            "ready": self.is_ready,
            "client_type": type(self._client).__name__ if self._client else None,
        }

    def embed_query(self, text: str) -> list[float]:
        """把查询文本转换为 query vector。

        入参：
            text: 用户问题或检索查询文本。
        流程：
            真实 OpenAI-compatible embeddings API 通常不区分 query/document
            endpoint，因此这里把单条文本包装成列表交给 _embed_many()，
            再取第一条向量返回。
        """
        vectors = self._embed_many([text])
        return vectors[0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """把一批文档文本转换为 document vectors。

        入参：
            texts: 文档 chunk 正文列表，顺序应与返回向量一致。
        流程：
            直接交给 _embed_many() 批量调用 embeddings endpoint。
        """
        return self._embed_many(texts)

    def _embed_many(self, texts: list[str]) -> list[list[float]]:
        """批量调用 embeddings endpoint 并校验响应。

        入参：
            texts: 待向量化文本列表，可以为空。
        流程：
            1. 空列表直接返回空列表。
            2. 通过 _ensure_client() 获取真实或注入 client。
            3. 调用 client.embeddings.create(model=..., input=texts)。
            4. 校验 response.data 是列表，且每项都包含 embedding。
            5. 记录或校验维度，并对每条向量 normalize()。
            6. 校验返回向量数量与输入文本数量一致。
        """
        if not texts:
            return []

        client = self._ensure_client()
        response = client.embeddings.create(model=self.model_name, input=texts)
        data = getattr(response, "data", None)
        if not isinstance(data, list):
            raise ValueError("Embedding response must expose a list-like `data` field.")

        vectors: list[list[float]] = []
        for index, item in enumerate(data):
            raw_vector = getattr(item, "embedding", None)
            if not isinstance(raw_vector, list):
                raise ValueError(f"Embedding item at index {index} is missing a vector.")
            self._record_dimensions(raw_vector)
            vectors.append(normalize([float(value) for value in raw_vector]))

        if len(vectors) != len(texts):
            raise ValueError("Embedding provider returned an unexpected vector count.")
        return vectors

    def _record_dimensions(self, vector: list[float]) -> None:
        """记录首次响应维度，或校验后续响应没有维度漂移。

        入参：
            vector: endpoint 返回的单条原始向量。
        流程：
            1. 如果 provider.dimensions 仍为 0，用当前向量长度初始化。
            2. 否则要求当前向量长度等于已记录维度。
        """
        if self.dimensions == 0:
            self.dimensions = len(vector)
            return
        if len(vector) != self.dimensions:
            raise ValueError(
                f"Embedding vector has dimensions={len(vector)}, expected {self.dimensions}."
            )

    def _ensure_client(self) -> Any:
        """获取可用 OpenAI-compatible client。

        入参：
            无。
        流程：
            1. 如果已有注入或缓存 client，直接返回。
            2. 如果没有 api_key，抛出配置错误。
            3. 延迟导入 openai.OpenAI。
            4. 按 api_key 和可选 base_url 创建 SDK client 并缓存。
        """
        if self._client is not None:
            return self._client

        if not self.api_key:
            raise ValueError(
                "Missing embedding API key. Set EMBEDDING_API_KEY or OPENAI_API_KEY."
            )

        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - depends on local env
            raise ImportError(
                "openai is required for real embedding calls. Run `python -m pip install -r requirements.txt`."
            ) from exc

        kwargs: dict[str, str] = {"api_key": self.api_key}
        if self.base_url:
            kwargs["base_url"] = self.base_url
        self._client = OpenAI(**kwargs)
        return self._client


class MockSemanticOpenAIClient:
    """内置 mock client，模拟 OpenAI SDK 的 embeddings 资源结构。"""

    def __init__(self) -> None:
        """创建 mock embeddings resource。

        入参：
            无。
        流程：
            把 _MockSemanticEmbeddingsResource 挂到 self.embeddings，
            使其具备 client.embeddings.create() 形态。
        """
        self.embeddings = _MockSemanticEmbeddingsResource()


class _MockSemanticEmbeddingsResource:
    def create(self, *, model: str, input: list[str] | str) -> MockEmbeddingResponse:
        """模拟 embeddings.create() 方法。

        入参：
            model: 调用方传入的模型名，会原样放入响应。
            input: 单条文本或文本列表。
        流程：
            1. 把 input 统一转换为文本列表。
            2. 对每条文本调用 build_mock_semantic_vector()。
            3. 包装成 MockEmbeddingResponse 返回。
        """
        texts = [input] if isinstance(input, str) else list(input)
        return MockEmbeddingResponse(
            data=[
                MockEmbeddingData(index=index, embedding=build_mock_semantic_vector(text))
                for index, text in enumerate(texts)
            ],
            model=model,
        )


def first_env(*keys: str) -> str | None:
    """按顺序读取第一个有值的环境变量。

    入参：
        *keys: 环境变量名列表，越靠前优先级越高。
    流程：
        1. 逐个读取 os.getenv(key)。
        2. 遇到非空值立即返回。
        3. 全部为空时返回 None。
    """
    for key in keys:
        value = os.getenv(key)
        if value:
            return value
    return None


def demo_chunk_metadata(source: str, content: str, chunk_index: int = 0) -> dict[str, str | int]:
    """为 demo chunk 构造第二章风格的 metadata。

    入参：
        source: 原始文档路径或来源标识。
        content: chunk 正文，用于计算字符数和行数。
        chunk_index: 当前 chunk 在文档中的序号。
    流程：
        1. 从 source 中拆出 filename 和 suffix。
        2. 根据 content 计算 char_count、line_count 和范围字段。
        3. 返回包含 source、filename、suffix、chunk_index、字符范围等字段的字典。
    """
    filename = source.rsplit("/", maxsplit=1)[-1]
    suffix = f".{filename.rsplit('.', maxsplit=1)[-1]}" if "." in filename else ""
    char_count = len(content)
    line_count = 0 if not content else content.count("\n") + 1
    return {
        "source": source,
        "filename": filename,
        "suffix": suffix,
        "char_count": char_count,
        "line_count": line_count,
        "chunk_index": chunk_index,
        "char_start": 0,
        "char_end": char_count,
        "chunk_chars": char_count,
    }


def load_demo_source_chunk_specs(path: Path | None = None) -> list[dict[str, Any]]:
    """读取 demo source chunk 的 JSON 配置。

    入参：
        path: 可选 JSON 路径；为空时读取 data/source_chunks.json。
    流程：
        1. 决定目标文件路径。
        2. 用 UTF-8 读取并 json.load()。
        3. 校验顶层结构必须是 list。
        4. 返回原始 spec 列表，后续由 demo_source_chunks() 转成 SourceChunk。
    """
    target_path = path or SOURCE_CHUNKS_PATH
    with target_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise TypeError("source chunk specs must be a list")
    return data


def load_search_cases(path: Path | None = None) -> list[dict[str, Any]]:
    """读取本章检索回归样例。

    入参：
        path: 可选 JSON 路径；为空时读取 data/search_cases.json。
    流程：
        1. 决定目标文件路径。
        2. 用 UTF-8 读取并 json.load()。
        3. 校验顶层结构必须是 list。
        4. 返回 search case 列表，供脚本和测试复用。
    """
    target_path = path or SEARCH_CASES_PATH
    with target_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise TypeError("search cases must be a list")
    return data


def build_openai_provider_or_mock(
    *,
    force_mock: bool = False,
    model_name: str | None = None,
) -> tuple[OpenAICompatibleEmbeddingProvider, str]:
    """构造真实 OpenAI-compatible provider，或回退到 mock provider。

    入参：
        force_mock: 为 True 时无条件使用内置 mock semantic client。
        model_name: 可选模型名；为空时真实 provider 读环境变量，mock 使用默认名。
    流程：
        1. 如果 force_mock=True，直接返回 mock provider 和 "mock" 模式。
        2. 否则从环境变量构造真实 provider。
        3. 如果真实 provider 已具备 client 或 api_key，返回它和 "real" 模式。
        4. 如果缺少真实配置，回退到 mock provider，保证教学脚本可运行。
    """
    if force_mock:
        return (
            OpenAICompatibleEmbeddingProvider(
                client=MockSemanticOpenAIClient(),
                model_name=model_name or "mock-semantic-bridge",
                expected_dimensions=SEMANTIC_DIMENSIONS,
            ),
            "mock",
        )

    provider = OpenAICompatibleEmbeddingProvider.from_env(model_name=model_name)
    if provider.is_ready:
        return provider, "real"

    # 没有真实环境变量时仍然回退到 mock，方便继续观察第三章的契约和排序闭环。
    return (
        OpenAICompatibleEmbeddingProvider(
            client=MockSemanticOpenAIClient(),
            model_name=model_name or "mock-semantic-bridge",
            expected_dimensions=SEMANTIC_DIMENSIONS,
        ),
        "mock",
    )


def demo_source_chunks(path: Path | None = None) -> list[SourceChunk]:
    """把 JSON specs 转换为 SourceChunk 对象列表。

    入参：
        path: 可选 source_chunks.json 路径；为空时读取本章默认数据。
    流程：
        1. 调用 load_demo_source_chunk_specs() 读取原始配置。
        2. 逐条取出 source、content、chunk_index。
        3. 用 demo_chunk_metadata() 生成基础 metadata。
        4. 如果 spec 中有额外 metadata，则合并覆盖。
        5. 创建 SourceChunk 并保持原始顺序返回。
    """
    chunks: list[SourceChunk] = []
    for spec in load_demo_source_chunk_specs(path):
        source = str(spec["source"])
        content = str(spec["content"])
        chunk_index = int(spec.get("chunk_index", 0))
        metadata = demo_chunk_metadata(source, content, chunk_index)

        extra_metadata = spec.get("metadata")
        if isinstance(extra_metadata, dict):
            metadata.update(extra_metadata)

        chunks.append(
            SourceChunk(
                chunk_id=str(spec["chunk_id"]),
                document_id=str(spec["document_id"]),
                content=content,
                metadata=metadata,
            )
        )
    return chunks


def ensure_vector_dimensions(
    vector: list[float],
    expected_dimensions: int,
    context: str,
) -> None:
    """校验单条向量维度是否符合预期。

    入参：
        vector: 要检查的向量。
        expected_dimensions: 预期维度。
        context: 错误信息中的上下文说明，例如 query vector 或 chunk id。
    流程：
        直接比较 len(vector) 和 expected_dimensions，不一致就抛出 ValueError。
    """
    if len(vector) != expected_dimensions:
        raise ValueError(
            f"{context} has dimensions={len(vector)}, expected {expected_dimensions}."
        )


def ensure_same_embedding_space(
    chunk: EmbeddedChunk,
    provider: EmbeddingProvider,
) -> None:
    """校验 query provider 和 document chunk 处于同一 embedding space。

    入参：
        chunk: 已经向量化的 EmbeddedChunk。
        provider: 当前用于生成 query vector 的 provider。
    流程：
        1. 比较 provider_name 和 model_name，防止跨 provider/model 打分。
        2. 比较 chunk.dimensions 和 provider.dimensions。
        3. 调用 ensure_vector_dimensions() 校验 chunk.vector 的实际长度。
    """
    # 这里校验的是 provider/model/dimensions 身份，而不只是“向量长度对不对”。
    if chunk.provider_name != provider.provider_name or chunk.model_name != provider.model_name:
        raise ValueError("Query and document vectors must come from the same provider/model.")

    if chunk.dimensions != provider.dimensions:
        raise ValueError("Embedded chunk dimensions do not match provider dimensions.")

    ensure_vector_dimensions(
        chunk.vector,
        chunk.dimensions,
        context=f"embedded chunk {chunk.chunk.chunk_id}",
    )


def embed_chunks(
    chunks: list[SourceChunk],
    provider: EmbeddingProvider,
) -> list[EmbeddedChunk]:
    """把 SourceChunk 列表批量转换为 EmbeddedChunk 列表。

    入参：
        chunks: 稳定文档块列表，每个 chunk 至少包含 id、document_id、content、metadata。
        provider: 实现 EmbeddingProvider 契约的向量提供者。
    流程：
        1. 空输入直接返回空列表。
        2. 收集所有 chunk.content，统一走 provider.embed_documents()。
        3. 校验返回向量数量必须等于 chunk 数量。
        4. 逐条校验向量维度。
        5. 用原始 SourceChunk、vector 和 provider 身份封装为 EmbeddedChunk。
    """
    if not chunks:
        return []

    # 先统一走 document path，把稳定 chunk 资产收束成可比较的 document vectors。
    vectors = provider.embed_documents([chunk.content for chunk in chunks])
    if len(vectors) != len(chunks):
        raise ValueError("Embedding provider returned an unexpected vector count.")

    embedded_chunks: list[EmbeddedChunk] = []
    for chunk, vector in zip(chunks, vectors):
        ensure_vector_dimensions(
            vector,
            provider.dimensions,
            context=f"document vector for {chunk.chunk_id}",
        )
        embedded_chunks.append(
            EmbeddedChunk(
                chunk=chunk,
                vector=vector,
                provider_name=provider.provider_name,
                model_name=provider.model_name,
                dimensions=provider.dimensions,
            )
        )
    return embedded_chunks


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """计算两个向量的余弦相似度。

    入参：
        left: 左侧向量。
        right: 右侧向量。
    流程：
        1. 校验两个向量维度相同。
        2. 分别计算两个向量的 L2 norm。
        3. 任一向量为零向量时返回 0.0。
        4. 计算 dot product / (left_norm * right_norm)。
    """
    if len(left) != len(right):
        raise ValueError("Cosine similarity requires vectors with the same dimensions.")

    left_norm = sqrt(sum(value * value for value in left))
    right_norm = sqrt(sum(value * value for value in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0

    dot_product = sum(left_value * right_value for left_value, right_value in zip(left, right))
    return dot_product / (left_norm * right_norm)


def score_query_against_chunks(
    question: str,
    chunks: list[EmbeddedChunk],
    provider: EmbeddingProvider,
) -> list[tuple[EmbeddedChunk, float]]:
    """用 query vector 给一组 EmbeddedChunk 打分并排序。

    入参：
        question: 用户问题，会通过 provider.embed_query() 生成 query vector。
        chunks: 已经用 document path 向量化好的 EmbeddedChunk 列表。
        provider: 生成 query vector 的 provider，必须与 chunks 同空间。
    流程：
        1. 空 chunks 直接返回空列表。
        2. 生成 query vector 并校验维度。
        3. 逐个 chunk 校验 provider/model/dimensions 一致。
        4. 计算 query vector 与 chunk.vector 的 cosine similarity。
        5. 按分数从高到低排序返回。
    """
    if not chunks:
        return []

    query_vector = provider.embed_query(question)
    ensure_vector_dimensions(query_vector, provider.dimensions, context="query vector")
    scored: list[tuple[EmbeddedChunk, float]] = []
    for chunk in chunks:
        ensure_same_embedding_space(chunk, provider)
        # 到这里才真正进入 query vs document 的比较阶段。
        scored.append((chunk, cosine_similarity(query_vector, chunk.vector)))
    return sorted(scored, key=lambda item: item[1], reverse=True)


def build_mock_semantic_vector(text: str) -> list[float]:
    """为 mock semantic client 构造语义概念向量。

    入参：
        text: 待向量化文本。
    流程：
        1. 归一化大小写和空白。
        2. 遍历 SEMANTIC_CONCEPT_GROUPS，统计每个语义概念的关键词命中。
        3. 调用 normalize() 返回单位向量。
    """
    normalized = " ".join(text.lower().split())
    vector = [0.0] * SEMANTIC_DIMENSIONS

    for index, (_, keywords) in enumerate(SEMANTIC_CONCEPT_GROUPS):
        hits = sum(1.0 for keyword in keywords if keyword in normalized)
        vector[index] = hits

    return normalize(vector)


def normalize(vector: list[float]) -> list[float]:
    """把向量归一化为单位向量。

    入参：
        vector: 原始浮点向量。
    流程：
        1. 计算 L2 norm。
        2. 如果是零向量，原样返回，避免除以 0。
        3. 否则逐维除以 norm。
    """
    norm = sqrt(sum(value * value for value in vector))
    if norm == 0.0:
        return vector
    return [value / norm for value in vector]
