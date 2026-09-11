# factories

factories are illustrace's answer to a simple observation: people don't just want styles transferred onto existing art, they want *editable assets generated in a style*. a factory is a small, focused generator that produces one family of editable assets, and only that family. fonts from the font factory, blobs from the blob factory, seals from the seal factory. each one is a mini-specialist, not a general model.

or simply put: a factory is where an editable preset gets *born* instead of transferred. the style composer moves factors between images; a factory synthesizes a fresh asset from parameters alone, with no source image required at all.

## the one rule

every factory output must be an editable preset, never a flattened render. a font ships as glyph paths plus spacing and kerning parameters plus color-zone and texture recipe layers. a blob ships as a parametric outline with draggable control points. a seal ships as a layered vector with per-layer overrides. the flattened png is an export *from* the asset, not the asset. this is the same rule the whole project runs on, applied to generation instead of transfer.

## the second rule (the intent rule)

factories are browsing surfaces, not slot machines. randomize buttons are fine as a way to *explore* a parameter space, but the moment an asset is saved, what gets saved is the deterministic program: the parameters, the seed, the manual edits. reopening it reproduces exactly what you saw. no "look what the ai made" energy, ever. the user is the sole architect of the mental image; the factory is a high-intent execution engine that makes that image come forth.

## factory studio (the future composition surface)

the long game is a studio where factory outputs compose: a wordmark from the font factory, an organic mark from the blob factory, a seal around it from the sigil factory, all as live editable presets that recolor and restyle together like figma components. logomarks, brand kits, poster systems. this is parked for now; the factories come first, the studio comes when there are enough factories worth composing.

## the floor plan

| factory | makes | status |
| --- | --- | --- |
| [fontasy](/factories/fontasy) | fonts, glyph sheets, wordmarks | parked, readme only |
| [inkora](/factories/inkora) | abstract blobs, flowy botanicals, futuristic geometry | parked, readme only |
| [ikonic](/factories/ikonic) | consistent-style icon kits | parked, readme only |
| [weaverly](/factories/weaverly) | stitched, woven, laced, beaded media | parked, readme only |
| [analogistry](/factories/analogistry) | analog print process treatments | parked, readme only |
| [sigilry](/factories/sigilry) | emblems, seals, stamps, monograms, crests | parked, readme only |
| [patterns](/factories/patterns) | repeat patterns and tiles | parked, readme only |
| [filigree](/factories/filigree) | flourishes, ornaments, decorative detail | parked, readme only |

## status

this whole folder is a parking lot. readmes are written so the ideas keep their shape; no build work is scheduled. when a factory starts, its readme becomes its spec and grows a build section.
