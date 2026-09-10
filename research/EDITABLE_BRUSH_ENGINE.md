---
title: editable brush engine research
summary: deep research pass on making brushstrokes editable vectors — figma import semantics, the centerline+brush two-layer representation, brush parameter decomposition
status: active research (started 2026-09-10, first pass)
---

# editable brush engine: strokes as adjustable points, brushes as switchable recipes

the application vision (application/README.md, mirrored from exactly.ai's live
parameter sliders): the user selects a stroke, moves its points, switches its
brush, drags a strength slider, and the output is an editable figma-importable
vector — never a flattened png. this document researches what that requires on
the svg front, in depth.

## 0. the vision, stated precisely

think figma vector drawing with procreate-style brushes:

1. every brushstroke is an editable vector — selectable, movable points
   (figma's edit-path handles)
2. every stroke carries a *brush assignment* that is switchable after the fact:
   select the roof stroke, swap "ink pen" for "watercolor round", re-render
3. brush parameters are live sliders (width, taper, jitter, texture amp),
   not baked constants — adjusting re-renders the stroke
4. the whole thing imports into figma as vectors, not images

two representations are in tension: **svg native strokes** (editable,
uniform width only) and **baked outlines** (any brush look, but geometry
is frozen — the brush recipe is destroyed into a filled path).

## 1. what the current substrate has — and where it breaks

established first-hand 2026-09-10 (`benchmarks/svg_house.py`):

with the plain `clean` brush, output is genuinely figma-ready:

```xml
<g id="strokes" stroke="#45251c" stroke-width="5" stroke-linecap="square"
   stroke-linejoin="round" fill="none">
  <path class="stroke stroke-walls" data-brush="linework"
        d="M 140.0 220.0 L 140.0 392.0 L 330.0 392.0 L 330.0 220.0"/>
  ...
</g>
```

per-stroke identity (`stroke-walls`), per-stroke brush assignment
(`data-brush="linework"`), uniform-width native strokes — 8 selectable
paths. good bones.

the break: the instant a brush gets a *personality* (any taper or jitter),
`build_svg` calls `bake_outline()` and **replaces the centerline path with a
filled outline polygon**. verified: the taper-away variant renders 8
`baked-outline` filled paths and 0 native stroked paths. consequences:

- the brush recipe is destroyed into geometry — no re-baking with a
  different brush, no slider, no taper adjustment
- the editable centerline is gone — moving a point in figma moves a
  baked blob's vertex, not the stroke's skeleton
- brush semantics survive only as `data-brush` metadata — which figma
  import drops anyway (see §2)

so today the substrate can deliver *either* editability *or* brush
character. the application needs both at once. that is the whole problem.

## 2. figma import semantics (what survives the border)

[research pending — sub-agent pass in flight; primary-source verification of
what figma's svg importer keeps, converts, and drops. working notes:]

- native strokes (stroke-width, linecap, linejoin, dasharray) import as
  figma vector strokes — editable points preserved
- filled paths import as vector shapes — editable, but semantically flat
- css classes and `data-*` attributes are dropped at import: any brush
  semantics encoded there exist only in the file, not in figma
- what survives figma is therefore geometry + basic stroke props;
  **brush identity must live in a sidecar keyed to stroke identity**, and
  re-enter the figma context via a plugin or by re-export

## 3. the two-layer representation (proposed core architecture)

the fix is the source of truth split that cad tools have used forever:

```
layer 1: centerline (the editable skeleton)
  - svg path with named identity, editable points, no bake
layer 2: brush recipe (the style, per stroke or per group)
  - params: width, taper(+direction), jitter, grain amp, texture mode...
  - strength slider = lerp distance through recipe param space
bake (on demand): centerline + recipe -> filled outline geometry
  - regenerable at any time, cacheable, disposable
```

render pipeline becomes: `centerline x recipe -> bake -> svg/png`. changing
the brush re-bakes from the untouched centerline. moving a point changes
only layer 1. strength sliders interpolate layer 2 only. this maps
directly onto the stylebench thesis: layer 1 is *content*, layer 2 is
*style*, and independence is structural, not aspirational.

current substrate pieces that already fit: `GEO` (the centerlines as
point lists), `BRUSHES` (recipe dicts), `bake_outline` (the bake
function). what's missing is keeping layer 1 in the output and deferring
the bake: emit centerline + recipe sidecar, bake at render/export time,
and re-bake on any parameter change.

first-hand verification (2026-09-10, `bake_outline` round-trip test):
centerline is identical after baking with two different brushes;
geometry differs between brushes; re-baking with the same recipe is
byte-identical. layer 1 invariance and bake regenerability hold today —
only the *emission* of layer 1 is missing (bake currently replaces the
centerline in the output instead of decorating it).

open questions:

- does figma import of a *group* preserve ordering/identity well enough
  to re-match centerlines to baked outlines by position? (likely yes —
  same document order)
- brush interpolation: is "switch brush" a discrete jump or a continuous
  path through recipe space? (slider friendliness says continuous)
- should baked strokes carry an invisible sibling centerline (e.g.
  `display:none` path) so figma users can re-select the skeleton? or is
  the sidecar + plugin the only honest channel?

## 4. brush parameter decomposition (what is a brush, parameterically)

[research pending — sub-agent pass on procreate brush studio, krita
engine, perfect-freehand parameters. working notes from the substrate's
own brushes:]

current `BRUSHES` in the substrate already decompose as: width, taper,
taper_dir, jitter (position noise sigma), grain_amp (texture), textured
flag. that is a 6-parameter family and the survey batches already show
some of them are perceptually separable (roughness, texture). the
question this research must answer: what is the *minimal complete*
parameter set for a procreate-class brush on vectors — shape/grain
wetness/pressure curves are raster-brush concepts; which translate to
vector strokes and which become recipe *texture layers* instead
(cf. the wash-as-recipe conclusion in research/STYLE_ONTOLOGY.md)?

## 5. figma make tool precedent (ai-authored, two-layer in the wild)

liat fed the brush engine concept to figma's agent and it authored a
working figma plugin/make-tool from it — "Brush strokes"
(vendor/figma-brush-tool/, source + compiled code.js + port test). it
is the two-layer representation implemented natively in figma, and it
is further along the figma round-trip than anything else we have:

- **state**: `centerline: {x,y}[]` extracted from any figma vector
  path (vectorNetwork segments flattened via tangent sampling), stored
  in `setPluginData` on the *original* node alongside the full params
  object — a recipe sidecar living on the geometry itself
- **params**: brush preset (9: clean, sketchy, marker, calligraphy,
  tapered, ink brush, charcoal, pencil, felt tip) -> width multiplier,
  jitter sigma, passes, taper fraction, taper_dir
  (symmetric/toward/away — the same vocabulary as our substrate),
  plus seed, color, and jitter/taper overrides
- **bake**: resample at 4px spacing, per-point normals, taper-scaled
  half-width (floor 0.05), left/right offset polygon, one filled
  vector per pass (charcoal = 3 jittered passes, deterministic via
  seeded LCG + box-muller)
- **re-bake**: params-change messages re-bake *in place* from the
  stored centerline, reusing the output node id — sliders re-render
  live, original centerline stays hidden-but-intact, "remove" restores
  it. relaunch button pinned on the node for later re-entry

verified by porting the pure functions out of typescript into the test
harness (vendor/figma-brush-tool/port_test/presets.svg): all nine
presets bake coherently — jitter, multi-pass, and tapers all behave.

what it lacks vs. our engine plan: fills are flat solid color only —
no texture/grain recipes, and multi-pass has no opacity variation so
charcoal passes just thicken; outlines are polyline-only (M/L/Z, no
curve fitting); centerline extraction assumes one ordered stroke
(the network walk would misread branching paths); `cap` is declared
but unused. so it covers layer 1 (centerline + width recipe) fully but
none of layer 2's texture side. good news: the gap is precisely where
our grain-amp/recipe layers live, and the pluginData sidecar + re-bake
pattern is directly adoptable for our figma round-trip.

the agent also shipped a **web version** (vendor/figma-brush-web/,
react+vite, builds clean): same engine exported as a dependency-free
`src/brushEngine.ts` with `generateOutlines` (pure: centerline+params
-> outlines) and `strokesToSVG` (stroke set -> svg export). draw on
canvas -> export svg -> import to figma -> plugin can re-bake from the
imported vectors. per-stroke opacity is new vs the plugin; still flat
fills, and strokes bake at pointer-up with no post-draw re-parametrize
ui yet — added 2026-09-10: an "edit strokes" mode (click a stroke,
its centerline highlights, sliders re-bake it in place from the stored
centerline; draw mode untouched). the web version is now as
non-destructive as the plugin: every stroke keeps its centerline and
recipe, and either can change at any time without touching the other. runs anywhere vite does, no figma plan or
desktop app needed.

figma plan note: the manifest declares `isTool: true` (agent-invocable
in figma make, paid ai features). but the same code runs as a plain
development plugin on the free plan — compiled `code.js` is in the
vendor folder, import via figma desktop -> plugins -> development ->
import from manifest, sliders work manually.

## 6. evaluation hook (keep it stylebench-shaped)

if the engine is "select vector, switch brush, adjust sliders," its
claims are testable in the existing stylebench frame:

- **re-bake fidelity**: bake -> unbake -> bake round trip is lossless in
  layer 1 (centerline identical, recipe identical)
- **brush independence**: switching stroke A's brush never changes
  stroke B's geometry
- **slider monotonicity**: moving taper 0.15 -> 0.30 -> 0.60 produces
  measured width changes matching the fidelity run 2 sweep
- **figma round trip**: export -> figma import -> move a point -> re-export
  -> re-bake keeps the rest of the document stable
