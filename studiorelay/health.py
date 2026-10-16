from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.error import URLError
from urllib.request import urlopen


@dataclass(frozen=True)
class HealthStatus:
    ok: bool
    status: str
    message: str
    payload: dict[str, object] | None = None


def check_health(host: str, port: int, timeout: float = 1.0) -> HealthStatus:
    url = f"http://{host}:{port}/health"
    try:
        with urlopen(url, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except (OSError, URLError, TimeoutError) as exc:
        return HealthStatus(
            ok=False,
            status="unreachable",
            message=f"Health endpoint is not reachable: {exc}",
        )

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return HealthStatus(
            ok=False,
            status="invalid_response",
            message="Health endpoint returned invalid JSON.",
        )

    if response.status == 200 and payload.get("service") in {"studiorelay", "kimibridge"}:
        svc = payload.get("service", "studiorelay")
        brand = "StudioRelay" if svc == "studiorelay" else "KimiBridge"
        return HealthStatus(
            ok=True,
            status="healthy",
            message=f"{brand} health endpoint is OK.",
            payload=payload,
        )

    return HealthStatus(
        ok=False,
        status="unexpected_response",
        message="Health endpoint did not identify itself as StudioRelay or KimiBridge.",
        payload=payload,
    )
