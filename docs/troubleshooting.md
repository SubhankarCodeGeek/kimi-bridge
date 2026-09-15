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

## Background Service (Linux systemd)

On Linux hosts, KimiBridge runs as a `systemd --user` service named `kimibridge`.

To view recent logs:

```bash
python3 -m kimibridge.cli logs
```

Or query systemd directly:

```bash
systemctl --user status kimibridge
journalctl --user -u kimibridge -n 50 --no-pager
```

To restart the background service:

```bash
python3 -m kimibridge.cli restart
```

