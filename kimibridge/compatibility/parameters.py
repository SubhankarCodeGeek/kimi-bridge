from __future__ import annotations

from copy import deepcopy
from typing import Any


UNSUPPORTED_PARAMETERS = {
    "metadata",
    "parallel_tool_calls",
    "store",
}


def normalize_parameters(payload: dict[str, Any], mode: str = "compatible") -> dict[str, Any]:
    if mode in {"passthrough", "strict"}:
        return deepcopy(payload)

    normalized = deepcopy(payload)
    for key in UNSUPPORTED_PARAMETERS:
        normalized.pop(key, None)
    return normalized
