# StudioRelay User Guide

Welcome to **StudioRelay**! This guide walks you through setting up and connecting StudioRelay to Android Studio, coding assistants, and developer tools.

> **Tagline:** One IDE Agent. Multiple AI Models. Zero Vendor Lock-in.

---

## What is StudioRelay?

StudioRelay is an open-source compatibility gateway that connects Android Studio's AI agent to supported alternative LLM providers.

Android Studio's AI agent remains responsible for its agentic workflow, including understanding coding tasks, using project context, interacting with tools, and coordinating development operations. StudioRelay provides the local compatibility infrastructure between that IDE agent and your selected LLM provider.

It automatically resolves protocol divergences between agentic clients and upstream providers:
- Exposes standard OpenAI `/v1/models`, `/v1/chat/completions`, and `/v1/responses` endpoints.
- Normalizes unsupported OpenAI `developer` role messages to `system` role.
- Cleans and filters incompatible request parameters (`parallel_tool_calls`, `store`, `metadata`).
- Translates `reasoning_content` to visible text when `content` is empty so thinking models output visible answers.
- Proxies real-time **Server-Sent Events (SSE)** streaming responses with zero latency.
- Formats upstream error payloads into clean OpenAI-standard formats.

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

Once installed, StudioRelay runs automatically in the background as a user service (`systemd` / `launchd` / `Task Scheduler`).

### Option B: Run Standalone Binary directly

```bash
# Build the binary
python3 scripts/build_binary.py

# Run the binary
./dist/studiorelay-linux-x86_64 start
```

### Option C: Run Python CLI directly

```bash
studiorelay start --auto-port
# Or: python3 -m studiorelay.cli start --auto-port
```

Default Base URLs:
```text
http://127.0.0.1:5001/v1   (DeepSeek)
http://127.0.0.1:5002/v1   (Kimi / Moonshot)
```

---

## 2. Choosing Your Target Provider

StudioRelay supports provider profiles and seamless switching with the `setup` (or `use`) command.

### Option 1: Use DeepSeek (1-Step Setup)
```bash
studiorelay setup deepseek
```
*(Automatically sets provider `deepseek`, upstream base URL `https://api.deepseek.com`, and restarts the background service).*

Supported models: `deepseek-chat`, `deepseek-reasoner`, `deepseek-v3-pro`, `deepseek-flash`, `deepseek-v3`, `deepseek-r1`.

### Option 2: Use Kimi / Moonshot AI
```bash
studiorelay setup kimi
```
*(Automatically sets provider `kimi`, upstream base URL `https://api.moonshot.ai`, and restarts the background service).*

Supported models: `kimi-k3`, `moonshot-v1-8k`, `moonshot-v1-32k`, `moonshot-v1-128k`.

### Option 3: Expose All Providers Concurrently
```bash
studiorelay setup all
```
*(Exposes all supported models simultaneously in client model dropdowns).*

---

## 3. Client Setup Guides

### 🤖 Android Studio AI Assistant Setup

With StudioRelay, you can run and configure **both DeepSeek and Kimi simultaneously** on separate local ports without any model list conflict:

#### DeepSeek Provider:
1. Open **Android Studio** ➔ **Settings** (or **Preferences** on macOS).
2. Navigate to **Tools** ➔ **AI Assistant** (or **LLM Provider / Custom OpenAI Provider**).
3. Select **OpenAI-compatible**.
4. Set the fields:
   - **Base URL**: `http://127.0.0.1:5001/v1` *(or your configured DeepSeek port)*
   - **API Key**: *Your DeepSeek API Key*
5. Click **Refresh**: Populates with `deepseek-chat`, `deepseek-reasoner`, `deepseek-v3-pro`, `deepseek-flash`.
6. Click **Apply**.

#### Kimi / Moonshot Provider:
1. Add a second custom OpenAI-compatible entry in Android Studio (or switch between profiles).
2. Set the fields:
   - **Base URL**: `http://127.0.0.1:5002/v1` *(or your configured Kimi port)*
   - **API Key**: *Your Kimi / Moonshot API Key*
3. Click **Refresh**: Populates with `kimi-k3`, `moonshot-v1-8k`, `moonshot-v1-32k`, etc.
4. Click **Apply**.

Both providers run independently in the background on separate ports. Refreshing models in one provider never overwrites or shows models from the other!

---

## 4. CLI Management Commands

| Command | Action |
|---------|--------|
| `studiorelay start` | Starts the proxy server in foreground. |
| `studiorelay doctor` | Runs environment diagnostics & health check. |
| `studiorelay status` | Checks background service health. |
| `studiorelay logs` | Views background service logs. |
| `studiorelay stop` | Stops background service. |
| `studiorelay restart` | Restarts background service. |
| `studiorelay config show` | Displays active config & endpoint. |
| `studiorelay config set provider deepseek` | Configures target provider (`deepseek`, `kimi`, `openai`, `auto`). |
| `studiorelay config set base-url <url>` | Sets upstream base URL. |
| `studiorelay config set port 5003` | Changes configured port. |
| `studiorelay migrate` | Safely migrates configurations from `~/.kimibridge/` to `~/.studiorelay/`. |
| `studiorelay uninstall` | Removes service and application files. |

*(Legacy command `kimibridge <action>` is supported identically)*

---

## 5. Troubleshooting & Diagnostics

Run the doctor command anytime to verify connectivity:

```bash
studiorelay doctor
```

Output example:
```text
StudioRelay Doctor (DEEPSEEK)
Version: 0.3.0
Python: 3.12.3
Config path: /home/user/.studiorelay/config-deepseek.json
Configured endpoint: http://127.0.0.1:5001/v1
Provider: deepseek
Compatibility mode: compatible
Upstream base URL: https://api.deepseek.com
Upstream fallback base URL: None
Port status: already_running
StudioRelay (deepseek) is already running on port 5001.
Health: healthy
Gateway health endpoint is OK.
```
