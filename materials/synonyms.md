# material synonyms

user language mapped to material candidates. all anticipated. material words are among the most conflation-prone in the branch because many (pastel, glossy, soft) are also palette or render words. append-only.

---

```json
{
  "synonyms": [
    { "term": "metallic",                  "canonical": "brushed_metal",    "source": "anticipated" },
    { "term": "like steel",                "canonical": "brushed_metal",    "source": "anticipated" },
    { "term": "like a kettle",             "canonical": "brushed_metal",    "source": "anticipated" },

    { "term": "chrome",                    "canonical": "chrome_slash",    "source": "anticipated" },
    { "term": "shiny robot",               "canonical": "chrome_slash",    "source": "anticipated" },
    { "term": "like a car ad",             "canonical": "chrome_slash",    "source": "anticipated" },

    { "term": "glassy",                    "canonical": "clear_glass",     "source": "anticipated" },
    { "term": "like a bottle",             "canonical": "clear_glass",     "source": "anticipated" },
    { "term": "see-through",               "canonical": "clear_glass",    "source": "anticipated" },

    { "term": "cloth-y",                   "canonical": "soft_fabric",    "source": "anticipated" },
    { "term": "like a hoodie",            "canonical": "soft_fabric",    "source": "anticipated" },
    { "term": "drapery",                   "canonical": "soft_fabric",    "source": "anticipated" },

    { "term": "watery",                    "canonical": "flowing_water",   "source": "anticipated" },
    { "term": "like a river",              "canonical": "flowing_water",   "source": "anticipated" },
    { "term": "splashy",                   "canonical": "flowing_water",   "source": "anticipated" },

    { "term": "furry",                     "canonical": "bristly_fiber",   "source": "anticipated" },
    { "term": "fluffy",                    "canonical": "bristly_fiber",   "source": "anticipated" },
    { "term": "like grass",                "canonical": "bristly_fiber",   "source": "anticipated" },
    { "term": "hairy",                     "canonical": "bristly_fiber",   "source": "anticipated" }
  ],

  "_ambiguous": [
    {
      "term": "shiny",
      "note": "the most commuted material word. chrome_slash, clear_glass, flowing_water, and wet organic_soft are all shiny. highlight *shape* decides, and description rarely carries it. image beats description."
    },
    {
      "term": "soft",
      "note": "material claim (soft_fabric, bristly_fiber), render softness (soft edges, palette/research), or a value key (palette high_key). three domains want this word. never silently resolve."
    },
    {
      "term": "wooden",
      "note": "materials candidate? no: wood without further cues is a texture claim (wood_grain_flow). material-ness needs finish or transport language ("polished wood", "weathered wood"). resolve to textures unless a second signal says substance."
    },
    {
      "term": "glossy",
      "note": "finish value (this folder) or overall finish of the whole image, which is render territory (hard edges, flat fills, print sheen). check whether the gloss is on a depicted object or on the picture."
    },
    {
      "term": "golden",
      "note": "material (metal family) or palette (a gold color scheme on anything). the classic material/color conflation. second signal mandatory."
    }
  ]
}
```
