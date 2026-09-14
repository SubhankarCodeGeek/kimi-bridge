import tempfile
import unittest
from pathlib import Path

from kimibridge.config import AppConfig, ServerConfig, load_config, save_config


class ConfigTests(unittest.TestCase):
    def test_save_and_load_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.json"
            config = AppConfig(server=ServerConfig(host="127.0.0.1", port=5002))

            save_config(config, path)
            loaded = load_config(path)

            self.assertEqual(loaded.server.host, "127.0.0.1")
            self.assertEqual(loaded.server.port, 5002)

    def test_missing_config_returns_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loaded = load_config(Path(temp_dir) / "missing.json")

            self.assertEqual(loaded.server.port, 5001)


if __name__ == "__main__":
    unittest.main()
