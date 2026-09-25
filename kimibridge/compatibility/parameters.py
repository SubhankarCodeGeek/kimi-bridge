from __future__ import annotations

from copy import deepcopy
from typing import Any

from kimibridge.compatibility.profiles import KIMI_PROFILE, ProviderProfile

UNSUPPORTED_PARAMETERS = {
    "metadata",
    "parallel_tool_calls",
    "store",
}


def normalize_parameters(
    payload: dict[str, Any],
    mode: str = "compatible",
    profile: ProviderProfile | None = None,
) -> dict[str, Any]:
    if mode in {"passthrough", "strict"}:
        return deepcopy(payload)

    active_profile = profile or KIMI_PROFILE
    keys_to_remove = active_profile.unsupported_parameters if active_profile else UNSUPPORTED_PARAMETERS

    normalized = deepcopy(payload)
    for key in keys_to_remove:
        normalized.pop(key, None)
    return normalized
