---
status: working ontology + research matrix — the taxonomy is itself a main output; every parameter carries evidence status, not pretend objectivity
---

# style ontology and research matrix

the working thesis: **visual style is not one thing.** an illustration's style is
the interaction of many semi-independent visual systems — linework, geometry,
color, shading, texture, rendering — and style transfer fails today because
tools treat it as a monolith to copy rather than systems to borrow from.

this document defines the ontology illustrace studies: the decomposition, the
parameter status ladder, the research matrix, and how each claim gets tested.
it is the research contract for the engine: nothing becomes a "control" until
it climbs the evidence ladder.

## scope

- intentionally stylized 2d illustration (later 3d): no realism, no human
  identity/anatomy, no unconstrained character work.
- asset classes decompose as **character / object / setting**. character design
  is out of scope for now — the study starts with **objects and settings**,
  single asset and composed set.
- reference points (nova3d, openscad, etc.) stay reference points; the study
  is standalone. style-transfer inspirations stay private by design (see
  PRIOR_ART.md).

## the granularity question (new, first-class)

the same artist treats a single asset and a composed set differently: the
palette, the coloring, the shading, the lighting of a lone chair is not the
palette/coloring/shading/lighting of that chair in a room. so style parameters
must be studied at two granularities:

```
asset-level profile   — one object or one setting element, isolated
set-level profile     — the composed scene: relations, lighting, staging
```

testable claim (stylebench-able): for each parameter, is it **granularity
stable** (asset and set readings agree) or **granularity dependent** (the set
changes it)? parameters that are granularity dependent need set-context in
their operational definition — an asset-level reading alone is not the style.
the benchmark stimulus families therefore come in pairs: same asset rendered
solo and inside its set, parameters otherwise identical.

## the ontology (ten dimensions + cross-cutting layers)

```
01 content                 what is depicted — preserved by default, not style
02 spatial construction    composition, staging, perspective, framing
03 shape language          primitive vocabulary, curvature, angularity, simplification
04 silhouette + geometry  silhouette statistics separate from internal construction
05 mark-making             stroke geometry, width, taper, jitter, direction, density
06 color + value           palette, value architecture, saturation, temperature, relationships
07 surface + texture       micro/meso/macro texture, grain, material cues
08 shading + illumination shading model, shadows, highlights, lighting field
09 edge + rendering        edge profiles, rendering model, medium simulation
10 medium + material      substrate behavior, pigment physics, material representation
```

cross-cutting measurement layers (not standalone categories):

```
frequency structure   — where visual information lives: low / mid / high band
relationships         — relational readings: stroke width / subject height, shadow
                        darkness / local value, texture scale / canvas resolution
scale                 — every px-valued reading normalized against a canonical size
```

**subject is not style.** a cottage, tree, chair, flower belong to the content
layer. how the cottage is constructed visually belongs to style. composition,
typography, ui elements, subject matter, objects, pose are disabled by default
in any transfer.

**typography/logos are an explicit non-goal, not just a disabled default.**
lettering, brand marks, and logo-with-text-content work stay out of scope for
illustrace entirely (liat, 2026-09-09) — separate from the "composition
preserved by default" rule above, which is about not transferring content;
this is about not building the capability at all. `research/OSS_TOOL_SCAN.md`
has a credited-by-name section on a teammate's typography tooling
(kqrla/fontasy, fontasy-mask) studied purely for technique cross-reference
(vectorization pipeline, pattern-as-mask), not as a direction illustrace
is heading in.

**02 spatial construction splits into a 2d-depth track and a 3d-positioning
track — different problems, not one deferred item.** 2d depth cues
(occlusion/overlap, relative scale, atmospheric/value falloff, layering order)
are how a flat illustration fakes depth without real 3d coordinates — that's
squarely illustrace's own future work. true 3d positioning (camera-relative
xyz, perspective projection, joint/kinematic placement) is the parallel
nova3d/openscad "editable presets" thread's problem
(`research/EDITABLE_PRESETS_RESEARCH.md`, outside this repo — standalone
research, reference point only), not this one. don't conflate the two when
scoping "positioning" work later.

## parameter status ladder

```
candidate parameter
  → measurable parameter        (test 1: a machine can measure it)
  → transferable parameter      (test 3: changing it is possible)
  → independently transferable (test 3b: changing it leaves others intact)
  → user-controllable parameter (human-usable control with a calibration curve)
```

those are not synonyms. "paper grain" is measurable and transferable but maybe
not independent from texture. "whimsy" is maybe measurable, probably not
directly controllable yet. the registry records where each parameter stands —
and the engine only exposes controls at the top of the ladder.

## the research matrix

for every candidate parameter, the row is the experiment backlog:

| parameter | operational definition | measurable? | human agreement | independent? | transferable? | scale-dependent? |
|---|---|---|---|---|---|---|

- **test 1 (machine):** fidelity sweeps on the parametric substrate — the
  parameter is ground truth, so the metric must track it monotonically (and
  linearly for slider-grade control; see the calibration note in
  SVG_SUBSTRATE_RUN2).
- **test 2 (human):** forced-choice pairwise judgments against the ground-truth
  ordering (survey app); agreement rate above the catch-pair noise floor.
- **test 3 (independence):** the confound test — change one parameter, measure
  the others; leakage within noise = independent (the run-1 grain/stroke
  confound is the cautionary tale).

the machine-readable version is `engine/registry.py` — the single source of
truth; `results/PARAMETER_MATRIX.md` renders from it.

## measurement families

six families, each with its own benchmark module:

```
family 1  geometry     shape complexity, curvature, angularity, symmetry,
                        simplification, silhouette, exaggeration, proportion
family 2  mark          stroke width, width variation, jitter (position/angle/
                        width split), taper, directionality, continuity,
                        density, contour hierarchy, contour completeness
family 3  color         palette size/entropy, hue, value, saturation,
                        temperature, contrast, color relationships
family 4  surface       texture scale (micro/meso/macro), frequency,
                        regularity, grain, material cues
family 5  illumination  value architecture, shading bands, shadow system,
                        highlight system, lighting field, occlusion
family 6  presentation  edge profiles (hard/soft/lost/irregular), rendering
                        model, medium simulation, visual density, negative space
```

## style profile shape

the engine's target representation — never a bare embedding, never raw px:

```json
{
  "mark": {
    "stroke_width": {
      "value": 0.018, "unit": "subject_height_ratio", "confidence": 0.94,
      "granularity": ["asset", "set"]
    },
    "width_variation": { "value": 0.71, "confidence": 0.88 },
    "roughness": {
      "value": 0.82,
      "frequency": { "low": 0.12, "mid": 0.67, "high": 0.21 }
    }
  }
}
```

each component carries raw measurement, normalized measurement, confidence,
scale, granularity stability, and dependencies. relationships are stored as
ratios against canonical sizes — `outline_width / subject_height` transfers
across resolutions; `4px` does not.

## pipeline

```
reference → style encoder → style profile → select components
→ transfer parameter relationships → reconstruct → measure output
→ compare against requested delta → record in the control plane
```

the research question that governs everything: **what is the smallest useful
set of measurable variables that explains the visual differences humans
perceive as style, within intentionally stylized imagery?** the ai part gets
substantially less mysterious once the representation is defined — models are
then estimating and manipulating a defined object, not conjuring style.

## study tooling

- **substrate:** parametric svg stimulus generator — deterministic renders
  from (geometry, recipes, seed); parameters are ground truth (svg_house).
- **control plane:** xano (runs, judgments, experiments; schema-first).
- **study infrastructure:** the adaption api — datasets for stimuli +
  measured profiles + human judgments (csv/jsonl upload), adaptive data to
  curate and normalize the reference sets, autoscientist for the later
  operator-learning research loop. sdk: `adaption`, key: $ADAPTIONLABS_API_KEY.
- **research scientist:** glm 4.7 via the model router for hypothesis
  synthesis and experiment interpretation (pending router access fix).

## current evidence (2026-09-09)

climbed so far (substrate fidelity + honesty about failures):

- stroke width: monotone + linear (0.78x stable bias) — slider-grade
- jitter σ: monotone, saturating — ordinal, calibration curve pending
- taper: monotone — good
- double-pass: detectable via stroke_density, nonlinear (overlap)
- grain amplitude: monotone (texture energy)
- palette lerp: monotone, compressive at long range — calibration pending
- lighting strength: monotone on mean luminance, fixed-support measurement;
  the old contrast signal was a mask-drift artifact
- lessons recorded: masks from reference renders, never per-image; calibration
  curves before claiming linear control; wrong expectations get caught by
  ground truth (taper direction)
- granularity run 1: stroke width scale-normalizable (stable to 1-3%
  normalized); asset palette stable while the set-level palette is a genuinely
  different profile (d=7.0 with zero new colors); canvas-anchored recipes
  (grain, lighting) shift subject-relative scale and readings with staging —
  recipes must declare their anchor. **metrology rule three: asset-level
  measurement must exclude set-context features** (ground line + bush arc
  inflated cv to 0.786 until the crop was context-cleaned)


## research scientist session notes (tensormux, glm-4-7-flash — 2026-09-09)

first synthesis session over the 46-candidate registry. recorded as
pre-registered predictions — they get tested, not trusted:

**next test-1 targets (mix of likely-pass and likely-informative-failure):**
- stroke_directionality — computable straight from path segment angles; likely pass
- value_range — trivially measurable; fundamental; likely pass
- texture_scale — directly tied to substrate noise parameters; easy parametric control
- shape_complexity — highest noise risk; a failure here would expose the substrate's
  inability to decouple geometry from stroke density (informative either way)

**pre-registered test-3 confound predictions:**
- stroke_density <-> shape_complexity — density is partly a proxy for complexity
- palette_size <-> value_range — bigger palettes tend to need wider value spread
- stroke_width <-> lighting_strength — thick-outline styles often couple to strong
  directional lighting or flat shading (stylistic correlation, not causation —
  the substrate can decouple them, the world just tends not to)
- texture_scale <-> texture_energy — scaling a pattern changes its band energy;
  likely inseparable in output statistics

**session meta:** glm-4-7-flash is a thinking model — completion budget must
include reasoning tokens (content arrives empty at low max_tokens). sessions
are uneven; use for ranking/critique passes, not final judgment.

## research scientist session notes (nebius token factory, glm-5.2 — 2026-09-09)

first glm-5.2 pass after the nebius token factory came online (openai-compatible,
thinking model: budget ~1.8k reasoning tokens before content; fast, ~14s per pass).
prompt: pilot survey findings + design batch 2 under a 5-minute-per-judge constraint.
full output below, lightly formatted.

### batch 2 (its proposal)

5 judges, ~22 pairs, under 5 minutes. four blocks:

- **taper block (8 pairs, jitter=0, grain=0):** heavy vs uniform (x2, L/R swapped);
  light vs uniform; heavy vs light; heavy vs uniform+jitter=2 (cross-cue test);
  heavy vs uniform at jitter=4. run half the block under the prompt "rougher" and
  half under "more calligraphic" — the within-judge framing swap is the dimension
  membership test. decision rule: if >=4/5 judges read heavy taper as smoother under
  "rougher" AND discriminate it under "calligraphic", promote taper to its own
  line-character axis; if it loads on neither, kill the candidate; if it loads on
  "rougher" with opposite polarity, invert the axis (wrong polarity, right dimension).
- **grain floor (6 pairs):** fixed finer steps 0v1, 0v2, 1v2, 2v4, 4v6, 6v8 —
  no staircase (needs 20+ trials per axis per judge; unaffordable). fixed steps
  replicate across judges and yield a psychometric curve directly. plus one ABX
  "same or different?" trial at 0v1 to separate true perceptual floor from response
  bias (d' separately from "which is more").
- **lighting verify (4 pairs):** 2 brightness, 2 warmth, on the corrected prompt.
- **catches (4):** identical pairs at non-round positions 4, 11, 17, 21.

### cheap tricks it flagged (priority order)

1. randomize L/R per judge (left bias runs 3-5 percent)
2. reverse polarity on ~30 percent of pairs ("smoother" instead of "rougher") —
   without this we measure response set, not perception
3. catches at non-round positions (predictable positions get auto-clicked)
4. ABX triplet catches ("which two are the same?") instead of identical pairs
5. 3-level confidence only (guess/sure/certain); 5-level burns decision time
6. log dwell time; flag sub-1.5s answers as noise, exclude from aggregates
7. open with one anchor pair (extreme difference, not scored) for calibration

### session meta

glm-5.2 is a clear step up from glm-4-7-flash for design critique: structured,
prioritized, concrete numbers. cost per pass ~2.4k completion tokens (trivial
against the credit balance). still treat as advisory — humans sign off on
survey instruments before they reach judges.

## adaption study-infrastructure scout (2026-09-09)

- **datasets (adaptive data):** upload flow is initiate -> s3 put -> complete
  (verified: s3 accepts, but adaption's storage-verify endpoint returned 503
  all day; re-runnable at research/adaption/upload_preferences.py). pilot
  judgments are exported as 10 preference pairs at
  research/adaption/pilot_preference_pairs.jsonl — chosen = the image the
  judge said matched the trait prompt, rejected = the other. augment()
  takes training_type=preference_pairs + domain/general row counts; estimates
  require a real dataset id, so the estimate runs after the upload lands.
- **autoscientist:** the loop trains against a dataset with
  training_method=instruction|alignment, data_format=chat, target_win_rate,
  max_iterations. 18 supported models, including VLM-capable variants
  (gemma-3-27b-it-VLM, gemma-4-31b-it-VLM, nemotron-3-nano-omni) — meaning a
  style-judge can be fine-tuned directly on image preference pairs once
  enough human judgments accumulate. that is the operator-learning loop the
  validation thread is building toward: humans validate the metrics, then the
  trained judge scales the measurement.
- **ladder:** the plan holds — humans sign off on instruments and metrics;
  glm-5.2 preregisters and interprets; the autoscientist loop only executes
  once its training data (human preference pairs) exists at real n.
