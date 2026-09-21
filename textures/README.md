# textures

> status: researched, unseeded. candidates only.

what covers the surface of the depicted things?

not what the marks did to the picture plane (that is render, whose surface_texture axis stays binary: does texture exist at all). this folder is about the *depicted world*: what pattern, grain, or structure the drawn surfaces say they carry. stipple on a shirt, wood grain on a table, scales on a fish, weave on a basket.

## why this is separate from render

"stippled" can mean a mark structure (dots as marks, render) or a depicted fabric pattern (dots as design on a vest). the difference is what the dots are *being*, not what they look like. render owns the picture plane. textures owns the surface of the depicted things. a block_fill image (render) can carry a full weave pattern on every region, and a pastel_open image can depict surfaces with no texture at all.

the relationship to materials: a texture is one of the cues a material is built from. you can ask for a texture with no material behind it ("speckled fill") or a material with no pattern texture at all ("make it read as glass", which is highlights and transparency, not grain). so they are two folders, and this one is the pattern grammar.

## the four axes

| axis | question |
|---|---|
| pattern_basis | what generates the texture: repeated marks, geometric units, organic flow, or noise? |
| unit_scale | how big is the texture unit relative to the object it covers? |
| regularity | grid-strict, drifting, or organic scatter? |
| form_following | does the texture decorate flatly or model the surface's volume? |

definitions in `axes.md`. candidates in `canonical_tags.md`, all unseeded. synonyms in `synonyms.md`, all anticipated, and expect the heaviest cross-domain traffic with render (grainy, rough, textured all commute between the two).
