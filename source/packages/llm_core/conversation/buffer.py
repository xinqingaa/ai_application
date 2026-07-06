"""Minimal conversation history primitives."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

MessageRole = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class ConversationMessage:
    role: MessageRole
    content: str

    def to_chat_message(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


class ConversationBuffer:
    """Small in-memory chat history with an optional rolling window."""

    def __init__(self, *, system_prompt: Optional[str] = None, max_messages: Optional[int] = None) -> None:
        self.max_messages = max_messages
        self._messages: list[ConversationMessage] = []
        if system_prompt:
            self.add("system", system_prompt)

    def add(self, role: MessageRole, content: str) -> None:
        text = content.strip()
        if not text:
            return
        self._messages.append(ConversationMessage(role=role, content=text))
        self._trim()

    def add_user(self, content: str) -> None:
        self.add("user", content)

    def add_assistant(self, content: str) -> None:
        self.add("assistant", content)

    def add_system(self, content: str) -> None:
        self.add("system", content)

    def to_messages(self) -> list[dict[str, str]]:
        return [message.to_chat_message() for message in self._messages]

    @property
    def message_count(self) -> int:
        return len(self._messages)

    def _trim(self) -> None:
        if self.max_messages is None or len(self._messages) <= self.max_messages:
            return
        system_messages = [msg for msg in self._messages if msg.role == "system"]
        non_system = [msg for msg in self._messages if msg.role != "system"]
        keep_system = system_messages[:1]
        keep_non_system = non_system[-max(self.max_messages - len(keep_system), 0):]
        self._messages = keep_system + keep_non_system
