from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5001
DEFAULT_BASE_URL = "https://api.moonshot.ai"


@dataclass(frozen=True)
class ServerConfig:
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT


@dataclass(frozen=True)
class KimiConfig:
    base_url: str = DEFAULT_BASE_URL


@dataclass(frozen=True)
class CompatibilityConfig:
    mode: str = "compatible"


@dataclass(frozen=True)
class AppConfig:
    server: ServerConfig = ServerConfig()
    kimi: KimiConfig = KimiConfig()
    compatibility: CompatibilityConfig = CompatibilityConfig()


def default_config_path() -> Path:
    return Path.home() / ".kimibridge" / "config.json"


def load_config(path: Path | None = None) -> AppConfig:
    config_path = path or default_config_path()
    if not config_path.exists():
        return AppConfig()

    data = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Config file must contain a JSON object.")

    server = data.get("server", {})
    kimi = data.get("kimi", {})
    compatibility = data.get("compatibility", {})

    return AppConfig(
        server=ServerConfig(
            host=str(server.get("host", DEFAULT_HOST)),
            port=int(server.get("port", DEFAULT_PORT)),
        ),
        kimi=KimiConfig(base_url=str(kimi.get("base_url", DEFAULT_BASE_URL))),
        compatibility=CompatibilityConfig(
            mode=str(compatibility.get("mode", "compatible"))
        ),
    )


def config_to_dict(config: AppConfig) -> dict[str, Any]:
    return {
        "server": {
            "host": config.server.host,
            "port": config.server.port,
        },
        "kimi": {
            "base_url": config.kimi.base_url,
        },
        "compatibility": {
            "mode": config.compatibility.mode,
        },
    }


def save_config(config: AppConfig, path: Path | None = None) -> Path:
    config_path = path or default_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    payload = config_to_dict(config)
    config_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return config_path
