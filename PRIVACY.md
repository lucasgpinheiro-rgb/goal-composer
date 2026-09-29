# Privacy

goal-composer is a Claude Code plugin with one skill and two Python scripts. It has no server, no account and no telemetry.

- **What it reads:** files in the project you run it in (README, CLAUDE.md, `git status`, `git log --oneline`, and the files a goal names), so that Claude can write the mandate. This happens inside your Claude Code session, like any other file Claude reads there.
- **What it writes:** only files under `.claude/goals/` in that project: the mandate, the design, the proofs file, the verifier if you approve one, the executor's checklist and `recheck-log.jsonl`.
- **What it runs:** `validate_goal.py` and `recheck_goal.py`, bundled with the plugin, and the proof commands you approve in the mandate. The scripts make no network calls. Proof commands are yours and run on your machine with your permissions.
- **What it sends:** nothing, to anyone. The plugin has no service that could receive or retain data. What Claude Code itself sends to Anthropic is governed by Anthropic's terms and privacy policy, not by this plugin.

Questions or reports: https://github.com/lucasgpinheiro-rgb/goal-composer/issues
