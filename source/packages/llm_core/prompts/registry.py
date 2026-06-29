"""Load YAML prompt templates and render OpenAI-style messages."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

import yaml

from llm_core.prompts.template import PromptTemplate

_PROMPTS_ROOT = Path(__file__).resolve().parent
_PLACEHOLDER = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")


def _normalize_version(version: str) -> str:
    version = version.strip()
    if version.isdigit():
        return f"{version}.0.0"
    if re.fullmatch(r"\d+\.\d+", version):
        return f"{version}.0"
    return version


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Prompt YAML 格式错误：{path}")
    return data


def _parse_template(data: dict[str, Any], source: Path) -> PromptTemplate:
    for key in ("prompt_id", "version", "model_config_ref", "system", "user"):
        if key not in data:
            raise ValueError(f"Prompt YAML 缺少字段 {key!r}：{source}")
    return PromptTemplate(
        prompt_id=str(data["prompt_id"]),
        version=str(data["version"]),
        model_config_ref=str(data["model_config_ref"]),
        system=str(data["system"]),
        user=str(data["user"]),
    )


def _iter_prompt_files() -> list[Path]:
    files: list[Path] = []
    for subdir in _PROMPTS_ROOT.iterdir():
        if subdir.is_dir() and not subdir.name.startswith("_"):
            files.extend(sorted(subdir.glob("*.yaml")))
    return files


def get_prompt(prompt_id: str, version: Optional[str] = None) -> PromptTemplate:
    """Load a prompt template by id and version (defaults to highest version)."""
    candidates: list[PromptTemplate] = []
    for path in _iter_prompt_files():
        data = _load_yaml(path)
        if data.get("prompt_id") != prompt_id:
            continue
        candidates.append(_parse_template(data, path))

    if not candidates:
        raise KeyError(f"未找到 prompt_id={prompt_id!r}")

    if version is None:
        return max(candidates, key=lambda t: _normalize_version(t.version))

    target = _normalize_version(version)
    for tpl in candidates:
        if _normalize_version(tpl.version) == target:
            return tpl
    available = ", ".join(sorted({t.version for t in candidates}))
    raise KeyError(f"未找到 {prompt_id} 版本 {version!r}，可选：{available}")


def list_prompt_versions(prompt_id: str) -> list[str]:
    versions: list[str] = []
    for path in _iter_prompt_files():
        data = _load_yaml(path)
        tpl = _parse_template(data, path)
        if tpl.prompt_id == prompt_id:
            versions.append(tpl.version)
    return sorted(versions, key=_normalize_version)


def _substitute(template: str, variables: dict[str, str]) -> str:
    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        return variables.get(key, "")

    return _PLACEHOLDER.sub(repl, template)


def render_prompt(
    template: PromptTemplate,
    variables: dict[str, str],
) -> list[dict[str, str]]:
    """Render template + variables into Chat API messages."""
    merged = {k: (v if v is not None else "") for k, v in variables.items()}
    system = _substitute(template.system, merged).strip()
    user = _substitute(template.user, merged).strip()
    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    if user:
        messages.append({"role": "user", "content": user})
    if not messages:
        raise ValueError(f"Prompt {template.ref} 渲染后 messages 为空")
    return messages
