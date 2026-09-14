from __future__ import annotations


DEFAULT_MODELS = [
    {
        "id": "kimi-k3",
        "object": "model",
        "owned_by": "moonshot",
    }
]


def normalized_models() -> dict[str, object]:
    return {
        "object": "list",
        "data": DEFAULT_MODELS,
    }
