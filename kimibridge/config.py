from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
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


@dataclass(frozen=True)
class CompatibilityConfig:
    mode: str = "compatible"


@dataclass(frozen=True)
class AppConfig:
    server: ServerConfig = ServerConfig()
    kimi: KimiConfig = KimiConfig()
    compatibility: CompatibilityConfig = CompatibilityConfig()
    provider: str = DEFAULT_PROVIDER


def normalize_provider_name(provider: str | None) -> str:
    p = (provider or "").strip().lower()
    if p in {"moonshot"}:
        return "kimi"
    return p


def config_path_for(provider: str | None = None, path: Path | None = None) -> Path:
    if path is not None:
        return path
    env_config = os.environ.get("STUDIORELAY_CONFIG") or os.environ.get("KIMIBRIDGE_CONFIG")
    if env_config:
        return Path(env_config)
    p = normalize_provider_name(provider)
    filename = f"config-{p}.json" if p and p not in {"all", "both", "auto", "default"} else "config.json"
    sr_path = Path.home() / ".studiorelay" / filename
    if sr_path.exists():
        return sr_path
    legacy_path = Path.home() / ".kimibridge" / filename
    if legacy_path.exists():
        return legacy_path
    return legacy_path


def default_config_path(provider: str | None = None) -> Path:
    return config_path_for(provider=provider)


def _read_config_file(config_path: Path) -> AppConfig:
    data = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Config file must contain a JSON object.")

    server = data.get("server", {})
    kimi = data.get("kimi", {})
    compatibility = data.get("compatibility", {})
    provider = str(data.get("provider", DEFAULT_PROVIDER))

    fallback_raw = kimi.get("fallback_base_url")
    fallback_base_url = str(fallback_raw) if fallback_raw is not None else None

    return AppConfig(
        server=ServerConfig(
            host=str(server.get("host", DEFAULT_HOST)),
            port=int(server.get("port", DEFAULT_PORT)),
        ),
        kimi=KimiConfig(
            base_url=str(kimi.get("base_url", DEFAULT_BASE_URL)),
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
    dir_path = config_dir or (Path.home() / ".kimibridge")
    if not dir_path.exists():
        return []

    results: list[tuple[str, Path, AppConfig]] = []
    seen_providers: set[str] = set()

    # Look for provider-specific configs: config-<provider>.json
    for path in sorted(dir_path.glob("config-*.json")):
        provider_name = path.stem.removeprefix("config-")
        try:
            cfg = _read_config_file(path)
            results.append((normalize_provider_name(provider_name), path, cfg))
            seen_providers.add(normalize_provider_name(provider_name))
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
