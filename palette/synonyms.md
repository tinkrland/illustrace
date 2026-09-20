# palette synonyms

user language mapped to palette candidates. all anticipated. this folder's ambiguity rate will be the highest in the branch: color words are the most conflation-prone in all of illustration language. append-only.

---

```json
{
  "synonyms": [
    { "term": "black and white but stark",     "canonical": "duotone_notan",     "source": "anticipated" },
    { "term": "like a woodcut",               "canonical": "duotone_notan",     "source": "anticipated" },
    { "term": "two colors only",              "canonical": "duotone_notan",     "source": "anticipated" },
    { "term": "risograph-y",                  "canonical": "duotone_notan",     "source": "anticipated" },
    { "term": "poster-y contrast",            "canonical": "duotone_notan",     "source": "anticipated" },

    { "term": "pastel",                        "canonical": "high_key_pastel",  "source": "anticipated" },
    { "term": "soft colors",                   "canonical": "high_key_pastel",  "source": "anticipated" },
    { "term": "light and airy",                "canonical": "high_key_pastel",  "source": "anticipated" },
    { "term": "spring-y",                     "canonical": "high_key_pastel",  "source": "anticipated" },
    { "term": "candy pastel",                  "canonical": "high_key_pastel",  "source": "anticipated" },

    { "term": "earthy",                        "canonical": "earth_muted",      "source": "anticipated" },
    { "term": "muted",                         "canonical": "earth_muted",      "source": "anticipated" },
    { "term": "like dirt colors",              "canonical": "earth_muted",      "source": "anticipated" },
    { "term": "ochre-y",                       "canonical": "earth_muted",      "source": "anticipated" },
    { "term": "vintage",                       "canonical": "earth_muted",      "source": "anticipated" },
    { "term": "plein air colors",              "canonical": "earth_muted",      "source": "anticipated" },

    { "term": "one pop of color",              "canonical": "neon_accent",      "source": "anticipated" },
    { "term": "the red coat",                  "canonical": "neon_accent",      "source": "anticipated" },
    { "term": "mostly grey but one thing glows", "canonical": "neon_accent",   "source": "anticipated" },
    { "term": "neon accents",                  "canonical": "neon_accent",      "source": "anticipated" },

    { "term": "cartoon colors",                "canonical": "classic_triad",   "source": "anticipated" },
    { "term": "toy colors",                    "canonical": "classic_triad",   "source": "anticipated" },
    { "term": "primary colors",                "canonical": "classic_triad",   "source": "anticipated" },
    { "term": "candy",                         "canonical": "classic_triad",   "source": "anticipated" }
  ],

  "_ambiguous": [
    {
      "term": "colorful",
      "note": "saturation_mode says loud, but the hue scheme is unspecified. classic_triad, neon_accent, or unrestricted all fit. needs a second signal."
    },
    {
      "term": "pastel",
      "note": "the canonical conflation trap. palette mood (high_key_pastel) or render type (render/pastel_open: dry medium marks with intentional white). the wrangler must determine which domain the user means, or ask. never silently pick one."
    },
    {
      "term": "vintage",
      "note": "could be earth_muted (palette) or aged texture and paper grain (render). the word carries both. image beats description."
    },
    {
      "term": "muted",
      "note": "desaturation (palette: muted / earth_muted) or atmospheric fade of distance (spatial: atmospheric_haze). check where the muteness lives before resolving."
    },
    {
      "term": "warm",
      "note": "temperature bias confirms but nothing else. resolves to no palette canonical alone. a second signal is mandatory."
    }
  ]
}
```

## the cross-domain ambiguity protocol

when a synonym appears in more than one folder's `_ambiguous` list ("muted", "3d looking", "pastel"), the wrangler must resolve the domain before the canonical. the protocol: ask, or take an image. the one thing it must never do is pick the domain it has the best prior for. this vocabulary system is for users who know exactly what they want. guessing is the bug.
