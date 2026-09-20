# render

> the seeded core. every other folder in this branch is this pattern pointed at a different question.

what did the mark actually do to the surface?

that is the only question this folder answers. not what tool was used, not what movement the artist belonged to, not what the subject is. what happened when the mark met the surface, and what did it leave behind.

## the five axes

every image can answer five questions. the answers combine into a canonical render type. definitions in `axes.md`.

| axis | question |
|---|---|
| mark_visibility | is the stroke visible, or did it dissolve into filled shape? |
| edge_quality | hard, soft, or broken edges between regions? |
| surface_texture | visible texture, or flat? |
| color_mode | color, mono, or limited? |
| paper_role | is unmarked paper absent, incidental, or intentional? |

`paper_role` exists because of a crayon landscape where the white gaps were the light. "not colored" is not the same as "unfinished".

## current canonicals

| id | mark | edge | texture | color | paper | plain description |
|---|---|---|---|---|---|---|
| block_fill | shape_filled | hard | flat | color | none | flat opaque color regions, stroke gone |
| hatching_color | stroke_visible | broken | textured | color | incidental | color made of lines |
| hatching_mono | stroke_visible | broken | textured | mono | incidental | black lines, shading by density |
| wash_gestural | both | soft | textured | mono | intentional | soft wash + hard marks on top |
| pastel_open | stroke_visible | broken | textured | color | intentional | loose color marks, white gaps = light |

## known gaps

**wash_gestural_color**. marker or watercolor wash with color, not mono. both wash_gestural seeds are mono. waiting on a real image.

**painterly_stroke**. oil or acrylic where the visible brushstroke is the expressive element. the gleason painting hints at it but filled shape still dominates there, so it resolved to block_fill. waiting on a clean example.

**lineart_flat**. clean digital linework over flat fill, the animation and comics default. extremely common, still unseeded. research on digital render styles (cel shading, flat shading) backs the prediction, but research does not bless canonicals. images do.

## adding a new canonical

requirements, all four:
1. at least one real seed image in `examples.md`
2. axis values that do not fully overlap an existing canonical
3. at least one synonym not already covered
4. a registry_hints entry showing which engine parameters it touches

do not add canonicals to fill out a taxonomy. add them when a real image fits nothing existing.

## prior art

`research.md` collects what already exists in the world for mark-making vocabulary, what this system agrees with, and where it deliberately departs.
