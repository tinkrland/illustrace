---
status: application-layer concept doc — the practical tool built on the research layer
---

# application: style composer

`research/` + `stylebench` ask whether style decomposes into measurable, validatable
factors. this folder is what happens if the answer is yes: **style composer** — the
illustrace application layer that applies the pilot research as an actual workflow.

illustrace (practical implementation concept) aims to rethink how "style transfer" works.
instead of treating a reference image as something to copy wholesale, illustrace treats
every visual style as a collection of independent artistic attributes that can be
extracted, mixed, controlled, and reused.

## the problem: reference intent

traditional style transfer tools typically operate like this:

```
image + reference = new image
```

the model attempts to imitate the *entire* reference image. this fails because it does
not understand *intent*. when a user provides a reference image, they are usually not
asking to recreate the composition, subject matter, text, layout, or objects. they are
trying to communicate visual qualities:

* "i like these brush strokes."
* "i want this watercolor texture."
* "use this artist's line quality."
* "keep my illustration, but color it like this."
* "borrow the rendering style without copying anything else."

wholesale transfer causes the predictable failures:

* copies layout
* copies poses
* copies objects
* copies backgrounds
* copies typography
* recreates decorative elements
* misunderstands ui screenshots
* cannot distinguish what the user actually wanted

for ui and illustration work, that's poor creative control. style composer is built
around the intent workflow instead.

## the solution: choose exactly which characteristics transfer

illustrace automatically analyzes every reference image into separate visual systems.
instead of transferring "the style," users choose exactly which characteristics they
want:

* stroke style
* coloring
* rendering
* shading
* textures
* geometry
* proportions
* lighting
* edge treatment
* decorative language
* visual effects

everything else can be ignored.

## visual style decomposition

every analyzed image becomes something conceptually like:

```
style
├── stroke
├── geometry
├── proportions
├── rendering
├── color
├── texture
├── shading
├── lighting
├── edge treatment
├── decoration
├── composition        ← disabled by default
├── typography         ← disabled by default
├── ui elements        ← disabled by default
├── subject matter     ← disabled by default
└── objects            ← disabled by default
```

the content-bearing categories (composition, typography, ui, subject, objects) are
disabled by default — intent, not imitation, is the default.

## reference understanding

instead of assuming every pixel is important, style composer first separates a
reference into different kinds of information:

```
illustration / text / logos / buttons / icons / background / objects / decorations / layout
```

users decide which categories participate in style extraction. this makes the tool
especially useful for:

* figma / ui references
* concept art
* editorial illustration
* storybook illustration
* design inspiration boards
* screenshots

## component transfer

every artistic component can be enabled or disabled independently:

```
✓ stroke    ✓ color     ✓ texture    ✓ shading
✓ rendering
✗ composition   ✗ objects   ✗ typography   ✗ ui   ✗ pose
```

the output keeps the user's artwork while borrowing only the selected characteristics.

## multiple reference images

each artistic component can have its own source — the heart of the compositional idea:

```
stroke    → illustration a
color     → illustration b
texture   → illustration c
lighting  → illustration d
rendering → illustration e
```

this creates entirely new visual styles that never existed before. no single reference
image contains the target style; the user composes it.

## adjustable strength

every component has an independent intensity slider — never a single global
"style strength" knob:

```
stroke 100%   color 70%   texture 35%   lighting 85%   geometry 20%
```

in the research layer this maps to *strength = distance traveled through style space*
per factor (see research/STYLEBENCH_THESIS.md): 70% means the measured component moved
70% of the way from the artwork's value to the reference's value.

## local preset system

users can save reusable style recipes. presets store:

* enabled components
* disabled components
* component strengths
* assigned references
* extraction settings

**not rendered images.** presets work like photoshop brushes, lightroom presets, or
figma styles — recipes, not artifacts.

this holds for word-bearing work too. lettering, wordmarks, and logo-with-text
requests come out as editable assets — font files, glyph sheets, layered
vector with per-glyph overrides — never as flattened images. a font is the
purest form of the preset idea: glyphs as parametric vector paths, spacing as
parameters, color and texture as recipe layers. (typography still transfers
*off* by default — a reference's typeface is its content, not its style.)

## style recipes

presets can be combined, composing completely new visual identities:

```
comic linework × muted editorial colors × watercolor texture × storybook rendering
```

## who this is built for: execution, not inspiration

style composer is built for people who already know, almost exactly, what they
want. the picture already exists in their head; the tool's only job is to make
that image come forth. we are outsourcing the *execution*, never the inspiration,
never the thinking.

that stance puts illustrace firmly against the "prompt and see what the ai
makes" school of tools. no slot machine, no interpretive surprises, no "here's
what i came up with." the user is not asking to be shown anything new. they are
asking for a very fast, very obedient pair of hands, and the tool that surprises
them is the tool that failed.

this is why every control in this doc is explicit: which components transfer,
how far each one moves, from which reference. surprise is a bug, not a feature.

## ideal users

illustrators, concept artists, ui designers, graphic designers, editorial artists,
game artists, children's book illustrators, comic artists, visual development artists,
art directors.

## philosophy

style is not one thing.

style is the interaction of many independent visual systems.

the intent is never in question. the user already knows what the picture should
be; execution is all we do, and any surprise on the way out is a defect.

illustrace lets artists work with those systems directly instead of forcing them into
all-or-nothing style transfer.

---

note for research readers: every capability above is a testable claim. component
independence is stylebench's independence test; per-component strength predictability is
its strength-control test; reference-content leakage is its leakage test; multi-reference
combination is its recombination test. the application layer is the research layer, worn
as a tool.
