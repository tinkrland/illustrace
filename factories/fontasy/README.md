# fontasy (font factory)

the font factory. it generates complete, usable, editable typefaces, which are arguably the purest expression of the whole editable-preset principle: a glyph is a parametric vector path, spacing and kerning are parameters, color zones and texture are recipe layers stacked on top. nothing about a font is a static render until you deliberately flatten it.

## what it makes

- full editable typefaces: glyph paths, spacing/kerning parameters, opentype features
- glyph sheets: every glyph as a layered, recolorable, individually overridable vector
- wordmarks: type plus per-glyph edits locked into an editable composition

outputs ship as real font files (.otf, .ttf, .woff, .woff2) *and* as the layered source that generated them. the font file is an export; the source is the asset.

## adoption terms (how much can be taken)

everything. this is the most takeable factory in the folder. the source projects are same-project-team work (karla's), permission to use the code was confirmed outright on 2026-09-09, and all three repos are MIT, so they are citable by name in public docs as well. concretely:

- **code can be reused wholesale**, cloned into `vendor/` when the build starts, not just studied
- **techniques are adoptable with attribution**: fontasy_fork's k-means color zones (the adoptable per-region vectorization path), bead and texture modes; fontasy-mask's pattern-as-mask, edge stitching, grain overlays, and per-letter overrides
- **ui patterns are a proven shape worth copying**: the figma plugin + standalone web app split that all three repos share

see `research/OSS_TOOL_SCAN.md` for the full scan and `research/STYLE_ONTOLOGY.md` for the typography decision that brought word-bearing outputs into scope: only the editable forms count; flattened static renders of type stay a non-goal.

## why a factory and not a transfer bucket

typography is a disabled-by-default transfer bucket because a reference's typeface is its *content*, not its style. but generating a font from scratch, in the user's parameters, is a different act entirely: nothing is being copied, the user is authoring. that's exactly the factory lane.

## studio role

the font factory is the anchor tenant of the factory studio: a wordmark from here drops next to a blob from inkora or a crest from sigilry and the composition stays live and editable end to end.

## status

parked. readme only, no build. when it starts, the build section grows here.
