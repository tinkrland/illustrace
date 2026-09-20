# construction synonyms

user language mapped to construction candidates. all entries here are `anticipated`: none of these words was said in a session yet. that makes this the first file in the branch to be entirely prediction, which is fine for synonyms (the wrangler will verify against images when they arrive) and forbidden for canonicals.

append-only, same as render. when real session language lands, entries gain `source: session` and stay in place.

---

```json
{
  "synonyms": [
    { "term": "flat like a kids book",        "canonical": "flat_parallel",     "source": "anticipated" },
    { "term": "no perspective",               "canonical": "flat_parallel",     "source": "anticipated" },
    { "term": "everything facing the camera","canonical": "flat_parallel",     "source": "anticipated" },
    { "term": "isometric",                   "canonical": "flat_parallel",     "source": "anticipated" },
    { "term": "storybook flat",              "canonical": "flat_parallel",     "source": "anticipated" },
    { "term": "like a stage backdrop",        "canonical": "flat_parallel",     "source": "anticipated" },

    { "term": "like the road goes into the picture", "canonical": "one_point_deep", "source": "anticipated" },
    { "term": "tunnel view",                 "canonical": "one_point_deep",     "source": "anticipated" },
    { "term": "everything pointing inward",  "canonical": "one_point_deep",     "source": "anticipated" },
    { "term": "vanishing point",             "canonical": "one_point_deep",     "source": "anticipated" },

    { "term": "like you're standing there",  "canonical": "eye_level_natural",  "source": "anticipated" },
    { "term": "normal view",                 "canonical": "eye_level_natural",  "source": "anticipated" },
    { "term": "street corner view",          "canonical": "eye_level_natural",  "source": "anticipated" },
    { "term": "eye level",                   "canonical": "eye_level_natural",  "source": "anticipated" },

    { "term": "looking up at it",            "canonical": "worms_eye",         "source": "anticipated" },
    { "term": "from below",                  "canonical": "worms_eye",         "source": "anticipated" },
    { "term": "low angle",                  "canonical": "worms_eye",         "source": "anticipated" },
    { "term": "worm's eye",                 "canonical": "worms_eye",         "source": "anticipated" },
    { "term": "towering",                   "canonical": "worms_eye",         "source": "anticipated" },
    { "term": "hero shot",                  "canonical": "worms_eye",         "source": "anticipated" },

    { "term": "from above",                 "canonical": "birds_eye",         "source": "anticipated" },
    { "term": "bird's eye",                 "canonical": "birds_eye",         "source": "anticipated" },
    { "term": "high angle",                 "canonical": "birds_eye",         "source": "anticipated" },
    { "term": "looking down on it",         "canonical": "birds_eye",         "source": "anticipated" },
    { "term": "god view",                   "canonical": "birds_eye",         "source": "anticipated" },
    { "term": "like a map",                 "canonical": "birds_eye",         "source": "anticipated" },

    { "term": "fisheye",                    "canonical": "fisheye_curved",     "source": "anticipated" },
    { "term": "warped",                     "canonical": "fisheye_curved",     "source": "anticipated" },
    { "term": "lens-y",                     "canonical": "fisheye_curved",     "source": "anticipated" },
    { "term": "wide angle",                 "canonical": "fisheye_curved",     "source": "anticipated" }
  ],

  "_ambiguous": [
    {
      "term": "dramatic angle",
      "note": "could be worms_eye, birds_eye, or fisheye_curved depending on which way the drama points. needs a second signal or image."
    },
    {
      "term": "3d looking",
      "note": "says depth or construction exists but not which system. any projective_system value could be behind it. do not auto-resolve."
    },
    {
      "term": "dutch angle",
      "note": "camera roll, not camera position. no axis covers roll yet. this synonym parking itself in _ambiguous is the signal that a roll axis may be needed."
    },
    {
      "term": "perspective",
      "note": "the word names the entire folder. by itself it resolves to nothing."
    }
  ]
}
```
