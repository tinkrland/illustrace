---
status: v0 — the honest list of what can break the stylometrics thesis (2026-09-19)
---

# bottlenecks

illustrace is an attempt to apply **metrology** to art: the working bet is that
computer vision can be treated like actual art theory, that the elements of art
(line, shape, color, texture, value) can become *measured quantities* with
defined units, uncertainty, and validation against human perception, the way
metrology treats length or voltage. not "ai understands art" — rather: art
theory already wrote down the decomposition, we give it instruments.

the deep dive (research/STYLOMETRY_DEEP_DIVE.md) found strong precedent for
measurability: brushstroke width/orientation validated against human subjects
(cepolina 2014), texture as a finite statistic vector (portilla-simoncelli),
color statistics carrying style signal on their own. so the metrology bet is
not crazy. but three bottlenecks sit between "measurable" and "decomposable
and transferable," and this note keeps them visible instead of buried.

## 1. the orthogonality illusion

the factor sliders pretend the factors are orthogonal axes. they are not.
visual systems interact: rougher stroke jitter changes perceived texture
energy and edge softness at the same time; a warm palette shift changes
perceived texture contrast. treating factors as independent is a useful
fiction that becomes a lie the moment cross-factor interactions dominate
the perceptual result.

metrology has an answer to this and it is not "pretend independence": it is
the **uncertainty budget**, where cross-terms are measured and stated. the
stylebench equivalent is an explicit interaction test: perturb one factor,
measure which *other* factors' readings move. a factor only earns slider
status once its cross-terms are quantified, not before.

## 2. human perceptual anchoring

metrology validates instruments against references. our reference is human
perception — but humans do not perceive style factor-by-factor; they form a
holistic impression first and each factor judgment is anchored by it. ask
"which is rougher" and the answer is contaminated by which one they *liked*,
which is more *familiar*, which subject they recognize. the judgment you
elicit is not the factor you think you measured.

this is not fatal (psychophysics exists, fechner built forced-choice
protocols for exactly this), but it constrains validation hard: single-factor
delta stimuli, randomized ladders, expertise effects controlled, and survey
questions that cannot be answered from the holistic gestalt alone. our
pilot preference pairs were built this way on purpose; every future survey
has to keep that discipline or the "validated" rung is fake.

## 3. latent feature entanglement

learned representations entangle factors. a gram matrix, a clip embedding, a
diffusion model's internal features — none of them have an axis that is
"stroke width" and only stroke width; moving the style dial moves many
correlated things at once. li et al. 2017 showed style transfer is
distribution alignment and that no representation is canonical, which frees
us to pick interpretable statistics, but it does not guarantee those
statistics are any less correlated in the wild.

the hedge is already the thesis: prefer handcrafted, interpretable
statistics (palette in lab space, stroke width cv, wavelet texture energy)
over hidden features, precisely because their cross-correlations can be
measured and reported. but the bottleneck stands: any learned operator
(spec models, lora adapters) inherits the entanglement of its
representation, and per-factor claims through a learned operator need the
same interaction tests as raw sliders.

## what this file is for

every one of these can quietly invalidate a stylebench claim if it is
unexamined: the orthogonality illusion breaks "independence," anchoring
breaks "validated against human judgment," entanglement breaks
"controllable." the experiment design checklist for any factor promotion
must therefore include:

- [ ] single-factor delta stimuli only
- [ ] cross-factor interaction measured (which other readings move)
- [ ] forced-choice survey immune to gestalt answering
- [ ] if a learned operator is involved: entanglement audit on its features
