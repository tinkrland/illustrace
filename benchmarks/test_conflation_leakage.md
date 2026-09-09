---
status: draft test design, not yet implemented
baseline class: component-conditioned
---

# conflation leakage test (content bleed through style buckets)

## the claim under test

stylebench claim: *prevent reference-content leakage* — when a system is asked to
transfer only style, nothing from the reference's content may appear in the output.

the case targets a specific architectural pattern observed in the wild: systems
that decompose a reference into a flat bucket list where content attributes
(appearance, outfit, pose, composition, environment) sit alongside style
attributes (color grading) with no content/style boundary declared. the working
hypothesis: **when the ontology conflates content and style, bucket-level
selection cannot prevent content bleed**, because the system has no representation
of what must never move.

## design principle: disjoint by construction

the stimulus pair is built so that target and reference share *zero* content:

- target: an architecture/interior subject from the current in-scope set
- reference: a different subject class entirely (e.g. flora/objects), carrying a
  strongly distinctive palette + texture + stroke signature, a deliberately
  loud layout, and one or two signature objects (an anchor motif)

if the system truly transfers only style, the output is the target subject
re-colored/texture-swapped. any drift toward the reference's subject, layout, or
anchor motif is unambiguous leakage — there is no incidental-overlap excuse.

## procedure (four arms, same seed, same prompt, same params)

1. **style-bucket arm**: transfer the style bucket only (e.g. color grading)
2. **all-together arm**: transfer everything the system can extract
3. **no-reference arm**: same prompt, no style conditioning — the content baseline
4. **catch arm**: transfer a *content* bucket explicitly (pose/outfit), which should
   move content — verifies the system's buckets do anything at all

## measurements (delta vector, registry-tied)

requested factor (per arm 1, palette/color grading):

- palette distance must move toward the reference by the requested strength,
  tolerance band as in the existing palette operator spec

non-requested factors must hold (arm 1, the actual test):

- content fidelity vs the no-reference arm: object count, spatial layout
  distance (region-overlap), silhouette difference
- **anchor motif detector**: the signature object appears in output at all = fail,
  binary, no threshold arguments
- edge entropy, stroke width cv, texture energy: within noise band of the
  no-reference arm

arm 2 quantifies how much worse all-together is (expected: full bleed), arm 3
calibrates the noise bands, arm 4 rules out "buckets are inert" as an excuse.

## human validation

pairwise forced choice through the survey app:

- "which output looks more like the *target* subject?" (arm 1 vs arm 3) — expect
  no significant preference, else humans see content drift
- "which output borrows more from the *reference*?" (arm 1 vs arm 2) — expect
  arm 2, confirming the reference is visible to judges and the instrument works

## pass criteria

- arm 1: requested factor moves ≥ the declared strength minus tolerance
- arm 1: every content metric inside the no-reference noise band, anchor motif
  absent, on ≥ 90% of seeds
- arms 2 and 4 behave as expected (bleed happens; buckets act)

a system passing arms 1–4 with a conflated ontology would falsify the working
hypothesis — also a useful result, it would say the boundary can be learned
implicitly.

## why this matters for illustrace_v0

illustrace's decomposition declares subject/pose/layout as content, never
transferable by default. this case is the adversarial twin of that invariant:
the benchmark asks the conflated ontology to do something it never promised,
and measures exactly how much of the reference's world leaks through.
