# KimiBridge 🌉

> **Local OpenAI-Compatible Gateway for Kimi / Moonshot AI & Developer Tools**

[![Tests](https://github.com/subhankar-android/kimi-bridge/actions/workflows/test.yml/badge.svg)](https://github.com/subhankar-android/kimi-bridge/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)

**KimiBridge** runs locally (`http://127.0.0.1:5001/v1`) to bridge OpenAI-compatible developer tools (such as **Android Studio**, **Cursor**, **VS Code**, and **Aider**) with **Kimi / Moonshot AI** models (`api.moonshot.ai`).

---

## ✨ Features

- ⚡ **Zero-Latency SSE Streaming**: Supports real-time streaming (`stream: true`) line-by-line forwarding.
- 🛠️ **Role Normalization**: Maps unsupported OpenAI `developer` role messages to `system` role.
- 🧹 **Payload Cleaning**: Filters out unsupported parameters (`parallel_tool_calls`, `store`, `metadata`).
- 🌐 **CORS Support**: Full preflight (`OPTIONS`) support for web tools and browser extensions.
- 🔌 **Graceful Port Management**: Automatic fallback port selection if port `5001` is occupied (`--auto-port`).
- 🖥️ **Cross-Platform Background Services**: Native background startup on **macOS** (`launchd`), **Linux** (`systemd`), and **Windows** (`Task Scheduler`).
- 📦 **Standalone Executables**: Builds self-contained single-file binaries with zero Python dependencies required at runtime.

---

## 🚀 Quick Start (2-Minute Setup for Host Machine Users)

### Step 1: Install & Start Background Service

Clone the repository and run the installer script on your host machine:

**Linux / macOS:**
```bash
git clone https://github.com/SubhankarCodeGeek/kimi-bridge.git
cd kimi-bridge
./installers/install.sh
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/SubhankarCodeGeek/kimi-bridge.git
cd kimi-bridge
.\installers\install.ps1
```

> **Note:** The installer automatically registers KimiBridge as a background user service (`systemctl --user` on Linux, `launchd` on macOS, `Task Scheduler` on Windows) listening on `http://127.0.0.1:5001/v1`.

---

### Step 2: Verify Host Service Health

Run diagnostics to confirm the background gateway is running properly:

```bash
python3 -m kimibridge.cli doctor
```

On Linux host machines, you can also manage and inspect the systemd user daemon directly:

```bash
# Check systemd user service status
systemctl --user status kimibridge

# View recent service logs
python3 -m kimibridge.cli logs
# or
journalctl --user -u kimibridge -n 50 --no-pager
```

---

### Step 3: Configure Android Studio

1. Open **Android Studio** ➔ **Settings** (or **Preferences** on macOS) ➔ **Tools** ➔ **AI Assistant** (or Custom LLM Provider).
2. Select **OpenAI-compatible**.
3. Fill in:
   - **Base URL**: `http://127.0.0.1:5001/v1`
   - **API Key**: *Your Kimi / Moonshot API Key* (`sk-...`)
   - **Model**: `kimi-k3` (or `moonshot-v1-8k`, `moonshot-v1-32k`)
4. Click **Apply / Test Connection**.

---

### Step 4: Enjoy AI Assistance in Android Studio!

KimiBridge automatically runs in the background. If you ever need to restart or manage the proxy service, run:

```bash
python3 -m kimibridge.cli restart
```

---

## 🎯 Additional Client Setup Guides

### ⚡ Cursor IDE
1. Open **Cursor Settings** ➔ **Models**.
2. Set **Override OpenAI Base URL** to `http://127.0.0.1:5001/v1`.
3. Enter your Kimi API Key and select model `kimi-k3`.

### 🐍 Aider CLI
```bash
export OPENAI_API_BASE="http://127.0.0.1:5001/v1"
export OPENAI_API_KEY="YOUR_KIMI_API_KEY"

aider --model openai/kimi-k3
```

### 💻 cURL Request Example
```bash
curl -N http://127.0.0.1:5001/v1/chat/completions \
  -H "Authorization: Bearer YOUR_KIMI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "kimi-k3",
    "messages": [{"role": "user", "content": "Hello Kimi!"}],
    "stream": true
  }'
```

---

## 🛠️ CLI Reference & Diagnostics

```bash
# Check service & endpoint diagnostics
python3 -m kimibridge.cli doctor

# Check server status
python3 -m kimibridge.cli status

# View logs
python3 -m kimibridge.cli logs

# Service controls
python3 -m kimibridge.cli stop
python3 -m kimibridge.cli restart

# Configuration management
python3 -m kimibridge.cli config show
python3 -m kimibridge.cli config set port 5002
python3 -m kimibridge.cli config set compatibility-mode compatible
```

For full details, see the [User Guide](docs/user_guide.md).

---

## 🏗️ Architecture

```text
OpenAI-compatible Client (Android Studio, Cursor, Aider, cURL)
                         │
                         ▼
          KimiBridge Proxy (127.0.0.1:5001)
                         │
                         ▼
        Compatibility Engine (Roles, Parameters)
                         │
                         ▼
         Kimi / Moonshot API (api.moonshot.ai)
```

---

## ⚙️ Compatibility Modes

- **`compatible`** *(default)*: Normalizes `developer` role ➔ `system` and purges unsupported parameters.
- **`strict`**: Leaves request parameters intact while maintaining mode validation.
- **`passthrough`**: Forwards raw HTTP requests directly to Moonshot upstream.

---

## 📦 Building Standalone Binaries

Compile single-file executables and SHA-256 checksums:

```bash
python3 scripts/build_binary.py
```

Outputs compiled binaries to `dist/` (e.g. `kimibridge-linux-x86_64`, `kimibridge-windows-x86_64.exe`).

---

## 📄 Documentation

- [User Guide](docs/user_guide.md) - Complete client configuration guides.
- [Installation Guide](docs/installation.md) - Detailed installation instructions.
- [Compatibility Matrix](docs/compatibility.md) - Tested tools and feature support.
- [Roadmap](docs/roadmap.md) - Project development phases.
- [Security Policy](SECURITY.md) - Privacy & credential safety policy.

---

## 📄 License

[MIT](LICENSE) © KimiBridge contributors.
