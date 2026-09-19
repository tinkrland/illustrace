---
title: llm layer
summary: the semantic compiler (intent in, validated parameters out), the eval ledger on langsmith, and the spec/judge fine-tune path, what exists vs what's roadmap
---

# llm, the semantic compiler layer

root readme says the problem: existing tools treat style as one undifferentiated
blob scored by a mystery knob ("style strength: 70%"), which makes style transfer
a slot machine, heavy reference-content leakage, prompt bleeding, no per-factor
control. the llm layer is the other half of the fix: **qualitative artist intent
is the input format**, and the llm's whole job is compiling it into the explicit
factor coordinates the deterministic engine ([stylebench](../engine/)) can
measure and move.

the llm never generates images and never freestyles. it is a **semantic
compiler**: intent in, schema-valid parameters out, validator-enforced, human-
approved. surprise is a bug, so every output passes through a local validator
before it touches anything downstream, an llm that hallucinates a parameter
name fails validation the same way a bad csv does.

## what exists (built, tested)

- **intent-to-spec compiler**, [survey/build_spec.py](../survey/build_spec.py):
  plain-language style hypothesis in ("bracket the jnd for taper"), draft
  preregistration spec out. one glm-5.2 pass, assembled from spec schema +
  batch exemplars + the live stimulus inventory + pilot learnings; the local
  validator enforces every structural rule `build_batch.py` assumes; drafts
  land in `survey/specs/drafts/` and are never auto-promoted.
- **eval ledger**, [trace.py](trace.py): every llm pass (spec drafts,
  critiques, judge passes) traced to langsmith (eu region, project
  `illustrace`): exact prompt, model, tokens, latency. when a batch verdict
  looks weird in three months, the run that produced it is queryable, not
  folklore. see [research/LLM_TRACING.md](../research/LLM_TRACING.md).
- **trace export**, [export_traces.py](export_traces.py): langsmith access is
  temporary, the corpus is not. every traced run becomes an openai-format
  fine-tune pair in `data/generated/ft/`.
- **qlora runner**, [lora_train.py](lora_train.py): trains the spec-draft
  model (first target) and the judge model (second) from exported pairs,
  on either backend: `local` (mi300x, rocm pytorch + peft, 4-bit nf4,
  r=64) or `nebius` (tokenfactory post-training, verified live 2026-09-19;
  no gpu needed, so the text models don't wait on amd. image-style loras
  do, tokenfactory fine-tuning is text-only).

model ladder (liat's external credits, cheapest-first): tensormux glm-4.7 for
cheap passes, nebius glm-5.2 for thinking passes, featherless for open-source
passes, backboard only when a frontier pass is genuinely needed. langsmith only
observes the calls.

## the roadmap half (framed honestly)

the full semantic-compiler vision: the llm reads intent and **dynamically
adapts the runtime**, cross-attention masks, ip-adapter configurations, lora
adapter weights, inside open-weight models, so "rougher linework, keep the
palette" becomes live slider positions instead of a prompt. today only the
compile-to-spec step exists; the runtime adaptation is design work in
[research/STYLE_LORA_ENGINE.md](../research/STYLE_LORA_ENGINE.md) and
[research/NODE_UI_RESEARCH.md](../research/NODE_UI_RESEARCH.md): diffusers
`set_adapters` + `adapter_weights` (sub-millisecond, so sliders are live),
masking nodes preferred over raw stacking because adapter interference grows
past 2–3 simultaneous loras.

## open weights, not apis

factor isolation needs deep access to the latent space, so the adapter layer
targets open weights:

- **current stack:** flux.1 [dev] via kohya sd-scripts on the mi300x box:
  the packaging spec is [research/DATASET_PACKAGING.md](../research/DATASET_PACKAGING.md)
  and the composition rules live in the lora engine doc.
- **candidate sweep for the next round:** flux.2 [dev] (32b, open-weight,
  non-commercial), flux.2 [klein] (4b/9b, the 4b is apache 2.0), stable
  diffusion 3.5 large/medium as a second transformer backbone. nothing
  decided until the first adapter loop closes on flux.1 and the probe harness
  can actually score the alternatives.
- **micro-datasets on purpose:** 6–10 reference images per inspo is the design
  (36-work painter corpora in practice), because each adapter's contract is
  bounded by [probe deltas](../engine/adapter_probe.py), not by training
  volume.

the amd asterisk: training is blocked on amd developer cloud access; everything
upstream of the gpu (ingestion, probing, the spec compiler, the queue in xano
`training_jobs`) is built and waiting.

## inspos

- **recraft**, style sets and brand styles as first-class, pickable objects:
  style-as-a-preset-that-combines, not style-as-a-prompt.
- **exactly.ai**, the editable-preset principle (outputs stay adjustable,
  never a flattened render); the application vision in
  [application/README.md](../application/README.md) mirrors its live parameter
  sliders.
- **scenario.com**, game-asset loras trained per art style on small curated
  sets, proof that micro-dataset style adapters work in production.

none of them decompose style into measured, independently-transferable factors
or validate against human judgment, that's the illustrace thesis, not a
feature borrowed from any of them.

## module map

```
llm/
  trace.py           traced_chat / log_note, langsmith (eu) eval ledger
  export_traces.py   traces -> openai-format fine-tune jsonl
  lora_train.py      lora_train.py      fine-tune runner: --backend local (mi300x qlora) or
                     --backend nebius (tokenfactory post-training)
survey/build_spec.py the intent-to-spec compiler itself (lives with its
                     validator's consumers in survey/)
```

## where it breaks (honest)

- **the compiler has one validated output type.** specs for judgment batches.
  intent → node-graph recipes is the obvious next step; not built.
- **no runtime adaptation yet.** the compiler produces specs; the runtime
  (masks, adapter weights) is research docs.
- **the fine-tune corpus is small.** every build_spec.py run adds a pair, but
  "under 50 examples is smoke, thin for a real lora" per lora_train.py. the
  nebius backend works and is wired in, but there's nothing worth training
  yet.
- **langsmith access is time-boxed.** that's why export_traces.py exists;
  the corpus survives the window.
