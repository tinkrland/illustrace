# survey — human judgment validation

this directory contains the illustrace stylebench human-judgment validation survey:
a lightweight, single-page static app that presents pairwise style comparisons to
judges, downloads their responses as JSON/CSV, and an ingestion script that normalises
those responses into `human_judgments` table records.

the science note: this survey validates that human perception orders style factors the
same way the measured parameters do. if judges consistently pick the provably higher-parameter
image as more rough / more textured / heavier / cooler / warmer, it confirms that the
computed metrics are perceptually meaningful. see `results/SVG_SUBSTRATE_RUN2.md` for
the metric results this is validated against.

---

## files

```
survey/
  index.html       — the survey app (single-page, no build step, no cdn)
  stimuli.json     — 12 pairwise questions + ground truth (version-controlled)
  ingest.py        — normalises downloaded results into human_judgments records
  judgments_out.json — written by ingest.py (gitignored; re-generated per run)
  README.md        — this file
```

---

## serving

images live at `../data/generated/arch_svg/` relative to `survey/` — they are
referenced with those paths in `stimuli.json` and in the `<img>` tags of the app.
serve from the **repo root** so the relative paths resolve correctly:

```bash
# from repo root:
python3 -m http.server 8080
# then open:  http://localhost:8080/survey/
```

do **not** open `survey/index.html` as a `file://` url: `fetch("stimuli.json")`
will be blocked by CORS restrictions in most browsers.

---

## running a session

1. open `http://localhost:8080/survey/` in a browser.
2. optionally enter a judge id (leave blank for anonymous).
3. for each of the 12 question pairs, click the image that matches the prompt,
   then choose a confidence level (a little / pretty sure / very sure), then click next.
4. on the done screen, click **download JSON** (or CSV).
5. save the file — it is not transmitted anywhere; it only lives in the browser.

left/right order is randomised per question at runtime. the downloaded file records
the filename chosen (not "left" or "right"), so ingestion can join to ground truth
regardless of the randomisation.

---

## ingesting results

```bash
# normalise and write survey/judgments_out.json:
python survey/ingest.py path/to/survey_results_judge_xxx.json

# validate only (no file written):
python survey/ingest.py path/to/survey_results_judge_xxx.json --dry-run
```

ingest prints a per-dimension agreement summary and catch-pair stats to stdout.
records that fail schema validation are skipped with a reason printed to stderr.

---

## results format (downloaded JSON)

```json
{
  "judge_id": "jdoe",
  "started_at": "2024-01-01T10:00:00.000Z",
  "completed_at": "2024-01-01T10:05:32.000Z",
  "answers": [
    {
      "question_id": "q01",
      "dimension": "roughness",
      "prompt": "which linework feels rougher / more hand-drawn?",
      "left_file": "jit_0p00.png",
      "right_file": "jit_1p25.png",
      "choice": "jit_1p25.png",
      "confidence": "pretty sure",
      "elapsed_ms": 3210
    }
  ]
}
```

fields:
- `judge_id` — string entered at the start screen, or `"anonymous"`.
- `started_at` / `completed_at` — iso8601 timestamps.
- `answers[].question_id` — matches `stimuli.json` ids (`q01`–`q12`).
- `answers[].choice` — the **filename** (basename) the judge clicked, not "left"/"right".
  this is stable regardless of the randomised display order.
- `answers[].confidence` — `"a little"` | `"pretty sure"` | `"very sure"`.
- `answers[].elapsed_ms` — milliseconds from question render to next click.

---

## normalized (human_judgments) record format

after `ingest.py`, `judgments_out.json` contains records shaped for the xano
`human_judgments` table (see `xano/schema.py`):

```json
{
  "id": 1,
  "run_id": 4521,
  "judge_id": "jdoe",
  "dimension": "roughness",
  "score": 1,
  "notes": "confidence: pretty sure; question_id: q01",
  "created_at": "2024-01-01T10:10:00Z"
}
```

fields:
- `run_id` — derived deterministically from `question_id` via `djb2(question_id) mod 9000 + 1000`.
  stable across python versions (does not use `hash()` which is session-randomised).
- `score` — `1` if choice matches ground truth, `0` if wrong, `null` for catch pairs.
- `notes` — concatenation of confidence, question_id, and any catch/note strings.

---

## catch pairs

questions `q04` and `q07` are catch pairs: both images are identical, so there is no
ground truth. `gt` is `null` in `stimuli.json`. `score` is `null` in the normalized
record. the catch-pair count in the summary indicates judge noise / click rate.

---

## stimuli spec

`stimuli.json` version 1. each question:
```
id          unique string q01–q12
dimension   roughness | texture | line_weight | color_temperature | lighting
prompt      the question shown above the images
left/right  paths relative to survey/ (../data/generated/arch_svg/*.png)
gt          "left" | "right" | null   (null = catch pair)
note        optional explanatory note
```

---

## running tests

```bash
python -m pytest tests/test_survey_ingest.py -v
# or with plain unittest:
python -m unittest tests.test_survey_ingest -v
```

tests cover: normalization, gt joins, catch-pair null scores, invalid records
skipped with reasons, dry-run behaviour, and summary aggregation.

## batch 2 (2026-09-09)

batch 2 is spec-driven end to end (research/VALIDATION_LOOP.md in practice):

- **preregistration:** `survey/specs/batch_2.json` declares every question,
  its ground truth, catch positions, pass criteria, and adaptive rules before
  any judge sees it. the glm-5.2 scientist session reviewed the draft; its
  corrections (grain floor reallocated to the 0-8/8-14 brackets, taper
  roughness polarity inverted per the pilot refutation, lighting JND pairs)
  are folded in and cited in the spec.
- **build:** `python3 survey/build_batch.py` renders any missing stimuli via
  the svg substrate and writes `survey/stimuli.json` (v2). `--dry-run`
  validates the spec against existing images only.
- **mechanics:** every question carries an honest "no difference / can't
  tell" option, so identical-pair catches become implicit attention checks
  ("no difference" is the correct answer) and "no difference" on scored pairs
  is recorded as a perceptual-floor signal, not an incident. one same/different
  question (grain 0 vs 8) separates detection from "which is more". catch
  pairs sit at fixed display positions (5, 12, 19) with dimension-consistent
  prompts so they blend in. left/right randomization per judge stays.
- **analysis:** `python3 survey/analyze_batch.py results_*.json` scores
  answers against the spec, excludes judges who miss more than one catch,
  computes per-question agreement, per-dimension agreement with bootstrap
  95% CIs, applies the verdict rules (taper promotion/split/kill, grain floor
  bracket, lighting validation), and flags 50/50 splits as stimulus failures
  to regenerate next batch. `--demo` runs synthetic judges offline.
- **legacy:** the pilot stimuli are archived at
  `survey/specs/stimuli_batch1.json`; `ingest()` takes a `stimuli_path` for
  scoring old records.
