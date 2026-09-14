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
        self.assertTrue(run.call_args.args[0][1].endswith("installers/uninstall.sh"))

    def test_windows_uninstall_uses_powershell_uninstaller(self) -> None:
        with patch("platform.system", return_value="Windows"):
            with patch("subprocess.run") as run:
                run.return_value = Mock(returncode=0, stdout="", stderr="")
                result = service_uninstall()

        self.assertTrue(result.ok)
        self.assertEqual(run.call_args.args[0][0], "powershell")
        self.assertTrue(run.call_args.args[0][-1].endswith("installers/uninstall.ps1"))


if __name__ == "__main__":
    unittest.main()
