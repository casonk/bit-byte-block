# Contributor Architecture Blueprint

## Runtime Flow

1. Local miners connect to the asyncio proxy on the LAN.
2. The proxy opens a matching TCP session to Solo CKPool.
3. Bytes are relayed bidirectionally without protocol mutation.
4. If the primary upstream is unavailable, the proxy can fail over to a backup
   upstream for new connections.
5. Operators can query the public pool-status endpoint with the CLI.

## Primary Components

- `src/bit_byte_block/config.py` resolves runtime settings from environment
  variables and optional env files.
- `src/bit_byte_block/proxy.py` accepts local connections and relays them
  upstream with bounded timeouts.
- `src/bit_byte_block/monitor.py` parses the public pool-status response.
- `scripts/run_proxy.sh` provides a shell-friendly service wrapper.

## Boundaries

- Local miner credentials remain on the miners themselves; the proxy is
  intentionally transparent.
- The repository does not operate a mining pool or perform proof-of-work
  locally.
- Public upstream defaults are documented in `README.md` and `REFS-PUBLIC.md`;
  private deployment details stay in local env files.
