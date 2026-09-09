# illustrace

illustrace tackles the widespread assumption that art style is one undifferentiated blob you can score with a single number, by treating style as a hierarchical, measurable, independently manipulable system of visual factors, validated against human judgment before a single transfer operator gets built.

or simply put, we basically think that "style similarity: 0.81" is a meaningless number, because style isn't *a* thing. it's mark-making, shape language, color, texture, rendering, edges, and until each of those can be measured, moved, and *proven* to have moved without dragging the others along, style transfer is vibes with a progress bar. true controllability comes from properly decomposing, validating, and **transferring only the factor you asked for** the way an artist actually thinks, rather than regurgitating a mush of latent features from a diffusion bucket.

## the idea behind stylometrics

we started with the well known concept in computational linguistics that is stylometry: the statistical analysis of *how* something is made, not *what* it depicts. classic stylometry answers "who wrote this." illustrace aims to do that for pictures:

- can the visual construction rules of an illustration be turned into numbers?
- do humans agree with those numbers?
- can the numbers be moved one at a time, predictably?

instead of treating style transfer as one operation, it decomposes style into a factor space, measures each factor, and transfers only what was requested. each transfer declares what must change, declares what must not, and produces a delta vector proving both. the whole thesis sits in one word, **stylometrics**: style has to become measurable before it can become transferable.

## the problem with wholesale transfer

you tell an existing tool "keep my illustration, color it like this one." the tool doesn't know what you meant, so it imitates the *entire* reference, and you get:

- the reference's composition
- the reference's poses and objects
- the reference's layout and backgrounds
- the reference's typography
- decorative elements you never asked for
- ui screenshots interpreted as things to paint

for ui and illustration work that's not creative control, it's a slot machine. the missing piece is *intent*: users reference brush strokes, watercolor texture, line quality, rendering feel. they almost never mean "copy everything."

## what's the goal

a shift from single-scalar similarity ("strength: 70%" on a mystery knob) to per-factor control with formal invariants. each transfer is an explicit vector, like `{"stroke_roughness": 0.8, "palette": 0.0}`, and each run produces a delta vector across *all* factors: "moved 91% of the way toward the reference's stroke roughness while unrelated properties changed by less than 4%." that sentence is the actual scientific claim. collateral style change is a first-class measured thing, not a surprise.

stylebench, the benchmark underneath, evaluates whether an image generation or editing system can:

- identify visual style attributes
- selectively transfer requested attributes
- preserve non-requested attributes
- preserve source content
- prevent reference-content leakage
- combine attributes from multiple references
- provide predictable control over transfer strength

## pillars

style is hierarchical, not flat. the 2d decomposition (full detail in the [thesis](/research/STYLEBENCH_THESIS.md)):

- **mark-making**: stroke width, variation, taper, jitter, edge roughness
- **shape language**: angularity, roundness, simplification, exaggeration
- **color language**: palette, saturation, value range, temperature
- **texture language**: grain, frequency, directional texture
- **rendering language**: flatness, gradients, shading complexity
- **edge language**: hard/soft, clean/rough, outlined/unoutlined

plus a parallel 3d decomposition: geometry, construction, surface, color, shading, rendering.

we explicitly do **not** assume these are independent. discovering which factors are truly orthogonal is literally the benchmark's first job.

## asset vs set

one question surfaced early and became first-class: does the same asset carry the same style when it's alone versus staged in a set? the substrate answered it with a controlled pair (identical house, identical brush, identical seed):

- stroke width: scale-normalizable to ~1.6% after normalizing by subject size
- palette: stable at the asset anchor, genuinely different at the set anchor (zero new colors added, distance 0.7 vs 7.0)
- edge entropy: stable everywhere, first uncaveated parameter
- grain and lighting: **canvas-anchored vs subject-anchored is a recipe property**, and each anchor has a predictable scale law (canvas reads flat, subject reads linear in scale)

metrology got four rules out of it (reference-render masks, fixed supports, context exclusion, scale-invariant metric construction). full story in [results/](/results/).

## scope constraint

for v1 and a long while, illustrace lives strictly in **intentionally stylized / illustrated assets**:

- in scope: hand illustration, graphic illustration, icons, sprites, low-poly, voxel, storybook 3d
- out of scope: photorealism, semirealism, human identity, anatomy, unconstrained character generation, product try-on, mockups

this isn't a limitation, it's the laboratory: style in this domain is strongly designed, visible, and exaggerated, which makes "is this even measurable" tractable *before* touching likeness and realism.

and crucially: illustrace makes **presets, not static assets**. generated pieces stay editable, parametric, layered, figma-style adjustable. never a baked render you can't take apart again.

## baselines (a neutral benchmark, not a comparison page)

stylebench evaluates several classes of existing reference-based systems:

- reference-transfer
- diffusion-edit
- multi-reference
- component-conditioned

each receives the same target, reference(s), requested components, weights, and generation parameters, evaluated with the same metrics. the benchmark assumes no architecture is correct.

baselines are simply named `baseline_001`, `baseline_002`, `baseline_003`, and `illustrace_v0`. no competitor names anywhere: illustrace shouldn't be defined as "the thing better than x," it should be defined by the measurable problem it's solving.

## where this sits (honesty first)

content/style disentanglement, reference-based generation, controllable editing, multi-reference conditioning all exist. illustrace does not claim to have invented style decomposition. the novel-ish angle is:

- the benchmark itself (per-factor claims, invariants, delta vectors)
- granularity (asset vs set, anchors with declared scale laws)
- the evaluation methodology (validate against human judgment before operators)
- illustration-specific focus

## what exists so far

a fully deterministic engine, nothing neural, on purpose. current hard numbers: 87 tests passing, 46 candidate parameters in the registry, 5 validated, 4 controlled research runs.

- `engine/analyzer.py` + `engine/texture_gt.py`: style measurements on raster and on vector-ground-truth fill regions (the scale-invariant construction)
- `engine/operators.py`: one transfer operator so far, palette transfer with strength-as-distance-traveled
- `engine/registry.py`: the parameter registry as code, renders `results/PARAMETER_MATRIX.md` with a status ladder (candidate → measurable → validated → controllable)
- `benchmarks/`: controlled stimulus pairs where exactly one style factor changes, plus the parametric svg substrate (brush recipes, texture, lighting) that serves as ground truth
- `research/STYLE_ONTOLOGY.md`: the ten-dimension decomposition, the granularity question, the metrology rules
- `survey/`: pairwise forced-choice human-judgment app (catch pairs, confidence, ingest + validation), built and tested, validation runs pending
- `xano/`: control-plane toolkit mirroring every run
- `results/`: the run records: fidelity, granularity, anchor, texture ground truth

next in research-first order: the test-1 batch on remaining candidates (value_range, stroke_directionality, shape_complexity), then human-judgment validation, because a metric that doesn't track what a human calls "rougher linework" is just a number wearing a lab coat.

## where it breaks (honest)

- **no metric is human-validated yet.** the survey tool exists; the validation study has not run. until it does, "validated" means internally consistent under ground truth, not artist-agreed.
- **one transfer operator.** palette v0. the interesting operators (stroke, texture) are deliberately queued behind validation.
- **2d svg substrate only.** the 3d decomposition lives in research; nothing renders it.
- **stylized-only scope.** findings may not transfer to photorealism; that's fine, it's excluded on purpose.

## where things live

```
application/   style composer, the pilot tool this research is for
benchmarks/    stimulus pairs + the parametric svg substrate
engine/        analyzer, metrics, operators, registry, texture ground truth
research/      thesis, ontology, prior art, editable-presets thread
results/       run records + the parameter matrix
survey/        human-judgment validation app
tests/         87 offline tests
xano/          control-plane toolkit
```

## the application layer

research without a tool at the end is a hobby. `application/` holds **style composer**, the pilot application of stylebench:

- per-component transfer: stroke yes, composition no
- independent strength sliders per component
- references mixed across components (stroke from a, color from b)
- presets that store *recipes, not rendered images*

the full concept doc lives in [application/README.md](/application/README.md).

## reference points (not affiliations)

nothing here is a flagship of anything. illustrace is a research project that thinks style should be measurable. reference points it keeps around: *nova3d* for where parametric preset styles could eventually go, *openscad* for programmatic geometry done right, and classic *stylometry* (the computational linguistics kind) for the whole "measure how something is made" attitude.
