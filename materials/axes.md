# material axes

four observable questions about what depicted surfaces are made of. unseeded, research-derived.

---

```json
{
  "axes": [
    {
      "id": "substance_family",
      "question": "what class of stuff does the surface claim to be?",
      "values": [
        { "id": "wood", "description": "grain-bearing rigid organic. planks, branches, carved." },
        { "id": "metal", "description": "conductive, reflective, often manufactured. chrome, gold, rusted iron." },
        { "id": "fabric", "description": "flexible woven or knit. cloth, felt, leather-adjacent." },
        { "id": "glass", "description": "transparent or translucent rigid. windows, bottles, lenses." },
        { "id": "liquid", "description": "flowing, cohesive, reflective at rest. water, ink, syrup." },
        { "id": "stone", "description": "mineral, granular or veined. rock, marble, concrete." },
        { "id": "fiber", "description": "many strands. fur, hair, grass, brush." },
        { "id": "organic_soft", "description": "flesh, leaf, food. matte, subtle subsurface, warm." }
      ]
    },
    {
      "id": "surface_finish",
      "question": "how do highlights read on it?",
      "values": [
        { "id": "matte", "description": "no highlights. value comes from albedo and shadow only." },
        { "id": "satin", "description": "soft broad highlights, no sharp shapes." },
        { "id": "gloss", "description": "sharp bright highlights with dark accented edges. the chrome slash." }
      ]
    },
    {
      "id": "light_transport",
      "question": "what does light do when it meets the substance?",
      "values": [
        { "id": "absorb", "description": "light stops at the surface. matte dark things, charcoal." },
        { "id": "diffuse", "description": "light scatters at the surface. paper, matte paint, most depicted things." },
        { "id": "specular", "description": "light bounces coherent off the surface. metal, calm water, gloss." },
        { "id": "transmit", "description": "light passes through, refracting or not. glass, some liquids." },
        { "id": "subsurface", "description": "light enters, scatters inside, exits elsewhere. the glow of a candle or an ear rim." }
      ]
    },
    {
      "id": "edge_identity",
      "question": "what kind of boundary does the object draw?",
      "values": [
        { "id": "crisp", "description": "clean silhouette. manufactured, stone, glass." },
        { "id": "fuzzy", "description": "soft broken silhouette from many fibers. fur, grass, frayed cloth." },
        { "id": "refracting", "description": "the boundary distorts what is behind it. glass and water edges." },
        { "id": "flowing", "description": "the boundary is a current, not a shape. liquids in motion." }
      ]
    }
  ]
}
```

## notes on the axis choices

- `light_transport` is the axis borrowed directly from perception science: gloss, specular structure, and subsurface scattering are how the vision literature proves humans read materials at all (specular image structure carries material category; subsurface scattering contributes to glossiness judgments). it is the least user-nameable axis, which is fine: users name substances and finishes, the wrangler maps those onto transport, the engine measures it.
- `substance_family` values are provisional and expected to grow the fastest of any axis in the branch. eight families is a starting inventory, not a closed set, and every addition needs exactly one real image.
- `edge_identity` overlaps spatial's layer_separation on purpose but answers a different question: not how layers separate, but what the *substance* does to its own silhouette. fur is fuzzy regardless of how staged the layers are.
