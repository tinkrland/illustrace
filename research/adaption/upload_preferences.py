"""upload the stylebench preference pairs to adaption datasets.

run:  python3 research/adaption/upload_preferences.py [jsonl_path]

adaption's storage verification endpoint was returning 503 on 2026-09-09
(s3 puts succeed, their verify service doesn't respond). re-run this script
later to complete the registration; it is idempotent per attempt.
"""
import os
import sys
import time
import json

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..")))
from adaption import Adaption  # noqa: E402

try:
    import httpx
except ImportError:  # adaption vendors httpx
    from adaption._compat import httpx  # pragma: no cover

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT = os.path.join(HERE, "pilot_preference_pairs.jsonl")
NAME = "illustrace-stylebench-pilot-preferences"


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT
    data = open(path, "rb").read()
    rows = data.count(b"\n")
    c = Adaption(api_key=os.environ["ADAPTIONLABS_API_KEY"])

    init = c.datasets.upload.initiate(name=NAME, file_format="jsonl")
    s3_key = init.upload_url.split("/datasets/")[1]
    r = httpx.put(init.upload_url, content=data,
                  headers={"Content-Type": "application/x-ndjson"})
    print(f"put: {r.status_code} ({rows} rows, {len(data)} bytes)")
    if r.status_code != 200:
        return 1

    for attempt in range(3):
        try:
            comp = c.datasets.upload.complete(
                s3_key=s3_key, name=NAME, file_format="jsonl",
                file_size_bytes=len(data),
            )
            did = getattr(comp, "dataset_id", None) or getattr(comp, "id", None)
            print("complete ok | dataset:", did)
            with open(os.path.join(HERE, "dataset_pilot.json"), "w") as f:
                json.dump({"dataset_id": did, "name": NAME, "rows": rows,
                           "source": path}, f, indent=2)
            return 0
        except Exception as e:
            print(f"complete attempt {attempt+1} failed: {str(e)[:120]}")
            time.sleep(10)
    print("storage verify still failing — re-run this script later")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
