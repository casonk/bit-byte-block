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

## AI Contribution Disclosure

Parts of this repository's code, documentation and commit history were drafted
with AI coding assistants, including Claude Code, OpenAI Codex, GitHub Copilot
and Continue. The maintainer directs that work, reviews and tests each change
before it merges, and is responsible for the result.

This section is the repository-wide disclosure. Individual commits, pull
requests and files do not carry per-tool attribution lines.
