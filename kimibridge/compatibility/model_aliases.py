from __future__ import annotations

from copy import deepcopy
from typing import Any

from kimibridge.compatibility.profiles import ProviderProfile


DEEPSEEK_MODEL_ALIASES = {
    "deepseek-chat": ("deepseek-flash", None),
    "deepseek-coder": ("deepseek-flash", None),
    "deepseek-v3": ("deepseek-flash", None),
    "deepseek-v3.1": ("deepseek-flash", None),
    "deepseek-v3.2": ("deepseek-flash", None),
    "deepseek-v4-flash": ("deepseek-flash", None),
    "deepseek-v4.1-flash": ("deepseek-flash", None),
    "deepseek-reasoner": ("deepseek-flash", "high"),
    "deepseek-r1": ("deepseek-flash", "high"),
    "deepseek-v3-pro": ("deepseek-v4-pro", None),
    "deepseek-v3.1-pro": ("deepseek-v4-pro", None),
    "deepseek-v3.2-pro": ("deepseek-v4-pro", None),
}


def normalize_model_aliases(
    payload: dict[str, Any],
    profile: ProviderProfile,
) -> dict[str, Any]:
    normalized = deepcopy(payload)
    if profile.name != "deepseek":
        return normalized

    model = normalized.get("model")
    if not isinstance(model, str):
        return normalized

    upstream_model, default_effort = DEEPSEEK_MODEL_ALIASES.get(model.lower(), (None, None))
    if upstream_model is None:
        return normalized

    normalized["model"] = upstream_model
    if default_effort is not None and "reasoning_effort" not in normalized:
        normalized["reasoning_effort"] = default_effort
    return normalized
