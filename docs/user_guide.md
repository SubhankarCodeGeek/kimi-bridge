# KimiBridge User Guide

Welcome to **KimiBridge**! This guide walks you through setting up and connecting KimiBridge to your favorite IDEs, AI assistants, and developer tools.

---

## What is KimiBridge?

KimiBridge is a local, lightweight compatibility gateway that exposes an **OpenAI-compatible API** (`http://127.0.0.1:5001/v1`) while translating requests under the hood to target LLM providers like **Kimi / Moonshot AI** (`api.moonshot.ai`) and **DeepSeek** (`api.deepseek.com`).

It automatically resolves protocol divergences between agentic clients and strict upstreams:
- Normalizes unsupported OpenAI `developer` role messages to `system` role.
- Cleans and filters incompatible request parameters (`parallel_tool_calls`, `store`, `metadata`).
- Proxies real-time **Server-Sent Events (SSE)** streaming responses with zero latency.
- Formats upstream error payloads (such as DeepSeek HTTP 422 deserialization errors) into clean OpenAI-standard formats.

---

## 1. Quick Installation & Startup

### Option A: Install as a Background Service (Recommended)

**macOS / Linux:**
```bash
./installers/install.sh
```

**Windows (PowerShell):**
```powershell
.\installers\install.ps1
```

Once installed, KimiBridge runs automatically in the background as a user service (`systemd` / `launchd` / `Task Scheduler`).

### Option B: Run Standalone Binary directly

```bash
# Build the binary
python3 scripts/build_binary.py

# Run the binary
./dist/kimibridge-linux-x86_64 start
```

### Option C: Run Python CLI directly

```bash
python3 -m kimibridge.cli start --auto-port
```

Default Base URL:
```text
http://127.0.0.1:5001/v1
```

---

## 2. Choosing Your Target Provider

KimiBridge supports provider profiles and seamless switching with the `setup` (or `use`) command.

### Option 1: Use DeepSeek (1-Step Setup)
```bash
python3 -m kimibridge.cli setup deepseek
```
*(Automatically sets provider `deepseek`, upstream base URL `https://api.deepseek.com`, and restarts the background service).*

Supported models: `deepseek-chat`, `deepseek-reasoner`, `deepseek-v3-pro`, `deepseek-flash`, `deepseek-v3`, `deepseek-r1`.

### Option 2: Use Kimi / Moonshot AI (Default)
```bash
python3 -m kimibridge.cli setup kimi
```
*(Automatically sets provider `kimi`, upstream base URL `https://api.moonshot.ai`, and restarts the background service).*

Supported models: `kimi-k3`, `moonshot-v1-8k`, `moonshot-v1-32k`, `moonshot-v1-128k`.

### Option 3: Expose All Providers Concurrently
```bash
python3 -m kimibridge.cli setup all
```
*(Exposes all supported models simultaneously in client model dropdowns).*

---

## 3. Client Setup Guides

### 🤖 Android Studio AI Assistant Setup

1. Open **Android Studio** ➔ **Settings** (or **Preferences** on macOS).
2. Navigate to **Tools** ➔ **AI Assistant** (or **LLM Provider / Custom OpenAI Provider**).
3. Select **OpenAI-compatible**.
4. Set the fields as follows:
   - **Base URL**: `http://127.0.0.1:5001/v1`
   - **API Key**: *Your API Key for the active provider*
   - **Model**: Click **Refresh** to select from discovered models (e.g. `deepseek-v3-pro`, `deepseek-chat`, or `kimi-k3`).
5. Click **Apply / Test Connection**.

---

### ⚡ Cursor IDE Setup

1. Open **Cursor Settings** (Gear icon in top right or `Ctrl+,` / `Cmd+,`).
2. Go to **Models** section.
3. Enable **OpenAI API Key** or Custom Provider.
4. Set:
   - **Override OpenAI Base URL**: `http://127.0.0.1:5001/v1`
   - **API Key**: *Your Provider API Key*
5. Add model (e.g. `deepseek-v3-pro`, `kimi-k3`).

---

### 💻 VS Code (with Continue or CodeGPT Extension)

In VS Code, add custom provider configuration (e.g. in Continue `config.json`):

```json
{
  "models": [
    {
      "title": "DeepSeek via KimiBridge",
      "provider": "openai",
      "model": "deepseek-v3-pro",
      "apiBase": "http://127.0.0.1:5001/v1",
      "apiKey": "YOUR_DEEPSEEK_API_KEY"
    }
  ]
}
```

---

### 🐍 Aider CLI Setup

```bash
export OPENAI_API_BASE="http://127.0.0.1:5001/v1"
export OPENAI_API_KEY="YOUR_API_KEY"

# With DeepSeek
aider --model openai/deepseek-v3-pro

# With Kimi
aider --model openai/kimi-k3
```

---

### 🌐 cURL Request Examples

#### Standard Chat Completion
```bash
curl http://127.0.0.1:5001/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-v3-pro",
    "messages": [
      {"role": "developer", "content": "You are an Android expert."},
      {"role": "user", "content": "Explain Coroutines vs Flow in Kotlin."}
    ]
  }'
```

#### Real-Time SSE Streaming
```bash
curl -N http://127.0.0.1:5001/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-v3-pro",
    "messages": [
      {"role": "user", "content": "Write a short poem about code."}
    ],
    "stream": true
  }'
```

---

## 4. CLI Management Commands

| Command | Action |
|---------|--------|
| `kimibridge start` | Starts the proxy server in foreground. |
| `kimibridge doctor` | Runs environment diagnostics & health check. |
| `kimibridge status` | Checks background service health. |
| `kimibridge logs` | Views background service logs. |
| `kimibridge stop` | Stops background service. |
| `kimibridge restart` | Restarts background service. |
| `kimibridge config show` | Displays active config & endpoint. |
| `kimibridge config set provider deepseek` | Configures target provider (`deepseek`, `kimi`, `openai`, `auto`). |
| `kimibridge config set base-url <url>` | Sets upstream base URL. |
| `kimibridge config set port 5002` | Changes configured port. |
| `kimibridge uninstall` | Removes service and application files. |

---

## 5. Troubleshooting & Diagnostics

Run the doctor command anytime to verify connectivity:

```bash
python3 -m kimibridge.cli doctor
```

Output example:
```text
KimiBridge Doctor
Version: 0.2.0
Config path: /home/user/.kimibridge/config.json
Configured endpoint: http://127.0.0.1:5001/v1
Provider: deepseek
Compatibility mode: compatible
Kimi base URL: https://api.deepseek.com
Port status: already_running
Health: healthy
KimiBridge health endpoint is OK.
```
