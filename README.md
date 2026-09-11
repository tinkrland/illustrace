# charatrace

every stylized character illustration is one drawing of a character who could have been drawn a thousand other ways. illustrace measures how something is drawn. charatrace keeps who is drawn constant while everything else about the drawing changes. the long-term scope, parked here on its own branch until illustrace earns it.

or simply put: the pinterest comments are the whole thesis. someone posts a stylized girl and the replies say "wow she'd look just like me if she was brunette and taller." charatrace is the tool that actually makes her brunette and taller, and hands back the same character, not a lookalike, not a re-imagining, not the model's own interpretation of her.

## what it is

a half sibling to illustrace, not a feature of it. illustrace treats style as an independent, measurable, compositional system (stylometrics: mark-making, shape, color, rendering, texture, edge language, each validated separately). charatrace takes that solved style substrate and applies it to one harder problem: the character herself, as a persistent, parametric entity. same style every time, same character every time, different drawing every time.

stylized only, forever. no photorealism, no real-person likeness, same scope rule illustrace already holds. the test of an asset is not "is it impressive" but "is it still her."

## the pillars, in order

### picrewify

the first axis: features swap within the style. hair, nose, height, build, proportions, accessories. the character is fitted as a set of editable part slots in her own art style, so changing the hair changes *her* hair drawn *her* way, not a generic hair asset pasted on. this is identity as a parametric layer. the user asks for brunette and taller and gets exactly that, at the strength asked for, with zero surprise. [characraft](/characraft) is the product surface this pillar builds toward: the actual picrew-style create-and-save flow.

### rigposer

the second axis: pose. the drawing is limb-aware, a 2d rig living under the flat image, so the character re-poses like a real doll: fold her up, sit her down, turn her shoulders. the output stays a flat stylized drawing indistinguishable from one the original artist made in that pose. the rig is invisible scaffolding, never the deliverable. this is what makes a [characraft](/characraft) character reusable across scenes instead of a single saved pose.

### camera angle switcher

the third axis: viewpoint. the same character redrawn from a different angle, with camera distance, framing, and lighting adjusted. front, profile, three-quarter, looking up, looking down. consistency of character and style across viewpoint change is the claim being tested, per viewpoint, the same way illustrace tests each style factor.

### backgrounds (explicitly not scope)

set design is an afterthought and is not part of charatrace. characters pose in the void. maybe someday, much much later, after illustrace is done and charatrace has earned its own pillars, backgrounds get a research pass. until then: nothing, and that's a decision, not a gap.

## the folders so far

- [characraft](/characraft): the character creator, presets plus picrew-style customization plus save-to-account plus reusable posing. parked, presets not designed yet.
- [factories](/factories): charatrace's own factories (separate from illustrace's), the expressive and doodled asset families closer to the character herself. [emotica](/factories/emotica) (consistent-style emoticon and expression sets) and [scribbleria](/factories/scribbleria) (scribbled, loose-line doodle marks, likely source of characraft's doodled base linework).

## what it inherits

- the style substrate: mark-making, palette, rendering factors, all measured and validated by illustrace's machinery. charatrace consumes stylometrics, it doesn't rebuild them.
- the philosophy: high-intent execution, not creative collaboration. the user knows the character; the engine executes. surprise is a bug.
- the method: every pillar ships as a preregistered, testable claim (is it still her? is it still her style? across swaps, poses, angles) before anything is built to "just work."
- the architecture instinct: parametric, layered, editable outputs. never baked, never flattened, never a static render pretending to be a system.

## sequencing

illustrace first, charatrace after. the style machinery has to exist and be validated before character persistence can sit on top of it. this readme is the only artifact on purpose: the branch is the north star, not the roadmap. when work starts, it starts with claims and a stylebench-style validation loop, same as everything else.
