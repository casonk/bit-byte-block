# SECURITY.md

## Operational Boundaries

- Do not commit real payout addresses, worker names, LAN topology, or hostnames
  tied to a private environment.
- Treat the Stratum proxy as a trusted-LAN or trusted-VPN service. The default
  `BIT_BYTE_BLOCK_BIND_HOST` / `bind_host` is `0.0.0.0`, so the proxy will
  listen on every reachable interface unless the operator narrows it.
- Do not expose the proxy directly to the public Internet. It accepts incoming
  miner connections and forwards work upstream, but it does not provide
  application-layer authentication, TLS termination, or per-client access
  controls on its own.
- If broader exposure is unavoidable, put the service behind explicit network
  controls such as WireGuard, a private VLAN, or host firewall rules, and
  prefer binding to a specific interface rather than every interface.
- Keep runtime overrides in gitignored local env files such as
  `config/bit-byte-block.env`.
- Treat connection logs and screenshots as potentially sensitive if they reveal
  wallet addresses or internal IP ranges.

## Reporting

Open a private maintainer channel for security-relevant issues rather than a
public issue when the report includes credentials, network details, or wallet
identifiers.
