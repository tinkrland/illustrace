---
status: anchor run 1 — complete; lighting anchors cleanly, grain anchors directionally, and texture_energy itself failed its granularity test
---

# anchor run 1: subject-anchored grain and lighting

the gating question from the granularity run 1 review: if grain and lighting
cannot be subject-anchored and scale-normalized, they are not valid
subject-level style parameters.

implementation: the grain patch is applied in house-local coordinates — the
same rng field cropped to the house bbox in solo space, scaled 0.55 with the
house, pasted at the staged position (the house experiences the same
noise-to-subject statistics as solo). subject-anchored lighting evaluates the
gradient in house-local coordinates over the house rect only; the context
stays unlit (an honest disjoint set).

## results

**lighting (house interior, fixed support):**

| anchor | mean lum | contrast |
|---|---|---|
| solo, canvas gradient | 133.8 | 22.7 |
| set, canvas-anchored | 134.2 (129.6 right staging) | 22.4 |
| set, subject-anchored | **133.7** | 23.0 |

**grain (texture energy on the house region, analyzer metric):**

| anchor | texture_energy |
|---|---|
| solo | 15.2 |
| set, canvas-anchored | 21.4 (+41%) |
| set, subject-anchored | 18.3 (+20%) |

**grain (ground-truth wall-fill blocks, |∇| per pixel):**

| block | solo | set subject-anchored | set canvas-anchored |
|---|---|---|---|
| left wall | 7.37 | 7.61 (+3%) | 9.12 (+24%) |
| right wall | 5.41 | 3.60 (-33%) | 5.89 (+9%) |

## findings

1. **subject-anchored lighting works, staging-independent by construction.**
   the identical house reads 133.7 vs solo 133.8 under its own light,
   wherever it is staged. anchor duality is a real stylistic choice, not a
   bug: canvas-anchored lighting = one shared light field (how sets are
   usually lit), subject-anchored = per-asset treatment. recipes now declare
   their anchor; the substrate renders both.

2. **grain can be subject-anchored, and the anchor changes what texture
   means.** on ground-truth fill blocks, subject-anchored grain reads -33%
   to +3% of solo while canvas-anchored reads +9% to +24% — the same noise,
   different subject-relative wavelength. verdict for the gating question:
   texture is a valid subject-level parameter; the anchor is a recipe
   property. (physically, canvas-anchored grain is also legitimate — paper
   grain belongs to the canvas, material texture belongs to the asset. the
   ontology gains an anchor column.)

3. **the run's biggest catch: texture_energy failed its own granularity
   test.** the analyzer metric (+41% / +20%) disagrees with ground-truth
   fill blocks (+9..24% / -33..+3%) — mechanism: the metric's interior mask
   (~stroke & ~bg-within-tolerance-30) collapses at small subject scale. the
   grain-off control returned exactly 0.0 in the set crop: the interior mask
   fell under the <100px guard; with grain, a small boundary-biased pixel
   remnant drives the mean. the +41% of granularity run 1 was substantially
   a metric construction artifact, not anchor behavior. texture_energy is
   demoted from validated to measurable (fixed-scale fidelity still holds).
   **metrology rule four: metric construction must be scale-invariant —
   masks from vector ground truth, thresholds independent of subject scale,
   never a masked image mean over a mask whose size is scale-coupled.**

4. the substrate's fix is available immediately: the svg source knows every
   fill region exactly, so per-region texture statistics can be computed
   over ground-truth interiors — the same source-of-truth discipline as the
   reference-render masks of rule one, one level deeper (vector, not raster).

## registry consequences

- lighting_strength: anchor duality documented (canvas-anchored recipe is
  position-dependent by construction; subject-anchored reproduces the asset
  reading exactly)
- texture_energy: demoted validated → measurable (fixed-scale fidelity only;
  granularity-brittle masked-mean construction)
- texture_scale: subject-anchored grain implemented and directionally
  scale-normalizing — valid subject-level parameter, anchor declared
- grain recipes must declare their anchor (canvas | subject)

## next

- rebuild texture measurement on vector-ground-truth fill regions
  (per-region σ + |∇|), re-run both anchor conditions, restore the metric
- the test-1 batch after that: value_range (trivial), stroke_directionality
  (path angles), shape_complexity (informative-failure candidate)

## research scientist review (tensormux, glm-4-7-flash)

1. the demotion of texture_energy is **justified** — the 20-40% disagreement
   with ground-truth blocks proves the guard/mask artifact was driving the
   signal, not the parameter; demotion prevents benchmark false positives.
2. the subject-anchoring verdict is **supported** — the -33..+3% block spread
   is the empirical proof that the noise is relative to the asset geometry,
   not the canvas.
3. the rebuild must compute per-region statistics **directly from svg source
   paths**, bypassing raster interior masks and their scale-coupling entirely.
