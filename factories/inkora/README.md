# inkora (blob factory)

the organic-mark factory. people love abstract blobs, flower-shaped blobs, amorphous organic silhouettes, the kind of shape that becomes a logo mark, an app icon, a sticker, an album cover. today they get these by drawing them by hand or by lucking into a random generator and screenshotting it. inkora makes them as editable parametric marks: you sculpt, you save, you reopen and it's the same shape.

## what it makes

- abstract blob marks: noise-displaced closed silhouettes, from smooth pebble to thorny flower
- parametric outlines with directly draggable control points, inspect-mode style
- appearance as recipe layers: fill, gradient, border (solid/dashed/dotted), texture (grain), mask, material, effect, each independently toggleable and styled

## the parameter surface (from the p5 sketch that seeded this)

the idea was seeded by a p5.js sketch, used purely as inspo for the parameter space, not as the build. the sketch's controls translate directly into the asset schema:

- **structure**: complexity, sharpness (curve tension from blobby to spiky), displacement, chaos, variance
- **appearance**: color + opacity + fill style (solid, hachure), multi-stop gradients (linear/radial), borders, grain texture, masks, materials, effects
- **interactive**: per-point dragging of the displaced outline, the key difference from a random generator

## the editable-preset contract

the sketch is random and animated; the factory is neither. in inkora, animation is at most a preview affordance and randomness is at most a browsing affordance. the saved asset is the deterministic program: base radius, resolution, noise seed, complexity/sharpness/displacement/chaos/variance, plus the manual per-point drag offsets. reopen reproduces the exact mark. export is layered svg first, png second.

## adoption terms (how much can be taken)

all of it, because the source is our own p5 sketch: there is no permission question, it is our code. but the repo stance is inspo only. the sketch is deliberately not committed, and the factory is not a port. what gets taken is the design, not the implementation posture:

- **fully takeable**: the parameter vocabulary (structure: complexity, sharpness, displacement, chaos, variance; appearance: fill, gradient, border, texture, mask, material, effect; interaction: inspect mode with per-point dragging), plus the general insight that people want these marks sculptable, not rolled
- **not taken**: the implementation approach. the sketch is noise-driven, random, and animated; the factory inverts that posture (deterministic saved programs, randomness as a browsing affordance only). the build is a re-expression of the same parameter surface under the editable-preset contract, not a code lift

since the sketch is ours, it can be dropped into `vendor/` or referenced directly the day the build starts, no ask needed.

## studio role

blob marks are the most-composed factory asset: they pair with type (fontasy), get sealed (sigilry), get stitched (weaverly), get printed (analogistry). first citizen of the studio.

## status

parked. readme only, no build.
