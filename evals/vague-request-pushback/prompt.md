---
description: A request with no measurable end state. The skill should push back and ask for the operation, the measure and the target instead of rendering a mandate (examples.md, example 4).
tags: [interview]
max_turns: 25
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill]
expected_outcome: No mandate or /goal line. The reply asks which operation to speed up, how it is measured (scripts/bench.py exists) and what target counts as done, and does not invent a threshold as if it were decided.
---

/goal-composer:goal-composer make the whole app faster
