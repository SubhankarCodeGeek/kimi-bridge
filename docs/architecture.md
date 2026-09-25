# Architecture

```text
                  OpenAI-Compatible Client
             (Android Studio, Cursor, Aider, etc.)
                             │
                             ▼
                    ┌──────────────────┐
                    │    KimiBridge    │
                    │   HTTP Gateway   │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  Compatibility   │
                    │      Engine      │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
         Kimi Profile   DeepSeek Prof.  OpenAI Prof.
              │              │              │
              ▼              ▼              ▼
       api.moonshot.ai api.deepseek.com api.openai.com
```

The gateway is platform-neutral and runs locally (default: `127.0.0.1:5001/v1`). Native service managers (`systemd` on Linux, `launchd` on macOS, and `Task Scheduler` on Windows) run the server as a background daemon.

---

## Provider-Aware Compatibility Pipeline

Agentic clients (like Android Studio AI Assistant) emit OpenAI-style schemas that utilize newer features—such as the `developer` message role, `store`, `metadata`, or `parallel_tool_calls` parameters. Many upstream providers advertise "OpenAI-compatible" endpoints, but strictly reject schema extensions with HTTP 422 or deserialization errors.

KimiBridge implements a provider-aware normalization pipeline:

```text
Request (OpenAI Schema)
          │
          ▼
Parse & Inspect Payload
          │
          ▼
Detect Provider Profile
(by header, config, model prefix, or upstream URL)
          │
          ▼
Role Adapter (e.g. developer ➔ system for Kimi & DeepSeek; preserve for OpenAI)
          │
          ▼
Parameter Adapter (strip unsupported keys like parallel_tool_calls, store, metadata)
          │
          ▼
Forward to Upstream Provider
          │
          ▼
Stream or Return Normalized Response
```

---

## Compatibility Modes

- **`compatible`** *(default)*: Detects the target provider profile, maps unsupported roles (e.g. `developer` ➔ `system` for Kimi and DeepSeek), and strips unsupported parameters.
- **`strict`**: Applies role normalizations required to avoid upstream deserialization failures while leaving parameters unmodified.
- **`passthrough`**: Forwards raw HTTP requests directly to the upstream without modifying roles or parameters.
