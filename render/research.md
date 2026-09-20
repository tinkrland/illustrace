# render research

what already exists in the world for mark-making vocabulary, what this system agrees with, and where it deliberately departs. sources from the artschool research pass (tavily + firecrawl, 2026-09-20). none of this blesses a canonical. research proposes, images dispose.

## the elements of art

art education already decomposes pictures into observable components: line, shape, form, value, texture, color, space (massart foundations curriculum, and every art teacher variant of it). that is the same instinct as the five axes. the difference: the elements are a list of components, this folder is a list of *questions with discrete answers*, because the engine needs a finite combination space, not a component inventory. mark_visibility, edge_quality, surface_texture, and color_mode are line/shape/value/texture/color turned into multiple choice.

`paper_role` has no standard equivalent in the elements. it is the novel axis here, and it came from a real image rather than from theory, which is the right order.

## hatching taxonomies

the standard hatching vocabulary (hachure, cross-hatching, contour hatching, stippling, scumbling, mark density for tone) maps cleanly onto hatching_color and hatching_mono. the one-word-per-technique tradition is why users say "crosshatching" or "pen sketch" and expect the system to know exactly what they mean. this folder agrees the technique matters, but refuses technique as a canonical identity: "crosshatching" is a synonym, the canonical is what the hatching *does* (stroke_visible / broken / textured / density-determined value). a user who says "like crosshatching but with color" resolves to hatching_color, and no technique taxonomy would have that row.

## digital render styles

cel shading (toon shading), flat shading, and painterly rendering are the digital art world's existing render-type vocabulary. cel/flat shading is precisely the unseeded lineart_flat prediction: hard shadow edges, flat fills, line on top. painterly rendering matches painterly_stroke. the match is reassuring but the rule holds: both remain predictions until a real image seeds them. the digital vocabulary confirms these gaps are real holes rather than artifacts of the session's image set.

## mark-making as personal language

abstract painting discourse treats mark-making as "the visual vocabulary an artist uses", "an artist's own personal visual language". this system agrees with the metaphor more than the discipline: it literalizes the metaphor into an actual vocabulary with synonyms and canonicals, so that a user's personal language wrangles onto shared parameters instead of staying private.

## ao3 tag wrangling

the wrangling precedent for the whole branch: canonical tags, synonym tags (synning), the principle that a synonym changes the search behavior without changing the canonical, and wranglers as the maintenance layer between free user tags and the structured system. this folder borrows the pattern wholesale. the difference is scale: ao3 wrangles human words about stories, this wrangles human words about pixels, and the canonicals must cash out as engine parameters rather than as search facets.

## deliberate departures

- no medium names as canonical identity. "marker", "colored pencil", "crayon" are synonyms. the canonicals describe behavior (what the mark did), because medium is a proxy for behavior that the engine cannot measure.
- no art-history periods. "impressionist" is not an answer to any of the five questions.
- no teacher-ese. vocabulary here must survive contact with a wrangler and a parameter recipe. anything that cannot be operationalized stays out.
