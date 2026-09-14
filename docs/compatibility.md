# Client Compatibility Matrix

KimiBridge provides a standard OpenAI-compatible API layer (`127.0.0.1:5001/v1`) designed to seamlessly connect developer tools to Kimi/Moonshot models (`api.moonshot.ai`).

## Tested Clients

| Client / Tool | Compatibility Mode | Status | Notes |
|---------------|-------------------|--------|-------|
| **Android Studio AI Assistant** | `compatible` (default) | ✅ Fully Supported | Auto-normalizes `developer` role to `system` and purges unsupported `parallel_tool_calls` parameters. |
| **Cursor / VS Code Extensions** | `compatible` | ✅ Fully Supported | Real-time SSE streaming (`stream: true`) and standard completions supported. |
| **Aider CLI** | `compatible` / `strict` | ✅ Fully Supported | Custom base URL `http://127.0.0.1:5001/v1` supported. |
| **Open WebUI** | `compatible` | ✅ Fully Supported | Full CORS preflight support enabled. |
| **cURL / Custom HTTP** | `passthrough` | ✅ Fully Supported | Pass raw OpenAI payloads directly. |

---

## Compatibility Modes

Set the active mode via CLI:

```bash
python3 -m kimibridge.cli config set compatibility-mode <mode>
```

- **`compatible`** *(default)*: Normalizes unsupported roles (`developer` ➔ `system`) and purges incompatible parameters (`store`, `parallel_tool_calls`, `metadata`).
- **`strict`**: Leaves parameters unchanged while rejecting unrecognized compatibility options.
- **`passthrough`**: Forwards raw HTTP requests directly to Kimi upstream without modifications.
