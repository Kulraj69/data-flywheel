"""Append-only feedback store: one JSON object per line."""

import json
import os
import time


def append_feedback(path: str, trajectory_id: str, rating: int, correction: str = "", reviewer: str = "") -> dict:
    """Record human feedback on a trajectory. rating: 1 (bad) .. 5 (perfect)."""
    if not 1 <= int(rating) <= 5:
        raise ValueError("rating must be 1..5")
    rec = {"ts": time.time(), "trajectory_id": trajectory_id,
           "rating": int(rating), "correction": correction, "reviewer": reviewer}
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    return rec


def load_feedback(path: str) -> list:
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def best_rated(path: str, min_rating: int = 4) -> dict:
    """Latest rating per trajectory, filtered to rating >= min_rating."""
    latest = {}
    for rec in load_feedback(path):
        latest[rec["trajectory_id"]] = rec
    return {tid: rec for tid, rec in latest.items() if rec["rating"] >= min_rating}
