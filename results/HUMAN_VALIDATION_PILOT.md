# human-validation pilot: judge 1 (anonymous)

first live survey session through the packaged zip: 1 judge, 12 pairs
(10 scored, 2 catch), ~67 seconds, confidence recorded per answer.
source: `survey/processed/4ed785560_survey_results_anonymous_1788981271664.json`
(csv twin logged in the same folder, not ingested separately).
normalized records: `survey/judgments_out.json`. n=1, so every number below is
a hypothesis for the next judge batch, not a verdict.

## agreement vs ground truth

| dimension | agreement | notes |
|---|---|---|
| roughness (jitter) | 3/3 | every jitter step correct, "pretty sure" to "very sure" |
| roughness (taper) | 0/1 | heavy taper read as *smoother*, not rougher |
| texture (grain) | 1/2 | grain_8 vs grain_14 correct; grain_0 vs grain_8 missed at "a little" |
| line_weight | 1/1 | "very sure" |
| color_temperature | 1/1 | "very sure" |
| lighting | 0/2 | "very sure" both times — and the judge was right |

catch pairs (identical images): 2/2 answered, no refusals.

## finding 1: the lighting gt was inverted (stimuli bug, not metric bug)

the judge chose light0 as "more warmly lit" with high confidence, twice.
measured on the stimuli themselves: lighting strength brightens the subject
(central crop luminance 133.1 -> 135.9 -> 137.7) but *cools* the cast, because
the soft-light color #ffedd0 (r-b 47) is cooler than the very warm base palette
(r-b 91 canvas, 120 central). the prompt asked about warmth; the parameter
moves brightness. gt direction relative to the validated metric was correct,
the *wording* was inverted.

action taken: q10/q11 prompts reworded to "which one feels brighter / more
strongly lit?" and the zip repackaged. lighting_strength keeps its validated
status (luminance over fixed-support interiors) — this is a prompt/parameter
alignment fix caught by the survey before any external judge saw it.

## finding 2: taper direction refuted at n=1

the stimuli note hypothesized "varied widths read as rougher" (heavy taper =
calligraphic width variation). this judge read near-uniform width as rougher
and heavy taper as smoother/more polished. recorded as a live refutation
candidate; needs more judges before touching the gt.

## finding 3: possible perceptual floor for grain

grain_0 vs grain_8 (the weakest step) missed at "a little" confidence while
grain_8 vs grain_14 was a confident hit. consistent with a perceptual floor on
the substrate rather than metric failure. next batch should watch this pair.

## judge quality

67s for 12 pairs is fast but not implausible for pairwise choice; answers are
directionally coherent (10/10 non-catch answers with a stated opinion, catch
pairs answered without flagging). "pretty sure" on an identical catch pair
suggests mild overconfidence; more judges needed before reading anything into it.

## xano sync status

judgments_out.json is the source of truth locally. the stylebench_human_judgments
table + /judgments endpoint are not yet provisioned (metadata api unreachable
from the sandbox at ingest time — api.xano.com dns failing, runtime endpoints
fine). provisioning is queued behind that; run records are unaffected.
