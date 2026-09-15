#!/usr/bin/env bash
set -euo pipefail

APP_NAME="kimibridge"
SERVICE_NAME="kimibridge"
INSTALL_DIR="${KIMIBRIDGE_INSTALL_DIR:-$HOME/.kimibridge/app}"
CONFIG_DIR="$HOME/.kimibridge"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

log() {
  printf '%s\n' "$1"
}

fail() {
  printf 'Error: %s\n' "$1" >&2
  exit 1
}

detect_os() {
  case "$(uname -s)" in
    Darwin) printf 'macos' ;;
    Linux) printf 'linux' ;;
    *) fail "Unsupported operating system: $(uname -s)" ;;
  esac
}

detect_arch() {
  case "$(uname -m)" in
    x86_64|amd64) printf 'x86_64' ;;
    arm64|aarch64) printf 'arm64' ;;
    *) printf '%s' "$(uname -m)" ;;
  esac
}

detect_python() {
  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return
  fi
  return 1
}

install_source() {
  mkdir -p "$INSTALL_DIR" "$CONFIG_DIR"
  tar \
    -C "$REPO_ROOT" \
    --exclude '.git' \
    --exclude '.codex' \
    --exclude '.agents' \
    --exclude '__pycache__' \
    --exclude '.venv' \
    -cf - . | tar -C "$INSTALL_DIR" -xf -
}

install_binary() {
  local binary_path="$1"
  mkdir -p "$INSTALL_DIR/bin" "$CONFIG_DIR"
  cp "$binary_path" "$INSTALL_DIR/bin/kimibridge"
  chmod +x "$INSTALL_DIR/bin/kimibridge"
}

configure_port() {
  local exec_cmd="$1"
  eval "$exec_cmd start --auto-port --save-port --dry-run"
}

install_macos_service() {
  local exec_cmd="$1"
  local plist_dir="$HOME/Library/LaunchAgents"
  local plist_path="$plist_dir/com.kimibridge.proxy.plist"

  mkdir -p "$plist_dir"
  awk -v cmd="$exec_cmd" -v dir="$INSTALL_DIR" '
    /__PROGRAM_ARGUMENTS__/ {
      n = split(cmd " start --auto-port", a, " ")
      for (i = 1; i <= n; i++) {
        print "    <string>" a[i] "</string>"
      }
      next
    }
    { gsub(/__INSTALL_DIR__/, dir); print }
  ' "$INSTALL_DIR/services/macos/com.kimibridge.proxy.plist" > "$plist_path"

  launchctl unload "$plist_path" >/dev/null 2>&1 || true
  launchctl load "$plist_path"
  launchctl start com.kimibridge.proxy >/dev/null 2>&1 || true
}

install_linux_service() {
  local exec_cmd="$1"
  local service_dir="$HOME/.config/systemd/user"
  local service_path="$service_dir/kimibridge.service"

  command -v systemctl >/dev/null 2>&1 || fail "systemd user services are required for automatic startup."

  mkdir -p "$service_dir"
  sed \
    -e "s#__EXEC_CMD__#$exec_cmd#g" \
    -e "s#__PYTHON_BIN__#$exec_cmd#g" \
    -e "s#__INSTALL_DIR__#$INSTALL_DIR#g" \
    "$INSTALL_DIR/services/linux/kimibridge.service" > "$service_path"

  systemctl --user daemon-reload
  systemctl --user enable "$SERVICE_NAME"
  systemctl --user restart "$SERVICE_NAME"
}

main() {
  local os
  local arch
  local python_bin=""
  local exec_cmd=""
  local binary_candidate

  os="$(detect_os)"
  arch="$(detect_arch)"
  binary_candidate="$REPO_ROOT/dist/kimibridge-${os}-${arch}"

  log "KimiBridge Installer"
  log "OS: $os ($arch)"
  log "Install directory: $INSTALL_DIR"

  install_source

  if [ -f "$binary_candidate" ]; then
    log "Found standalone binary artifact: $binary_candidate"
    install_binary "$binary_candidate"
    exec_cmd="$INSTALL_DIR/bin/kimibridge"
  else
    log "Standalone binary not found at $binary_candidate. Falling back to Python runtime."
    python_bin="$(detect_python || fail 'python3 is required on host when standalone binary is not built. Install python3 (e.g., sudo apt install python3) or build a standalone binary via python3 scripts/build_binary.py.')"
    exec_cmd="$python_bin -m kimibridge.cli"
  fi

  cd "$INSTALL_DIR"
  configure_port "$exec_cmd"

  case "$os" in
    macos) install_macos_service "$exec_cmd" ;;
    linux) install_linux_service "$exec_cmd" ;;
  esac

  log ""
  log "KimiBridge is installed."
  eval "$exec_cmd config show"
  log ""
  log "Use the endpoint above in Android Studio as an OpenAI-compatible provider."
  log "Run diagnostics with:"
  log "  $exec_cmd doctor"
}

main "$@"
