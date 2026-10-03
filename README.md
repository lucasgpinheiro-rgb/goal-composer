# goal-composer

A Claude Code skill that interviews you ("grill me" style), explores the approaches with you, designs the chosen one, and writes a mandate for the built-in `/goal` command, then makes sure the proofs in it mean something.

> **Claude Code only.** The skill writes for Claude Code's `/goal` command and runs Python and bash scripts on your machine. If you add it from the Claude directory it may also show up in claude.ai chat and Cowork, but it cannot do its job there.

![goal-composer demo: interview, baseline, /goal run and independent recheck](docs/demo.gif)

*Condensed reconstruction of a session. The baseline, validator and recheck outputs are real runs on a demo project.*

What you get per goal:

- 2–3 alternative approaches with their trade-offs (proofs, scope, risk, turns), and a design of the chosen one validated section by section and saved as a file the executor reads first and is bound to: needing a rejected approach is a BLOCKED, not a silent switch. Depth is proportional: full for Change and Batch, method only for Audit, Research and Release review, skipped when you bring a spec;
- a mandate within the 4,000-character limit: objective, criteria each with a printed proof, scope, constraints, forbidden shortcuts, a task checklist, and an exit written as branch (B) of the condition itself (three BLOCKED lines or LIMIT REACHED end the goal), because an evaluator told by policy to accept a blocked run still answered not-met;
- an interview that asks for the cases nobody said (the negative case, empty input, errors, repetition, boundaries) and reads its understanding back with each item labelled confirmed, assumed, open decision, tension or out of scope;
- a red-team pass by a fresh subagent that tries to satisfy each proof without doing the work, and writes its cheap attacks (a stub returning a constant, a deleted test, an edited input) as scripts that are then run against the proofs in a throwaway git worktree: each attack is CAUGHT or a HOLE, so whether a fix really closes it is measured, not claimed;
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

Plugin skills are always namespaced, so the command is `/goal-composer:goal-composer`. Updates arrive through `/plugin update goal-composer@goal-composer`; auto-update is a per-marketplace setting on your side, off by default for a marketplace you add yourself (see the Claude Code docs on plugin versions and updates). Start a new session after an update.

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

## What it runs and writes

Everything happens in your Claude Code session, under your own permission settings. The skill has no hooks, no MCP servers and no dependencies beyond the Python 3 standard library, and neither of its scripts makes network calls.

- **Reads**: your project, to learn its layout and starting state (README, CLAUDE.md, the directory tree, `git status`, `git log`), plus its own reference files.
- **Runs before the goal**: read-only checks during reconnaissance, such as the test suite when that is cheap; a red-team subagent (a fresh Claude instance, which counts against your usage like any subagent); `validate_goal.py`, which only reads the mandate and proofs files; `recheck_goal.py --baseline`, which executes each command listed in `.claude/goals/<slug>-proofs.json` in bash from the project root (the proof commands you agreed to during the interview); and `recheck_goal.py --attacks`, which runs the red-team's attack scripts.
- **The attack run**: it creates a temporary git worktree at `HEAD` in your system's temp folder, copies in `.claude/goals/` and the gitignored inputs listed in `attack_copy`, checks that the clean copy reproduces the baseline, then for each script in `.claude/goals/<slug>-attacks/` resets the copy, runs the script with bash and runs the proofs. Your working tree is never modified; git registers the worktree under `.git/worktrees` while it runs, and it is removed at the end, also on failure. It refuses to run when tracked files have uncommitted changes. Proofs marked `"external": true` (a paid API, a production host) are never run in attack mode. The scripts are code written by a model and run under your permissions, like the proofs: the skill shows them to you first, and you should read them.
- **Runs after the goal**: nothing on its own. You run `recheck_goal.py`, which executes the same proof commands again. Read the proofs file before running it, as you would any script.
- **Writes**: only under `.claude/goals/` in your project (mandate, design, proofs, optional verifier, checklist). The baseline stores its counter values in the proofs file.
- **Network**: only what your own proof commands do, such as a test suite that calls an API. The interview asks about external effects and sets a safe mode before the goal starts.
- **Does not** run `/goal` for you.

## Files

- `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`: this repository is both the plugin and its marketplace

Under `skills/goal-composer/`:

- `SKILL.md`: nine phases: reconnaissance, understanding, approaches, design, contract, drafting, red-team, baseline, delivery
- `scripts/validate_goal.py`: mandate checks (UTF-16 length, sections, proofs, branch (B) exit and three-strike line, stop clauses, vague or unbounded terms, undetectable stop conditions, criteria count, turn budget, proofs-file consistency, design file cited and pinned, a `catches` line on every target proof, a ruling log in the per-turn protocol); `--hash <path>` prints a SHA-256 of a file or directory
- `scripts/recheck_goal.py`: `--baseline` before the goal, `--attacks <dir>` after the baseline, plain run after the goal; the full `proofs.json` format is in its docstring (including `external` and `attack_copy`); pinned paths can be files or whole directories; every run appends one line to `recheck-log.jsonl` next to the proofs file (`--no-log` to skip)
- `references/traps.md`: false-completion traps by project type, read during the interview
- `references/scenarios.md`: skeletons per scenario
- `references/examples.md`: four worked examples (code, document audit in Portuguese, data batch, a vague request that is pushed back)

The eval suite for `claude plugin eval` (interview behaviour with and without the plugin, and two full-flow conformance cases) lives on the [`evals` branch](https://github.com/lucasgpinheiro-rgb/goal-composer/tree/evals), not on `main`, so it is not shipped to people who install the plugin. That branch is `main` plus one commit that adds `evals/`; see `evals/README.md` there.

Per goal, in `.claude/goals/`: `<slug>.md` (mandate), `<slug>-design.md` (chosen and rejected approaches, components, tests to criteria, steps; pinned), `<slug>-proofs.json` (proofs, counters, pins, sample, recorded baseline), `<slug>-attacks/` (the red-team's attack scripts), optionally `<slug>-verify.*` (verifier), and `<slug>-tasks.md` (checklist kept by the executor). Shared by all goals: `recheck-log.jsonl`, one JSON line per baseline or recheck run (goal, mode, verdict, counters, proofs file hash, time), which directory pins ignore.

## Open question: `/goal @file`

In Codex, `/goal @path/to/file.md` loads the goal from a file. It is not documented whether Claude Code's `/goal` expands `@file` in the condition. If it does not, the evaluator receives only the path and has nothing to judge. Test before relying on it: run `/goal @.claude/goals/<slug>.md`, then `/goal` with no argument, and check whether the status shows the file's text or just the path. Until confirmed, paste the text.

## What we measured

A retrospective over one real project, read from Claude Code transcripts without re-running anything: 15 goals composed with the skill and 18 `/goal` runs, in September 2026. It is a small case series with no control group, so it says what happened with the skill, not what would have happened without it.

- **Red-team.** In the 3 rounds whose reports could be counted, none of the 31 attacks was fully blocked by the first draft (28 unblocked, 3 partly). In the final mandates 28 were closed, 4 of them only weakly (a rule in prose, not a check), and 3 were left open.
- **Branch (B) exit.** 3 runs were pasted into the wrong checkout; the first-action guard printed BLOCKED and the goal ended through branch (B) with nothing touched. One older run, written before branch (B) existed, was relaunched 27 times against a 20-turn limit until the user cleared it.
- **Recheck.** A recheck was recorded for only 4 of the 14 executed goals (all DONE), so "no false completion caught" means little. That gap is why 1.1.0 writes every baseline and recheck to `recheck-log.jsonl`.
- **Baseline.** No vacuous or invalid proof reached the baseline in 10 goals; it caught 2 broken proof commands.

## Limits

- No check guarantees that a proof captures your intent. The baseline, counters and red-team make proofs harder to satisfy vacuously or by shortcut; they do not make them complete. The sample exists for the part only you can judge.
- Subjective end states (style, tone, "reads well") have no transcript proof; the skill says so instead of writing a condition that cannot be judged.
- Exercised in practice on Windows 11 with Git Bash. macOS and Linux have not been exercised yet; please report issues.

## Em português

A skill conversa na língua de quem a usa e escreve o mandato nessa língua, com rótulos próprios para português (`OBJETIVO`, `CONCLUÍDO QUANDO`, `PARADA`...). O exemplo 2 de `references/examples.md` é um mandato completo em português. Instalação e uso são os mesmos descritos acima.

## Prior art and credits

Other skills already help write `/goal` conditions, and this one takes ideas from several of them:

- [grill-me](https://www.aihero.dev/my-grill-me-skill-has-gone-viral) by Matt Pocock: the interview, one question at a time, each with a recommended answer.
- [goal-prompt-builder](https://github.com/win4r/goal-prompt-builder) by win4r, written for Codex: false-completion traps by project type, scenario skeletons, a first action that prints counts, numbers or an enumerable source instead of "all", 3 to 8 criteria, stop conditions that can be detected mechanically, and short design notes at delivery.
- [goal-forge](https://github.com/michaelpersonal/goal-forge) by Michael Guo: a fast check while iterating and a log of discarded attempts.
- [goal-setter](https://github.com/computerphilosopher/agent-skills/tree/main/skills/goal-setter) by computerphilosopher: what a BLOCKED report must contain, the research report format, and the `/goal @file` question.
- [goal](https://github.com/patrick-fu/awesome-skills) by patrick-fu: the rule for when to ask and when to assume a default.

Exploring approaches and then validating a design section by section follows the same pattern as the [brainstorming](https://github.com/obra/superpowers/blob/main/skills/brainstorming/SKILL.md) skill in obra/superpowers. Three more ideas come from the same repository (MIT): every target proof names the break it catches ("name the break", from `test-driven-development/writing-good-tests.md`); a red-team fix counts as closed only when it is a check that fails mechanically, not a prose rule ("match the form to the failure", from `writing-skills`); and the executor logs every decision the mandate does not settle as a ruling with its cost if wrong (from `subagent-driven-development`).

Running the red-team's attacks instead of reading them is the idea behind mutation testing. The list of cheap fakes (a constant stub, a swallowed error, a requirement quietly narrowed) and the implicit cases the interview asks for (the negative case, empty and error states) come from [Spec Drift Detector](https://github.com/h102-log/spec-drift-detector-plan) (MIT). The labelled read-back at the end of the interview, and the rule that a criterion that cannot be checked is badly written, come from [GroundWork](https://github.com/Hemanthkaruturi/GroundWork) (MIT).

What goal-composer adds is the verification side: the design bound into the mandate (a rejected approach becomes a stop clause), the branch (B) exit, the red-team pass on the proofs with its attacks executed, the baseline that rejects vacuous proofs, and the independent recheck with counters and hash pinning.

## License

MIT, see [LICENSE](LICENSE).
