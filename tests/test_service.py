import unittest
from unittest.mock import Mock, patch

from kimibridge.service import service_action, service_logs, service_uninstall


class ServiceTests(unittest.TestCase):
    def test_linux_stop_uses_systemctl_user(self) -> None:
        with patch("platform.system", return_value="Linux"):
            with patch("subprocess.run") as run:
                run.return_value = Mock(returncode=0, stdout="", stderr="")
                result = service_action("stop")

        self.assertTrue(result.ok)
        run.assert_called_once()
        self.assertEqual(
            run.call_args.args[0],
            ["systemctl", "--user", "stop", "kimibridge"],
        )

    def test_macos_restart_uses_launchctl(self) -> None:
        with patch("platform.system", return_value="Darwin"):
            with patch("subprocess.run") as run:
                run.return_value = Mock(returncode=0, stdout="", stderr="")
                result = service_action("restart")

        self.assertTrue(result.ok)
        self.assertEqual(run.call_count, 2)

    def test_windows_stop_uses_scheduled_task(self) -> None:
        with patch("platform.system", return_value="Windows"):
            with patch("subprocess.run") as run:
                run.return_value = Mock(returncode=0, stdout="", stderr="")
                result = service_action("stop")

        self.assertTrue(result.ok)
        self.assertEqual(
            run.call_args.args[0],
            ["schtasks", "/End", "/TN", "KimiBridge"],
        )

    def test_linux_start_uses_systemctl_user(self) -> None:
        with patch("platform.system", return_value="Linux"):
            with patch("subprocess.run") as run:
                run.return_value = Mock(returncode=0, stdout="", stderr="")
                result = service_action("start")

        self.assertTrue(result.ok)
        self.assertEqual(run.call_args.args[0], ["systemctl", "--user", "start", "kimibridge"])

    def test_linux_status_uses_systemctl_user(self) -> None:
        with patch("platform.system", return_value="Linux"):
            with patch("subprocess.run") as run:
                run.return_value = Mock(returncode=0, stdout="", stderr="")
                result = service_action("status")

        self.assertTrue(result.ok)
        self.assertEqual(run.call_args.args[0], ["systemctl", "--user", "status", "kimibridge"])

    def test_macos_start_uses_launchctl(self) -> None:
        with patch("platform.system", return_value="Darwin"):
            with patch("subprocess.run") as run:
                run.return_value = Mock(returncode=0, stdout="", stderr="")
                result = service_action("start")

        self.assertTrue(result.ok)
        self.assertEqual(run.call_args.args[0], ["launchctl", "start", "com.kimibridge.proxy"])

    def test_macos_status_uses_launchctl(self) -> None:
        with patch("platform.system", return_value="Darwin"):
            with patch("subprocess.run") as run:
                run.return_value = Mock(returncode=0, stdout="", stderr="")
                result = service_action("status")

        self.assertTrue(result.ok)
        self.assertEqual(run.call_args.args[0], ["launchctl", "list", "com.kimibridge.proxy"])

    def test_windows_start_uses_scheduled_task(self) -> None:
        with patch("platform.system", return_value="Windows"):
            with patch("subprocess.run") as run:
                run.return_value = Mock(returncode=0, stdout="", stderr="")
                result = service_action("start")

        self.assertTrue(result.ok)
        self.assertEqual(run.call_args.args[0], ["schtasks", "/Run", "/TN", "KimiBridge"])

    def test_windows_status_uses_scheduled_task(self) -> None:
        with patch("platform.system", return_value="Windows"):
            with patch("subprocess.run") as run:
                run.return_value = Mock(returncode=0, stdout="", stderr="")
                result = service_action("status")

        self.assertTrue(result.ok)
        self.assertEqual(run.call_args.args[0], ["schtasks", "/Query", "/TN", "KimiBridge", "/FO", "LIST", "/V"])

    def test_windows_logs_missing_file_fallback(self) -> None:
        with patch("platform.system", return_value="Windows"):
            with patch("pathlib.Path.exists", return_value=False):
                result = service_logs()

        self.assertFalse(result.ok)
        self.assertIn("Log file does not exist", result.message)

    def test_linux_uninstall_uses_shell_uninstaller(self) -> None:
        with patch("platform.system", return_value="Linux"):
            with patch("subprocess.run") as run:
                run.return_value = Mock(returncode=0, stdout="", stderr="")
                result = service_uninstall()

        self.assertTrue(result.ok)
        self.assertEqual(run.call_args.args[0][0], "bash")
        self.assertTrue(str(run.call_args.args[0][1]).replace("\\", "/").endswith("installers/uninstall.sh"))

    def test_windows_uninstall_uses_powershell_uninstaller(self) -> None:
        with patch("platform.system", return_value="Windows"):
            with patch("subprocess.run") as run:
                run.return_value = Mock(returncode=0, stdout="", stderr="")
                result = service_uninstall()

        self.assertTrue(result.ok)
        self.assertEqual(run.call_args.args[0][0], "powershell")
        self.assertTrue(str(run.call_args.args[0][-1]).replace("\\", "/").endswith("installers/uninstall.ps1"))


class InstallerServiceTemplateTests(unittest.TestCase):
    def test_linux_service_template_rendering_python(self) -> None:
        from pathlib import Path
        import tempfile
        import subprocess

        repo_root = Path(__file__).resolve().parents[1]
        template = repo_root / "services" / "linux" / "kimibridge.service"
        exec_cmd = "/usr/bin/python3 -m kimibridge.cli"
        install_dir = "/home/testuser/.kimibridge/app"

        with tempfile.NamedTemporaryFile("w+", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        cmd = [
            "sed",
            "-e", f"s#__EXEC_CMD__#{exec_cmd}#g",
            "-e", f"s#__PYTHON_BIN__#{exec_cmd}#g",
            "-e", f"s#__INSTALL_DIR__#{install_dir}#g",
            str(template),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        rendered = res.stdout

        self.assertIn("ExecStart=/usr/bin/python3 -m kimibridge.cli start --auto-port", rendered)
        self.assertNotIn("-m kimibridge.cli -m kimibridge.cli", rendered)
        self.assertIn(f"WorkingDirectory={install_dir}", rendered)

    def test_linux_service_template_rendering_binary(self) -> None:
        from pathlib import Path
        import tempfile
        import subprocess

        repo_root = Path(__file__).resolve().parents[1]
        template = repo_root / "services" / "linux" / "kimibridge.service"
        exec_cmd = "/home/testuser/.kimibridge/app/bin/kimibridge"
        install_dir = "/home/testuser/.kimibridge/app"

        cmd = [
            "sed",
            "-e", f"s#__EXEC_CMD__#{exec_cmd}#g",
            "-e", f"s#__PYTHON_BIN__#{exec_cmd}#g",
            "-e", f"s#__INSTALL_DIR__#{install_dir}#g",
            str(template),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        rendered = res.stdout

        self.assertIn("ExecStart=/home/testuser/.kimibridge/app/bin/kimibridge start --auto-port", rendered)
        self.assertNotIn("-m kimibridge.cli", rendered)

    def test_macos_service_template_rendering(self) -> None:
        from pathlib import Path
        import tempfile
        import subprocess

        repo_root = Path(__file__).resolve().parents[1]
        template = repo_root / "services" / "macos" / "com.kimibridge.proxy.plist"
        exec_cmd = "/usr/bin/python3 -m kimibridge.cli"
        install_dir = "/home/testuser/.kimibridge/app"

        program_args = []
        for arg in f"{exec_cmd} start --auto-port".split():
            program_args.append(f"    <string>{arg}</string>")
        args_str = "\n".join(program_args)

        awk_script = """
        /__PROGRAM_ARGUMENTS__/ { print args; next }
        { gsub(/__INSTALL_DIR__/, dir); print }
        """
        cmd = ["awk", "-v", f"args={args_str}", "-v", f"dir={install_dir}", awk_script, str(template)]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        rendered = res.stdout

        self.assertIn("<string>/usr/bin/python3</string>", rendered)
        self.assertIn("<string>-m</string>", rendered)
        self.assertIn("<string>kimibridge.cli</string>", rendered)
        self.assertIn("<string>start</string>", rendered)
        self.assertIn("<string>--auto-port</string>", rendered)
        self.assertNotIn("__PROGRAM_ARGUMENTS__", rendered)


if __name__ == "__main__":
    unittest.main()
