the stylebench tables and endpoints, as provisioned via the metadata api
(post /api:meta/workspace/1/table and /api:meta/workspace/1/apigroup/4/api,
content-type text/x-xanoscript). rerunnable as-is.

tables (ids 15-17): stylebench_runs, stylebench_assets, stylebench_experiments
endpoints (ids 18-21): POST /runs, POST /assets, GET /run?id=, GET /runs?experiment=
group: stylebench, canonical o_C6f1ff, mounted at /api:o_C6f1ff

gotchas learned the hard way:
- table schema needs `timestamp created_at?=now` (bare created_at errors with SQL 42703)
- db.query does not accept a `limit` block param (paging via ?limit=&page= query params)
- missing text input arrives as "" not null, so filter with `== "" || == null || match`
- endpoint update via PATCH is not exposed; delete + recreate works (DELETE .../api/{id})
