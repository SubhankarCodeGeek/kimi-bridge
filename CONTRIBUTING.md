# Contributing

Thanks for helping improve KimiBridge.

## Development

```bash
python3 -m kimibridge.cli start
python3 -m unittest
```

Keep compatibility changes fixture-driven where possible:

```text
OpenAI-style request
-> compatibility pipeline
-> expected Kimi request
```
