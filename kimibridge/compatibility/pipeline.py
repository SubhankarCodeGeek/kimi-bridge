from __future__ import annotations

from typing import Any

from kimibridge.compatibility.parameters import normalize_parameters
from kimibridge.compatibility.roles import normalize_roles


VALID_MODES = {"compatible", "passthrough", "strict"}


def normalize_request(payload: dict[str, Any], mode: str = "compatible") -> dict[str, Any]:
    if mode not in VALID_MODES:
        raise ValueError(f"Unsupported compatibility mode: {mode}")

    normalized = normalize_roles(payload, mode)
    normalized = normalize_parameters(normalized, mode)
    return normalized
