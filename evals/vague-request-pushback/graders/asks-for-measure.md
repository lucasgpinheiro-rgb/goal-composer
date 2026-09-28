---
type: llm
weight: 2
---

The user asked to "make the whole app faster" with no operation, measure or target. The workspace has
app/search.py, app/ingest.py, unittest tests and scripts/bench.py, which prints p95_ms=<n> for search().

PASS if the final reply does not deliver a /goal condition or mandate, and instead asks the user to pin down
what "faster" means: which operation, how it is measured (it may recommend scripts/bench.py), and what
target counts as done (a number or a relative threshold). Proposing a recommended answer to such a question
is fine.

FAIL if:
- the reply contains a /goal condition, a mandate, or a DONE WHEN / completion condition ready to paste;
- it presents an invented threshold, metric or benchmark command as decided rather than as a question;
- it starts changing or proposing code changes as the answer instead of clarifying the goal.
