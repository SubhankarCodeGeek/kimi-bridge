from __future__ import annotations

import argparse
from dataclasses import replace
import json
import os
from pathlib import Path
import sys

from studiorelay import __version__
from studiorelay.compatibility import normalized_models
from studiorelay.compatibility.pipeline import VALID_MODES
from studiorelay.config import (
    DEFAULT_BASE_URL,
    AppConfig,
    CONFIG_DIR,
    LEGACY_CONFIG_DIR,
    CompatibilityConfig,
    KimiConfig,
    ServerConfig,
    config_to_dict,
    default_config_path,
    list_configured_providers,
    load_config,
    migrate_legacy_configuration,
    normalize_provider_name,
    save_config,
)
from studiorelay.health import check_health
from studiorelay.ports import resolve_port
from studiorelay.service import (
    service_action,
    service_logs,
    service_name,
    service_uninstall,
)


def ensure_user_path() -> tuple[bool, str | None]:
    """Ensure ~/.local/bin is present in ~/.bashrc or ~/.zshrc if not in active PATH."""
    home = Path.home()
    local_bin = home / ".local" / "bin"
    active_paths = [Path(p).resolve() for p in os.environ.get("PATH", "").split(os.pathsep) if p]

    try:
        local_bin.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass

    in_path = local_bin.resolve() in active_paths
    modified_file = None

    if not in_path:
        for filename in [".bashrc", ".zshrc", ".profile"]:
            cfg = home / filename
            if cfg.exists():
                try:
                    content = cfg.read_text(encoding="utf-8")
                    if ".local/bin" not in content:
                        with open(cfg, "a", encoding="utf-8") as f:
                            f.write('\n# Added by StudioRelay\nexport PATH="$HOME/.local/bin:$PATH"\n')
                        if not modified_file:
                            modified_file = filename
                except OSError:
                    pass

    return (in_path, modified_file)
from studiorelay.server import run_server


def build_parser() -> argparse.ArgumentParser:
    prog = "studiorelay"
    if len(sys.argv) > 0 and Path(sys.argv[0]).stem in {"kimibridge", "kimi-proxy"}:
        prog = Path(sys.argv[0]).stem
    parser = argparse.ArgumentParser(
        prog=prog,
        description="StudioRelay: OpenAI-compatible gateway that bridges Android Studio's AI agent with multiple LLM providers.",
    )
    parser.add_argument("--version", action="store_true", help="Print version and exit.")
    subparsers = parser.add_subparsers(dest="command")

    setup = subparsers.add_parser("setup", help="Quick setup for a target provider (deepseek, kimi, all, openai).")
    setup.add_argument("provider", choices=["deepseek", "kimi", "moonshot", "openai", "all"])
    setup.add_argument("--port", type=int, help="Port to bind.")
    setup.add_argument("--base-url", help="Custom upstream base URL. Defaults to provider standard.")
    setup.add_argument("--no-restart", action="store_true", help="Do not restart background service after setup.")

    use = subparsers.add_parser("use", help="Alias for setup: switch target provider.")
    use.add_argument("provider", choices=["deepseek", "kimi", "moonshot", "openai", "all"])
    use.add_argument("--port", type=int, help="Port to bind.")
    use.add_argument("--base-url", help="Custom upstream base URL. Defaults to provider standard.")
    use.add_argument("--no-restart", action="store_true", help="Do not restart background service after setup.")

    start_parser = subparsers.add_parser("start", help="Start the local proxy.")
    start_parser.add_argument("--host", help="Host to bind. Defaults to config or 127.0.0.1.")
    start_parser.add_argument("--port", type=int, help="Port to bind. Defaults to config or 5001.")
    start_parser.add_argument("--provider", choices=["deepseek", "kimi", "moonshot", "openai", "all"], help="Target provider profile.")
    start_parser.add_argument("--config", help="Custom configuration file path.")
    start_parser.add_argument(
        "--auto-port",
        action="store_true",
        help="Choose the next available port if the configured port is busy.",
    )
    start_parser.add_argument(
        "--save-port",
        action="store_true",
        help="Persist the selected fallback port to the config file.",
    )
    start_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve configuration and print the endpoint without starting the server.",
    )

    doctor_parser = subparsers.add_parser("doctor", help="Check local proxy configuration.")
    doctor_parser.add_argument("--provider", choices=["deepseek", "kimi", "moonshot", "openai", "all"], help="Check specific provider.")

    status_parser = subparsers.add_parser("status", help="Check whether the local proxy is running.")
    status_parser.add_argument("--provider", choices=["deepseek", "kimi", "moonshot", "openai", "all"], help="Check specific provider.")

    stop_parser = subparsers.add_parser("stop", help="Stop the installed background service.")
    stop_parser.add_argument("--provider", choices=["deepseek", "kimi", "moonshot", "openai", "all"], help="Target provider.")

    restart_parser = subparsers.add_parser("restart", help="Restart the installed background service.")
    restart_parser.add_argument("--provider", choices=["deepseek", "kimi", "moonshot", "openai", "all"], help="Target provider.")

    logs_parser = subparsers.add_parser("logs", help="Show recent background service logs.")
    logs_parser.add_argument("--provider", choices=["deepseek", "kimi", "moonshot", "openai", "all"], help="Target provider.")

    uninstall_parser = subparsers.add_parser("uninstall", help="Remove installed service and app files.")
    uninstall_parser.add_argument("--provider", choices=["deepseek", "kimi", "moonshot", "openai", "all"], help="Target provider to uninstall.")
    uninstall_parser.add_argument("--all", action="store_true", help="Remove all instances.")

    migrate_parser = subparsers.add_parser("migrate", help="Safely migrate configurations from ~/.kimibridge/ to ~/.studiorelay/.")
    migrate_parser.add_argument("--dry-run", action="store_true", help="Simulate migration without modifying files.")
    migrate_parser.add_argument("--force", action="store_true", help="Overwrite existing StudioRelay configurations.")

    config = subparsers.add_parser("config", help="Show or update local config.")
    config_subparsers = config.add_subparsers(dest="config_command")
    show_parser = config_subparsers.add_parser("show", help="Print the active config.")
    show_parser.add_argument("--provider", choices=["deepseek", "kimi", "moonshot", "openai", "all"], help="Target provider.")

    set_config = config_subparsers.add_parser("set", help="Set a config value.")
    set_config.add_argument(
        "key",
        choices=["base-url", "compatibility-mode", "fallback-base-url", "host", "port", "provider"],
    )
    set_config.add_argument("value")
    set_config.add_argument("--provider", choices=["deepseek", "kimi", "moonshot", "openai", "all"], help="Target provider.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(__version__)
        return 0

    if args.command in {"setup", "use"}:
        return setup_provider(args)

    if args.command == "start":
        return start(args)

    if args.command == "doctor":
        return doctor(args)

    if args.command == "status":
        return status(args)

    if args.command == "stop":
        return run_service_action("stop", provider=getattr(args, "provider", None))

    if args.command == "restart":
        return run_service_action("restart", provider=getattr(args, "provider", None))

    if args.command == "logs":
        return logs(args)

    if args.command == "uninstall":
        return uninstall(args)

    if args.command == "migrate":
        return run_migrate(args)

    if args.command == "config":
        return config_command(args)

    parser.print_help()
    return 0


def setup_provider(args: argparse.Namespace) -> int:
    provider = normalize_provider_name(args.provider)
    config = load_config(provider=provider)

    if getattr(args, "base_url", None):
        base_url = args.base_url.strip()
    elif provider == "deepseek":
        base_url = "https://api.deepseek.com"
    elif provider == "kimi":
        base_url = "https://api.moonshot.ai"
    elif provider == "openai":
        base_url = "https://api.openai.com"
    else:  # all
        base_url = config.kimi.base_url

    target_port = getattr(args, "port", None) or config.server.port
    resolution = resolve_port(
        config.server.host,
        target_port,
        auto_port=True,
        target_provider=provider,
    )
    port = resolution.selected_port

    new_config = replace(
        config,
        server=ServerConfig(host=config.server.host, port=port),
        provider=provider,
        kimi=replace(config.kimi, base_url=base_url),
    )
    config_path = save_config(new_config, provider=provider)

    endpoint = f"http://{new_config.server.host}:{new_config.server.port}/v1"
    print(f"StudioRelay configured for provider: {provider.upper()}")
    print(f"  Target Provider:   {provider}")
    print(f"  Upstream Base URL: {base_url}")
    print(f"  Proxy Endpoint:    {endpoint}")
    print(f"  Saved to:          {config_path}")

    models_resp = normalized_models(provider, base_url=base_url)
    models_list = [m["id"] for m in models_resp.get("data", [])]
    if models_list:
        print(f"  Available Models:  {', '.join(models_list[:6])}" + ("..." if len(models_list) > 6 else ""))

    if not getattr(args, "no_restart", False):
        health = check_health(new_config.server.host, new_config.server.port)
        if health.ok:
            result = service_action("restart", provider=provider)
            if result.ok:
                print(f"  Background Service ({service_name(provider)}): Successfully restarted")
            else:
                print(f"  Background Service: {result.message}")
        else:
            print(f"  Background Service: Not currently running (run 'studiorelay start --provider {provider} --auto-port' to start)")

    print()
    print("In Android Studio / Cursor / Aider:")
    print(f"  1. Set Base URL: {endpoint}")
    print(f"  2. Enter your {provider.capitalize()} API Key")
    print("  3. Click Refresh: Models will load into the dropdown!")

    in_path, modified_file = ensure_user_path()
    if not in_path and modified_file:
        print()
        print(f"  Tip: Added ~/.local/bin to ~/{modified_file}.")
        print("  Run 'source ~/.bashrc' to enable the 'studiorelay' command in this terminal.")
    return 0


def start(args: argparse.Namespace) -> int:
    provider = getattr(args, "provider", None)
    config_path = Path(args.config) if getattr(args, "config", None) else default_config_path(provider)
    config = load_config(path=config_path, provider=provider)
    target_provider = provider or config.provider
    host = args.host or config.server.host
    requested_port = args.port or config.server.port
    resolution = resolve_port(host, requested_port, auto_port=args.auto_port, target_provider=target_provider)

    print(resolution.message)

    if resolution.status == "already_running" and not args.save_port:
        print(f"Endpoint: http://{host}:{resolution.selected_port}/v1")
        return 0

    if resolution.status in {"conflict", "no_available_port", "unknown"}:
        return 2

    selected_config = replace(
        config,
        server=ServerConfig(host=host, port=resolution.selected_port),
        provider=target_provider,
    )

    if (args.save_port and resolution.changed) or (args.save_port and provider):
        saved_path = save_config(selected_config, path=config_path, provider=target_provider)
        print(f"Saved selected port to {saved_path}")

    print(f"Endpoint: http://{host}:{resolution.selected_port}/v1")
    if args.dry_run:
        return 0

    run_server(selected_config, config_path=config_path)
    return 0


def doctor(args: argparse.Namespace | None = None) -> int:
    provider = getattr(args, "provider", None) if args else None
    if provider:
        return _doctor_single(provider=provider)

    configured = list_configured_providers()
    if len(configured) > 1:
        print("StudioRelay Doctor (Multi-Provider Setup)")
        print(f"Version: {__version__}")
        exit_code = 0
        for p, path, cfg in configured:
            print("\n----------------------------------------")
            code = _doctor_single(provider=p, path=path, config=cfg)
            if code != 0:
                exit_code = code
        return exit_code

    return _doctor_single(provider=provider)


def _doctor_single(
    provider: str | None = None,
    path: Path | None = None,
    config: AppConfig | None = None,
) -> int:
    cfg = config or load_config(path=path, provider=provider)
    cfg_path = path or default_config_path(provider or cfg.provider)
    resolution = resolve_port(cfg.server.host, cfg.server.port, target_provider=cfg.provider)
    endpoint = f"http://{cfg.server.host}:{cfg.server.port}/v1"

    print(f"StudioRelay Doctor ({cfg.provider.upper()})")
    print(f"Version: {__version__}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Config path: {cfg_path}")
    print(f"Configured endpoint: {endpoint}")
    print(f"Provider: {cfg.provider}")
    print(f"Compatibility mode: {cfg.compatibility.mode}")
    print(f"Upstream base URL: {cfg.kimi.base_url}")
    print(f"Upstream fallback base URL: {cfg.kimi.fallback_base_url or 'None'}")
    print(f"Port status: {resolution.status}")
    print(resolution.message)

    if resolution.status == "already_running":
        health = check_health(cfg.server.host, cfg.server.port)
        print(f"Health: {health.status}")
        print(health.message)
        return 0 if health.ok else 1

    if resolution.status == "available":
        print("Service: not running")
        return 0

    if resolution.status in {"conflict", "fallback"}:
        suggestion = resolve_port(
            cfg.server.host,
            cfg.server.port,
            auto_port=True,
            target_provider=cfg.provider,
        )
        if suggestion.status == "fallback":
            print(f"Suggested endpoint: http://{cfg.server.host}:{suggestion.selected_port}/v1")

    return 1


def status(args: argparse.Namespace | None = None) -> int:
    provider = getattr(args, "provider", None) if args else None
    if provider:
        config = load_config(provider=provider)
        health = check_health(config.server.host, config.server.port)
        endpoint = f"http://{config.server.host}:{config.server.port}/v1"
        print(f"Provider: {provider}")
        print(f"Endpoint: {endpoint}")
        print(f"Status: {health.status}")
        print(health.message)
        return 0 if health.ok else 1

    configured = list_configured_providers()
    if configured:
        print("StudioRelay Configured Endpoints:")
        any_running = False
        for p, path, cfg in configured:
            h = check_health(cfg.server.host, cfg.server.port)
            stat = "running" if h.ok else "stopped"
            if h.ok:
                any_running = True
            print(f"  • {p.capitalize():<10} http://{cfg.server.host}:{cfg.server.port}/v1 [{stat}] (config: {path.name})")
        return 0 if any_running else 1

    config = load_config()
    health = check_health(config.server.host, config.server.port)
    endpoint = f"http://{config.server.host}:{config.server.port}/v1"
    print(f"Endpoint: {endpoint}")
    print(f"Status: {health.status}")
    print(health.message)
    return 0 if health.ok else 1


def run_service_action(action: str, provider: str | None = None) -> int:
    result = service_action(action, provider=provider)
    print(result.message)
    if result.output:
        print(result.output.rstrip())
    return 0 if result.ok else 1


def logs(args: argparse.Namespace | None = None) -> int:
    provider = getattr(args, "provider", None) if args else None
    result = service_logs(provider=provider)
    print(result.message)
    if result.output:
        print(result.output.rstrip())
    return 0 if result.ok else 1


def uninstall(args: argparse.Namespace | None = None) -> int:
    is_all = getattr(args, "all", False) if args else False
    provider = getattr(args, "provider", None) if args and not is_all else None
    result = service_uninstall(provider=provider, all_instances=is_all)
    print(result.message)
    if result.output:
        print(result.output.rstrip())
    return 0 if result.ok else 1


def run_migrate(args: argparse.Namespace) -> int:
    dry_run = getattr(args, "dry_run", False)
    force = getattr(args, "force", False)
    src = Path(getattr(args, "source", None) or LEGACY_CONFIG_DIR)
    dst = Path(getattr(args, "destination", None) or CONFIG_DIR)
    report = migrate_legacy_configuration(source_dir=src, dest_dir=dst, dry_run=dry_run, force=force)

    if not report["source_found"]:
        print(f"No legacy KimiBridge directory found at {report['source_dir']}.")
        return 0

    mode_str = " (dry-run)" if dry_run else ""
    print(f"StudioRelay Migration{mode_str}:")
    print(f"  Source:      {report['source_dir']}")
    print(f"  Destination: {report['dest_dir']}")
    if report["backup_path"]:
        print(f"  Backup saved to: {report['backup_path']}")

    if report["copied"]:
        print(f"  Configurations migrated: {', '.join(report['copied'])}")
    if report["skipped"]:
        print(f"  Configurations skipped (already exist): {', '.join(report['skipped'])} (use --force to overwrite)")

    if report["error"]:
        print(f"  Error: {report['error']}")
        return 1

    print("Migration completed successfully.")
    return 0


def config_command(args: argparse.Namespace) -> int:
    provider = getattr(args, "provider", None)
    if args.config_command == "show":
        config = load_config(provider=provider)
        print(json.dumps(config_to_dict(config), indent=2))
        print(f"Config path: {default_config_path(provider)}")
        return 0

    if args.config_command == "set":
        return set_config_value(args.key, args.value, provider=provider)

    print("Usage: studiorelay config show|set")
    return 2


def set_config_value(key: str, value: str, provider: str | None = None) -> int:
    config = load_config(provider=provider)

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
        clean_url = value.strip()
        new_provider = config.provider
        if "deepseek.com" in clean_url.lower() and config.provider in {"kimi", "auto"}:
            new_provider = "deepseek"
        elif "moonshot.ai" in clean_url.lower() and config.provider == "deepseek":
            new_provider = "kimi"
        elif "openai.com" in clean_url.lower() and config.provider in {"kimi", "auto"}:
            new_provider = "openai"

        config = replace(
            config,
            provider=new_provider,
            kimi=replace(config.kimi, base_url=clean_url),
        )

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

        new_base_url = config.kimi.base_url
        if val_clean == "deepseek" and (config.kimi.base_url == DEFAULT_BASE_URL or "moonshot.ai" in config.kimi.base_url):
            new_base_url = "https://api.deepseek.com"
        elif val_clean in {"kimi", "moonshot"} and ("deepseek.com" in config.kimi.base_url):
            new_base_url = DEFAULT_BASE_URL
        elif val_clean == "openai" and (config.kimi.base_url == DEFAULT_BASE_URL or "moonshot.ai" in config.kimi.base_url):
            new_base_url = "https://api.openai.com"

        config = replace(
            config,
            provider=val_clean,
            kimi=replace(config.kimi, base_url=new_base_url),
        )

    else:
        print(f"Unknown config key: {key}")
        return 2

    config_path = save_config(config, provider=provider or config.provider)
    print(f"Saved config to {config_path}")
    health = check_health(config.server.host, config.server.port)
    if health.ok:
        restart_res = service_action("restart", provider=provider or config.provider)
        if restart_res.ok:
            print("Background service restarted to apply changes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
