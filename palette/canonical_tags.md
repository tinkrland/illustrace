# palette canonical tags

> status: research-derived candidates. none is a canonical yet. no image has been tagged against any of these, and palette is the folder where untested taxonomies rot fastest.

---

```json
{
  "canonicals": [],

  "_candidates": [
    {
      "id": "duotone_notan",
      "label": "duotone notan",
      "axes": { "value_structure": "notan_2", "hue_scheme": "mono", "saturation_mode": "saturated", "temperature_bias": "neutral" },
      "description": "two values, one hue family, full commitment. woodcut, screenprint, risograph energy. the design reads at thumbnail size.",
      "would_touch": { "value_bands": 2, "hue_count": 1, "enforce_steps": true }
    },
    {
      "id": "high_key_pastel",
      "label": "high key pastel",
      "axes": { "value_structure": ["notan_3", "full_range"], "hue_scheme": "analogous", "saturation_mode": "muted", "temperature_bias": "warm" },
      "description": "light values throughout, soft hue neighbors, low saturation. confectionery, nursery, spring poster. never a dark shadow in sight.",
      "would_touch": { "mean_value": "high", "saturation_mean": "low", "hue_spread_degrees": "narrow" }
    },
    {
      "id": "earth_muted",
      "label": "earth muted",
      "axes": { "value_structure": "full_range", "hue_scheme": "earth", "saturation_mode": "muted", "temperature_bias": "warm" },
      "description": "ochre, sienna, umber, olive. the plein air earth palette. muddy on purpose, observational at heart.",
      "would_touch": { "hue_cluster": "earth", "saturation_mean": "low", "temperature_mean": "warm" }
    },
    {
      "id": "neon_accent",
      "label": "neon accent",
      "axes": { "value_structure": "full_range", "hue_scheme": "complementary", "saturation_mode": "accent", "temperature_bias": "split" },
      "description": "one or two loud pops over a restrained field. the single red coat. noir poster energy, graphic and pointed.",
      "would_touch": { "saturation_variance": "high", "accent_isolation": "enforced" }
    },
    {
      "id": "classic_triad",
      "label": "classic triad",
      "axes": { "value_structure": "full_range", "hue_scheme": "triadic", "saturation_mode": "saturated", "temperature_bias": "neutral" },
      "description": "three hues spread on the wheel, all loud. cartoon, candy, toy-box palette. the primary-color default of animation.",
      "would_touch": { "hue_count": 3, "hue_spread_degrees": "even", "saturation_mean": "high" }
    }
  ]
}
```

## what will probably move

- high_key_pastel carries two value_structure values, which is a smell. when real images arrive this usually means the candidate is two canonicals (confectionery pastel vs soft-watercolor value) or that value_structure needs a value between notan_3 and full_range.
- the engine already has a palette metric from before this branch existed. every candidate here must eventually express itself as arguments to that operator, or the vocabulary and the engine drift apart. the registry hint names in `would_touch` are placeholders until that reconciliation pass happens.
