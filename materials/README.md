# materials

> status: researched, unseeded. candidates only.

what do the depicted things read as being made of?

wood, metal, fabric, glass, water, fur, stone. not the marks (render), not the pattern covering the surface (textures, one of the cues materials are built from), but the substance itself: what the surface says it is when you look at its highlights, its edges, its light behavior.

## the material bundle

a material in 2d is a bundle of simultaneous cues: surface finish (matte to gloss), light behavior (absorb, diffuse, specular, transmit), edge identity (crisp, fuzzy, refracting), and optionally a texture from the textures/ folder. change any one cue and the substance changes. this is why materials is its own folder: no single other axis cluster can say "this is metal" or "this is glass", because substance is a *conjunction*, and conjunctions need their own vocabulary.

the rendering industry agrees: material properties in 3d pipelines (BRDF terms: diffuse, specular, roughness, transmission, subsurface) are exactly this bundle, formalized. this folder is that vocabulary, drawn flat.

## the four axes

| axis | question |
|---|---|
| substance_family | what class of stuff is it? |
| surface_finish | how do highlights read: matte, satin, or gloss? |
| light_transport | what does light do inside it? |
| edge_identity | what kind of boundary does the object draw? |

definitions in `axes.md`. candidates in `canonical_tags.md`, all unseeded. synonyms in `synonyms.md`, all anticipated.

## honest scope

materials in 2d are *claims*, not physics. a flat illustration of chrome is three value shapes and one white slash. this folder catalogues the claims users ask for and the minimal cue sets that make them legible, not photoreal PBR. if a user asks for physically-accurate glass rendering they want a 3d renderer, not a wrangler vocabulary.
