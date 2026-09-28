---
description: Full flow with every decision delegated to the skill's recommended answers. Checks that the skill reaches delivery with its own gates passed - design and proofs files, red-team subagent, BASELINE OK, validator OK, branch (B) exit, recheck command - and writes nothing outside .claude/goals/. Conformance case; run with --ablation none.
tags: [pipeline]
runs: 1
max_turns: 80
timeout_seconds: 2400
allowed_tools: [Read, Glob, Grep, Skill, Agent, TodoWrite, Bash, Write, Edit]
expected_outcome: .claude/goals/<slug>-design.md and -proofs.json exist; the transcript shows VERDICT BASELINE OK and RESULT OK; the final reply holds a mandate with the (B) ENDED branch and a recheck command with --expect-sha and a 64-hex hash. Note the fixture uses unittest, where a target for a test module that does not exist yet is reported BROKEN ("No module named") or VACUOUS ("Ran 0 tests ... OK"); the skill has to make the proof strict (for example expect_regex on "Ran [1-9]") to reach BASELINE OK.
---

/goal-composer:goal-composer add retry with exponential backoff to fetch_invoice in billing/client.py: 3 attempts, only on timeouts, 5xx and 429, delays 0.5s, 1s, 2s.

I can't answer questions in this session. At every question take your recommended answer, accept each design section and the pre-draft summary as you propose them, and carry on through the red-team, the baseline, the validation and the delivery. List the defaults you took.
