---
title: fitter experiment specs (amd mi300x runner)
summary: the experiment ladder for factor-fitters, the inverse models that map image crops to recipe params. every run is preregistered on xano, every gate is written before the run. fx1 is queued as training job 1
status: spec (draft 2, glm-5.2 critique folded in 2026-09-11)
---

# fitter experiments: from sliders-as-guesses to sliders-as-measurements

the pitch (research/AMD_DEVELOPER_CLOUD.md): drop an image into a
component slot and the fit happens — sliders start at the measured value.
the fitter is a learned inverse of the substrate: the substrate renders
recipe params theta -> image, the fitter learns image -> theta-hat.
everything below is the experiment ladder that earns (or kills) that
pitch, one falsifiable run at a time.

the data factory is the whole trick: the substrate renders with *known*
theta, so training data is infinite and free of hand labels. but an
inverse learned on synthetic substrate renders only counts if it
transfers to real images — the ladder ends at that test (fx3), and the
probe harness built for the lora work is the measuring instrument.

## the ladder (each gate written before its run)

### fx0 — substrate measurability (no gpu)

sweep theta over the v0 recipe params (jitter sigma, taper profile,
stroke width, palette zone weights), render crops, and check that
`engine/inspo_profile.py` metrics track each knob **monotonically**
across the sweep: jitter sigma vs stroke_width_cv, width vs
width_mean, taper vs boundary shape stats.

- gate: every param has at least one existing metric with monotone
  relation (spearman >= 0.9 across >= 7 sweep steps).
- second-chance clause (preregistered, not post-hoc): a knob that fails
  spearman gets exactly one inspection — if the relation is non-monotone
  (u-shaped, phase change below pixel sampling rate), one engineered
  metric variant (variance instead of mean, etc.) is registered and
  retested before any kill.
- kill condition: a knob the measurement layer can't see can't be
  fitted — the fitter would learn to see it, but then fx3 round-trip
  has no instrument. fix the substrate or the metric first.

### fx1 — jitter pilot (queued: training_jobs id 1)

the first real run. two arms, same data:

- **arm a (control)**: ridge regression on the handcrafted profile
  features (inspo_profile outputs only). this is the "it's just
  measurement" baseline.
- **arm b (treatment)**: small cnn (<= 2m params) on raw 256px crops.

data: 5k crops from a jitter-sigma sweep (+ width co-varying to prevent
the fitter latching onto width as a jitter proxy), 80/10/10 split by
sweep value so no theta value spans train and test. the split must be
**interpolative only** — hold out interior sweep values, never the range
extremes; extrapolation is a different experiment and would fail both
arms for reasons that have nothing to do with the hypothesis. crops are
pre-rendered to disk (nvme) and fed by a dataloader (workers 16+); the
substrate render, not the gpu, is the bottleneck.

- metrics: MAE per param normalized by sweep range; r2 per param.
- gate: arm b beats arm a on normalized MAE, AND absolute MAE <= 10%
  of sweep range on jitter sigma.
- kill condition: arm b loses to ridge — the inverse is a measurement
  problem, not a learning problem; stop training cnns until the
  features are the bottleneck.

### fx2 — joint recipe regression + cross-param leakage

regress the full recipe vector at once (sigma, taper, width). the
stylebench discipline applied to the fitter itself: does width
perturbation leak into the sigma prediction?

- metrics: per-param MAE (unchanged), plus a leakage matrix —
  MAE(sigma-hat | width sweep) evaluated while holding sigma fixed.
- gate: diagonal MAEs under threshold, off-diagonal degradation
  <= 1.5x the diagonal MAE.
- this run decides whether the node ui fits components independently
  (one fitter each) or jointly (one fitter, all params). preregister
  both interpretations now so the result can't be argued after.

### fx3 — real-image transfer (the one that matters)

fitters trained on synthetic only, tested on the painter corpora
already in the repo (monet / van_gogh / hokusai, 81 works). take real
crops, predict theta-hat, re-render through the substrate, and run
`engine/adapter_probe.py` machinery on the round trip: rendered crop vs
source crop, component shifts.

- metrics: per-painter round-trip component shift (the probe's
  standardized deltas), palette mean dE.
- gate: palette dE <= 10 (the lora spec's threshold, with its known
  several-dE noise floor), stroke-family shifts <= 1.0, on >= 70% of
  crops per painter.
- known cliff, preregistered follow-up: real crops carry noise, canvas
  texture, jpeg artifacts the substrate doesn't — the fitter may
  hallucinate jitter sigma to explain noise. if fx3 fails the gate, the
  preregistered retry is the noise-augmented sweep (gaussian + jpeg
  re-encode augmentation registered with fx1's data manifest, one retry
  only), not ad-hoc tuning. painter-corpus fine-tuning of the fitter
  (the old fx3.1) stays out: it changes the pitch from "measured
  sliders" to "per-painter calibration" and needs a new spec.

### fx4 — boundary mapping (only if fx3 passes)

failure cartography: at which crop sizes, stroke densities, and
resolutions does MAE blow up? output is an applicability map the node
ui can use to refuse bad fits (refusing a fit is honest ui; a wrong fit
is a bug).

## runner protocol (shared)

- every run is a row in `training_jobs` (queue -> claim -> metrics back),
  preregistered: params json holds the gate before the run starts, and
  the gate is committed to the repo in the same commit as the runner
  script. payload shape (fx1 example):

      { "experiment_id": "fx1",
        "hypothesis": "small cnn beats ridge on the inverse mapping",
        "data_manifest": {"sweep_size": 5000, "covariates": ["width"],
                          "split": "interpolative, by sweep value",
                          "augmentation": "none (noise variant registered)"},
        "gates": {"primary": "cnn MAE < ridge MAE",
                   "secondary": "jitter MAE <= 10% of sweep range"},
        "kill_condition": "cnn loses to ridge = measurement problem",
        "budget": {"max_gpu_hours": 2, "fail_run_at": 4} }
- hardware: one mi300x, rocm pytorch docker (rocm 6.0+ for mi300
series), diffusers/accelerate unneeded for fx0-fx2 (pure torch); crops
pre-rendered cpu-side, only training on gpu.
- eta budget: fx1 <= 2 gpu-hours, fx2 <= 4, fx3 inference only + cpu
  rendering (<= 1). if a run exceeds budget x2, it fails the run, not
  the gate.
- every artifact (weights, sweep manifests, metrics json) posted to the
  job row; the registry promotes factors per batch_4 rules only from
  passing gates.

## out of scope (deliberate)

- lora runs — separate spec (research/DATASET_PACKAGING.md lineage).
- full-image fitting — crops only; composition is content, not style.
- generative inversion (diffusion-based image -> params) — the whole
  point of small regressors is cheap, deterministic, auditable fits.
