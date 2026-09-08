# xano — stylebench control plane

queryable mirror of every run, asset, experiment, and human judgment. local json
in `results/runs/` stays the source of truth; xano is the read side (filter by
experiment, aggregate scores, export workspace snapshots).

## env vars

| var | purpose |
|-----|---------|
| `XANO_API_TOKEN` | bearer token for both the runtime api (`api:o_C6f1ff`) and the metadata api (`api:meta`). provisioned 2026-09-08, metadata token expires 2026-09-15 — renew from xano settings > metadata api. |

## endpoint map

### runtime api (live)

base: `https://xpnx-e4ie-cfuf.z7.xano.io/api:o_C6f1ff`

| method | path | function | status |
|--------|------|----------|--------|
| POST | `/runs` | `client.post_run(run)` | ✅ live |
| GET | `/runs?experiment=X` | `client.list_runs(experiment)` | ✅ live |
| GET | `/run?id=N` | `client.get_run(rid)` | ✅ live |
| POST | `/assets` | `client.post_asset(asset)` | ✅ live |

### metadata api (control-plane introspection)

base: `https://api.xano.com`

| method | path | function | status |
|--------|------|----------|--------|
| GET | `/api:meta/instance` | `client.list_instances()` | ✅ live |
| GET | `/api:meta/workspace` | `client.list_workspaces(instance_id)` | ✅ live |
| GET | `/api:meta/workspace/{id}/branch` | `client.list_branches(instance_id, workspace_id)` | ✅ live |
| GET | `/api:meta/workspace/{id}/export?branch=main` | `client.export_workspace(instance_id, workspace_id)` | ✅ live |

all metadata calls fail-soft — they return `None` or `[]` with a one-line print
on any network or auth failure, never raise.

## tables (pending xano provisioning)

the six control-plane tables below extend the three existing ones
(`stylebench_runs`, `stylebench_assets`, `stylebench_experiments`). they are
defined in `xano/schema.py` but **not yet provisioned** in the xano instance —
provisioning them requires re-running the metadata api create-table calls
(see `PROVISIONING.md` for the exact pattern).

| table | key fields | status |
|-------|-----------|--------|
| `projects` | id, name, description, created_at | ⏳ pending |
| `assets` | id, project_id, kind, name, file_url, style_profile (json) | ⏳ pending (extends existing) |
| `transfer_requests` | id, project_id, asset_id, components (json), strengths (json), status, created_at, completed_at | ⏳ pending |
| `experiments` | id, project_id, name, description, hypothesis, created_at | ⏳ pending (extends existing) |
| `runs` | id, experiment_id, subject, requested, params (json), metrics (json), verdict, artifacts (json), created_at | ✅ live (as `stylebench_runs`) |
| `human_judgments` | id, run_id, judge_id, dimension, score, notes, created_at | ⏳ pending |

## usage

### validate a record

```python
from xano.schema import validate

errors = validate("runs", my_record)
if errors:
    print("invalid:", errors)
```

### sync results/runs/ to xano

```sh
# validate + post everything
python -m xano.sync

# validate only (no network calls)
python -m xano.sync --dry-run

# custom directory
python -m xano.sync path/to/my/runs --dry-run
```

`sync_runs()` is also importable for programmatic use:

```python
from xano.sync import sync_runs

summary = sync_runs(dry_run=True)
print(summary)
# {"found": 6, "valid": 6, "invalid": 0, "synced": 0, "skipped_reasons": []}
```

### metadata api

```python
from xano import client

instances = client.list_instances()
workspaces = client.list_workspaces(instance_id="xpnx-e4ie-cfuf")
branches = client.list_branches("xpnx-e4ie-cfuf", workspace_id=1)
export = client.export_workspace("xpnx-e4ie-cfuf", workspace_id=1, branch="main")

# raw call
result = client.meta_call("GET", "/api:meta/workspace/1/table")
```

## module layout

```
xano/
  client.py        runtime api (post_run, post_asset, get_run, list_runs)
                   + metadata api (meta_call, list_instances, list_workspaces,
                                   list_branches, export_workspace)
  schema.py        dataclasses + validate() for all six tables
  sync.py          results/runs/ → xano harness; --dry-run mode
  PROVISIONING.md  how the instance and endpoints were provisioned
  definitions/     xanoscript payloads for tables and endpoints
  README.md        this file
```

## what is live vs pending

**live**: `stylebench_runs`, `stylebench_assets`, `stylebench_experiments` tables
and their four endpoints exist in workspace "anne's Workspace #1", branch v1.
`client.post_run`, `post_asset`, `get_run`, `list_runs` all work today.

**pending**: the five new tables (`projects`, `transfer_requests`,
`human_judgments`, and the extended `assets` / `experiments` with `project_id`)
need to be provisioned via the metadata api before the corresponding client
functions can write to them. the schema definitions and validation in
`schema.py` are ready; the xanoscript create-table calls are the only gap.
