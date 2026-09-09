# parameter matrix (renders from engine/registry.py — edit there)

status ladder: candidate -> measurable -> detector -> validated ->
(transferable -> independently transferable -> controllable, tested next).

**46 candidates** across 6 families —
candidate: 36 detector: 2 measurable: 3 validated: 5

## geometry (9)

| parameter | status | granularity | operational definition | evidence |
|---|---|---|---|---|
| shape_complexity | candidate | both | contour information density: number of direction changes per unit contour length | untested |
| angularity | candidate | both | corner angle distribution: acute/obtuse frequency + polygonality index | untested |
| curvature_mean | candidate | both | mean signed curvature along dominant contours | untested |
| curvature_variance | candidate | both | curvature variance + frequency of abrupt direction changes | untested |
| silhouette_complexity | candidate | both | perimeter^2/area + fractal dimension of the subject mask | untested |
| silhouette_convexity | candidate | both | subject area / convex hull area (concavity and pocket structure) | untested |
| simplification | candidate | both | detail-to-area ratio: feature count vs minimum feature size | untested |
| exaggeration | candidate | asset | proportion deviation from a canonical object model (needs canonical baselines) | untested |
| symmetry | candidate | both | bilateral symmetry score of the subject mask | untested |

## mark (10)

| parameter | status | granularity | operational definition | evidence |
|---|---|---|---|---|
| stroke_width | validated | both, scale-normalizable | mean stroke width, normalized by subject height (px never transfers alone) | fidelity run 2: monotone + linear, 0.78x bias; granularity run 1: normalized w/subject_height stable to 1-3% across staging (0.01691 vs 0.01735) |
| stroke_width_variation | validated | both | width coefficient of variation along strokes | fidelity runs 1-2: tracks jitter sigma (saturating), detects taper; granularity run 1: contaminated crops inflate cv to 0.786 (context features mixing into the width population) — asset measurement requires context exclusion |
| jitter_position | detector | both | contour deviation amplitude: high-frequency normal displacement of the ideal line | svg sweep: monotone via cv/edge entropy but saturating after sigma~1.25 — ordinal, calibration curve pending |
| jitter_width | candidate | both | width modulation amplitude along the stroke (separate from position jitter) | split proposed in the ontology; untested as a separate axis |
| taper | validated | both | width change along stroke: ease fraction + taper rate/symmetry | fidelity run 2: mean width rises monotonically as taper eases; cv confirms profile detection |
| stroke_directionality | measurable | both | orientation distribution entropy + local directional coherence | edge_direction_entropy monotone on the jitter sweep; granularity run 1: stable across solo/set/staging (0.991-0.992) — first uncaveated 'both, stable' |
| stroke_density | detector | both | stroke_mask coverage: marks per area | double-pass ratio 1.34 (not ~2 — spatial overlap); detects, does not scale |
| stroke_continuity | candidate | both | average uninterrupted run length + gap frequency | untested |
| contour_hierarchy | candidate | both | outer/inner contour width ratio | untested |
| contour_completeness | candidate | both | fraction of implied region boundaries that carry a drawn contour | untested |

## color (9)

| parameter | status | granularity | operational definition | evidence |
|---|---|---|---|---|
| palette_size | candidate | both | distinct perceptual color clusters | k currently fixed at 6 — perceptual-count estimator pending |
| palette_entropy | candidate | both | color cluster distribution entropy | untested |
| value_range | candidate | both | luminance percentile spread (p5-p95) | untested |
| value_bands | candidate | both | quantized tonal band count in interiors | untested |
| saturation_mean | candidate | both | mean saturation over subject regions | untested |
| temperature_balance | candidate | both | warm/cool luminance-weighted hue balance | untested |
| color_relationships | candidate | both | relationship tendency scores (complementary/analogous/triadic) + relative structure, not raw rgb | untested |
| local_contrast | candidate | both | adjacent-region color distance distribution | untested |
| palette_distance | measurable | both | distance between measured palettes (mean nearest-color) | lerp sweep: monotone but compressive at long range; granularity run 1: asset-anchored palette stable (d=0.7), set-anchored differs (d=7.0, zero new colors) — the set is a real different profile |

## surface (6)

| parameter | status | granularity | operational definition | evidence |
|---|---|---|---|---|
| texture_energy | validated | both | per-region luminance sigma + gradient over vector-ground-truth fill interiors | gt run 1: rebuilt per rule four — sigma linear in grain amp (1.94/4.85/7.16 at 0/8/14); anchor laws hold (canvas-anchored flat at -7%, subject-anchored linear 0.55 law within 4%). the rebuild also caught the corner-cutting jitter bug (vertices were being dropped) |
| texture_scale | measurable | both | micro/meso/macro band split of spatial frequency energy (paper grain vs brush patches vs blooms) | anchor run 1: subject-anchored grain implemented (noise in house-local coords) — wall blocks read -33..+3% of solo vs canvas-anchored +9..+24%: texture is a valid subject-level parameter; anchor is a declared recipe property |
| texture_directionality | candidate | both | dominant texture orientation distribution | untested |
| texture_regularity | candidate | both | periodicity/regularity of texture pattern | untested |
| grain_strength | candidate | both | grain amplitude at the micro band | independence from texture_energy untested — likely confounded by construction |
| fill_boundary_precision | candidate | both | fill boundary sharpness + color bleed at region edges | untested |

## illumination (7)

| parameter | status | granularity | operational definition | evidence |
|---|---|---|---|---|
| shading_band_count | candidate | both | quantized luminance transition count in interior regions | untested |
| shadow_softness | candidate | both | shadow transition width profiles | untested |
| shadow_darkness | candidate | both | shadow value relative to local fill value (relational reading) | untested |
| highlight_intensity | candidate | both | highlight luminance + size distribution | untested |
| lighting_strength | validated | both | mean luminance delta over fixed-support interiors (w3c soft-light model) | run 2b: monotone 94.3->100.8 under true soft-light + fixed support; granularity run 1: canvas-anchored recipe — identical house reads 133.8/134.2/129.6 by staging position (set-context contaminates unless subject-anchored) |
| lighting_directionality | candidate | both | luminance gradient field directionality across the subject | untested |
| shading_contrast | candidate | both | interior luminance std on fixed supports | FAILED as a lighting-strength metric (flat response by design of the recipe) — kept as candidate for directional-lighting recipes |

## presentation (5)

| parameter | status | granularity | operational definition | evidence |
|---|---|---|---|---|
| edge_hardness | candidate | both | edge transition width profile (hard/soft/lost) | untested |
| edge_irregularity | candidate | both | edge deviation + broken-edge frequency | untested |
| negative_space_ratio | candidate | both | empty-area proportion + empty-region distribution | untested |
| visual_density | candidate | both | marks + details per area vs negative space (minimalist vs ornate) | overlaps stroke_density at the line level — independence test pending |
| medium_bleed | candidate | both | pigment/substrate interaction: bleed, pooling, dry-brush gaps (medium simulation, not overlay texture) | untested |

## evidence legend

- validated — machine fidelity passed (monotone at minimum)
- measurable — tracks ground truth; linearity unproven
- detector — detects change, nonlinear response
- candidate — proposed, awaiting test 1
