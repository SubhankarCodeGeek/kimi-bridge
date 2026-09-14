# Troubleshooting

## Port Already In Use

KimiBridge defaults to:

```text
127.0.0.1:5001
```

To let KimiBridge choose another available port:

```bash
python3 -m kimibridge.cli start --auto-port
```

Use the printed endpoint in Android Studio.

To set a port manually:

```bash
python3 -m kimibridge.cli config set port 5002
python3 -m kimibridge.cli start
```

To inspect the current endpoint:

```bash
python3 -m kimibridge.cli config show
```

To check whether the proxy is running:

```bash
python3 -m kimibridge.cli status
```
