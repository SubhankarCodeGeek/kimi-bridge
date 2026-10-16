from __future__ import annotations

from dataclasses import dataclass
import json
import socket
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen


DEFAULT_PORT_DEEPSEEK = 5001
DEFAULT_PORT_KIMI = 5002


def get_default_port(provider: str | None = None) -> int:
    p = (provider or "").strip().lower()
    if p in {"moonshot", "kimi"}:
        return DEFAULT_PORT_KIMI
    return DEFAULT_PORT_DEEPSEEK


@dataclass(frozen=True)
class PortResolution:
    host: str
    requested_port: int
    selected_port: int
    status: str
    message: str

    @property
    def changed(self) -> bool:
        return self.requested_port != self.selected_port


def is_port_available(host: str, port: int) -> bool:
    status = check_port_available(host, port)
    return status is True


def check_port_available(host: str, port: int) -> bool | None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((host, port))
            return True
    except PermissionError as exc:
        if getattr(exc, "winerror", None) == 10013 or getattr(exc, "errno", None) in (13, 10013):
            return False
        return None
    except OSError:
        return False


def _normalize_provider(provider: str | None) -> str:
    p = (provider or "").strip().lower()
    if p in {"moonshot"}:
        return "kimi"
    return p


def _detect_provider_from_models(host: str, port: int, timeout: float = 0.5) -> str | None:
    try:
        with urlopen(f"http://{host}:{port}/v1/models", timeout=timeout) as response:
            if response.status != 200:
                return None
            body = response.read().decode("utf-8")
        data = json.loads(body)
        models = [str(m.get("id", "")).lower() for m in data.get("data", [])]
        has_deepseek = any("deepseek" in m for m in models)
        has_kimi = any("kimi" in m or "moonshot" in m for m in models)
        if has_deepseek and has_kimi:
            return "all"
        if has_deepseek:
            return "deepseek"
        if has_kimi:
            return "kimi"
    except Exception:
        pass
    return None


def get_kimibridge_status(host: str, port: int, timeout: float = 0.5) -> dict[str, Any] | None:
    try:
        with urlopen(f"http://{host}:{port}/health", timeout=timeout) as response:
            if response.status != 200:
                return None
            body = response.read().decode("utf-8")
    except (OSError, URLError, TimeoutError):
        return None

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return None

    if isinstance(payload, dict) and payload.get("service") in {"studiorelay", "kimibridge"}:
        if not payload.get("provider"):
            detected = _detect_provider_from_models(host, port, timeout=timeout)
            if detected:
                payload["provider"] = detected
        return payload
    return None


def get_service_status(host: str, port: int, timeout: float = 0.5) -> dict[str, Any] | None:
    return get_kimibridge_status(host, port, timeout)


get_studiorelay_status = get_service_status


def is_service_running(host: str, port: int, timeout: float = 0.5) -> bool:
    return get_service_status(host, port, timeout) is not None


is_kimibridge_running = is_service_running
is_studiorelay_running = is_service_running


def find_available_port_for_provider(
    host: str,
    start_port: int,
    limit: int = 10,
    target_provider: str | None = None,
) -> tuple[int, str] | None:
    target = _normalize_provider(target_provider)
    for port in range(start_port, start_port + limit + 1):
        if check_port_available(host, port) is True:
            return (port, "available")
        info = get_kimibridge_status(host, port)
        if info and target:
            running = _normalize_provider(info.get("provider"))
            if running == target:
                return (port, "already_running")
    return None


def find_available_port(host: str, start_port: int, limit: int = 10) -> int | None:
    res = find_available_port_for_provider(host, start_port, limit=limit)
    return res[0] if res is not None else None


def resolve_port(
    host: str,
    requested_port: int,
    *,
    auto_port: bool = False,
    search_limit: int = 10,
    target_provider: str | None = None,
) -> PortResolution:
    target = _normalize_provider(target_provider)
    availability = check_port_available(host, requested_port)

    if availability is True:
        return PortResolution(
            host=host,
            requested_port=requested_port,
            selected_port=requested_port,
            status="available",
            message=f"Port {requested_port} is available.",
        )

    running_info = get_kimibridge_status(host, requested_port)
    if running_info:
        running_provider = _normalize_provider(running_info.get("provider"))
        if target:
            if running_provider and target == running_provider:
                return PortResolution(
                    host=host,
                    requested_port=requested_port,
                    selected_port=requested_port,
                    status="already_running",
                    message=f"StudioRelay ({running_provider}) is already running on port {requested_port}.",
                )

            provider_desc = f"hosting '{running_provider}'" if running_provider else "already in use"
            if not auto_port:
                return PortResolution(
                    host=host,
                    requested_port=requested_port,
                    selected_port=requested_port,
                    status="conflict",
                    message=(
                        f"Port {requested_port} is {provider_desc}. "
                        f"Use --auto-port or choose a different port for '{target_provider}'."
                    ),
                )

            candidate = find_available_port_for_provider(
                host,
                requested_port + 1,
                limit=search_limit,
                target_provider=target,
            )
            if candidate is None:
                return PortResolution(
                    host=host,
                    requested_port=requested_port,
                    selected_port=requested_port,
                    status="no_available_port",
                    message=(
                        f"Port {requested_port} is {provider_desc} and no available port "
                        f"was found in the next {search_limit} ports."
                    ),
                )

            selected_port, port_status = candidate
            current_desc = f"currently hosting '{running_provider}'" if running_provider else "currently in use"
            return PortResolution(
                host=host,
                requested_port=requested_port,
                selected_port=selected_port,
                status="already_running" if port_status == "already_running" else "fallback",
                message=(
                    f"Port {requested_port} is {current_desc}. "
                    f"Selected port {selected_port} for '{target_provider}' to prevent conflict."
                ),
            )

        return PortResolution(
            host=host,
            requested_port=requested_port,
            selected_port=requested_port,
            status="already_running",
            message=f"StudioRelay is already running on port {requested_port}.",
        )

    if availability is None:
        return PortResolution(
            host=host,
            requested_port=requested_port,
            selected_port=requested_port,
            status="unknown",
            message=(
                f"Port {requested_port} could not be checked in this environment. "
                "Run doctor in a normal user shell or choose a port explicitly."
            ),
        )

    if not auto_port:
        return PortResolution(
            host=host,
            requested_port=requested_port,
            selected_port=requested_port,
            status="conflict",
            message=(
                f"Port {requested_port} is already in use by another process. "
                "Use --auto-port or choose a different port."
            ),
        )

    candidate = find_available_port_for_provider(
        host,
        requested_port + 1,
        limit=search_limit,
        target_provider=target,
    )
    if candidate is None:
        return PortResolution(
            host=host,
            requested_port=requested_port,
            selected_port=requested_port,
            status="no_available_port",
            message=(
                f"Port {requested_port} is unavailable and no fallback port was "
                f"found in the next {search_limit} ports."
            ),
        )

    fallback, fallback_status = candidate
    return PortResolution(
        host=host,
        requested_port=requested_port,
        selected_port=fallback,
        status="already_running" if fallback_status == "already_running" else "fallback",
        message=f"Port {requested_port} is unavailable. Selected port {fallback}.",
    )
