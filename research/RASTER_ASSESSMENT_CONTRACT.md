---
status: v0.1 provisional instrument contract
scope: post-hoc assessment of fixed diffusion-native raster outputs
---

# raster assessment contract

## purpose

raster assessment does not assume that a generator exposes factor controls, preserves
pixel correspondence, or will revise an output. it measures finished candidates, reports
what is and is not observable, and ranks candidates against factor-specific references.
the editable vector path is a separate output regime.

```
factor references + finished raster + optional source/masks
  -> factor evidence + provisional similarities + uncertainty + abstentions
```

v0.1 is an **instrument**, not a learned perceptual judge. its scores are provisional
until calibrated against factor-specific human pairwise judgments. no score may be
reported without its component measurements, observability, and confidence basis.

## inputs

- `candidate`: one finished RGB raster.
- `references`: one or more reference rasters for each requested factor.
- `source` (optional): the intended content image. it is a content anchor, never a style
  reference unless the user explicitly assigns it to a factor.
- `subject_mask` (optional): a candidate-space binary mask identifying the region to score
  as the focus subject.
- `region_mode`: `whole`, `subject`, or `background`.
- `reference_aggregation`: `mean` (match the reference set as a whole) or `best` (match any
  valid reference in the set).

paths in a spec are resolved relative to the spec file. the machine-readable input schema
lives at `schemas/raster_assessment.schema.json`.

## factor vocabulary

v0.1 scores the seven composer factors already used by the application:

- `palette`
- `value`
- `color_zones`
- `shading`
- `texture`
- `stroke`
- `edges`

references remain user-assigned to these factors. neither saliency nor a vision model is
allowed to silently decide which image contributes which factor.

## focus subject and opencv

opencv can help with mask morphology, connected components, contours, color conversion,
and classical saliency. it cannot determine the intended focus object reliably from pixels
alone. high contrast, central placement, and semantic importance are different concepts.

subject-region authority is therefore ordered:

1. explicit candidate-space mask supplied by the user or dataset;
2. mask from a version-pinned semantic segmentation model, with model and confidence logged;
3. deterministic border-contrast foreground heuristic, labeled `heuristic_foreground`;
4. whole-frame fallback, labeled `whole_frame`.

v0.1 implements 1, 3, and 4 with numpy/scipy/pillow. semantic segmentation and dense
source-to-candidate correspondence are intentionally deferred. if a heuristic cannot find a
credible foreground area, regional scoring falls back to the whole frame and lowers
confidence. a source image is not used as a candidate mask unless a later correspondence
layer maps it into candidate coordinates.

## measurement structure

for each factor, v0.1 emits multiple bounded channels rather than one opaque embedding:

| factor | deterministic channels |
|---|---|
| palette | perceptual lab histogram, lab moments |
| value | luminance histogram, luminance quantiles, contrast |
| color_zones | spatial color pyramid, drift-tolerant sorted tile colors |
| shading | low-frequency gradient magnitude, orientation, tonal coverage |
| texture | multiscale high-pass energy, residual distributions |
| stroke | dark-line coverage, width mean/cv, axis/concentration |
| edges | multiscale density, magnitude distribution, orientation entropy |

all factors are measured over the selected region. color zones retain both a spatial channel
and a location-tolerant channel so composition drift is visible instead of accidentally
ignored.

## outputs

one scorecard contains:

- factor similarity in `[0, 1]`, explicitly marked `provisional`;
- score per measurement channel;
- candidate observability for that factor;
- agreement among channels and among multiple references;
- confidence value and `high`, `medium`, or `low` label;
- abstention boolean and reason codes;
- mask provenance and mask coverage;
- uncalibrated no-reference quality observations;
- instrument version and limitations.

there is no universal style score in v0.1. factors have different psychometric scales and
cannot be averaged honestly before human calibration. candidate ranking will operate on
factor ranks later, not raw cross-factor arithmetic.

## confidence and abstention

v0.1 confidence is instrumental, not perceptual. it combines:

- factor observability in the candidate;
- channel agreement;
- agreement across references;
- regional-mask confidence.

it abstains when the selected region is too small, linework is not observable for stroke,
edge evidence is insufficient, or every requested factor lacks a reference. future human
calibration will add perceptual noise floors and confidence intervals.

## content/style boundary

- source-to-output content preservation is a separate measurement family.
- reference-to-output factor similarity is style evidence.
- subject and background scorecards remain separate when a mask exists.
- content-reference leakage requires a learned or correspondence-aware content descriptor;
  v0.1 does not pretend its low-level statistics can prove identity leakage.

## validation obligations

before a deterministic channel can become a validated style measurement it must pass:

1. identity: an image compared with itself scores near one;
2. perturbation specificity: known palette, blur, grain, edge, and value changes move the
   intended channels more than unrelated channels;
3. raster robustness: jpeg, webp, resize, and mild decoder-like perturbations stay below a
   measured noise floor;
4. subject generalization: behavior survives held-out illustrated subjects;
5. generator generalization: behavior survives held-out diffusion systems;
6. human agreement: score differences predict single-factor pairwise judgments on a held-out
   calibration set.

until item 6, every similarity remains `provisional` and may rank candidates only with that
warning attached.
