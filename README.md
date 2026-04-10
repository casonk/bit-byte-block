# bit-byte-block

Local Bitcoin mining ingress and monitoring for `solo.ckpool.org`.

`bit-byte-block` runs a lightweight Stratum TCP proxy on your local network so
ASIC miners can point at one stable LAN endpoint while the proxy forwards their
traffic upstream to Solo CKPool. The initial scope is intentionally small:
transport relay, upstream failover, and pool-status inspection.

## Why This Repo Exists

- Keep miner configuration pointed at one local host instead of hard-coding the
  public pool hostname into every device.
- Centralize upstream defaults for Solo CKPool.
- Provide a small place to grow local operational tooling without bundling pool
  software or ASIC-specific firmware.

## Upstream Defaults

Solo CKPool documents these defaults on the public pool homepage:

- Primary host: `solo.ckpool.org`
- Standard port: `3333`
- High-difficulty rentals port: `4334`
- Username format: `BTC_ADDRESS.worker`
- Password: ignored by the pool

Regional notes from the same upstream:

- Europe and Africa: `eusolo.ckpool.org`
- Oceania: `ausolo.ckpool.org`
- IPv4-only: `solo4.ckpool.org`
- IPv6-only: `solo6.ckpool.org`

## Quick Start

```bash
python3 -m pip install -e ".[dev]"
cp config/bit-byte-block.env.example config/bit-byte-block.env
bash scripts/run_proxy.sh
```

The wrapper script loads `config/bit-byte-block.env` if present, then starts the
proxy. Point miners at the host running this repo, for example:

- Pool host: `192.168.1.50`
- Pool port: `3333`
- Username: `YOUR_BTC_ADDRESS.s19-01`
- Password: `x`

## CLI

```bash
# Start the local proxy with env-file defaults
python3 -m bit_byte_block proxy --env-file config/bit-byte-block.env

# Show the upstream pool-status snapshot
python3 -m bit_byte_block status --env-file config/bit-byte-block.env
```

The status command fetches the public status document exposed by the upstream
pool and prints a compact summary of connected workers, hashrate windows, share
counts, and best share.

## Local Validation

```bash
pre-commit run --all-files
pytest -q
```

## Contributing

See `CONTRIBUTING.md`.

## License

MIT. See `LICENSE`.
