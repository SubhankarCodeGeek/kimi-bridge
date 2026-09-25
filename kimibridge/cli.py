from __future__ import annotations

import argparse
from dataclasses import replace
import json
import sys

from kimibridge import __version__
from kimibridge.compatibility.pipeline import VALID_MODES
from kimibridge.config import (
    CompatibilityConfig,
    KimiConfig,
    ServerConfig,
    config_to_dict,
    default_config_path,
    load_config,
    save_config,
)
from kimibridge.health import check_health
from kimibridge.ports import resolve_port
from kimibridge.service import service_action, service_logs, service_uninstall
from kimibridge.server import run_server


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="kimibridge")
    parser.add_argument("--version", action="store_true", help="Print version and exit.")
    subparsers = parser.add_subparsers(dest="command")

    start = subparsers.add_parser("start", help="Start the local proxy.")
    start.add_argument("--host", help="Host to bind. Defaults to config or 127.0.0.1.")
    start.add_argument("--port", type=int, help="Port to bind. Defaults to config or 5001.")
    start.add_argument(
        "--auto-port",
        action="store_true",
        help="Choose the next available port if the configured port is busy.",
    )
    start.add_argument(
        "--save-port",
        action="store_true",
        help="Persist the selected fallback port to the config file.",
    )
    start.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve configuration and print the endpoint without starting the server.",
    )

    subparsers.add_parser("doctor", help="Check local proxy configuration.")
    subparsers.add_parser("status", help="Check whether the local proxy is running.")
    subparsers.add_parser("stop", help="Stop the installed background service.")
    subparsers.add_parser("restart", help="Restart the installed background service.")
    subparsers.add_parser("logs", help="Show recent background service logs.")
    subparsers.add_parser("uninstall", help="Remove installed service and app files.")

    config = subparsers.add_parser("config", help="Show or update local config.")
    config_subparsers = config.add_subparsers(dest="config_command")
    config_subparsers.add_parser("show", help="Print the active config.")

    set_config = config_subparsers.add_parser("set", help="Set a config value.")
    set_config.add_argument(
        "key",
        choices=["base-url", "compatibility-mode", "fallback-base-url", "host", "port", "provider"],
    )
    set_config.add_argument("value")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(__version__)
        return 0

    if args.command == "start":
        return start(args)

    if args.command == "doctor":
        return doctor()

    if args.command == "status":
        return status()

    if args.command == "stop":
        return run_service_action("stop")

    if args.command == "restart":
        return run_service_action("restart")

    if args.command == "logs":
        return logs()

    if args.command == "uninstall":
        return uninstall()

    if args.command == "config":
        return config_command(args)

    parser.print_help()
    return 0


def start(args: argparse.Namespace) -> int:
    config = load_config()
    host = args.host or config.server.host
    requested_port = args.port or config.server.port
    resolution = resolve_port(host, requested_port, auto_port=args.auto_port)

    print(resolution.message)

    if resolution.status == "already_running":
        print(f"Endpoint: http://{host}:{resolution.selected_port}/v1")
        return 0

    if resolution.status in {"conflict", "no_available_port", "unknown"}:
        return 2

    selected_config = replace(
        config,
        server=ServerConfig(host=host, port=resolution.selected_port),
    )

    if args.save_port and resolution.changed:
        config_path = save_config(selected_config)
        print(f"Saved selected port to {config_path}")

    print(f"Endpoint: http://{host}:{resolution.selected_port}/v1")
    if args.dry_run:
        return 0

    run_server(selected_config)
    return 0


def doctor() -> int:
    config = load_config()
    resolution = resolve_port(config.server.host, config.server.port)
    endpoint = f"http://{config.server.host}:{config.server.port}/v1"

    print("KimiBridge Doctor")
    print(f"Version: {__version__}")
    print(f"Config path: {default_config_path()}")
    print(f"Configured endpoint: {endpoint}")
    print(f"Provider: {config.provider}")
    print(f"Compatibility mode: {config.compatibility.mode}")
    print(f"Kimi base URL: {config.kimi.base_url}")
    print(f"Kimi fallback base URL: {config.kimi.fallback_base_url or 'None'}")
    print(f"Port status: {resolution.status}")
    print(resolution.message)

    if resolution.status == "already_running":
        health = check_health(config.server.host, config.server.port)
        print(f"Health: {health.status}")
        print(health.message)
        return 0 if health.ok else 1

    if resolution.status == "available":
        print("Service: not running")
        return 0

    if resolution.status == "conflict":
        suggestion = resolve_port(
            config.server.host,
            config.server.port,
            auto_port=True,
        )
        if suggestion.status == "fallback":
            print(f"Suggested endpoint: http://{config.server.host}:{suggestion.selected_port}/v1")

    return 1


def status() -> int:
    config = load_config()
    health = check_health(config.server.host, config.server.port)
    endpoint = f"http://{config.server.host}:{config.server.port}/v1"

    print(f"Endpoint: {endpoint}")
    print(f"Status: {health.status}")
    print(health.message)
    return 0 if health.ok else 1


def run_service_action(action: str) -> int:
    result = service_action(action)
    print(result.message)
    if result.output:
        print(result.output.rstrip())
    return 0 if result.ok else 1


def logs() -> int:
    result = service_logs()
    print(result.message)
    if result.output:
        print(result.output.rstrip())
    return 0 if result.ok else 1


def uninstall() -> int:
    result = service_uninstall()
    print(result.message)
    if result.output:
        print(result.output.rstrip())
    return 0 if result.ok else 1


def config_command(args: argparse.Namespace) -> int:
    if args.config_command == "show":
        config = load_config()
        print(json.dumps(config_to_dict(config), indent=2))
        print(f"Config path: {default_config_path()}")
        return 0

    if args.config_command == "set":
        return set_config_value(args.key, args.value)

    print("Usage: kimibridge config show|set")
    return 2


def set_config_value(key: str, value: str) -> int:
    config = load_config()

    if key == "port":
        try:
            port = int(value)
        except ValueError:
            print("Port must be a number.")
            return 2

        if not 1 <= port <= 65535:
            print("Port must be between 1 and 65535.")
            return 2

        config = replace(config, server=replace(config.server, port=port))

    elif key == "host":
        config = replace(config, server=replace(config.server, host=value))

    elif key == "base-url":
        config = replace(config, kimi=replace(config.kimi, base_url=value))

    elif key == "fallback-base-url":
        fallback_val = value if value.strip().lower() != "none" and value.strip() != "" else None
        config = replace(config, kimi=replace(config.kimi, fallback_base_url=fallback_val))

    elif key == "compatibility-mode":
        if value not in VALID_MODES:
            print(f"Compatibility mode must be one of: {', '.join(sorted(VALID_MODES))}")
            return 2
        config = replace(config, compatibility=CompatibilityConfig(mode=value))

    elif key == "provider":
        valid_providers = {"kimi", "moonshot", "deepseek", "openai", "generic", "auto", "all"}
        val_clean = value.strip().lower()
        if val_clean not in valid_providers:
            print(f"Provider must be one of: {', '.join(sorted(valid_providers))}")
            return 2
        config = replace(config, provider=val_clean)

    else:
        print(f"Unknown config key: {key}")
        return 2

    config_path = save_config(config)
    print(f"Saved config to {config_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
