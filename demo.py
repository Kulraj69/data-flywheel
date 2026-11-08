"""Reproduces the demo video's real output: feedback -> gate -> golden."""
import json, os
from flywheel.store import append_feedback, best_rated
from flywheel.promote import promote

FB, POOL, GOLDEN = "/tmp/fw-demo/feedback.jsonl", "/tmp/fw-demo/pool.jsonl", "/tmp/fw-demo/golden.jsonl"
if __name__ == "__main__":
    os.makedirs("/tmp/fw-demo", exist_ok=True)
    pool_rows = [
        {"id": "traj-101", "task": "Book cheapest BLR-DEL flight", "steps": [], "final_answer": "IndiGo 06:10 INR 4,320"},
        {"id": "traj-102", "task": "Summarize SD 3.5 release", "steps": [], "final_answer": "SD 3.5 Large 8B, open weights"},
        {"id": "traj-103", "task": "Find hotel in Goa", "steps": [], "final_answer": "Could not search hotels"},
    ]
    open(POOL, "w").write("\n".join(json.dumps(r) for r in pool_rows))
    append_feedback(FB, "traj-101", 5, correction="add window-seat note", reviewer="kulraj")
    append_feedback(FB, "traj-102", 4, reviewer="kulraj")
    append_feedback(FB, "traj-103", 2, correction="looped on timeout", reviewer="kulraj")
    print("best_rated(>=4):", list(best_rated(FB, min_rating=4)))
    print("promote:", promote(FB, POOL, GOLDEN, min_rating=4))
