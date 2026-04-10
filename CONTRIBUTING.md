# CONTRIBUTING.md

## Workflow

1. Read `AGENTS.md`, `LESSONSLEARNED.md`, and local `CHATHISTORY.md` before
   resuming work.
2. Keep changes additive and update docs when behavior changes.
3. Run the local CI gate before pushing:

```bash
pre-commit run --all-files
pytest -q
```

## Development Setup

```bash
python3 -m pip install -e ".[dev]"
cp config/bit-byte-block.env.example config/bit-byte-block.env
```

## Change Expectations

- Keep the proxy transparent unless the task explicitly requires protocol-aware
  mutation.
- Keep runtime dependencies stdlib-only where practical.
- Update `REFS-PUBLIC.md` when public upstream documentation changes.
