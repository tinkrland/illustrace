---
status: positioning doc — what illustrace is building and, just as deliberately, what it refuses
---

# positioning: first principles, not mystery knobs

the project aim is **multi-reference style mixing**: a node-based compositional
engine where several reference images each contribute a chosen component to
one output, instead of one reference being imitated wholesale. one reference
lends the mark-making, another the color language, a third the edge
treatment, and the user decides which component comes from where.

the technical focus is the hard pair that comes with that aim:

* **component mixing** — mark-making, shape language, edge entropy, and
  color language as separately controlled factors, each with its own
  strength and its own reference.
* **multi-reference routing without parameter bleed** — routing says
  which reference feeds which component; bleed is the failure mode where
  reference A's palette leaks into the component that was supposed to
  come from reference B. routing correctness is a testable claim, not a
  hope (see the stylebench leakage and independence claims).

## what we are intentionally rejecting

the standard path is faster: take a pre-existing style-transfer block,
bolt on more references, and tune until outputs look nice. we reject it
deliberately. the core philosophy:

> you cannot fix style transfer by just turning a mystery knob on a
> pre-existing block. you have to break it down and build it up from
> scratch again.

"mystery knob" is not a strawman. today's black-box transfer works
exactly like that: latent-space interpolation between the content image
and the reference image, steered by a handful of scalar weights nobody
can interpret. when the result drifts, the only move is another knob
turn and another vibe check. the mush cannot be debugged because there
is nothing inside it to point at.

the cost of that speed is the mush: outputs that vibe-match the
reference, cannot be measured, cannot be edited after the fact, and
transfer attributes the user never asked for. every "style" knob in a
black-box stack is a proxy for factors the stack never actually
identified.

## why first principles

by decomposing style into its individual foundation stones, we know
exactly what the pieces are: mark-making, shape language, edge entropy,
color language. each one is measurable on a corpus (stylometrics), each
one is independently transferable in principle, and each one can be
validated against human judgment before any transfer operator is built.
that validation gate is the whole reason the research layer exists:
measurement first, human validation second, operators last.

this time around, we can build a strong, deterministic structure where
style and content are genuinely disentangled, rather than relying on the
loose vibes of a latent-space mush. deterministic here has a precise
meaning:

* the same inputs produce the same output, so failures reproduce;
* each component's contribution is attributable, so bleed can be
  detected by measurement, not by squinting;
* a preset is a recipe of components, strengths, and routing, not a
  rendered image, so it can be inspected, edited, and recombined.

none of that is possible on top of a block whose internals nobody can
see. it is only possible if style is broken down to its foundation
stones first, built back up with measurement at every step, and only
then exposed to the user as composable parts.

## what this means in practice

the pipeline is ordered so that rigor stays cheap: measure candidate
factors on reference corpora, validate the measurements against human
judgment (stylebench), then build transfer operators per component, and
only then compose multi-reference routing on top. the application layer
(see [README.md](README.md)) inherits this structure directly: its
sliders are the measured factors, its presets are recipes, its claims
are the stylebench claims (independence, strength control, leakage,
recombination).

slower than the black-box path, deliberately. the black-box path ships a
demo first and discovers it cannot deliver intent later. this path ships
claims it can test, in the order they can be tested.
