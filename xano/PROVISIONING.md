# xano provisioning — DONE (2026-09-08)

instance: https://xpnx-e4ie-cfuf.z7.xano.io
token: $XANO_API_TOKEN (xano metadata api key, aud xano:meta, expires 2026-09-15)

provisioned programmatically via the metadata api (`/api:meta/...`). no ui click-through
needed after all — this file is now a record of what exists, not a todo.

## what exists

api group: **stylebench** (id 4, canonical `o_C6f1ff`, mounted at `/api:o_C6f1ff`)

tables (in workspace "anne's Workspace #1", branch v1):
- `stylebench_runs` (id 15): experiment, subject, requested, params (json), metrics (json),
  verdict, artifacts (json), created_at
- `stylebench_assets` (id 16): kind, name, file_url, style_profile (json), created_at
- `stylebench_experiments` (id 17): name, hypothesis, pass_criteria (json), created_at

endpoints (group stylebench):
- `POST /api:o_C6f1ff/runs` — insert a run record, returns it with id
- `GET  /api:o_C6f1ff/runs?experiment=X` — list runs (newest first; empty filter = all)
- `GET  /api:o_C6f1ff/run?id=N` — single run
- `POST /api:o_C6f1ff/assets` — insert an asset record

existing tables from anne's other projects (user, event_log, design_jobs, substrate_*) were
left untouched.

## how it was done

metadata api conventions used (see definitions/README.md for gotchas):
- `POST /api:meta/workspace/1/apigroup` (json) — create group
- `POST /api:meta/workspace/1/table` (text/x-xanoscript) — create table
- `POST /api:meta/workspace/1/apigroup/4/api` (text/x-xanoscript) — create endpoint
- `DELETE /api:meta/workspace/1/apigroup/4/api/{id}` — delete endpoint (no PATCH exists)
- group base url = `/api:<canonical>` (from the group record / apispec link)

the exact xanoscript payloads and the pitfalls (created_at?=now, no db.query limit block,
missing text input = "" not null) are in `definitions/README.md`.

## client

`xano/client.py` posts runs + assets; `benchmarks/run_bench.py` mirrors every run
automatically. local json in results/runs/ stays the source of truth; xano is the
queryable control plane (GET /runs?experiment=measurability_v0 etc).

note: metadata key expires 2026-09-15 — renew from settings > metadata api when it does;
the *runtime* endpoints (api:o_C6f1ff) are public and don't need it.
