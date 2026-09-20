# construction research

sources from the artschool research pass (tavily + firecrawl, 2026-09-20). research proposes, images dispose.

## the 16 types of perspective (lifedrawing.academy)

vladimir london's enumeration (one-, two-, three-point plus axonometric and aerial variants) is the fullest named list found. the useful confirmations:

- one-point: frontal plane undistorted, vanishing lines converge behind. used when one face of the subject faces the viewer squarely.
- eye level = horizon line, by definition. the source drills this as the core insight: the horizon is not a property of the scene, it is a property of the viewer's height. which is exactly why this folder calls the axis `eye_level` and not `horizon_position`.
- above/below the horizon flips what you see of horizontal planes. the same cube at, above, and below eye level reads as three different drawings. this is the observation behind the eye_level axis values.
- aerial perspective appears here too (line boldness falling with distance), but that effect is assigned to spatial/ in this taxonomy. it is a depth cue, not a camera property.

## curvilinear perspective (wikipedia, perspective graphical)

at the extremes of the visual field parallel lines curve. most art and photography crops it away. keeping it as an axis value (curvilinear) rather than pretending the straight-line projections are exhaustive is the one place this system is more permissive than the classical curriculum. fisheye energy in modern illustration (posters, skate graphics, wide-angle moods) justifies it.

## oblique/axonometric projections

isometric, cabinet, military projection: parallel lines stay parallel. the classical world treats these as technical drawing, not perspective. this system folds them into `projective_system: none` because users experience them as "flat" or "game-like", and the wrangler needs the mapping to be about experience, not drafting convention. if usage distinguishes them later, the axis splits.

## what is missing from the sources

none of the sources gives a vocabulary for convergence *discipline* (systematic vs naive construction). art education either teaches the strict version or ignores construction entirely. the `convergence_strength` axis is the novel proposal here, borrowed from the render seeds where the same dial (systematic buildings vs gestural house) was already needed. it is the least-researched and most likely axis to move once real images arrive.
