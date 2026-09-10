# llm tracing (langsmith, eu region)

every "research scientist" llm pass in illustrace gets a trace: the exact
prompt, model, tokens, latency, and output, stored permanently. the point
is a ledger — when a batch verdict looks weird in three months, the exact
run that drafted the spec or the critique is queryable, not folklore.

## setup

- api: https://eu.api.smith.langchain.com (eu region only — the us
  endpoint 403s this key)
- key: $LANGCHAIN_API_KEY (lsv2_pt_..., ~$100 credits, sep 2026)
- project: `illustrace` (all illustrace traces land here)
- sdk: langsmith 0.12.x, helper at `llm/trace.py`

## the helper

```python
from llm.trace import traced_chat, log_note

out = traced_chat(
    run_name,          # human-readable, e.g. "batch_4 critique pass"
    base_url,          # any openai-compatible endpoint (tensormux, nebius, featherless)
    api_key,           # that provider's key
    model,             # provider model id
    messages,          # openai-style chat messages
    extra={"batch": "batch_4"},   # free-form metadata, lands on the trace
)
log_note("some decision", "detail text")  # non-llm leaves: verdicts, decisions
```

traced_chat closes the run (status success, end_time) and records usage
+ finish_reason + latency. glm-4.7 caveat: it burns hidden reasoning
tokens, so max_tokens under ~1000 can return content null with
finish_reason length — keep the 8000 default.

## what gets traced (wiring plan)

- spec drafting + critique passes (the glm-5.2 workflow that validated
  batch_4) — adopted first
- intent-to-spec generation (survey/build_spec.py)
- judge-model passes once a judge model enters the loop
- log_note leaves for: batch promotions, preregistration decisions,
  failed probes (the fine-tuning 500s, endpoint quirks)

## querying

```python
import langsmith as ls
c = ls.Client(api_url="https://eu.api.smith.langchain.com")
runs = list(c.list_runs(project_name="illustrace", limit=50))
r = c.read_run(runs[0].id)   # full inputs/outputs/usage
```

(list_runs is deprecated in favor of client.runs.query() but works
through langsmith 0.12; the raw eu /api/v1/runs/query endpoint is picky
about filter shapes — use the sdk.)

## cost note

langsmith bills per-trace, not per-token. $100 is enormous runway for
illustrace's volume (tens of runs per batch). the token spend itself
still goes to the provider (tensormux/nebius), unchanged.
