# xano — stylebench control plane

queryable mirror of every run, asset, experiment, human judgment, training
job, node graph, and preset. local json in `results/runs/` stays the source
of truth; xano is the read side (filter by experiment, aggregate scores,
export workspace snapshots) plus the write side for the survey app and the
amd runner.

## env vars

| var | purpose |
|-----|---------|
| `XANO_API_TOKEN` | token for the metadata api (`api:meta`) and bulk-content calls. the *runtime* endpoints (`api:o_C6f1ff`) are public and need no auth. metadata tokens expire (~2 weeks); renew from xano settings > metadata api. |
| `ILLUSTRACE_RUNNER_SECRET` | shared secret for `POST /training_jobs_update` (runner-only status transitions). lives in the runner env + this workspace; never in the repo. |

## bases

| surface | base |
|---------|------|
| runtime api | `https://xpnx-e4ie-cfuf.z7.xano.io/api:o_C6f1ff` |
| metadata api | `https://xpnx-e4ie-cfuf.z7.xano.io/api:meta` |

note: `api.xano.com` does NOT resolve in the sandbox — always use the instance
host for metadata calls too (this bit us: `client.py` pointed at the wrong host
and every metadata call silently fail-softed to `None`).

## endpoint map (live)

### stylebench runs/assets (provisioned 2026-09-08)

| method | path | function | status |
|--------|------|----------|--------|
| POST | `/runs` | `client.post_run(run)` | ✅ live |
| GET | `/runs?experiment=X` | `client.list_runs(experiment)` | ✅ live |
| GET | `/run?id=N` | `client.get_run(rid)` | ✅ live |
| POST | `/assets` | `client.post_asset(asset)` | ✅ live |

### judgments (provisioned 2026-09-10)

| method | path | status |
|--------|------|--------|
| POST | `/judgments` | ✅ live — the survey app posts each answer directly (cors allows any origin incl. `null` for `file://` pages); 12 pilot records synced |

### amd backbone (provisioned 2026-09-10/11) — see [research/AMD_DEVELOPER_CLOUD.md](../research/AMD_DEVELOPER_CLOUD.md)

| method | path | purpose | status |
|--------|------|---------|--------|
| POST | `/training_jobs_ingest` | queue a job (fitter/lora/batch_render) | ✅ live (id 57) |
| GET | `/training_jobs_list?status=queued` | runner claims queued work | ✅ live (id 56) |
| POST | `/training_jobs_update` | runner flips status (shared secret; ledger non-rewindable by design) | ✅ live (id 62), verified end-to-end 2026-09-11 |
| POST | `/node_graphs_ingest` / GET `/node_graphs_list` | composer canvas save/list | ✅ live (ids 58/59) |
| POST | `/presets_ingest` / GET `/presets_list` | pin/list saved recipes | ✅ live (ids 60/61) |

## tables (all live — ids from the provisioning notes)

| table | id | provisioned | feeds |
|-------|----|-------------|-------|
| `stylebench_runs` | 15 | 2026-09-08 | run mirroring (`xano/sync.py`) |
| `stylebench_assets` | 16 | 2026-09-08 | asset mirroring |
| `stylebench_experiments` | 17 | 2026-09-08 | experiment registry |
| `judgments` | 26 | 2026-09-10 | survey app + `scripts/sync_judgments.py` |
| `training_jobs` | 33 | 2026-09-10 | amd runner queue + ledger |
| `datasets` | 34 | 2026-09-10 | substrate sweeps / reference uploads (no ingest endpoint yet — meta-api bulk insert only) |
| `node_graphs` | 35 | 2026-09-10 | composer canvas saves (append-only, graph_version++) |
| `presets` | 36 | 2026-09-10 | saved recipes referencing graph_id |

the table and endpoint definitions live in [definitions/](definitions/) as
xanoscript (the amd round was reconstructed 2026-09-19 from the provisioning
notes — see definitions/README.md for the fidelity caveat and the expired
metadata-token situation).

## usage

### validate a record

```python
from xano.schema import validate

errors = validate("stylebench_runs", my_record)
if errors:
    print("invalid:", errors)
```

### sync results/runs/ to xano

```sh
python -m xano.sync             # validate + post everything
python -m xano.sync --dry-run   # validate only (no network calls)
```

`sync_runs()` is also importable for programmatic use.

### metadata api

```python
from xano import client

client.list_instances()
client.list_workspaces("xpnx-e4ie-cfuf")
client.list_branches("xpnx-e4ie-cfuf", workspace_id=1)
client.export_workspace("xpnx-e4ie-cfuf", workspace_id=1, branch="main")
client.meta_call("GET", "/api:meta/workspace/1/table")
```

## module layout

```
xano/
  client.py        runtime api (post_run, post_asset, get_run, list_runs)
                   + metadata api (meta_call, list_instances, list_workspaces,
                                   list_branches, export_workspace)
  schema.py        dataclasses + validate() for the eight live tables
  sync.py          results/runs/ -> xano harness; --dry-run mode
  PROVISIONING.md  provisioning history: what exists, how, and the gotchas
  definitions/     xanoscript payloads for tables and endpoints (+ fidelity notes)
  README.md        this file
```

## known gaps (next provisioning round)

- no auth on any endpoint except `training_jobs_update` — fine while
  single-user, must change before anything public.
- `datasets` has no ingest endpoint; manifests go in via the meta api bulk
  insert (body key `items`).
- the original runs/assets endpoints (ids 18-21) were never captured as
  xanoscript in `definitions/` — low priority (stable, unlikely to change).
- metadata token expires ~every two weeks; renew before any provisioning or
  reconciliation work.
