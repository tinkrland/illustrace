"""tests for llm/lora_train.py, offline only (no network, no gpu).

covers the shared dataset validator and the nebius hyperparameter mapping
(the batch floor that used to 500 on their side before we enforced it
locally). the actual upload/poll path is exercised manually against the
live api (see the 2026-09-19 probe in the repo notes).
"""

import json
import os
import sys
import tempfile
import unittest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from llm.lora_train import (validate_dataset, build_hyperparameters,
                            nebius_key, NEBIUS_MIN_BATCH_TOKENS)


def _write(lines):
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    with os.fdopen(fd, "w") as f:
        for l in lines:
            f.write(json.dumps(l) + "\n")
    return path


def _pair(user="hi", assistant="ok"):
    return {"messages": [{"role": "system", "content": "s"},
                         {"role": "user", "content": user},
                         {"role": "assistant", "content": assistant}]}


class _Args:
    def __init__(self, batch=4, lr=None, epochs=3, rank=64):
        self.batch, self.lr, self.epochs, self.rank = batch, lr, epochs, rank


class TestValidateDataset(unittest.TestCase):
    def test_valid_chat_format(self):
        p = _write([_pair(), _pair("say yes", "yes")])
        try:
            n, roles_ok, bad = validate_dataset(p)
        finally:
            os.unlink(p)
        self.assertEqual((n, roles_ok, bad), (2, True, 0))

    def test_empty_lines_skipped(self):
        fd, p = tempfile.mkstemp(suffix=".jsonl")
        with os.fdopen(fd, "w") as f:
            f.write(json.dumps(_pair()) + "\n\n")
        try:
            n, roles_ok, bad = validate_dataset(p)
        finally:
            os.unlink(p)
        self.assertEqual(n, 1)

    def test_non_assistant_final_role_marks_malformed(self):
        bad_pair = {"messages": [{"role": "user", "content": "hi"},
                                  {"role": "assistant", "content": "ok"},
                                  {"role": "user", "content": "again"}]}
        p = _write([bad_pair])
        try:
            _, roles_ok, _ = validate_dataset(p)
        finally:
            os.unlink(p)
        self.assertFalse(roles_ok)

    def test_unparsable_line_counts_bad(self):
        fd, p = tempfile.mkstemp(suffix=".jsonl")
        with os.fdopen(fd, "w") as f:
            f.write("not json at all\n")
        try:
            n, roles_ok, bad = validate_dataset(p)
        finally:
            os.unlink(p)
        self.assertEqual((n, roles_ok, bad), (1, True, 1))

    def test_empty_content_counts_bad(self):
        hollow = {"messages": [{"role": "user", "content": ""},
                                {"role": "assistant", "content": "ok"}]}
        p = _write([hollow])
        try:
            _, _, bad = validate_dataset(p)
        finally:
            os.unlink(p)
        self.assertEqual(bad, 1)

    def test_missing_file_raises(self):
        with self.assertRaises(Exception):
            validate_dataset("/nonexistent/path.jsonl")


class TestBuildHyperparameters(unittest.TestCase):
    def test_defaults_shape(self):
        hp = build_hyperparameters(_Args())
        self.assertEqual(hp["batch_size"], 4)
        self.assertEqual(hp["learning_rate"], 1e-5)
        self.assertTrue(hp["lora"])
        self.assertEqual(hp["lora_alpha"], hp["lora_r"] * 2)

    def test_explicit_lr_respected(self):
        hp = build_hyperparameters(_Args(lr=2e-5))
        self.assertEqual(hp["learning_rate"], 2e-5)

    def test_batch_floor_raised_when_under(self):
        # 32768 / 8192 = 4 exactly, so batch 2 must be raised to 4
        hp = build_hyperparameters(_Args(batch=2))
        self.assertEqual(hp["batch_size"], 4)

    def test_batch_at_floor_kept(self):
        hp = build_hyperparameters(_Args(batch=4))
        self.assertEqual(hp["batch_size"], 4)

    def test_batch_over_floor_kept(self):
        hp = build_hyperparameters(_Args(batch=8))
        self.assertEqual(hp["batch_size"], 8)

    def test_floor_is_satisfied_by_output(self):
        # the whole point: never emit a request tokenfactory 500s on
        for batch in (1, 2, 3, 4, 5, 16):
            hp = build_hyperparameters(_Args(batch=batch))
            self.assertGreaterEqual(hp["batch_size"] * hp["context_length"],
                                    NEBIUS_MIN_BATCH_TOKENS)


class TestNebiusKey(unittest.TestCase):
    def test_assembled_from_id_and_secret(self):
        os.environ["NEBIUS_API_KEY"] = ""
        os.environ["NEBIUS_TOKEN_ID"] = " abc "
        os.environ["NEBIUS_TOKEN_SECRET"] = " def "
        try:
            self.assertEqual(nebius_key(), "v1.abc.def")
        finally:
            del os.environ["NEBIUS_TOKEN_ID"]
            del os.environ["NEBIUS_TOKEN_SECRET"]

    def test_prefers_explicit_key(self):
        os.environ["NEBIUS_API_KEY"] = "v1.x.y"
        try:
            self.assertEqual(nebius_key(), "v1.x.y")
        finally:
            os.environ["NEBIUS_API_KEY"] = ""


if __name__ == "__main__":
    unittest.main()
