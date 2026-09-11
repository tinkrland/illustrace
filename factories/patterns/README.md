# patterns (pattern and surface design factory)

the repeat and surface factory. seamless repeating patterns as editable presets: tiles, half-drops, brick offsets, thrown/tossed layouts. and surface design, the composed-surface lane: the applied end of patterns, endpapers, wrapping paper, wallpaper, textile prints, packaging faces, where the surface is a *composition*, not just a tile stamp repeated to the edges. the motif set comes from other factories (a blob, a stitch, a filigree sprig, a glyph) and the pattern factory is the engine that makes it repeat, or compose, without visible seams.

## what it makes

the pattern lane:

- seamless tiles in standard repeat systems: block, brick, half-drop, mirror, tossed
- density, scale, rotation-jitter, and overlap parameters as the layout recipe
- motif libraries: a pattern is (motif set) + (layout recipe) + (colorway), each swappable independently

the surface design lane:

- composed surfaces with intent: placement prints (the one big motif on the tee, the asymmetric wrap), framed panels, borders and fills, scenes and vignettes
- surface-aware constraints: a design knows its substrate dimensions and safe areas (a phone case is not a bolt of fabric), so it composes to the actual surface rather than tiling blindly
- both lanes share the motif libraries and colorways: the same motif set can leave as a seamless tile or as a composed surface

## the editable-preset contract

a pattern is a live program: change the motif and every repeat updates; change the colorway and the tile re-renders. export as tileable svg/png plus a live preview, never a flattened screenshot of one crop.

## why a dedicated factory

seamlessness is a hard, checkable invariant (edge matching), repeat systems are a compact, well-studied parameter space, and surface fit (does the composition actually work on this substrate) is checkable too. that makes this a good early candidate when factories start getting built: small surface, crisp contract, composes with everything.

## studio role

patterns and surfaces are the studio's applied layer: wrap the seal, fill the packaging, become the fabric that fontasy-mask lettering sits on, become the endpaper of the thing, the wrap of the gift, the face of the box. any composed identity can leave through this factory as an applied surface, not just a flat asset.

## status

parked. readme only, no build.
