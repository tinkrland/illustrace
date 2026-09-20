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

the core engine is deterministic on purpose; the learned layers around it (the llm compiler, the style adapters) exist to be *constrained* by it, not to replace it. flux shows up below as one substrate the adapter lane trains on, nothing more: the benchmark scores any generator or editor, the classical operators run with no generator at all, and a different backbone would not change a single claim. current hard numbers: 178 tests passing, 46 parameters in the registry, 7 validated, 4 controlled research runs.

- style measurements on raster and on vector-ground-truth fill regions (the scale-invariant construction), [here](/engine/analyzer.py) and [here](/engine/texture_gt.py)
- the classical operator set: palette, stroke, texture, edge, value, color-zone, shading. strength-as-distance-traveled on each, independence checked against measured noise floors, [here](/engine/operators.py)
- the **diffusion noise floor protocol**: no-op jitter ladders (resample, warp, grain, bleed, unsharp, tint, webp, and the combo proxy) that give every metric an uncertainty bar before any operator effect gets believed, [here](/engine/noise_floor.py)
- the parameter registry as code, renders a status ladder (candidate → measurable → validated → controllable) into [the parameter matrix](/results/PARAMETER_MATRIX.md), registry lives [here](/engine/registry.py)
- controlled stimulus pairs where exactly one style factor changes, plus the parametric svg substrate (brush recipes, texture, lighting) that serves as ground truth, [here](/benchmarks)
- the ten-dimension decomposition, the granularity question, the metrology rules, [here](/research/STYLE_ONTOLOGY.md)
- the human-judgment lane, built and waiting on judges: pairwise forced-choice survey app (catch pairs, confidence, ingest + validation), an early pilot judged (directional), and batches 2–4 packaged for the full study, [here](/survey)
- the **llm semantic compiler**: plain-language style hypothesis in, schema-valid preregistration spec out (validator-enforced, never auto-promoted), plus a langsmith eval ledger and the qlora path for a spec/judge model, [here](/llm)
- the **style lora engine**: public-domain painter corpora ingested from wikidata (monet, van gogh, hokusai), measured into inspo profiles, an adapter probe that scores style fidelity with cie76 deltae in lab space (self-test passes at dE 0.0, cross-artist fails at dE 38.5, so it catches leakage), a kohya packaging spec, and a node-based composer ui with strength wires, [here](/research/STYLE_LORA_ENGINE.md) and [here](/engine)
- the **gpu runner lane**: a xano job queue with a non-rewindable ledger, a pull-model runner that trains kohya flux style-loras on an a100, and a preregistered fitter ladder (fx0 measurability to fx3 real-image transfer), [here](/runner) and [here](/research/FITTER_EXPERIMENTS.md)
- control-plane toolkit mirroring every run, judgment, job, graph, and preset, eight live tables, [here](/xano)
- the run records: fidelity, granularity, anchor, texture ground truth, [here](/results)
- parked concept stubs: readme-only [factories](/factories) for editable-asset mini-generators (fonts, blobs, icons, weave), a future factory studio

the test-1 batch landed: value_range exact against the area mixture, stroke_directionality rotation-exact with a tie caveat, shape_complexity pinned to the vector source (raster proxies answered a 23% ground-truth change with 3%, which is the finding). next in research-first order: human-judgment validation, because a metric that doesn't track what a human calls "rougher linework" is just a number wearing a lab coat.

## where it breaks (honest)

- **human validation is pilot-stage.** one judge, 12 pairs: roughness, line weight, and color temperature track the metrics, taper got refuted, and the pilot caught two stimuli bugs (an inverted lighting prompt, a grain step below the perceptual floor). real, but pilot-stage; the full study is packaged and waiting on judges.
- **transfer operators are young.** palette, stroke, texture, edge, value, color-zone, shading exist as deterministic classical baselines; the learned operators are deliberately queued behind validation.
- **the learned layers are pre-training.** the llm compiler drafts specs, the adapter probe and composer exist, and the fitter ladder is preregistered, but nothing has trained yet (gpu provisioning in progress). the whole learned stack is design + queue, zero checkpoints.
- **2d svg substrate only.** the 3d decomposition lives in research; nothing renders it.
- **stylized-only scope.** findings may not transfer to photorealism; that's fine, it's excluded on purpose.

## where things live

```
application/   style composer, the pilot tool this research is for
benchmarks/    stimulus pairs + the parametric svg substrate
engine/        analyzer, metrics, operators, registry, inspo profiles, adapter probe
factories/     parked readme-only stubs (fonts, blobs, icons, weave)
llm/           semantic compiler + eval ledger + spec/judge qlora path
research/      thesis, ontology, prior art, lora engine, fitter ladder, editable-presets thread
runner/        the gpu runner (claims xano jobs, kohya flux loras, posts results)
results/       run records + the parameter matrix
survey/        human-judgment validation app (pilot judged, batches 2-4 packaged)
tests/         160 offline tests
xano/          control-plane toolkit (8 live tables, amd runner queue)
```

## the application layer

research without a tool at the end is a hobby. `application/` holds **style composer**, the pilot application of stylebench:

- per-component transfer: stroke yes, composition no
- independent strength sliders per component
- references mixed across components (stroke from a, color from b)
- presets that store *recipes, not rendered images*

the composer is node-based, and every node carries two axes kept separate on purpose: **priority order** and **influence**. priority order settles fights: when two nodes claim the same pixels, the order decides who paints first and who blends under. influence decides reach: how far a reference's say extends, scoped to the factor it was wired to, so a stroke reference can set the linework without leaking its palette or composition into everything downstream. that scoping is the anti-bleed design: multi-image, multi-parameter inspo (stroke from a, color from b, edges from c) is the whole point, and the known failure mode of multi-reference systems is precisely that the references bleed into each other. here a reference never attaches to "the image," it attaches to a factor node, with an influence slider, in a priority lane, and the benchmark's leakage claim measures whether that actually held.

the full concept doc lives in [application/README.md](/application/README.md).

## reference points (not affiliations)

nothing here is a flagship of anything. illustrace is a research project that thinks style should be measurable. it isn't part of a program or ecosystem; these are just reference points it keeps around, nothing more:

| reference | why it's here |
|---|---|
| classic *stylometry* | the computational linguistics kind, for the whole "measure how something is made" attitude |
| *metrology* | the measurement-science attitude: every claim carries an uncertainty bar, which is what the noise floors are |

(the 3d thread keeps its own references in the [editable-presets research](/research/EDITABLE_PRESETS_RESEARCH.md).)
