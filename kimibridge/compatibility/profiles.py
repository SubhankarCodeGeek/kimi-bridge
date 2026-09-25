from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProviderProfile:
    name: str
    supports_developer_role: bool = False
    developer_role_target: str = "system"
    supported_roles: frozenset[str] = frozenset({"system", "user", "assistant", "tool"})
    unsupported_parameters: frozenset[str] = frozenset()
    default_base_url: str = ""
    default_models: tuple[dict[str, Any], ...] = ()


KIMI_PROFILE = ProviderProfile(
    name="kimi",
    supports_developer_role=False,
    developer_role_target="system",
    supported_roles=frozenset({"system", "user", "assistant", "tool"}),
    unsupported_parameters=frozenset({"metadata", "parallel_tool_calls", "store"}),
    default_base_url="https://api.moonshot.ai",
    default_models=(
        {"id": "kimi-k3", "object": "model", "owned_by": "moonshot"},
        {"id": "kimi-latest", "object": "model", "owned_by": "moonshot"},
        {"id": "kimi-k1.5", "object": "model", "owned_by": "moonshot"},
        {"id": "kimi-k2", "object": "model", "owned_by": "moonshot"},
        {"id": "moonshot-v1-auto", "object": "model", "owned_by": "moonshot"},
        {"id": "moonshot-v1-8k", "object": "model", "owned_by": "moonshot"},
        {"id": "moonshot-v1-32k", "object": "model", "owned_by": "moonshot"},
        {"id": "moonshot-v1-128k", "object": "model", "owned_by": "moonshot"},
        {"id": "moonshot-v1-8k-vision-preview", "object": "model", "owned_by": "moonshot"},
        {"id": "moonshot-v1-32k-vision-preview", "object": "model", "owned_by": "moonshot"},
        {"id": "moonshot-v1-128k-vision-preview", "object": "model", "owned_by": "moonshot"},
    ),
)

DEEPSEEK_PROFILE = ProviderProfile(
    name="deepseek",
    supports_developer_role=False,
    developer_role_target="system",
    supported_roles=frozenset({"system", "user", "assistant", "tool", "latest_reminder"}),
    unsupported_parameters=frozenset({"metadata", "store"}),
    default_base_url="https://api.deepseek.com",
    default_models=(
        {"id": "deepseek-chat", "object": "model", "owned_by": "deepseek"},
        {"id": "deepseek-reasoner", "object": "model", "owned_by": "deepseek"},
        {"id": "deepseek-v3", "object": "model", "owned_by": "deepseek"},
        {"id": "deepseek-v3-pro", "object": "model", "owned_by": "deepseek"},
        {"id": "deepseek-r1", "object": "model", "owned_by": "deepseek"},
        {"id": "deepseek-flash", "object": "model", "owned_by": "deepseek"},
        {"id": "deepseek-coder", "object": "model", "owned_by": "deepseek"},
    ),
)

OPENAI_PROFILE = ProviderProfile(
    name="openai",
    supports_developer_role=True,
    developer_role_target="developer",
    supported_roles=frozenset({"system", "developer", "user", "assistant", "tool", "function"}),
    unsupported_parameters=frozenset(),
    default_base_url="https://api.openai.com",
    default_models=(
        {"id": "gpt-4o", "object": "model", "owned_by": "openai"},
        {"id": "gpt-4o-mini", "object": "model", "owned_by": "openai"},
        {"id": "o1", "object": "model", "owned_by": "openai"},
        {"id": "o3-mini", "object": "model", "owned_by": "openai"},
    ),
)

GENERIC_PROFILE = ProviderProfile(
    name="generic",
    supports_developer_role=False,
    developer_role_target="system",
    supported_roles=frozenset({"system", "user", "assistant", "tool"}),
    unsupported_parameters=frozenset({"metadata", "parallel_tool_calls", "store"}),
    default_base_url="",
    default_models=(
        {"id": "default-model", "object": "model", "owned_by": "generic"},
    ),
)

PROFILES: dict[str, ProviderProfile] = {
    "kimi": KIMI_PROFILE,
    "moonshot": KIMI_PROFILE,
    "deepseek": DEEPSEEK_PROFILE,
    "openai": OPENAI_PROFILE,
    "generic": GENERIC_PROFILE,
}


def get_provider_profile(name_or_alias: str | None) -> ProviderProfile:
    if not name_or_alias:
        return KIMI_PROFILE
    key = name_or_alias.strip().lower()
    return PROFILES.get(key, GENERIC_PROFILE)


def detect_provider(
    model: str | None = None,
    base_url: str | None = None,
    configured_provider: str | None = None,
    headers: dict[str, str] | None = None,
) -> ProviderProfile:
    """
    Detect provider profile based on explicit headers, configuration, model name heuristic,
    or upstream base URL heuristic.
    """
    if headers:
        for k, v in headers.items():
            if k.lower() in {"x-bridge-provider", "x-provider"}:
                return get_provider_profile(v)

    if configured_provider and configured_provider.lower() not in {"auto", "default"}:
        return get_provider_profile(configured_provider)

    if model:
        m = model.lower()
        if "deepseek" in m:
            return DEEPSEEK_PROFILE
        if "kimi" in m or "moonshot" in m:
            return KIMI_PROFILE
        if m.startswith("gpt-") or m.startswith("o1") or m.startswith("o3"):
            return OPENAI_PROFILE

    if base_url:
        u = base_url.lower()
        if "deepseek.com" in u:
            return DEEPSEEK_PROFILE
        if "moonshot.ai" in u:
            return KIMI_PROFILE
        if "openai.com" in u:
            return OPENAI_PROFILE

    if configured_provider:
        return get_provider_profile(configured_provider)

    return KIMI_PROFILE
