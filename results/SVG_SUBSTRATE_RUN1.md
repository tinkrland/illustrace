# svg substrate run 1 — 2026-09-08

stimuli: `data/generated/arch_svg/` — same house geometry, now a layered svg
document (geometry + brush recipes + fill roles + texture filter + lighting
overlay). each image ships as canonical `.svg` + analysis `.png` + ground-truth
manifest. research pass: `research/EDITABLE_SVG_STROKES.md`.

new experiment unlocked by parametric stimuli: **measurement fidelity** — the
parameters are ground truth, so we can ask whether the analyzer tracks the
factor that provably moved, not just "separates pairs".

## fidelity 1: jitter σ → stroke measurements (brush factor)

| jitter σ | stroke cv | edge entropy | texture |
|---|---|---|---|
| 0.00 | 0.330 | 0.792 | 5.7 |
| 1.25 | 0.379 | 0.957 | 4.3 |
| 2.50 | 0.410 | 0.969 | 4.3 |
| 3.75 | 0.416 | 0.976 | 4.5 |

monotone: yes. linear: no — stroke cv saturates after σ≈1.25; edge entropy
keeps rising but decelerating. takeaway: single-metric readings are nonlinear
in the parameter; either use metric ensembles per factor or treat measured
values as ordinal, not linear, until calibration curves exist.

## fidelity 2: grain amplitude → texture energy (texture factor)

| grain amp | texture energy | stroke cv |
|---|---|---|
| 0 | 5.8 | 0.330 |
| 8 | 11.5 | 0.295 |
| 14 | 14.8 | 0.326 |

monotone: yes. and note — stroke cv stayed stable (drift ≤ 0.035, within
run-to-run noise) in this raster path, vs the 0.094 contamination seen in the
pil arch set. the cairo-rendered svg strokes + this grain application
contaminated stroke metrics less, but the pil-set confound was real; the
stroke_mask thinness constraint stays on the roadmap as the principled fix.

## the editable substrate works

`showcase.svg` is a full style-composer-shaped artifact: one geometry, sketchy
brush recipe (σ=2.5, double-pass), grain filter on the fills group, lighting
overlay (soft-light gradient) — each a separate svg layer with the recipe
recorded in `data-recipe` attributes. selecting a stroke and swapping its brush
= swapping the recipe on that path; presets are recipe bindings; the raster is
a disposable cache.

## next

- brush inventory beyond jitter: taper (baked outline via width profile),
  marker/width, double-pass sketchiness as explicit params
- palette/lighting fidelity sweeps (lighting strength → measurable shading
  contrast) to bring the remaining factors under ground truth
- stroke_mask thinness constraint + rerun pil arch regression pair (A-D)
- then human-judgment validation on svg-derived stimuli: we can now say "this
  image has σ=2.5 jitter" and ask humans whether it reads as rougher than σ=1.25
