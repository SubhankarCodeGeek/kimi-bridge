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
- 🔁 **Responses API Bridge**: Supports `POST /v1/responses` by translating Responses requests to upstream Chat Completions and translating results back.
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
# First-time installation:
git clone https://github.com/SubhankarCodeGeek/kimi-bridge.git
cd kimi-bridge
.\installers\install-kimi.ps1

# If you already cloned previously / updating:
cd kimi-bridge; git pull origin main
.\installers\install-kimi.ps1
```

---

#### ⚙️ Option C: Interactive / Custom Setup

Run the general installer to choose your provider interactively:
- **Linux / macOS:** `./installers/install.sh`
- **Windows (PowerShell):** `.\installers\install.ps1`

---

> **Note:** The installer automatically registers KimiBridge as a background user service (`systemctl --user` on Linux, `launchd` on macOS, `Task Scheduler` on Windows).
> **Multi-Provider Concurrent Hosting:** If you install both DeepSeek and Kimi, KimiBridge automatically assigns dedicated ports (e.g. DeepSeek on `5001` and Kimi on `5002`) and runs independent background services (`kimibridge-deepseek` and `kimibridge-kimi`). Neither service stops or overwrites the other!

---

### Step 2: Verify Host Service Health

Run diagnostics to inspect all active provider endpoints:

```bash
# Check all configured endpoints and statuses
python3 -m kimibridge.cli status

# Run full health checks across all instances
python3 -m kimibridge.cli doctor
```

On Linux host machines, you can inspect each provider's background service individually:

```bash
# Check systemd user service status
systemctl --user status kimibridge-deepseek
systemctl --user status kimibridge-kimi

# View recent service logs
python3 -m kimibridge.cli logs --provider deepseek
python3 -m kimibridge.cli logs --provider kimi
```

---

### Step 3: Configure Android Studio

You can configure **DeepSeek** and **Kimi** side-by-side as separate OpenAI-compatible providers in Android Studio:

#### DeepSeek Configuration:
1. Open **Android Studio** ➔ **Settings** ➔ **Tools** ➔ **AI Assistant** (or Custom Provider).
2. Set **Base URL**: `http://127.0.0.1:5001/v1` *(or your assigned DeepSeek port)*.
3. Set **API Key**: *Your DeepSeek API Key*.
4. Click **Refresh**: Populates with `deepseek-chat`, `deepseek-reasoner`, `deepseek-v3-pro`, `deepseek-flash`.

#### Kimi / Moonshot AI Configuration:
1. In Android Studio, add a second OpenAI-compatible provider (or configure your Kimi entry).
2. Set **Base URL**: `http://127.0.0.1:5002/v1` *(or your assigned Kimi port)*.
3. Set **API Key**: *Your Kimi / Moonshot API Key*.
4. Click **Refresh**: Populates with `kimi-k3`, `moonshot-v1-8k`, `moonshot-v1-32k`, etc.

Both providers run concurrently in the background with zero port collisions and zero model dropdown cross-contamination!

---

### Step 4: Manage & Reconfigure Instances Anytime

You can adjust ports, upstream URLs, or restart instances anytime:

```bash
# Reconfigure or change ports
python3 -m kimibridge.cli setup deepseek --port 5001
python3 -m kimibridge.cli setup kimi --port 5002

# Restart a specific provider
python3 -m kimibridge.cli restart --provider deepseek
python3 -m kimibridge.cli restart --provider kimi

# View active configuration
python3 -m kimibridge.cli config show --provider deepseek
python3 -m kimibridge.cli config show --provider kimi
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
                    │ /v1/chat + /v1/  │
                    │    responses     │
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
- [Contributing Guide](CONTRIBUTING.md) - Developer prerequisites, architecture tour, and testing.
- [Compatibility Matrix](docs/compatibility.md) - Tested tools and feature support.
- [Roadmap](docs/roadmap.md) - Project development phases.
- [Security Policy](SECURITY.md) - Privacy & credential safety policy.

---

## 📄 License

[MIT](LICENSE) © KimiBridge contributors.
