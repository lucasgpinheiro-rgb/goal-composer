# goal-composer

A Claude Code skill that interviews you ("grill me" style), explores the approaches with you, designs the chosen one, and writes a mandate for the built-in `/goal` command, then makes sure the proofs in it mean something.

What you get per goal:

- 2–3 alternative approaches with their trade-offs (proofs, scope, risk, turns), and a design of the chosen one validated section by section and saved as a file the executor reads first and is bound to: needing a rejected approach is a BLOCKED, not a silent switch. Depth is proportional: full for Change and Batch, method only for Audit, Research and Release review, skipped when you bring a spec;
- a mandate within the 4,000-character limit: objective, criteria each with a printed proof, scope, constraints, forbidden shortcuts, a task checklist, and an exit written as branch (B) of the condition itself (three BLOCKED lines or LIMIT REACHED end the goal), because an evaluator told by policy to accept a blocked run still answered not-met;
- a red-team pass by a fresh subagent that tries to satisfy each proof without doing the work;
- a baseline run that rejects vacuous proofs (a "target" proof that already passes measures nothing) and records counters such as test or record counts;
- an independent recheck you run yourself after the goal ends: it re-runs every proof, enforces the counters, verifies pinned file hashes and the proofs file's own hash, and prints DONE / NOT-DONE / BROKEN, optionally followed by a random sample of outputs for human review.

Scenario skeletons for Change, Batch, Audit, Research and Release review goals, plus a catalog of false-completion traps by project type (Node, Python, Go, Rust, JVM/.NET, browser automation, documents, data). Works for code, document and data projects. Conversations and mandates follow your language (Portuguese and English labels built in; other languages use the English labels).

## Why

`/goal` keeps Claude working until a separate small model judges your condition met. That evaluator never runs commands or reads files; it only reads the transcript. So a condition must be provable by printed output, and even then the evaluator cannot tell a fresh output from a stale or cherry-picked one. This skill covers both: provable conditions going in, independent verification coming out.

## Requirements

- Claude Code v2.1.139 or later (the `/goal` command)
- Python 3
- bash: on Windows, Git for Windows (the same Git Bash Claude Code uses; set `CLAUDE_CODE_GIT_BASH_PATH` if it is not in the default location)

## Install

### As a plugin (recommended)

Inside Claude Code:

```
/plugin marketplace add lucasgpinheiro-rgb/goal-composer
/plugin install goal-composer@goal-composer
```

Plugin skills are always namespaced, so the command is `/goal-composer:goal-composer`. Updates arrive through `/plugin`.

### Manually

Copy the `skills/goal-composer/` folder of this repository to:

- all projects: `~/.claude/skills/goal-composer/` (Windows: `C:\Users\<you>\.claude\skills\goal-composer\`)
- one project: `<project>/.claude/skills/goal-composer/`

The folder must contain `SKILL.md` directly (watch out for a doubled `goal-composer/goal-composer/`). The command is then `/goal-composer`. Start a new Claude Code session after installing.

## Use

```
/goal-composer:goal-composer migrate the payment endpoints to the new client
```

(or `/goal-composer ...` with a manual install)

Answer the questions (each comes with a recommended answer), pick an approach, and confirm the design one section at a time. The skill writes its files to `.claude/goals/`, runs the baseline, validates the mandate and shows it. Then:

```
/goal <paste the mandate>
```

For unattended runs use auto mode. `/goal` alone shows status; `/goal clear` cancels.

When the goal reports achieved, run the recheck command the skill gave you at delivery (it carries the resolved script path and the baseline hash), from the project root:

```
python <skill-dir>/scripts/recheck_goal.py .claude/goals/<slug>-proofs.json --expect-sha <hash from the baseline>
```

Accept the work only on DONE. BROKEN means the proofs file was modified or a check could not run.

The skill is slash-only (`disable-model-invocation: true`). Remove that line from `SKILL.md` if you want Claude to offer it on its own.

## Files

- `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`: this repository is both the plugin and its marketplace

Under `skills/goal-composer/`:

- `SKILL.md`: nine phases: reconnaissance, understanding, approaches, design, contract, drafting, red-team, baseline, delivery
- `scripts/validate_goal.py`: mandate checks (UTF-16 length, sections, proofs, branch (B) exit and three-strike line, stop clauses, vague or unbounded terms, undetectable stop conditions, criteria count, turn budget, proofs-file consistency, design file cited and pinned); `--hash <path>` prints a SHA-256 of a file or directory
- `scripts/recheck_goal.py`: `--baseline` before the goal, plain run after it; the full `proofs.json` format is in its docstring; pinned paths can be files or whole directories
- `references/traps.md`: false-completion traps by project type, read during the interview
- `references/scenarios.md`: skeletons per scenario
- `references/examples.md`: four worked examples (code, document audit in Portuguese, data batch, a vague request that is pushed back)

Per goal, in `.claude/goals/`: `<slug>.md` (mandate), `<slug>-design.md` (chosen and rejected approaches, components, tests to criteria, steps; pinned), `<slug>-proofs.json` (proofs, counters, pins, sample, recorded baseline), optionally `<slug>-verify.*` (verifier), and `<slug>-tasks.md` (checklist kept by the executor).

## Open question: `/goal @file`

In Codex, `/goal @path/to/file.md` loads the goal from a file. It is not documented whether Claude Code's `/goal` expands `@file` in the condition. If it does not, the evaluator receives only the path and has nothing to judge. Test before relying on it: run `/goal @.claude/goals/<slug>.md`, then `/goal` with no argument, and check whether the status shows the file's text or just the path. Until confirmed, paste the text.

## Limits

- No check guarantees that a proof captures your intent. The baseline, counters and red-team make proofs harder to satisfy vacuously or by shortcut; they do not make them complete. The sample exists for the part only you can judge.
- Subjective end states (style, tone, "reads well") have no transcript proof; the skill says so instead of writing a condition that cannot be judged.
- Exercised in practice on Windows 11 with Git Bash. macOS and Linux have not been exercised yet; please report issues.

## Em português

A skill conversa na língua de quem a usa e escreve o mandato nessa língua, com rótulos próprios para português (`OBJETIVO`, `CONCLUÍDO QUANDO`, `PARADA`...). O exemplo 2 de `references/examples.md` é um mandato completo em português. Instalação e uso são os mesmos descritos acima.

## License

MIT, see [LICENSE](LICENSE).
