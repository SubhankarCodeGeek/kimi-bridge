# Installation

## macOS And Linux

From a local checkout:

```bash
./installers/install.sh
```

The installer:

- copies the source tree to `~/.kimibridge/app`
- checks the configured port
- chooses a fallback port when needed
- saves the selected port to `~/.kimibridge/config.json`
- installs a user-level background service

Service backend:

```text
macOS: launchd
Linux: systemd --user
```

## Windows

From PowerShell in a local checkout:

```powershell
.\installers\install.ps1
```

The installer registers a user-level scheduled task named:

```text
KimiBridge
```

## Standalone Native Binary Builds

Build single-file executable artifacts and SHA-256 checksums:

```bash
python3 scripts/build_binary.py
```

Or run `scripts/build.sh` with binary mode:

```bash
./scripts/build.sh --binary
```

The compiled binaries will be output to `dist/` alongside `SHA256SUMS.txt`.

Installers (`install.sh` and `install.ps1`) automatically detect prebuilt standalone binaries in `dist/` and install them directly without requiring a Python runtime.

## Uninstall

macOS/Linux:

```bash
./installers/uninstall.sh
```

Windows:

```powershell
.\installers\uninstall.ps1
```

The uninstallers remove app files and service registrations. User config is left in place.

## Service Commands

After installation:

```bash
python3 -m kimibridge.cli status
python3 -m kimibridge.cli stop
python3 -m kimibridge.cli restart
python3 -m kimibridge.cli logs
python3 -m kimibridge.cli uninstall
```

On Windows, `logs` is not implemented yet; use Task Scheduler history during this phase.
