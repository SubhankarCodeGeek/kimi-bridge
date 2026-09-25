from __future__ import annotations

import json
from typing import Any


def normalize_error(status: int, body: bytes) -> dict[str, Any]:
    message = "Upstream error"
    error_type = "invalid_request_error" if status in {400, 422} else "upstream_error"
    code = "invalid_parameters" if status == 422 else None

    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        payload = None

    if isinstance(payload, dict):
        raw_error = payload.get("error")
        if isinstance(raw_error, dict):
            message = str(raw_error.get("message", message))
            error_type = str(raw_error.get("type", error_type))
            code = raw_error.get("code", code)
        elif isinstance(raw_error, str):
            message = raw_error
        elif "detail" in payload:
            raw_detail = payload["detail"]
            if isinstance(raw_detail, str):
                message = raw_detail
            elif isinstance(raw_detail, list):
                parts = []
                for item in raw_detail:
                    if isinstance(item, dict):
                        loc = ".".join(str(p) for p in item.get("loc", []))
                        msg = item.get("msg", "")
                        parts.append(f"{loc}: {msg}" if loc else str(msg))
                    else:
                        parts.append(str(item))
                message = "; ".join(parts) if parts else "Invalid request parameters"
            else:
                message = str(raw_detail)
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
