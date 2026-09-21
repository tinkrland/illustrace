# texture research

sources from the artschool research pass (tavily, 2026-09-21). research proposes, images dispose.

## actual vs visual texture

art education splits texture into actual texture (physically feelable, irrelevant for 2d output) and visual texture ("how it appears to feel", thevirtualinstructor and every classroom variant). that split licenses this folder's whole premise: depicted surface quality is a real, teachable, nameable property of a picture, distinct from both the physical picture and the marks' behavior. the axes here are visual texture only.

## the stipple and pattern traditions

classroom texture lists enumerate techniques (stippling, hatching, scumbling, dry brush) which overlap heavily with render's mark vocabulary, confirming the boundary problem this folder must police: technique words belong to render when they describe the marks, to textures when they describe depicted surfaces. the same dot gesture is render when it is the image's mark structure, textures when it is denim speckle on a vest. pattern-design vocabulary (the artlandia glossary tradition: regular/irregular, motif, repeat, textile pattern) contributes the regularity axis: textile and wallpaper design have been formalizing pattern discipline for centuries and the grid/drift/scatter ladder is a simplification of their terminology, kept coarse because users speak coarsely.

## no external vocabulary for form_following

no source gives vocabulary for whether texture follows the depicted form. it is the single most important property for illustration quality (flat sticker texture vs scales compressing around a flank), it is measurable (subregion density gradients), and it is completely unnamed in the art-education sources found. like the cutout depth model in spatial, this is working-illustrator knowledge that theory has not absorbed. the axis is this branch's own coinage, expected to earn or lose its keep against real images.

## engine hooks

the engine's existing texture_energy metric measures whether texture exists. this folder needs the next generation: texture_periodicity (grid vs scatter), texture unit shape, and density gradients across regions (form_following). all three are classical CV measurements, none are built yet, and this file is the requirements document for them.
