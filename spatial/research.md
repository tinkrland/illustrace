# spatial research

sources from the artschool research pass (tavily + firecrawl, 2026-09-20). research proposes, images dispose.

## the depth-cue inventory (piter pasma, "visual depth cues")

the most complete single list found, from a generative artist's research pass rather than a textbook, which makes it unusually honest about what art can actually use. monocular cues relevant to static 2d work:

- occlusion / overlap (the blocker is closer, the outline that looks more continuous feels nearer)
- relative size, familiar size, absolute size
- elevation (objects nearer the horizon read as farther, moving off the horizon reads as approaching. cheap, powerful, underused vocabulary)
- texture gradient (near texture detailed, far texture smooth)
- linear perspective
- aerial / atmospheric perspective (far things bluish or hazy, but the brain accepts any hue: this is why purple fog works)
- shading and shadows
- plus the dynamic/binocular cues (motion parallax, optical expansion, kinetic depth, accommodation, convergence) that a static image cannot use, listed for completeness

the binocular and motion cues mark the boundary of the possible for illustration. this folder's axes deliberately stop where static images stop.

## art-foundations teaching set (nmu foundations, depth cues)

the classroom version compresses the same list to: linear perspective, atmospheric perspective, overlap, shadows/shading, relative size, known size. the compression loses elevation and texture gradient, which are the two cues the axes here depend on most (detail_gradient is texture gradient, and layer staging leans on elevation). a case where the teaching set is smaller than what working illustrators use.

## how the axes relate to the cue inventory

the axes are treatments, the cues are measurements. `atmospheric_cue` is aerial perspective operationalized as falloff curves (contrast_by_depth, saturation_by_depth). `detail_gradient` is texture gradient operationalized as mark-density falloff. `layer_separation` is occlusion plus elevation operationalized as inter-layer gap. the engine measures cues. users name treatments. canonicals bridge the two, and that is the whole trick of this branch in miniature.

## what is missing

no research source gives vocabulary for the *cutout* depth model, because perceptual psychology studies photographs and classrooms teach realism. paper_cut_layers and diorama_stages have no external precedent found. they come from illustration practice (cutout animation, theatre flats, picture-book staging). being under-theorized by the literature does not make them rare in usage. if anything it predicts users will have many words for them and no theory, which is exactly what a wrangler is for.
