"""Miner configuration for local Bitcoin solo mining."""

from __future__ import annotations

import json
from pathlib import Path


def write_cpuminer_config(
    config_dir: Path,
    address: str,
    worker: str,
    proxy_host: str,
    proxy_port: int,
    threads: int | None = None,
) -> Path:
    """Write cpuminer-opt JSON config (sha256d, Stratum)."""
    cfg: dict = {
        "algo": "sha256d",
        "url": f"stratum+tcp://{proxy_host}:{proxy_port}",
        "user": f"{address}.{worker}",
        "pass": "x",
    }
    if threads is not None:
        cfg["threads"] = threads
    path = config_dir / "cpuminer.json"
    path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    return path


def write_ccminer_config(
    config_dir: Path,
    address: str,
    worker: str,
    proxy_host: str,
    proxy_port: int,
) -> Path:
    """Write ccminer JSON config (sha256d, Stratum, NVIDIA CUDA)."""
    cfg = {
        "algo": "sha256d",
        "url": f"stratum+tcp://{proxy_host}:{proxy_port}",
        "user": f"{address}.{worker}",
        "pass": "x",
    }
    path = config_dir / "ccminer.json"
    path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    return path


def write_cgminer_config(
    config_dir: Path,
    address: str,
    worker: str,
    proxy_host: str,
    proxy_port: int,
) -> Path:
    """Write cgminer JSON config (sha256d, Stratum, AMD OpenCL)."""
    cfg = {
        "pools": [
            {
                "url": f"stratum+tcp://{proxy_host}:{proxy_port}",
                "user": f"{address}.{worker}",
                "pass": "x",
            }
        ]
    }
    path = config_dir / "cgminer.conf"
    path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    return path
