# data-flywheel

Self-improving data flywheel - project #9 from the TOP 1% AI projects list.
Turn reviewed agent runs into new golden tests, gated by regression checks so
data only compounds when every addition keeps the eval suite green.

## What it does

- **store**: append-only JSONL feedback log. Reviewers rate trajectories
  (1-5) and can attach a correction; the latest rating wins.
- **promote**: moves well-rated pool trajectories into the golden set - but
  only after the full candidate set passes teval's graders. A correction
  becomes the new expected answer before the gate runs. Bad or unrated data
  never reaches the golden set.

## Why the gate matters

A flywheel without a regression gate is a bug amplifier: one bad "approved"
trajectory silently becomes ground truth. Here, promotion IS the eval, so the
golden set can only improve.

## Usage

```python
from flywheel.store import append_feedback
from flywheel.promote import promote

append_feedback("feedback.jsonl", "run-041", 5, correction="4 [tool:calc]", reviewer="kulraj")
result = promote("feedback.jsonl", "pool.jsonl", "golden.jsonl")
# {"promoted": ["run-041"], "rejected": {}, "golden_size": 7}
```

## Test

```bash
python -m unittest discover -s tests
```

7 tests cover rating bounds, latest-wins re-rating, promotion gating
(bad trajectories rejected), correction-as-expected-answer, and missing-pool
skips.

## Scope

Deterministic and offline. Pairs with `trajectory-eval` (the gate),
`agent-lab` (the run source) and `cost-router` (which model produced the run).

## Demo

`demo.py` reproduces the recorded demo run end to end, offline (standard
library only, no model calls):

    python demo.py

It executes the library's real code path and prints the same output shown in
the recorded demo video.
