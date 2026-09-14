from __future__ import annotations

from copy import deepcopy
from typing import Any


def normalize_roles(payload: dict[str, Any], mode: str = "compatible") -> dict[str, Any]:
    if mode == "passthrough":
        return deepcopy(payload)

    normalized = deepcopy(payload)
    messages = normalized.get("messages")
    if not isinstance(messages, list):
        return normalized

    for message in messages:
        if isinstance(message, dict) and message.get("role") == "developer":
            message["role"] = "system"

    return normalized
