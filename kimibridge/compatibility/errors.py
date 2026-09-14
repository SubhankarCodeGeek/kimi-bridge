from __future__ import annotations

import json
from typing import Any


def normalize_error(status: int, body: bytes) -> dict[str, Any]:
    message = "Upstream error"
    error_type = "upstream_error"
    code = None

    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        payload = None

    if isinstance(payload, dict):
        raw_error = payload.get("error")
        if isinstance(raw_error, dict):
            message = str(raw_error.get("message", message))
            error_type = str(raw_error.get("type", error_type))
            code = raw_error.get("code")
        elif isinstance(raw_error, str):
            message = raw_error
        elif "message" in payload:
            message = str(payload["message"])

    return {
        "error": {
            "message": message,
            "type": error_type,
            "param": None,
            "code": code or f"upstream_http_{status}",
        }
    }
