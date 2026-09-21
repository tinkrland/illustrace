#!/usr/bin/env python3
"""composer server tests: graph execution, determinism, guards."""
import base64
import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from PIL import Image

from application.composer_server.executor import execute_graph

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
GRAPH = {
    "nodes": [
        {"id": "s1", "type": "source", "path": "test_images/ref_01.webp"},
        {"id": "s2", "type": "source", "path": "monet/monet_000_1890.jpg"},
        {"id": "op1", "type": "op", "op": "palette", "strength": 0.8},
        {"id": "op2", "type": "op", "op": "texture", "strength": 0.6, "seed": 3},
        {"id": "p1", "type": "preview"},
    ],
    "edges": [
        {"from": "s1", "to": "op1", "port": "base"},
        {"from": "s2", "to": "op1", "port": "ref"},
        {"from": "op1", "to": "op2", "port": "base"},
        {"from": "s2", "to": "op2", "port": "ref"},
        {"from": "op2", "to": "p1", "port": "in"},
    ],
}


class TestExecutor:
    def test_chain_renders_and_changes(self):
        out = execute_graph(GRAPH, DATA)
        assert "p1" in out["images"] and not out["errors"]
        a = Image.open(os.path.join(DATA, "test_images/ref_01.webp")).convert("RGB")
        b = Image.open(io.BytesIO(base64.b64decode(
            out["images"]["p1"].split(",", 1)[1])))
        moved = np.abs(
            np.array(a.resize(b.size)) - np.array(b)).mean()
        assert moved > 2.0, "chain output identical to the source input"

    def test_deterministic(self):
        # the preset principle: same recipe, same render, every time
        a = execute_graph(GRAPH, DATA)["images"]["p1"]
        b = execute_graph(GRAPH, DATA)["images"]["p1"]
        assert a == b

    def test_every_operator_wires(self):
        from application.composer_server.executor import OPERATORS
        for op in OPERATORS:
            g = {
                "nodes": [
                    {"id": "s1", "type": "source",
                     "path": "test_images/ref_01.webp"},
                    {"id": "s2", "type": "source",
                     "path": "monet/monet_000_1890.jpg"},
                    {"id": "op1", "type": "op", "op": op, "strength": 1.0},
                    {"id": "p", "type": "preview"},
                ],
                "edges": [
                    {"from": "s1", "to": "op1", "port": "base"},
                    {"from": "s2", "to": "op1", "port": "ref"},
                    {"from": "op1", "to": "p", "port": "in"},
                ],
            }
            out = execute_graph(g, DATA)
            assert "p" in out["images"] and not out["errors"], (op, out["errors"])

    def test_missing_input_is_an_error_not_a_crash(self):
        bad = {
            "nodes": [
                {"id": "s1", "type": "source", "path": "test_images/ref_01.webp"},
                {"id": "op1", "type": "op", "op": "palette"},
                {"id": "p1", "type": "preview"},
            ],
            "edges": [
                {"from": "s1", "to": "op1", "port": "base"},
                {"from": "op1", "to": "p1", "port": "in"},
            ],
        }
        out = execute_graph(bad, DATA)
        assert out["errors"].get("p1")

    def test_path_escape_blocked(self):
        esc = {
            "nodes": [
                {"id": "s", "type": "source", "path": "../llm/README.md"},
                {"id": "p", "type": "preview"},
            ],
            "edges": [{"from": "s", "to": "p", "port": "in"}],
        }
        out = execute_graph(esc, DATA)
        assert out["errors"].get("p")
