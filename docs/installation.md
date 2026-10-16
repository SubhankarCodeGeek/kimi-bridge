# Installation & Updates

## Recommended: Install for DeepSeek (Android Studio / Agentic Tools)

**Linux / macOS:**
```bash
# First-time install:
git clone https://github.com/SubhankarCodeGeek/studio-relay.git
cd studio-relay
./installers/install-deepseek.sh

# Updating existing install:
cd studio-relay && git pull origin main
./installers/install-deepseek.sh
```

**Windows (PowerShell):**
```powershell
# First-time install:
git clone https://github.com/SubhankarCodeGeek/studio-relay.git
cd studio-relay
.\installers\install-deepseek.ps1

# Updating existing install:
cd studio-relay; git pull origin main
.\installers\install-deepseek.ps1
```

> **Troubleshooting:**
> - If `fatal: destination path 'studio-relay' already exists and is not an empty directory`: run `cd studio-relay && git pull origin main && ./installers/install-deepseek.sh`.
> - If `bash: Permission denied`: run `chmod +x installers/*.sh` or execute with `bash ./installers/install-deepseek.sh`.

---

## Install for Kimi / Moonshot AI

**Linux / macOS:**
```bash
./installers/install-kimi.sh
```

**Windows (PowerShell):**
```powershell
.\installers\install.ps1 -Kimi
```

---

## Interactive / General Installation

From a local checkout:

**Linux / macOS:**
```bash
./installers/install.sh
```

**Windows (PowerShell):**
```powershell
.\installers\install.ps1
```

The installer:
- Copies application files to `~/.studiorelay/app`
- Preserves existing configuration in `~/.studiorelay/config.json` (or migrates seamlessly from `~/.kimibridge/config.json`)
- Tests and configures the port (defaults to `5001` for DeepSeek, `5002` for Kimi, falls back cleanly if busy)
- Registers and starts the background user service (`launchd` on macOS, `systemd --user` on Linux, Task Scheduler on Windows)

---

## Upgrading from KimiBridge

StudioRelay includes a seamless, safe migration path for existing KimiBridge installations:

1. **Migrate configurations explicitly (optional, installer also does this automatically):**
   ```bash
   studiorelay migrate --dry-run
   studiorelay migrate
   ```
   This safely copies configurations from `~/.kimibridge/` to `~/.studiorelay/` with an automatic timestamped backup and zero credential exposure.

2. **Re-run the installer:**
   ```bash
   ./installers/install.sh
   ```
   The installer automatically detects legacy services (`kimibridge-deepseek.service`, `kimibridge.service`), stops them cleanly to prevent port conflicts, and starts `studiorelay-*.service`.

---

## Switching Providers Anytime

Switch providers anytime after installation without reinstalling:
```bash
studiorelay setup deepseek
# or: studiorelay setup kimi
# or: studiorelay setup all
```

*(Legacy command `kimibridge setup <provider>` remains fully supported)*

---

## Updating / Upgrading StudioRelay

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
The installer automatically updates application files in `~/.studiorelay/app`, preserves your existing `config.json` (keeping your ports and providers), and restarts the background service with the new build.

Verify the running version:
```bash
studiorelay doctor
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

The uninstallers remove app files and service registrations. User configurations in `~/.studiorelay/` and `~/.kimibridge/` are safely preserved.

---

## Service Commands

After installation:

```bash
studiorelay status
studiorelay stop
studiorelay restart
studiorelay logs
studiorelay doctor
studiorelay uninstall
```
