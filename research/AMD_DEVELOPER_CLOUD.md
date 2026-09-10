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
