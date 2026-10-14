from __future__ import annotations

import socket
import unittest

from kimibridge.ports import find_available_port, is_port_available, resolve_port


def reserve_port() -> tuple[socket.socket, int]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    sock.listen(1)
    return sock, sock.getsockname()[1]


class PortTests(unittest.TestCase):
    def test_available_port_resolves_to_requested_port(self) -> None:
        port = find_available_port("127.0.0.1", 55000, limit=100)
        if port is None:
            self.skipTest("No available local test port found.")

        resolution = resolve_port("127.0.0.1", port)

        self.assertEqual(resolution.status, "available")
        self.assertEqual(resolution.selected_port, port)
        self.assertFalse(resolution.changed)

    def test_conflict_without_auto_port_reports_conflict(self) -> None:
        try:
            sock, port = reserve_port()
        except (PermissionError, OSError):
            self.skipTest("Local sockets are not permitted in this environment.")
        try:
            resolution = resolve_port("127.0.0.1", port, auto_port=False)
        finally:
            sock.close()

        self.assertEqual(resolution.status, "conflict")
        self.assertEqual(resolution.selected_port, port)

    def test_conflict_with_auto_port_uses_fallback(self) -> None:
        try:
            sock, port = reserve_port()
        except (PermissionError, OSError):
            self.skipTest("Local sockets are not permitted in this environment.")
        try:
            resolution = resolve_port("127.0.0.1", port, auto_port=True)
        finally:
            sock.close()

        self.assertEqual(resolution.status, "fallback")
        self.assertGreater(resolution.selected_port, port)
        self.assertTrue(is_port_available("127.0.0.1", resolution.selected_port))
        self.assertTrue(resolution.changed)

    def test_resolve_port_same_provider_already_running(self) -> None:
        from unittest.mock import patch
        with patch("kimibridge.ports.check_port_available", return_value=False):
            with patch("kimibridge.ports.get_kimibridge_status", return_value={"service": "kimibridge", "provider": "deepseek"}):
                res = resolve_port("127.0.0.1", 5001, target_provider="deepseek")
                self.assertEqual(res.status, "already_running")
                self.assertEqual(res.selected_port, 5001)

    def test_resolve_port_conflict_without_auto_port_different_provider(self) -> None:
        from unittest.mock import patch
        with patch("kimibridge.ports.check_port_available", return_value=False):
            with patch("kimibridge.ports.get_kimibridge_status", return_value={"service": "kimibridge", "provider": "deepseek"}):
                res = resolve_port("127.0.0.1", 5001, auto_port=False, target_provider="kimi")
                self.assertEqual(res.status, "conflict")
                self.assertIn("hosting 'deepseek'", res.message)

    def test_resolve_port_falls_back_when_different_provider_is_hosted(self) -> None:
        from unittest.mock import patch
        def mock_status(host: str, port: int, timeout: float = 0.5):
            if port == 5001:
                return {"service": "kimibridge", "provider": "deepseek"}
            return None

        def mock_available(host: str, port: int):
            if port == 5001:
                return False
            if port == 5002:
                return True
            return False

        with patch("kimibridge.ports.check_port_available", side_effect=mock_available):
            with patch("kimibridge.ports.get_kimibridge_status", side_effect=mock_status):
                res = resolve_port("127.0.0.1", 5001, auto_port=True, target_provider="kimi")
                self.assertEqual(res.status, "fallback")
                self.assertEqual(res.selected_port, 5002)
                self.assertIn("hosting 'deepseek'", res.message)
                self.assertIn("Selected port 5002 for 'kimi'", res.message)

    def test_legacy_provider_detected_from_models(self) -> None:
        from unittest.mock import MagicMock, patch
        import json

        models_response = {
            "object": "list",
            "data": [{"id": "kimi-k3", "owned_by": "moonshot"}]
        }
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps(models_response).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp

        health_response = {"ok": True, "service": "kimibridge"}  # No provider field
        mock_h_resp = MagicMock()
        mock_h_resp.status = 200
        mock_h_resp.read.return_value = json.dumps(health_response).encode("utf-8")
        mock_h_resp.__enter__.return_value = mock_h_resp

        def fake_urlopen(url: str, timeout: float = 0.5):
            if "/health" in url:
                return mock_h_resp
            if "/v1/models" in url:
                return mock_resp
            raise OSError("Unknown url")

        with patch("kimibridge.ports.urlopen", side_effect=fake_urlopen):
            from kimibridge.ports import get_kimibridge_status
            status = get_kimibridge_status("127.0.0.1", 5001)
            self.assertIsNotNone(status)
            self.assertEqual(status.get("provider"), "kimi")


if __name__ == "__main__":
    unittest.main()
