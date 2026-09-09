"""build a shareable, double-clickable survey package.

the served app fetches stimuli.json, which browsers block on file://. this
script produces a self-contained zip: stimuli inlined into index.html, images
copied next to it with rewritten paths, and a judge-facing readme. the judge
unzips, opens index.html, answers, and sends the downloaded results file back.
"""
import json
import os
import re
import shutil
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
IMG_DIR = os.path.join(ROOT, "data", "generated", "arch_svg")
PKG_DIR = os.path.join(ROOT, "dist", "survey_package")
ZIP_PATH = os.path.join(ROOT, "dist", "stylebench_survey.zip")

JUDGE_README = """illustrace stylebench - human judgment survey

1. unzip this folder somewhere
2. open index.html by double-clicking it (any modern browser)
3. enter a name or nickname, answer the 12 pairwise questions
   (each asks which of two images feels more like the described trait -
   there are no wrong answers, go with your gut, and use the confidence
   buttons honestly)
4. at the end, download the results file (json or csv, either is fine)
5. send that file back

about: the survey checks whether measurable image statistics line up with
what humans actually perceive. takes about 5 minutes. thanks!
"""


def build():
    # fresh package dir
    if os.path.exists(PKG_DIR):
        shutil.rmtree(PKG_DIR)
    os.makedirs(os.path.join(PKG_DIR, "images"))

    # stimuli: load, copy images, rewrite paths to images/<name>
    with open(os.path.join(HERE, "stimuli.json")) as f:
        stimuli = json.load(f)

    used = set()
    for q in stimuli["questions"]:
        for side in ("left", "right"):
            name = os.path.basename(q[side])
            src = os.path.join(IMG_DIR, name)
            if not os.path.exists(src):
                raise SystemExit("missing image: " + src)
            shutil.copy2(src, os.path.join(PKG_DIR, "images", name))
            used.add(name)
            q[side] = "images/" + name

    # index.html: inline stimuli before the main script, with the id boot falls
    # back to when fetch fails (file://)
    with open(os.path.join(HERE, "index.html")) as f:
        html = f.read()
    if 'id="stimuli-data"' in html:
        raise SystemExit("index.html already contains embedded stimuli; regenerate from clean copy")
    block = ('<script type="application/json" id="stimuli-data">\n'
             + json.dumps(stimuli, indent=2)
             + "\n</script>\n<script>")
    # first script tag after body content is the app; inline just before it
    html = html.replace("<script>", block, 1)

    with open(os.path.join(PKG_DIR, "index.html"), "w") as f:
        f.write(html)

    with open(os.path.join(PKG_DIR, "README.txt"), "w") as f:
        f.write(JUDGE_README)

    # verify: embedded json parses, every path resolves inside the package
    m = re.search(r'id="stimuli-data">\n(.*?)\n</script>', open(os.path.join(PKG_DIR, "index.html")).read(), re.S)
    emb = json.loads(m.group(1))
    for q in emb["questions"]:
        for side in ("left", "right"):
            if not os.path.exists(os.path.join(PKG_DIR, q[side])):
                raise SystemExit("package broken: " + q[side])

    # zip
    if os.path.exists(ZIP_PATH):
        os.remove(ZIP_PATH)
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for base, _, files in os.walk(PKG_DIR):
            for name in sorted(files):
                full = os.path.join(base, name)
                rel = os.path.relpath(full, PKG_DIR)
                zf.write(full, os.path.join("stylebench_survey", rel))

    print("images:", len(used))
    print("questions:", len(emb["questions"]))
    print("zip:", ZIP_PATH, os.path.getsize(ZIP_PATH), "bytes")


if __name__ == "__main__":
    build()
