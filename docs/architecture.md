# Architecture

```text
OpenAI-compatible client
          |
          v
   KimiBridge HTTP server
          |
          v
 Compatibility pipeline
          |
          v
   Kimi/Moonshot upstream
```

The proxy core is platform-neutral. Installers and service managers are platform-specific wrappers around the same local gateway.

## Compatibility Pipeline

```text
OpenAI-style request
          |
          v
Role adapter
          |
          v
Parameter adapter
          |
          v
Kimi upstream request
```

The default mode is `compatible`, which applies known safe normalizations. `strict` keeps unsupported parameters visible while still rejecting unknown compatibility modes. `passthrough` leaves request shape as close to the client payload as possible.
