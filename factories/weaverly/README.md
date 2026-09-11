# weaverly (stitch factory)

the media-translation factory. it takes an asset and renders it into stitched media: cross-stitch, embroidery, needlepoint, beadwork, pixel-art. the pinterest-core aesthetic of embroidered and cross-stitched logos exists because the medium is charming; but today you either hand-embroider it or you apply a fake filter. weaverly makes it a real, structured translation with editable output.

## what it makes

- pixelated / gridded conversions of any asset (marks, icons, type) at chosen stitch counts and grid densities
- embroidery-style treatments: satin-stitch fills, running-stitch outlines, applique layers
- thread palettes: real thread-brand color systems, so the palette is chosen in dmc-anchor space, not rgb
- charts: exportable stitch charts (cross-stitch pdfs, pixel grids) alongside the layered vector

## provenance

named after karla's weaverly (https://github.com/kqrla/weaverly, same-project-team, perms confirmed). note: as of 2026-09-11 the repo is not publicly visible, so pull from the team when this factory starts. adjacent adoptable techniques live in the fontasy family: fontasy-mask's fabric patterns, edge stitching, and grain overlays, and fontasy_fork's bead and texture modes.

## the editable-preset contract

the stitch grid is a parameter layer over the source asset, not a destructive rasterize: change the source mark, the stitching follows. stitch density, thread palette, fill style, and outline treatment are all recipe parameters.

## studio role

weaverly is a finisher: anything the studio composes (a logomark, a wordmark, a crest) can leave through it as a stitched artifact.

## status

parked. readme only, no build.
