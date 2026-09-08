# svg substrate run 2 — 2026-09-08

fidelity bench `benchmarks/svg_fidelity2.py`: every remaining factor swept against
ground-truth parameters on the svg stimulus substrate. stimuli in
`data/generated/arch_svg/` (fid2_* + manifest_fid2.json).

## sweep results

### 1. stroke width → measured mean width: strong
| true | measured | ratio |
|---|---|---|
| 3 | 2.37 | 0.79 |
| 5 | 3.88 | 0.78 |
| 7 | 5.37 | 0.77 |
| 9 | 6.88 | 0.76 |

monotone, and the measured/true ratio is nearly constant (~0.78). the ~22%
systematic undercount is the stroke_mask dark-core threshold reading only the
stroke's dark center — a stable, calibratable scale bias, which is exactly the
profile you want from a measurement: predictable bias + linear response.

### 2. taper → measured width: monotone (after fixing my own expectation)
taper is an ease-fraction: te=0.6 spends 60% of the path easing in/out (heavy
taper → thin), te=0.15 tapers only near the ends (nearly uniform).

| te | measured width | stroke cv |
|---|---|---|
| 0.60 | 2.95 | 0.476 |
| 0.30 | 4.29 | 0.541 |
| 0.15 | 5.01 | 0.490 |

measured width rises monotonically as taper eases — correct. and variable-width
baked outlines produce stroke cv ~0.5 vs ~0.19–0.33 for uniform strokes: the cv
metric detects width profiles, not just jitter. bench note: the first version of
this sweep had the expectation inverted (my error, not the analyzer's) — the
substrate was measuring correctly the whole time. that's what ground truth buys
you: wrong expectations get caught by data.

### 3. double-pass → stroke density: detectable, nonlinear
passes 1 → 2: density 0.0320 → 0.0431 (ratio 1.34, naive expectation was ~2).
the second jittered pass overlaps the first, so coverage grows sublinearly.
density is a valid detector (monotone, well above noise) but not proportional to
pass count — spatial overlap breaks linearity. new candidate metric:
`stroke_density` = stroke_mask coverage. unvalidated, same status as the other
candidates.

### 4. lighting → luminance/contrast: fails v0
mean interior luminance: 94.3 → 168.2 → 168.3 → 170.0 (strength 0 → 0.25 → 0.5 →
0.75); contrast not monotone (32.7 → 38.8 → 38.6 → 37.7). the raster
approximation (alpha-composite overlay) does not reproduce soft-light blend
physics: luminance saturates almost immediately, contrast drifts down. verdict:
**lighting fidelity under the v0 raster approximation is not established.** two
fixes possible: implement true soft-light in the raster bake, or render the
canonical svg with a blend-aware rasterizer. the svg layer itself is correct —
this is a renderer-parity gap, same class as the feTurbulence approximation.

### 5. palette interpolation → measured vs true distance: monotone, compressive
| lerp s | measured | true | ratio |
|---|---|---|---|
| 0.25 | 0.0617 | 0.0763 | 0.81 |
| 0.50 | 0.1223 | 0.1543 | 0.79 |
| 0.75 | 0.1424 | 0.2314 | 0.62 |
| 1.00 | 0.1828 | 0.3098 | 0.59 |

monotone, but the measured/true ratio decays with distance — palette_distance
(mean nearest-color between k-means palettes) compresses long-range moves,
likely because k-means centroids of blended images drift less than the role
colors themselves (bg dominance, centroid averaging). usable ordinally; for
strength sliders (application layer) we need a calibration curve or a
role-aware distance.

## where this leaves the fidelity table

| factor | parameter → metric | monotone | linear | verdict |
|---|---|---|---|---|
| jitter | σ → stroke cv / edge entropy | yes | saturating | ordinal, calibrate |
| width | w → mean width | yes | yes (0.78x) | strong |
| taper | te → mean width, cv | yes | untested | good |
| passes | n → stroke density | yes | no (overlap) | detector only |
| texture | amp → texture energy | yes | untested | good |
| palette | lerp s → palette distance | yes | compressive | calibrate |
| lighting | strength → lum/contrast | lum only | no | **fail — renderer parity** |

## next

- lighting: true soft-light in the bake, or blend-aware rasterization; then
  re-sweep
- calibration curves for jitter/palette so strength sliders can claim linear
  control
- stroke_density + shading_contrast added as unvalidated candidate metrics
- stroke_mask speckle fix (run 1 confound) still queued; regression pair A-D
- then: human-judgment validation, now with parameter-labeled stimuli
