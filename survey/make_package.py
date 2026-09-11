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
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
IMG_DIR = os.path.join(ROOT, "data", "generated", "arch_svg")
PKG_DIR = os.path.join(ROOT, "dist", "survey_package")
ZIP_PATH = os.path.join(ROOT, "dist", "stylebench_survey.zip")

JUDGE_README_HEAD = "illustrace stylebench - human judgment survey"
JUDGE_README = """illustrace stylebench - human judgment survey

1. unzip this folder somewhere
2. open index.html by double-clicking it (any modern browser)
3. enter a name or nickname, answer the pairwise questions
   (each asks which of two images feels more like the described trait -
   there are no wrong answers, go with your gut, and use the confidence
   buttons honestly. if a pair genuinely looks identical to you, the
   "no difference / can't tell" button is the honest answer - use it)
4. at the end, download the results file (json or csv, either is fine)
5. send that file back

about: the survey checks whether measurable image statistics line up with
what humans actually perceive. takes about 5 minutes. thanks!
"""


def build(batch=None):
    # fresh package dir
    global ZIP_PATH
    if os.path.exists(PKG_DIR):
        shutil.rmtree(PKG_DIR)
    os.makedirs(os.path.join(PKG_DIR, "images"))

    # stimuli: load, copy images, rewrite paths to images/<name>
    stim_file = "stimuli_%s.json" % batch if batch else "stimuli.json"
    with open(os.path.join(HERE, stim_file)) as f:
        stimuli = json.load(f)
    if batch:
        ZIP_PATH = os.path.join(ROOT, "dist", "stylebench_survey_%s.zip" % batch)

    used = set()

    def ship(name, src):
        if not os.path.exists(src):
            raise SystemExit("missing image: " + src)
        if name not in used:
            shutil.copy2(src, os.path.join(PKG_DIR, "images", name))
            used.add(name)

    def rewrite(p):
        # stimuli paths are repo-relative ("../data/generated/...") and may
        # point at arch_svg or substrate_v2 — resolve from the path itself
        src = os.path.join(ROOT, p.replace("../", "", 1))
        ship(os.path.basename(p), src)
        return "images/" + os.path.basename(p)

    for q in stimuli["questions"]:
        for side in ("left", "right"):
            q[side] = rewrite(q[side])
    for c in stimuli.get("catches", []):
        c["image"] = rewrite(c["image"])

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
        if batch:
            f.write("\n\nthis package is the %s session (%d questions).\n"
                    % (batch, len(stimuli["questions"])))

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
    args = [a for a in sys.argv[1:]]
    build(args[0] if args else None)
