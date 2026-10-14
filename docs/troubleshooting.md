# Troubleshooting

## Port Already In Use

KimiBridge defaults to:

```text
127.0.0.1:5001
```

To let KimiBridge choose another available port:

```bash
python3 -m kimibridge.cli start --auto-port
```

Use the printed endpoint in Android Studio.

To set a port manually:

```bash
python3 -m kimibridge.cli config set port 5002
python3 -m kimibridge.cli start
```

To inspect the current endpoint:

```bash
python3 -m kimibridge.cli config show
```

To check whether the proxy is running:

```bash
python3 -m kimibridge.cli status
```

---

## HTTP 422: `unknown variant developer` (DeepSeek / Kimi)

### Symptom:
When querying DeepSeek or Kimi directly from Android Studio or another agentic IDE, queries fail with:
```text
422: Failed to deserialize the JSON body into the target type: 
messages[0].role: unknown variant developer, 
expected one of system, user, assistant, tool, latest_reminder
```

### Cause:
Android Studio and modern coding agents inject system/developer prompts with `role: "developer"`. Strict upstream API proxies (such as DeepSeek's Rust/Serde deserializer) reject the `developer` role before the request ever reaches the LLM.

### Fix:
Route requests through KimiBridge at `http://127.0.0.1:5001/v1`. KimiBridge intercepts the request and normalizes `developer` ➔ `system`, allowing the request to deserialize cleanly upstream.

---

## Android Studio: `useResponsesAPI=true` then `404 Not found`

### Symptom:
Android Studio logs show a request failure similar to:

```text
OpenAI streamGenerateContent failed
with flags: [streaming=true, useResponsesAPI=true, reasoningEffort=true]
Falling back to Completion API. Error: 404: Not found
No ModelResponse at all
```

### Cause:
The client is calling `POST /v1/responses`. Older KimiBridge versions only implemented `GET /v1/models` and `POST /v1/chat/completions`, so model discovery could work while inference failed.

### Fix:
Update KimiBridge and restart the background service. Current versions translate `POST /v1/responses` into the upstream Chat Completions schema, then translate the completion or stream events back into Responses API format.

---

## DeepSeek: HTTP 400 with `deepseek-v3`, `deepseek-v3-pro`, or `deepseek-reasoner`

### Symptom:
Requests fail with an upstream HTTP 400 after selecting a DeepSeek model such as:

```text
deepseek-v3
deepseek-v3-pro
deepseek-reasoner
deepseek-chat
```

### Cause:
The current DeepSeek API accepts `deepseek-flash` and `deepseek-v4-pro` as model IDs. Older IDE configs and dropdown entries may still use legacy or marketing-style names such as `deepseek-v3-pro`.

### Fix:
Update KimiBridge and restart the background service. Current versions keep the legacy names visible for client compatibility, but rewrite them before forwarding upstream:

```text
deepseek-chat      -> deepseek-flash
deepseek-reasoner  -> deepseek-flash + reasoning_effort=high
deepseek-v3        -> deepseek-flash
deepseek-v3-pro    -> deepseek-v4-pro
```

For new configurations, prefer selecting `deepseek-flash` or `deepseek-v4-pro` directly.

---

## DeepSeek: Generated Status but No Output

### Symptom:
When using KimiBridge, Android Studio shows the model as generating or generated, but no assistant text appears.

### Cause:
DeepSeek can return thinking output in `reasoning_content` before or instead of final `content`. Older KimiBridge versions only translated `content` into Responses API `output_text`, so a successful HTTP 200 stream could complete with an empty visible answer.

### Fix:
Update KimiBridge and restart the background service. Current versions use `reasoning_content` as a fallback visible output when final `content` is empty.

---

## HTTP 403 with Kimi / Moonshot

### Symptom:
Requests through KimiBridge fail with:

```text
403 Forbidden
```

or an OpenAI-style error whose code is `upstream_permission_denied`.

### Common causes:

- The API key does not belong to the configured provider. Moonshot Open Platform keys and other Kimi/Kimi Code credentials are not interchangeable.
- The configured base URL is stale after switching providers. For the Moonshot Open Platform, use `https://api.moonshot.ai` or `https://api.moonshot.ai/v1`; KimiBridge normalizes either form internally.
- Android Studio is still sending a model from another provider after a provider switch. Refresh the model list and select a `kimi-*` or `moonshot-*` model for Kimi.
- The account or key does not have permission for the selected model.

### Fix:

```bash
python3 -m kimibridge.cli setup kimi
python3 -m kimibridge.cli restart
python3 -m kimibridge.cli config show
```

Then use your Moonshot/Kimi API key in the client and refresh the model dropdown.

---

## Model Dropdown Showing Outdated Models

If Android Studio displays models from another provider (e.g. `kimi-k3` instead of DeepSeek models):

1. Switch your provider with a single command:
   ```bash
   python3 -m kimibridge.cli setup deepseek
   ```
   *(Or for Kimi: `python3 -m kimibridge.cli setup kimi`, or for all models: `python3 -m kimibridge.cli setup all`)*

   This command automatically:
   - Sets the target provider (`deepseek`)
   - Configures the matching upstream base URL (`https://api.deepseek.com`)
   - Restarts the background service to apply changes immediately

2. In Android Studio, click **Refresh** on the models dropdown. DeepSeek models (`deepseek-chat`, `deepseek-v3-pro`, `deepseek-flash`, etc.) will appear.

---

## Background Service Management

### Linux (`systemd --user`)
On Linux hosts, KimiBridge runs as a `systemd --user` service named `kimibridge`.

```bash
# View recent service logs
python3 -m kimibridge.cli logs

# Query systemd directly
systemctl --user status kimibridge
journalctl --user -u kimibridge -n 50 --no-pager

# Restart service
python3 -m kimibridge.cli restart
```

### macOS (`launchd`)
On macOS hosts, KimiBridge runs as a LaunchAgent:

```bash
python3 -m kimibridge.cli restart
python3 -m kimibridge.cli logs
```

### Windows (Task Scheduler)
On Windows hosts, KimiBridge runs via Task Scheduler as `KimiBridge`:

```powershell
python -m kimibridge.cli restart
python -m kimibridge.cli doctor
```

---

## Installation Issues

### `fatal: destination path 'kimi-bridge' already exists and is not an empty directory`

This happens when `git clone` is executed while a `kimi-bridge` folder already exists locally. To update your installation:

```bash
cd kimi-bridge
git pull origin main
./installers/install-deepseek.sh
```

### `bash: ./installers/install-deepseek.sh: Permission denied`

This happens if file execution permissions are restricted on the cloned files. To resolve:

```bash
chmod +x installers/*.sh
./installers/install-deepseek.sh
```

Or execute directly through `bash`:

```bash
bash ./installers/install-deepseek.sh
```

---

## Upgrading KimiBridge

When updating to a new version of KimiBridge:

1. Pull the latest repository updates:
   ```bash
   cd kimi-bridge
   git pull origin main
   ```
2. Run the installer:
   ```bash
   # macOS / Linux (DeepSeek)
   ./installers/install-deepseek.sh

   # macOS / Linux (General)
   ./installers/install.sh

   # Windows
   .\installers\install.ps1
   ```
The installer automatically preserves your existing configuration file (`~/.kimibridge/config.json`), updates the application files, and restarts the background service.
