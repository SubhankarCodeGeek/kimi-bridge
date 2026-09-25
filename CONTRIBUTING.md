# Contributing to KimiBridge 🌉

Thank you for your interest in contributing to **KimiBridge**! We welcome contributions of all kinds: bug fixes, new provider profiles, IDE compatibility improvements, documentation updates, and test expansions.

This document outlines everything you need to know to get started, understand the codebase, set up your development environment, and submit high-quality pull requests.

---

## Table of Contents

- [Core Principles](#-core-principles)
- [Prerequisites & System Requirements](#-prerequisites--system-requirements)
- [Development Setup](#-development-setup)
- [Codebase Architecture & Tour](#-codebase-architecture--tour)
- [How to Add or Modify Features](#-how-to-add-or-modify-features)
  - [Adding a New Provider Profile](#1-adding-a-new-provider-profile)
  - [Adding or Updating Models](#2-adding-or-updating-models)
  - [Adding Request/Response Compatibility Rules](#3-adding-requestresponse-compatibility-rules)
  - [Modifying Installers & Background Services](#4-modifying-installers--background-services)
- [Testing & Quality Assurance](#-testing--quality-assurance)
- [Pull Request Guidelines & CI Matrix](#-pull-request-guidelines--ci-matrix)
- [Commit Message Conventions](#-commit-message-conventions)

---

## 🧭 Core Principles

1. **Zero Runtime Dependencies**: The core proxy, CLI, and compatibility engine rely solely on the **Python Standard Library** (`http.server`, `urllib`, `dataclasses`, `argparse`, `json`, `subprocess`). Do not introduce third-party runtime package dependencies (`requests`, `flask`, `fastapi`, etc.) unless strictly isolated for optional tools.
2. **Cross-Platform Parity**: Every feature must work seamlessly across **Linux**, **macOS**, and **Windows**. Background services must support `systemd --user`, macOS `launchd`, and Windows `Task Scheduler`.
3. **Fixture-Driven Compatibility**: Protocol transformations (such as normalizing `developer` role to `system`, or filtering `store` / `metadata`) must be grounded in real OpenAI client payloads and verified using deterministic test fixtures.
4. **Idempotent & Safe Installers**: Installers must cleanly terminate running processes, remove stale binaries, preserve user configuration (`~/.kimibridge/config.json`), and configure ports without conflicts.

---

## 📋 Prerequisites & System Requirements

### Required

| Tool | Minimum Version | Purpose |
|---|---|---|
| **Python** | `3.10+` (3.10, 3.11, or 3.12) | Core runtime, CLI, and test execution |
| **Git** | `2.20+` | Version control (`core.fileMode` enabled on Unix) |
| **Bash** | `4.0+` | Running shell installers on Linux / macOS |
| **PowerShell** | `5.1+` or `7+` (`pwsh`) | Running Windows installers on Windows |

### Operating System Requirements

- **Linux**:
  - `systemd` with user session support (`systemctl --user`)
  - `procps` (`pkill` / `pgrep`)
  - POSIX utilities (`tar`, `sed`, `awk`, `grep`)
- **macOS**:
  - macOS 11.0 (Big Sur) or newer
  - `launchd` and `launchctl` (standard on all macOS installations)
- **Windows**:
  - Windows 10/11 or Windows Server 2019+
  - Task Scheduler service enabled
  - Execution policy allowing local script execution (`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`)

### Optional Development Tools

- **PyInstaller**: Only required if building self-contained standalone binaries (`python3 scripts/build_binary.py`).
- **cURL & jq**: Useful for manual SSE streaming verification from the command line.

---

## 💻 Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/SubhankarCodeGeek/kimi-bridge.git
cd kimi-bridge
```

### 2. Set Up a Virtual Environment (Optional)

Since KimiBridge uses only the standard library, a virtual environment is optional, but recommended if you install development tools like PyInstaller or pre-commit hooks:

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1
```

### 3. Verify Your Environment

Run the full unit and integration test suite directly:

```bash
python3 -m unittest discover -s tests
```

You should see all 80+ tests pass with `OK`.

### 4. Running KimiBridge Locally in Development

You can run the CLI directly from source without installing the background service:

```bash
# Check version and CLI commands
python3 -m kimibridge.cli --help

# Start the proxy server on port 5001 (or auto-fallback)
python3 -m kimibridge.cli start --auto-port

# Inspect doctor diagnostics
python3 -m kimibridge.cli doctor

# View active configuration
python3 -m kimibridge.cli config show
```

---

## 🏛️ Codebase Architecture & Tour

```text
kimi-bridge/
├── kimibridge/                    # Core Python package (Zero dependencies)
│   ├── __init__.py                # Package version (__version__ = "0.2.1")
│   ├── cli.py                     # Command-line interface & subcommands
│   ├── config.py                  # Dataclass configs & ~/.kimibridge/config.json I/O
│   ├── health.py                  # Local health check client (/health)
│   ├── ports.py                   # Port binding check & automatic collision fallback
│   ├── server.py                  # HTTP server, SSE streaming, and request routing
│   ├── service.py                 # OS service manager (systemd / launchd / Task Scheduler)
│   ├── upstream.py                # Upstream HTTP client with URL path normalization
│   └── compatibility/             # Protocol normalization & provider profiles
│       ├── errors.py              # Normalizes upstream errors to OpenAI error payloads
│       ├── models.py              # Provider model catalog & /v1/models response
│       ├── parameters.py          # Filters incompatible fields (store, metadata, etc.)
│       ├── pipeline.py            # Ordered request processing pipeline
│       ├── profiles.py            # Provider profiles (Kimi, DeepSeek, OpenAI, All)
│       └── roles.py               # Role normalization (developer -> system)
├── installers/                    # Cross-platform installation & uninstallation scripts
│   ├── install.sh                 # Linux/macOS main installer
│   ├── install-deepseek.sh        # Dedicated DeepSeek installer wrapper (executable)
│   ├── install-kimi.sh            # Dedicated Kimi installer wrapper (executable)
│   ├── install.ps1                # Windows PowerShell installer
│   ├── install-deepseek.ps1       # Windows PowerShell DeepSeek wrapper
│   ├── uninstall.sh               # Linux/macOS clean uninstaller
│   └── uninstall.ps1              # Windows PowerShell clean uninstaller
├── services/                      # OS service template descriptors
│   ├── linux/kimibridge.service   # systemd user service template
│   └── macos/com.kimibridge.proxy.plist # launchd plist template
├── tests/                         # Test suite (80+ unit and integration tests)
│   ├── fixtures/                  # Request & response JSON fixtures
│   ├── test_cli.py                # CLI commands and configuration setting tests
│   ├── test_config.py             # Config loading, merging, and migration tests
│   ├── test_errors.py             # Error transformation tests
│   ├── test_integration.py        # End-to-end integration tests (HTTP, SSE streaming)
│   ├── test_models.py             # Model discovery and formatting tests
│   ├── test_pipeline.py           # Compatibility pipeline pass tests
│   ├── test_ports.py              # Port resolution and collision fallback tests
│   ├── test_profiles.py           # Provider profile registry tests
│   ├── test_roles.py              # Role normalization tests
│   └── test_service.py            # Service template rendering & action tests
├── scripts/                       # Developer and release scripts
│   ├── build.sh                   # Compilation, test discovery, and build wrapper
│   ├── build_binary.py            # PyInstaller standalone executable compiler
│   └── release.sh                 # Version tagging and release helper
├── docs/                          # Comprehensive user & technical documentation
├── pyproject.toml                 # Package definition and entry points
└── CONTRIBUTING.md                # This contributing guide
```

### Request Flow

```text
[OpenAI Client (e.g. Android Studio)]
                │
                ▼ (HTTP POST /v1/chat/completions)
    ┌─────────────────────────┐
    │   KimiBridgeHandler     │ (server.py)
    │  - CORS preflight       │
    │  - /health & /v1/models │
    └───────────┬─────────────┘
                │
                ▼
    ┌─────────────────────────┐
    │  CompatibilityPipeline  │ (compatibility/pipeline.py)
    │  - Role Normalization   │ (roles.py: developer -> system)
    │  - Parameter Filtering  │ (parameters.py: strip unsupported fields)
    └───────────┬─────────────┘
                │
                ▼
    ┌─────────────────────────┐
    │   KimiUpstreamClient    │ (upstream.py)
    │  - Normalizes base URL  │ (strips trailing /v1 to avoid /v1/v1)
    │  - Forwards auth header │
    │  - Primary + Fallback   │
    └───────────┬─────────────┘
                │
        ┌───────┴───────┐
        ▼               ▼
[Stream Mode]    [Unary Mode]
SSE pass-through Raw JSON forwarding (with error normalization)
```

---

## 🛠️ How to Add or Modify Features

### 1. Adding a New Provider Profile

All provider profiles inherit from `ProviderProfile` in [`kimibridge/compatibility/profiles.py`](file:///media/subhankar-android/T7%20Shield/Projects/Ai_Ml/kimi-bridge/kimibridge/compatibility/profiles.py).

To add a new provider (e.g. `anthropic` or `groq`):

1. Define the class in `kimibridge/compatibility/profiles.py`:
   ```python
   @dataclass(frozen=True)
   class MyProviderProfile(ProviderProfile):
       name: str = "myprovider"
       display_name: str = "My Provider"
       default_base_url: str = "https://api.myprovider.com"
       normalize_developer_role: bool = True
       unsupported_parameters: tuple[str, ...] = ("store", "metadata")
       default_models: tuple[str, ...] = ("model-v1", "model-v2")
   ```
2. Register it in `PROVIDER_PROFILES`:
   ```python
   PROVIDER_PROFILES["myprovider"] = MyProviderProfile()
   ```
3. Add tests in `tests/test_profiles.py` verifying that:
   - `get_profile("myprovider")` resolves correctly.
   - Provider name aliases (e.g. casing or alternate spellings) work as expected.
   - The CLI `python3 -m kimibridge.cli setup myprovider` configures the provider and upstream URL correctly.

### 2. Adding or Updating Models

Static fallback models are defined in [`kimibridge/compatibility/models.py`](file:///media/subhankar-android/T7%20Shield/Projects/Ai_Ml/kimi-bridge/kimibridge/compatibility/models.py):

- `DEEPSEEK_MODELS`: List of supported DeepSeek model IDs (`deepseek-chat`, `deepseek-reasoner`, `deepseek-v3-pro`, `deepseek-flash`, etc.).
- `KIMI_MODELS`: List of supported Kimi/Moonshot model IDs (`kimi-k3`, `moonshot-v1-8k`, etc.).

When updating model lists:
1. Update the appropriate model tuple in `models.py`.
2. Update the corresponding tests in `tests/test_models.py`.

### 3. Adding Request/Response Compatibility Rules

- **Role transformations**: Modify [`kimibridge/compatibility/roles.py`](file:///media/subhankar-android/T7%20Shield/Projects/Ai_Ml/kimi-bridge/kimibridge/compatibility/roles.py).
- **Parameter filtering**: Modify [`kimibridge/compatibility/parameters.py`](file:///media/subhankar-android/T7%20Shield/Projects/Ai_Ml/kimi-bridge/kimibridge/compatibility/parameters.py).
- **Error normalization**: Modify [`kimibridge/compatibility/errors.py`](file:///media/subhankar-android/T7%20Shield/Projects/Ai_Ml/kimi-bridge/kimibridge/compatibility/errors.py).

Always add a new fixture under `tests/fixtures/` and an accompanying test in `test_roles.py`, `test_pipeline.py`, or `test_errors.py`.

### 4. Modifying Installers & Background Services

When modifying shell scripts or PowerShell installers:

- **Executable File Permissions**: All `.sh` scripts in `installers/` and `scripts/` **must** have executable permissions in Git (`100755` mode):
  ```bash
  chmod +x installers/*.sh scripts/*.sh
  git update-index --chmod=+x installers/*.sh scripts/*.sh
  ```
- **Process Cleanup**: Installers must stop running services and terminate any lingering `kimibridge` processes to release ports and prevent "file in use" errors on Windows/Linux.
- **Binary Cleanup**: When not explicitly installing in `--binary` mode, installers must remove existing installed binaries and stale `dist/` artifacts to prevent running outdated compiled code.
- **POSIX Syntax Checking**: Always verify shell scripts syntax before committing:
  ```bash
  bash -n installers/install.sh
  bash -n installers/install-deepseek.sh
  bash -n installers/install-kimi.sh
  bash -n installers/uninstall.sh
  ```
- **PowerShell Syntax Checking**: Verify PowerShell syntax using `pwsh` or Windows PowerShell:
  ```powershell
  Get-ChildItem installers/*.ps1 | ForEach-Object {
      $err = $null
      [System.Management.Automation.Language.Parser]::ParseInput((Get-Content $_.FullName -Raw), [ref]$null, [ref]$err)
      if ($err) { throw "Syntax error in $_: $err" }
  }
  ```

---

## 🧪 Testing & Quality Assurance

### Running All Tests

```bash
# Run unit and integration tests
python3 -m unittest discover -s tests

# Or run with verbosity
python3 -m unittest discover -s tests -v
```

### Running Specific Test Modules

```bash
python3 -m unittest tests/test_roles.py
python3 -m unittest tests/test_profiles.py
python3 -m unittest tests/test_cli.py
python3 -m unittest tests/test_integration.py
```

### Syntax & Bytecode Compilation Check

```bash
python3 -m compileall kimibridge tests
```

---

## 🚀 Pull Request Guidelines & CI Matrix

Before opening a Pull Request:

1. **Verify All Tests Pass Locally**:
   ```bash
   python3 -m compileall kimibridge tests
   python3 -m unittest discover -s tests
   ```
2. **Check Installer Syntax**:
   ```bash
   bash -n installers/*.sh
   ```
3. **Verify Git File Permissions**:
   Make sure newly added shell scripts are tracked with mode `100755`:
   ```bash
   git ls-files --stage installers/
   ```
4. **Update Documentation**:
   If you change CLI flags, configuration parameters, or supported providers/models, update [`README.md`](README.md), [`docs/user_guide.md`](docs/user_guide.md), and [`docs/troubleshooting.md`](docs/troubleshooting.md).

### CI Matrix

Every Pull Request triggers a GitHub Actions matrix workflow (`.github/workflows/test.yml`) validating:
- **Python 3.10, 3.11, and 3.12** across **Ubuntu**, **macOS**, and **Windows** (9 parallel jobs).
- **Installer shell syntax check** on Ubuntu.
- **PowerShell syntax parser check** on Windows.

All jobs must pass green before merging.

---

## 📝 Commit Message Conventions

We follow [Conventional Commits](https://www.conventionalcommits.org/):

| Type | Purpose | Example |
|---|---|---|
| `feat` | A new feature or provider profile | `feat: add groq provider profile and models` |
| `fix` | A bug fix | `fix: normalize developer role in streaming mode` |
| `docs` | Documentation changes only | `docs: update installation instructions for Windows` |
| `test` | Adding or updating tests | `test: add unit tests for DeepSeek 422 error normalization` |
| `refactor` | Code change that neither fixes a bug nor adds a feature | `refactor: extract model normalization helper` |
| `chore` | Maintenance tasks or tooling updates | `chore: update github actions runner node version` |

---

## 📄 License

By contributing to KimiBridge, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).
