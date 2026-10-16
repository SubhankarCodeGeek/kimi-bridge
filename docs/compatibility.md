# Compatibility Matrix

StudioRelay provides a standard OpenAI-compatible API gateway (`127.0.0.1:5001/v1` for DeepSeek, `127.0.0.1:5002/v1` for Kimi) that translates rich agentic client protocols into provider-specific schemas.

---

## Provider Capability Matrix

| Feature / Schema Element | OpenAI Direct | Kimi / Moonshot | DeepSeek (Chat Completions) | StudioRelay Normalized |
|--------------------------|---------------|-----------------|-----------------------------|-----------------------|
| **`developer` role** | ✅ Supported | ❌ 422 / Reject | ❌ 422 (`unknown variant developer`) | 🔄 Normalized to `system` |
| **`parallel_tool_calls`** | ✅ Supported | ❌ Unrecognized | ⚠️ Parameter Ignored / Varies | 🧹 Stripped in `compatible` mode |
| **`store` & `metadata`** | ✅ Supported | ❌ Unrecognized | ❌ Unrecognized | 🧹 Stripped in `compatible` mode |
| **SSE Streaming** | ✅ Supported | ✅ Supported | ✅ Supported | ⚡ Zero-latency line-by-line forwarding |
| **Model Listing (`/v1/models`)** | ✅ Standard | ⚠️ Moonshot ID list | ⚠️ DeepSeek ID list | 📋 Standard OpenAI model objects |
| **Responses API (`/v1/responses`)** | ✅ Supported | ❌ Chat endpoint only | ❌ Chat endpoint only | 🔁 Translated to/from Chat Completions |

---

## Tested Clients

| Client / Tool | Compatibility Mode | Status | Notes |
|---------------|-------------------|--------|-------|
| **Android Studio AI Assistant** | `compatible` (default) | ✅ Fully Supported | Supports `/v1/responses`, auto-normalizes `developer` role to `system`, and purges unsupported parameters (`parallel_tool_calls`, `store`). |
| **Cursor / VS Code Extensions** | `compatible` | ✅ Fully Supported | Real-time SSE streaming (`stream: true`) and standard completions supported. |
| **Aider CLI** | `compatible` / `strict` | ✅ Fully Supported | Custom base URL `http://127.0.0.1:5001/v1` supported. |
| **Open WebUI** | `compatible` | ✅ Fully Supported | Full CORS preflight support enabled. |
| **cURL / Custom HTTP** | `passthrough` | ✅ Fully Supported | Pass raw OpenAI payloads directly. |

---

## Configuring Providers

You can configure StudioRelay to target different providers or let it auto-detect based on the model or upstream URL:

```bash
# Configure for DeepSeek
studiorelay config set provider deepseek
studiorelay config set base-url https://api.deepseek.com

# Configure for Kimi / Moonshot
studiorelay config set provider kimi
studiorelay config set base-url https://api.moonshot.ai

# Set compatibility mode
studiorelay config set compatibility-mode compatible
```

### Compatibility Modes

- **`compatible`** *(default)*: Uses provider profiles to map unsupported message roles (e.g. `developer` ➔ `system`) and strip incompatible parameters.
- **`strict`**: Leaves parameters unchanged while normalizing roles required to prevent upstream deserialization errors.
- **`passthrough`**: Forwards raw HTTP requests directly to the upstream without modifications.
