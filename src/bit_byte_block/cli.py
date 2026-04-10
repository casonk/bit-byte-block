"""Command-line interface for bit-byte-block."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from typing import Any

from .config import ProxyConfig, load_env_file, load_proxy_config
from .monitor import fetch_pool_status_snapshot
from .proxy import StratumProxyServer


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level CLI parser."""
    parser = argparse.ArgumentParser(
        prog="bit-byte-block",
        description="Local Bitcoin Stratum proxy and status tooling for solo.ckpool.org.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    proxy_parser = subparsers.add_parser("proxy", help="Run the local Stratum proxy service.")
    proxy_parser.add_argument(
        "--env-file", help="Optional env file to load before resolving config."
    )
    proxy_parser.add_argument("--bind-host", help="Host/interface to bind locally.")
    proxy_parser.add_argument("--bind-port", type=int, help="Local TCP port to bind.")
    proxy_parser.add_argument("--upstream-host", help="Primary upstream host.")
    proxy_parser.add_argument("--upstream-port", type=int, help="Primary upstream TCP port.")
    proxy_parser.add_argument("--backup-host", help="Optional backup upstream host.")
    proxy_parser.add_argument("--backup-port", type=int, help="Optional backup upstream TCP port.")
    proxy_parser.add_argument(
        "--connect-timeout", type=float, help="Upstream connect timeout in seconds."
    )
    proxy_parser.add_argument("--idle-timeout", type=float, help="Idle relay timeout in seconds.")
    proxy_parser.add_argument("--log-level", help="Python logging level.")

    status_parser = subparsers.add_parser("status", help="Fetch upstream pool status.")
    status_parser.add_argument(
        "--env-file", help="Optional env file to load before resolving config."
    )
    status_parser.add_argument("--status-url", help="Pool-status URL override.")
    status_parser.add_argument(
        "--timeout", type=float, default=10.0, help="HTTP timeout in seconds."
    )
    status_parser.add_argument(
        "--json", action="store_true", help="Print the full snapshot as JSON."
    )

    return parser


def format_snapshot(snapshot: dict[str, Any]) -> str:
    """Format the upstream pool status snapshot for terminal output."""
    summary = snapshot["summary"]
    hashrate = snapshot["hashrate"]
    shares = snapshot["shares"]
    lines = [
        f"lastupdate={summary.get('lastupdate')}",
        f"users={summary.get('Users')} workers={summary.get('Workers')}",
        (
            f"idle={summary.get('Idle')} disconnected={summary.get('Disconnected')} "
            f"runtime={summary.get('runtime')}"
        ),
        (
            f"hashrate: 1m={hashrate.get('hashrate1m')} 5m={hashrate.get('hashrate5m')} "
            f"15m={hashrate.get('hashrate15m')} 1h={hashrate.get('hashrate1hr')}"
        ),
        (
            f"shares: diff={shares.get('diff')} accepted={shares.get('accepted')} "
            f"rejected={shares.get('rejected')} bestshare={shares.get('bestshare')}"
        ),
    ]
    return "\n".join(lines)


async def run_proxy(config: ProxyConfig) -> None:
    """Run the Stratum proxy until interrupted."""
    server = StratumProxyServer(config)
    await server.start()
    logging.getLogger(__name__).info(
        "proxy listening on %s:%s -> %s:%s",
        config.bind_host,
        config.bind_port,
        config.upstream_host,
        config.upstream_port,
    )
    if config.backup_host:
        logging.getLogger(__name__).info(
            "backup upstream configured: %s:%s",
            config.backup_host,
            config.backup_port,
        )
    try:
        await server.serve_forever()
    finally:
        await server.close()


def configure_logging(level: str) -> None:
    """Configure process logging."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    env_file = getattr(args, "env_file", None)
    if env_file:
        load_env_file(env_file)

    if args.command == "proxy":
        config = load_proxy_config(args)
        configure_logging(args.log_level or config.log_level)
        try:
            asyncio.run(run_proxy(config))
        except KeyboardInterrupt:
            logging.getLogger(__name__).info("proxy interrupted")
        return 0

    if args.command == "status":
        config = load_proxy_config(args)
        snapshot = fetch_pool_status_snapshot(
            args.status_url or config.status_url, timeout=args.timeout
        )
        if args.json:
            print(json.dumps(snapshot, indent=2, sort_keys=True))
        else:
            print(format_snapshot(snapshot))
        return 0

    parser.error(f"unsupported command: {args.command}")
    return 2
