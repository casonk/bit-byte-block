"""Command-line interface for bit-byte-block."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from .config import ProxyConfig, load_env_file, load_proxy_config
from .monitor import fetch_pool_status_snapshot
from .proxy import StratumProxyServer

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


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

    wallet_parser = subparsers.add_parser("wallet", help="Manage the solo mining wallet.")
    wallet_sub = wallet_parser.add_subparsers(dest="wallet_action", required=True)
    gen_parser = wallet_sub.add_parser(
        "generate", help="Generate a new secp256k1 keypair and native SegWit address."
    )
    gen_parser.add_argument(
        "--save",
        action="store_true",
        help="Store the WIF key and address in KeePassXC via auto-pass.",
    )
    gen_parser.add_argument(
        "--keepass-entry",
        default="crypto/bitcoin/solo-mining",
        help="KeePass entry path (default: crypto/bitcoin/solo-mining).",
    )
    gen_parser.add_argument(
        "--auto-pass-env",
        help="Path to an auto-pass env file to load before saving (sets AUTO_PASS_KEEPASSXC_DB_PATH etc.).",
    )

    miner_parser = subparsers.add_parser("miner", help="Install and configure local miners.")
    miner_sub = miner_parser.add_subparsers(dest="miner_action", required=True)

    # -- miner install --
    mi_parser = miner_sub.add_parser(
        "install", help="Install miner binaries via dnf or print build instructions."
    )
    mi_parser.add_argument("--cpu", action="store_true", help="Install cpuminer-opt (CPU).")
    mi_parser.add_argument("--nvidia", action="store_true", help="Install ccminer (NVIDIA CUDA).")
    mi_parser.add_argument("--amd", action="store_true", help="Install cgminer (AMD OpenCL).")

    # -- miner configure --
    mc_parser = miner_sub.add_parser(
        "configure", help="Write miner config files and install systemd unit files."
    )
    mc_parser.add_argument("--cpu", action="store_true", help="Configure cpuminer-opt.")
    mc_parser.add_argument("--nvidia", action="store_true", help="Configure ccminer.")
    mc_parser.add_argument("--amd", action="store_true", help="Configure cgminer.")
    mc_parser.add_argument(
        "--address",
        help="Bitcoin address. Looked up from KeePassXC if omitted.",
    )
    mc_parser.add_argument(
        "--worker", default="desk", help="Worker name appended to address (default: desk)."
    )
    mc_parser.add_argument(
        "--proxy-host", default="127.0.0.1", help="Stratum proxy host (default: 127.0.0.1)."
    )
    mc_parser.add_argument(
        "--proxy-port", type=int, default=3333, help="Stratum proxy port (default: 3333)."
    )
    mc_parser.add_argument(
        "--threads", type=int, help="CPU thread count for cpuminer (default: auto)."
    )
    mc_parser.add_argument(
        "--keepass-entry",
        default="crypto/bitcoin/solo-mining",
        help="KeePass entry to read address from (default: crypto/bitcoin/solo-mining).",
    )
    mc_parser.add_argument(
        "--auto-pass-env",
        help="Path to an auto-pass env file (sets AUTO_PASS_KEEPASSXC_DB_PATH etc.).",
    )
    mc_parser.add_argument(
        "--target",
        choices=["systemd-user", "systemd-system"],
        default="systemd-user",
        help="Systemd installation target (default: systemd-user).",
    )

    setup_parser = subparsers.add_parser(
        "setup", help="Install the proxy as a systemd service via clockwork."
    )
    setup_parser.add_argument(
        "--target",
        choices=["systemd-user", "systemd-system"],
        default="systemd-user",
        help="Systemd installation target (default: systemd-user).",
    )
    setup_parser.add_argument(
        "--manifest",
        help="Path to the clockwork manifest TOML. Defaults to config/clockwork.toml in the repo root.",
    )
    setup_parser.add_argument(
        "--env-file",
        help="Path to the runtime env file. Created from the example if missing.",
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


def run_wallet(args: Any) -> int:
    """Dispatch wallet subcommands."""
    if args.wallet_action == "generate":
        return _wallet_generate(args)
    return 0


def _wallet_generate(args: Any) -> int:
    """Generate a new keypair and optionally save to KeePassXC."""
    from .wallet import generate_keypair

    wif, address = generate_keypair()

    print(f"address : {address}")
    print(f"wif     : {wif}")
    print()
    print("Configure each miner's username as:  <address>.<worker>")
    print(f"Example: {address}.desk")

    if args.save:
        try:
            from auto_pass import (
                KeepassCommandError,
                apply_keepass_profile_environment,
                ensure_group,
                upsert_keepassxc_entry,
            )
        except ImportError:
            print("error: auto-pass is not installed", file=sys.stderr)
            return 1
        if args.auto_pass_env:
            load_env_file(args.auto_pass_env)
        apply_keepass_profile_environment()
        try:
            # keepassxc-cli mkdir does not create parent groups recursively,
            # so create each ancestor in order before the upsert.
            parts = [p for p in args.keepass_entry.strip("/").split("/") if p]
            for depth in range(1, len(parts)):
                ensure_group("/".join(parts[:depth]), allow_interactive=True)
            mode = upsert_keepassxc_entry(
                entry=args.keepass_entry,
                username=address,
                password=wif,
                notes=f"Bitcoin solo mining wallet\nAddress: {address}",
                create_group=True,
                allow_interactive=True,
            )
        except KeepassCommandError as exc:
            print(f"error: {exc}", file=sys.stderr)
            print(
                "hint: set AUTO_PASS_KEEPASSXC_DB_PATH or pass --auto-pass-env <path>",
                file=sys.stderr,
            )
            return 1
        print(f"\nSaved to KeePassXC ({mode}): {args.keepass_entry}")
    else:
        print("\nWARNING: back up your WIF key now — it will not be shown again.")

    return 0


def run_miner(args: Any) -> int:
    """Dispatch miner subcommands."""
    if args.miner_action == "install":
        return _miner_install(args)
    if args.miner_action == "configure":
        return _miner_configure(args)
    return 0


def _rpm_fusion_enabled(repo_id: str) -> bool:
    result = subprocess.run(
        ["dnf", "repolist", "--enabled"],
        capture_output=True,
        text=True,
        check=False,
    )
    return repo_id in result.stdout


def _run_shell(cmd: str) -> int:
    """Run cmd via bash -c, printing it first. Returns returncode."""
    print(f"  + {cmd}")
    return subprocess.run(cmd, shell=True, check=False).returncode


def _ensure_rpm_fusion(nonfree: bool = False) -> int:
    """Enable RPM Fusion free or nonfree if not already enabled."""
    tier = "nonfree" if nonfree else "free"
    repo_id = f"rpmfusion-{tier}"
    if _rpm_fusion_enabled(repo_id):
        return 0
    print(f"enabling RPM Fusion {tier} ...")
    return _run_shell(
        f"sudo dnf install -y "
        f"https://download1.rpmfusion.org/{tier}/fedora/"
        f"rpmfusion-{tier}-release-$(rpm -E %fedora).noarch.rpm"
    )


def _install_cpu() -> int:
    """Install cpuminer-opt. Try dnf first, fall back to source build."""
    found = next((b for b in ("cpuminer-opt", "cpuminer", "minerd") if shutil.which(b)), None)
    if found:
        print(f"cpu: {found} already installed ({shutil.which(found)}).")
        return 0

    rc = _ensure_rpm_fusion(nonfree=False)
    if rc != 0:
        print("cpu: failed to enable RPM Fusion free.", file=sys.stderr)
        return rc

    print("cpu: trying dnf install cpuminer ...")
    if subprocess.run(["sudo", "dnf", "install", "-y", "cpuminer"], check=False).returncode == 0:
        print("cpu: installed cpuminer via dnf.")
        return 0

    print("cpu: dnf package unavailable; building cpuminer-opt from source ...")
    steps = [
        "sudo dnf install -y autoconf automake libcurl-devel openssl-devel gmp-devel",
        "rm -rf /tmp/cpuminer-opt && git clone https://github.com/JayDDee/cpuminer-opt /tmp/cpuminer-opt",
        "cd /tmp/cpuminer-opt && ./autogen.sh",
        "cd /tmp/cpuminer-opt && ./configure CFLAGS='-O3 -march=native' LDFLAGS='-lcurl' --prefix=$HOME/.local",
        "cd /tmp/cpuminer-opt && make -j$(nproc) && make install",
    ]
    for step in steps:
        rc = _run_shell(step)
        if rc != 0:
            print(f"cpu: build step failed (rc={rc}).", file=sys.stderr)
            return rc

    # cpuminer-opt installs the binary as "cpuminer" (not "cpuminer-opt")
    local_bin = Path.home() / ".local" / "bin" / "cpuminer"
    found = next((b for b in ("cpuminer-opt", "cpuminer", "minerd") if shutil.which(b)), None)
    if found or local_bin.exists():
        print("cpu: cpuminer-opt installed.")
        if not found:
            print("  hint: ensure ~/.local/bin is on your PATH")
        return 0
    print("cpu: build finished but binary not found.", file=sys.stderr)
    return 1


def _install_nvidia() -> int:
    """Install ccminer (CUDA). Always requires source build — not in any distro repo."""
    if shutil.which("ccminer"):
        print(f"nvidia: ccminer already installed ({shutil.which('ccminer')}).")
        return 0

    # nvcc (CUDA compiler) is required to build ccminer.
    # It is NOT in RPM Fusion — it lives in NVIDIA's own CUDA repo.
    if not shutil.which("nvcc"):
        fedora_ver = subprocess.run(
            "rpm -E %fedora", shell=True, capture_output=True, text=True, check=False
        ).stdout.strip()
        print("nvidia: nvcc not found. Install the CUDA toolkit:", file=sys.stderr)
        print(
            f"  sudo dnf config-manager --add-repo \\\n"
            f"    https://developer.download.nvidia.com/compute/cuda/repos/"
            f"fedora{fedora_ver}/x86_64/cuda-fedora{fedora_ver}.repo\n"
            f"  sudo dnf install -y cuda-toolkit\n"
            f"Then re-run:  python3 -m bit_byte_block miner install --nvidia",
            file=sys.stderr,
        )
        return 1

    print("nvidia: building ccminer from source ...")
    steps = [
        "rm -rf /tmp/ccminer && git clone https://github.com/tpruvot/ccminer /tmp/ccminer",
        "cd /tmp/ccminer && ./autogen.sh && ./configure",
        "cd /tmp/ccminer && make -j$(nproc)",
        "mkdir -p $HOME/.local/bin && cp /tmp/ccminer/ccminer $HOME/.local/bin/",
    ]
    for step in steps:
        rc = _run_shell(step)
        if rc != 0:
            print(f"nvidia: build step failed (rc={rc}).", file=sys.stderr)
            return rc

    local_bin = Path.home() / ".local" / "bin" / "ccminer"
    if shutil.which("ccminer") or local_bin.exists():
        print("nvidia: ccminer installed.")
        if not shutil.which("ccminer"):
            print("  hint: ensure ~/.local/bin is on your PATH")
        return 0
    print("nvidia: build finished but binary not found.", file=sys.stderr)
    return 1


def _install_amd() -> int:
    """Install cgminer. Try dnf first, fall back to source build."""
    if shutil.which("cgminer"):
        print(f"amd: cgminer already installed ({shutil.which('cgminer')}).")
        return 0

    rc = _ensure_rpm_fusion(nonfree=False)
    if rc != 0:
        print("amd: failed to enable RPM Fusion free.", file=sys.stderr)
        return rc

    print("amd: trying dnf install cgminer ...")
    if subprocess.run(["sudo", "dnf", "install", "-y", "cgminer"], check=False).returncode == 0:
        print("amd: installed cgminer via dnf.")
        return 0

    print("amd: dnf package unavailable; building cgminer from source ...")
    steps = [
        "sudo dnf install -y autoconf automake libtool opencl-headers",
        "rm -rf /tmp/cgminer && git clone https://github.com/ckolivas/cgminer /tmp/cgminer",
        "cd /tmp/cgminer && ./autogen.sh",
        "cd /tmp/cgminer && ./configure --enable-opencl CFLAGS='-fcommon -O2'",
        "cd /tmp/cgminer && make -j$(nproc)",
        "cd /tmp/cgminer && sudo make install",
    ]
    for step in steps:
        rc = _run_shell(step)
        if rc != 0:
            print(f"amd: build step failed (rc={rc}).", file=sys.stderr)
            return rc

    if shutil.which("cgminer"):
        print("amd: cgminer installed.")
        return 0
    print("amd: build finished but binary not found.", file=sys.stderr)
    return 1


def _miner_install(args: Any) -> int:
    """Install miner binaries, enabling RPM Fusion and building from source as needed."""
    if not any([args.cpu, args.nvidia, args.amd]):
        print("error: specify at least one of --cpu, --nvidia, --amd", file=sys.stderr)
        return 1

    rc = 0
    if args.cpu:
        rc = max(rc, _install_cpu())
    if args.nvidia:
        rc = max(rc, _install_nvidia())
    if args.amd:
        rc = max(rc, _install_amd())
    return rc


def _resolve_address(args: Any) -> str | None:
    """Return the BTC address from --address or KeePassXC."""
    if args.address:
        return args.address
    try:
        from auto_pass import (
            apply_keepass_profile_environment,
            resolve_keepassxc_entry,
        )
    except ImportError:
        return None
    if args.auto_pass_env:
        load_env_file(args.auto_pass_env)
    apply_keepass_profile_environment()
    try:
        result = resolve_keepassxc_entry(
            args.keepass_entry,
            attrs_map={"address": "username"},
            allow_interactive=True,
        )
        return result.get("address")
    except Exception:
        return None


def _miner_configure(args: Any) -> int:
    """Write miner config files and install systemd unit files via clockwork."""
    from .miner import write_ccminer_config, write_cgminer_config, write_cpuminer_config

    if not any([args.cpu, args.nvidia, args.amd]):
        print("error: specify at least one of --cpu, --nvidia, --amd", file=sys.stderr)
        return 1

    address = _resolve_address(args)
    if not address:
        print(
            "error: provide --address or configure KeePass via --auto-pass-env",
            file=sys.stderr,
        )
        return 1

    config_dir = _REPO_ROOT / "config" / "miners"
    config_dir.mkdir(parents=True, exist_ok=True)

    manifests: list[Path] = []

    if args.cpu:
        path = write_cpuminer_config(
            config_dir,
            address,
            args.worker,
            args.proxy_host,
            args.proxy_port,
            getattr(args, "threads", None),
        )
        print(f"wrote {path}")
        manifests.append(_REPO_ROOT / "config" / "miners" / "clockwork-cpu.toml")

    if args.nvidia:
        path = write_ccminer_config(
            config_dir, address, args.worker, args.proxy_host, args.proxy_port
        )
        print(f"wrote {path}")
        manifests.append(_REPO_ROOT / "config" / "miners" / "clockwork-nvidia.toml")

    if args.amd:
        path = write_cgminer_config(
            config_dir, address, args.worker, args.proxy_host, args.proxy_port
        )
        print(f"wrote {path}")
        manifests.append(_REPO_ROOT / "config" / "miners" / "clockwork-amd.toml")

    for manifest in manifests:
        result = subprocess.run(
            ["clockwork", "install", "--manifest", str(manifest), "--target", args.target],
            check=False,
        )
        if result.returncode != 0:
            return result.returncode

    if manifests:
        print("\nNext steps:")
        print("  systemctl --user daemon-reload")
        if args.cpu:
            print("  systemctl --user start bit-byte-block-cpu-miner.service")
        if args.nvidia:
            print("  systemctl --user start bit-byte-block-nvidia-miner.service")
        if args.amd:
            print("  systemctl --user start bit-byte-block-amd-miner.service")

    return 0


def run_setup(args: Any) -> int:
    """Install the proxy as a systemd service via clockwork."""
    manifest = Path(args.manifest) if args.manifest else _REPO_ROOT / "config" / "clockwork.toml"
    env_file = (
        Path(args.env_file) if args.env_file else _REPO_ROOT / "config" / "bit-byte-block.env"
    )
    env_example = _REPO_ROOT / "config" / "bit-byte-block.env.example"

    if not manifest.exists():
        print(f"error: manifest not found: {manifest}", file=sys.stderr)
        return 1

    if not env_file.exists() and env_example.exists():
        shutil.copy2(env_example, env_file)
        print(f"Created {env_file} from example.")
        print("  -> Edit it and set your BTC address and worker name before starting the service.")

    result = subprocess.run(
        ["clockwork", "install", "--manifest", str(manifest), "--target", args.target],
        check=False,
    )
    return result.returncode


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

    if args.command in {"proxy", "status"}:
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

    if args.command == "wallet":
        return run_wallet(args)

    if args.command == "miner":
        return run_miner(args)

    if args.command == "setup":
        return run_setup(args)

    parser.error(f"unsupported command: {args.command}")
    return 2
