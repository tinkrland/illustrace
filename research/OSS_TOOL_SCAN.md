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

## teammate tools (same project team as liat/karla — adoptable, perms confirmed 2026-09-09)

karla's repos (kqrla/fontasy, kqrla/fontasy_fork, kqrla/fontasy-mask) are
teammate work on the same project — liat confirmed we have permission to use
the code. all MIT. this is a different case from PRIOR_ART.md's competitor
observations (those stay name-free); these are credited by name and citable.
clones live outside the repo in the conversation workspace `vendor/` folder.
typography output is in scope when editable (liat, 2026-09-09): fontasy's
whole pipeline — glyphs as vector paths, kerning/spacing as parameters,
color zones + texture as recipe layers — is the word-bearing case of
illustrace's editable-preset principle. lettering/brand-mark deliverables
come out as fonts/glyph sheets/layered vector, never flattened renders.

**fontasy_fork is the adoptable one:**

- **k-means color zones** (`kMeansColors` in web/index.html) — this is the
  vtracer replacement we had penciled in under "modify: suppress color
  merging, keep per-region paths". it clusters glyph pixels in rgb space
  (2-8 clusters, 12 fixed iters), builds a per-cluster binary mask, traces
  each mask through the same moore → douglas-peucker → catmull-rom pipeline,
  and emits per-zone paths with per-zone mean color. zero dependencies,
  ~40 lines. adopt for raster→vector ingestion where per-region paths and
  recipe injection matter; exactly the structure the transfer engine needs.
- **bead mode** — the "skip vectorization, preserve the raster crop" escape
  hatch. this is the same pattern as the editable-presets thread's
  "disposable glb": keep the parametric vector for what it's good at, drop
  to raster when physical texture matters more than editability.
- **texture modes** (clean/rough/crayon/pencil/chalk) — named presets over
  continuous blur params. trivial implementation, but the
  preset-name-over-continuous-slider pattern is exactly illustrace's recipe
  design philosophy; a good minimal case study for bucket 09/10 naming.
- **contour pipeline** (moore trace, dp simplify eps≈1.2-2, catmull-rom
  tension 0.3-0.4, hole detection via flood-fill + winding reversal) —
  battle-tested second implementation to cross-check our svg substrate's
  trace/simplify/smooth stages, or lift directly (mit + team perms).

**fontasy-mask** — pattern-fill-as-mask (composite `source-in`) + dashed
edge-stitch + salt-and-pepper fabric grain overlay + recolorable palette
swatches, with per-letter overrides. structurally identical to illustrace's
layered substrate bake (fill recipe → edge treatment → grain layer, per-
instance overrides as layers). its compositing chain is a clean reference
for the surface/texture bucket (07) rendering path; the per-letter override
model mirrors the editable-presets "overrides stored as layers" idea.

**fontasy (base)** — the fork supersedes it for our purposes; original is
the cleaner minimal read of the pipeline (650-line single file, jszip +
opentype.js only, everything else hand-rolled including a woff sfnt wrapper).

**rogo** (Jakob-Bock/Rogo, rework at lab.vanity-ibex.xyz) — also teammate
work. hofmann-inspired rope/pole generative tool, svg export. pure
procedural mark-making (bucket 05): small fully-exposed parameter set (pin,
resize, layer toggle, snap) driving line output. candidate reference for a
generative (not baked-jitter) mark-making mode if that bucket grows.

fork roadmap items worth tracking as convergent signals: variable weight
axis from stroke-thickness detection, kerning from inter-glyph spacing,
"style transfer between fonts" — all the same measure-then-parameterize
philosophy illustrace runs on, arriving from the typography side.

## non-goals reminder

no human identity/anatomy/realism subjects; no flattened-static-render
outputs anywhere (typography included — words ship as editable fonts/
vector, not baked images); inspos stay private; benchmarks stay
name-neutral (see PRIOR_ART.md).
