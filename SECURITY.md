# SECURITY.md

## Operational Boundaries

- Do not commit real payout addresses, worker names, LAN topology, or hostnames
  tied to a private environment.
- Keep runtime overrides in gitignored local env files such as
  `config/bit-byte-block.env`.
- Treat connection logs and screenshots as potentially sensitive if they reveal
  wallet addresses or internal IP ranges.

## Reporting

Open a private maintainer channel for security-relevant issues rather than a
public issue when the report includes credentials, network details, or wallet
identifiers.
