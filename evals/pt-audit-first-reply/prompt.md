---
description: Portuguese request for a read-only document audit. The first reply should be in Portuguese, treat the audit as read-only and ask at most one question with a recommended answer.
tags: [interview, pt]
max_turns: 25
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill]
expected_outcome: Reply in Portuguese that recognizes an audit of 3 procedures against 5 checklist items, keeps procedimentos/ and referencia/ untouched, and asks one question (report shape, or a verifier for citations) with a recommended answer.
---

/goal-composer:goal-composer auditar os procedimentos em procedimentos/ contra o checklist de referencia/checklist.md
