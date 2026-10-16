#!/usr/bin/env bash
set -euo pipefail

APP_NAME="studiorelay"
SERVICE_NAME="studiorelay"
INSTALL_DIR="${STUDIORELAY_INSTALL_DIR:-${KIMIBRIDGE_INSTALL_DIR:-$HOME/.studiorelay/app}}"
CONFIG_DIR="$HOME/.studiorelay"
LEGACY_CONFIG_DIR="$HOME/.kimibridge"
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

  # If legacy configuration directory exists, migrate configurations safely
  if [ -d "$LEGACY_CONFIG_DIR" ] && [ -n "$(ls -A "$LEGACY_CONFIG_DIR"/*.json 2>/dev/null || true)" ]; then
    log "Existing KimiBridge configuration found at $LEGACY_CONFIG_DIR."
    log "Migrating configuration to StudioRelay..."
    local py
    py="$(detect_python || true)"
    if [ -n "$py" ]; then
      "$py" -c "
import sys
sys.path.insert(0, '$REPO_ROOT')
from studiorelay.config import migrate_legacy_configuration
res = migrate_legacy_configuration()
if res.get('copied'):
    print(f'Migrated: {\", \".join(res[\"copied\"])}')
" 2>/dev/null || true
    fi
  fi
}

install_binary() {
  local binary_path="$1"
  mkdir -p "$INSTALL_DIR/bin" "$CONFIG_DIR"
  cp "$binary_path" "$INSTALL_DIR/bin/studiorelay"
  chmod +x "$INSTALL_DIR/bin/studiorelay"
  ln -sf "$INSTALL_DIR/bin/studiorelay" "$INSTALL_DIR/bin/kimibridge"
}

MACOS_LABEL="com.studiorelay.proxy"

configure_port() {
  local exec_cmd="$1"
  local provider_arg="$2"
  local port_arg="${3:-}"
  local cmd="$exec_cmd start --auto-port --save-port --dry-run"
  if [ -n "$provider_arg" ]; then
    cmd="$cmd --provider $provider_arg"
  fi
  if [ -n "$port_arg" ]; then
    cmd="$cmd --port $port_arg"
  fi
  eval "$cmd"
}

install_macos_service() {
  local exec_cmd="$1"
  local provider_arg="$2"
  local plist_dir="$HOME/Library/LaunchAgents"
  local plist_path="$plist_dir/${MACOS_LABEL}.plist"
  local log_out="$INSTALL_DIR/${SERVICE_NAME}.log"
  local log_err="$INSTALL_DIR/${SERVICE_NAME}.err.log"

  local extra_arg=""
  if [ -n "$provider_arg" ] && [ "$provider_arg" != "all" ]; then
    extra_arg="--provider $provider_arg"
  fi

  local template="$INSTALL_DIR/services/macos/com.studiorelay.proxy.plist"
  if [ ! -f "$template" ]; then
    template="$INSTALL_DIR/services/macos/com.kimibridge.proxy.plist"
  fi

  mkdir -p "$plist_dir"
  awk -v cmd="$exec_cmd" -v dir="$INSTALL_DIR" -v extra="$extra_arg" -v label="$MACOS_LABEL" -v out="$log_out" -v err="$log_err" '
    /__PROGRAM_ARGUMENTS__/ {
      full_cmd = cmd " start " extra " --auto-port"
      n = split(full_cmd, a, " ")
      for (i = 1; i <= n; i++) {
        if (a[i] != "") {
          print "    <string>" a[i] "</string>"
        }
      }
      next
    }
    {
      gsub(/__INSTALL_DIR__/, dir);
      gsub(/__SERVICE_LABEL__/, label);
      gsub(/__LOG_PATH__/, out);
      gsub(/__ERR_LOG_PATH__/, err);
      print;
    }
  ' "$template" > "$plist_path"

  launchctl unload "$plist_path" >/dev/null 2>&1 || true
  launchctl load "$plist_path"
  launchctl start "$MACOS_LABEL" >/dev/null 2>&1 || true
}

install_linux_service() {
  local exec_cmd="$1"
  local provider_arg="$2"
  local service_dir="$HOME/.config/systemd/user"
  local service_path="$service_dir/${SERVICE_NAME}.service"

  command -v systemctl >/dev/null 2>&1 || fail "systemd user services are required for automatic startup."

  local provider_flag=""
  if [ -n "$provider_arg" ] && [ "$provider_arg" != "all" ]; then
    provider_flag="--provider $provider_arg"
  fi

  local template="$INSTALL_DIR/services/linux/studiorelay.service"
  if [ ! -f "$template" ]; then
    template="$INSTALL_DIR/services/linux/kimibridge.service"
  fi

  mkdir -p "$service_dir"
  sed \
    -e "s#__EXEC_CMD__#$exec_cmd#g" \
    -e "s#__PYTHON_BIN__#$exec_cmd#g" \
    -e "s#__INSTALL_DIR__#$INSTALL_DIR#g" \
    -e "s#__PROVIDER_FLAG__#$provider_flag#g" \
    "$template" > "$service_path"

  systemctl --user daemon-reload
  systemctl --user enable "$SERVICE_NAME"
  systemctl --user restart "$SERVICE_NAME"
}

cleanup_previous_install() {
  local os="$1"
  local service="$2"
  local provider_arg="$3"
  local binary_mode="${4:-false}"
  log "Checking for existing background service: $service..."
  case "$os" in
    macos)
      local plist_path="$HOME/Library/LaunchAgents/${MACOS_LABEL}.plist"
      launchctl unload "$plist_path" >/dev/null 2>&1 || true
      rm -f "$plist_path"

      # Also unload legacy plist if migrating
      if [ -n "$provider_arg" ] && [ "$provider_arg" != "all" ]; then
        local leg_plist="$HOME/Library/LaunchAgents/com.kimibridge.proxy.${provider_arg}.plist"
        launchctl unload "$leg_plist" >/dev/null 2>&1 || true
        rm -f "$leg_plist"
      fi
      local leg_def="$HOME/Library/LaunchAgents/com.kimibridge.proxy.plist"
      launchctl unload "$leg_def" >/dev/null 2>&1 || true
      rm -f "$leg_def"
      ;;
    linux)
      local service_path="$HOME/.config/systemd/user/${service}.service"
      if command -v systemctl >/dev/null 2>&1; then
        systemctl --user stop "$service" >/dev/null 2>&1 || true
        systemctl --user disable "$service" >/dev/null 2>&1 || true
        rm -f "$service_path"
        systemctl --user daemon-reload >/dev/null 2>&1 || true
      fi

      # Check for and disable matching legacy kimibridge services to prevent port conflict
      local legacy_candidates=()
      if [ -n "$provider_arg" ] && [ "$provider_arg" != "all" ]; then
        legacy_candidates=("kimibridge-${provider_arg}" "kimibridge")
      else
        legacy_candidates=("kimibridge")
      fi
      for leg_s in "${legacy_candidates[@]}"; do
        local leg_path="$HOME/.config/systemd/user/${leg_s}.service"
        if [ -f "$leg_path" ]; then
          log "Found legacy service '$leg_s'. Migrating to '$service'..."
          systemctl --user stop "$leg_s" >/dev/null 2>&1 || true
          systemctl --user disable "$leg_s" >/dev/null 2>&1 || true
          rm -f "$leg_path"
          systemctl --user daemon-reload >/dev/null 2>&1 || true
        fi
      done
      ;;
  esac

  # Explicitly remove old binary files to avoid stale paths
  log "Checking for existing binaries..."
  local binary_candidates=(
    "$INSTALL_DIR/bin/studiorelay"
    "$INSTALL_DIR/bin/studiorelay.exe"
    "$INSTALL_DIR/bin/kimibridge"
    "$INSTALL_DIR/bin/kimibridge.exe"
    "$HOME/.local/bin/studiorelay"
    "$HOME/.local/bin/kimibridge"
  )
  for bin_loc in "${binary_candidates[@]}"; do
    if [ -f "$bin_loc" ] || [ -L "$bin_loc" ]; then
      rm -f "$bin_loc"
    fi
  done
  if [ -d "$INSTALL_DIR/bin" ]; then
    rm -rf "$INSTALL_DIR/bin"
  fi

  # Remove existing build artifacts if not running in explicit binary install mode
  if [ "$binary_mode" = false ]; then
    if [ -d "$REPO_ROOT/dist" ]; then
      rm -rf "$REPO_ROOT/dist"
    fi
    if [ -d "$REPO_ROOT/build" ]; then
      rm -rf "$REPO_ROOT/build"
    fi
  fi
}

main() {
  local os
  local arch
  local python_bin=""
  local exec_cmd=""
  local binary_candidate
  local provider="${STUDIORELAY_PROVIDER:-${KIMIBRIDGE_PROVIDER:-}}"
  local base_url="${STUDIORELAY_BASE_URL:-${KIMIBRIDGE_BASE_URL:-}}"
  local requested_port=""
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
      --port)
        requested_port="$2"
        shift 2
        ;;
      --port=*)
        requested_port="${1#*=}"
        shift
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
      if [ ! -f "$CONFIG_DIR/config.json" ] && [ ! -f "$LEGACY_CONFIG_DIR/config.json" ]; then
        provider="deepseek"
      fi
    fi
  fi

  provider=$(echo "$provider" | tr '[:upper:]' '[:lower:]')
  if [ "$provider" = "moonshot" ]; then
    provider="kimi"
  fi

  if [ -n "$provider" ] && [ "$provider" != "all" ]; then
    SERVICE_NAME="studiorelay-$provider"
    MACOS_LABEL="com.studiorelay.proxy.$provider"
  else
    SERVICE_NAME="studiorelay"
    MACOS_LABEL="com.studiorelay.proxy"
  fi

  os="$(detect_os)"
  arch="$(detect_arch)"
  binary_candidate="$REPO_ROOT/dist/studiorelay-${os}-${arch}"
  if [ ! -f "$binary_candidate" ]; then
    binary_candidate="$REPO_ROOT/dist/kimibridge-${os}-${arch}"
  fi

  log "StudioRelay Installer"
  log "OS: $os ($arch)"
  log "Target Provider: ${provider:-default}"
  log "Service Name: $SERVICE_NAME"
  log "Install directory: $INSTALL_DIR"

  cleanup_previous_install "$os" "$SERVICE_NAME" "$provider" "$use_binary_mode"

  install_source

  if [ "$use_binary_mode" = true ] && [ -f "$binary_candidate" ]; then
    log "Found standalone binary artifact: $binary_candidate"
    mkdir -p "$INSTALL_DIR/bin" "$HOME/.local/bin"
    ln -sf "$INSTALL_DIR/bin/studiorelay" "$HOME/.local/bin/studiorelay"
    ln -sf "$INSTALL_DIR/bin/studiorelay" "$HOME/.local/bin/kimibridge"
    exec_cmd="$INSTALL_DIR/bin/studiorelay"
  else
    if [ "$use_binary_mode" = true ]; then
      log "Standalone binary not found at $binary_candidate. Falling back to Python runtime."
    fi
    python_bin="$(detect_python || fail 'python3 is required on host when standalone binary is not built. Install python3 (e.g., sudo apt install python3) or build a standalone binary via python3 scripts/build_binary.py.')"
    exec_cmd="$python_bin -m studiorelay.cli"

    mkdir -p "$HOME/.local/bin"
    cat << EOF > "$HOME/.local/bin/studiorelay"
#!/usr/bin/env bash
export PYTHONPATH="${INSTALL_DIR}\${PYTHONPATH:+:\$PYTHONPATH}"
exec "$python_bin" -m studiorelay.cli "\$@"
EOF
    chmod +x "$HOME/.local/bin/studiorelay"
    ln -sf "$HOME/.local/bin/studiorelay" "$HOME/.local/bin/kimibridge"
  fi

  # Automatically ensure ~/.local/bin is in shell config
  case "$os" in
    linux|macos)
      local path_added=false
      for rc_file in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile"; do
        if [ -f "$rc_file" ] && ! grep -q '\.local/bin' "$rc_file" 2>/dev/null; then
          printf '\n# Added by StudioRelay\nexport PATH="$HOME/.local/bin:$PATH"\n' >> "$rc_file"
          path_added=true
        fi
      done
      if [ "$path_added" = true ]; then
        log "Added ~/.local/bin to shell configuration."
      fi
      ;;
  esac

  cd "$INSTALL_DIR"

  if [ -n "$provider" ]; then
    log ""
    log "Configuring provider settings: $provider"
    local setup_args="\"$provider\""
    if [ -n "$base_url" ]; then
      setup_args="$setup_args --base-url \"$base_url\""
    fi
    if [ -n "$requested_port" ]; then
      setup_args="$setup_args --port \"$requested_port\""
    fi
    eval "$exec_cmd setup $setup_args --no-restart"
  else
    configure_port "$exec_cmd" "$provider" "$requested_port"
    log ""
    eval "$exec_cmd config show"
  fi

  case "$os" in
    macos) install_macos_service "$exec_cmd" "$provider" ;;
    linux) install_linux_service "$exec_cmd" "$provider" ;;
  esac

  local active_port
  active_port=$(python3 -c "from studiorelay.config import load_config; print(load_config(provider='$provider').server.port)" 2>/dev/null || echo "5001")

  log ""
  log "============================================================"
  log "  StudioRelay (${provider:-default}) is ready for Android Studio!"
  log "============================================================"
  log "  Provider:  ${provider:-default}"
  log "  Base URL:  http://127.0.0.1:${active_port}/v1"
  log "  Action:    In Android Studio, enter your API key and"
  log "             click Refresh to populate the model dropdown."
  log "============================================================"

  # Display all active endpoints if multiple instances exist
  python3 -c "
from studiorelay.config import list_configured_providers
from studiorelay.health import check_health
cfgs = list_configured_providers()
if len(cfgs) > 1:
    print('  Active Configured Endpoints:')
    for p, _, cfg in cfgs:
        h = check_health(cfg.server.host, cfg.server.port)
        stat = 'running' if h.ok else 'stopped'
        print(f'    • {p.capitalize():<10} http://{cfg.server.host}:{cfg.server.port}/v1 [{stat}]')
    print('============================================================')
" 2>/dev/null || true
}

main "$@"
