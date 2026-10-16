# Contributing to StudioRelay 🌉

Thank you for your interest in contributing to **StudioRelay**! We welcome contributions of all kinds: bug fixes, new provider profiles, IDE compatibility improvements, documentation updates, and test expansions.

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
4. **Idempotent & Safe Installers**: Installers must cleanly terminate running processes, remove stale binaries, preserve user configuration (`~/.studiorelay/` and legacy `~/.kimibridge/`), and configure ports without conflicts.
5. **Rock-Solid Backward Compatibility**: Existing installations using `kimibridge` commands, imports, or configs must continue to function seamlessly without broken workflows.

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

---

## 💻 Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/SubhankarCodeGeek/studio-relay.git
cd studio-relay
```

### 2. Set Up a Virtual Environment (Optional)

Since StudioRelay uses only the standard library, a virtual environment is optional, but recommended if you install development tools like PyInstaller:

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1
```

### 3. Verify Your Environment

Run the full unit and integration test suite directly:

```bash
python3 -m unittest discover -s tests
```

You should see all 115 tests pass with `OK`.

### 4. Running StudioRelay Locally in Development

You can run the CLI directly from source:

```bash
# Check version and CLI commands
python3 -m studiorelay.cli --help

# Start the proxy server on port 5001 (or auto-fallback)
python3 -m studiorelay.cli start --auto-port

# Inspect doctor diagnostics
python3 -m studiorelay.cli doctor

# View active configuration
python3 -m studiorelay.cli config show
```

---

## 🏛️ Codebase Architecture & Tour

```text
studio-relay/
├── studiorelay/                   # Primary Python package (Zero dependencies)
│   ├── __init__.py                # Package version
│   ├── cli.py                     # Command-line interface & subcommands
│   ├── config.py                  # Dataclass configs & configuration I/O
│   ├── health.py                  # Local health check client (/health)
│   ├── ports.py                   # Port binding check & automatic collision fallback
│   ├── server.py                  # HTTP server, SSE streaming, and request routing
│   ├── service.py                 # OS service manager (systemd / launchd / Task Scheduler)
│   ├── upstream.py                # Upstream HTTP client with URL path normalization
│   └── compatibility/             # Protocol normalization & provider profiles
│       ├── errors.py              # Normalizes upstream errors to OpenAI error payloads
│       ├── model_aliases.py       # Model alias mapping (e.g. deepseek-v3 -> deepseek-flash)
│       ├── models.py              # Provider model catalog & /v1/models response
│       ├── parameters.py          # Filters incompatible fields (store, metadata, etc.)
│       ├── pipeline.py            # Ordered request processing pipeline
│       ├── profiles.py            # Provider profiles (Kimi, DeepSeek, OpenAI, All)
│       ├── responses.py           # Responses API request/response translation
│       └── roles.py               # Role normalization (developer -> system)
├── kimibridge/                    # Backward-compatibility layer (delegates to studiorelay)
├── installers/                    # Cross-platform installation & uninstallation scripts
│   ├── install.sh                 # Linux/macOS main installer
│   ├── install-deepseek.sh        # Dedicated DeepSeek installer wrapper (executable)
│   ├── install-kimi.sh            # Dedicated Kimi installer wrapper (executable)
│   ├── install.ps1                # Windows PowerShell installer
│   ├── install-deepseek.ps1       # Windows PowerShell DeepSeek wrapper
│   ├── install-kimi.ps1           # Windows PowerShell Kimi wrapper
│   ├── uninstall.sh               # Linux/macOS clean uninstaller
│   └── uninstall.ps1              # Windows PowerShell clean uninstaller
├── services/                      # OS service template descriptors
│   ├── linux/studiorelay.service  # systemd user service template
│   ├── linux/kimibridge.service   # legacy systemd template alias
│   ├── macos/com.studiorelay.proxy.plist # launchd plist template
│   └── macos/com.kimibridge.proxy.plist  # legacy launchd plist template
├── tests/                         # Test suite (115 unit and integration tests)
│   ├── fixtures/                  # Request & response JSON fixtures
│   ├── test_build.py              # Binary build tests
│   ├── test_cli.py                # Legacy CLI test suite
│   ├── test_config.py             # Config loading, merging, and migration tests
│   ├── test_errors.py             # Error transformation tests
│   ├── test_integration.py        # End-to-end integration tests (HTTP, SSE streaming)
│   ├── test_models.py             # Model discovery and formatting tests
│   ├── test_pipeline.py           # Compatibility pipeline pass tests
│   ├── test_ports.py              # Port resolution and collision fallback tests
│   ├── test_profiles.py           # Provider profile registry tests
│   ├── test_roles.py              # Role normalization tests
│   ├── test_service.py            # Service template rendering & action tests
│   └── test_studiorelay.py         # StudioRelay package, migration, and CLI tests
├── scripts/                       # Developer and release scripts
│   ├── build.sh                   # Compilation, test discovery, and build wrapper
│   ├── build_binary.py            # PyInstaller standalone executable compiler
│   └── release.sh                 # Version tagging and release helper
├── docs/                          # Comprehensive user & technical documentation
├── pyproject.toml                 # Package definition and entry points
└── CONTRIBUTING.md                # This contributing guide
```

---

## 🛠️ How to Add or Modify Features

### 1. Adding a New Provider Profile

All provider profiles inherit from `ProviderProfile` in [`studiorelay/compatibility/profiles.py`](file:///media/subhankar-android/T7%20Shield/Projects/Ai_Ml/kimi-bridge/studiorelay/compatibility/profiles.py).

To add a new provider:

1. Define the class in `studiorelay/compatibility/profiles.py`:
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
3. Add tests in `tests/test_profiles.py`.

### 2. Adding or Updating Models

Static fallback models are defined in [`studiorelay/compatibility/models.py`](file:///media/subhankar-android/T7%20Shield/Projects/Ai_Ml/kimi-bridge/studiorelay/compatibility/models.py):

- `DEEPSEEK_MODELS`: List of supported DeepSeek model IDs.
- `KIMI_MODELS`: List of supported Kimi/Moonshot model IDs.

### 3. Adding Request/Response Compatibility Rules

- **Role transformations**: Modify `studiorelay/compatibility/roles.py`.
- **Parameter filtering**: Modify `studiorelay/compatibility/parameters.py`.
- **Error normalization**: Modify `studiorelay/compatibility/errors.py`.
- **Responses API translation**: Modify `studiorelay/compatibility/responses.py`.

---

## 🧪 Testing & Quality Assurance

### Running All Tests

```bash
# Run unit and integration tests
python3 -m unittest discover -s tests

# Check bytecode compilation
python3 -m compileall studiorelay kimibridge tests
```

---

## 🚀 Pull Request Guidelines & CI Matrix

Before opening a Pull Request:

1. **Verify All Tests Pass Locally**:
   ```bash
   python3 -m compileall studiorelay kimibridge tests
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

By contributing to StudioRelay, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).
