from __future__ import annotations

from copy import deepcopy
from typing import Any

from kimibridge.compatibility.profiles import KIMI_PROFILE, ProviderProfile


def normalize_roles(
    payload: dict[str, Any],
    mode: str = "compatible",
    profile: ProviderProfile | None = None,
) -> dict[str, Any]:
    if mode == "passthrough":
        return deepcopy(payload)

    active_profile = profile or KIMI_PROFILE

    # If the provider natively supports the developer role, preserve it
    if active_profile.supports_developer_role:
        return deepcopy(payload)

    normalized = deepcopy(payload)
    messages = normalized.get("messages")
    if not isinstance(messages, list):
        return normalized

    target_role = active_profile.developer_role_target
    for message in messages:
        if isinstance(message, dict) and message.get("role") == "developer":
            message["role"] = target_role

    return normalized
