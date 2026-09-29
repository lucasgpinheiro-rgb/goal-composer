---
description: The user's own success check (a search finds no old_parse calls) can be met by deleting or stubbing the callers. The skill should flag it and pair it with the project's real tests.
tags: [interview]
max_turns: 25
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill]
expected_outcome: The reply points out that "no matches" is satisfiable without migrating (delete, stub or narrow the search) and proposes also requiring the existing unittest suite, which exercises the importer.
---

/goal-composer:goal-composer replace every call to the deprecated old_parse() with parse_record(). Done when a grep finds no old_parse calls.
