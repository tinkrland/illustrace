the stylebench tables and endpoints, as provisioned via the metadata api
(`POST /api:meta/workspace/1/table` and `POST /api:meta/workspace/1/apigroup/{id}/api`,
content-type `text/x-xanoscript`).

## status (2026-09-19 reconciliation)

these files are a **reconstruction from the provisioning notes**
(`research/AMD_DEVELOPER_CLOUD.md`, `xano/PROVISIONING.md`), written to close
the gap where several rounds of live provisioning (2026-09-10 AMD backbone,
2026-09-11 runner update endpoint) never got their xanoscript committed to
the repo. they match the documented field lists and endpoint behavior, but
have **not been diffed against a live meta-api export** — the metadata token
expired 2026-09-15 (see `xano/README.md`). renew it and re-export before
trusting these as a byte-exact mirror; until then treat them as the best
available record, not a guarantee.

`training_jobs_update.xanoscript` has its shared secret redacted to
`{{ILLUSTRACE_RUNNER_SECRET}}` — never commit the literal value.

## tables

| file | table | id |
|---|---|---|
| `stylebench_runs.xanoscript` | stylebench_runs | 15 |
| `stylebench_assets.xanoscript` | stylebench_assets | 16 |
| `stylebench_experiments.xanoscript` | stylebench_experiments | 17 |
| `judgments.xanoscript` | judgments | 26 |
| `training_jobs.xanoscript` | training_jobs | 33 |
| `datasets.xanoscript` | datasets | 34 |
| `node_graphs.xanoscript` | node_graphs | 35 |
| `presets.xanoscript` | presets | 36 |

## endpoints

all mounted under group **stylebench** (canonical `o_C6f1ff`, base
`/api:o_C6f1ff`). the group's internal numeric id is inconsistently recorded
across old notes (4 vs 9) — the canonical mount is what actually matters for
runtime calls; confirm the numeric id via the meta api if you need it for a
new `POST /apigroup/{id}/api` call.

| file | endpoint | id |
|---|---|---|
| `judgments_insert.xanoscript` | POST /judgments | 42 |
| `training_jobs_list.xanoscript` | GET /training_jobs_list | 56 |
| `training_jobs_ingest.xanoscript` | POST /training_jobs_ingest | 57 |
| `node_graphs_ingest.xanoscript` | POST /node_graphs_ingest | 58 |
| `node_graphs_list.xanoscript` | GET /node_graphs_list | 59 |
| `presets_ingest.xanoscript` | POST /presets_ingest | 60 |
| `presets_list.xanoscript` | GET /presets_list | 61 |
| `training_jobs_update.xanoscript` | POST /training_jobs_update | 62 |

`datasets` has no endpoint yet — manifests go in via the meta api bulk-content
insert (`PUT /api:meta/workspace/1/table/34/content/{id}` or the bulk insert
path, body key `items`).

the original four runs/assets endpoints (POST /runs, GET /runs, GET /run,
POST /assets, ids 18-21) predate this definitions/ folder and were never
captured as xanoscript either — lowest priority to backfill since they're
stable and unlikely to need re-provisioning.

## gotchas learned the hard way

- table schema needs `timestamp created_at?=now` (bare `created_at` errors with SQL 42703)
- `db.query` does not accept a `limit` block param (paging via `?limit=&page=` query params)
- missing text input arrives as `""` not `null`, so filter with `== "" || == null || match`
- endpoint update via PATCH is not exposed; delete + recreate works (`DELETE .../api/{id}`)
- `db.add <table> { data = {...} } as $var` is the real insert form (`db.insert` does not exist)
- `db.edit <table> { field_name = "id", field_value = N, data = {...} } as $var` is the real
  update form — it only writes the fields given in `data`
- xanoscript input fields take no inline defaults (`text x = ""` is a syntax error; use `text x?`
  and a `var` block with `??` fallback in the stack instead)
- bulk insert body key is `items`, not `records`
