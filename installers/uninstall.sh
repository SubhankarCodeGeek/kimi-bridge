#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="${KIMIBRIDGE_INSTALL_DIR:-$HOME/.kimibridge/app}"

detect_os() {
  case "$(uname -s)" in
    Darwin) printf 'macos' ;;
    Linux) printf 'linux' ;;
    *) printf 'unknown' ;;
  esac
}

uninstall_macos_service() {
  local plist_path="$HOME/Library/LaunchAgents/com.kimibridge.proxy.plist"
  launchctl unload "$plist_path" >/dev/null 2>&1 || true
  rm -f "$plist_path"
}

uninstall_linux_service() {
  local service_path="$HOME/.config/systemd/user/kimibridge.service"
  if command -v systemctl >/dev/null 2>&1; then
    systemctl --user stop kimibridge >/dev/null 2>&1 || true
    systemctl --user disable kimibridge >/dev/null 2>&1 || true
    rm -f "$service_path"
    systemctl --user daemon-reload >/dev/null 2>&1 || true
  fi
}

main() {
  case "$(detect_os)" in
    macos) uninstall_macos_service ;;
    linux) uninstall_linux_service ;;
  esac

  if command -v pkill >/dev/null 2>&1; then
    pkill -f "kimibridge" >/dev/null 2>&1 || true
  fi

  rm -f "$INSTALL_DIR/bin/kimibridge"
  rm -f "$HOME/.local/bin/kimibridge"
  rm -f "$HOME/.kimibridge/bin/kimibridge"
  rm -rf "$INSTALL_DIR"

  printf '%s\n' "KimiBridge service, binaries, and app files were removed."
  printf '%s\n' "User config remains at $HOME/.kimibridge/config.json"
}

main "$@"
