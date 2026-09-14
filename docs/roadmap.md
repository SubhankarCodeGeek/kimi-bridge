# Roadmap

## Phase 0: Baseline Audit

- Document the prototype behavior.
- Identify platform, packaging, testing, and support gaps.

## Phase 1: Repository Foundation

- Add README, security policy, contribution guide, changelog, docs, and package metadata.
- Establish the project identity as KimiBridge.

## Phase 2: Platform-Neutral Proxy Core

- Add `GET /health`.
- Add `GET /v1/models`.
- Add `POST /v1/chat/completions` (with real-time SSE streaming and CORS preflight support).
- Add config loading.
- Keep the server bound to `127.0.0.1`.

Status: complete.

## Phase 3: Graceful Port Management

- Default to `127.0.0.1:5001`.
- Detect whether the configured port is available.
- If the port is already serving KimiBridge, report that the service is already running.
- If another process owns the port, either fail clearly or choose a fallback port when `--auto-port` is enabled.
- Persist installer-selected ports in config.
- Always print the final endpoint users should paste into Android Studio.

Status: complete.

## Phase 4: Compatibility Pipeline

- Normalize `developer` messages to `system`.
- Normalize model listing.
- Add compatibility modes: `strict`, `compatible`, and `passthrough`.
- Add fixtures for known client incompatibilities.

Status: complete.

## Phase 5: Tests

- Add unit tests for adapters.
- Add integration tests with a mocked upstream.
- Add streaming and error translation tests.

Status: complete.

## Phase 6: Installers And Services

- macOS: launchd.
- Linux: systemd user service.
- Windows: Task Scheduler.
- Keep the service independent from Android Studio process detection.

Status: complete.

## Phase 7: CLI And Doctor

- Add `start`, `stop`, `restart`, `status`, `logs`, `config`, `doctor`, and `uninstall`.
- Make `doctor` the primary support command.

Status: complete.

## Phase 8: Native Binaries

- Build standalone artifacts for macOS, Linux, and Windows.
- Update installers to download the correct artifact.
- Generate checksums.

Status: complete.

## Phase 9: CI And Releases

- Add GitHub Actions test matrix.
- Add release automation for version tags.

Status: complete.

## Phase 10: Community

- Add issue templates.
- Add compatibility matrix.
- Maintain release notes and troubleshooting docs.

Status: complete.
