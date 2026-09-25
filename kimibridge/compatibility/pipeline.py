from __future__ import annotations

from typing import Any

from kimibridge.compatibility.parameters import normalize_parameters
from kimibridge.compatibility.profiles import (
    ProviderProfile,
    detect_provider,
    get_provider_profile,
)
from kimibridge.compatibility.roles import normalize_roles


VALID_MODES = {"compatible", "passthrough", "strict"}


def normalize_request(
    payload: dict[str, Any],
    mode: str = "compatible",
    provider: str | ProviderProfile | None = None,
    base_url: str | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    if mode not in VALID_MODES:
        raise ValueError(f"Unsupported compatibility mode: {mode}")

    if isinstance(provider, ProviderProfile):
        profile = provider
    else:
        profile = detect_provider(
            model=payload.get("model") if isinstance(payload, dict) else None,
            base_url=base_url,
            configured_provider=provider,
            headers=headers,
        )

    normalized = normalize_roles(payload, mode=mode, profile=profile)
    normalized = normalize_parameters(normalized, mode=mode, profile=profile)
    return normalized
