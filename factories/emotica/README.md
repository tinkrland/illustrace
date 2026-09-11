# emotica (emoticon factory)

the expression-kit factory. a consistent-style set of emoticons: one base shape vocabulary (star, moon, cloud, blob, egg) wearing a wide range of expressions, minimal linework, single accent color for the mouth or blush, floating accessory marks (sparkles, hearts, zzz, tears, motion lines). this is the family of sticker packs that flood pinterest and messaging apps, and the reason they read as a set instead of forty unrelated doodles is a small, disciplined parameter surface underneath, exactly the thing a factory should formalize.

## what it makes

- expression sets on a shared base shape: the same star, moon, or blob wears sleepy eyes, sparkle eyes, x-eyes, closed content eyes, heart eyes, each an editable expression slot, not a redrawn face
- accessory marks as an independent layer: zzz clouds, sparkle bursts, tears, blush ovals, motion streaks, speech bubbles, composited on top of, not baked into, the base
- kit-wide consistency, ikonic's contract applied to faces: one accent color, one line weight, one corner language, across the whole set

## the parameter surface (from the attached reference)

the reference sheet (kawaii star and moon emoticons, green accent, consistent outline weight) breaks cleanly into slots:

- **base shape**: star, moon (crescent/gibbous), cloud, blob, egg, each with point-count / roundness parameters
- **eyes**: shape (dot, line, arc, sparkle, heart, x), tilt, spacing
- **mouth**: shape and the one accent-color fill (this factory's signature move, a single filled shape carrying all the warmth of the expression)
- **accessories**: independently toggleable overlays, positioned relative to the base shape, not hand-placed per icon
- **grouping**: some expressions are two-base-shapes-touching (a pair cuddling, one shape peeking from behind another), so composition slots exist alongside single-shape slots

## the editable-preset contract

an emoticon is (base shape params) + (eyes slot) + (mouth slot) + (accessory layer list) + (accent color). change the accent color once, the whole set restyles. change the base shape from star to cloud, every expression in the library re-renders onto the new base. nothing is a flattened sticker; the sticker is an export.

## relationship to charatrace

emotica is the face-and-affect vocabulary that a full character eventually needs (see the [picrewify pillar](/README.md#picrewify)): today it is standalone expression kits for stickers and reaction sets; later, the same expression-slot logic is a candidate source for how a characraft character's face reads emotion.

## status

parked. readme only, no build.
