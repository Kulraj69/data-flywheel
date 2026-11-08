import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.realpath(os.path.join(_HERE, "..", "..", "trajectory-eval")))

from flywheel.promote import promote
from flywheel.store import append_feedback, best_rated, load_feedback


def good_traj(tid):
    return {"id": tid, "task": "say hi",
            "steps": [{"kind": "tool_call", "tool_call": {"name": "chat", "arguments": {}}},
                      {"kind": "tool_result", "content": "hi"},
                      {"kind": "answer", "content": "hi [tool:chat]"}],
            "final_answer": "hi [tool:chat]",
            "metadata": {"eval": {"allowed_tools": ["chat"]}}}


def bad_traj(tid):
    return {"id": tid, "task": "say hi",
            "steps": [{"kind": "answer", "content": "hi [tool:chat]"}],  # cites tool never called
            "final_answer": "hi [tool:chat]",
            "metadata": {"eval": {"allowed_tools": ["chat"]}}}


class TestStore(unittest.TestCase):
    def test_append_and_load(self):
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "fb.jsonl")
            append_feedback(p, "t1", 5, reviewer="kulraj")
            append_feedback(p, "t2", 2)
            recs = load_feedback(p)
            self.assertEqual(len(recs), 2)
            self.assertEqual(recs[0]["rating"], 5)

    def test_rating_bounds(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                append_feedback(os.path.join(td, "fb.jsonl"), "t1", 9)

    def test_best_rated_latest_wins(self):
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "fb.jsonl")
            append_feedback(p, "t1", 5)
            append_feedback(p, "t1", 1)  # re-rated down
            self.assertEqual(best_rated(p), {})


class TestPromote(unittest.TestCase):
    def _write(self, td, name, trajs):
        p = os.path.join(td, name)
        with open(p, "w") as f:
            for t in trajs:
                f.write(json.dumps(t) + "\n")
        return p

    def test_good_candidate_promoted(self):
        with tempfile.TemporaryDirectory() as td:
            pool = self._write(td, "pool.jsonl", [good_traj("t1")])
            golden = os.path.join(td, "golden.jsonl")
            fb = os.path.join(td, "fb.jsonl")
            append_feedback(fb, "t1", 5)
            out = promote(fb, pool, golden)
            self.assertEqual(out["promoted"], ["t1"])
            self.assertEqual(out["golden_size"], 1)

    def test_bad_candidate_rejected_by_gate(self):
        with tempfile.TemporaryDirectory() as td:
            pool = self._write(td, "pool.jsonl", [bad_traj("t9")])
            golden = os.path.join(td, "golden.jsonl")
            fb = os.path.join(td, "fb.jsonl")
            append_feedback(fb, "t9", 5)  # human liked it, but it hallucinated a tool call
            out = promote(fb, pool, golden)
            self.assertEqual(out["promoted"], [])
            self.assertIn("fails eval gate", out["rejected"]["t9"])
            self.assertEqual(out["golden_size"], 0)

    def test_correction_becomes_expected_answer(self):
        with tempfile.TemporaryDirectory() as td:
            t = good_traj("t2")
            pool = self._write(td, "pool.jsonl", [t])
            golden = os.path.join(td, "golden.jsonl")
            fb = os.path.join(td, "fb.jsonl")
            # reviewer corrects the expected answer; gate then expects "hi"
            append_feedback(fb, "t2", 5, correction="hi [tool:chat]")
            out = promote(fb, pool, golden)
            self.assertEqual(out["promoted"], ["t2"])
            saved = [json.loads(l) for l in open(golden)]
            self.assertEqual(saved[0]["metadata"]["eval"]["expected_answer"], "hi [tool:chat]")

    def test_unapproved_and_missing_pool_skipped(self):
        with tempfile.TemporaryDirectory() as td:
            pool = self._write(td, "pool.jsonl", [good_traj("t1")])
            golden = os.path.join(td, "golden.jsonl")
            fb = os.path.join(td, "fb.jsonl")
            append_feedback(fb, "t1", 2)          # below threshold
            append_feedback(fb, "ghost", 5)       # not in pool
            out = promote(fb, pool, golden)
            self.assertEqual(out["promoted"], [])
            self.assertEqual(out["rejected"]["ghost"], "trajectory not in pool")


if __name__ == "__main__":
    unittest.main()
