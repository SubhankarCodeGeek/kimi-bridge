from __future__ import annotations

from dataclasses import dataclass
import platform
import subprocess
from pathlib import Path


MACOS_LABEL = "com.kimibridge.proxy"
LINUX_SERVICE = "kimibridge"
WINDOWS_TASK = "KimiBridge"


@dataclass(frozen=True)
class ServiceResult:
    ok: bool
    message: str
    output: str = ""


def service_action(action: str) -> ServiceResult:
    system = platform.system().lower()

    if system == "darwin":
        return _macos_action(action)
    if system == "linux":
        return _linux_action(action)
    if system == "windows":
        return _windows_action(action)

    return ServiceResult(False, f"Unsupported platform for service action: {system}")


def service_logs() -> ServiceResult:
    system = platform.system().lower()

    if system in {"darwin", "windows"}:
        log_path = Path.home() / ".kimibridge" / "app" / "kimibridge.log"
        if log_path.exists():
            return _read_log(log_path)
        if system == "windows":
            return ServiceResult(
                False,
                f"Log file does not exist yet at {log_path}. Check Task Scheduler history in Windows Event Viewer.",
            )
        return _read_log(log_path)
    if system == "linux":
        log_path = Path.home() / ".kimibridge" / "app" / "kimibridge.log"
        if log_path.exists():
            return _read_log(log_path)
        return _run(["journalctl", "--user", "-u", LINUX_SERVICE, "-n", "80", "--no-pager"])

    return ServiceResult(False, f"Unsupported platform for logs: {system}")


def service_uninstall() -> ServiceResult:
    system = platform.system().lower()
    root = Path(__file__).resolve().parents[1]

    if system in {"darwin", "linux"}:
        return _run(["bash", str(root / "installers" / "uninstall.sh")])

    if system == "windows":
        script = root / "installers" / "uninstall.ps1"
        return _run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script),
            ]
        )

    return ServiceResult(False, f"Unsupported platform for uninstall: {system}")


def _macos_action(action: str) -> ServiceResult:
    if action == "start":
        return _run(["launchctl", "start", MACOS_LABEL])
    if action == "stop":
        return _run(["launchctl", "stop", MACOS_LABEL])
    if action == "restart":
        stop = _run(["launchctl", "stop", MACOS_LABEL])
        start = _run(["launchctl", "start", MACOS_LABEL])
        return ServiceResult(start.ok, "Restarted KimiBridge service.", stop.output + start.output)
    if action == "status":
        return _run(["launchctl", "list", MACOS_LABEL])
    return ServiceResult(False, f"Unsupported macOS service action: {action}")


def _linux_action(action: str) -> ServiceResult:
    if action == "start":
        return _run(["systemctl", "--user", "start", LINUX_SERVICE])
    if action == "stop":
        return _run(["systemctl", "--user", "stop", LINUX_SERVICE])
    if action == "restart":
        return _run(["systemctl", "--user", "restart", LINUX_SERVICE])
    if action == "status":
        return _run(["systemctl", "--user", "status", LINUX_SERVICE])
    return ServiceResult(False, f"Unsupported Linux service action: {action}")


def _windows_action(action: str) -> ServiceResult:
    if action == "start":
        return _run(["schtasks", "/Run", "/TN", WINDOWS_TASK])
    if action == "stop":
        return _run(["schtasks", "/End", "/TN", WINDOWS_TASK])
    if action == "restart":
        stop = _run(["schtasks", "/End", "/TN", WINDOWS_TASK])
        start = _run(["schtasks", "/Run", "/TN", WINDOWS_TASK])
        return ServiceResult(start.ok, "Restarted KimiBridge task.", stop.output + start.output)
    if action == "status":
        return _run(["schtasks", "/Query", "/TN", WINDOWS_TASK, "/FO", "LIST", "/V"])
    return ServiceResult(False, f"Unsupported Windows service action: {action}")


def _read_log(path: Path) -> ServiceResult:
    if not path.exists():
        return ServiceResult(False, f"Log file does not exist yet: {path}")

    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-80:]
    return ServiceResult(True, f"Last {len(lines)} log lines from {path}", "\n".join(lines))


def _run(command: list[str]) -> ServiceResult:
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        return ServiceResult(False, f"Command not found: {exc.filename}")

    output = (completed.stdout or "") + (completed.stderr or "")
    return ServiceResult(completed.returncode == 0, "Command completed.", output)
