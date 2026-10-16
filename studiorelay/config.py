from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import shutil
import time
from typing import Any


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5001
DEFAULT_BASE_URL = "https://api.moonshot.ai"
DEFAULT_PROVIDER = "kimi"


@dataclass(frozen=True)
class ServerConfig:
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT


@dataclass(frozen=True)
class KimiConfig:
    base_url: str = DEFAULT_BASE_URL
    fallback_base_url: str | None = None


# UpstreamConfig is an alias for KimiConfig for provider-neutral terminology
UpstreamConfig = KimiConfig


@dataclass(frozen=True)
class CompatibilityConfig:
    mode: str = "compatible"


@dataclass(frozen=True)
class AppConfig:
    server: ServerConfig = ServerConfig()
    kimi: KimiConfig = KimiConfig()
    compatibility: CompatibilityConfig = CompatibilityConfig()
    provider: str = DEFAULT_PROVIDER

    @property
    def upstream(self) -> KimiConfig:
        return self.kimi


def normalize_provider_name(provider: str | None) -> str:
    p = (provider or "").strip().lower()
    if p in {"moonshot"}:
        return "kimi"
    return p


def get_studiorelay_dir() -> Path:
    return Path.home() / ".studiorelay"


def get_legacy_dir() -> Path:
    return Path.home() / ".kimibridge"


CONFIG_DIR = get_studiorelay_dir()
LEGACY_CONFIG_DIR = get_legacy_dir()


def legacy_config_path(provider: str | None = None) -> Path:
    p = normalize_provider_name(provider)
    if p and p not in {"all", "both", "auto", "default"}:
        return Path(LEGACY_CONFIG_DIR) / f"config-{p}.json"
    return Path(LEGACY_CONFIG_DIR) / "config.json"


def studiorelay_config_path(provider: str | None = None) -> Path:
    p = normalize_provider_name(provider)
    if p and p not in {"all", "both", "auto", "default"}:
        return Path(CONFIG_DIR) / f"config-{p}.json"
    return Path(CONFIG_DIR) / "config.json"


def config_path_for(provider: str | None = None, path: Path | None = None) -> Path:
    """
    Resolve configuration path by precedence:
    1. Explicit path argument
    2. STUDIORELAY_CONFIG environment variable
    3. KIMIBRIDGE_CONFIG environment variable (legacy)
    4. Existing StudioRelay configuration (~/.studiorelay/config*.json)
    5. Existing KimiBridge configuration (~/.kimibridge/config*.json)
    6. Default StudioRelay configuration path (~/.studiorelay/config*.json)
    """
    if path is not None:
        return path

    env_config = os.environ.get("STUDIORELAY_CONFIG") or os.environ.get("KIMIBRIDGE_CONFIG")
    if env_config:
        return Path(env_config)

    sr_path = studiorelay_config_path(provider)
    if sr_path.exists():
        return sr_path

    legacy_path = legacy_config_path(provider)
    if legacy_path.exists():
        return legacy_path

    return sr_path


def default_config_path(provider: str | None = None) -> Path:
    return config_path_for(provider=provider)


resolve_config_path = config_path_for


def _read_config_file(config_path: Path) -> AppConfig:
    data = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Config file must contain a JSON object.")

    server = data.get("server", {})
    # Support both upstream and kimi keys for provider-neutral config format
    upstream = data.get("upstream") or data.get("kimi", {})
    compatibility = data.get("compatibility", {})
    provider = str(data.get("provider", DEFAULT_PROVIDER))

    fallback_raw = upstream.get("fallback_base_url")
    fallback_base_url = str(fallback_raw) if fallback_raw is not None else None

    return AppConfig(
        server=ServerConfig(
            host=str(server.get("host", DEFAULT_HOST)),
            port=int(server.get("port", DEFAULT_PORT)),
        ),
        kimi=KimiConfig(
            base_url=str(upstream.get("base_url", DEFAULT_BASE_URL)),
            fallback_base_url=fallback_base_url,
        ),
        compatibility=CompatibilityConfig(
            mode=str(compatibility.get("mode", "compatible"))
        ),
        provider=provider,
    )


def load_config(path: Path | None = None, provider: str | None = None) -> AppConfig:
    config_path = path or default_config_path(provider)
    if not config_path.exists():
        # If a provider-specific config does not exist yet, check if primary config matches
        primary_path = default_config_path()
        if provider and primary_path.exists():
            try:
                candidate = _read_config_file(primary_path)
                if normalize_provider_name(candidate.provider) == normalize_provider_name(provider):
                    return candidate
            except Exception:
                pass
        prov_norm = normalize_provider_name(provider) or DEFAULT_PROVIDER
        base_url = DEFAULT_BASE_URL
        if prov_norm == "deepseek":
            base_url = "https://api.deepseek.com"
        elif prov_norm == "openai":
            base_url = "https://api.openai.com"
        return AppConfig(provider=prov_norm, kimi=KimiConfig(base_url=base_url))

    return _read_config_file(config_path)


def list_configured_providers(config_dir: Path | None = None) -> list[tuple[str, Path, AppConfig]]:
    results: list[tuple[str, Path, AppConfig]] = []
    seen_providers: set[str] = set()

    dirs_to_check: list[Path] = []
    if config_dir is not None:
        dirs_to_check.append(config_dir)
    else:
        # Precedence: check ~/.studiorelay first, then ~/.kimibridge
        sr_dir = get_studiorelay_dir()
        if sr_dir.exists():
            dirs_to_check.append(sr_dir)
        legacy_dir = get_legacy_dir()
        if legacy_dir.exists():
            dirs_to_check.append(legacy_dir)

    for dir_path in dirs_to_check:
        if not dir_path.exists():
            continue

        # Look for provider-specific configs: config-<provider>.json
        for path in sorted(dir_path.glob("config-*.json")):
            provider_name = path.stem.removeprefix("config-")
            norm_name = normalize_provider_name(provider_name)
            if norm_name in seen_providers:
                continue
            try:
                cfg = _read_config_file(path)
                results.append((norm_name, path, cfg))
                seen_providers.add(norm_name)
            except Exception:
                pass

        # Check generic config.json if not already represented
        primary = dir_path / "config.json"
        if primary.exists():
            try:
                cfg = _read_config_file(primary)
                p = normalize_provider_name(cfg.provider)
                if p not in seen_providers:
                    results.append((p, primary, cfg))
                    seen_providers.add(p)
            except Exception:
                pass

    return results


def config_to_dict(config: AppConfig) -> dict[str, Any]:
    return {
        "server": {
            "host": config.server.host,
            "port": config.server.port,
        },
        "kimi": {
            "base_url": config.kimi.base_url,
            "fallback_base_url": config.kimi.fallback_base_url,
        },
        "compatibility": {
            "mode": config.compatibility.mode,
        },
        "provider": config.provider,
    }


def save_config(
    config: AppConfig,
    path: Path | None = None,
    provider: str | None = None,
) -> Path:
    target_provider = provider or config.provider
    config_path = path or default_config_path(target_provider)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    payload = config_to_dict(config)
    config_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    # If saving a provider-specific config, also maintain config.json if it is missing
    # or currently set to this provider
    primary_path = default_config_path()
    if config_path != primary_path:
        try:
            if not primary_path.exists():
                primary_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            else:
                existing = _read_config_file(primary_path)
                if normalize_provider_name(existing.provider) == normalize_provider_name(config.provider):
                    primary_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        except Exception:
            pass

    return config_path


def migrate_legacy_configuration(
    source_dir: Path | None = None,
    dest_dir: Path | None = None,
    *,
    dry_run: bool = False,
    force: bool = False,
) -> dict[str, Any]:
    """
    Safely and idempotently migrate configuration files from legacy ~/.kimibridge/ to ~/.studiorelay/.
    Creates a timestamped backup before any modifications.
    Never prints or logs secret contents.
    """
    src = source_dir or get_legacy_dir()
    dst = dest_dir or get_studiorelay_dir()

    report: dict[str, Any] = {
        "source_dir": str(src),
        "dest_dir": str(dst),
        "source_found": src.exists(),
        "copied": [],
        "skipped": [],
        "backup_path": None,
        "dry_run": dry_run,
        "error": None,
    }

    if not src.exists():
        return report

    configs = sorted([p for p in src.glob("*.json") if p.is_file()])
    if not configs:
        return report

    if not dry_run:
        # Create backup directory inside ~/.kimibridge/backups/<timestamp>
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_dir = src / "backups" / timestamp
        backup_dir.mkdir(parents=True, exist_ok=True)
        report["backup_path"] = str(backup_dir)

        dst.mkdir(parents=True, exist_ok=True)

    for cfg in configs:
        target_file = dst / cfg.name
        if target_file.exists() and not force:
            report["skipped"].append(cfg.name)
            continue

        if not dry_run:
            # Backup original
            shutil.copy2(cfg, backup_dir / cfg.name)
            # Copy to new location with verified JSON validity
            try:
                data = json.loads(cfg.read_text(encoding="utf-8"))
                target_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
                report["copied"].append(cfg.name)
            except Exception as exc:
                report["error"] = f"Failed migrating {cfg.name}: {exc}"
        else:
            report["copied"].append(cfg.name)

    return report
