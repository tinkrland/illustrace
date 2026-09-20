# canonical render tags

each canonical is a combination of axis values plus a parameter recipe hint for the engine. seeded from real images reviewed in session, see `examples.md`. no canonical without a real image that demonstrates it.

the canonicals below are validated. the gaps at the bottom are predictions only.

---

```json
{
  "canonicals": [
    {
      "id": "block_fill",
      "label": "block fill",
      "axes": {
        "mark_visibility": "shape_filled",
        "edge_quality": "hard",
        "surface_texture": "flat",
        "color_mode": "color",
        "paper_role": "none"
      },
      "description": "image is built from flat opaque color regions. no visible stroke. edges are hard and geometric. marks dissolved completely into shapes. the extreme version approaches rectangular tiles.",
      "registry_hints": {
        "stroke_width_cv": "low: marks are uniform or absent",
        "edge_hardness": "high",
        "texture_energy": "low",
        "value_bands": "distinct: flat regions create clear tonal steps",
        "medium_bleed": "none"
      },
      "seed_images": ["kevin_gleason_plein_air.jpg", "digital_block_painting_landscape.jpg"],
      "notes": "gleason is the softer end (some stroke texture visible). the digital block painting is the hard end (purely rectangular). both resolve here because filled shape dominates over visible mark."
    },
    {
      "id": "hatching_color",
      "label": "color hatching",
      "axes": {
        "mark_visibility": "stroke_visible",
        "edge_quality": "broken",
        "surface_texture": "textured",
        "color_mode": "color",
        "paper_role": "incidental"
      },
      "description": "color is made of lines, not fill. parallel or cross-hatched strokes in multiple colors build tone and hue. regions are implied by line density and direction, not by filled areas. the line IS the color.",
      "registry_hints": {
        "stroke_width_cv": "low to medium: lines are fairly consistent width",
        "stroke_directionality": "high: lines have a dominant direction per region",
        "edge_hardness": "low: edges are broken by line ends",
        "texture_energy": "high: line texture dominates",
        "medium_bleed": "none"
      },
      "seed_images": ["colored_pencil_trees_landscape.jpg", "pen_hatching_lighthouse_color.jpg"],
      "notes": "the lighthouse is harder and more systematic (deliberate cross-hatching). the colored pencil trees are softer and more open. both are fundamentally color made of lines."
    },
    {
      "id": "hatching_mono",
      "label": "mono hatching",
      "axes": {
        "mark_visibility": "stroke_visible",
        "edge_quality": "broken",
        "surface_texture": "textured",
        "color_mode": "mono",
        "paper_role": "incidental"
      },
      "description": "same structure as hatching_color but no hue. black or dark ink lines on white paper. shading entirely through line density and cross-hatching. paper white is the lightest value.",
      "registry_hints": {
        "stroke_directionality": "high",
        "stroke_width_cv": "low to medium",
        "texture_energy": "high",
        "value_range": "determined by line density: sparse = light, dense = dark"
      },
      "seed_images": ["pen_buildings_crosshatch.jpg", "pen_house_gestural.jpg"],
      "notes": "the buildings are deliberate and systematic. the house is gestural and loose. that sub-difference lives in stroke_directionality in the registry, not in a separate canonical."
    },
    {
      "id": "wash_gestural",
      "label": "wash + gestural marks",
      "axes": {
        "mark_visibility": "both",
        "edge_quality": "soft",
        "surface_texture": "textured",
        "color_mode": "mono",
        "paper_role": "intentional"
      },
      "description": "two distinct layers: a soft wash creating tone and soft edges, plus visible gestural marks on top adding structure and detail. paper white is active, wash areas leave white for light.",
      "registry_hints": {
        "medium_bleed": "high: wash layer bleeds at edges",
        "stroke_width_cv": "high: gestural marks vary a lot",
        "edge_hardness": "mixed: wash is soft, marks are hard",
        "texture_energy": "medium",
        "value_range": "wide: white paper to dark marks"
      },
      "seed_images": ["marker_wash_road_trees.jpg", "marker_wash_river_landscape.jpg"],
      "notes": "color_mode is mono in both seeds. a color version (wash_gestural_color) almost certainly exists but has no seed image, so it is not added."
    },
    {
      "id": "pastel_open",
      "label": "pastel / crayon open",
      "axes": {
        "mark_visibility": "stroke_visible",
        "edge_quality": "broken",
        "surface_texture": "textured",
        "color_mode": "color",
        "paper_role": "intentional"
      },
      "description": "loose color marks (crayon, oil pastel, soft pastel) that do not fully cover the surface. unmarked paper is intentional and reads as light or air. marks are expressive and directional. colors may overlap or layer without fully mixing.",
      "registry_hints": {
        "medium_bleed": "low to none: dry medium",
        "stroke_width_cv": "high: loose marks vary",
        "texture_energy": "high: paper grain shows through",
        "edge_hardness": "low: marks trail off",
        "value_range": "compressed at light end: paper provides the lightest value"
      },
      "seed_images": ["crayon_river_landscape_open.jpg"],
      "notes": "the observation that triggered the paper_role axis. the salmon cloud area and blue water both show deliberate gaps reading as light. this is not unfinished hatching_color. the white is load-bearing."
    }
  ],

  "_unseeded_predictions": [
    {
      "id": "wash_gestural_color",
      "prediction": "same two-layer structure as wash_gestural but with hue in the wash. needs a seed image before it becomes a canonical."
    },
    {
      "id": "painterly_stroke",
      "prediction": "visible expressive brushwork as the dominant element, edges soft to broken, texture high. the gleason seed hints at it but filled shape dominates there. needs a clean seed."
    },
    {
      "id": "lineart_flat",
      "prediction": "clean digital linework over flat color fill (animation and comics default). axes: both / hard / flat / color / none. extremely common, research-backed (cel shading, flat shading), still unseeded."
    }
  ]
}
```

## canonical vs candidate

the `_unseeded_predictions` block is not canonicals. it is the wrangler's expectation of what real images will force into existence. when a seed image arrives for one of these, it moves into `canonicals` with real axis values and real registry hints. until then it is a hypothesis, and hypotheses do not touch the engine.
