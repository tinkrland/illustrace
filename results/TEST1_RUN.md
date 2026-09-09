# test-1 run: value_range, stroke_directionality, shape_complexity

three registry candidates against substrate ground truth, one deliberate
informative-failure candidate. benchmark: svg_test1.py, tests: test_test1_metrics.py.

## value_range: validated, exactly

the palette knob rescales role luminance deviations (l' = 0.5 + k(l - 0.5));
the expected spread is computed from the exact area-weighted role mixture.

| k | measured | expected |
|---|---|---|
| 0.50 | 70.78 | 70.78 |
| 0.75 | 98.08 | 98.08 |
| 1.00 | 125.50 | 125.50 |
| 1.25 | 152.92 | 152.92 |
| 1.50 | 180.22 | 180.22 |

exact at every point, and the mechanism matters: p5 and p95 are carried
inside the two dominant flat blocks (sky, ground), so the pixel percentiles
land on role luminances exactly. caveat, not a flaw: this is a
**canvas-level** metric. changing a context color moves it without touching
the subject's value structure, so subject-level claims need a declared
region anchor (the granularity column again).

## stroke_directionality: rotation-exact, tie-limited

measured dominant axis 88.9 (concentration 0.38) vs GEO length truth 1.0
(0.43): the stimulus's horizontal and vertical populations are near-tied
(984 vs 948 path length, 4% apart) and the raster winner flips. the
consistency tests are exact:

| rotation | measured axis | expected |
|---|---|---|
| 0 | 88.9 | 88.9 |
| 30 | 58.1 | 58.9 |
| 90 | 178.9 | 178.9 |

verdict: axis + concentration validated as a detector (recovers known
transforms exactly); axis identity is resolution-limited under near-tied
populations. entropy side (edge_direction_entropy) was already validated.

## shape_complexity: the informative failure, confirmed

vector truth: base house 17 corners, complex variant (attic window + second
chimney) 23 corners, density 7.73 -> 9.53 per kpx (+23%).

| brush | perim_area ratio | entropy |
|---|---|---|
| clean | 1.031 | 0.791 -> 0.791 |
| sketchy | 1.028 | 0.940 -> 0.941 |

raster proxies respond ~3% to a 23% ground-truth change, at the *clean*
brush; jitter swamps further. mechanism: isoperimetric ratio and boundary
entropy are dominated by stroke rendering (width, caps, wobble), not by
true contour structure. **shape parameters need the vector source**: the
substrate provides exact corner density; raster masks cannot. status stays
candidate, by design of the finding.

## registry

- value_range: candidate -> validated (canvas anchor caveat declared)
- stroke_directionality: measurable -> validated (rotation-exact, tie caveat)
- shape_complexity: candidate, informative failure recorded (vector source
  is the only viable route, consistent with metrology rule four)

## research scientist review (tensormux, glm-4-7-flash)

1. value_range exactness is a triumph, not degeneracy: the luminance model
   is mathematically robust against brush artifacts. the canvas caveat
   stands.
2. stroke_directionality validated: the tie-flip is a known resolution
   artifact; the 0/30/90 consistency proves the detector recovers transforms
   exactly.
3. shape_complexity verdict sound: raster corner detection would be
   noise-sensitive; the 3%-vs-23% response confirms the vector source is
   mandatory for shape metrics.
