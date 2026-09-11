# weaverly (stitch factory)

the media-translation factory. it takes an asset and renders it into textile media: cross-stitch, embroidery, weaving, lace, beadwork, plus ascii as an honorary member. the pinterest-core aesthetic of embroidered and cross-stitched logos exists because the medium is charming; but today you either hand-embroider it or you apply a fake filter. weaverly makes it a real, structured translation with editable output.

## the structural grammar insight (from the repo)

named after karla's weaverly (https://github.com/kqrla/weaverly, same-project-team, perms confirmed, typescript). its core thesis, adopted wholesale: these are not one filter with different skins. each medium obeys a completely different structural grammar and needs a fundamentally separate generation engine:

- **cross-stitch** = discrete embroidery lattice
- **weaving** = over-under thread simulation
- **lace** = recursive radial connectivity
- **beadwork** = clustered bead topology
- **ascii** = terminal flow logic

the repo is building cross-stitch first, and its corrections there are the discipline this factory inherits: every stitch snaps to a discrete cell, no floating placements, no subpixel positioning, patterns emerge from stitch repetition, woven density, thread pathways, and loom constraints. constrained, cellular, woven, tactile, never a free-floating glyph cloud.

## what it makes

- grid-true stitched conversions of any asset (marks, icons, type) at chosen stitch counts and lattice densities
- weaving, lace, and beadwork modes once their engines exist, each faithful to its own grammar
- thread palettes: real thread-brand color systems, so the palette is chosen in dmc-anchor space, not rgb
- charts: exportable stitch charts (cross-stitch pdfs, pixel grids) alongside the layered vector

adjacent adoptable techniques live in the fontasy family: fontasy-mask's fabric patterns, edge stitching, and grain overlays, and fontasy_fork's bead and texture modes.

## the editable-preset contract

the stitch lattice is a parameter layer over the source asset, not a destructive rasterize: change the source mark, the stitching follows. lattice density, thread palette, fill style, and outline treatment are all recipe parameters, and the grammar constraint (grid discipline per medium) is enforced by the engine, not by vibes.

## studio role

weaverly is a finisher: anything the studio composes (a logomark, a wordmark, a crest) can leave through it as a stitched artifact.

## status

parked. readme only, no build.
