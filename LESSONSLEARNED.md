# LESSONSLEARNED.md

Tracked durable lessons for `bit-byte-block`.
Unlike `CHATHISTORY.md`, this file should keep only reusable lessons that should
change how future sessions work in this repo.

## How To Use

- Read this file after `AGENTS.md` and before `CHATHISTORY.md` when resuming
  work.
- Add lessons that generalize beyond a single session.
- Keep entries concise and action-oriented.
- Do not use this file for transient status updates or full session logs.

## Lessons

- Keep the proxy transparent until there is a concrete need to parse or rewrite
  Stratum messages; transparent relays are easier to reason about and test.
- Keep upstream pool connection details in one place so the README, example env
  file, and status client stay aligned when pool settings change.
- Re-run repo-appropriate validation after changing runtime or CI-facing files
  so formatting and compatibility issues are caught before push.
