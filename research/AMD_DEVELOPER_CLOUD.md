---
title: amd developer cloud — what we use it for
summary: the gpu compute plan for illustrace — factor-fitters first, lora hybrid in reserve, everything else is batch work. liat has hardware access credits (2026-09-10)
status: planning note
---

amd developer cloud is the project's gpu compute (mi300x, rocm stack —
standard pytorch-rocm + diffusers runs fine on it). liat has access
credits. what we actually use it for, in priority order:

## now: factor-fitters (the measurement layer)

- small regression models that map image crops → recipe params
  (true jitter sigma, taper profile, stroke width, palette zones)
- training data comes from the substrate itself: it renders images with
  *known* params, so it's an infinite synthetic data factory — sweep
  params, render crops, label = ground truth, no hand labeling ever
- this is what makes the node canvas magical: drop image 2 into the
  palette slot and the fit happens automatically, sliders start at the
  measured value instead of a guess
- hours on a single mi300x per fitter, not days

## now-ish: batch synthetic data + stimuli generation

- large substrate sweeps for stylebench stimuli (separability batches,
  dose-response curves, leakage probes) — thousands of renders per batch
- rerasterization of reference sets for evaluation runs
- embarrassingly parallel, cheap, no training involved

## in reserve: lora fine-tuning (the hybrid step)

- only if stylebench proves a factor genuinely exceeds recipe
  expressivity (the known candidate: watercolor washes, bucket-07)
- would fine-tune a diffusion model on style patches (kohya path,
  bitsandbytes rocm build) to generate the *texture recipe layer* while
  geometry stays vector and editable — a recipe layer, not the engine
- a 10-image lora is ~30 min on one mi300x; credits stretch far
- deliberately last: this is the exact lane we're not competing in
  (wholesale style cloning). it earns its place only as a bounded,
  per-factor texture tool

## not on amd (routing note)

- text-llm work (thinking passes, spec generation, judge models,
  fine-tuning them) stays on nebius/tensormux/featherless per the llm
  ladder — amd is for image/vision compute only
- xano stays the control plane, zero compute there

## when provisioning

- request: mi300x instances, rocm pytorch docker image
  (`rocm/pytorch` nightly or stable), diffusers/accelerate on top
- first job when live: fitter pilot — substrate sweep → crops → small
  cnn regressor → eval against held-out param values (see
  research/EDITABLE_BRUSH_ENGINE.md for the recipe param space)

## xano backbone (staged 2026-09-10)

the control plane for lora fine-tuning + the node ui is live. four tables
plus six endpoints, all verified with seeded records.

tables (workspace 1, stylebench group 9):

- `training_jobs` (33) — the job queue + ledger. job_type
  (fitter|lora|batch_render), status (queued|running|done|failed),
  target_factor, hardware, dataset_ref, params json, metrics json,
  artifact_uri, gpu_hours
- `datasets` (34) — substrate sweeps + reference uploads feeding training.
  name, source, manifest json, image_count
- `node_graphs` (35) — node-ui documents. graph json
  ({nodes:[{id,type,image|component|preset,...}], edges:[{from,to}]}),
  graph_version, status (draft|validated|superseded)
- `presets` (36) — saved recipes = style slots. recipe json
  (components, strengths, extraction settings), recipe_version, graph_id

endpoints (instance https://xpnx-e4ie-cfuf.z7.xano.io/api:o_C6f1ff, no auth
for now, add auth when the runner goes multi-user):

- `POST /training_jobs_ingest` (57) — queue a job
- `GET /training_jobs_list?status=queued` (56) — runner claims queued work
- `POST /training_jobs_update` (62) — runner flips status with a shared
  secret: claims queued -> running, posts results -> done/failed with
  metrics/params/artifact_uri/gpu_hours. wrong secret or invalid status
  returns ok:false and writes nothing. secret lives in the
  $ILLUSTRACE_RUNNER_SECRET env (runner + this workspace); the allowed
  transitions are running|done|failed, requeueing is meta-api-only by
  design so the ledger can't be rewound by the runner. verified
  end-to-end 2026-09-11, job 1 exercised and reset
- `POST /node_graphs_ingest` (58) / `GET /node_graphs_list` (59)
- `POST /presets_ingest` (60) / `GET /presets_list` (61)

job flow (pull model, amd box holds no state):

1. queue: research pass creates a training_jobs row via ingest (job 1 =
   the fitter pilot, already queued: jitter_lat, mi300x, small cnn)
2. claim: the amd runner polls training_jobs_list?status=queued, takes
   the lowest id, marks it running (update endpoint: todo below)
3. run: rocm box trains, posts metrics + artifact_uri back on completion
4. registry: metrics that pass a batch's preregistered criteria promote
   the factor into the style registry; the node ui reads node_graphs +
   presets so sliders snap to measured jnd steps (batch_4 registry rules)

node ui flow: the canvas saves graphs via node_graphs_ingest (each save =
new row, graph_version++, never mutated — old versions stay queryable),
users pin presets via presets_ingest referencing the graph_id they were
extracted from. fits live inside the graph json as component nodes, so
the measurement records and the ui document are one thing.

known gaps (next provisioning round):

- no auth on any endpoint — fine while single-user, must change before
  anything public (training_jobs_update has its shared secret; the rest
  are open)
- datasets table has no ingest endpoint yet; manifests go in via meta api
  bulk insert for now
