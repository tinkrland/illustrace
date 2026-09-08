---
status: research pass on the editable-svg stroke substrate — read before building stroke/brush tooling
---

# editable svg strokes: research pass

the application layer (`application/README.md`) commits to presets that store
*recipes, not renders*. this pass pins down what that means physically for
strokes: a parametric svg document where every visual factor is an addressable
parameter, procreate-ish expressiveness with figma-ish modularity.

## what "editable stroke" has to mean (constraints from the svg spec)

- svg strokes are uniform-width. `stroke-width` is a single number; there is no
  native taper/variable width. the w3c has a standing proposal
  (`Proposals/Variable width stroke`), not a standard. so expressive brushes
  (taper, pressure profiles) cannot be pure presentation attributes.
- filters (`feTurbulence`, `feDisplacementMap`, grain via `feComposite`) are
  non-destructive and layer-scopable, but can't express width profiles either.
- conclusion: a **brush = deterministic re-render of a clean path from
  parameters**. keep the clean path as the source of truth; bake stylized
  geometry on render; keep the recipe. this is exactly how the proven tools do
  it (below), so it's not a novel gamble — it's the established pattern.

## prior art (parameter inventories worth stealing)

- **rough.js** — hand-drawn look on top of clean shapes. brush-relevant params:
  `roughness` (0 = clean), `bowing` (systematic curvature), `seed`
  (reproducibility), `strokeWidth`, `maxRandomnessOffset`, `curveFitting`,
  plus per-shape `hachureFill` styles. proves that one geometry + one param set
  spans clean-to-sketchy space.
- **perfect-freehand** (powers tldraw's pencil) — input points →
  variable-width outline path. params: `thinning` (how much width follows
  pressure/velocity), `smoothing`, `streamline`, `easing`, `start/end taper`,
  `simulatePressure`. proves taper lives in baked outlines, not attributes.
- **tldraw** — infinite-canvas editor whose strokes are stored as
  (`points`, `style` recipe) and re-rendered from params; brushes in tldraw =
  named parameter presets over the same path data.
- **procreate brushes** — the reference parameter inventory for "brush type":
  spacing, jitter (position/angle), taper, pressure/velocity curves, grain
  (texture source + blend), wetness/charge. none of these are svg-native; all
  become either baked geometry (taper/jitter) or a grain filter/overlay
  (texture).
- **figma styles / component properties** — the modularity model: an object
  references a style; editing the style re-renders every object using it.
  presets in illustrace = the same referential structure.

## the illustrace stroke model (v0)

```
document
├── geometry layer      clean paths (the "intent" — what the artist drew)
├── brush layer          per-path or per-group brush recipe:
│                        { width, jitter_σ, bowing, taper, seed, caps/joins }
├── fill layer           palette swatch references (roles: wall/roof/…)
├── texture layer        layer-scoped grain filter, { density, scale, blend }
├── lighting layer       overlay group { direction, color, blend, strength }
└── preset               a named recipe binding values to the above slots
```

- render = deterministic bake from (geometry, recipes, seed). same seed, same
  image — which is what makes it stylebench-compatible: **the parameters are
  ground truth**. the analyzer measures the raster; fidelity = measured value
  tracks the true parameter (monotonic, ideally linear).
- "change the brush on selection" = swap the recipe on that path/group; other
  layers untouched. that's the independence claim made physical.
- transfer operators become **recipe rewrites on svg elements**, not pixel
  surgery. disposable raster is just the render cache.

## stylebench consequence

parametric svg stimuli close a loop the pixel-only frog/arch sets left open:
we now have exact factor ground truth (jitter σ, width, grain amplitude,
lighting strength). the bench gains a third experiment: **measurement
fidelity** — does measured stroke cv track true jitter monotonically? does
measured texture energy track grain amplitude? any analyzer that can't track
the parameter that provably moved has no business near human-judgment
validation.

## open questions (next pass)

- cap/join interplay: does `stroke-linecap=round` interact with jitter
  measurements? (bench it)
- multi-pass sketchiness (rough.js double-stroke) as one param or two?
- hachure/fill-pattern brushes for the fill layer — same recipe mechanism?
- 3d extension of the same idea lives in the parallel editable-presets thread
  (parametric program + usd-style layers + disposable glb) — same architecture,
  one dimension up.
