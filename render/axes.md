# render axes

five questions that describe what a mark actually did to a surface. not art history. not tool names. observable properties only. every canonical render tag is a combination of answers to these.

design notes on the axes themselves:

- `mark_visibility` is the load-bearing axis. it decides whether the image is about strokes or about shapes, and everything else in the engine's stroke-related parameters hangs off it.
- `edge_quality` and `surface_texture` are deliberately independent. hard edges with visible texture (marker tiles) and soft edges with flat fills (airbrush) both exist, so neither axis can be derived from the other.
- `color_mode` keeps `limited` separate from `color` because "one accent hue over mono" behaves differently in palette extraction than "many hues".
- `paper_role` was the last axis added and the one that catches the most mistakes. a classifier without it reads the crayon landscape's white gaps as unfinished hatching.

---

```json
{
  "axes": [
    {
      "id": "mark_visibility",
      "question": "is the individual stroke/mark visible, or did it dissolve into filled shape?",
      "values": [
        {
          "id": "stroke_visible",
          "description": "you can see individual marks. the line or stroke is the thing."
        },
        {
          "id": "shape_filled",
          "description": "marks dissolved. what remains is a filled region. stroke is gone."
        },
        {
          "id": "both",
          "description": "some marks visible (linework, accent strokes) over filled regions."
        }
      ]
    },
    {
      "id": "edge_quality",
      "question": "are region boundaries hard/sharp or soft/blurred?",
      "values": [
        {
          "id": "hard",
          "description": "clean boundary between one color/tone and the next. deliberate edge."
        },
        {
          "id": "soft",
          "description": "colors or tones bleed into each other. edge is gradual or absent."
        },
        {
          "id": "broken",
          "description": "edge exists but is irregular: gaps, wobble, line texture interrupts it."
        }
      ]
    },
    {
      "id": "surface_texture",
      "question": "is there visible texture within filled or marked areas, or is it flat?",
      "values": [
        {
          "id": "textured",
          "description": "grain, paper tooth, brush texture, or mark density variation is visible."
        },
        {
          "id": "flat",
          "description": "regions are even. no visible texture within a color area."
        }
      ]
    },
    {
      "id": "color_mode",
      "question": "does the image use color, or is it monochrome?",
      "values": [
        {
          "id": "color",
          "description": "hue is present and intentional."
        },
        {
          "id": "mono",
          "description": "black, grey, white only. no hue."
        },
        {
          "id": "limited",
          "description": "one or two accent hues over an otherwise mono base, or a very restricted palette."
        }
      ]
    },
    {
      "id": "paper_role",
      "question": "does unmarked paper/canvas play an active role, or is it incidental?",
      "values": [
        {
          "id": "none",
          "description": "surface is fully covered. paper is not visible in the final image."
        },
        {
          "id": "incidental",
          "description": "some paper shows through gaps in marks but those gaps are not intentional design decisions."
        },
        {
          "id": "intentional",
          "description": "unmarked areas are deliberate. paper white reads as light, highlight, or negative space on purpose."
        }
      ]
    }
  ]
}
```
