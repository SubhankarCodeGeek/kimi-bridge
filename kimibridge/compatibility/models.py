from __future__ import annotations

from typing import Any

from kimibridge.compatibility.profiles import (
    DEEPSEEK_PROFILE,
    KIMI_PROFILE,
    OPENAI_PROFILE,
    ProviderProfile,
    get_provider_profile,
)

DEFAULT_MODELS = list(KIMI_PROFILE.default_models)


def normalized_models(provider: str | ProviderProfile | None = None) -> dict[str, Any]:
    if provider is not None:
        if isinstance(provider, str) and provider.strip().lower() in {"all", "both"}:
            combined: list[dict[str, Any]] = []
            seen_ids: set[str] = set()
            for profile in (KIMI_PROFILE, DEEPSEEK_PROFILE, OPENAI_PROFILE):
                for m in profile.default_models:
                    if m["id"] not in seen_ids:
                        seen_ids.add(m["id"])
                        combined.append(m)
            return {
                "object": "list",
                "data": combined,
            }

        profile = (
            provider
            if isinstance(provider, ProviderProfile)
            else get_provider_profile(provider)
        )
        if profile.default_models:
            return {
                "object": "list",
                "data": list(profile.default_models),
            }

    return {
        "object": "list",
        "data": DEFAULT_MODELS,
    }
