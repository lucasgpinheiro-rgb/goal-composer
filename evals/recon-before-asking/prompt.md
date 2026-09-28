---
description: A short request with real gaps in a project whose layout answers the routine questions. The skill should read the project first, not ask what it already answers, and ask one question with a recommended answer.
tags: [interview]
max_turns: 25
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill]
expected_outcome: The reply shows facts from the project (unittest, reports/cli.py, the report command) and asks at most one question, with a recommended answer, about something the project cannot answer, such as the CSV columns or where the file goes.
---

/goal-composer:goal-composer add a --csv option to the report command
