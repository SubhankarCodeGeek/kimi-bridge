# StudioRelay

### Connect Android Studio's AI Agent to the AI Models You Choose.

> **Tagline:** One IDE Agent. Multiple AI Models. Zero Vendor Lock-in.

---

## Overview

Android Studio's AI agent is powerful, but connecting it to alternative AI providers can involve compatibility challenges.

StudioRelay is an open-source compatibility gateway designed to bridge that gap.

It translates API requests and responses between Android Studio's AI agent and supported LLM providers, helping different models work within the same agentic development workflow.

Use Kimi. Use DeepSeek. Add more providers. Keep your IDE agent.

Android Studio's AI agent remains responsible for its agentic workflow, including understanding coding tasks, using project context, interacting with tools, and coordinating development operations. StudioRelay provides the local compatibility infrastructure between that IDE agent and your selected LLM provider, handling the protocol adaptation necessary for supported providers to work with the IDE's expected API behavior.

---

## Problem Statement

When connecting Android Studio's AI agent to alternative LLM providers (such as DeepSeek or Kimi / Moonshot AI), developers frequently encounter API protocol divergences:

1. **Unsupported Message Roles (`HTTP 422: unknown variant developer`)**: Android Studio sends system/developer prompts with `role: "developer"`. Strict upstream APIs (such as DeepSeek's deserializer) reject this role before inference begins.
2. **Missing Endpoint (`POST /v1/responses 404`)**: Android Studio AI Assistant calls the newer OpenAI Responses API (`/v1/responses`). Most alternative LLM providers only expose `/v1/chat/completions`.
3. **Incompatible Request Parameters**: Parameters like `store`, `metadata`, or `parallel_tool_calls` trigger deserialization errors on alternative providers.
4. **Blank Thinking Output**: Models like DeepSeek Reasoner emit thinking in `reasoning_content` while leaving final `content` empty, causing standard OpenAI clients to display blank answers.
5. **Port and Service Conflicts**: Running multiple alternative providers simultaneously typically causes port collisions and model dropdown confusion.

---

## How StudioRelay Works

StudioRelay acts as a transparent, high-performance local proxy:

1. **Local Gateway**: Binds locally (`127.0.0.1:5001` for DeepSeek, `127.0.0.1:5002` for Kimi) with zero external exposure.
2. **Protocol Adaptation**: Intercepts `/v1/chat/completions` and `/v1/responses`, maps `developer` messages to `system`, filters unsupported parameters, and translates Responses API schemas into Chat Completions.
3. **Reasoning Fallback**: When thinking models return `reasoning_content` with empty final `content`, StudioRelay surfaces the reasoning as visible text so answers are never blank.
4. **Zero-Latency Streaming**: Translates Server-Sent Events (SSE) line-by-line in real time.
5. **Dual Service Isolation**: Runs dedicated background service daemons on separate ports so both DeepSeek and Kimi can be active in Android Studio simultaneously.

---

## Architecture Overview

```text
                  Android Studio AI Agent
           (or Cursor, VS Code, Aider, Open WebUI)
                             │
                             ▼
                    ┌──────────────────┐
                    │   StudioRelay    │
                    │  Local Gateway   │
                    │  (127.0.0.1)     │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  Compatibility   │
                    │      Engine      │
                    │ - Role Adapter   │
                    │ - Param Filter   │
                    │ - Responses API  │
                    │ - Reasoning Map  │
                    └────────┬─────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
     DeepSeek Profile               Kimi/Moonshot Profile
     (Port 5001 / v1)               (Port 5002 / v1)
              │                             │
              ▼                             ▼
       api.deepseek.com              api.moonshot.ai
```

---

## Supported Providers

- **DeepSeek** (`https://api.deepseek.com`):
  - Supported models: `deepseek-chat`, `deepseek-reasoner`, `deepseek-v3-pro`, `deepseek-flash`, `deepseek-v3`, `deepseek-r1`
  - Automatic alias rewriting: `deepseek-chat` ➔ `deepseek-flash`, `deepseek-reasoner` ➔ `deepseek-flash` with `reasoning_effort=high`, `deepseek-v3-pro` ➔ `deepseek-v4-pro`
  - Normalizes `developer` role to `system` to prevent HTTP 422 errors
  - Normalizes `reasoning_content` fallback when `content` is empty
- **Kimi / Moonshot AI** (`https://api.moonshot.ai`):
  - Supported models: `kimi-k3`, `moonshot-v1-8k`, `moonshot-v1-32k`, `moonshot-v1-128k`
  - Normalizes `developer` role to `system`
  - Strips unsupported parameters (`store`, `metadata`, `parallel_tool_calls`)
- **OpenAI / Generic Passthrough**:
  - Preserves standard schema for native OpenAI endpoints or generic proxies

---

## Features

- ⚡ **Zero-Latency Streaming**: Line-by-line SSE chunk forwarding.
- 🔄 **Responses API Bridge**: Seamless support for Android Studio's `/v1/responses` queries.
- 🧠 **Reasoning Fallback**: Always displays reasoning content if final content is empty.
- 🛡️ **Zero Secret Logging**: Never logs `Authorization` headers, API keys, or tokens.
- 🔌 **Intelligent Port Allocation**: Automatically detects port availability and avoids conflicts (`--auto-port`).
- 🖥️ **Background Service Daemons**: Native `systemd` user units on Linux, `launchd` LaunchAgents on macOS, and `Task Scheduler` on Windows.
- 📦 **Zero Runtime Dependencies**: Built entirely on the Python Standard Library (`http.server`, `urllib`, `dataclasses`, `argparse`).
- 🔙 **Full Backward Compatibility**: Seamlessly supports existing `kimibridge` commands, imports, configurations, and service files.

---

## Prerequisites

- **Python**: `3.10+` (3.10, 3.11, or 3.12)
- **Operating System**:
  - **Linux**: `systemd` with user session support (`systemctl --user`), `procps`
  - **macOS**: macOS 11.0 (Big Sur) or newer with `launchd`
  - **Windows**: Windows 10/11 with PowerShell 5.1+ and Task Scheduler
- **Git**: `2.20+`

---

## Installation

### Method 1: Install via PyPI (Recommended & Fastest)

Install the latest release directly using `pipx` (recommended) or `pip`:

```bash
pipx install studiorelay
```

*(Alternatively, with standard pip: `pip install --user studiorelay`)*

> [!TIP]
> **First-time `pipx` / `pip` users:** If your terminal says `studiorelay: command not found`, reload your shell so `~/.local/bin` is added to your active `$PATH`:
> ```bash
> source ~/.bashrc
> ```
> *(Or open a fresh terminal window).*

#### Verify Installation

Check that the CLI is ready:

```bash
studiorelay --version
```
Expected output:
```text
StudioRelay 0.3.0
```

---

#### Next Steps for the User

1. **Configure your target provider:**

   For **DeepSeek** (default port: `5001`):
   ```bash
   studiorelay setup deepseek
   ```

   For **Kimi / Moonshot** (default port: `5002`):
   ```bash
   studiorelay setup kimi
   ```

   **Terminal output:**
   ```text
   StudioRelay configured for provider: DEEPSEEK
     Target Provider:   deepseek
     Upstream Base URL: https://api.deepseek.com
     Proxy Endpoint:    http://127.0.0.1:5001/v1
     Saved to:          ~/.studiorelay/config-deepseek.json
     Available Models:  deepseek-flash, deepseek-v4-pro, deepseek-chat, deepseek-reasoner, deepseek-v3, deepseek-v3-pro...

   In Android Studio / Cursor / Aider:
     1. Set Base URL: http://127.0.0.1:5001/v1
     2. Enter your DeepSeek API Key
     3. Click Refresh: Models will load into the dropdown!
   ```

2. **Start the gateway:**

   ```bash
   studiorelay start --provider deepseek --auto-port &
   ```
   *(Or run in foreground: `studiorelay start --provider deepseek`)*

3. **Verify the gateway:**

   ```bash
   studiorelay doctor
   ```

---

### Method 2: Git Clone & Daemon Installer Scripts

If you want automated background daemons (`systemd` user units on Linux, `launchd` on macOS, or `Task Scheduler` on Windows):

#### 1-Step Setup for DeepSeek

**Linux / macOS:**
```bash
git clone https://github.com/SubhankarCodeGeek/studio-relay.git
cd studio-relay
./installers/install-deepseek.sh
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/SubhankarCodeGeek/studio-relay.git
cd studio-relay
.\installers\install-deepseek.ps1
```

#### 1-Step Setup for Kimi / Moonshot AI

**Linux / macOS:**
```bash
./installers/install-kimi.sh
```

**Windows (PowerShell):**
```powershell
.\installers\install.ps1 -Kimi
```

#### Interactive Multi-Provider Installer

- **Linux / macOS:** `./installers/install.sh`
- **Windows (PowerShell):** `.\installers\install.ps1`

The installer sets up application files in `~/.studiorelay/app` and registers your background service automatically.

---

## Upgrade from KimiBridge

StudioRelay provides a safe, non-destructive upgrade path for existing KimiBridge installations:

1. **Step 1: Migrate Configuration (Optional, installer also handles this)**
   ```bash
   studiorelay migrate --dry-run
   studiorelay migrate
   ```
   This safely copies configs from `~/.kimibridge/` to `~/.studiorelay/` with an automated timestamped backup in `~/.kimibridge/backups/`. Secrets are never logged.

2. **Step 2: Update Application & Services**
   ```bash
   cd studio-relay && git pull origin main
   ./installers/install.sh
   ```
   The installer automatically detects active legacy `kimibridge-*.service` units, stops and disables them to prevent port collisions, and enables the new `studiorelay-*.service`.

3. **Step 3: Verify Upgrade**
   ```bash
   studiorelay doctor
   ```

*(Note: Legacy `kimibridge` commands and `~/.kimibridge` configuration files remain fully functional via backward-compatibility aliases).*

---

## Android Studio Configuration

Configure supported providers in Android Studio without touching IDE internals:

### 1. Configure DeepSeek
1. Open **Android Studio** ➔ **Settings** (or **Preferences** on macOS) ➔ **Tools** ➔ **AI Assistant**.
2. Select **Custom OpenAI Provider** (or OpenAI-compatible).
3. Set **Base URL**: `http://127.0.0.1:5001/v1`
4. Set **API Key**: *Your DeepSeek API Key*
5. Click **Refresh** to populate models (`deepseek-chat`, `deepseek-reasoner`, `deepseek-v3-pro`, `deepseek-flash`).
6. Click **Apply**.

### 2. Configure Kimi / Moonshot AI
1. Add a second OpenAI-compatible provider entry in Android Studio.
2. Set **Base URL**: `http://127.0.0.1:5002/v1`
3. Set **API Key**: *Your Moonshot / Kimi API Key*
4. Click **Refresh** to populate models (`kimi-k3`, `moonshot-v1-8k`, etc.).
5. Click **Apply**.

Both providers run concurrently in the background with zero port collisions and zero dropdown interference!

---

## Provider Configuration

Switch or reconfigure target providers anytime:

```bash
# Switch to DeepSeek
studiorelay setup deepseek

# Switch to Kimi / Moonshot
studiorelay setup kimi

# Expose both provider model lists concurrently
studiorelay setup all
```

---

## CLI Usage

StudioRelay provides a complete management CLI:

```bash
# Check version
studiorelay --version

# Show help
studiorelay --help

# Run comprehensive system diagnostics
studiorelay doctor

# Inspect running provider endpoints
studiorelay status

# View recent service logs
studiorelay logs
studiorelay logs --provider deepseek

# Start server in foreground (development mode)
studiorelay start --auto-port

# Migrate legacy configurations
studiorelay migrate
```

*(The `kimibridge` CLI executable is also installed as an alias to `studiorelay`).*

---

## Configuration Management

Configuration precedence is strictly deterministic:

1. **Explicit path argument** (`--config /path/to/config.json`)
2. **`STUDIORELAY_CONFIG`** environment variable
3. **`KIMIBRIDGE_CONFIG`** environment variable (legacy)
4. **StudioRelay directory** (`~/.studiorelay/config-<provider>.json` or `config.json`)
5. **Legacy KimiBridge directory** (`~/.kimibridge/config-<provider>.json` or `config.json`)

To inspect or update settings:

```bash
# View active configuration (secrets masked)
studiorelay config show

# Set custom port
studiorelay config set port 5003

# Set custom upstream base URL
studiorelay config set base-url https://api.deepseek.com

# Change compatibility mode
studiorelay config set compatibility-mode compatible
```

---

## Service Management

### Linux (`systemd --user`)
```bash
# Check service status
systemctl --user status studiorelay-deepseek

# View journal logs
journalctl --user -u studiorelay-deepseek -n 50 --no-pager

# Restart service via CLI
studiorelay restart --provider deepseek
```

### macOS (`launchd`)
```bash
studiorelay restart
studiorelay logs
```

### Windows (Task Scheduler)
```powershell
studiorelay restart
studiorelay status
```

---

## Health Checks

StudioRelay provides local health diagnostic endpoints:

```bash
# Check JSON health endpoint
curl http://127.0.0.1:5001/health

# Output:
# {"status": "ok", "service": "kimibridge", "gateway": "studiorelay", "provider": "deepseek", "port": 5001}
```

Or run `studiorelay doctor` for complete endpoint validation.

---

## Troubleshooting

- **Port in Use**: If port 5001 is already taken by another application, run `studiorelay start --auto-port` or `studiorelay setup deepseek --port 5003`.
- **422 Unknown Variant Developer**: Ensure Android Studio base URL points to `http://127.0.0.1:5001/v1` so StudioRelay normalizes the message role.
- **Empty Thinking Output**: Ensure you are running StudioRelay 0.3.0+, which automatically extracts `reasoning_content` into visible output.
- **For more solutions**, see [Troubleshooting Guide](docs/troubleshooting.md).

---

## Security

- **Localhost Loopback Only**: The server binds exclusively to `127.0.0.1`.
- **Credential Safety**: StudioRelay never logs, saves, or prints `Authorization` headers or API keys.
- **Client Header Forwarding**: API keys entered in Android Studio are forwarded directly to upstream providers via secure HTTPS.
- For complete details, see [Security Policy](SECURITY.md).

---

## Development Setup

```bash
# Clone the repository
git clone https://github.com/SubhankarCodeGeek/studio-relay.git
cd studio-relay

# (Optional) Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Verify bytecode compilation
python3 -m compileall studiorelay kimibridge tests
```

---

## Running Tests

Run the full automated unit and integration test suite:

```bash
python3 -m unittest discover -s tests
```

All tests execute with local mocks and require zero external API credits or credentials.

---

## Contributing

We welcome contributions! Please review our [Contributing Guide](CONTRIBUTING.md) for architecture details, testing conventions, and pull request guidelines.

---

## License

[MIT](LICENSE) © StudioRelay contributors.
