# seed examples

ground-truth labeled images from the design session. `canonical_tags.md` was derived from these. no canonical without a real image here first.

`confidence` reflects how clean the classification is: low means the image sits near the boundary of two canonicals.

the image files themselves live with the session assets and are not committed yet. the filenames below are the canonical names. when the binaries land, they go in this folder so examples never dangle.

---

```json
{
  "examples": [
    {
      "filename": "kevin_gleason_plein_air.jpg",
      "description": "oil painting, landscape with trees and path, warm light",
      "canonical": "block_fill",
      "confidence": "medium",
      "user_description": "not watercolor. just colors. but more shaped shaped than the real shapes",
      "notes": "softer end of block_fill. some stroke texture visible, some edge variation. sits near the boundary with the hypothetical painterly_stroke canonical. classified here because filled shape dominates over visible mark."
    },
    {
      "filename": "digital_block_painting_landscape.jpg",
      "description": "digital painting, canyon landscape, rectangular color blocks, sunset",
      "canonical": "block_fill",
      "confidence": "high",
      "user_description": "more chunky chunky filled",
      "notes": "hard end of block_fill. nearly rectangular tiles of flat color. stroke completely absent. the cleaner of the two block_fill examples."
    },
    {
      "filename": "colored_pencil_trees_landscape.jpg",
      "description": "colored pencil or crayon, trees on rolling hills, vertical line strokes",
      "canonical": "hatching_color",
      "confidence": "high",
      "user_description": "lines (grouped with the lighthouse as lines)",
      "notes": "vertical colored strokes build up the fill of each region. no flat color areas. line direction consistent within each shape. paper shows through slightly, incidental not intentional."
    },
    {
      "filename": "pen_hatching_lighthouse_color.jpg",
      "description": "ballpoint or fine pen, lighthouse scene, colored cross-hatching per region",
      "canonical": "hatching_color",
      "confidence": "high",
      "user_description": "lines (grouped with colored pencil trees)",
      "notes": "more systematic than the colored pencil example. cross-hatching deliberate and directional per region, different colors per zone. same canonical because the fundamental behavior is identical: color built from lines."
    },
    {
      "filename": "pen_buildings_crosshatch.jpg",
      "description": "ink pen, urban apartment buildings, dense cross-hatching for shadow",
      "canonical": "hatching_mono",
      "confidence": "high",
      "user_description": "sketchy (grouped with house sketch, noted not all sketchy is the same)",
      "notes": "systematic cross-hatching. lines deliberate and controlled. shadow areas dense hatch, light areas sparse or blank. architectural subject and systematic line quality distinguish it from the house sketch within the same canonical."
    },
    {
      "filename": "pen_house_gestural.jpg",
      "description": "ink pen, house with trees, gestural hatching, dated 17.10.2025",
      "canonical": "hatching_mono",
      "confidence": "high",
      "user_description": "sketchy (grouped with buildings)",
      "notes": "same canonical as the buildings but the loose end. lines fast and gestural, hatching directional but not systematic. stroke_directionality in the registry would score lower here. same canonical, different parameter values within it."
    },
    {
      "filename": "marker_wash_road_trees.jpg",
      "description": "ink or marker wash, road through trees, grey tones, gestural dark marks",
      "canonical": "wash_gestural",
      "confidence": "high",
      "user_description": "marker (grouped with river landscape)",
      "notes": "two clear layers: grey wash giving soft tone, dark gestural marks giving structure. paper white active in road and sky. mono only, no hue."
    },
    {
      "filename": "marker_wash_river_landscape.jpg",
      "description": "ink or marker wash, open landscape with water, grey tones, marker marks",
      "canonical": "wash_gestural",
      "confidence": "high",
      "user_description": "marker (grouped with road/trees)",
      "notes": "same canonical as road/trees. slightly softer marks, more wash dominance. same two-layer structure."
    },
    {
      "filename": "crayon_river_landscape_open.jpg",
      "description": "crayon or oil pastel, marsh/river landscape, loose marks, intentional white gaps",
      "canonical": "pastel_open",
      "confidence": "high",
      "user_description": "what's intentionally NOT COLORED is also important",
      "notes": "the observation that triggered the paper_role axis. salmon clouds and blue water both show deliberate gaps reading as light. this is not unfinished hatching_color. the white is load-bearing."
    }
  ]
}
```

## open slots

seed images wanted for: wash_gestural_color, painterly_stroke, lineart_flat. one real image each promotes them from prediction to canonical. nine seeds produced five canonicals with clean boundaries, so the yield per image is high.
