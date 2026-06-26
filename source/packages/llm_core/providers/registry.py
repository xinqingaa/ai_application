"""Load models.yaml and resolve config_ref to ModelConfig."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml

from llm_core.config import CapabilityTags, ModelConfig, ModelRole
from llm_core.providers.openai_compat import OpenAICompatProvider

_ENV_PATTERN = re.compile(r"\$\{([^}]+)\}")


def _resolve_env_placeholders(value: Any) -> Any:
    if isinstance(value, str):
        def repl(match: re.Match[str]) -> str:
            expr = match.group(1)
            if ":-" in expr:
                name, default = expr.split(":-", 1)
                return os.environ.get(name, default)
            return os.environ.get(expr, "")

        return _ENV_PATTERN.sub(repl, value)
    if isinstance(value, dict):
        return {k: _resolve_env_placeholders(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_env_placeholders(v) for v in value]
    return value


def _empty_to_none(value: Any) -> Any:
    if value == "":
        return None
    return value


class ConfigRegistry:
    def __init__(self, configs: dict[str, ModelConfig]) -> None:
        self._configs = configs
        self._providers = {
            "openai_compat": OpenAICompatProvider(),
        }

    @classmethod
    def from_yaml_path(cls, path: Path) -> ConfigRegistry:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        raw = _resolve_env_placeholders(raw)
        configs: dict[str, ModelConfig] = {}

        for section, entries in raw.items():
            if not isinstance(entries, dict):
                continue
            for name, entry in entries.items():
                if not isinstance(entry, dict):
                    continue
                config_ref = f"{section}.{name}"
                base_url = _empty_to_none(entry.get("base_url"))
                configs[config_ref] = ModelConfig(
                    config_ref=config_ref,
                    role=entry.get("role", section),  # type: ignore[arg-type]
                    provider=entry["provider"],
                    model=entry["model"],
                    api_key_env=entry["api_key_env"],
                    base_url=base_url,
                    default_params=dict(entry.get("default_params") or {}),
                    capabilities=CapabilityTags.from_dict(entry.get("capabilities")),
                )
        return cls(configs)

    @classmethod
    def default(cls) -> ConfigRegistry:
        path = Path(__file__).resolve().parent.parent / "config" / "models.yaml"
        return cls.from_yaml_path(path)

    def get_config(self, config_ref: str) -> ModelConfig:
        if config_ref not in self._configs:
            known = ", ".join(sorted(self._configs))
            raise KeyError(f"未知 config_ref: {config_ref!r}，可选: {known}")
        return self._configs[config_ref]

    def list_config_refs(self, role: ModelRole | None = None) -> list[str]:
        if role is None:
            return sorted(self._configs)
        return sorted(ref for ref, cfg in self._configs.items() if cfg.role == role)

    def get_provider(self, provider_name: str) -> OpenAICompatProvider:
        provider = self._providers.get(provider_name)
        if provider is None:
            raise KeyError(f"未知 provider: {provider_name!r}")
        return provider
