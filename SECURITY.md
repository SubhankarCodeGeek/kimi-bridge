# Security Policy

KimiBridge is designed to run locally and bind only to `127.0.0.1` by default.

## Secrets

KimiBridge must not:

- log API keys
- print `Authorization` headers
- commit secrets
- send telemetry without explicit consent

## Reporting Issues

Please avoid posting API keys, logs with bearer tokens, or private request payloads in public issues.
