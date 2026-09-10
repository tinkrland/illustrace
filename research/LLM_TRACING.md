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

## the corpus outlives the access window

langsmith access is temporary; the training corpus is not. two scripts
close that loop:

- `llm/export_traces.py` — pulls every llm run from the project into
  `data/generated/ft/`: a raw jsonl (full pairs + usage) and an
  openai-format `spec_drafts.openai.jsonl` ready for fine-tuning upload.
  run it periodically; each export is a snapshot.
- `llm/lora_train.py` — the qlora runner for the mi300x box (rocm pytorch
  + peft, 4-bit nf4 base, r=64 on attention projections). `--dry-run`
  validates the dataset anywhere; the full path loads the model only on
  the box. default base: llama-3.3-70b (in the nebius catalog, so the
  adapter can serve there once their fine_tuning/jobs backend stops
  500ing, or locally on featherless-adjacent inference).

fine-tune targets, in order:

1. spec drafts — glm-5.2 trace pairs (hypothesis + context -> preregistered
   spec) teach a model the house style; every build_spec.py run adds a
   training pair automatically now.
2. judge model (later) — human 2afc judgments from the xano `judgments`
   table become the corpus; an exporter gets written when judgment volume
   justifies it.

xano integration: training_jobs (table 33) takes job_type="lora" — queue a
job, the amd runner pulls it, trains from the exported jsonl, posts
metrics + adapter uri back.
