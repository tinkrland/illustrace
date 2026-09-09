# illustrace

illustrace tackles the widespread assumption that art style is an undifferentiated latent blob by treating style as a hierarchical, measurable, and independently manipulable system of visual factors—validated against human judgment before a single transfer operator gets built.

or simply put, we basically think that "style similarity: 0.81" is a meaningless number, because style isn't *a* thing. it's mark-making, shape language, color, texture, rendering, edges—and until each of those can be measured, moved, and *proven* to have moved without dragging the others along, style transfer is vibes with a progress bar. true controllability comes from properly decomposing, validating, and **transferring only the factor you asked for** the way an artist actually thinks, rather than regurgitating a mush of latent features from a diffusion bucket.

## the idea behind stylometrics
we started with the well known concept in computational linguistics that is stylometry—the statistical analysis of *how* something is made, not *what* it depicts. while classic stylometry answers "who wrote this," illustrace aims to do that for pictures: can the visual construction rules of an illustration be turned into numbers that humans agree with?

instead of treating style transfer as one operation, it decomposes style into a factor space, measures each factor, and only transfers what was requested. it's essentially giving style transfer the computational equivalent of a controlled experiment—declare what must change, declare what must not, and produce a delta vector proving both.

the goal behind illustrace is the concept we refer to as stylometrics since it captures the entire thesis in a single word—style has to become measurable before it can become transferable. we aim to completely bypass the "just fine-tune a model on it" jargon and hit right at the core of what illustrace is keen on doing: giving visual style an explicit, inspectable, editable representation instead of a frozen one.

## where this sits (honesty first)
existing approaches demonstrate that visual characteristics can be extracted, represented, or conditioned independently — content/style disentanglement, reference-based generation, controllable image editing, multi-reference conditioning, artistic style transfer. illustrace does not claim to have invented style decomposition.

the novel-ish angle is the particular benchmark + granularity + evaluation methodology + illustration-specific focus. stylebench investigates how reliably those characteristics can be **isolated, selectively transferred, recombined, and quantitatively evaluated in hand-illustrated imagery.**

## what's the goal
the goal is a shift in style transfer from single-scalar similarity (like "strength: 70%" on a mystery knob) to per-factor control with formal invariants. each transfer is an explicit vector—`{"stroke_roughness": 0.8, "palette": 0.0}`—and each run produces a delta vector across *all* factors: "moved 91% of the way toward the reference's stroke roughness while unrelated properties changed by less than 4%." that sentence is the actual scientific claim. collateral style change is a first-class measured thing, not a surprise.

stylebench, the benchmark underneath, evaluates whether an image generation or image-editing system can:

1. identify visual style attributes
2. selectively transfer requested attributes
3. preserve non-requested attributes
4. preserve source content
5. prevent reference-content leakage
6. combine attributes from multiple references
7. provide predictable control over transfer strength

## baselines (a neutral benchmark, not a comparison page)
stylebench evaluates multiple classes of existing reference-based image generation and editing systems — reference-transfer, diffusion-edit, multi-reference, component-conditioned. each system receives the same target image, reference image(s), requested component(s), component weights, and generation parameters, and outputs are evaluated with the same metrics. the benchmark does not assume that any particular architecture is correct.

baselines are simply named `baseline_001`, `baseline_002`, `baseline_003` … and `illustrace_v0`. no competitor names anywhere — illustrace shouldn't be defined as "the thing that's better than x." it should be defined by the measurable problem it's solving.

## pillars
as defined thoroughly in the [thesis](/research/STYLEBENCH_THESIS.md), style is hierarchical, not flat:
- **mark-making** — stroke width, variation, taper, jitter, edge roughness
- **shape language** — angularity, roundness, simplification, exaggeration
- **color language** — palette, saturation, value range, temperature
- **texture language** — grain, frequency, directional texture
- **rendering language** — flatness, gradients, shading complexity
- **edge language** — hard/soft, clean/rough, outlined/unoutlined

(and a full parallel decomposition for 3d: geometry, construction, surface, color, shading, rendering languages)

we explicitly do **not** assume these are independent. discovering which factors are truly orthogonal is literally the benchmark's first job.

## scope constraint
for v1 and a long while, illustrace lives strictly in **intentionally stylized / illustrated assets**—hand illustration, graphic illustration, icons, sprites, low-poly, voxel, storybook 3d. no photorealism, no semirealism, no human identity, no anatomy, no unconstrained character generation, no product try-on, no mockups. this isn't a limitation, it's the laboratory: style in this domain is strongly designed, visible, and exaggerated, which makes "is this even measurable" tractable *before* touching the nastier problems of likeness and realism.

and crucially: illustrace makes **presets, not static assets**. the goal is for generated pieces to stay editable — parametric, layered, figma-style adjustable — rather than baked into a render you can't take apart again.

## what exists so far
an embarrassingly small, fully deterministic engine (nothing neural yet, on purpose):
- `engine/analyzer.py` — four candidate style measurements: palette, stroke width variation, edge direction entropy, texture energy. candidates, not validated factors yet.
- `engine/operators.py` — one transfer operator: palette transfer with soft cluster membership and strength-as-distance-traveled.
- `research/STYLE_ONTOLOGY.md` — the decomposition: ten dimensions, the parameter status ladder, the research matrix, and the granularity question (asset vs set)
- `engine/registry.py` — the parameter registry as code (renders `results/PARAMETER_MATRIX.md`)
- `benchmarks/` — controlled stimulus pairs where exactly one style factor changes; if the analyzer can't tell them apart, nothing downstream matters.
- `benchmarks/svg_house.py` — the same house as a layered, parametric svg (brush recipes, texture filter, lighting overlay) — editable substrate + measurement-fidelity bench.
- `engine/metrics.py` — requested fidelity + non-target preservation, the first two invariants.
- `application/` — style composer, the practical tool that applies the research
- `xano/` — a queryable control plane mirroring every run.

next up (in research-first order): rebuild stimuli on architecture/interior subjects from `data/references/`, then run the human-judgment validation benchmark — because a metric that doesn't track what a human calls "rougher linework" is just a number wearing a lab coat.

## the application layer
research without a tool at the end is a hobby. `application/` holds **style composer** —
the pilot application of stylebench: per-component transfer (stroke yes, composition no),
independent strength sliders per component, multiple references mixed across components,
and reusable presets that store *recipes, not rendered images*. the whole concept doc
lives in [application/README.md](/application/README.md).

## reference points (not affiliations)
nothing here is a flagship of anything — illustrace is just a research project that thinks style should be measurable. a few good reference points it keeps around: *nova3d* for where parametric preset styles could eventually go, *openscad* for programmatic geometry done right, and classic *stylometry* (the computational linguistics kind) for the whole "measure how something is made" attitude.
