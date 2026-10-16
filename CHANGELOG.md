# Changelog

## 0.3.1

- **Automated PATH Detection & Shell Configuration**:
  - Automatically detect if `~/.local/bin` is in active `$PATH`.
  - Safely add `export PATH="$HOME/.local/bin:$PATH"` to `~/.bashrc`, `~/.zshrc`, and `~/.profile` when missing.
  - Install direct launcher script in `~/.local/bin/studiorelay` and symlink `kimibridge`.
  - Provide clear in-terminal reload guidance (`source ~/.bashrc`) and zero-PATH alternative (`python3 -m studiorelay <command>`).

## 0.3.0

- **Project Rebranding: KimiBridge → StudioRelay**:
  - Rebrand the project identity to **StudioRelay** ("*One IDE Agent. Multiple AI Models. Zero Vendor Lock-in.*").
  - Introduce primary Python distribution and package namespace: `studiorelay`.
  - Introduce primary CLI executable: `studiorelay` (with subcommands `start`, `setup`, `doctor`, `status`, `stop`, `restart`, `logs`, `config`, `migrate`, `uninstall`).
- **Full Backward Compatibility Layer**:
  - Preserve `kimibridge` Python package as an import alias that delegates to `studiorelay`.
  - Register `kimibridge` console entry point pointing to the same CLI runner so existing scripts and tools remain functional.
  - Support `python3 -m kimibridge.cli` execution seamlessly.
- **Configuration & Migration**:
  - Introduce `~/.studiorelay/` as the new configuration directory while preserving existing `~/.kimibridge/` installations.
  - Implement deterministic configuration precedence: `STUDIORELAY_CONFIG` > `KIMIBRIDGE_CONFIG` > `~/.studiorelay/` > `~/.kimibridge/`.
  - Add `studiorelay migrate` command supporting `--dry-run` and safe execution with timestamped backups and zero secret exposure.
- **Service & Installer Lifecycle**:
  - Introduce `studiorelay.service` and `studiorelay-<provider>.service` systemd user service definitions and macOS `com.studiorelay.proxy.plist` descriptors.
  - Upgrade `installers/install.sh`, `installers/uninstall.sh`, and PowerShell equivalents to detect legacy `kimibridge` services, stopping them cleanly to prevent port collisions.
  - Preserve user configuration files during installation, updates, and uninstallation.
- **Android Studio & Provider Compatibility**:
  - Retain 100% compatibility with Android Studio's AI agent across `/v1/chat/completions`, `/v1/responses`, and `/v1/models`.
  - Preserve DeepSeek and Kimi/Moonshot support, `developer` ➔ `system` role normalization, reasoning-to-visible-text fallback, and SSE streaming.

## 0.2.3

- **Concurrent Multi-Provider Hosting & Port Isolation**:
  - Store provider configurations separately (`~/.kimibridge/config-kimi.json`, `~/.kimibridge/config-deepseek.json`) so installing one provider never overwrites or stops another.
  - Implement smart port collision detection: when port `5001` is already hosting another provider, automatically assign the next available port (e.g. `5002`) so Android Studio can configure both providers simultaneously with zero model list conflict.
  - Support explicit `--port` overrides in all installers (`install.sh`, `install-deepseek.sh`, `install-kimi.sh`, `install.ps1`, `install-deepseek.ps1`, `install-kimi.ps1`) and CLI commands.
  - Run provider-specific background services (`kimibridge-kimi`, `kimibridge-deepseek`) concurrently across Linux (`systemd`), macOS (`launchd`), and Windows (`Task Scheduler`).
  - Update `/health` endpoint to report running provider and port, with fallback model-inspection heuristic for backwards compatibility with legacy instances.
  - Add multi-instance reporting to `kimibridge status` and `kimibridge doctor`, listing all active provider endpoints at a glance.
  - Update `uninstall.sh` and `uninstall.ps1` to support `--provider <name>` (removes only that provider's service without touching shared binaries or other providers) and `--all`.
  - Add `install-kimi.ps1` for PowerShell installer parity.

## 0.2.2

- Add `POST /v1/responses` compatibility for clients that use the OpenAI Responses API, including Android Studio.
- Translate Responses `input`, `instructions`, `max_output_tokens`, function tools, and streaming requests into upstream Chat Completions requests.
- Translate upstream Chat Completions responses and SSE chunks back into Responses API JSON and streaming event shapes.
- Prefer explicit model-family detection over stale configured base URLs to avoid sending Kimi and DeepSeek requests to the wrong provider.
- Normalize upstream HTTP 403 responses as permission errors with clearer troubleshooting guidance.
- Rewrite legacy DeepSeek model aliases such as `deepseek-chat`, `deepseek-reasoner`, `deepseek-v3`, and `deepseek-v3-pro` to current upstream model IDs before forwarding.
- Map Responses API `reasoning.effort` to DeepSeek Chat Completions `reasoning_effort`.
- Fall back to DeepSeek `reasoning_content` when a successful response contains no final `content`, preventing blank generated responses in strict clients.

## 0.2.1

- Add dedicated `kimibridge setup <provider>` and `kimibridge use <provider>` commands for 1-step switching (e.g. `setup deepseek`, `setup kimi`, `setup all`).
- Automatically synchronize provider and default upstream base URL when setting either `provider` or `base-url`.
- Automatically restart running background services on configuration changes so updates take effect immediately.
- Enable live dynamic configuration reloading in `KimiBridgeServer`.
- Prioritize detected provider from base URL and requested model in `/v1/models` and `/v1/chat/completions`.
- Order DeepSeek models first in `/v1/models` when connected to DeepSeek or when provider is `all`.
- Strip trailing `/v1` from upstream base URLs to prevent `/v1/v1` path concatenation issues.
- Support `--provider` and `--base-url` flags as well as `KIMIBRIDGE_PROVIDER` in `install.sh` and `install.ps1`.

## 0.2.0

- Evolve KimiBridge from single-provider proxy to a **Provider-Aware Compatibility Engine**.
- Add `ProviderProfile` abstraction for Kimi, DeepSeek, OpenAI, and generic upstreams.
- Add provider auto-detection based on model naming heuristics (`deepseek-*`, `kimi-*`, `moonshot-*`, `gpt-*`), upstream base URLs, and explicit `X-Bridge-Provider` request headers.
- Support DeepSeek Chat Completions compatibility:
  - Normalize unsupported `developer` role to `system` role before reaching upstream Serde deserializer.
  - Handle large agentic request payloads (50KB+) and recalculate HTTP `Content-Length`.
  - Expose DeepSeek models (`deepseek-chat`, `deepseek-reasoner`, `deepseek-v3-pro`, `deepseek-flash`) via `/v1/models`.
  - Normalize DeepSeek HTTP 422 deserialization errors (`unknown variant developer`) to OpenAI-compliant `invalid_request_error` format.
- Add CLI configuration support for providers: `kimibridge config set provider <name>`.
- Update `doctor` command to inspect active provider profile and diagnostics.
- Ensure installers (`install.sh` and `install.ps1`) preserve existing user configuration files across updates.
- Add comprehensive test fixtures and integration tests for DeepSeek chat completions and error translation.

## 0.1.0

- Bootstrap repository foundation.
- Add platform-neutral proxy skeleton.
- Add graceful port resolution design and tests.
- Add compatibility pipeline scaffolding.
- Add upstream client module.
- Add OpenAI-style upstream error normalization.
- Add `config show` and `config set` CLI commands.
- Add `status` command and richer `doctor` output.
- Add source-install scaffolding for macOS, Linux, and Windows.
- Add launchd, systemd user service, and Task Scheduler templates.
- Add service-management CLI commands for `stop`, `restart`, and `logs`.
- Add `uninstall` CLI command.
- Add mocked upstream integration tests for health, models, and chat completion forwarding.
- Add graceful foreground server shutdown on keyboard interrupt.
