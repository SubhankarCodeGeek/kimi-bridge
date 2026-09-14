#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import os
import platform
import shutil
import subprocess
import sys
import zipapp
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = REPO_ROOT / "dist"


def get_target_name() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()

    if machine in {"amd64", "x86_64"}:
        arch = "x86_64"
    elif machine in {"arm64", "aarch64"}:
        arch = "arm64"
    else:
        arch = machine

    ext = ".exe" if system == "windows" else ""
    return f"kimibridge-{system}-{arch}{ext}"


def compute_sha256(file_path: Path) -> str:
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def generate_checksums(dist_dir: Path = DIST_DIR) -> Path:
    checksum_file = dist_dir / "SHA256SUMS.txt"
    lines: list[str] = []

    for item in sorted(dist_dir.glob("kimibridge*")):
        if item.is_file() and item.name != "SHA256SUMS.txt":
            digest = compute_sha256(item)
            lines.append(f"{digest}  {item.name}")

    content = "\n".join(lines) + ("\n" if lines else "")
    checksum_file.write_text(content, encoding="utf-8")
    return checksum_file


def build_pyinstaller(target_name: str) -> Path:
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--name",
        target_name,
        "--distpath",
        str(DIST_DIR),
        "--workpath",
        str(DIST_DIR / "build"),
        "--specpath",
        str(DIST_DIR / "spec"),
        str(REPO_ROOT / "kimibridge" / "cli.py"),
    ]
    subprocess.run(cmd, check=True)
    return DIST_DIR / target_name


def build_zipapp(target_name: str) -> Path:
    target_path = DIST_DIR / target_name
    zipapp.create_archive(
        source=REPO_ROOT,
        target=target_path,
        interpreter="/usr/bin/env python3",
        main="kimibridge.cli:main",
        compressed=True,
    )
    # Ensure execution permissions on Unix
    if platform.system().lower() != "windows":
        target_path.chmod(target_path.stat().st_mode | 0o755)
    return target_path


def main() -> int:
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    target_name = get_target_name()
    print(f"Building binary artifact: {target_name}")

    has_pyinstaller = False
    try:
        res = subprocess.run(
            [sys.executable, "-m", "PyInstaller", "--version"],
            capture_output=True,
            text=True,
        )
        if res.returncode == 0:
            has_pyinstaller = True
    except Exception:
        has_pyinstaller = False

    if has_pyinstaller:
        print("Using PyInstaller for standalone compilation...")
        artifact = build_pyinstaller(target_name)
    else:
        print("PyInstaller not found. Building portable zipapp binary executable...")
        artifact = build_zipapp(target_name)

    print(f"Built artifact: {artifact}")
    checksum_file = generate_checksums()
    print(f"Updated checksums: {checksum_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
