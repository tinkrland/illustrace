# patterns (pattern factory)

the repeat factory. seamless repeating patterns as editable presets: tiles, half-drops, brick offsets, thrown/tossed layouts. the motif set comes from other factories (a blob, a stitch, a filigree sprig, a glyph) and the pattern factory is the engine that makes it repeat without visible seams.

## what it makes

- seamless tiles in standard repeat systems: block, brick, half-drop, mirror, tossed
- density, scale, rotation-jitter, and overlap parameters as the layout recipe
- motif libraries: a pattern is (motif set) + (layout recipe) + (colorway), each swappable independently

## the editable-preset contract

a pattern is a live program: change the motif and every repeat updates; change the colorway and the tile re-renders. export as tileable svg/png plus a live preview, never a flattened screenshot of one crop.

## why a dedicated factory

seamlessness is a hard, checkable invariant (edge matching), and repeat systems are a compact, well-studied parameter space. that makes this a good early candidate when factories start getting built: small surface, crisp contract, composes with everything.

## studio role

patterns are the studio's surface treatment: wrap the seal, fill the packaging, become the fabric that fontasy-mask lettering sits on.

## status

parked. readme only, no build.
