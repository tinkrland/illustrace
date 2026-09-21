# texture canonical tags

> status: research-derived candidates. none is a canonical yet.

---

```json
{
  "canonicals": [],

  "_candidates": [
    {
      "id": "stipple_field",
      "label": "stipple field",
      "axes": { "pattern_basis": "mark_repetition", "unit_scale": "micro", "regularity": "drift", "form_following": "modeling" },
      "description": "dots of varying density and tone building a surface. dot density is value. engraving stipple, pointillism surface work, denim speckle.",
      "would_touch": { "texture_energy": "high", "texture_unit": "dot", "density_gradient": "enforced" }
    },
    {
      "id": "weave_grid",
      "label": "weave grid",
      "axes": { "pattern_basis": "geometric_unit", "unit_scale": "visible", "regularity": "grid", "form_following": "flat" },
      "description": "interlocking cells lying flat on the surface. weave, wicker, checker, knitted fabric. decoration, not modeling.",
      "would_touch": { "texture_periodicity": "high", "unit_shape": "closed cell", "texture_energy": "medium" }
    },
    {
      "id": "scale_rows",
      "label": "scale rows",
      "axes": { "pattern_basis": "geometric_unit", "unit_scale": "visible", "regularity": "drift", "form_following": "modeling" },
      "description": "overlapping rounded units compressing and spreading across the form. fish, dragon, lizard, sequin. the drift plus modeling is what keeps it alive.",
      "would_touch": { "unit_shape": "overlapping arc", "density_gradient": "enforced", "texture_energy": "medium" }
    },
    {
      "id": "wood_grain_flow",
      "label": "wood grain flow",
      "axes": { "pattern_basis": "organic_flow", "unit_scale": "macro", "regularity": "drift", "form_following": "modeling" },
      "description": "long flowing lines with occasional knots, following the object's structure. plank, branch, tabletop. the canonical organic flow case.",
      "would_touch": { "stroke_directionality": "high", "flow_coherence": "high", "knot_frequency": "low" }
    },
    {
      "id": "speckle_scatter",
      "label": "speckle scatter",
      "axes": { "pattern_basis": "noise_field", "unit_scale": "micro", "regularity": "scatter", "form_following": "flat" },
      "description": "random unstructured speckle across surfaces. granite counter, bird egg, stucco. noise as depicted surface, distinct from film grain (which is render's picture plane).",
      "would_touch": { "texture_energy": "medium", "spatial_autocorrelation": "low", "unit_shape": "none" }
    }
  ]
}
```

## expected churn

- marble (organic_flow, visible unit, scatter) has no candidate yet because it straddles wood_grain_flow and speckle_scatter. wait for a real image rather than inventing the split now.
- wallpaper and textile design have entire industries of pattern taxonomy (the artlandia glossary tradition) that this system is refusing to import wholesale. if users start naming damasks and toile, the vocabulary imports those words as synonyms, and canonicals appear only when images demand them.
