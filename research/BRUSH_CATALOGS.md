---
title: brush + recipe catalogues (procreate, ibispaint, polarr, stamps, palettes)
summary: research pass on how the big brush/filter engines parameterize their presets — what maps to our vector two-layer engine, what becomes texture recipes, what's raster-only
status: complete (2026-09-10, firecrawl+tavily pass)
---

catalog pass for the editable brush engine (answers the pending question in
research/EDITABLE_BRUSH_ENGINE.md §4: what is the minimal complete parameter
set for a procreate-class brush on vectors). sources: procreate handbook
(official docs scrape fine), ibispaint (official lectures are js-walled —
used community libraries, as predicted), brushgalaxy (stamps), polarr
support docs (filter architecture). all scraped 2026-09-10.

## procreate brush studio: the 14 attributes

procreate decomposes a brush into 14 attribute groups. the full sub-param
inventory, with our verdict on each:

| attribute | key params | verdict for vector engine |
|---|---|---|
| stroke path | spacing, spacing jitter, jitter (lateral/linear), fall off | adopt: spacing = resample step; jitter split lateral/linear is finer than our single sigma (candidate); fall off = opacity ramp along t (candidate) |
| stabilization | streamline amount/pressure, stabilization, motion filtering | adopt as centerline pre-bake smoothing (input transform, not bake param) |
| taper | pressure/touch taper size+opacity, link tip, tip animation, classic taper | we have size taper + dir; opacity taper and tip shape are candidates |
| shape | source image, scatter, rotation, count, count jitter, randomized, flip x/y, roundness (pressure/tilt graphs, jitter) | shape = outline profile; count/scatter/rotation ≈ our multi-pass (charcoal); scatter+rotation per-pass is the stamp-ness knob |
| grain | source texture, moving vs texturized, scale, zoom, rotation, depth, depth jitter, offset jitter, blend mode, brightness/contrast | this is our layer 2 exactly: grain-as-recipe. "moving vs texturized" = grain that follows the stroke vs stays fixed in canvas space — a real distinction our recipes need |
| rendering | glaze/blending modes (light, uniformed, intense, heavy glaze, blending) | bake-time compositing; texture recipe layer, not geometry |
| wet mix | dilution, charge, attack, pull, grade, blur, wetness jitter | raster pigment physics — exclude from vector core; only reachable as a named texture recipe (the wash-as-recipe conclusion again) |
| color dynamics | per-stamp + per-stroke jitter of hue/sat/lightness/secondary; pressure/tilt color curves | per-stroke color jitter is adoptable (recipe layer); per-stamp jitter = grain-adjacent |
| dynamics | speed/pressure response curves for size/opacity | the big one our substrate lacks: width/opacity as *functions of t*, not constants. a width_profile(t) param subsumes taper + pressure response in one param |
| apple pencil | tilt/azimuth hardware | n/a, hardware input |
| properties | name, use as eraser/smudge, preview icon | metadata, we have it |
| materials | watermark etc | n/a |
| preview/about | housekeeping | n/a |

the catalog converges on a cleaner split than ours: procreate has exactly
one "geometric" concept we haven't parameterized — **response curves**
(width/opacity as functions of position along the stroke), and one finer
**jitter split** (lateral vs linear). everything else wet/raster is already
on the recipe side of our model.

## ibispaint: the parameter family

official lectures scrape to junk (js-heavy), community tutorials carry it.
their brush settings family: thickness, pattern opacity, blending mode,
spacing, **fade (start/end)** — which is just taper-toward/away with two
independent knobs — and a jitter family (jitter thickness, jitter angle,
jitter spacing, jitter opacity), plus shadow size (offset shadow = a
decoration layer), brush hardness, stabilizer. v14.1.0 adds stroke
prediction + ink-bleed brushes.

notable: artwork itself can be imported as brush pattern / paper texture /
texture shape — user-authored sources, same idea as procreate's shape/grain
libraries. their fade-start/fade-end independent tapers is a slightly
richer taper param than ours (one fraction + dir); cheap to adopt as
taper_start/taper_end.

## stamps: a brush is sometimes just a preset with spacing=100%

stamp brushes = shape+grain applied in a single tap: the same engine with
spacing maxed and count=1. nothing new architecturally — but a good
reminder that our "discrete mark pass" (scatter/rotation/count on the
centerline) is the only thing needed to cover stamps, confetti, foliage,
and texture brushes in one param group.

## palettes: the preset-as-portable-file precedent

procreate's palette library: swatches (single colors) grouped into
palettes, importable/shareable as .swatches files. distribution of
mini-presets as portable files with a share ecosystem. this is the
distribution model for our recipe files too (and polarr's QR/shortcode
below is the same idea one level up).

## polarr: the closest thing to style composer in the wild

polarr (web version live at polarr.com, photo editing) ships filters as
**compositional recipes**, and their support docs describe the exact
structure:

- **global adjustments**: light, color, HSL, curves, toning, effects,
  vignette, fringing, grain, detail, LUT
- **selections** (any number): radial, linear, color, luminance, depth,
  AI-detected objects (sky, person, ground) — each selection carries its
  own adjustment stack, plus refinements (reflect, invert, feather,
  smoothing, opacity)
- **overlays** (any number): textures/images, gradients, duotone — each
  with blend mode + opacity, and overlays can live inside selections
- distribution: filters share as **QR codes or shortcodes**; there's a
  creator feed with curation + ranking — a full preset ecosystem

this is the strongest precedent yet for the recipe model: independent
component layers, per-layer params, masks with their own adjustments
(same idea as fontasy-mask's per-zone overrides), packaged as portable
recipes rather than rendered images. the gaps for us: it's photo-only
(raster adjustments, no geometry layer), and there's no editability of
the underlying content — exactly the two things our two-layer engine adds.

## synthesis: the minimal complete vector brush set

folding the catalogs into our existing 6-param family (width, taper,
taper_dir, jitter, grain_amp, textured):

**layer 1 — geometry (centerline + outline):**
- width, as `width_profile(t)` — one param that subsumes taper, fade
  start/end, and pressure response (start/end tapers as special cases)
- spacing (resample step), smoothing (stabilization, pre-bake)
- jitter split: lateral sigma + linear sigma (procreate's split; our single
  sigma is the degenerate case)
- passes: count, scatter, rotation, rotation_jitter (covers stamps, double-
  stroke sketchiness, charcoal multi-pass in one group)

**layer 2 — fill recipe:**
- color, opacity, opacity_falloff(t)
- grain: source, scale, depth, blend, moving vs canvas-fixed
- edge hardness, wet/bleed named recipes (not params)

**the additions worth stylebench claims:** lateral/linear jitter split,
opacity_falloff, width_profile, per-pass scatter/rotation. everything else
in the procreate 14 attributes is either metadata, hardware, or already
ours by another name. that's the answer to the §4 pending question: our
substrate is missing 4 params, not 40.

## post-implementation check (2026-09-10, same day)

all four params are in the substrate now (benchmarks/svg_house.py v2 +
benchmarks/svg_substrate_v2.py sweep, data/generated/substrate_v2/) —
with one null result that reshuffles the layer split:

- **width_profile, jitter_lat, opacity_falloff, pass_scatter,
  pass_rotation**: all render and all separate visually (pixel-diff step
  checks positive at every level).
- **jitter_lin is degenerate on vector geometry.** displacing samples
  *along* the local path direction just slides them along the same
  segment — the polyline is unchanged (verified: 0.0000 pixel diff at
  sigma 4.5 on the house set). procreate's linear jitter is a *stamp
  spacing* wobble, visible only when the brush is raster stamps along
  the path. so jitter_lin moves to layer 2 (stamp/texture density
  param), and the layer-1 jitter is lateral only. one catalog param
  down, three to go.

regression: legacy brushes (clean/sketchy/marker) render byte-identical
to the pre-v2 substrate — old stimuli and judgments stay valid.

next: preregister the stylebench batch for separability of the new
params (width_profile shape, lateral jitter, opacity falloff, pass
scatter/rotation) — survey/specs is the vehicle.
