---
status: internal research note — name-free by design
---

# prior-art observations (internal)

competitive / prior-art notes, kept name-free in the project by design. capability
observations only; which specific systems showed which capability stays in private
research notes, not in the repo, docs, benchmark naming, or public framing.

## observed capabilities in the wild

- multi-reference conditioning exists
- reference attribute extraction exists
- visual attribute controls exist

## open questions to investigate against existing systems

- how well do existing systems isolate individual attributes?
- is there reference-content leakage (unwanted content/subject bleeding from the
  reference into the output)?
- how controllable is each individual attribute, independently?
- does transfer strength behave predictably (requested % vs measured %)?

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
