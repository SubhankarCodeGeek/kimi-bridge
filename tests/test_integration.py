from __future__ import annotations

from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import socket
import threading
import unittest
from pathlib import Path
from typing import Any, Iterator
from urllib.request import Request, urlopen

from kimibridge.config import AppConfig, KimiConfig, ServerConfig
from kimibridge.server import KimiBridgeHandler, KimiBridgeServer


FIXTURES = Path(__file__).parent / "fixtures"


class MockUpstreamHandler(BaseHTTPRequestHandler):
    received: dict[str, Any] | None = None

    def log_message(self, format: str, *args: Any) -> None:
        return

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        type(self).received = {
            "path": self.path,
            "headers": dict(self.headers.items()),
            "payload": json.loads(body.decode("utf-8")),
        }

        response = {
            "id": "chatcmpl-test",
            "object": "chat.completion",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "hello"},
                    "finish_reason": "stop",
                }
            ],
        }
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        encoded = json.dumps(response).encode("utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


class QuietKimiBridgeHandler(KimiBridgeHandler):
    def log_message(self, format: str, *args: Any) -> None:
        return


class QuietKimiBridgeServer(KimiBridgeServer):
    def __init__(self, address: tuple[str, int], config: AppConfig) -> None:
        ThreadingHTTPServer.__init__(self, address, QuietKimiBridgeHandler)
        self.config = config


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@contextmanager
def running_server(server: ThreadingHTTPServer) -> Iterator[ThreadingHTTPServer]:
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


class IntegrationTests(unittest.TestCase):
    def test_health_and_models(self) -> None:
        try:
            port = free_port()
        except PermissionError:
            self.skipTest("Local sockets are not permitted in this environment.")

        config = AppConfig(server=ServerConfig(port=port))
        with running_server(QuietKimiBridgeServer(("127.0.0.1", port), config)):
            with urlopen(f"http://127.0.0.1:{port}/health", timeout=2) as response:
                health = json.loads(response.read().decode("utf-8"))
            with urlopen(f"http://127.0.0.1:{port}/v1/models", timeout=2) as response:
                models = json.loads(response.read().decode("utf-8"))

        self.assertTrue(health["ok"])
        self.assertEqual(health["service"], "kimibridge")
        self.assertEqual(models["data"][0]["id"], "kimi-k3")

    def test_options_cors(self) -> None:
        try:
            port = free_port()
        except PermissionError:
            self.skipTest("Local sockets are not permitted in this environment.")

        config = AppConfig(server=ServerConfig(port=port))
        request = Request(f"http://127.0.0.1:{port}/v1/chat/completions", method="OPTIONS")
        with running_server(QuietKimiBridgeServer(("127.0.0.1", port), config)):
            with urlopen(request, timeout=2) as response:
                status = response.status
                headers = dict(response.headers.items())

        self.assertEqual(status, 204)
        self.assertEqual(headers.get("Access-Control-Allow-Origin"), "*")
        self.assertIn("POST", headers.get("Access-Control-Allow-Methods", ""))

    def test_chat_completion_forwards_normalized_request(self) -> None:
        try:
            upstream_port = free_port()
            proxy_port = free_port()
        except PermissionError:
            self.skipTest("Local sockets are not permitted in this environment.")

        MockUpstreamHandler.received = None
        upstream = ThreadingHTTPServer(("127.0.0.1", upstream_port), MockUpstreamHandler)
        config = AppConfig(
            server=ServerConfig(port=proxy_port),
            kimi=KimiConfig(base_url=f"http://127.0.0.1:{upstream_port}"),
        )
        proxy = QuietKimiBridgeServer(("127.0.0.1", proxy_port), config)

        payload = json.loads(
            (FIXTURES / "android-studio-developer-role.json").read_text(encoding="utf-8")
        )
        request = Request(
            f"http://127.0.0.1:{proxy_port}/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": "Bearer test-key",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with running_server(upstream):
            with running_server(proxy):
                with urlopen(request, timeout=2) as response:
                    result = json.loads(response.read().decode("utf-8"))

        self.assertEqual(result["choices"][0]["message"]["content"], "hello")
        self.assertIsNotNone(MockUpstreamHandler.received)
        assert MockUpstreamHandler.received is not None
        self.assertEqual(MockUpstreamHandler.received["path"], "/v1/chat/completions")
        self.assertEqual(
            MockUpstreamHandler.received["payload"]["messages"][0]["role"],
            "system",
        )
        self.assertNotIn("parallel_tool_calls", MockUpstreamHandler.received["payload"])
        self.assertNotIn("store", MockUpstreamHandler.received["payload"])
        self.assertEqual(
            MockUpstreamHandler.received["headers"]["Authorization"],
            "Bearer test-key",
        )

    def test_chat_completion_streaming(self) -> None:
        try:
            upstream_port = free_port()
            proxy_port = free_port()
        except PermissionError:
            self.skipTest("Local sockets are not permitted in this environment.")

        MockStreamUpstreamHandler.received = None
        upstream = ThreadingHTTPServer(("127.0.0.1", upstream_port), MockStreamUpstreamHandler)
        config = AppConfig(
            server=ServerConfig(port=proxy_port),
            kimi=KimiConfig(base_url=f"http://127.0.0.1:{upstream_port}"),
        )
        proxy = QuietKimiBridgeServer(("127.0.0.1", proxy_port), config)

        payload = {
            "messages": [{"role": "user", "content": "hi"}],
            "stream": True,
        }
        request = Request(
            f"http://127.0.0.1:{proxy_port}/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with running_server(upstream):
            with running_server(proxy):
                with urlopen(request, timeout=2) as response:
                    body = response.read().decode("utf-8")
                    content_type = response.headers.get("Content-Type")

        self.assertIn("text/event-stream", content_type or "")
        self.assertIn('data: {"choices": [{"delta": {"content": "hello"}}]}', body)
        self.assertIn("data: [DONE]", body)
        self.assertIsNotNone(MockStreamUpstreamHandler.received)
        assert MockStreamUpstreamHandler.received is not None
        self.assertTrue(MockStreamUpstreamHandler.received["payload"]["stream"])


class MockStreamUpstreamHandler(BaseHTTPRequestHandler):
    received: dict[str, Any] | None = None

    def log_message(self, format: str, *args: Any) -> None:
        return

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        type(self).received = {
            "path": self.path,
            "headers": dict(self.headers.items()),
            "payload": json.loads(body.decode("utf-8")),
        }

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(b'data: {"choices": [{"delta": {"content": "hello"}}]}\n\n')
        self.wfile.flush()
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()


if __name__ == "__main__":
    unittest.main()
