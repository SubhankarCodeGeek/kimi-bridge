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

    def test_save_and_load_fallback_base_url(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.json"
            config = AppConfig(
                kimi=load_config(Path(temp_dir) / "missing.json").kimi.__class__(
                    base_url="http://office-proxy.local:5001",
                    fallback_base_url="https://api.moonshot.ai",
                )
            )

            save_config(config, path)
            loaded = load_config(path)

            self.assertEqual(loaded.kimi.base_url, "http://office-proxy.local:5001")
            self.assertEqual(loaded.kimi.fallback_base_url, "https://api.moonshot.ai")

    def test_save_and_load_provider(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.json"
            config = AppConfig(provider="deepseek")

            save_config(config, path)
            loaded = load_config(path)

            self.assertEqual(loaded.provider, "deepseek")

    def test_missing_config_returns_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loaded = load_config(Path(temp_dir) / "missing.json")

            self.assertEqual(loaded.server.port, 5001)
            self.assertIsNone(loaded.kimi.fallback_base_url)
            self.assertEqual(loaded.provider, "kimi")

    def test_provider_specific_config_paths(self) -> None:
        from kimibridge.config import default_config_path
        kimi_path = default_config_path("kimi")
        deepseek_path = default_config_path("deepseek")
        default_path = default_config_path()

        self.assertTrue(kimi_path.name.endswith("config-kimi.json"))
        self.assertTrue(deepseek_path.name.endswith("config-deepseek.json"))
        self.assertEqual(default_path.name, "config.json")

    def test_provider_specific_save_and_load(self) -> None:
        from kimibridge.config import list_configured_providers
        with tempfile.TemporaryDirectory() as temp_dir:
            dir_path = Path(temp_dir)
            kimi_cfg = AppConfig(server=ServerConfig(port=5001), provider="kimi")
            deepseek_cfg = AppConfig(server=ServerConfig(port=5002), provider="deepseek")

            save_config(kimi_cfg, path=dir_path / "config-kimi.json", provider="kimi")
            save_config(deepseek_cfg, path=dir_path / "config-deepseek.json", provider="deepseek")

            loaded_kimi = load_config(path=dir_path / "config-kimi.json")
            loaded_deepseek = load_config(path=dir_path / "config-deepseek.json")

            self.assertEqual(loaded_kimi.server.port, 5001)
            self.assertEqual(loaded_kimi.provider, "kimi")
            self.assertEqual(loaded_deepseek.server.port, 5002)
            self.assertEqual(loaded_deepseek.provider, "deepseek")

            providers = list_configured_providers(dir_path)
            provider_names = [p[0] for p in providers]
            self.assertIn("kimi", provider_names)
            self.assertIn("deepseek", provider_names)


if __name__ == "__main__":
    unittest.main()
