# adaptionlabs

the machine side of artschool. this branch's vocabulary is human-curated, but two things can be manufactured at scale on adaptionlabs (api.prod.adaptionlabs.ai, adaption sdk): a synthetic corpus of style-description language, and a trained wrangler model that maps that language onto canonical tags. both run on adaptionlabs credits, not base44.

## the invented dataset

`datasets.invent(...)` on adaptionlabs manufactured a synthetic instruction corpus for the wrangler task.

| field | value |
|---|---|
| dataset id | `fb3e1081-9501-4140-aa27-85acd42a1bae` |
| name | illustrace-style-wrangler-v1 |
| type | instruction_dataset, 500 rows |
| domains | art (painting_drawing, illustration, digital_art) |
| cost | 50 credits of 2210 available |

the invention prompt asks for colloquial user descriptions ("chunky chunky filled", "like marker but blurry") mapped onto the render canonicals, including the three unseeded ones (wash_gestural_color, painterly_stroke, lineart_flat), with axis values and rationales, plus deliberately ambiguous cases that must resolve to ambiguity notes rather than canonicals. the fixed vocabulary was taken verbatim from `render/` in this branch, so the dataset and the human-curated files stay in sync at the seed level.

download (when you want the corpus):

```bash
python3 -c "
import os
from adaption import Client
c = Client(api_key=os.environ['ADAPTIONLABS_API_KEY'])
r = c.datasets.download('fb3e1081-9501-4140-aa27-85acd42a1bae', file_format='jsonl')
open('adaptionlabs/style_wrangler_v1.jsonl','wb').write(r.content)
"
```

## the autoscientist run

`autoscientist.create(...)` trains a model on the invented dataset as an automated research loop (it iterates with augmentation until it beats a target win rate, then the model is downloadable). this is the experiment: can a small model wrangle colloquial style language onto render canonicals reliably enough to act as the automated wrangler for real users?

status, goals, and how to check on the run are recorded in `autoscientist.md` once the experiment is launched. the honest framing: this run tests the *wrangler pattern*, not the vocabulary. if the model wins its games, it says the mapping task is learnable at all. if it loses, the dataset spec was wrong, not the canonicals.

## rules of engagement

- adaptionlabs credits only. no base44 credits for any pass in this folder.
- the invented corpus is training data for the wrangler, not evidence for canonicals. a synthetic row saying "minecraft = block_fill" changes nothing about what users mean. only real images and real session language bless canonicals. this is the same rule as everywhere else in the branch, applied to machines.
- if the wrangler model is adopted, it reads the canonical files in this branch as its spec. the files are the source of truth, the model is an accelerator over them.
