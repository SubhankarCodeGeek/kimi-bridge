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
    --exclude 'dist' \
    -cf - . | tar -C "$INSTALL_DIR" -xf -
  chmod +x "$INSTALL_DIR"/installers/*.sh 2>/dev/null || true
  chmod +x "$INSTALL_DIR"/scripts/*.sh 2>/dev/null || true
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

cleanup_previous_install() {
  local os="$1"
  local binary_mode="${2:-false}"
  log "Cleaning up any existing installation and background services..."
  case "$os" in
    macos)
      local plist_path="$HOME/Library/LaunchAgents/com.kimibridge.proxy.plist"
      launchctl unload "$plist_path" >/dev/null 2>&1 || true
      rm -f "$plist_path"
      ;;
    linux)
      local service_path="$HOME/.config/systemd/user/kimibridge.service"
      if command -v systemctl >/dev/null 2>&1; then
        systemctl --user stop kimibridge >/dev/null 2>&1 || true
        systemctl --user disable kimibridge >/dev/null 2>&1 || true
        rm -f "$service_path"
        systemctl --user daemon-reload >/dev/null 2>&1 || true
      fi
      ;;
  esac

  # Terminate any running kimibridge processes to ensure ports and binary files are released
  if command -v pkill >/dev/null 2>&1; then
    pkill -f "kimibridge" >/dev/null 2>&1 || true
  fi

  # Explicitly remove any existing binary files
  log "Checking for existing binaries to remove..."
  local binary_candidates=(
    "$INSTALL_DIR/bin/kimibridge"
    "$INSTALL_DIR/bin/kimibridge.exe"
    "$CONFIG_DIR/bin/kimibridge"
    "$CONFIG_DIR/bin/kimibridge.exe"
    "$HOME/.local/bin/kimibridge"
    "$HOME/.local/bin/kimibridge.exe"
  )
  for bin_loc in "${binary_candidates[@]}"; do
    if [ -f "$bin_loc" ] || [ -L "$bin_loc" ]; then
      log "Removing existing binary: $bin_loc"
      rm -f "$bin_loc"
    fi
  done
  if [ -d "$INSTALL_DIR/bin" ]; then
    rm -rf "$INSTALL_DIR/bin"
  fi

  # Remove existing build artifacts if not running in explicit binary install mode
  if [ "$binary_mode" = false ]; then
    if [ -d "$REPO_ROOT/dist" ]; then
      log "Removing existing build artifacts: $REPO_ROOT/dist"
      rm -rf "$REPO_ROOT/dist"
    fi
    if [ -d "$REPO_ROOT/build" ]; then
      rm -rf "$REPO_ROOT/build"
    fi
  fi

  if [ -d "$INSTALL_DIR" ]; then
    log "Removing previous installation directory: $INSTALL_DIR"
    rm -rf "$INSTALL_DIR"
  fi
}

main() {
  local os
  local arch
  local python_bin=""
  local exec_cmd=""
  local binary_candidate
  local provider="${KIMIBRIDGE_PROVIDER:-}"
  local base_url="${KIMIBRIDGE_BASE_URL:-}"
  local use_binary_mode=false

  while [ $# -gt 0 ]; do
    case "$1" in
      --deepseek)
        provider="deepseek"
        shift
        ;;
      --kimi)
        provider="kimi"
        shift
        ;;
      --all)
        provider="all"
        shift
        ;;
      --provider)
        provider="$2"
        shift 2
        ;;
      --base-url)
        base_url="$2"
        shift 2
        ;;
      --binary)
        use_binary_mode=true
        shift
        ;;
      *)
        shift
        ;;
    esac
  done

  if [ -z "$provider" ]; then
    if [ -t 0 ] && [ -t 1 ]; then
      log ""
      log "Select your target AI provider for Android Studio / LLM clients:"
      log "  1) DeepSeek (https://api.deepseek.com) [Recommended]"
      log "  2) Kimi / Moonshot AI (https://api.moonshot.ai)"
      log "  3) All Providers (exposes both DeepSeek and Kimi models)"
      read -r -p "Enter choice [1-3, default: 1]: " user_choice || user_choice=""
      case "${user_choice:-1}" in
        1|deepseek|DeepSeek)
          provider="deepseek"
          ;;
        2|kimi|Kimi|moonshot|Moonshot)
          provider="kimi"
          ;;
        3|all|All)
          provider="all"
          ;;
        *)
          provider="deepseek"
          ;;
      esac
    else
      if [ ! -f "$CONFIG_DIR/config.json" ]; then
        provider="deepseek"
      fi
    fi
  fi

  os="$(detect_os)"
  arch="$(detect_arch)"
  binary_candidate="$REPO_ROOT/dist/kimibridge-${os}-${arch}"

  log "KimiBridge Installer"
  log "OS: $os ($arch)"
  log "Install directory: $INSTALL_DIR"

  cleanup_previous_install "$os" "$use_binary_mode"

  install_source

  if [ "$use_binary_mode" = true ] && [ -f "$binary_candidate" ]; then
    log "Found standalone binary artifact: $binary_candidate"
    install_binary "$binary_candidate"
    exec_cmd="$INSTALL_DIR/bin/kimibridge"
  else
    if [ "$use_binary_mode" = true ]; then
      log "Standalone binary not found at $binary_candidate. Falling back to Python runtime."
    fi
    python_bin="$(detect_python || fail 'python3 is required on host when standalone binary is not built. Install python3 (e.g., sudo apt install python3) or build a standalone binary via python3 scripts/build_binary.py.')"
    exec_cmd="$python_bin -m kimibridge.cli"
  fi

  cd "$INSTALL_DIR"
  configure_port "$exec_cmd"

  case "$os" in
    macos) install_macos_service "$exec_cmd" ;;
    linux) install_linux_service "$exec_cmd" ;;
  esac

  if [ -n "$provider" ]; then
    log ""
    log "Configuring provider: $provider"
    if [ -n "$base_url" ]; then
      eval "$exec_cmd setup \"$provider\" --base-url \"$base_url\""
    else
      eval "$exec_cmd setup \"$provider\""
    fi
  else
    log ""
    eval "$exec_cmd config show"
  fi

  log ""
  log "============================================================"
  log "  KimiBridge is ready for Android Studio!"
  log "============================================================"
  log "  Base URL:  http://127.0.0.1:5001/v1"
  log "  Action:    In Android Studio, enter your API key and"
  log "             click Refresh to populate the model dropdown."
  log "============================================================"
}

main "$@"
