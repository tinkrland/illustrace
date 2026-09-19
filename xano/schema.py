"""xano schema — dataclasses and validation for the actual live stylebench
control-plane tables (reconciled 2026-09-19 against research/AMD_DEVELOPER_CLOUD.md
and xano/PROVISIONING.md; the previous version of this file described a
speculative six-table plan — projects/transfer_requests/etc — that was
superseded by training_jobs/node_graphs/presets and never actually built).

tables: stylebench_runs, stylebench_assets, stylebench_experiments, judgments,
training_jobs, datasets, node_graphs, presets.

validate(table_name, record) -> list[str] of error strings; empty list means valid.
json-typed fields (params, metrics, artifacts, style_profile, pass_criteria,
raw, graph, recipe, manifest) accept any dict or list — type checking only,
not content inspection.
"""
from dataclasses import dataclass
from typing import Any, Optional


# ---------------------------------------------------------------------------
# dataclasses (documentation / constructor convenience — not enforced at runtime
# by the validator; validate() works directly on plain dicts)
# ---------------------------------------------------------------------------

@dataclass
class Run:
    id: int
    experiment: str
    subject: str
    requested: str
    params: dict
    metrics: dict
    verdict: str
    artifacts: Any  # json — dict or list
    created_at: str


@dataclass
class Asset:
    id: int
    kind: str
    name: str
    file_url: str
    style_profile: dict
    created_at: str


@dataclass
class Experiment:
    id: int
    name: str
    hypothesis: str
    pass_criteria: dict
    created_at: str


@dataclass
class Judgment:
    id: int
    dimension: str
    stimulus_a_id: str
    stimulus_b_id: str
    chosen: str
    session_id: str
    question_id: str
    judge_id: Optional[str] = None
    confidence: Optional[str] = None
    is_catch_pair: Optional[bool] = None
    noise_flag: Optional[bool] = None
    reaction_ms: Optional[int] = None
    raw: Optional[Any] = None
    created_at: Optional[str] = None


@dataclass
class TrainingJob:
    id: int
    job_type: str      # fitter | lora | batch_render
    status: str        # queued | running | done | failed
    target_factor: str
    hardware: str
    dataset_ref: str
    params: dict
    metrics: dict
    artifact_uri: str
    gpu_hours: float
    notes: Optional[str] = None
    created_at: Optional[str] = None


@dataclass
class Dataset:
    id: int
    name: str
    source: str
    manifest: dict
    image_count: int
    created_at: Optional[str] = None


@dataclass
class NodeGraph:
    id: int
    graph: Any  # json — {nodes: [...], edges: [...]}
    graph_version: int
    status: str  # draft | validated | superseded
    created_at: Optional[str] = None


@dataclass
class Preset:
    id: int
    recipe: dict
    recipe_version: int
    graph_id: int
    created_at: Optional[str] = None


# ---------------------------------------------------------------------------
# json-schema-style descriptors (informational; used by validate())
# ---------------------------------------------------------------------------

_SCHEMAS = {
    "stylebench_runs": {
        "required": ["id", "experiment", "subject", "requested", "params",
                     "metrics", "verdict", "artifacts"],
        "types": {
            "id": int, "experiment": str, "subject": str, "requested": str,
            "params": (dict,), "metrics": (dict,), "verdict": str,
            "artifacts": (dict, list),
        },
        "nonempty": ["subject", "requested", "verdict"],
    },
    "stylebench_assets": {
        "required": ["id", "kind", "name", "file_url", "style_profile"],
        "types": {
            "id": int, "kind": str, "name": str, "file_url": str,
            "style_profile": (dict,),
        },
        "nonempty": ["kind", "name", "file_url"],
    },
    "stylebench_experiments": {
        "required": ["id", "name", "hypothesis", "pass_criteria"],
        "types": {
            "id": int, "name": str, "hypothesis": str, "pass_criteria": (dict,),
        },
        "nonempty": ["name", "hypothesis"],
    },
    "judgments": {
        "required": ["id", "dimension", "stimulus_a_id", "stimulus_b_id",
                     "chosen", "session_id", "question_id"],
        "types": {
            "id": int, "dimension": str, "stimulus_a_id": str,
            "stimulus_b_id": str, "chosen": str, "session_id": str,
            "question_id": str, "judge_id": str, "confidence": str,
            "is_catch_pair": (bool,), "noise_flag": (bool,), "reaction_ms": int,
            "raw": (dict, list),
        },
        "nonempty": ["dimension", "chosen"],
    },
    "training_jobs": {
        "required": ["id", "job_type", "status", "target_factor", "hardware",
                     "dataset_ref"],
        "types": {
            "id": int, "job_type": str, "status": str, "target_factor": str,
            "hardware": str, "dataset_ref": str, "params": (dict,),
            "metrics": (dict,), "artifact_uri": str, "gpu_hours": (int, float),
            "notes": str,
        },
        "nonempty": ["job_type", "target_factor"],
        "enum": {
            "job_type": ["fitter", "lora", "batch_render"],
            "status": ["queued", "running", "done", "failed"],
        },
    },
    "datasets": {
        "required": ["id", "name", "source", "manifest", "image_count"],
        "types": {
            "id": int, "name": str, "source": str, "manifest": (dict,),
            "image_count": int,
        },
        "nonempty": ["name"],
    },
    "node_graphs": {
        "required": ["id", "graph", "graph_version", "status"],
        "types": {
            "id": int, "graph": (dict, list), "graph_version": int, "status": str,
        },
        "nonempty": [],
        "enum": {"status": ["draft", "validated", "superseded"]},
    },
    "presets": {
        "required": ["id", "recipe", "recipe_version", "graph_id"],
        "types": {
            "id": int, "recipe": (dict,), "recipe_version": int, "graph_id": int,
        },
        "nonempty": [],
    },
}

_KNOWN_TABLES = set(_SCHEMAS)


def validate(table_name: str, record: dict) -> list:
    """return a list of error strings for record against table_name's schema.

    empty list means the record is valid. unknown table_name is itself an error.
    record may be a plain dict or a dataclass converted via dataclasses.asdict().
    """
    if table_name not in _KNOWN_TABLES:
        return ["unknown table: %s (known: %s)" % (table_name, ", ".join(sorted(_KNOWN_TABLES)))]

    schema = _SCHEMAS[table_name]
    errors = []

    # missing required fields
    for key in schema["required"]:
        if key not in record or record[key] is None:
            errors.append("missing required field: %s" % key)

    # type checks (only for fields that are present and non-None)
    for key, expected in schema.get("types", {}).items():
        if key not in record or record[key] is None:
            continue  # already caught above if required
        val = record[key]
        if isinstance(expected, tuple):
            if not isinstance(val, expected):
                names = " or ".join(t.__name__ for t in expected)
                errors.append("field %s must be %s, got %s" % (key, names, type(val).__name__))
        else:
            # bool is a subclass of int in python — reject bools for int fields
            if expected is int and isinstance(val, bool):
                errors.append("field %s must be int, got bool" % key)
            elif not isinstance(val, expected):
                errors.append("field %s must be %s, got %s" % (key, expected.__name__, type(val).__name__))

    # nonempty string checks
    for key in schema.get("nonempty", []):
        if key in record and isinstance(record[key], str) and record[key].strip() == "":
            errors.append("field %s must not be empty" % key)

    # enum checks
    for key, allowed in schema.get("enum", {}).items():
        if key in record and record[key] is not None and record[key] not in allowed:
            errors.append("field %s must be one of %s, got %r" % (key, allowed, record[key]))

    return errors
