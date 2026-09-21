# artschool

> a vocabulary curriculum for illustrace. the branch where the user's words learn to talk to the engine's parameters.

users say "chunky chunky filled". the engine wants `stroke_width_cv 0.15, edge_hardness 0.9, texture_energy 0.1`. everything between those two sentences is what lives here. or simply put: this branch is the translation layer, taught like a school, one classroom per visual domain.

each domain answers exactly one question about an image, and each domain uses the same four-file pattern:

| file | job |
|---|---|
| axes.md | the small set of observable questions every image in this domain can answer |
| canonical_tags.md | canonicals = combinations of axis values, plus hints about which engine parameters they touch |
| synonyms.md | user language mapped onto canonicals. append-only, never corrected by deletion |
| examples.md | ground-truth seed images a canonical was derived from. no seed, no canonical |

the pattern is borrowed from ao3's tag wrangling: users tag freely, a wrangler (here: the llm compiler, informed by these files) syns their words onto canonicals, the engine only ever receives canonicals. wrong synonyms are kept as evidence of ambiguity, evidence that a canonical needs a split, not a scolding.

## the domains

| domain | question |
|---|---|
| render/ | what did the marks do to the picture plane? |
| construction/ | where is the camera? |
| spatial/ | how is depth built, and what belongs to which layer? |
| palette/ | what is the color doing? |
| textures/ | what covers the surfaces of the depicted things? |
| materials/ | what do the depicted things read as being made of? |

they are separate folders because conflating them is what makes style transfer apply the wrong shadow direction when you asked for a wash, or treat "pastel" as both a medium and a color mood at once. each domain is one orthogonal dial cluster. users can turn them independently. the engine should too.

## status

| domain | state |
|---|---|
| render/ | seeded. five canonicals from nine session images, synonyms from real user language. the template everything else is copied from. |
| construction/ | researched, unseeded. axes and candidate canonicals exist but no real image has blessed any of them yet. |
| spatial/ | researched, unseeded. depth-cue vocabulary from perceptual psychology and art foundations. |
| palette/ | researched, unseeded. deliberately late. color is the domain most prone to confidently wrong taxonomies. |
| textures/ | researched, unseeded. surface-pattern grammar (stipple, weave, scales, grain, speckle). |
| materials/ | researched, unseeded. substance claims (metal, glass, fabric, water, fur). the least externally-grounded folder: perception science and pipeline vocabulary, no art-education precedent. |
| adaptionlabs/ | the machine side: a synthetic style-description dataset (invented via adaptive data) and an autoscientist run that trains a wrangler model on it. |

## the one rule that keeps this honest

no canonical enters canonical_tags.md without a real image in examples.md that demonstrates it. research can propose, paraphrase, and anticipate synonyms all day. a canonical is a claim about what users mean, and claims get validated against real pictures, not against thesauri.

that rule is why the researched folders carry `candidate_` canonicals that are not canonicals yet. the difference between this and an art-history glossary is that every entry here must eventually cash out as engine parameters on a real image.

## what this is not

not art theory. not movements, periods, or schools. not a glossary of what critics say. the words here are chosen because they describe observable properties of a picture, the kind a measurement or a wrangler can act on. "impressionist" is art history. "marks dissolved into filled shape, edges soft, texture visible" is a fact about pixels.
