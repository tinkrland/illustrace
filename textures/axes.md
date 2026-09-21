# texture axes

four observable questions about what covers depicted surfaces. unseeded, research-derived.

---

```json
{
  "axes": [
    {
      "id": "pattern_basis",
      "question": "what generates the texture?",
      "values": [
        {
          "id": "mark_repetition",
          "description": "one mark type repeated: stipple dots, dashes, short strokes. the mark is the unit."
        },
        {
          "id": "geometric_unit",
          "description": "a closed shape tiles the surface: checker, weave, scales, brick. the cell is the unit."
        },
        {
          "id": "organic_flow",
          "description": "flowing lines without a repeating unit: wood grain, marble veining, water ripples, hair. the gesture is the unit."
        },
        {
          "id": "noise_field",
          "description": "random, unstructured variation: film grain, static, sand, dust. there is no unit."
        }
      ]
    },
    {
      "id": "unit_scale",
      "question": "how big is the texture unit relative to the object it covers?",
      "values": [
        {
          "id": "micro",
          "description": "texture reads as an even surface quality at a glance. individual units resolve only on close look."
        },
        {
          "id": "visible",
          "description": "individual units are readable: each dot, each scale counts."
        },
        {
          "id": "macro",
          "description": "a few large units per object: big checks, one or two wood seams, single rivulets."
        }
      ]
    },
    {
      "id": "regularity",
      "question": "how disciplined is the placement?",
      "values": [
        {
          "id": "grid",
          "description": "strict alignment. checkerboards, weave, printed fabric."
        },
        {
          "id": "drift",
          "description": "a tendency toward arrangement with wobble. hand-placed dots, fish-scale rows that wander."
        },
        {
          "id": "scatter",
          "description": "organic irregularity. splatter, fur, stone speckle."
        }
      ]
    },
    {
      "id": "form_following",
      "question": "does the texture lie flat or follow the form?",
      "values": [
        {
          "id": "flat",
          "description": "texture is surface decoration, like a printed sticker. ignores volume."
        },
        {
          "id": "modeling",
          "description": "texture bends, compresses, or changes density across the form. the texture is doing shading work."
        }
      ]
    }
  ]
}
```

## notes on the axis choices

- `form_following` is the axis the engine will love most: density gradients across a region are measurable (texture_energy per subregion), and it is also the axis that separates naive texture application (flat stickers on shapes) from skilled depiction (scales shrinking around the fish's belly).
- `pattern_basis` deliberately includes noise_field, which art education's texture lists often forget because grain and static are photography vocabulary. users ask for grain constantly.
- regularity and pattern_basis are independent on purpose: you can have grid-locked organic units (brick-like wood parquet) and scattered geometric units (hand-tossed confetti checks).
