# ingest test: fontasy_fork color zones over whole illustrations

run 2026-09-09. harness: `scripts/fork_ingest_test.mjs` — runs kqrla/fontasy_fork's
raster→vector pipeline (k-means color zones → moore boundary trace →
douglas-peucker → catmull-rom bezier, plus hole detection) verbatim, with two
labeled INGEST adaptations: (1) paper-color background mask replaces the
otsu ink threshold (illustrations are washes, not letter scans), (2) every
connected component of every color zone gets traced (the fork traces one
component per glyph).

## results

| ref | k | paths | time | mean rgb l2 err (of 441) |
|---|---|---|---|---|
| ref_20 (loose ink + light wash) | 6 | 1165 | 549ms | 111.6 |
| ref_22 (watercolor + ink storefront) | 6 | 1381 | 832ms | 114.2 |

zone palettes came out plausible on both: ref_22 = white #e4dfda, blue
#86a5d0, near-black ink #161111, tan #f2d8af, two grays — a correct reading
of a flat-color storefront. ref_20's zones went muddy: rgb-space k-means on
continuous watercolor washes clusters paper-shade tones (a near-white
#eae8e4 zone of 73k px) instead of paint regions.

## read

- **flat-color / posterized styles: adopt as-is.** the storefront traces
  structurally clean; per-zone paths with per-zone colors is exactly the
  transfer-engine ingestion target (the vtracer "suppress color merging"
  modification, already solved).
- **continuous-wash styles: not solved by rgb k-means alone.** watercolor
  needs either lab-space clustering, edge-aware clustering (watershed on
  gradient), or wash-as-texture-layer treatment (the wash isn't a color
  zone, it's a bucket-07 recipe applied over zones). the muddy result on
  ref_20 is a boundary finding, not a blocker: fontasy's own color zones
  were built for poster-style lettering, not washes.
- the fork's trace stack itself is solid: holes handled, components
  <12px dropped cleanly, 1200+ paths traced in <1s per image.

files: `ref_20_zones.svg`, `ref_22_zones.svg` (editable vector output — open
in any editor, each region a selectable path), `*_stats.json`,
`contact_sheet.png` (reference vs reconstruction, both refs).
