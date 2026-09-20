# spatial synonyms

user language mapped to spatial candidates. all anticipated, no session language yet. append-only.

---

```json
{
  "synonyms": [
    { "term": "flat",                        "canonical": "flat_graphic",       "source": "anticipated" },
    { "term": "no depth",                    "canonical": "flat_graphic",       "source": "anticipated" },
    { "term": "everything in one plane",     "canonical": "flat_graphic",       "source": "anticipated" },
    { "term": "sticker-like",               "canonical": "flat_graphic",       "source": "anticipated" },
    { "term": "like an icon",                "canonical": "flat_graphic",       "source": "anticipated" },

    { "term": "paper cutout",               "canonical": "paper_cut_layers",   "source": "anticipated" },
    { "term": "layers",                     "canonical": "paper_cut_layers",   "source": "anticipated" },
    { "term": "like paper layers",           "canonical": "paper_cut_layers",   "source": "anticipated" },
    { "term": "stacked",                    "canonical": "paper_cut_layers",   "source": "anticipated" },
    { "term": "like a shadow box",          "canonical": "paper_cut_layers",   "source": "anticipated" },
    { "term": "parallax-y",                 "canonical": "paper_cut_layers",   "source": "anticipated" },

    { "term": "misty mountains",            "canonical": "atmospheric_haze",   "source": "anticipated" },
    { "term": "faded background",           "canonical": "atmospheric_haze",   "source": "anticipated" },
    { "term": "hazy distance",              "canonical": "atmospheric_haze",   "source": "anticipated" },
    { "term": "the distance goes blue",     "canonical": "atmospheric_haze",   "source": "anticipated" },
    { "term": "atmospheric",                "canonical": "atmospheric_haze",   "source": "anticipated" },
    { "term": "foggy depth",                "canonical": "atmospheric_haze",   "source": "anticipated" },
    { "term": "like chinese ink landscapes", "canonical": "atmospheric_haze",   "source": "anticipated" },

    { "term": "foreground pops",            "canonical": "diorama_stages",     "source": "anticipated" },
    { "term": "front middle back",           "canonical": "diorama_stages",     "source": "anticipated" },
    { "term": "theater stage-y",            "canonical": "diorama_stages",     "source": "anticipated" },
    { "term": "diorama",                    "canonical": "diorama_stages",     "source": "anticipated" },
    { "term": "staged",                     "canonical": "diorama_stages",     "source": "anticipated" }
  ],

  "_ambiguous": [
    {
      "term": "depth",
      "note": "names the whole folder. resolves to nothing by itself."
    },
    {
      "term": "3d looking",
      "note": "shared with construction/synonyms.md. could mean camera geometry (construction) or depth treatment (spatial). the wrangler should ask which is meant, or take an image."
    },
    {
      "term": "misty",
      "note": "could be atmospheric_haze (spatial) or a rendering/texture effect (render). if the fog is surface texture rather than distance grading it belongs to render. image beats description."
    }
  ]
}
```
