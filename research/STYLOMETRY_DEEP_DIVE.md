---
status: source-grounded literature dive into stylometry + art-style quantification, mapped against the illustrace factor list (2026-09-19)
---

# stylometry deep dive: what the literature actually measures

the stylebench thesis says style decomposes into measurable, independently
transferable factors. this dive asks: does anyone else already measure style
that way, what do they measure, and how do they validate it? sources pulled
via tavily search + firecrawl scrape (raw notes in conversation workspace,
not committed).

## 1. stylometry proper: the text-origin discipline

stylometry predates visual style analysis by a century. its core construct is
the **writer invariant**: "a property held in common by all texts ... written
by a given author" ([wikipedia/stylometry](https://en.wikipedia.org/wiki/Stylometry)).
the classic pipeline:

1. pick unconscious, high-frequency, low-salience features (function words,
   the 50 most common words) rather than conscious, content-bearing ones;
2. chunk text into windows, measure feature frequencies per chunk;
3. project chunk-vectors into low-d space (pca) and look at clustering.

three lessons transfer directly to visual stylometrics:

* **invariance comes from unconscious habit.** style lives in features the
  maker does not deliberately attend to. for illustrators that predicts
  mark-making, edge treatment, and spacing habits carry more style signal
  than subject matter — exactly the decomposition we claim.
* **statistics over a corpus, not per-image truth.** a style is a
  distribution over many samples, not a property of one image. our corpus
  profiling (palette deltas, stroke cv over 39+ works) is the same move.
* **low-d projection for legibility.** the pca step exists so a human can
  look at the style. our composer's palette gravity is the same instinct.

## 2. what computer vision already measures, per factor

### mark-making / brushstrokes

the most direct precedent. "computer-assisted analysis of painting
brushstrokes" (cepolina et al., 2014,
[springer](https://link.springer.com/article/10.1186/1687-5281-2014-53))
extracts individual brushstrokes from van gogh's paintings via
segmentation + shape/area constraints, then computes **orientation, length,
and width** per stroke — and, crucially, **validates the metrics against
human subjects' observations** ("results that are rather close to those
obtained by human subjects"). that is our stroke_width_cv metric family,
with the validation protocol we keep saying comes first.

adjacent precedents in the same lineage: stroke-ending-shape classification
(vill & sablatnig), patch-level aggregate features for artist id (keren
2002: rembrandt vs van gogh vs picasso vs magritte vs dali), texture-based
authentication (berezhnoy: circular filter -> skeleton -> polynomial fit
-> point cloud per artist), multifractal analysis of bruegel drawings
(wendt/jaffard/abry 2012). yale's "decoupling strokes and high-level
attributes" ([pdf](https://graphics.cs.yale.edu/sites/default/files/strokes.pdf))
does the separation explicitly: stroke-level descriptors disentangled from
semantic attributes.

### texture

portilla-simoncelli ([parametric texture model,
2000](https://www.cns.nyu.edu/~lcv/texture/)) is the canonical answer:
texture = a fixed set of **marginal statistics + cross-scale and
cross-orientation correlations** of wavelet coefficients (~700 numbers),
sufficient for indistinguishable synthesis. this is the strongest
literature support for texture_energy being a real, measurable factor —
and it is a *recipe*, not a monolith: statistics you can list, inspect,
and perturb one at a time. that is the illustrace notion of a factor.

### color

a 2026 nature scientific reports study "experimentally validates the
critical role of color characteristics" in style recognition
([nature](https://www.nature.com/articles/s41598-026-51895-z)) — color
statistics alone carry substantial style signal. color histograms + edge
features are repeatedly observed to "quantify artistic style"
(cepolina et al. and refs within). our palette delta-e in lab space is a
perceptually-motivated refinement of this line, not an invention.

### style as a whole (classification / "deep" features)

the wikiart ecosystem dominates style *classification* (an mdpi survey
notes the field's "clear concentration around wikiart and wikiart-derived
collections"). elgammal et al. ("the shape of art history in the eyes of
the machine") quantify influence links with learned features. important
nuance: classification accuracy proves a style *signature exists* in the
feature; it does not give you a *controllable decomposition*. cnn
features are evidence for measurability, not a transfer architecture.

### what style transfer research says style *is*

"demystifying neural style transfer" (li et al., ijcai 2017,
[pdf](https://www.ijcai.org/proceedings/2017/0310.pdf)) proves the gram
matrix loss is an **mmd distribution alignment** between neural
activations — and that other alignment methods (linear-kernel mmd,
moment matching) "achieve diverse but all reasonable style transfer
results." read from our side:

* style matching = matching feature *distributions* between images —
  style is statistical, which is the stylometric claim again;
* the gram matrix specifically is **not necessary** — second-order
  stats are sufficient but not unique. there is no single canonical
  style representation; multiple statistics of the same signal work.
  this legitimizes choosing *interpretable* statistics (palette,
  stroke width, edge entropy) over hidden ones, provided they
  validate against human judgment.

## 3. the art-historical vocabulary (formal analysis)

formal analysis (khan academy, massart, getty lines) decomposes an
artwork's *visible* structure into elements: **line, shape, form, color,
value, texture, space** (+ pattern), organized by principles (balance,
contrast, rhythm, emphasis, movement, proportion, unity). two takeaways:

* the elements-of-art list and our factor ontology are near-isomorphic
  for the 2d layer (line -> mark-making, shape -> shape language,
  color+value -> color language, texture -> texture). ours is not a
  novel taxonomy, and we should say so; novelty is the measurement +
  validation + per-factor transfer, not the vocabulary.
* art history's decomposition was built for *description*; nobody made
  each element independently measurable or transferable. the gap is
  exactly where stylebench lives.

## 4. experimental aesthetics: validation has a discipline too

fechner founded empirical aesthetics (psychophysics applied to art);
modern overviews: iep.utm.edu/empirical-aesthetics,
"the experimental aesthetics of style" (siefkes et al., 2013) argues
style perception is **multimodal** and must be studied experimentally
across modes. the practical warnings for stylebench survey design:
expertise effects (nodine et al.), cross-cultural universals vs
variation (symmetry preference), and that perceptual experiments need
forced-choice designs with controlled stimuli — which our pilot
preference pairs (roughness/texture/line weight jitter ladders) already
are. the van gogh brushstroke paper's human-subject comparison is the
template for metric validation.

## 5. synthesis: the mapping table

| illustrace factor | literature precedent | measurement family | validated vs humans? |
|---|---|---|---|
| mark-making | cepolina 2014 (van gogh strokes) | stroke orientation/length/width distributions | yes (2014) |
| texture | portilla-simoncelli 2000 | wavelet marginals + correlations | yes (synthesis indistinguishability) |
| color | nature 2026 + histogram line | palette stats, perceptual color spaces | partially (classification probes) |
| edge language | cepolina ref-web (edge features) | edge direction entropy, gradient stats | no (candidate) |
| "style" (whole) | wikiart classification; gram/mmd | cnn features, distribution alignment | n/a (existence proof only) |
| decomposition itself | elements of art (art history) | descriptive vocabulary, not measurable | n/a (the gap) |

conclusions worth pinning:

1. **measurability is settled science.** brushstrokes, texture, color have
   decades of quantification precedent. nobody should fear the claim
   "style factors are measurable."
2. **validation against humans is also precedented** — we are not
   inventing the methodology, we are applying fechner's discipline to a
   decomposition art history already wrote down.
3. **no one has made the factors independent or composable.** the
   literature measures to *classify or authenticate*, not to *transfer
   per-factor with routing*. that remains the open, unclaimed question.
4. interpretable statistics are a legitimate choice, not a compromise —
   the gram-must- fall (li 2017) means representations are plural, so
   pick the ones you can validate and expose as sliders.

## next steps this licenses

- promote stroke_width_cv and texture_energy candidate metrics toward
  the validated rung using the cepolina protocol: corpus measurement
  vs human-subject forced choice (our judgment survey format).
- treat palette (delta-e in lab) as a third candidate with the same
  protocol.
- keep edge_direction_entropy as a candidate but do not promote until
  it survives its own ladder rung (no human-validation precedent found).
- in docs: credit the elements-of-art vocabulary openly; claim novelty
  only for measurement+validation+per-factor transfer.
