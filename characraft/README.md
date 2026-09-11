# characraft

the character creator. this is where a charatrace character is actually born: pick preset options, picrew-style, and build a doodled humanoid character piece by piece, then save her to your account as a persistent entity you can reuse forever, pose her in scenes, put her in different outfits, draw her from a different angle, without redrawing her from scratch each time.

or simply put: picrew proved people love building a character from a menu of parts. characraft is that menu, in a doodled illustration style, wired into charatrace's persistence model instead of ending at a single flattened export.

## how it starts

humanoid doodled characters first. not because that's the ceiling, because it's the clearest onboarding shape and the most crowded, most-loved reference category (picrew's own back catalog is almost entirely humanoid). other base types (creatures, mascots, the star/moon/cloud vocabulary that [emotica](/factories/emotica) uses) are a later, separate preset family once this one is proven.

## the flow

1. **presets**: choose from base body presets, not built yet, this is the parked part. proportions, body type, base pose, the skeleton of the character before any feature gets picked.
2. **picrew-style customize**: swap features from a menu, hair, face, outfit, accessories, each a part slot in the doodled style, exactly like the [picrewify pillar](/README.md#picrewify) illustrace's sibling doc already scoped: changing the hair changes *her* hair drawn in *her* line, not a generic asset pasted on top.
3. **save**: the finished combination is saved to the user's account as a character record, the part choices and style parameters, not a flattened image. this is the character, permanently reusable, not a one-off export.
4. **reuse**: later, pull the saved character into a scene and pose her, the [rigposer pillar](/README.md#rigposer) is what makes that possible, fold her up, sit her down, turn her shoulders, same character, same style, new pose.

## why this folder exists separately from the pillars docs

picrewify and rigposer (in the main [charatrace readme](/README.md)) are the *capability* claims: can features swap without surprise, can poses change without breaking identity. characraft is the *product surface* those capabilities add up to, the actual create-and-save flow a user touches. the pillars get validated as testable claims first; characraft is what they're for.

## the doodle base

the starting body is a doodled humanoid figure, sketchy and hand-drawn rather than clean vector, which makes [scribbleria](/factories/scribbleria) (charatrace's loose-line doodle factory) the likely source of the base linework hand once building starts.

## status

parked. readme only, no build. presets are explicitly not designed yet; this doc holds the shape of the flow, not its spec.
