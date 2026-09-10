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

---

# judgments provisioning — DONE (2026-09-10)

## what exists now (added)

table: **`judgments`** (id 26, workspace 1, branch v1) — human judgment records
from the style-survey app:

| field | type | notes |
|---|---|---|
| id, created_at | int, timestamp | auto |
| judge_id | text | judge identifier or "anonymous" |
| dimension | text | style dimension under test (roughness, texture, ...) |
| stimulus_a_id / stimulus_b_id | text | left / right stimulus filenames |
| chosen | text | chosen stimulus filename |
| confidence | text | self-reported confidence label |
| is_catch_pair | bool | identical-image catch trial (q04, q07) |
| noise_flag | bool | flagged inconsistent/noisy response |
| reaction_ms | int | reaction time |
| session_id | text | survey session identifier |
| question_id | text | survey question id (q01..) |
| raw | json | full original answer payload |

endpoint (group stylebench, id 42):
- `POST /api:o_C6f1ff/judgments` — insert a judgment record, returns it with id.
  created via the metadata api `POST /api:meta/workspace/1/apigroup/9/api` with
  `text/x-xanoscript` (real xanoscript: `query <name> verb=POST { input {...} stack { db.add <table> { data = {...} } as $record } response = $record }`).
  xanoscript syntax reference: docs.xano.com/xanoscript/function-reference/database-operations

synced: 12 pilot judgment records (session anonymous_1788981271664) via the
metadata bulk-content endpoint (`items` array, not `records`).

## pipeline

- `survey/index.html` — "send to stylebench" button posts each answer
  directly to the endpoint (local-first; downloads unchanged). cors on the
  group already allows any origin incl. `null` (file:// pages).
- `scripts/sync_judgments.py` — idempotent repo-side sync of any processed
  session not yet in the table (skips by session_id).
- `survey/ingest.py` still validates + scores locally; the ingest sweep
  workflow remains the local ledger of record. xano mirrors it.

## gotchas learned this round

- `api.xano.com` still does not resolve in the sandbox; the instance host
  `https://xpnx-e4ie-cfuf.z7.xano.io/api:meta/...` serves the full metadata
  api (spec at `/apispec:meta?type=json&token=<token>` — has *everything*:
  tables, bulk content, endpoint create via xanoscript, branches, releases).
- bulk insert body key is `items`, not `records`.
- xanoscript input fields take no inline defaults (`text judge_id = ""` is a
  syntax error; just `text judge_id`).
- `db.add <table> { data = { col: $input.x } } as $var` is the real insert
  form (`db.insert` does not exist).
