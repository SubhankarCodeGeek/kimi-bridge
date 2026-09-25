from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from typing import Any
from urllib.parse import urlparse

from kimibridge import __version__
from kimibridge.compatibility import normalize_error, normalize_request, normalized_models
from kimibridge.config import AppConfig
from kimibridge.upstream import KimiUpstreamClient, UpstreamHttpError, UpstreamUnavailable


class KimiBridgeHandler(BaseHTTPRequestHandler):
    server_version = "KimiBridge"

    def log_message(self, format: str, *args: Any) -> None:
        # Avoid logging request headers; Authorization must never be printed.
        print(f"{self.address_string()} - {format % args}")

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._add_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:
        path = urlparse(self.path).path

        if path == "/health":
            self._send_json(
                200,
                {
                    "ok": True,
                    "service": "kimibridge",
                    "version": __version__,
                },
            )
            return

        if path == "/v1/models":
            config: AppConfig = getattr(self.server, "config", AppConfig())
            auth_header = self.headers.get("Authorization")
            if auth_header:
                headers = self._forward_headers()
                clients_to_try = [KimiUpstreamClient(config.kimi.base_url)]
                if config.kimi.fallback_base_url and config.kimi.fallback_base_url.rstrip("/") != config.kimi.base_url.rstrip("/"):
                    clients_to_try.append(KimiUpstreamClient(config.kimi.fallback_base_url))

                for client in clients_to_try:
                    try:
                        upstream_resp = client.list_models(headers)
                        if upstream_resp.status == 200:
                            upstream_data = json.loads(upstream_resp.body.decode("utf-8"))
                            if isinstance(upstream_data, dict) and "data" in upstream_data and isinstance(upstream_data["data"], list):
                                upstream_ids = {
                                    m["id"] for m in upstream_data["data"] if isinstance(m, dict) and "id" in m
                                }
                                default_models_data = normalized_models(config.provider).get("data", [])
                                merged = list(upstream_data["data"])
                                for m in default_models_data:
                                    if isinstance(m, dict) and m.get("id") not in upstream_ids:
                                        merged.append(m)
                                self._send_json(200, {"object": "list", "data": merged})
                                return
                    except Exception:
                        pass

            self._send_json(200, normalized_models(config.provider))
            return

        self._send_json(404, {"error": {"message": "Not found"}})

    def do_POST(self) -> None:
        path = urlparse(self.path).path

        if path != "/v1/chat/completions":
            self._send_json(404, {"error": {"message": "Not found"}})
            return

        config: AppConfig = self.server.config  # type: ignore[attr-defined]
        try:
            payload = self._read_json()
        except ValueError as exc:
            self._send_json(400, {"error": {"message": str(exc)}})
            return

        headers = self._forward_headers()
        try:
            upstream_payload = normalize_request(
                payload,
                mode=config.compatibility.mode,
                provider=config.provider,
                base_url=config.kimi.base_url,
                headers=headers,
            )
        except ValueError as exc:
            self._send_json(500, {"error": {"message": str(exc)}})
            return
        clients_to_try = [KimiUpstreamClient(config.kimi.base_url)]
        if config.kimi.fallback_base_url and config.kimi.fallback_base_url.rstrip("/") != config.kimi.base_url.rstrip("/"):
            clients_to_try.append(KimiUpstreamClient(config.kimi.fallback_base_url))

        if upstream_payload.get("stream") is True:
            for idx, client in enumerate(clients_to_try):
                try:
                    with client.stream_chat_completions(headers, upstream_payload) as stream_resp:
                        content_type = stream_resp.headers.get("Content-Type", "text/event-stream")
                        self.send_response(stream_resp.status)
                        self._add_cors_headers()
                        self.send_header("Content-Type", content_type)
                        self.send_header("Cache-Control", "no-cache")
                        self.send_header("Connection", "close")
                        self.end_headers()

                        try:
                            for chunk in stream_resp.iter_chunks():
                                self.wfile.write(chunk)
                                self.wfile.flush()
                        except (BrokenPipeError, ConnectionResetError, OSError):
                            pass
                        finally:
                            self.close_connection = True
                        return
                except (UpstreamUnavailable, UpstreamHttpError) as exc:
                    is_unavailable = isinstance(exc, UpstreamUnavailable)
                    is_5xx = isinstance(exc, UpstreamHttpError) and exc.status >= 500
                    if (is_unavailable or is_5xx) and idx < len(clients_to_try) - 1:
                        print(f"Primary upstream ({client.base_url}) failed: {exc}. Trying fallback ({clients_to_try[idx + 1].base_url})...")
                        continue

                    if isinstance(exc, UpstreamHttpError):
                        self._send_json(exc.status, normalize_error(exc.status, exc.body))
                        return
                    self._send_json(
                        502,
                        {
                            "error": {
                                "message": f"Could not reach Kimi upstream: {exc.reason}",
                                "type": "upstream_unavailable",
                                "param": None,
                                "code": "upstream_unavailable",
                            }
                        },
                    )
                    return
            return

        for idx, client in enumerate(clients_to_try):
            try:
                response = client.chat_completions(headers, upstream_payload)
                self._send_raw(
                    response.status,
                    response.body,
                    response.headers.get("Content-Type", "application/json"),
                )
                return
            except (UpstreamUnavailable, UpstreamHttpError) as exc:
                is_unavailable = isinstance(exc, UpstreamUnavailable)
                is_5xx = isinstance(exc, UpstreamHttpError) and exc.status >= 500
                if (is_unavailable or is_5xx) and idx < len(clients_to_try) - 1:
                    print(f"Primary upstream ({client.base_url}) failed: {exc}. Trying fallback ({clients_to_try[idx + 1].base_url})...")
                    continue

                if isinstance(exc, UpstreamHttpError):
                    self._send_json(exc.status, normalize_error(exc.status, exc.body))
                    return
                self._send_json(
                    502,
                    {
                        "error": {
                            "message": f"Could not reach Kimi upstream: {exc.reason}",
                            "type": "upstream_unavailable",
                            "param": None,
                            "code": "upstream_unavailable",
                        }
                    },
                )
                return

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            raise ValueError("Request body is required.")
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("Request body must be valid JSON.") from exc
        if not isinstance(payload, dict):
            raise ValueError("Request body must be a JSON object.")
        return payload

    def _forward_headers(self) -> dict[str, str]:
        blocked = {"host", "content-length", "connection"}
        headers = {
            key: value
            for key, value in self.headers.items()
            if key.lower() not in blocked
        }
        headers["Content-Type"] = "application/json"
        return headers

    def _add_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, Accept, X-Requested-With")

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        self._send_raw(status, json.dumps(payload).encode("utf-8"), "application/json")

    def _send_raw(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self._add_cors_headers()
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass


class KimiBridgeServer(ThreadingHTTPServer):
    def __init__(self, address: tuple[str, int], config: AppConfig) -> None:
        super().__init__(address, KimiBridgeHandler)
        self.config = config


def run_server(config: AppConfig) -> None:
    server = KimiBridgeServer((config.server.host, config.server.port), config)
    print(f"KimiBridge listening on http://{config.server.host}:{config.server.port}/v1")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("KimiBridge stopped.")
    finally:
        server.server_close()
