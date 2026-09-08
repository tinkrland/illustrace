# arch stimuli run 1 — 2026-09-08

stimuli: `data/generated/arch/` (A–H, 2x2x2 factorial: palette x stroke x texture)
palette provenance: measured k-means palettes of ref_01 (warm riso) and ref_02 (cool
ink), roles assigned deterministically (bg = lightest, stroke = darkest, etc).
same composition/seed throughout; only factors move.

## pair separation vs base A (p1, clean, flat)

| check | value | expectation | verdict |
|---|---|---|---|
| palette dist A-B (palette-only) | 0.1803 | large | pass |
| palette dist A-C (stroke-only) | 0.0008 | ~0 | pass |
| palette dist A-D (texture-only) | 0.0032 | ~0 | pass |
| stroke cv A vs C | 0.198 → 0.333 | C >> A | pass |
| edge entropy A vs C | 0.836 → 0.955 | C > A | pass |
| stroke cv drift A-B | 0.006 | ~0 | pass |
| edge entropy drift A-B | 0.001 | ~0 | pass |
| texture energy A vs D | 5.2 → 10.4 | D >> A | pass |
| texture drift A-C | 0.2 | ~0 | pass |
| stroke cv drift A-D | **0.094** | ~0 | **FAIL** |
| edge entropy drift A-D | **0.109** | ~0 | **FAIL** |

## the finding

texture is not yet independent of stroke: adding grain to the fill layer leaks into
stroke measurements (stroke cv drift 0.094, edge entropy drift 0.109). root cause:
`stroke_mask` defines linework as "dark and unsaturated", so grain speckle in dark
fills counts as stroke pixels. this is exactly what a controlled bench is supposed to
catch — the *stimulus* is fine, the *analyzer* conflates two factors.

## next analyzer iteration (before any operator work)

- stroke_mask needs a thinness/connectivity constraint: linework = elongated connected
  components (distance transform width < some max), grain = speckle. filters grain out.
- or: compute stroke metrics after excluding `texture_energy` regions.
- regression pair for the fix: A-D must show stroke cv drift ~0 while texture doubles.

## interpretation

two of three candidate factors (palette, stroke) now separate cleanly on a
non-character subject with reference-derived palettes. one measurement confound
discovered and specified. human-judgment validation still pending — these numbers say
the machine can see the factors, not that humans agree. stimulus set ready for that
benchmark.
