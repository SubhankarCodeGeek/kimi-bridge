from __future__ import annotations

from dataclasses import dataclass
import json
import socket
from urllib.error import URLError
from urllib.request import urlopen


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
    except PermissionError:
        return None
    except OSError:
        return False


def is_kimibridge_running(host: str, port: int, timeout: float = 0.5) -> bool:
    try:
        with urlopen(f"http://{host}:{port}/health", timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except (OSError, URLError, TimeoutError):
        return False

    if response.status != 200:
        return False

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return False

    return payload.get("service") == "kimibridge"


def find_available_port(host: str, start_port: int, limit: int = 10) -> int | None:
    for port in range(start_port, start_port + limit + 1):
        if check_port_available(host, port) is True:
            return port
    return None


def resolve_port(
    host: str,
    requested_port: int,
    *,
    auto_port: bool = False,
    search_limit: int = 10,
) -> PortResolution:
    availability = check_port_available(host, requested_port)

    if availability is True:
        return PortResolution(
            host=host,
            requested_port=requested_port,
            selected_port=requested_port,
            status="available",
            message=f"Port {requested_port} is available.",
        )

    if is_kimibridge_running(host, requested_port):
        return PortResolution(
            host=host,
            requested_port=requested_port,
            selected_port=requested_port,
            status="already_running",
            message=f"KimiBridge is already running on port {requested_port}.",
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

    fallback = find_available_port(host, requested_port + 1, search_limit)
    if fallback is None:
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

    return PortResolution(
        host=host,
        requested_port=requested_port,
        selected_port=fallback,
        status="fallback",
        message=f"Port {requested_port} is unavailable. Selected port {fallback}.",
    )
