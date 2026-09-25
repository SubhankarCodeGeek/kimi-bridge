# Installation & Updates

## Quick Install (macOS & Linux)

From a local checkout:

```bash
./installers/install.sh
```

The installer:
- Copies application files to `~/.kimibridge/app`
- Preserves existing configuration in `~/.kimibridge/config.json`
- Tests and configures the port (defaults to `5001`, falls back cleanly if busy)
- Registers and starts the background user service (`launchd` on macOS, `systemd --user` on Linux)

---

## Quick Install (Windows)

From PowerShell in a local checkout:

```powershell
.\installers\install.ps1
```

The installer registers and starts a background scheduled task named `KimiBridge`.

---

## Updating / Upgrading KimiBridge

Upgrades are designed to be zero-downtime and non-destructive for existing settings:

1. Pull the newest version or checkout the release tag:
   ```bash
   git pull origin main
   ```
2. Re-run the installer script:
   ```bash
   # Linux / macOS
   ./installers/install.sh

   # Windows
   .\installers\install.ps1
   ```
The installer automatically replaces application files in `~/.kimibridge/app`, preserves your existing `config.json` (keeping your ports and providers), and restarts the background service with the new build.

Verify the running version:
```bash
python3 -m kimibridge.cli doctor
```

---

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

---

## Uninstall

macOS/Linux:

```bash
./installers/uninstall.sh
```

Windows:

```powershell
.\installers\uninstall.ps1
```

The uninstallers remove app files and service registrations. User config in `~/.kimibridge/config.json` is left in place.

---

## Service Commands

After installation:

```bash
python3 -m kimibridge.cli status
python3 -m kimibridge.cli stop
python3 -m kimibridge.cli restart
python3 -m kimibridge.cli logs
python3 -m kimibridge.cli doctor
python3 -m kimibridge.cli uninstall
```
