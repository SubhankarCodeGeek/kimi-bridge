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


def service_name(provider: str | None = None) -> str:
    p = (provider or "").strip().lower()
    if p in {"moonshot"}:
        p = "kimi"
    if p and p not in {"all", "both", "default", "auto"}:
        return f"kimibridge-{p}"
    return LINUX_SERVICE


def macos_label(provider: str | None = None) -> str:
    p = (provider or "").strip().lower()
    if p in {"moonshot"}:
        p = "kimi"
    if p and p not in {"all", "both", "default", "auto"}:
        return f"com.kimibridge.proxy.{p}"
    return MACOS_LABEL


def windows_task(provider: str | None = None) -> str:
    p = (provider or "").strip().lower()
    if p in {"moonshot"}:
        p = "kimi"
    if p and p not in {"all", "both", "default", "auto"}:
        return f"KimiBridge-{p}"
    return WINDOWS_TASK


def service_action(action: str, provider: str | None = None) -> ServiceResult:
    system = platform.system().lower()

    if system == "darwin":
        return _macos_action(action, macos_label(provider))
    if system == "linux":
        return _linux_action(action, service_name(provider), provider=provider)
    if system == "windows":
        return _windows_action(action, windows_task(provider))

    return ServiceResult(False, f"Unsupported platform for service action: {system}")


def service_logs(provider: str | None = None) -> ServiceResult:
    system = platform.system().lower()
    p = (provider or "").strip().lower()
    log_name = f"kimibridge-{p}.log" if p and p not in {"all", "both", "default", "auto"} else "kimibridge.log"

    if system in {"darwin", "windows"}:
        log_path = Path.home() / ".kimibridge" / "app" / log_name
        if not log_path.exists():
            fallback_log = Path.home() / ".kimibridge" / "app" / "kimibridge.log"
            if fallback_log.exists():
                return _read_log(fallback_log)
        if log_path.exists():
            return _read_log(log_path)
        if system == "windows":
            return ServiceResult(
                False,
                f"Log file does not exist yet at {log_path}. Check Task Scheduler history in Windows Event Viewer.",
            )
        return _read_log(log_path)
    if system == "linux":
        log_path = Path.home() / ".kimibridge" / "app" / log_name
        if log_path.exists():
            return _read_log(log_path)
        s_name = service_name(provider)
        return _run(["journalctl", "--user", "-u", s_name, "-n", "80", "--no-pager"])

    return ServiceResult(False, f"Unsupported platform for logs: {system}")


def service_uninstall(provider: str | None = None, all_instances: bool = False) -> ServiceResult:
    system = platform.system().lower()
    root = Path(__file__).resolve().parents[1]
    args: list[str] = []
    if all_instances:
        args.append("--all")
    elif provider:
        args.extend(["--provider", provider])

    if system in {"darwin", "linux"}:
        return _run(["bash", str(root / "installers" / "uninstall.sh")] + args)

    if system == "windows":
        script = root / "installers" / "uninstall.ps1"
        cmd = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
        ]
        if all_instances:
            cmd.append("-All")
        elif provider:
            cmd.extend(["-Provider", provider])
        return _run(cmd)

    return ServiceResult(False, f"Unsupported platform for uninstall: {system}")


def _macos_action(action: str, label: str = MACOS_LABEL) -> ServiceResult:
    if action == "start":
        return _run(["launchctl", "start", label])
    if action == "stop":
        return _run(["launchctl", "stop", label])
    if action == "restart":
        stop = _run(["launchctl", "stop", label])
        start = _run(["launchctl", "start", label])
        return ServiceResult(start.ok, f"Restarted KimiBridge service ({label}).", stop.output + start.output)
    if action == "status":
        return _run(["launchctl", "list", label])
    return ServiceResult(False, f"Unsupported macOS service action: {action}")


def _linux_action(action: str, service: str = LINUX_SERVICE, provider: str | None = None) -> ServiceResult:
    if action == "start":
        return _run(["systemctl", "--user", "start", service])
    if action == "stop":
        return _run(["systemctl", "--user", "stop", service])
    if action == "restart":
        return _run(["systemctl", "--user", "restart", service])
    if action == "status":
        return _run(["systemctl", "--user", "status", service])
    return ServiceResult(False, f"Unsupported Linux service action: {action}")


def _windows_action(action: str, task: str = WINDOWS_TASK) -> ServiceResult:
    if action == "start":
        return _run(["schtasks", "/Run", "/TN", task])
    if action == "stop":
        return _run(["schtasks", "/End", "/TN", task])
    if action == "restart":
        stop = _run(["schtasks", "/End", "/TN", task])
        start = _run(["schtasks", "/Run", "/TN", task])
        return ServiceResult(start.ok, f"Restarted KimiBridge task ({task}).", stop.output + start.output)
    if action == "status":
        return _run(["schtasks", "/Query", "/TN", task, "/FO", "LIST", "/V"])
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

