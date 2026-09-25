from __future__ import annotations

import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from kimibridge import cli
from kimibridge.config import load_config


class CliTests(unittest.TestCase):
    def test_set_port_rejects_invalid_port(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.json"
            with patch("kimibridge.cli.default_config_path", return_value=path):
                with patch("kimibridge.config.default_config_path", return_value=path):
                    with redirect_stdout(StringIO()):
                        result = cli.set_config_value("port", "70000")

            self.assertEqual(result, 2)
            self.assertFalse(path.exists())

    def test_set_port_saves_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.json"
            with patch("kimibridge.config.default_config_path", return_value=path):
                with redirect_stdout(StringIO()):
                    result = cli.set_config_value("port", "5002")
                loaded = load_config(path)

            self.assertEqual(result, 0)
            self.assertEqual(loaded.server.port, 5002)

    def test_start_dry_run_does_not_start_server(self) -> None:
        args = cli.build_parser().parse_args(["start", "--port", "5001", "--dry-run"])

        with patch("kimibridge.cli.load_config") as load_config_mock:
            with patch("kimibridge.cli.resolve_port") as resolve_port_mock:
                with patch("kimibridge.cli.run_server") as run_server_mock:
                    load_config_mock.return_value = load_config(Path("/missing/config.json"))
                    resolve_port_mock.return_value.status = "available"
                    resolve_port_mock.return_value.selected_port = 5001
                    resolve_port_mock.return_value.changed = False
                    resolve_port_mock.return_value.message = "Port 5001 is available."

                    with redirect_stdout(StringIO()):
                        result = cli.start(args)

        self.assertEqual(result, 0)
        run_server_mock.assert_not_called()

    def test_set_fallback_base_url_saves_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.json"
            with patch("kimibridge.config.default_config_path", return_value=path):
                with redirect_stdout(StringIO()):
                    result = cli.set_config_value("fallback-base-url", "https://api.moonshot.ai")
                loaded = load_config(path)

            self.assertEqual(result, 0)
            self.assertEqual(loaded.kimi.fallback_base_url, "https://api.moonshot.ai")

    def test_set_provider_saves_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.json"
            with patch("kimibridge.config.default_config_path", return_value=path):
                with redirect_stdout(StringIO()):
                    result = cli.set_config_value("provider", "deepseek")
                loaded = load_config(path)

            self.assertEqual(result, 0)
            self.assertEqual(loaded.provider, "deepseek")
            self.assertEqual(loaded.kimi.base_url, "https://api.deepseek.com")

    def test_set_provider_rejects_invalid_provider(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.json"
            with patch("kimibridge.config.default_config_path", return_value=path):
                with redirect_stdout(StringIO()):
                    result = cli.set_config_value("provider", "invalid_provider_xyz")

            self.assertEqual(result, 2)
            self.assertFalse(path.exists())

    def test_set_base_url_auto_syncs_provider_to_deepseek(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.json"
            with patch("kimibridge.config.default_config_path", return_value=path):
                with redirect_stdout(StringIO()):
                    result = cli.set_config_value("base-url", "https://api.deepseek.com")
                loaded = load_config(path)

            self.assertEqual(result, 0)
            self.assertEqual(loaded.provider, "deepseek")
            self.assertEqual(loaded.kimi.base_url, "https://api.deepseek.com")

    def test_setup_provider_deepseek(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.json"
            args = cli.build_parser().parse_args(["setup", "deepseek", "--no-restart"])
            with patch("kimibridge.config.default_config_path", return_value=path):
                with patch("kimibridge.cli.default_config_path", return_value=path):
                    with redirect_stdout(StringIO()):
                        result = cli.setup_provider(args)
                    loaded = load_config(path)

            self.assertEqual(result, 0)
            self.assertEqual(loaded.provider, "deepseek")
            self.assertEqual(loaded.kimi.base_url, "https://api.deepseek.com")

    def test_setup_provider_kimi(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.json"
            args = cli.build_parser().parse_args(["setup", "kimi", "--no-restart"])
            with patch("kimibridge.config.default_config_path", return_value=path):
                with patch("kimibridge.cli.default_config_path", return_value=path):
                    with redirect_stdout(StringIO()):
                        result = cli.setup_provider(args)
                    loaded = load_config(path)

            self.assertEqual(result, 0)
            self.assertEqual(loaded.provider, "kimi")
            self.assertEqual(loaded.kimi.base_url, "https://api.moonshot.ai")

    def test_setup_provider_with_custom_base_url(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.json"
            args = cli.build_parser().parse_args(
                ["setup", "deepseek", "--base-url", "https://custom.deepseek.proxy/v1", "--no-restart"]
            )
            with patch("kimibridge.config.default_config_path", return_value=path):
                with patch("kimibridge.cli.default_config_path", return_value=path):
                    with redirect_stdout(StringIO()):
                        result = cli.setup_provider(args)
                    loaded = load_config(path)

            self.assertEqual(result, 0)
            self.assertEqual(loaded.provider, "deepseek")
            self.assertEqual(loaded.kimi.base_url, "https://custom.deepseek.proxy/v1")

    def test_use_provider_alias(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.json"
            args = cli.build_parser().parse_args(["use", "deepseek", "--no-restart"])
            with patch("kimibridge.config.default_config_path", return_value=path):
                with patch("kimibridge.cli.default_config_path", return_value=path):
                    with redirect_stdout(StringIO()):
                        result = cli.main(["use", "deepseek", "--no-restart"])
                    loaded = load_config(path)

            self.assertEqual(result, 0)
            self.assertEqual(loaded.provider, "deepseek")


if __name__ == "__main__":
    unittest.main()
