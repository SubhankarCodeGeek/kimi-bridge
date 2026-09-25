from __future__ import annotations

from typing import Any

from kimibridge.compatibility.profiles import (
    DEEPSEEK_PROFILE,
    KIMI_PROFILE,
    OPENAI_PROFILE,
    ProviderProfile,
    detect_provider,
    get_provider_profile,
)

DEFAULT_MODELS = list(KIMI_PROFILE.default_models)


def normalized_models(
    provider: str | ProviderProfile | None = None,
    base_url: str | None = None,
) -> dict[str, Any]:
    target_provider = provider
    if (
        target_provider is None
        or (isinstance(target_provider, str) and target_provider.strip().lower() in {"auto", "default"})
    ) and base_url:
        target_provider = detect_provider(base_url=base_url)

    if target_provider is not None:
        if isinstance(target_provider, str) and target_provider.strip().lower() in {"all", "both"}:
            combined: list[dict[str, Any]] = []
            seen_ids: set[str] = set()
            profiles_order = (
                (DEEPSEEK_PROFILE, KIMI_PROFILE, OPENAI_PROFILE)
                if (base_url and "deepseek" in base_url.lower())
                else (KIMI_PROFILE, DEEPSEEK_PROFILE, OPENAI_PROFILE)
            )
            for profile in profiles_order:
                for m in profile.default_models:
                    if m["id"] not in seen_ids:
                        seen_ids.add(m["id"])
                        combined.append(m)
            return {
                "object": "list",
                "data": combined,
            }

        profile = (
            target_provider
            if isinstance(target_provider, ProviderProfile)
            else get_provider_profile(target_provider)
        )
        if profile.default_models:
            return {
                "object": "list",
                "data": list(profile.default_models),
            }

    if base_url:
        detected = detect_provider(base_url=base_url)
        if detected.default_models and detected.name != "generic":
            return {
                "object": "list",
                "data": list(detected.default_models),
            }

    return {
        "object": "list",
        "data": DEFAULT_MODELS,
    }
