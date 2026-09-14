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
        except PermissionError:
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
        except PermissionError:
            self.skipTest("Local sockets are not permitted in this environment.")
        try:
            resolution = resolve_port("127.0.0.1", port, auto_port=True)
        finally:
            sock.close()

        self.assertEqual(resolution.status, "fallback")
        self.assertGreater(resolution.selected_port, port)
        self.assertTrue(is_port_available("127.0.0.1", resolution.selected_port))
        self.assertTrue(resolution.changed)


if __name__ == "__main__":
    unittest.main()
