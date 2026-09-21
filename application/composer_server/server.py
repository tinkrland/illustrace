#!/usr/bin/env python3
"""local execution server for the node composer.

serves the infinite-canvas ui and executes composer graphs with the
real operators, so a node graph renders actual assets instead of
displaying static profiles. stdlib only: nothing to install.

    python3 application/composer_server/server.py   # http://localhost:8642

endpoints:
    GET  /                     the canvas page
    GET  /api/inspos           the inspo library (profiles + thumbnails)
    GET  /api/thumb?path=...   an image under data/ (path-guarded)
    POST /api/run              {graph} -> rendered previews (data urls)
    POST /api/save             {graph, name} -> writes the recipe json +
                                 the preview renders to results/composer/
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from application.composer_server.executor import execute_graph

ROOT = os.path.dirname(os.path.abspath(__file__))
APP_ROOT = os.path.dirname(ROOT)
REPO = os.path.dirname(APP_ROOT)
DATA_ROOT = os.path.join(REPO, "data")
RESULTS = os.path.join(REPO, "results", "composer")
PORT = int(os.environ.get("COMPOSER_PORT", "8642"))

MAX_BODY = 12 * 1024 * 1024  # 12MB graphs are already absurd


def library():
    """inspo entries: every profile with a resolvable image path."""
    import glob as _glob

    items = []

    def add(profiles, base_dir, painter):
        for p in profiles:
            items.append({
                "path": os.path.relpath(os.path.join(base_dir, p["file"]), DATA_ROOT),
                "painter": painter,
            })

    main = os.path.join(DATA_ROOT, "generated", "inspo", "profiles.json")
    if os.path.exists(main):
        with open(main) as f:
            add(json.load(f).get("profiles", []),
                os.path.join(DATA_ROOT, "test_images"), "subjects")
    for pj in sorted(_glob.glob(os.path.join(DATA_ROOT, "generated", "inspo",
                                             "*_profiles.json"))):
        painter = os.path.basename(pj).replace("_profiles.json", "")
        with open(pj) as f:
            add(json.load(f).get("profiles", []),
                os.path.join(DATA_ROOT, painter), painter)
    return items


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):  # quiet: the canvas is the interface
        pass

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/":
            with open(os.path.join(ROOT, "index.html"), "rb") as f:
                self._send(200, f.read(), "text/html")
        elif u.path == "/api/inspos":
            self._send(200, json.dumps(library()).encode())
        elif u.path == "/api/thumb":
            rel = parse_qs(u.query).get("path", [""])[0]
            p = os.path.realpath(os.path.join(DATA_ROOT, rel))
            if not p.startswith(os.path.realpath(DATA_ROOT) + os.sep) \
                    or not os.path.isfile(p):
                return self._send(404, b"not found", "text/plain")
            ext = {"jpg": "image/jpeg", "jpeg": "image/jpeg",
                   "png": "image/png", "webp": "image/webp"}.get(
                       p.rsplit(".", 1)[-1].lower(), "application/octet-stream")
            with open(p, "rb") as f:
                self._send(200, f.read(), ext)
        else:
            self._send(404, b"not found", "text/plain")

    def do_POST(self):
        u = urlparse(self.path)
        n = int(self.headers.get("Content-Length", 0))
        if n > MAX_BODY:
            return self._send(413, b"too big", "text/plain")
        body = json.loads(self.rfile.read(n) or b"{}")
        if u.path == "/api/run":
            try:
                self._send(200, json.dumps(
                    execute_graph(body.get("graph", {}), DATA_ROOT)).encode())
            except Exception as e:
                self._send(200, json.dumps(
                    {"images": {}, "errors": {"graph": str(e)}}).encode())
        elif u.path == "/api/save":
            name = (body.get("name") or "preset_%s"
                    % __import__("time").strftime("%Y%m%d_%H%M%S"))
            name = "".join(c for c in name if c.isalnum() or c in "-_")
            os.makedirs(RESULTS, exist_ok=True)
            out = execute_graph(body.get("graph", {}), DATA_ROOT)
            import base64 as _b64
            renders = 0
            for nid, url in out["images"].items():
                with open(os.path.join(
                        RESULTS, "%s_%s.png" % (name, nid)), "wb") as f:
                    f.write(_b64.b64decode(url.split(",", 1)[1]))
                renders += 1
            recipe = {"name": name, "graph": body.get("graph", {}),
                      "errors": out["errors"]}
            with open(os.path.join(RESULTS, "%s.json" % name), "w") as f:
                json.dump(recipe, f, indent=1)
            self._send(200, json.dumps(
                {"ok": True, "name": name, "renders": renders,
                 "errors": out["errors"]}).encode())
        else:
            self._send(404, b"not found", "text/plain")


if __name__ == "__main__":
    print("composer execution server on http://localhost:%d" % PORT)
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
