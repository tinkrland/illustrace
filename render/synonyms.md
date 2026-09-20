# synonyms

user language mapped to canonical ids. append-only: never delete a synonym even if it seems wrong. wrong synonyms are evidence of ambiguity that needs a better canonical or a split.

`source` tracks where the synonym came from:
- `session`: said directly during the design session that produced this folder
- `inferred`: not said verbatim but clearly implied by context
- `anticipated`: not yet seen but predictable from the pattern

the `_ambiguous` block lists terms that must not auto-resolve. the wrangler should ask for a second signal or an image instead of guessing.

---

```json
{
  "synonyms": [
    { "term": "chunky",                                   "canonical": "block_fill",      "source": "session" },
    { "term": "chunky chunky",                            "canonical": "block_fill",      "source": "session" },
    { "term": "chunky chunky filled",                     "canonical": "block_fill",      "source": "session" },
    { "term": "more shaped shaped than the real shapes",  "canonical": "block_fill",      "source": "session" },
    { "term": "shaped shaped",                            "canonical": "block_fill",      "source": "session" },
    { "term": "not watercolor just colors",               "canonical": "block_fill",      "source": "session" },
    { "term": "like minecraft but painted",               "canonical": "block_fill",      "source": "anticipated" },
    { "term": "minecraft",                                "canonical": "block_fill",      "source": "anticipated" },
    { "term": "flat colors",                              "canonical": "block_fill",      "source": "anticipated" },
    { "term": "color blocks",                             "canonical": "block_fill",      "source": "anticipated" },
    { "term": "blocky",                                   "canonical": "block_fill",      "source": "anticipated" },

    { "term": "lines but colored",                        "canonical": "hatching_color",  "source": "session" },
    { "term": "like colored in with lines",               "canonical": "hatching_color",  "source": "inferred" },
    { "term": "colored pencil",                           "canonical": "hatching_color",  "source": "session" },
    { "term": "crayons",                                  "canonical": "hatching_color",  "source": "session" },
    { "term": "color pencils",                            "canonical": "hatching_color",  "source": "session" },
    { "term": "pen but colored",                          "canonical": "hatching_color",  "source": "inferred" },
    { "term": "lines make the color",                     "canonical": "hatching_color",  "source": "inferred" },
    { "term": "stripy fill",                              "canonical": "hatching_color",  "source": "anticipated" },
    { "term": "hatching with color",                      "canonical": "hatching_color",  "source": "anticipated" },

    { "term": "sketchy",                                  "canonical": "hatching_mono",   "source": "session" },
    { "term": "pen drawing",                              "canonical": "hatching_mono",   "source": "session" },
    { "term": "pen sketch",                               "canonical": "hatching_mono",   "source": "session" },
    { "term": "ink lines",                                "canonical": "hatching_mono",   "source": "anticipated" },
    { "term": "crosshatching",                            "canonical": "hatching_mono",   "source": "anticipated" },
    { "term": "black and white lines",                    "canonical": "hatching_mono",   "source": "anticipated" },
    { "term": "like an architecture drawing",             "canonical": "hatching_mono",   "source": "anticipated" },
    { "term": "technical sketch",                         "canonical": "hatching_mono",   "source": "anticipated" },

    { "term": "marker",                                   "canonical": "wash_gestural",   "source": "session" },
    { "term": "marker but blurry",                        "canonical": "wash_gestural",   "source": "inferred" },
    { "term": "blurry with marks",                        "canonical": "wash_gestural",   "source": "inferred" },
    { "term": "ink wash",                                 "canonical": "wash_gestural",   "source": "anticipated" },
    { "term": "watercolor sketch",                        "canonical": "wash_gestural",   "source": "anticipated" },
    { "term": "watercolor but with lines",                "canonical": "wash_gestural",   "source": "anticipated" },
    { "term": "grey wash",                                "canonical": "wash_gestural",   "source": "anticipated" },
    { "term": "loose and washy",                          "canonical": "wash_gestural",   "source": "anticipated" },

    { "term": "pastel",                                   "canonical": "pastel_open",     "source": "anticipated" },
    { "term": "oil pastel",                               "canonical": "pastel_open",     "source": "anticipated" },
    { "term": "crayon",                                   "canonical": "pastel_open",     "source": "session" },
    { "term": "the white parts are on purpose",           "canonical": "pastel_open",     "source": "session" },
    { "term": "gaps are the light",                       "canonical": "pastel_open",     "source": "inferred" },
    { "term": "not colored everywhere",                   "canonical": "pastel_open",     "source": "session" },
    { "term": "loose scribbles",                          "canonical": "pastel_open",     "source": "anticipated" },
    { "term": "soft and open",                            "canonical": "pastel_open",     "source": "anticipated" }
  ],

  "_ambiguous": [
    {
      "term": "watercolor",
      "note": "could be wash_gestural (if marks visible over wash) or pastel_open (if color is loose with intentional white). needs a second signal or image. do not auto-resolve."
    },
    {
      "term": "painted",
      "note": "too broad. block_fill, wash_gestural, and pastel_open are all painted. needs a second signal."
    },
    {
      "term": "sketchy but colored",
      "note": "could be hatching_color or pastel_open depending on whether lines are systematic or loose. image beats description here."
    }
  ]
}
```

## why append-only

a wrong synonym is data. if users keep saying "crayons" for things that are not pastel_open, that is not a user error, that is the canonical boundary being in the wrong place. the fix is a split or a new axis value, never deleting the evidence.
