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

## Model Dropdown Showing Outdated Models

If Android Studio displays models from another provider (e.g. `kimi-k3` instead of DeepSeek models):

1. Confirm your configured provider in KimiBridge:
   ```bash
   python3 -m kimibridge.cli config set provider deepseek
   python3 -m kimibridge.cli config set base-url https://api.deepseek.com
   ```
2. Restart the background service to reload the updated configuration:
   ```bash
   python3 -m kimibridge.cli restart
   ```
3. In Android Studio, click **Refresh** on the models dropdown.

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

## Upgrading KimiBridge

When updating to a new version of KimiBridge:

1. Pull the latest repository updates:
   ```bash
   git pull
   ```
2. Run the installer:
   ```bash
   # macOS / Linux
   ./installers/install.sh

   # Windows
   .\installers\install.ps1
   ```
The installer automatically preserves your existing configuration file (`~/.kimibridge/config.json`), updates the application files, and restarts the background service.
