# dataset packaging spec (kohya sd-scripts, flux.1 [dev] lora)

the goal: turn a painter corpus (v0: monet, 39 works) into a kohya-ready
dataset for a **style adapter lora** — the claim is palette + broken-color
rendering (late monet is impasto, not watercolor; "wash" was a mislabel,
caught in the glm-5.2 critique pass), not subject. this spec is the last
pre-gpu artifact: when the amd box arrives, training is a command, not a
design decision.

critique pass: glm-5.2 (nebius tokenfactory), 2026-09-10; fixes folded
in below and marked [critique-fix].

source requirements verified from sd-scripts docs (2026-09-10,
`.research_cache/kohya_*.md`): flux lora example uses
`--network_module networks.lora_flux --network_dim 16 --network_alpha 1
--learning_rate 1e-4 --timestep_sampling shift` (+ `--discrete_flow_shift
3.1582 --model_prediction_type raw --guidance_scale 1.0` for flux.1 dev);
datasets support folder+txt captions or metadata.jsonl with `caption`,
`tags`, `image_size` (image_size lets bucketing skip file reads).

## resize / crop policy

- **no cropping.** the corpus is wash-dominant; crops change texture
  statistics (the thing the adapter claims) and the probe would measure
  the crop, not the style. aspect-ratio bucketing handles the mixed
  landscape/portrait corpus natively.
- **resolution 1024, enable_bucket=true**, `min_bucket_reso=768`,
  `max_bucket_reso=1024` [critique-fix: 1280 buckets upscale non-square
  inputs ~25%; 1024 caps every bucket at native res, no upscale anywhere].
- if a future corpus exceeds 1280, downscale long side to 1280, never
  upscale.

## captioning strategy

the adapter is style-only, so captions must describe the **subject** and
leave style unspoken — undescribed features get absorbed into the trigger
token, described ones get credited to the text (and leak into every
generation that mentions them).

- template: `<trigger>, a painting of <subject>` — trigger is a
  **no-english-subword token** (`mzqtlv` for v0) [critique-fix: the first
  draft's "mntwash" contains the word "wash", which would contaminate the
  trigger with the exact claim it's supposed to absorb]. verify the BPE
  split at training time.
- `<subject>` derived from the work title, hand-pruned of style words,
  generic filler, **and time-of-day/lighting words** (sunset, evening,
  moonlight...) [critique-fix: "sunset stays because it's subject" was
  circular — sunset IS the late-period palette, and the pruner was making
  the style/subject call the adapter is supposed to find. lighting goes to
  the trigger with the rest of the palette].
- subject distribution is checked at packaging (water-lilies share of a
  late monet convenience sample can quietly hit 50%+); if one subject
  family dominates, the trigger risks absorbing subject, not style —
  rebalance or stratify before training.
- no tags for v0 (kept simple), but **caption_dropout_rate 0.1** is on
  [critique-fix: with dropout, some steps see no caption at all, forcing
  style absorption into the trigger rather than text-credit. it's also the
  cheap test that style was learned, not memorized].

## repeats / steps math

39 images -> 36 train, repeats 3, epochs 16, batch 1 -> ~1728 steps
(~48 effective steps/image; community range for flux style loras is
80-200, so still lean — first run tells us which side of it we land on).
**dim 16 / alpha 16** [critique-fix: alpha 1 = effective scale 0.0625,
below measurability at ~1k steps — you can't measure an effect that isn't
there; alpha=dim keeps the adapter small but measurable]. save every 2
epochs (8 candidates) — 3 candidates was too coarse for a noisy probe.

## hold-out eval set

3 corpus works are **excluded from training** and reserved as probe
targets, picked by stratified random (year tercile, not the year extremes
— early/mid/late picks would make the holdout an extrapolation test
without saying so [critique-fix]). the eval at each checkpoint:

1. the probe target is the **36-work training profile** [critique-fix:
   profiling all 39 put the holdouts inside the target — leakage by
   construction].
2. generate all 3 holdout subjects + a **negative set** (non-monet
   prompts, e.g. a portrait of a dog, an interior) with the checkpoint.
3. probe: fidelity = holdout generations vs training target (mean palette
   dE < 10, claimed-component shift < 1.0); leakage = unclaimed components
   on the negative set moving above the **base-model floor** (generate the
   same sets with untrained flux.1 dev as the baseline — "passes fidelity"
   is uncalibrated without it).
4. promotion: lowest mean palette dE among checkpoints with no unclaimed
   shift above floor + 1sd. aggregate over holdouts, ties broken by
   fewer leaked components.

## packaging layout

    data/kohya/monet/            # training images + captions (.txt same stem)
    data/kohya/monet/metadata.jsonl   # caption + image_size per image
    data/kohya/monet_holdout/    # 3 held-out works (probe targets)

`engine/package_dataset.py` writes all of it from the corpus dir +
metadata.json. validation gate: profiling `data/kohya/monet` must equal
the corpus target profile (identity check — packaging changed nothing).

pre-training gates (block training until each passes): trigger-prior
check — generations with `mzqtlv` on untrained flux.1 dev must not already
look monet; subject-distribution check — no single subject family >40% of
captions.

measurement caveat (found packaging monet, 2026-09-10): the k-means
palette extractor is not stable under jpeg recompression — a q95
re-encode shifted centroids up to dE 25 on near-tie clusters (water
lilies greens). packaged copies are therefore bit-identical for
already-srgb sources, and palette-fidelity thresholds (dE < 10) should
be read as containing several dE of measurement noise, not zero.

known confounds, accepted for v0 and disclosed in the demo: the corpus is
1024px scans (museum tiffs downsampled differently per source; icc profiles
and jpeg artifacts vary — the adapter learns scan-of-monet to some degree);
1024px on ~2m canvases destroys stroke-level texture, so claims are
palette + color rendering, not brush micro-structure; provenance (scan
heterogeneity) is real and unmeasured.

open items (deliberately deferred): captioning automation for corpus
scale-up (not worth it until painter #4), multi-resolution training
(1024 only for v0), color management per source (unify to srgb at
packaging; per-museum profiles later).
