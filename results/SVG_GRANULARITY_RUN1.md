---
status: granularity run 1 — complete; the headline is a metrology rule, not a style claim
---

# granularity run 1: asset vs set (svg substrate)

the claim under test (STYLE_ONTOLOGY.md): the same asset rendered solo vs
staged in a set carries different palette/shading/lighting treatment, so
style parameters need a granularity column.

the stimulus pair controls everything except composition: identical house
geometry, roles (the set adds **zero new colors**), brush recipe, and seed.
the set stages the house at scale 0.55 with sun, trees, bushes on shared
ground. two stagings: house left (context right) and house right (context
mirrored) — staging position matters for canvas-anchored parameters.

## results

**A. house region, solo vs in-set (contaminated crops, full bbox):**

| reading | solo | set-left | set-right |
|---|---|---|---|
| stroke_width_px | 5.05 | 3.20 | 3.74 |
| stroke_width_cv | 0.243 | 0.488 | **0.786** |
| edge_dir_entropy | 0.992 | 0.991 | — |
| texture_energy | 15.2 | 21.4 | 21.1 |
| palette_distance | 0.7 (vs solo) | | |

**B. full canvas, solo vs set:** stroke width 4.39 → 4.03 px, texture 11.5 →
12.8, **palette_distance 7.0** (house-region palette distance: 0.7).

**C. lighting (canvas gradient, house interior, fixed support):**
mean lum solo 133.8, set-left 134.2, set-right 129.6.

**D. clean-crop control (context excluded from the region):**

| reading | solo | set-left | set-right |
|---|---|---|---|
| stroke_width_cv | 0.285 | 0.357 | 0.244 |
| stroke_width_px | 4.43 | 2.50 | 2.48 |
| normalized w/h | 0.01691 | 0.01735 | — |

## findings

1. **stroke width is scale-normalizable, and after normalization,
   granularity-stable to ~1-3%.** raw px drops 0.56x at scale 0.55 exactly as
   predicted; width/subject_height reads 0.01691 solo vs 0.01735 in-set.
   px readings without normalization are meaningless across granularities —
   the registry's scale-dependence column is now evidence-backed.

2. **the contaminated crops exposed a metrology confound, not a style
   effect.** in-set cv inflated to 0.786 — not because the house changed, but
   because canvas-scale context features (the 5px ground line crossing the
   crop, a bush arc bleeding into the bbox) mixed into the stroke-width
   population. raising the crop bottom above the ground band collapses cv
   back to 0.242-0.357. **rule three of the metrology: asset-level
   measurement must exclude set-context features** — crop to the subject
   bbox, and where bbox cropping can't exclude context, use context-class
   masks (or measure from the vector source, where parameters are exact).
   run 1's mask lessons now number three: reference-render masks, fixed
   supports, context exclusion.

3. **palette is granularity-stable at the asset anchor and granularity
   dependent at the set anchor.** house-region palette distance 0.7 (noise
   floor — the house itself is unchanged), full-canvas 7.0 (the set
   redistributes color areas even with zero new colors). this is the
   ontology's granularity claim, measured: the set-level profile is a real
   different profile, not a sum of asset profiles.

4. **canvas-anchored parameters shift subject-relative scale with staging.**
   grain (canvas px) reads +41% texture energy on the smaller house while
   staying staging-position-stable (21.1 vs 21.4); lighting reads on the
   identical house differ by staging position (133.8 / 134.2 / 129.6) purely
   from where the gradient puts the asset. substrate consequence: recipes
   must declare their anchor (canvas vs subject) — an undeclared anchor is a
   hidden granularity bug. subject-anchored grain = filter inside the
   transform; canvas-anchored = applied post-group.

5. **edge direction entropy is granularity-stable** (0.991-0.992 across
   solo, set, and staging) — the first parameter to earn "both, stable" with
   no caveats.

## registry consequences

- stroke_width: granularity "both, scale-normalizable (validated ~1-3%)"
- stroke_width_cv: evidence updated with the contamination caveat
- edge_direction_entropy: "both, stable"
- texture_energy / grain: "canvas-anchored (declared); subject-relative
  scale shifts with staging"
- lighting_strength: "canvas-anchored; asset reading is staging-position
  dependent — set-context contaminates unless lighting is subject-anchored"

## next

- subject-anchored grain/lighting variants (recipes inside the transform)
  to measure the other anchor condition
- real-corpus granularity: the substrate proves the *measurement* behaves;
  whether human artists actually change treatment between asset and set is
  a corpus question (adapted datasets, stylebench claim vs human judgment)
- context-class masks in the analyzer (svg source knows what is context)

## research scientist review (tensormux, glm-4-7-flash)

recorded as critique of this draft, pre-registered for the next runs:

1. **threats to validity.** "palette is granularity dependent" survives only
   with the anchor distinction explicit — the run shows the *set-level*
   profile differs while the *asset-level* profile is stable; conflating them
   is anchor ambiguity. the lighting delta (129.6 vs 134.2) is a property of
   the canvas-anchored gradient recipe, not evidence about artist behavior —
   contextual contamination if read as a stylistic claim.
2. **next experiment.** subject-anchored grain/lighting variants (recipes
   inside the transform) — the only way to know whether texture and lighting
   are valid subject-level style parameters or positioning artifacts.
3. **priority change.** texture_scale promotes to the #1 test-1 target: the
   substrate must prove it can be subject-anchored and scale-normalizable;
   if grain stays canvas-anchored it is not a valid style parameter for
   transfer. stroke_directionality and value_range follow.
