# autoscientist run

the experiment: give adaptionlabs' autoscientist the invented wrangler corpus (500 synthetic instruction rows) and let its automated research loop train a model that maps colloquial style language onto render canonicals. the loop iterates with augmentation against a target win rate, then the model is downloadable.

## the question this answers

can the wrangler pattern be *learned* at all. a positive result says: colloquial style language to canonical tags is a learnable mapping, and a small model can act as the automated wrangler between users and the engine. a negative result says the dataset spec was wrong (most likely: the ambiguous-case rows, or vocabulary drift between the invention prompt and the canonical files), not that the canonicals are wrong.

## how it is launched

```bash
python3 -c "
import os, json
from adaption import Client
c = Client(api_key=os.environ['ADAPTIONLABS_API_KEY'])
run = c.autoscientist.create(dataset_id='fb3e1081-9501-4140-aa27-85acd42a1bae', training_method='instruction', data_format='chat')
print(run.id, run.status)
"
```

`run_info.json` in this folder records the experiment id and status once the run exists. training runs on adaptionlabs credits. poll with `autoscientist.get(experiment_id)`; download the finished model with `autoscientist.download(experiment_id)`.

## what the model is for, and what it is not for

- for: acting as the automated wrangler over the vocabulary in this branch, resolving user language to canonicals quickly and consistently, flagging ambiguity instead of guessing.
- not for: being evidence. a model trained on synthetic rows cannot bless a canonical, promote a candidate, or add a synonym from a session it did not attend. the files in this branch remain the source of truth. the model is an accelerator over them, and it gets retrained whenever the files change.

## evaluation honesty

the invented corpus is the only judge available at launch, which is circular (the corpus was written from the same canonical files the model must predict). two de-circularizing checks before any adoption:

1. held-out session test: run the model on the nine real session seed descriptions in `render/examples.md` and check it agrees with the ground-truth canonicals.
2. live synonym test: feed it the `_ambiguous` terms ("painted", "watercolor", "pastel", "muted") and check it refuses to auto-resolve. a wrangler that confidently resolves ambiguous terms is worse than no wrangler.

## lineage

| thing | id |
|---|---|
| invented dataset | fb3e1081-9501-4140-aa27-85acd42a1bae (illustrace-style-wrangler-v1, 500 rows) |
| autoscientist experiment | 8a376b64-3ca4-45d6-a2b8-14f884bbe42e (llama-4-scout, instruction method, +500 domain / +250 general augmentation, target win rate 0.8, max 3 iterations, status at launch: running) |
| corpus file | style_wrangler_v1.jsonl (500 rows, downloaded, committed) |
