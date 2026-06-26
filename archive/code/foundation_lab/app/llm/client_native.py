"""
foundation_lab 的原生 LLM 客户端。

这个文件承担两层目标：
1. 在没有真实模型配置时，保留一条可观察的 mock 路径
2. 在提供 API Key 和兼容端点后，支持最小真实原生调用

这样做的原因是：
- 文档和代码都能继续按同一条抽象边界推进
- 当前环境即使没有依赖和网络，也不会阻塞整体项目阅读
- 后续接入真实 provider 时，不需要再推翻 service 和 chain 结构
"""

from __future__ import annotations

from collections.abc import Iterator
import json
from urllib import error, request

from app.config import Settings, get_settings


class NativeLLMClient:
    """提供 mock 与真实原生调用两套最小路径。

    推荐阅读顺序：
    1. `mocked`：先看什么时候会回退到 mock
    2. `invoke()`：看一次普通调用如何发出
    3. `stream()`：看流式调用如何逐片返回
    4. `structured_invoke()`：看结构化示例如何在原生客户端层暴露
    5. `_request_json()`、`_stream_json()`：看最底层 HTTP 请求细节
    """

    def __init__(self, settings: Settings | None = None) -> None:
        """保存运行配置，供真实调用和 mock 回退共同复用。"""

        self.settings = settings or get_settings()

    @property
    def mocked(self) -> bool:
        """判断当前是否应该走 mock 路径。

        回退条件保持刻意简单：
        - provider 明确设为 `mock`
        - 没有 API Key，且允许在未配置时自动走 mock
        """

        return self.settings.provider == "mock" or (
            self.settings.use_mock_when_unconfigured and not self.settings.api_key
        )

    @property
    def api_base_url(self) -> str:
        """返回真实调用所使用的 API 根地址。"""

        if self.settings.base_url:
            return self.settings.base_url.rstrip("/")
        return "https://api.openai.com/v1"

    def invoke(self, prompt: str) -> str:
        """执行一次普通文本调用。

        执行顺序是：
        1. 先判断是否走 mock
        2. 如果不是 mock，就构造最小 chat completions 请求
        3. 再从返回 JSON 中提取模型文本
        """

        if self.mocked:
            return self._mock_response(prompt)
        payload = self._build_chat_payload(prompt, stream=False)
        response = self._request_json("/chat/completions", payload)
        return self._extract_text(response)

    def stream(self, prompt: str) -> Iterator[str]:
        """执行最小流式调用。

        当前实现分两种情况：
        - mock 模式：把完整文本拆词输出，方便在本地观察
        - 真实模式：读取兼容 SSE 的 `data:` 片段
        """

        if self.mocked:
            text = self.invoke(prompt)
            for token in text.split():
                yield f"{token} "
            return

        payload = self._build_chat_payload(prompt, stream=True)
        yield from self._stream_json("/chat/completions", payload)

    def structured_invoke(self, question: str) -> dict[str, str | bool]:
        """演示原生客户端如何暴露结构化结果。

        这里不追求复杂 schema，只固定一个最小例子：
        - `summary`
        - `category`

        这样后续再接更严格的结构化输出时，service 层接口不需要重写。
        """

        instruction = (
            "Return only JSON with keys summary and category. "
            'Use a short summary and a simple category such as "definition", '
            '"comparison", or "other". '
            f"Question: {question}"
        )
        raw_text = self.invoke(instruction)
        parsed = self._try_parse_json_object(raw_text)
        return {
            "question": question,
            "engine": "native",
            "mocked": self.mocked,
            "summary": str(parsed.get("summary", raw_text)).strip(),
            "category": str(parsed.get("category", "other")).strip(),
        }

    def _mock_response(self, prompt: str) -> str:
        """在未接真实模型前，返回可观察的占位结果。"""

        preview = " ".join(prompt.split())[:220]
        return (
            "Native mock response. "
            "This output proves the service layer and prompt pipeline are wired. "
            f"Prompt preview: {preview}"
        )

    def _build_chat_payload(self, prompt: str, stream: bool) -> dict[str, object]:
        """把上层 prompt 转成最小兼容 chat completions 请求体。"""

        return {
            "model": self.settings.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.settings.temperature,
            "max_tokens": self.settings.max_tokens,
            "stream": stream,
        }

    def _request_json(self, path: str, payload: dict[str, object]) -> dict[str, object]:
        """发送一次普通 JSON 请求并返回解析后的结果。"""

        response_text = self._send_request(path, payload)
        assert isinstance(response_text, str)
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Native provider returned invalid JSON.") from exc
        if not isinstance(data, dict):
            raise RuntimeError("Native provider returned an unexpected response shape.")
        return data

    def _stream_json(self, path: str, payload: dict[str, object]) -> Iterator[str]:
        """读取 SSE 风格流式响应，并提取 delta 文本。"""

        raw_stream = self._send_request(path, payload, stream=True)
        assert not isinstance(raw_stream, str)
        for raw_line in raw_stream:
            line = raw_line.decode("utf-8").strip()
            if not line or not line.startswith("data: "):
                continue
            event = line[6:]
            if event == "[DONE]":
                break
            try:
                chunk = json.loads(event)
            except json.JSONDecodeError:
                continue
            content = self._extract_stream_text(chunk)
            if content:
                yield content

    def _send_request(
        self,
        path: str,
        payload: dict[str, object],
        stream: bool = False,
    ) -> str | Iterator[bytes]:
        """发送底层 HTTP 请求。

        这是整个真实 native 路径的最底层：
        - 统一组装 URL、headers、body
        - 普通调用返回字符串
        - 流式调用返回逐行字节流
        """

        if not self.settings.api_key:
            raise RuntimeError("OPENAI_API_KEY or FOUNDATION_LAB_API_KEY is required for native calls.")

        body = json.dumps(payload).encode("utf-8")
        http_request = request.Request(
            url=f"{self.api_base_url}{path}",
            data=body,
            headers={
                "Authorization": f"Bearer {self.settings.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            response = request.urlopen(http_request, timeout=self.settings.timeout_seconds)
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Native provider request failed with status {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"Native provider request failed: {exc.reason}") from exc

        if stream:
            return iter(response)
        return response.read().decode("utf-8")

    def _extract_text(self, response: dict[str, object]) -> str:
        """从普通 chat completions 返回中提取文本内容。"""

        choices = response.get("choices")
        if not isinstance(choices, list) or not choices:
            raise RuntimeError("Native provider response did not contain choices.")
        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise RuntimeError("Native provider returned an invalid choice entry.")
        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise RuntimeError("Native provider response did not contain a message.")
        content = message.get("content", "")
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            text_parts: list[str] = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_value = item.get("text")
                    if isinstance(text_value, str):
                        text_parts.append(text_value)
            return "".join(text_parts).strip()
        raise RuntimeError("Native provider returned unsupported content format.")

    def _extract_stream_text(self, chunk: dict[str, object]) -> str:
        """从单个流式事件里提取增量文本。"""

        choices = chunk.get("choices")
        if not isinstance(choices, list) or not choices:
            return ""
        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            return ""
        delta = first_choice.get("delta")
        if not isinstance(delta, dict):
            return ""
        content = delta.get("content", "")
        return content if isinstance(content, str) else ""

    def _try_parse_json_object(self, raw_text: str) -> dict[str, str]:
        """尽量从模型文本中解析出一个简单 JSON 对象。"""

        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError:
            return {}
        if not isinstance(data, dict):
            return {}
        parsed: dict[str, str] = {}
        for key, value in data.items():
            parsed[str(key)] = str(value)
        return parsed
