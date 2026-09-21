# material research

sources from the artschool research pass (tavily, 2026-09-21). research proposes, images dispose.

## perception science: materials are read from light behavior

the vision literature (schmid & anderson on material category from specular structure, gigilashvili on subsurface scattering and glossiness) establishes the core fact this folder is built on: humans categorize substances from how light behaves at the surface, especially specular highlight structure, and even subsurface transport contributes to gloss judgments. the axes here (surface_finish, light_transport) are a wrangler-friendly discretization of that finding. the science also warns us: gloss alone does not determine material (the feedforward hypothesis failed), which is why finish and transport are separate axes rather than one gloss slider.

## the rendering pipeline vocabulary

3d material properties (diffuse, specular, roughness, transmission, subsurface, BRDF) are the industry formalization of the same bundle, and the `light_transport` values map almost one-to-one. the difference in intent: pipelines describe light physics so a simulator can reproduce it. this folder describes the *claims* a flat image makes, so a wrangler can name them and the engine can fake them with value shapes. chrome in illustration is one white slash; the pipeline would call that fraud, the wrangler calls it canonical.

## art education has almost nothing

unlike render, construction, spatial, and palette, no classroom source found gives a vocabulary for depicting substance. classroom texture lists stop at "texture", museum materials-and-techniques pages are about the *actual* artwork's substances (the physical print's paper, the sculpture's bronze), not depiction. this is the least externally-grounded folder in the branch. its axis values lean on perception science and pipeline vocabulary, and its canonical set will be decided almost entirely by real images and real session language.

## boundary with textures

the folder boundary decided here: textures owns surface *pattern*, materials owns substance *behavior* (finish, transport, edge). wood grain alone is textures; "polished wood" with sheen and edge behavior is materials plus a texture. the wrangler resolution order for substance words: no second signal -> textures; finish/transport/edge language present -> materials. this is written into materials/synonyms.md `_ambiguous` (see "wooden").
