# CHANGELOG.md

## Unreleased

- Added `bootstrap.sh`, which creates a virtualenv, installs the package in
  editable mode, verifies the `bit-byte-block` command runs, and seeds
  `config/bit-byte-block.env` from the example without overwriting an existing
  one. The Quick Start previously opened with a bare
  `python3 -m pip install -e ".[dev]"`, which PEP 668 causes current Debian,
  Ubuntu, Arch and openSUSE to refuse outright.
- Added the initial `bit-byte-block` repository baseline.
- Added a stdlib-only asyncio Stratum proxy with optional backup upstream.
- Added a CLI command for `solo.ckpool.org` pool status inspection.
