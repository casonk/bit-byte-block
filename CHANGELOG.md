# CHANGELOG.md

## Unreleased

## 0.1.1

- Fixed the proxy disconnecting every miner every two minutes: the idle
  timeout was applied to each direction separately, and a miner sends nothing
  between shares (days apart for a small miner) while the pool keeps sending
  work. The timeout now applies to the whole session, so a connection closes
  only when neither side has sent anything for `idle_timeout` seconds.
- Fixed `bit-byte-block status` failing with "expected 3 JSON objects in pool
  status payload, found 5": solo.ckpool.org now appends client-count and
  Stratum V2 job-declaration sections. The first three sections are still
  required; later ones are kept under `extra`.
- Fixed the proxy logging an "Unhandled exception" traceback whenever a miner
  or the pool reset the connection; a dropped connection now ends that relay
  with one log line.
- Declared the `cryptography` dependency of `wallet generate` as the `wallet`
  extra (and `Recommends: python3-cryptography` in the RPM); without it the
  command now explains what to install instead of failing with a traceback.
- Added RPM packaging in `packaging/`: a noarch spec built from the release
  tarball, a hardened systemd service (`DynamicUser`, read-only filesystem,
  not enabled by default), settings in `/etc/bit-byte-block`, and a firewalld
  service for the proxy port. A test keeps the spec version, service, and port
  in step with the Python package.
- Added `bootstrap.sh`, which creates a virtualenv, installs the package in
  editable mode, verifies the `bit-byte-block` command runs, and seeds
  `config/bit-byte-block.env` from the example without overwriting an existing
  one. The Quick Start previously opened with a bare
  `python3 -m pip install -e ".[dev]"`, which PEP 668 causes current Debian,
  Ubuntu, Arch and openSUSE to refuse outright.
- Added the initial `bit-byte-block` repository baseline.
- Added a stdlib-only asyncio Stratum proxy with optional backup upstream.
- Added a CLI command for `solo.ckpool.org` pool status inspection.
