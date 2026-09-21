# texture synonyms

user language mapped to texture candidates. all anticipated. this file will trade heavily with render/synonyms.md: grainy, rough, and textured all commute between picture-plane marks and depicted surfaces. append-only.

---

```json
{
  "synonyms": [
    { "term": "speckled",                        "canonical": "stipple_field",     "source": "anticipated" },
    { "term": "stippled",                        "canonical": "stipple_field",     "source": "anticipated" },
    { "term": "dotty",                           "canonical": "stipple_field",     "source": "anticipated" },
    { "term": "like pointillism but on objects", "canonical": "stipple_field",     "source": "anticipated" },

    { "term": "woven",                           "canonical": "weave_grid",        "source": "anticipated" },
    { "term": "wicker",                          "canonical": "weave_grid",        "source": "anticipated" },
    { "term": "checkered",                       "canonical": "weave_grid",        "source": "anticipated" },
    { "term": "knit-y",                          "canonical": "weave_grid",        "source": "anticipated" },
    { "term": "like fabric print",               "canonical": "weave_grid",        "source": "anticipated" },

    { "term": "scaly",                           "canonical": "scale_rows",        "source": "anticipated" },
    { "term": "like fish scales",                "canonical": "scale_rows",        "source": "anticipated" },
    { "term": "sequin-y",                        "canonical": "scale_rows",        "source": "anticipated" },

    { "term": "wood grain",                      "canonical": "wood_grain_flow",   "source": "anticipated" },
    { "term": "grain-y like wood",               "canonical": "wood_grain_flow",   "source": "anticipated" },
    { "term": "like a plank",                    "canonical": "wood_grain_flow",   "source": "anticipated" },
    { "term": "woodsy",                          "canonical": "wood_grain_flow",   "source": "anticipated" },

    { "term": "like granite",                    "canonical": "speckle_scatter",   "source": "anticipated" },
    { "term": "stucco-y",                        "canonical": "speckle_scatter",   "source": "anticipated" },
    { "term": "like a bird egg",                "canonical": "speckle_scatter",   "source": "anticipated" }
  ],

  "_ambiguous": [
    {
      "term": "grainy",
      "note": "three homes possible: render (paper grain in the marks), textures (wood grain on depicted surfaces), or a film-grain overlay. the wrangler must ask what the grain belongs to. never silently pick."
    },
    {
      "term": "textured",
      "note": "names the whole folder, or render's surface_texture axis, depending on where the speaker's attention sits. needs a second signal."
    },
    {
      "term": "rough",
      "note": "depicted surface quality (this folder), mark quality (render), or even loose handling (render/gestural). the most commuted word in the branch."
    },
    {
      "term": "pattern",
      "note": "could be any texture candidate, or none: patterns exist that are compositions, not surfaces (a pattern in the layout). check what the pattern is on."
    }
  ]
}
```
