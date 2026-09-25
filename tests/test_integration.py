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

from kimibridge.config import AppConfig, CompatibilityConfig, KimiConfig, ServerConfig
from kimibridge.server import KimiBridgeHandler, KimiBridgeServer


FIXTURES = Path(__file__).parent / "fixtures"
TEST_TIMEOUT = 10


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

    def do_GET(self) -> None:
        if self.path == "/v1/models":
            response = {
                "object": "list",
                "data": [
                    {"id": "kimi-custom-finetune", "object": "model", "owned_by": "moonshot"},
                ],
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            encoded = json.dumps(response).encode("utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
            return
        self.send_response(404)
        self.end_headers()


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
        thread.join(timeout=5)


class IntegrationTests(unittest.TestCase):
    def test_health_and_models(self) -> None:
        try:
            port = free_port()
        except (PermissionError, OSError):
            self.skipTest("Local sockets are not permitted in this environment.")

        config = AppConfig(server=ServerConfig(port=port))
        with running_server(QuietKimiBridgeServer(("127.0.0.1", port), config)):
            with urlopen(f"http://127.0.0.1:{port}/health", timeout=TEST_TIMEOUT) as response:
                health = json.loads(response.read().decode("utf-8"))
            with urlopen(f"http://127.0.0.1:{port}/v1/models", timeout=TEST_TIMEOUT) as response:
                models = json.loads(response.read().decode("utf-8"))

        self.assertTrue(health["ok"])
        self.assertEqual(health["service"], "kimibridge")
        self.assertEqual(models["data"][0]["id"], "kimi-k3")

    def test_models_with_authorization_merges_live_upstream_models(self) -> None:
        try:
            upstream_port = free_port()
            proxy_port = free_port()
        except (PermissionError, OSError):
            self.skipTest("Local sockets are not permitted in this environment.")

        upstream = ThreadingHTTPServer(("127.0.0.1", upstream_port), MockUpstreamHandler)
        config = AppConfig(
            server=ServerConfig(port=proxy_port),
            kimi=KimiConfig(base_url=f"http://127.0.0.1:{upstream_port}"),
            provider="kimi",
        )
        proxy = QuietKimiBridgeServer(("127.0.0.1", proxy_port), config)

        request = Request(
            f"http://127.0.0.1:{proxy_port}/v1/models",
            headers={"Authorization": "Bearer test-key"},
        )

        with running_server(upstream):
            with running_server(proxy):
                with urlopen(request, timeout=TEST_TIMEOUT) as response:
                    models = json.loads(response.read().decode("utf-8"))

        model_ids = {m["id"] for m in models["data"]}
        self.assertIn("kimi-custom-finetune", model_ids)
        self.assertIn("kimi-k3", model_ids)
        self.assertIn("moonshot-v1-128k", model_ids)

    def test_models_returns_deepseek_models_when_provider_is_deepseek(self) -> None:
        try:
            port = free_port()
        except (PermissionError, OSError):
            self.skipTest("Local sockets are not permitted in this environment.")

        config = AppConfig(
            server=ServerConfig(port=port),
            provider="deepseek",
            kimi=KimiConfig(base_url="https://api.deepseek.com"),
        )
        with running_server(QuietKimiBridgeServer(("127.0.0.1", port), config)):
            with urlopen(f"http://127.0.0.1:{port}/v1/models", timeout=TEST_TIMEOUT) as response:
                models = json.loads(response.read().decode("utf-8"))

        model_ids = {m["id"] for m in models["data"]}
        self.assertIn("deepseek-chat", model_ids)
        self.assertIn("deepseek-v3-pro", model_ids)
        self.assertNotIn("kimi-k3", model_ids)

    def test_models_returns_deepseek_models_when_base_url_is_deepseek(self) -> None:
        try:
            port = free_port()
        except (PermissionError, OSError):
            self.skipTest("Local sockets are not permitted in this environment.")

        config = AppConfig(
            server=ServerConfig(port=port),
            provider="kimi",
            kimi=KimiConfig(base_url="https://api.deepseek.com/v1"),
        )
        with running_server(QuietKimiBridgeServer(("127.0.0.1", port), config)):
            with urlopen(f"http://127.0.0.1:{port}/v1/models", timeout=TEST_TIMEOUT) as response:
                models = json.loads(response.read().decode("utf-8"))

        model_ids = {m["id"] for m in models["data"]}
        self.assertIn("deepseek-chat", model_ids)
        self.assertIn("deepseek-v3-pro", model_ids)
        self.assertNotIn("kimi-k3", model_ids)

    def test_options_cors(self) -> None:
        try:
            port = free_port()
        except (PermissionError, OSError):
            self.skipTest("Local sockets are not permitted in this environment.")

        config = AppConfig(server=ServerConfig(port=port))
        request = Request(f"http://127.0.0.1:{port}/v1/chat/completions", method="OPTIONS")
        with running_server(QuietKimiBridgeServer(("127.0.0.1", port), config)):
            with urlopen(request, timeout=TEST_TIMEOUT) as response:
                status = response.status
                headers = dict(response.headers.items())

        self.assertEqual(status, 204)
        self.assertEqual(headers.get("Access-Control-Allow-Origin"), "*")
        self.assertIn("POST", headers.get("Access-Control-Allow-Methods", ""))

    def test_chat_completion_forwards_normalized_request(self) -> None:
        try:
            upstream_port = free_port()
            proxy_port = free_port()
        except (PermissionError, OSError):
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
                with urlopen(request, timeout=TEST_TIMEOUT) as response:
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
        except (PermissionError, OSError):
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
                with urlopen(request, timeout=TEST_TIMEOUT) as response:
                    body = response.read().decode("utf-8")
                    content_type = response.headers.get("Content-Type")

        self.assertIn("text/event-stream", content_type or "")
        self.assertIn('data: {"choices": [{"delta": {"content": "hello"}}]}', body)
        self.assertIn("data: [DONE]", body)
        self.assertIsNotNone(MockStreamUpstreamHandler.received)
        assert MockStreamUpstreamHandler.received is not None
        self.assertTrue(MockStreamUpstreamHandler.received["payload"]["stream"])

    def test_chat_completion_fallback_when_primary_fails(self) -> None:
        try:
            dead_primary_port = free_port()
            fallback_port = free_port()
            proxy_port = free_port()
        except (PermissionError, OSError):
            self.skipTest("Local sockets are not permitted in this environment.")

        MockUpstreamHandler.received = None
        fallback_upstream = ThreadingHTTPServer(("127.0.0.1", fallback_port), MockUpstreamHandler)
        config = AppConfig(
            server=ServerConfig(port=proxy_port),
            kimi=KimiConfig(
                base_url=f"http://127.0.0.1:{dead_primary_port}",
                fallback_base_url=f"http://127.0.0.1:{fallback_port}",
            ),
        )
        proxy = QuietKimiBridgeServer(("127.0.0.1", proxy_port), config)

        payload = {
            "messages": [{"role": "user", "content": "hello fallback"}],
        }
        request = Request(
            f"http://127.0.0.1:{proxy_port}/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with running_server(fallback_upstream):
            with running_server(proxy):
                with urlopen(request, timeout=TEST_TIMEOUT) as response:
                    result = json.loads(response.read().decode("utf-8"))

        self.assertEqual(result["choices"][0]["message"]["content"], "hello")
        self.assertIsNotNone(MockUpstreamHandler.received)
        assert MockUpstreamHandler.received is not None
        self.assertEqual(
            MockUpstreamHandler.received["payload"]["messages"][0]["content"],
            "hello fallback",
        )

    def test_chat_completion_streaming_fallback_when_primary_fails(self) -> None:
        try:
            dead_primary_port = free_port()
            fallback_port = free_port()
            proxy_port = free_port()
        except (PermissionError, OSError):
            self.skipTest("Local sockets are not permitted in this environment.")

        MockStreamUpstreamHandler.received = None
        fallback_upstream = ThreadingHTTPServer(("127.0.0.1", fallback_port), MockStreamUpstreamHandler)
        config = AppConfig(
            server=ServerConfig(port=proxy_port),
            kimi=KimiConfig(
                base_url=f"http://127.0.0.1:{dead_primary_port}",
                fallback_base_url=f"http://127.0.0.1:{fallback_port}",
            ),
        )
        proxy = QuietKimiBridgeServer(("127.0.0.1", proxy_port), config)

        payload = {
            "messages": [{"role": "user", "content": "hello fallback stream"}],
            "stream": True,
        }
        request = Request(
            f"http://127.0.0.1:{proxy_port}/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with running_server(fallback_upstream):
            with running_server(proxy):
                with urlopen(request, timeout=TEST_TIMEOUT) as response:
                    body = response.read().decode("utf-8")

        self.assertIn('data: {"choices": [{"delta": {"content": "hello"}}]}', body)
        self.assertIsNotNone(MockStreamUpstreamHandler.received)

    def test_deepseek_developer_role_normalization_end_to_end(self) -> None:
        try:
            upstream_port = free_port()
            proxy_port = free_port()
        except (PermissionError, OSError):
            self.skipTest("Local sockets are not permitted in this environment.")

        MockDeepSeekUpstreamHandler.received = None
        upstream = ThreadingHTTPServer(("127.0.0.1", upstream_port), MockDeepSeekUpstreamHandler)
        config = AppConfig(
            server=ServerConfig(port=proxy_port),
            kimi=KimiConfig(base_url=f"http://127.0.0.1:{upstream_port}"),
            provider="deepseek",
        )
        proxy = QuietKimiBridgeServer(("127.0.0.1", proxy_port), config)

        payload = json.loads(
            (FIXTURES / "deepseek-developer-role.json").read_text(encoding="utf-8")
        )
        request = Request(
            f"http://127.0.0.1:{proxy_port}/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with running_server(upstream):
            with running_server(proxy):
                with urlopen(request, timeout=TEST_TIMEOUT) as response:
                    result = json.loads(response.read().decode("utf-8"))

        self.assertEqual(result["choices"][0]["message"]["content"], "Compose response from DeepSeek")
        self.assertIsNotNone(MockDeepSeekUpstreamHandler.received)
        assert MockDeepSeekUpstreamHandler.received is not None
        self.assertEqual(
            MockDeepSeekUpstreamHandler.received["payload"]["messages"][0]["role"],
            "system",
        )

    def test_deepseek_422_error_normalization_in_passthrough(self) -> None:
        from urllib.error import HTTPError
        try:
            upstream_port = free_port()
            proxy_port = free_port()
        except (PermissionError, OSError):
            self.skipTest("Local sockets are not permitted in this environment.")

        MockDeepSeekUpstreamHandler.received = None
        upstream = ThreadingHTTPServer(("127.0.0.1", upstream_port), MockDeepSeekUpstreamHandler)
        config = AppConfig(
            server=ServerConfig(port=proxy_port),
            kimi=KimiConfig(base_url=f"http://127.0.0.1:{upstream_port}"),
            compatibility=CompatibilityConfig(mode="passthrough"),
            provider="deepseek",
        )
        proxy = QuietKimiBridgeServer(("127.0.0.1", proxy_port), config)

        payload = json.loads(
            (FIXTURES / "deepseek-developer-role.json").read_text(encoding="utf-8")
        )
        request = Request(
            f"http://127.0.0.1:{proxy_port}/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with running_server(upstream):
            with running_server(proxy):
                with self.assertRaises(HTTPError) as ctx:
                    urlopen(request, timeout=TEST_TIMEOUT)

        err_body = json.loads(ctx.exception.read().decode("utf-8"))
        self.assertEqual(ctx.exception.code, 422)
        self.assertEqual(err_body["error"]["type"], "invalid_request_error")
        self.assertEqual(err_body["error"]["code"], "invalid_parameters")
        self.assertIn("unknown variant developer", err_body["error"]["message"])


class MockDeepSeekUpstreamHandler(BaseHTTPRequestHandler):
    received: dict[str, Any] | None = None

    def log_message(self, format: str, *args: Any) -> None:
        return

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        payload = json.loads(body.decode("utf-8"))
        type(self).received = {
            "path": self.path,
            "headers": dict(self.headers.items()),
            "payload": payload,
        }

        # Emulate DeepSeek validation: developer role triggers 422
        messages = payload.get("messages", [])
        for msg in messages:
            if isinstance(msg, dict) and msg.get("role") == "developer":
                err_response = {
                    "detail": "Failed to deserialize the JSON body into the target type: messages[0].role: unknown variant developer, expected one of system, user, assistant, tool, latest_reminder"
                }
                encoded_err = json.dumps(err_response).encode("utf-8")
                self.send_response(422)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(encoded_err)))
                self.end_headers()
                self.wfile.write(encoded_err)
                return

        response = {
            "id": "chatcmpl-deepseek-test",
            "object": "chat.completion",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "Compose response from DeepSeek"},
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
