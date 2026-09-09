---
status: research scan for adoptable oss — read before building substrate/editor/ingestion tooling
---

# oss tool scan: adopt / modify / skip

scan sources: web search + repo read + one agentic synthesis pass. criteria:
does it move illustrace's specific architecture (parametric substrate, recipe
baked renders, ground-truth fidelity), or just do generic graphics?

## adopt

- **tldraw** — editor layer. its storage pattern (`points[]` + style recipe →
  re-render) is exactly the illustrace stroke model, proven at scale. build the
  thin editor wrapper around its canvas sdk when the interactive layer starts;
  perfect-freehand is already bundled in it as the outline baker.
- **rough.js** — substrate bake. parameter inventory (`roughness`, `bowing`,
  `seed`, `maxRandomnessOffset`, `curveFitting`, hachure fills) maps directly
  onto the brush-recipe slots; use as the sketchy-geometry baking pass with the
  recipe's seed threaded through for determinism. (our v0 jitter bake is a
  reimplementation of a subset of this — swap when brushes grow.)
- **perfect-freehand** — substrate bake. `thinning/smoothing/streamline/taper/
  simulatePressure` map 1:1 onto the width-profile slots proven in fidelity run
  2. adopt as the baked-outline generator for tapered strokes (same role as
  our `bake_outline`, battle-tested).
- **meerk40t/svgelements** — recipe i/o. most complete pure-python svg parser;
  use for round-tripping parametric svg docs (path geometry + params) from
  bench tooling without a headless browser.

## modify

- **vtracer** — transfer engine ingestion. raster→svg is the path from
  reference illustrations to clean geometry before recipe assignment.
  modification: suppress color merging (keep per-region paths) and surface
  path-level output for recipe injection.
- **CompVis/content-style-disentangled-ST** — transfer engine. closest
  published architecture to factor-independent transfer. modification is heavy:
  replace the monolithic style vector with per-factor recipe channels (stroke,
  palette, texture, lighting independent) — but the loss landscape and training
  regime are reusable rather than invented from scratch. candidate for the
  learned-operator research track.

## skip

- **penpot** — svg-native open-source design tool, but its data model is
  presentation-attributed svg (widths/fills baked in attributes), not
  parametric recipes. retrofitting recipe indirection costs more than building
  the thin editor we need. revisit only if preset interchange with penpot
  users becomes a goal.
- **svg.brushstroke.js** — decorative baked brush geometry, no recipe
  abstraction, no determinism story. rough.js + perfect-freehand cover it.

## xano control plane (parallel finding)

xano exposes a metadata api (bearer auth, aud `xano:meta`) with instance/
workspace/branch endpoints and full workspace export — the control plane is
programmable end to end, not just a data api. the repo's xano client was
already provisioned through it; the toolkit task this week extends coverage.

## teammate tools (credited by name — permitted, not competitor prior art)

these are OSS by a teammate (kqrla / Jakob-Bock), explicitly ok to reference
by name — different case from PRIOR_ART.md's competitor observations, which
stay name-free on purpose. illustrace itself stays clear of logos/text-content
work (typography, lettering, brand marks are out of scope), but the underlying
techniques cross-reference our own pipeline:

- **kqrla/fontasy** — handwriting-to-font tool (figma plugin + web app).
  its vectorization stage is structurally the same pipeline illustrace's
  svg substrate already runs: moore boundary tracing (contour) → douglas-
  peucker (simplify) → catmull-rom→cubic-bezier (smooth) → opentype.js
  export. useful as a second implementation to check our own trace/simplify/
  smooth stages against, not a component to adopt (different output target,
  fonts vs illustration strokes).
- **kqrla/fontasy-mask** — applies decorative pattern fills (gingham, polka,
  stripes, checkered) plus edge-stitch and fabric-noise overlays as masks
  onto letterforms, with recolorable swatches. the pattern-as-mask + edge
  treatment + noise overlay structure maps directly onto ontology bucket
  **07 surface + texture** (`research/STYLE_ONTOLOGY.md`) — worth studying
  as a second surface-recipe implementation, kept general (any vector shape,
  not just letterforms) for illustrace's use.
- **kqrla/fontasy_fork** — fork/variant of fontasy, not yet reviewed in depth.
- **Jakob-Bock/Rogo** (+ rework at lab.vanity-ibex.xyz/rogo_rework) — armin
  hofmann-inspired generative tool: draw ropes between adjustable poles,
  export as svg. no text/logo involvement at all — this is pure procedural
  mark-making (bucket **05 mark-making**), closer to a generative-geometry
  reference than fontasy/fontasy-mask. the pole/rope parameterization (pin,
  resize, layer toggle, snap-to-grid) is a clean example of a small, fully
  exposed parameter set driving varied line output — same spirit as
  illustrace's brush-recipe sliders, worth a closer look if/when the mark-
  making bucket needs a generative (not just baked-jitter) mode.

## non-goals reminder

no human identity/anatomy/realism subjects; inspos stay private; benchmarks
stay name-neutral (see PRIOR_ART.md).
