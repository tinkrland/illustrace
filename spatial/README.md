# spatial

> status: researched, unseeded. candidates only.

how is depth built, and which marks belong to which layer?

that is the question here. not where the camera is (that is construction) and not what the marks look like (that is render). what the picture does with near and far.

## why this is separate from construction

you can have perfect one-point construction with no atmospheric depth at all (technical line drawing), and you can have flat parallel construction with rich layering (paper cutout). construction is the geometry of the camera. spatial is the treatment of distance. they correlate in real photographs and decouple constantly in illustration, which is exactly why they need separate axes.

## the four axes

| axis | question |
|---|---|
| depth_model | is depth continuous, layered in planes, or absent? |
| atmospheric_cue | does distance fade, haze, or desaturate? |
| detail_gradient | does detail density fall off with distance? |
| layer_separation | how strongly do layers read as separate? |

definitions in `axes.md`. candidates in `canonical_tags.md`, all unseeded. synonyms all anticipated.

## the physical cue inventory

the perceptual psychology tradition (monocular depth cues) gives a longer list than the axes: occlusion/overlap, relative size, familiar size, elevation, texture gradient, linear perspective, aerial perspective, shading, and the binocular/motion cues that static images cannot use. the four axes here are not a replacement for that inventory. they are the four *treatments* users actually name when they talk about depth. the cue inventory lives in `research.md` as the engine's measurement shopping list: each cue is measurable, and the axes are what users call the cues' combined effects.
