# Troubleshooting

## Port Already In Use

StudioRelay defaults to:

- `127.0.0.1:5001` (DeepSeek)
- `127.0.0.1:5002` (Kimi)

To let StudioRelay choose another available port:

```bash
studiorelay start --auto-port
```

Use the printed endpoint in Android Studio.

To set a port manually:

```bash
studiorelay config set port 5003
studiorelay start
```

To inspect the current endpoint:

```bash
studiorelay config show
```

To check whether the proxy is running:

```bash
studiorelay status
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
Route requests through StudioRelay at `http://127.0.0.1:5001/v1`. StudioRelay intercepts the request and normalizes `developer` ➔ `system`, allowing the request to deserialize cleanly upstream.

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
The client is calling `POST /v1/responses`. Standard LLMs only implement `POST /v1/chat/completions`, so model discovery could work while agentic inference failed.

### Fix:
Update StudioRelay and restart the background service. StudioRelay translates `POST /v1/responses` into the upstream Chat Completions schema, then translates the completion or stream events back into Responses API format.

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
Update StudioRelay and restart the background service. StudioRelay keeps legacy names visible for client compatibility, but rewrites them before forwarding upstream:

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
Android Studio shows the model as generating or generated, but no assistant text appears.

### Cause:
DeepSeek can return thinking output in `reasoning_content` before or instead of final `content`. When final `content` is empty, an ordinary gateway leaves the answer blank.

### Fix:
StudioRelay uses `reasoning_content` as a fallback visible output whenever final `content` is empty.

---

## HTTP 403 with Kimi / Moonshot

### Symptom:
Requests through StudioRelay fail with:

```text
403 Forbidden
```

or an OpenAI-style error whose code is `upstream_permission_denied`.

### Common causes:

- The API key does not belong to the configured provider. Moonshot Open Platform keys and other Kimi credentials are not interchangeable.
- The configured base URL is stale after switching providers. For the Moonshot Open Platform, use `https://api.moonshot.ai` or `https://api.moonshot.ai/v1`.
- Android Studio is still sending a model from another provider after a provider switch. Refresh the model list and select a `kimi-*` or `moonshot-*` model for Kimi.
- The account or key does not have permission for the selected model.

### Fix:

```bash
studiorelay setup kimi
studiorelay restart
studiorelay config show
```

Then use your Moonshot/Kimi API key in the client and refresh the model dropdown.

---

## Model Dropdown Showing Outdated Models

If Android Studio displays models from another provider (e.g. `kimi-k3` instead of DeepSeek models):

1. Switch your provider with a single command:
   ```bash
   studiorelay setup deepseek
   ```
   *(Or for Kimi: `studiorelay setup kimi`, or for all models: `studiorelay setup all`)*

   This command automatically:
   - Sets the target provider (`deepseek`)
   - Configures the matching upstream base URL (`https://api.deepseek.com`)
   - Restarts the background service to apply changes immediately

2. In Android Studio, click **Refresh** on the models dropdown. DeepSeek models (`deepseek-chat`, `deepseek-v3-pro`, `deepseek-flash`, etc.) will appear.

---

## Background Service Management

### Linux (`systemd --user`)
On Linux hosts, StudioRelay runs as a `systemd --user` service named `studiorelay-<provider>` (e.g. `studiorelay-deepseek`):

```bash
# View recent service logs
studiorelay logs

# Query systemd directly
systemctl --user status studiorelay-deepseek
journalctl --user -u studiorelay-deepseek -n 50 --no-pager

# Restart service
studiorelay restart
```

*(Legacy services named `kimibridge-*` or `kimibridge` remain recognized)*

### macOS (`launchd`)
On macOS hosts, StudioRelay runs as a LaunchAgent:

```bash
studiorelay restart
studiorelay logs
```

### Windows (Task Scheduler)
On Windows hosts, StudioRelay runs via Task Scheduler as `StudioRelay`:

```powershell
studiorelay restart
studiorelay doctor
```

---

## Installation Issues

### `fatal: destination path 'studio-relay' already exists and is not an empty directory`

This happens when `git clone` is executed while a directory already exists locally. To update your installation:

```bash
cd studio-relay
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

## Migrating from KimiBridge to StudioRelay

To migrate an existing installation safely:

1. Safely migrate configuration:
   ```bash
   studiorelay migrate --dry-run
   studiorelay migrate
   ```
2. Reinstall background services:
   ```bash
   ./installers/install.sh
   ```
3. Run diagnostics to confirm healthy operation:
   ```bash
   studiorelay doctor
   ```
The installer automatically stops the previous `kimibridge` service to avoid port collisions and starts the new `studiorelay` service.
