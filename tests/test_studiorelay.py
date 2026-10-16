"""Tests for StudioRelay package, CLI, configuration, and migration."""

import io
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import studiorelay
import studiorelay.config as config
import studiorelay.ports as ports
import studiorelay.service as service
from studiorelay.cli import main
from studiorelay.compatibility.pipeline import normalize_request
from studiorelay.compatibility.responses import chat_completion_to_response


class TestStudioRelayPackage(unittest.TestCase):
    def test_version_present(self):
        self.assertTrue(hasattr(studiorelay, "__version__"))
        self.assertIsInstance(studiorelay.__version__, str)
        self.assertGreater(len(studiorelay.__version__), 0)

    def test_module_exports(self):
        self.assertTrue(hasattr(studiorelay, "config"))
        self.assertTrue(hasattr(studiorelay, "server"))
        self.assertTrue(hasattr(studiorelay, "cli"))
        self.assertTrue(hasattr(studiorelay, "ports"))
        self.assertTrue(hasattr(studiorelay, "service"))


class TestStudioRelayConfig(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.legacy_dir = os.path.join(self.test_dir, ".kimibridge")
        self.new_dir = os.path.join(self.test_dir, ".studiorelay")
        os.makedirs(self.legacy_dir, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_precedence_env_var_studiorelay(self):
        custom_cfg = os.path.join(self.test_dir, "custom_sr.json")
        with open(custom_cfg, "w") as f:
            json.dump({"port": 9001}, f)

        with patch.dict(os.environ, {"STUDIORELAY_CONFIG": custom_cfg}):
            self.assertEqual(str(config.resolve_config_path()), custom_cfg)

    def test_precedence_env_var_kimibridge(self):
        custom_cfg = os.path.join(self.test_dir, "custom_kb.json")
        with open(custom_cfg, "w") as f:
            json.dump({"port": 9002}, f)

        with patch.dict(os.environ, {"KIMIBRIDGE_CONFIG": custom_cfg}, clear=False):
            if "STUDIORELAY_CONFIG" in os.environ:
                del os.environ["STUDIORELAY_CONFIG"]
            self.assertEqual(str(config.resolve_config_path()), custom_cfg)

    def test_precedence_new_directory_over_legacy(self):
        os.makedirs(self.new_dir, exist_ok=True)
        new_file = os.path.join(self.new_dir, "config.json")
        legacy_file = os.path.join(self.legacy_dir, "config.json")
        with open(new_file, "w") as f:
            json.dump({"provider": "deepseek", "port": 5001}, f)
        with open(legacy_file, "w") as f:
            json.dump({"provider": "deepseek", "port": 5001}, f)

        with patch.object(config, "CONFIG_DIR", self.new_dir), \
             patch.object(config, "LEGACY_CONFIG_DIR", self.legacy_dir), \
             patch.dict(os.environ, {}, clear=True):
            resolved = config.resolve_config_path()
            self.assertEqual(str(resolved), new_file)

    def test_fallback_to_legacy_directory_when_new_missing(self):
        legacy_file = os.path.join(self.legacy_dir, "config.json")
        with open(legacy_file, "w") as f:
            json.dump({"provider": "kimi", "port": 5002}, f)

        with patch.object(config, "CONFIG_DIR", self.new_dir), \
             patch.object(config, "LEGACY_CONFIG_DIR", self.legacy_dir), \
             patch.dict(os.environ, {}, clear=True):
            resolved = config.resolve_config_path()
            self.assertEqual(str(resolved), legacy_file)

    def test_provider_specific_config_resolution(self):
        legacy_kimi = os.path.join(self.legacy_dir, "config-kimi.json")
        with open(legacy_kimi, "w") as f:
            json.dump({"provider": "kimi", "port": 5002}, f)

        with patch.object(config, "CONFIG_DIR", self.new_dir), \
             patch.object(config, "LEGACY_CONFIG_DIR", self.legacy_dir), \
             patch.dict(os.environ, {}, clear=True):
            resolved = config.resolve_config_path(provider="kimi")
            self.assertEqual(str(resolved), legacy_kimi)


class TestStudioRelayMigration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.legacy_dir = os.path.join(self.test_dir, ".kimibridge")
        self.new_dir = os.path.join(self.test_dir, ".studiorelay")
        os.makedirs(self.legacy_dir, exist_ok=True)

        self.cfg_content = {"provider": "deepseek", "port": 5001, "api_key": "test-key-do-not-leak"}
        with open(os.path.join(self.legacy_dir, "config.json"), "w") as f:
            json.dump(self.cfg_content, f)
        with open(os.path.join(self.legacy_dir, "config-deepseek.json"), "w") as f:
            json.dump(self.cfg_content, f)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_cli_migrate_dry_run(self, mock_stdout):
        with patch("studiorelay.cli.CONFIG_DIR", self.new_dir), \
             patch("studiorelay.cli.LEGACY_CONFIG_DIR", self.legacy_dir):
            exit_code = main(["migrate", "--dry-run"])
            self.assertEqual(exit_code, 0)
            output = mock_stdout.getvalue()
            self.assertIn("dry-run", output)
            self.assertIn("config.json", output)
            # Ensure new dir was not created in dry run
            self.assertFalse(os.path.exists(os.path.join(self.new_dir, "config.json")))

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_cli_migrate_execution_and_idempotency(self, mock_stdout):
        with patch("studiorelay.cli.CONFIG_DIR", self.new_dir), \
             patch("studiorelay.cli.LEGACY_CONFIG_DIR", self.legacy_dir):
            exit_code = main(["migrate"])
            self.assertEqual(exit_code, 0)
            # Verify file copied correctly
            migrated_file = os.path.join(self.new_dir, "config.json")
            self.assertTrue(os.path.exists(migrated_file))
            with open(migrated_file, "r") as f:
                data = json.load(f)
            self.assertEqual(data["port"], 5001)

            # Check that sensitive keys are not exposed in standard output
            output = mock_stdout.getvalue()
            self.assertNotIn("test-key-do-not-leak", output)
            self.assertIn("Migration completed successfully", output)

            # Rerun migration to verify idempotency (does not fail, does not overwrite without notice)
            exit_code_rerun = main(["migrate"])
            self.assertEqual(exit_code_rerun, 0)


class TestStudioRelayCLI(unittest.TestCase):
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_cli_help(self, mock_stdout):
        with self.assertRaises(SystemExit) as cm:
            main(["--help"])
        self.assertEqual(cm.exception.code, 0)
        output = mock_stdout.getvalue()
        self.assertIn("StudioRelay", output)
        self.assertIn("Android Studio", output)
        self.assertIn("migrate", output)
        self.assertIn("doctor", output)

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_cli_version(self, mock_stdout):
        exit_code = main(["--version"])
        self.assertEqual(exit_code, 0)
        output = mock_stdout.getvalue()
        self.assertIn(studiorelay.__version__, output)

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_cli_doctor(self, mock_stdout):
        exit_code = main(["doctor"])
        self.assertIn(exit_code, (0, 1))
        output = mock_stdout.getvalue()
        self.assertIn("StudioRelay Doctor", output)
        self.assertIn("Python:", output)

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_cli_config_show(self, mock_stdout):
        test_cfg = config.AppConfig(
            server=config.ServerConfig(port=5001),
            provider="deepseek",
        )
        with patch("studiorelay.cli.load_config", return_value=test_cfg), \
             patch("studiorelay.cli.default_config_path", return_value=Path("/tmp/config.json")):
            exit_code = main(["config", "show"])
            self.assertEqual(exit_code, 0)
            output = mock_stdout.getvalue()
            self.assertIn("deepseek", output)
            self.assertIn("5001", output)


class TestStudioRelayServiceAndPorts(unittest.TestCase):
    def test_service_unit_names(self):
        self.assertEqual(service.get_service_name("deepseek"), "studiorelay-deepseek")
        self.assertEqual(service.get_service_name("kimi"), "studiorelay-kimi")
        self.assertEqual(service.get_service_name("default"), "studiorelay")

    def test_ports_defaults(self):
        self.assertEqual(ports.DEFAULT_PORT_DEEPSEEK, 5001)
        self.assertEqual(ports.DEFAULT_PORT_KIMI, 5002)
        self.assertEqual(ports.get_default_port("deepseek"), 5001)
        self.assertEqual(ports.get_default_port("kimi"), 5002)


class TestStudioRelayReasoningFallback(unittest.TestCase):
    def test_responses_api_uses_reasoning_content_when_content_is_empty(self):
        chat_response = {
            "id": "chatcmpl-test-1",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "deepseek-reasoner",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "",
                        "reasoning_content": "This is step-by-step thinking.",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        }

        responses_api_obj = chat_completion_to_response(chat_response, {"model": "deepseek-reasoner"})
        output_items = responses_api_obj.get("output", [])
        self.assertEqual(len(output_items), 1)
        message_item = output_items[0]
        self.assertEqual(message_item.get("type"), "message")
        content_items = message_item.get("content", [])
        self.assertEqual(len(content_items), 1)
        self.assertEqual(content_items[0].get("text"), "This is step-by-step thinking.")


if __name__ == "__main__":
    unittest.main()
