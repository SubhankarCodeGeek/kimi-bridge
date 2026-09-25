# Changelog

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
