---
status: internal research note — name-free by design
---

# prior-art observations (internal)

competitive / prior-art notes, kept name-free in the project by design. capability
observations only; which specific systems showed which capability stays in private
research notes, not in the repo, docs, benchmark naming, or public framing.

## observed capabilities in the wild

- multi-reference conditioning exists
- reference attribute extraction exists — reference images can be decomposed into
  named buckets (appearance, outfit/clothing, pose, color grading, composition,
  environment/background) and extracted either all together or bucket-by-bucket
- extraction fidelity is exposed as a binary mode (two named presets, not a
  continuous dial) — contrasts with a continuous per-component strength design
- visual attribute controls exist, but as generic scene/mood sliders
  (complexity, distance, lighting, mood, motion) decoupled entirely from any
  style ontology — a separate "vibe" axis, not decomposition of style itself
- decomposition, where it exists, applies to the *reference input being fed in*,
  not to the *trained/selected style* — picking a style from a library remains a
  monolithic choice (thumbnail in, no parameters exposed on the style itself);
  only the conditioning reference gets attribute-decomposed
- generation methods can be conditionally gated by style/model compatibility
  (a given style may not support a given generation mode) — a compatibility
  matrix, not a controllability feature

## open questions to investigate against existing systems

- how well do existing systems isolate individual attributes?
- is there reference-content leakage (unwanted content/subject bleeding from the
  reference into the output)?
- how controllable is each individual attribute, independently? (binary
  creative/precise modes suggest coarse control at best)
- does transfer strength behave predictably (requested % vs measured %)?
- when a bucket taxonomy mixes content attributes (pose, outfit) with style
  attributes (color grading) in one flat list, does that conflate content and
  style in ways illustrace's decomposition explicitly avoids?

these observations inform test-case design only. stylebench remains a neutral
benchmark: baselines are `baseline_001`, `baseline_002`, ... by class
(reference-transfer, diffusion-edit, multi-reference, component-conditioned) plus
`illustrace_v0`, all scored identically.

## adapter layout (planned)

```
/stylebench
  /baselines
    /reference-transfer
    /diffusion-edit
    /multi-reference
    /component-conditioned
    /illustrace
```
