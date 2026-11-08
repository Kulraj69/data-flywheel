"""Promotion gate: move reviewed, corrected trajectories into the golden set.

A candidate only lands in the golden set if the FULL set (existing golden +
candidate, with the correction applied as the new expected answer) still
passes teval's graders. Regression safety is the whole point of a flywheel:
data only compounds when every addition keeps the suite green.
"""

import dataclasses
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
for _sib in ("../../trajectory-eval",):
    _p = os.path.realpath(os.path.join(_HERE, _sib))
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.append(_p)

from teval.harness import evaluate
from teval.schema import load_jsonl

from .store import best_rated


def promote(feedback_path: str, pool_path: str, golden_path: str, min_rating: int = 4) -> dict:
    """Try to promote well-rated pool trajectories into the golden set.

    pool_path: JSONL of candidate trajectories collected from production.
    Returns {"promoted": [...], "rejected": {id: reason}, "golden_size": n}.
    """
    golden = load_jsonl(golden_path) if os.path.exists(golden_path) else []
    pool = {t.id: t for t in load_jsonl(pool_path)}
    approved = best_rated(feedback_path, min_rating)

    promoted, rejected = [], {}
    for tid, rec in approved.items():
        traj = pool.get(tid)
        if traj is None:
            rejected[tid] = "trajectory not in pool"
            continue
        if rec["correction"]:
            traj = type(traj)(**{**traj.__dict__,
                                 "metadata": {**traj.metadata,
                                              "eval": {**traj.metadata.get("eval", {}),
                                                       "expected_answer": rec["correction"]}}})
        candidate = golden + [traj]
        result = evaluate(candidate, {})
        if result.passed:
            golden.append(traj)
            promoted.append(tid)
        else:
            rejected[tid] = f"fails eval gate (score {result.score:.3f})"

    if promoted:
        with open(golden_path, "w", encoding="utf-8") as f:
            for t in golden:
                f.write(json.dumps(dataclasses.asdict(t)) + "\n")
    return {"promoted": promoted, "rejected": rejected, "golden_size": len(golden)}
