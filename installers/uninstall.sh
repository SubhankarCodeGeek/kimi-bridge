#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="${STUDIORELAY_INSTALL_DIR:-${KIMIBRIDGE_INSTALL_DIR:-$HOME/.studiorelay/app}}"
LEGACY_INSTALL_DIR="$HOME/.kimibridge/app"
CONFIG_DIR="$HOME/.studiorelay"
LEGACY_CONFIG_DIR="$HOME/.kimibridge"

detect_os() {
  case "$(uname -s)" in
    Darwin) printf 'macos' ;;
    Linux) printf 'linux' ;;
    *) printf 'unknown' ;;
  esac
}

normalize_provider() {
  local p
  p=$(printf '%s' "${1:-}" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]')
  if [ "$p" = "moonshot" ]; then
    printf 'kimi'
  else
    printf '%s' "$p"
  fi
}

uninstall_macos_service() {
  local provider="$1"
  local plist_dir="$HOME/Library/LaunchAgents"

  if [ -n "$provider" ]; then
    local candidates=(
      "$plist_dir/com.studiorelay.proxy.${provider}.plist"
      "$plist_dir/com.studiorelay.${provider}.plist"
      "$plist_dir/com.kimibridge.proxy.${provider}.plist"
      "$plist_dir/com.kimibridge.${provider}.plist"
    )
    for p in "${candidates[@]}"; do
      if [ -f "$p" ]; then
        launchctl unload "$p" >/dev/null 2>&1 || true
        rm -f "$p"
      fi
    done
  else
    for p in "$plist_dir"/*studiorelay*.plist "$plist_dir"/*kimibridge*.plist; do
      if [ -f "$p" ]; then
        launchctl unload "$p" >/dev/null 2>&1 || true
        rm -f "$p"
      fi
    done
  fi
}

uninstall_linux_service() {
  local provider="$1"
  local service_dir="$HOME/.config/systemd/user"

  if ! command -v systemctl >/dev/null 2>&1; then
    return
  fi

  if [ -n "$provider" ]; then
    local targets=(
      "studiorelay-${provider}"
      "kimibridge-${provider}"
    )
    for sname in "${targets[@]}"; do
      systemctl --user stop "$sname" >/dev/null 2>&1 || true
      systemctl --user disable "$sname" >/dev/null 2>&1 || true
      rm -f "$service_dir/${sname}.service"
    done

    # Check un-prefixed services
    for base in "studiorelay" "kimibridge"; do
      if [ -f "$service_dir/${base}.service" ]; then
        for cdir in "$CONFIG_DIR" "$LEGACY_CONFIG_DIR"; do
          if [ -f "$cdir/config.json" ]; then
            local prov
            prov=$(grep -o '"provider": *"[^"]*"' "$cdir/config.json" 2>/dev/null | cut -d'"' -f4 || true)
            if [ "$prov" = "$provider" ]; then
              systemctl --user stop "$base" >/dev/null 2>&1 || true
              systemctl --user disable "$base" >/dev/null 2>&1 || true
              rm -f "$service_dir/${base}.service"
            fi
          fi
        done
      fi
    done
  else
    # Remove all studiorelay and kimibridge user services
    for sfile in "$service_dir"/studiorelay*.service "$service_dir"/kimibridge*.service; do
      if [ -f "$sfile" ]; then
        local base
        base=$(basename "$sfile" .service)
        systemctl --user stop "$base" >/dev/null 2>&1 || true
        systemctl --user disable "$base" >/dev/null 2>&1 || true
        rm -f "$sfile"
      fi
    done
  fi
  systemctl --user daemon-reload >/dev/null 2>&1 || true
}

has_other_providers() {
  local target_provider="$1"
  for cdir in "$CONFIG_DIR" "$LEGACY_CONFIG_DIR"; do
    if [ -d "$cdir" ]; then
      for cfg in "$cdir"/config-*.json; do
        if [ -f "$cfg" ]; then
          local p
          p=$(basename "$cfg" .json)
          p="${p#config-}"
          if [ "$p" != "$target_provider" ]; then
            return 0
          fi
        fi
      done
    fi
  done

  # Check if other systemd services exist
  local sdir="$HOME/.config/systemd/user"
  if [ -d "$sdir" ]; then
    for sfile in "$sdir"/studiorelay-*.service "$sdir"/kimibridge-*.service; do
      if [ -f "$sfile" ]; then
        local sname
        sname=$(basename "$sfile" .service)
        sname="${sname#studiorelay-}"
        sname="${sname#kimibridge-}"
        if [ "$sname" != "$target_provider" ]; then
          return 0
        fi
      fi
    done
  fi

  return 1
}

main() {
  local provider=""
  local uninstall_all=false

  while [ $# -gt 0 ]; do
    case "$1" in
      --kimi)
        provider="kimi"
        shift
        ;;
      --deepseek)
        provider="deepseek"
        shift
        ;;
      --provider|-p)
        provider="${2:-}"
        shift 2
        ;;
      --all)
        uninstall_all=true
        shift
        ;;
      --help|-h)
        printf '%s\n' "Usage: uninstall.sh [--provider <kimi|deepseek|...>] [--all]"
        exit 0
        ;;
      *)
        shift
        ;;
    esac
  done

  provider=$(normalize_provider "$provider")

  local os
  os="$(detect_os)"

  if [ -n "$provider" ] && [ "$uninstall_all" = false ]; then
    case "$os" in
      macos) uninstall_macos_service "$provider" ;;
      linux) uninstall_linux_service "$provider" ;;
    esac

    if has_other_providers "$provider"; then
      printf '%s\n' "StudioRelay ($provider) background service was stopped and removed."
      printf '%s\n' "Other configured providers remain active. Shared binaries at $INSTALL_DIR were preserved."
      printf '%s\n' "Configuration remains at $CONFIG_DIR/config-$provider.json"
      return 0
    fi
  else
    case "$os" in
      macos) uninstall_macos_service "" ;;
      linux) uninstall_linux_service "" ;;
    esac

    if command -v pkill >/dev/null 2>&1; then
      pkill -f "studiorelay" >/dev/null 2>&1 || true
      pkill -f "kimibridge" >/dev/null 2>&1 || true
    fi
  fi

  # Remove binaries and app directories
  rm -f "$INSTALL_DIR/bin/studiorelay"
  rm -f "$INSTALL_DIR/bin/kimibridge"
  rm -f "$HOME/.local/bin/studiorelay"
  rm -f "$HOME/.local/bin/kimibridge"
  rm -f "$LEGACY_INSTALL_DIR/bin/kimibridge"
  rm -rf "$INSTALL_DIR"

  if [ "$uninstall_all" = true ] && [ -d "$LEGACY_INSTALL_DIR" ]; then
    rm -rf "$LEGACY_INSTALL_DIR"
  fi

  if [ -n "$provider" ]; then
    printf '%s\n' "StudioRelay ($provider) service, binaries, and app files were removed."
    printf '%s\n' "User config remains preserved at $CONFIG_DIR/config-$provider.json"
  else
    printf '%s\n' "All StudioRelay services, binaries, and app files were removed."
    printf '%s\n' "User configs remain safely preserved in $CONFIG_DIR"
  fi
}

main "$@"
