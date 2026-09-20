# spatial canonical tags

> status: research-derived candidates. none is a canonical yet.

---

```json
{
  "canonicals": [],

  "_candidates": [
    {
      "id": "flat_graphic",
      "label": "flat graphic",
      "axes": { "depth_model": "none", "atmospheric_cue": "none", "detail_gradient": "weak", "layer_separation": "blended" },
      "description": "one plane, no distance. sticker, heraldry, icon, flat poster. nothing in the picture is nearer than anything else.",
      "would_touch": { "layer_count": 1, "depth_cue_weights": "all zero" }
    },
    {
      "id": "paper_cut_layers",
      "label": "paper cut layers",
      "axes": { "depth_model": "layered", "atmospheric_cue": "none", "detail_gradient": "weak", "layer_separation": "distinct" },
      "description": "discrete flat planes stacked with visible separation. cutout animation, shadow-box diorama, theatre flats. depth exists as slots, not as distance.",
      "would_touch": { "layer_count": "3-6", "inter_layer_gap": "visible", "atmospheric_falloff": 0 }
    },
    {
      "id": "atmospheric_haze",
      "label": "atmospheric haze",
      "axes": { "depth_model": "continuous", "atmospheric_cue": "strong", "detail_gradient": "strong", "layer_separation": "blended" },
      "description": "distance expressed through fading: haze, desaturation, contrast drop, detail loss. misty mountains, ink-landscape tradition, morning-road plein air.",
      "would_touch": { "contrast_by_depth": "falling", "saturation_by_depth": "falling", "haze_strength": "high" }
    },
    {
      "id": "diorama_stages",
      "label": "diorama stages",
      "axes": { "depth_model": "layered", "atmospheric_cue": "subtle", "detail_gradient": "strong", "layer_separation": "distinct" },
      "description": "fg/mg/bg read as distinct stages, each fully detailed, separated by value or overlap rather than haze. classic illustration and animation staging.",
      "would_touch": { "layer_count": 3, "contrast_between_layers": "high", "atmospheric_falloff": "low" }
    }
  ]
}
```

## what real usage will probably do to this list

- atmospheric_haze and diorama_stages feel well-separated. they may be.
- flat_graphic and paper_cut_layers differ only in layer count. if wrangling keeps sending the same images to both, they merge and `layer_separation` absorbs the difference.
- the missing obvious candidates are the photographic treatments (shallow focus, foreground framing) that photography vocabulary covers and illustration vocabulary mostly does not. they stay out until a user actually asks for them, since this branch serves illustration language first.
