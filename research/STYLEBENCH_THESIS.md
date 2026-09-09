---
status: v0 — formalized 2026-09-08, supersedes the "operator-first" framing in results/report.md
---

# stylebench thesis v0

## the premise

"style" cannot be treated as an undifferentiated latent property if we want controllable
transfer. it needs an explicit, computationally measurable representation *first*.
transfer is not the first operation — measurement is.

```
raw asset -> measurement -> style representation -> transfer -> new representation -> render
```

"style transfer" is not a single operation. before we can define it we have to answer:

- what style properties exist?
- how are they measured?
- how independent are they?
- how do they interact?
- how perceptually important are they?

only after that do we get to define transfer. everything built so far (palette distance,
stroke width cv, edge direction entropy, texture energy, the palette_transfer operator) is
real work but it was built in the wrong order relative to this — we jumped to an operator
on one factor (color) before validating that any of our measurements track something a
human would actually call "style." this doc reorders the roadmap around that gap.

## scope constraint (v1 and for a while)

explicitly stylized / illustrated assets only. this is a deliberate laboratory choice, not
a permanent limitation: style is strongly designed, visible, and exaggerated in this domain,
which makes "is this measurable" tractable *before* touching the much nastier problems of
anatomy, identity, realism, and likeness.

```
stylebench v0
│
├── 2d
│   ├── hand illustration
│   ├── graphic illustration
│   ├── icons
│   ├── decorative art
│   ├── sprites
│   └── flat / cel / painterly stylization
│
├── 3d
│   ├── low-poly
│   ├── voxel
│   ├── toy-like
│   ├── geometric
│   ├── stylized hard-surface
│   └── illustrated / storybook 3d
│
└── explicitly excluded for now
    ├── photorealism
    ├── semirealism
    ├── human identity / likeness
    ├── facial anatomy
    ├── realistic anatomy
    ├── unconstrained character generation
    └── product try-on / mockup / product-shot use cases
```

also a hard output constraint, not just an input one: illustrace produces **presets,
not static assets**. generated pieces must remain editable — parametric, layered,
figma-style adjustable — rather than baked into a render that can't be taken apart.
this is the same belief as the parametric-preset-styles thread: style should survive
edits, not just exist in a render.

practical consequence for stimulus design: the frog stimuli (benchmarks/make_stimuli.py)
are borderline — a face with eyes reads as "character" even though it's not human/realistic.
architecture/interior subjects are cleaner: no anatomy, no identity, and still has all the
style-bearing structure we care about (mark-making, shape language, color, texture, edges).
8 reference illustrations pulled into `data/test_images/` (2026-09-08) as the target texture
for the next stimulus generation pass — riso-style streets, ink-line storybook houses,
painterly warped houses, flat gouache row-houses, painted tree/bench, flat vector towns,
cartoon night streets, flat vector institutional building. buildings/streets/interiors are
the new default non-character subject going forward; frogs stay as a secondary sanity check,
not the primary domain.

## the style representation is hierarchical

some style properties aren't atomic — they decompose. **we should not assume all of these
are independent; discovering which ones actually are is stylebench's first job.**

### 2d: illustration style

```
mark-making        stroke width, width variation, taper, jitter, pressure behavior, edge roughness
shape language      angularity, roundness, simplification, exaggeration, symmetry, curvature
color language       palette size, saturation, value range, temperature, contrast, relationships
rendering language    flatness, gradient usage, shading complexity, highlight/shadow behavior
texture language      grain, frequency, irregularity, directional texture, material simulation
edge language          hard/soft, clean/rough, outlined/unoutlined, contour emphasis
```

### 3d: style

```
geometry language     polygon density, faceting, silhouette complexity, simplification,
                       exaggeration, curvature, proportion distortion
construction language  primitive vocabulary, modularity, beveling, extrusion behavior,
                        boolean/detail language
surface language        roughness, gloss, metallicness, texture density, surface variation
color language            palette, quantization, saturation, contrast, value structure
shading language            flat/smooth, cel behavior, ao strength, shadow structure
rendering language            outlines, dithering, post effects, lighting behavior
```

mapped onto the four representation families for 3d specifically: image-native, geometry-
native, material-native, render-native parameters. the same transfer framework should
eventually operate over all four — this is also directly relevant to the parallel
nova3d x openscad preset-styles thread (parametric + layered presets), since both projects
need a representation for "style" that survives edits, not just a baked render.

### mapping onto what's already built

| existing metric (engine/analyzer.py)     | hierarchy slot                          |
|---|---|
| palette (dominant colors + weights)       | color language: palette size, relationships |
| stroke_width_cv                            | mark-making: width variation             |
| edge_direction_entropy                     | shape/edge language: contour regularity  |
| texture_energy                             | texture language: grain/frequency proxy  |

these four are candidate measurements, not validated style factors yet — see below.

## prior work and honest positioning

we are not claiming to have invented style decomposition. there is substantial prior
work across content/style disentanglement, reference-based generation, controllable
image editing, multi-reference conditioning, style representations, and artistic
style transfer. existing approaches demonstrate that visual characteristics can be
extracted, represented, or conditioned independently.

the novel-ish angle of this project is the **particular benchmark + granularity +
evaluation methodology + illustration-specific focus**. precisely:

> stylebench investigates how reliably those characteristics can be isolated,
> selectively transferred, recombined, and quantitatively evaluated in
> hand-illustrated imagery.

competitive / prior-art observations are kept name-free in the project by design (see
research/PRIOR_ART.md); adapters for systems under research live under
`stylebench/baselines/{reference-transfer, diffusion-edit, multi-reference,
component-conditioned, illustrace}`.

## stylebench: the benchmark definition

stylebench evaluates whether an image generation or image-editing system can:

1. identify visual style attributes
2. selectively transfer requested attributes
3. preserve non-requested attributes
4. preserve source content
5. prevent reference-content leakage
6. combine attributes from multiple references
7. provide predictable control over transfer strength

baseline systems are evaluated by class, not by name. each receives the same target
image, reference image(s), requested component(s), component weights, and generation
parameters; outputs are scored with the same metrics. the benchmark does not assume
any particular architecture is correct. baselines are named simply `baseline_001`,
`baseline_002`, `baseline_003`, ... and `illustrace_v0`. no competitor names appear
anywhere in the project — illustrace should be defined by the measurable problem it
is solving, not by what it's better than.

## the core research problem is factorization

given a stylized asset `x`, we want:

```
x = content + structure + style
style = stroke + shape language + color + texture + rendering + ...
```

two falsifiable questions per factor:

1. **can factor a be changed without accidentally changing factor b?** (independence)
2. **does factor a remain meaningful across different subjects?** (generalization — this is
   why controlled pairs across multiple subjects, e.g. frog *and* building *and* tree, matter
   more than one perfect pair)

## discovery/validation before transfer (the reordering)

the roadmap so far skipped straight to a transfer operator (palette_transfer). the correct
order is:

```
1. propose candidate measurements (done: 4 metrics above)
2. validate against human judgment (NOT done — this is the actual next step)
3. only then build transfer operators against validated factors
```

validation design: for each candidate metric, ask humans binary/comparative questions —
"which of these two images has rougher linework?" / "how different are their palettes?" /
"did the second image adopt the first image's texture?" — and correlate human answers
against the computed metric across *many* subject pairs, not one. agreement rate (or
rank correlation) is the actual pass/fail criterion for a candidate becoming a validated
style factor. this benchmark doesn't exist yet; it's the next concrete deliverable.

## transfer, once factors are validated

an operation becomes an explicit vector over validated factors, not a single "strength" knob:

```json
{ "transfer": { "stroke_roughness": 0.8, "palette_size": 0.0, "texture_frequency": 0.4 } }
```

evaluated per-factor:

```
requested: stroke_roughness   before: 0.21   reference: 0.83   output: 0.75
-> "moved 91% of the way toward the reference while unrelated properties changed <4%"
```

that sentence is the actual scientific claim stylebench exists to produce — not a single
scalar "style similarity: 0.81."

### strength = distance traveled through style space

`strength = 70%` on an untouched latent knob is meaningless. redefined: strength is the
fraction of the measured distance from the target's factor value to the reference's factor
value that the output actually closes. this is exactly what
`requested_fidelity_fraction()` in engine/metrics.py already computes for palette — it was
accidentally the right idea, just not yet generalized to arbitrary factors or validated
against human perception of "how much did this move."

### style invariants

every transfer declares what must change and what must not:

```
instruction: transfer color only
MUST CHANGE:    color
MUST PRESERVE:  silhouette, geometry, stroke, texture, composition, subject
```

every run produces a delta vector across all factors (not just the requested one) — this
formalizes "collateral style change" as a first-class, measured thing. `content_preservation`
and `non_target_preservation` in engine/metrics.py are the first two invariants implemented;
they should generalize to one delta-per-factor as more factors get validated.

## revised core thesis

not: *can ai transfer art styles?* (already demonstrably possible, not interesting)
not: *can ai transfer styles more accurately?* (too vague to falsify)

instead:

> can visual style be decomposed into measurable, controllable factors that can be
> selectively transferred while preserving non-target properties?

```
stylebench
  -> discover factors
  -> validate factors (against human judgment)
  -> measure factors
  -> learn transfer relationships
  -> build transfer operators
  -> build style composer
  -> illustrace
```

## immediate next steps (in research-first order)

1. rebuild the controlled stimulus set on architecture/interior subjects (non-character,
   matches the excluded-domain constraint cleanly) using the 8 references as style targets —
   this replaces/extends the frog pairs as primary test subjects.
2. design and run the discovery/validation benchmark: human comparative judgments on the
   4 existing candidate metrics, across multiple subjects, correlated against computed values.
   this is the actual gating step before building operator #2.
3. only after (2) passes for a given factor: generalize `requested_fidelity_fraction` /
   `non_target_preservation` into a per-factor delta vector, and build the next deterministic
   operator (stroke roughness is the natural candidate — mark-making is orthogonal to color).
4. keep the v0.1 soft-assignment palette operator fix (in progress) as the reference
   implementation of "one validated factor, one clean operator" — it's the existing proof
   that this pipeline works end to end for color.
