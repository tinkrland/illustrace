# material canonical tags

> status: research-derived candidates. none is a canonical yet.

---

```json
{
  "canonicals": [],

  "_candidates": [
    {
      "id": "brushed_metal",
      "label": "brushed metal",
      "axes": { "substance_family": "metal", "surface_finish": "satin", "light_transport": "specular", "edge_identity": "crisp" },
      "description": "metal without the chrome theatrics: soft directional sheen, crisp silhouette, value bands from form. kettles, swords, kitchenware, mechs.",
      "would_touch": { "highlight_sharpness": "low", "value_bands": "distinct", "edge_hardness": "high" }
    },
    {
      "id": "chrome_slash",
      "label": "chrome slash",
      "axes": { "substance_family": "metal", "surface_finish": "gloss", "light_transport": "specular", "edge_identity": "crisp" },
      "description": "the maximal metal claim: hard value bands plus one white specular slash that ignores local light direction. retro robots, car art, bling.",
      "would_touch": { "highlight_sharpness": "high", "specular_count": "low and load-bearing", "value_bands": "hard steps" }
    },
    {
      "id": "clear_glass",
      "label": "clear glass",
      "axes": { "substance_family": "glass", "surface_finish": "gloss", "light_transport": "transmit", "edge_identity": "refracting" },
      "description": "substance shown almost entirely by edge: thin bright rims, background distortion at the boundary, almost no interior. windows, bottles, spectacles.",
      "would_touch": { "edge_emphasis": "high", "interior_opacity": "near zero", "background_distortion": "at boundary" }
    },
    {
      "id": "soft_fabric",
      "label": "soft fabric",
      "axes": { "substance_family": "fabric", "surface_finish": "matte", "light_transport": "diffuse", "edge_identity": "crisp" },
      "description": "cloth as soft volumes: no highlights, broad gradient folds, silhouette still crisp. hoodies, curtains, flags in repose.",
      "would_touch": { "highlight_absent": true, "fold_gradient": "broad", "edge_hardness": "medium" }
    },
    {
      "id": "flowing_water",
      "label": "flowing water",
      "axes": { "substance_family": "liquid", "surface_finish": "gloss", "light_transport": "specular", "edge_identity": "flowing" },
      "description": "water as movement: ribbons of highlight along currents, boundary that is a gesture not a shape. rivers, waves, pouring.",
      "would_touch": { "highlight_coherence": "along flow lines", "edge_style": "gestural", "flow_field": "enforced" }
    },
    {
      "id": "bristly_fiber",
      "label": "bristly fiber",
      "axes": { "substance_family": "fiber", "surface_finish": "matte", "light_transport": "diffuse", "edge_identity": "fuzzy" },
      "description": "substance as many strands: interior becomes strand strokes, silhouette dissolves into them. fur, grass, hair, tails.",
      "would_touch": { "interior_stroke_density": "high", "silhouette_break": "enforced", "strand_directionality": "high" }
    }
  ]
}
```

## expected churn

- no matte wood or stone candidate yet: those are mostly *textures* wearing a material name, and the boundary cases will decide whether materials canonicals are needed for them at all or whether "wood" and "granite" simply resolve to textures candidates. a real image will settle it.
- organic_soft (flesh, leaf, food) has no candidate despite the axis value existing, because no session has ever asked for it. it stays a value looking for a canonical.
- the whole folder is the most likely to be reshaped by the 3d-rendering lineage (BRDF parameters) once the engine starts measuring highlights. vocabulary from perception science, parameters from rendering, canonicals from images.
