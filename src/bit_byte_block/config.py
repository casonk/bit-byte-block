"""Configuration helpers for bit-byte-block."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ProxyConfig:
    """Runtime configuration for the proxy and status client."""

    bind_host: str = "0.0.0.0"
    bind_port: int = 3333
    upstream_host: str = "solo.ckpool.org"
    upstream_port: int = 3333
    backup_host: str | None = "eusolo.ckpool.org"
    backup_port: int = 3333
    status_url: str = "https://solo.ckpool.org/pool/pool.status"
    connect_timeout: float = 10.0
    idle_timeout: float = 120.0
    log_level: str = "INFO"


def _clean_value(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def load_env_file(path: str | os.PathLike[str]) -> None:
    """Load KEY=VALUE pairs from a local env file without overriding set vars."""
    for raw_line in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        if not separator:
            raise ValueError(f"invalid env line: {raw_line!r}")
        key = key.strip()
        if not key:
            raise ValueError(f"missing env key in line: {raw_line!r}")
        os.environ.setdefault(key, _clean_value(value))


def _env(name: str, default: Any) -> Any:
    return os.environ.get(name, default)


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def load_proxy_config(args: Any | None = None) -> ProxyConfig:
    """Resolve proxy config from CLI args layered over environment defaults."""
    args = args or object()

    bind_host = getattr(args, "bind_host", None) or _env("BIT_BYTE_BLOCK_BIND_HOST", "0.0.0.0")
    bind_port = int(getattr(args, "bind_port", None) or _env("BIT_BYTE_BLOCK_BIND_PORT", 3333))
    upstream_host = getattr(args, "upstream_host", None) or _env(
        "BIT_BYTE_BLOCK_UPSTREAM_HOST", "solo.ckpool.org"
    )
    upstream_port = int(
        getattr(args, "upstream_port", None) or _env("BIT_BYTE_BLOCK_UPSTREAM_PORT", 3333)
    )
    backup_host = _optional_string(
        getattr(args, "backup_host", None)
        or _env("BIT_BYTE_BLOCK_BACKUP_HOST", "eusolo.ckpool.org")
    )
    backup_port = int(
        getattr(args, "backup_port", None) or _env("BIT_BYTE_BLOCK_BACKUP_PORT", 3333)
    )
    status_url = getattr(args, "status_url", None) or _env(
        "BIT_BYTE_BLOCK_STATUS_URL", "https://solo.ckpool.org/pool/pool.status"
    )
    connect_timeout = float(
        getattr(args, "connect_timeout", None) or _env("BIT_BYTE_BLOCK_CONNECT_TIMEOUT", 10)
    )
    idle_timeout = float(
        getattr(args, "idle_timeout", None) or _env("BIT_BYTE_BLOCK_IDLE_TIMEOUT", 120)
    )
    log_level = getattr(args, "log_level", None) or _env("BIT_BYTE_BLOCK_LOG_LEVEL", "INFO")

    return ProxyConfig(
        bind_host=bind_host,
        bind_port=bind_port,
        upstream_host=upstream_host,
        upstream_port=upstream_port,
        backup_host=backup_host,
        backup_port=backup_port,
        status_url=status_url,
        connect_timeout=connect_timeout,
        idle_timeout=idle_timeout,
        log_level=log_level,
    )
