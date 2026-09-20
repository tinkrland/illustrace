# spatial axes

four observable questions about depth treatment. unseeded, research-derived, expected to move.

---

```json
{
  "axes": [
    {
      "id": "depth_model",
      "question": "how is depth organized in the picture?",
      "values": [
        {
          "id": "none",
          "description": "everything reads as one plane. graphic, heraldic, sticker-like. the picture knows no distance."
        },
        {
          "id": "layered",
          "description": "depth exists as a small number of discrete parallel planes: foreground / midground / background, paper cutouts, diorama stages."
        },
        {
          "id": "continuous",
          "description": "depth is a smooth gradient of position. things sit at many distances and the picture lets them."
        }
      ]
    },
    {
      "id": "atmospheric_cue",
      "question": "what does distance do to the far things?",
      "values": [
        {
          "id": "strong",
          "description": "far things clearly hazy, faded, desaturated, or contrast-reduced. mist, blue mountains, fog."
        },
        {
          "id": "subtle",
          "description": "a gentle fall-off exists but you must look for it."
        },
        {
          "id": "none",
          "description": "distance does nothing to the far things. flat depth treatment even if geometry is deep."
        }
      ]
    },
    {
      "id": "detail_gradient",
      "question": "does mark and texture density fall with distance?",
      "values": [
        {
          "id": "strong",
          "description": "near objects carry texture and detail, far objects smooth out. texture gradient doing the work."
        },
        {
          "id": "weak",
          "description": "detail spread roughly evenly regardless of depth."
        }
      ]
    },
    {
      "id": "layer_separation",
      "question": "how hard do the depth layers announce their edges?",
      "values": [
        {
          "id": "distinct",
          "description": "layers read as separate sheets. gaps, overlaps, or value jumps between planes. cutout or diorama feeling."
        },
        {
          "id": "blended",
          "description": "layers merge into each other. no perceptible boundary between planes."
        }
      ]
    }
  ]
}
```

## notes on the axis choices

- occlusion, relative size, elevation, and shading are physical cues, not axis values. they are how the engine *measures* depth. the axes describe what the treatments *look like*, because that is what users name ("faded mountains", "paper cutout"). two levels of description, deliberately not collapsed.
- `atmospheric_cue` is the axis the perceptual literature calls aerial perspective, renamed because "aerial" reads as art-history to users and "atmospheric" reads as what they actually say.
- `layer_separation` exists because the session's future test cases (sticker sheets, cutout animation, theatre-diorama scenes) all depend on the *gap* between layers, not the layers themselves.
