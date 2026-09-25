# KimiBridge 🌉

> **Local OpenAI-Compatible Gateway for DeepSeek, Kimi / Moonshot AI & Developer Tools**

[![Tests](https://github.com/SubhankarCodeGeek/kimi-bridge/actions/workflows/test.yml/badge.svg)](https://github.com/SubhankarCodeGeek/kimi-bridge/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)

**KimiBridge** runs locally (`http://127.0.0.1:5001/v1`) to bridge OpenAI-compatible developer tools (such as **Android Studio**, **Cursor**, **VS Code**, and **Aider**) with **DeepSeek** (`api.deepseek.com`) and **Kimi / Moonshot AI** (`api.moonshot.ai`) models.

---

## ✨ Features

- ⚡ **Zero-Latency SSE Streaming**: Supports real-time streaming (`stream: true`) line-by-line forwarding.
- 🧩 **Provider-Aware Compatibility**: Adapts requests to target provider profiles (e.g. **Kimi / Moonshot**, **DeepSeek**, **OpenAI**).
- 🛠️ **Role Normalization**: Maps unsupported OpenAI `developer` role messages to `system` role when targeting strict providers like Kimi or DeepSeek.
- 🧹 **Payload Cleaning**: Filters out unsupported parameters (`parallel_tool_calls`, `store`, `metadata`).
- 🌐 **CORS Support**: Full preflight (`OPTIONS`) support for web tools and browser extensions.
- 🔌 **Graceful Port Management**: Automatic fallback port selection if port `5001` is occupied (`--auto-port`).
- 🖥️ **Cross-Platform Background Services**: Native background startup on **macOS** (`launchd`), **Linux** (`systemd`), and **Windows** (`Task Scheduler`).
- 📦 **Standalone Executables**: Builds self-contained single-file binaries with zero Python dependencies required at runtime.

---

## 🚀 Quick Start (2-Minute Setup for Host Machine Users)

### Step 1: Install & Start Background Service

Choose your target LLM provider:

#### 🌟 Option A: DeepSeek Setup (Recommended for Android Studio & Agentic Tools)

**Linux / macOS:**
```bash
# First-time installation:
git clone https://github.com/SubhankarCodeGeek/kimi-bridge.git
cd kimi-bridge
./installers/install-deepseek.sh

# If you already cloned previously / updating:
cd kimi-bridge && git pull origin main
./installers/install-deepseek.sh
```

**Windows (PowerShell):**
```powershell
# First-time installation:
git clone https://github.com/SubhankarCodeGeek/kimi-bridge.git
cd kimi-bridge
.\installers\install-deepseek.ps1

# If you already cloned previously / updating:
cd kimi-bridge; git pull origin main
.\installers\install-deepseek.ps1
```

> **Troubleshooting Tips:**
> - If you see `fatal: destination path 'kimi-bridge' already exists`, run `cd kimi-bridge && git pull origin main && ./installers/install-deepseek.sh`.
> - If you see `bash: Permission denied`, run `chmod +x installers/*.sh` or execute with `bash ./installers/install-deepseek.sh`.

---

#### 🌙 Option B: Kimi / Moonshot AI Setup

**Linux / macOS:**
```bash
# First-time installation:
git clone https://github.com/SubhankarCodeGeek/kimi-bridge.git
cd kimi-bridge
./installers/install-kimi.sh

# If you already cloned previously / updating:
cd kimi-bridge && git pull origin main
./installers/install-kimi.sh
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/SubhankarCodeGeek/kimi-bridge.git
cd kimi-bridge
.\installers\install.ps1 -Kimi
```

---

#### ⚙️ Option C: Interactive / Custom Setup

Run the general installer to choose your provider interactively:
- **Linux / macOS:** `./installers/install.sh`
- **Windows (PowerShell):** `.\installers\install.ps1`

---

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
   - **API Key**: *Your Provider API Key* (e.g. your DeepSeek API key or Kimi API key)
4. Click **Refresh** (or test connection):
   - For **DeepSeek**: Dropdown automatically populates with `deepseek-chat`, `deepseek-reasoner`, `deepseek-v3-pro`, `deepseek-flash`.
   - For **Kimi**: Dropdown automatically populates with `kimi-k3`, `moonshot-v1-8k`, `moonshot-v1-32k`, `moonshot-v1-128k`.
5. Select your desired model and click **Apply**!

---

### Step 4: Switch Providers Anytime (No Reinstallation Needed!)

To switch between DeepSeek and Kimi at any time, run:

```bash
# Switch to DeepSeek
python3 -m kimibridge.cli setup deepseek

# Switch to Kimi
python3 -m kimibridge.cli setup kimi

# Expose both providers
python3 -m kimibridge.cli setup all
```

This 1-step command automatically updates your endpoint configuration and restarts the background service. In Android Studio, simply click **Refresh** on the models dropdown.

If you ever need to restart or manage the proxy service manually:

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

# Switch target provider (1-step setup: sets provider, base-url, and restarts service)
python3 -m kimibridge.cli setup deepseek
python3 -m kimibridge.cli setup kimi
python3 -m kimibridge.cli setup all

# Configuration management
python3 -m kimibridge.cli config show
python3 -m kimibridge.cli config set port 5002
python3 -m kimibridge.cli config set compatibility-mode compatible
```

For full details, see the [User Guide](docs/user_guide.md).

---

## 🏗️ Architecture

```text
                  OpenAI-Compatible Client
             (Android Studio, Cursor, Aider, etc.)
                             │
                             ▼
                    ┌──────────────────┐
                    │    KimiBridge    │
                    │   HTTP Gateway   │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  Compatibility   │
                    │      Engine      │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
         Kimi Profile   DeepSeek Prof.  OpenAI Prof.
              │              │              │
              ▼              ▼              ▼
       api.moonshot.ai api.deepseek.com api.openai.com
```

---

## ⚙️ Compatibility Modes

- **`compatible`** *(default)*: Normalizes `developer` role ➔ `system` for strict providers (Kimi, DeepSeek) and purges unsupported parameters (`store`, `metadata`, `parallel_tool_calls`).
- **`strict`**: Leaves parameters unchanged while normalizing roles required to prevent deserialization errors.
- **`passthrough`**: Forwards raw HTTP requests directly to upstream without modifications.

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
