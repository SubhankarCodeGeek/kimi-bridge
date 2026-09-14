# KimiBridge User Guide

Welcome to **KimiBridge**! This guide walks you through setting up and connecting KimiBridge to your favorite IDEs, AI assistants, and developer tools.

---

## What is KimiBridge?

KimiBridge is a local, lightweight proxy server that exposes an **OpenAI-compatible API** (`http://127.0.0.1:5001/v1`) while translating requests under the hood to Kimi/Moonshot AI (`api.moonshot.ai`).

It automatically handles compatibility differences, such as:
- Mapping OpenAI `developer` role messages to Kimi-supported `system` role.
- Filtering out unsupported request parameters (`parallel_tool_calls`, `store`, `metadata`).
- Proxying real-time **Server-Sent Events (SSE)** streaming responses.

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

## 2. Client Setup Guides

### 🤖 Android Studio AI Assistant Setup

1. Open **Android Studio** ➔ **Settings** (or **Preferences** on macOS).
2. Navigate to **Tools** ➔ **AI Assistant** (or **LLM Provider / Custom OpenAI Provider**).
3. Select **OpenAI-compatible**.
4. Set the fields as follows:
   - **Base URL**: `http://127.0.0.1:5001/v1`
   - **API Key**: *Your Kimi / Moonshot API Key* (`sk-...`)
   - **Model**: `kimi-k3` (or `moonshot-v1-8k`, `moonshot-v1-32k`)
5. Click **Test Connection** or **Apply**.

---

### ⚡ Cursor IDE Setup

1. Open **Cursor Settings** (Gear icon in top right or `Ctrl+,` / `Cmd+,`).
2. Go to **Models** section.
3. Enable **OpenAI API Key** or Custom Provider.
4. Set:
   - **Override OpenAI Base URL**: `http://127.0.0.1:5001/v1`
   - **API Key**: *Your Kimi API Key*
5. Add model `kimi-k3` to model list.

---

### 💻 VS Code (with Continue or CodeGPT Extension)

1. In VS Code, open your extension settings (e.g. `config.json` for Continue extension).
2. Add custom provider configuration:

```json
{
  "models": [
    {
      "title": "Kimi via KimiBridge",
      "provider": "openai",
      "model": "kimi-k3",
      "apiBase": "http://127.0.0.1:5001/v1",
      "apiKey": "YOUR_KIMI_API_KEY"
    }
  ]
}
```

---

### 🐍 Aider CLI Setup

To use Kimi with [Aider](https://aider.chat):

```bash
export OPENAI_API_BASE="http://127.0.0.1:5001/v1"
export OPENAI_API_KEY="YOUR_KIMI_API_KEY"

aider --model openai/kimi-k3
```

---

### 🌐 cURL / HTTP Request Setup

#### Standard Chat Completion
```bash
curl http://127.0.0.1:5001/v1/chat/completions \
  -H "Authorization: Bearer YOUR_KIMI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "kimi-k3",
    "messages": [
      {"role": "user", "content": "Explain machine learning in one sentence."}
    ]
  }'
```

#### Real-Time SSE Streaming
```bash
curl -N http://127.0.0.1:5001/v1/chat/completions \
  -H "Authorization: Bearer YOUR_KIMI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "kimi-k3",
    "messages": [
      {"role": "user", "content": "Write a short poem about code."}
    ],
    "stream": true
  }'
```

---

## 3. CLI Management Commands

| Command | Action |
|---------|--------|
| `kimibridge start` | Starts the proxy server in foreground. |
| `kimibridge doctor` | Runs environment diagnostics & health check. |
| `kimibridge status` | Checks background service health. |
| `kimibridge logs` | Views background service logs. |
| `kimibridge stop` | Stops background service. |
| `kimibridge restart` | Restarts background service. |
| `kimibridge config show` | Displays active config & endpoint. |
| `kimibridge config set port 5002` | Changes configured port. |
| `kimibridge uninstall` | Removes service and application files. |

---

## 4. Troubleshooting & Diagnostics

If you encounter issues, run the doctor command:

```bash
python3 -m kimibridge.cli doctor
```

Output example:
```text
KimiBridge Doctor
Version: 0.1.0
Config path: /home/user/.kimibridge/config.json
Configured endpoint: http://127.0.0.1:5001/v1
Compatibility mode: compatible
Kimi base URL: https://api.moonshot.ai
Port status: already_running
Health: ok
KimiBridge is healthy and responding on http://127.0.0.1:5001/v1
```
