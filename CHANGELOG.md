# Changelog

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
