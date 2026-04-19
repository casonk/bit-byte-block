# AGENTS.md — bit-byte-block

## Purpose

`bit-byte-block` provides a local Bitcoin mining ingress service that proxies
Stratum TCP traffic from miners on the local network to an upstream solo mining
pool, with `solo.ckpool.org` configured as the default upstream.

The repository is intentionally narrow:

1. Accept local miner connections on a stable LAN endpoint.
2. Relay Stratum traffic upstream with minimal added logic.
3. Expose a lightweight CLI to inspect upstream pool status.

It does not ship ASIC firmware, wallet management, or hosted pool software.

## Repository Layout

```text
bit-byte-block/
├── pyproject.toml                     # Package metadata and tooling config
├── src/bit_byte_block/
│   ├── __init__.py                    # Version export
│   ├── __main__.py                    # python -m entry point
│   ├── cli.py                         # CLI: proxy / status / setup
│   ├── config.py                      # Env-file loading and runtime config
│   ├── proxy.py                       # Asyncio Stratum TCP proxy
│   └── monitor.py                     # solo.ckpool.org pool-status fetcher
├── tests/
│   ├── test_config.py                 # Env-file parsing tests
│   ├── test_monitor.py                # Pool status parsing tests
│   └── test_proxy.py                  # Local relay and failover tests
├── config/
│   ├── bit-byte-block.env.example     # Example runtime configuration
│   ├── clockwork.toml                 # Clockwork manifest for the proxy systemd service
│   └── downstream-repos.toml          # Known downstream consumers
├── scripts/
│   ├── run_proxy.sh                   # Local service wrapper (direct launch)
│   └── setup.sh                       # Device setup wrapper (calls `bit-byte-block setup`)
└── docs/
    ├── contributor-architecture-blueprint.md
    └── diagrams/
        ├── repo-architecture.puml
        └── repo-architecture.drawio
```

## Quick Start

```bash
python3 -m pip install -e ".[dev]"

# One-time device setup: installs the proxy as a user systemd service via clockwork
bash scripts/setup.sh

# Edit the generated env file with your BTC address and worker name, then:
systemctl --user daemon-reload
systemctl --user enable --now bit-byte-block-proxy.service

# Ad-hoc commands
bash scripts/run_proxy.sh          # run proxy directly (no systemd)
python3 -m bit_byte_block status   # check upstream pool status
```

Point ASIC miners at the host running `bit-byte-block`, not directly at
`solo.ckpool.org`, and keep the miner-side username in the upstream-required
format: `BTC_ADDRESS.worker`.

## Operating Rules

1. Keep the proxy transparent by default. Do not silently rewrite miner
   credentials or mutate Stratum payloads unless the task explicitly calls for
   protocol-aware behavior.
2. Keep runtime dependencies minimal. The current service is stdlib-only; do not
   add third-party runtime dependencies without a concrete operational need.
3. Treat payout addresses, worker names, and local network topology as
   operationally sensitive. Keep real values in gitignored local env files.
4. When upstream host, port, or status endpoints change, update `README.md`,
   `config/bit-byte-block.env.example`, and `REFS-PUBLIC.md` in the same change.
5. If the service model expands beyond a simple always-on proxy, prefer using
   shared utilities from `clockwork`, `tachometer`, `wiring-harness`, and
   `short-circuit` instead of cloning infra logic locally.

## Testing Expectations

The tests are offline and use local loopback sockets or mocked HTTP responses.

```bash
python3 -m pip install -e ".[dev]"
pytest -q
```

Pre-commit validation:

```bash
pre-commit run --all-files
```

## Local CI Verification

Run before every push:

```bash
pre-commit run --all-files
pytest -q
```

Do not push changes that have not passed all checks locally.

## Portfolio Standards Reference

For portfolio-wide repository standards and baseline conventions, consult the
control-plane repo at `./util-repos/traction-control` from the portfolio root.

Start with:
- `./util-repos/traction-control/AGENTS.md`
- `./util-repos/traction-control/README.md`
- `./util-repos/traction-control/LESSONSLEARNED.md`

Shared implementation repos available portfolio-wide:
- `./util-repos/archility` for architecture toolchain bootstrap/render
  orchestration, Graphviz-capable diagram support, deterministic starter
  scaffolding, agentic architecture authoring, and drift checks
- `./util-repos/auto-pass` for KeePassXC-backed password management and secret
  retrieval/update flows
- `./util-repos/clockwork` for declarative cron and systemd scheduler manifest
  rendering and install helpers
- `./util-repos/tachometer` for manifest-driven local profiling snapshot, run,
  and summarize workflows
- `./util-repos/nordility` for NordVPN-based VPN switching and connection
  orchestration
- `./util-repos/shock-relay` for external messaging across Signal, Telegram,
  Twilio SMS, WhatsApp, and Gmail IMAP
- `./util-repos/short-circuit` for WireGuard VPN setup and configuration
- `./util-repos/snowbridge` for SMB-based private file sharing and
  phone-accessible fileshare workflows
- `./util-repos/dyno-lab` for unified test bench utilities
- `./util-repos/crew-chief` for local LLM inference via a Podman-hosted Ollama
  service
- `./util-repos/wiring-harness` for shared Caddy, mTLS, and DNS infrastructure

## Agent Memory

Use `./LESSONSLEARNED.md` as the tracked durable lessons file for this repo.
Use `./CHATHISTORY.md` as the standard local handoff file for this repo.

- `LESSONSLEARNED.md` is tracked and should capture only reusable lessons.
- `CHATHISTORY.md` is local-only, gitignored, and should capture transient
  handoff context.
- Read `LESSONSLEARNED.md` and `CHATHISTORY.md` after `AGENTS.md` when resuming
  work.
- Add durable lessons to `LESSONSLEARNED.md` when they should influence future
  sessions.
