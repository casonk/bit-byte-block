# BACKLOG.md

Portfolio backlog for this repository. Pending items are candidates for
execution - manually or via crew-chief. Entries sourced from archility audit are
tagged `[archility:YYYY-MM-DD]`; manual entries use `[manual:YYYY-MM-DD]`.

The archility weekly job populates this file automatically via
`archility audit --write-backlog`. To execute a backlog item with crew-chief:
`crew-chief agent "Work on item: <item text>"`. Mark items `[x]` when complete
and move them to Done.

## Pending

- [ ] [manual:2026-11-15] **Investigate running the Stratum proxy in K3s (kind `service`).** Read-only first. The
  security gain is pinning the pod's outbound traffic to the one mining pool (an FQDN allow-list; today nothing limits
  where the proxy may connect). Open questions: miners connect to the host's LAN address on 3333 and 4334, so the
  bridge must listen on the LAN rather than loopback (a socket-activated `systemd-socket-proxyd` to the pod's fixed
  ClusterIP works, but check how miners behave when the forwarder or pod restarts: they should reconnect without
  losing shares or being flagged by the pool); upstream failover and the pool-status inspection need DNS and the pool's
  hosts; and what metrics or logs the host currently provides. Scaffold with traction-control's
  `scaffold_deployment_modes.py --kind service`; do not cut over while miners are mid-round.
- [ ] [manual:2026-10-15] **Ask GitHub Support to purge pre-rewrite commits** — this
  repository's published history was rewritten (most recently on 2026-10-15,
  to remove per-commit AI attribution trailers). GitHub keeps serving the old
  commits to anyone with a hash, and through the read-only `refs/pull/*` refs
  of earlier pull requests, until Support garbage-collects them. The request
  is filed once for the whole portfolio from traction-control's backlog; mark
  this done when an old hash returns 404 here. Never push an old clone's
  history back.

- [manual:2026-04-09] Add a systemd unit template or wiring-harness integration
  once the runtime host and LAN exposure model are finalized.
- [manual:2026-04-09] Decide whether the proxy should remain transparent or grow
  protocol-aware credential rewriting and richer miner telemetry.

## In Progress

## Done

- [x] [manual:2026-04-09] Seed the repository baseline, asyncio proxy, and
  solo.ckpool.org status client.
