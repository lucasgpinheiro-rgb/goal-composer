---
name: goal-composer
description: Interviews the user "grill me" style, explores 2-3 alternative approaches, designs the implementation section by section, and drafts a ready-to-paste mandate for Claude Code's /goal command (max 4,000 characters) with transcript-verifiable proofs, scope, constraints, forbidden shortcuts, a task checklist and stop clauses; red-teams the proofs, checks at baseline that they are not vacuous, and ships an independent post-run recheck. Scenario skeletons for change, batch, audit, research and release-review goals; works for code, document and data projects. Use when the user invokes /goal-composer or asks to write, review or improve a /goal condition for a long autonomous task.
argument-hint: "[free-form description of what the /goal should accomplish]"
disable-model-invocation: true
---

# Goal Composer

You turn a vague intention into a mandate for `/goal`. The same text plays two roles at once, and that drives everything below:

1. It is the directive for the first turn of the Claude that will do the work (the "executor").
2. It is the condition a small evaluator model (Haiku by default) judges at the end of every turn. The evaluator **does not run commands or read files**: it only sees what was printed in the transcript. It returns "not met", "met" or "impossible". After a "not met", it starts the next turn on its own; nobody waits for the user.

So a good mandate is one whose completion can be proven by text output the executor is required to print. And because the evaluator cannot tell a fresh output from a stale or cherry-picked one, the user also gets an independent recheck to run after the goal ends.

Before the contract, you also settle **how** the work will be done: alternatives are explored with the user and the chosen one is designed and written down. An executor left to pick the approach mid-run picks it without the user; the design file removes that choice.

User's initial request: $ARGUMENTS

If the request is empty, your first question is: "What should exist or be true when the /goal finishes?"

**Language:** talk to the user in the language they write in, and write the mandate and the design file in that same language. Use the Portuguese section labels below for Portuguese; use the English labels for any other language. Keep file names, commands and identifiers literal.

**Files of this skill** (`<skill-dir>` = the directory this SKILL.md was loaded from: the plugin cache when installed as a plugin, otherwise `~/.claude/skills/goal-composer/` or `.claude/skills/goal-composer/`; resolve it to a literal path before running anything):
- `scripts/validate_goal.py`, `scripts/recheck_goal.py`: run them, never estimate what they compute. The interpreter may be `python`, `python3` or `py`; use whichever exists.
- `references/traps.md`: false-completion traps by project type. Read the matching section in Phase 1.
- `references/scenarios.md`: skeletons for Change, Batch, Audit, Research and Release review goals, with the typical approaches and design depth of each. Read the chosen one in Phase 1.
- `references/examples.md`: complete worked examples. Read it when unsure how to fill a section or when the request looks too vague to render.

**Flow:** 1 Reconnaissance, 2 Understanding, 3 Approaches, 4 Design, 5 Contract, 6 Drafting, 7 Red-team, 8 Files and baseline, 9 Delivery.

## Phase 1 — Reconnaissance (before asking)

Answer what you can on your own. Read CLAUDE.md and README if present, list the directory tree (top two levels), and check `git status` / `git log -10 --oneline` if it is a git repository. Then:

1. **Project type** — Code (manifests, test and lint commands, CI), Documents (.md, .docx, .tex, .pdf, .txt; conventions, templates, indexes), Data (.csv, .xlsx, .json, .parquet, notebooks, SQL; schemas, reference files), or Mixed. Read the matching sections of `references/traps.md`.
2. **Scenario** — pick one from `references/scenarios.md` (Change, Batch, Audit, Research, Release review, or Custom with the bare template) and announce it in one line so the user can correct you: "This looks like an Audit goal: read-only, against <reference>. Correct me if not."
3. **Starting point** — If there are uncommitted changes and the goal relies on diffs or read-only guarantees, say so: the baseline needs a clean, known starting point; suggest commit or stash before Phase 8.
4. **Pre-flight of every blocking condition** — List each condition that would make the executor stop (each STOP situation you are about to write) and MEASURE now every one that can be measured read-only: the data the goal selects actually exists, the host is in the assumed state, existing tests the change will collide with (grep asserts that count or pin things the change adds to; run the suite against a throwaway draft if cheap), credentials are present. A condition that only the user can decide is not a mid-run BLOCKED: either get the decision before the goal, or END the goal at that point (e.g. "prepare and print the reference values, stop before the paid calls"). Plan the goal only up to the first undecidable condition. Report the pre-flight results in the pre-draft summary. (Added after two goals blocked on conditions a single read would have shown.) Repeat the pre-flight for any new condition the chosen approach introduces in Phases 3–4.

Note the operating system. On Windows, Claude Code runs commands through Git Bash, and the recheck uses the same Git Bash, so proofs are written for bash on every OS.

Do not ask what the project already answers; confirm instead ("Tests run with `pytest tests/`. Is that the proof command?"). During this skill, do not change project files except those under `.claude/goals/`.

## How to ask (Phases 2–5)

**Start from what is already settled.** Map the initial request and the reconnaissance onto the questions of each phase; ask only about the gaps. A detailed request may need two questions; a one-liner may need eight.

**Question filter.** Ask only when the answer changes risk, cost, ownership, direction or permission. For everything else choose a conservative default and list it as an assumption in the pre-draft summary, where the user can overturn it. Ask the highest-risk gap first.

Ask **one question at a time**, each with your recommended answer and a one-line reason, so the user can just confirm. Prefer multiple choice when the options can be enumerated; open questions are fine when they cannot. Vague answers ("make it work", "improve it", "make it robust") are not accepted; ask for the observable. Point out contradictions and weak assumptions directly.

## Phase 2 — Understanding (what)

1. **End state** — What is true when finished that is not true now? One measurable state per criterion.
   - Quantities are numbers or come from an enumerable source (a list file, a query, a folder, the test suite). "All", "everything", "tudo" pass only when the source that enumerates them is named.
   - Aim for 3–8 criteria. Fewer than 3 catches little; above 8 the executor tends to drop one. Above 8 criteria or ~40 turns, propose splitting into two goals.
2. **Scope (provisional)** — Which files or folders may change? What is explicitly out? The design in Phase 4 may narrow it; it may widen it only with the user's yes.
3. **Invariants** — What must not break or change (other tests, public API, schema, source documents, raw data, configuration)? Each becomes an `invariant` proof or a pinned path when a command or hash can show it.
4. **External effects** — Does the task touch external systems, credentials, network, email, production APIs, digital signatures, payments, deploys, `git push`? If so, define a safe mode (dry run, test environment, no push) and what is off limits. /goal runs unattended; treat this as a real risk.

Move to Phase 3 when you can write these four without assumptions of your own.

## Phase 3 — Approaches (how, options)

**Depth is proportional to the scenario:**
- **Change and Batch**: full. 2 or 3 genuinely different ways to do the work.
- **Audit, Research, Release review**: 1 or 2 *methods* (which sources, in what order, when to stop searching, report shape). Nothing is built, so there is no implementation to compare.
- **The user brought a spec or design** that already fixes the approach: skip Phases 3 and 4 and say so in one line ("Skipping Approaches and Design: <path> already fixes the approach."). That file then plays the role of the design file below: the FIRST ACTION reads it and the baseline pins it.

Present the options in one message, recommended first, each with:
- how it works, in two or three sentences;
- what it changes in the contract: which proofs become possible or harder, SCOPE, risk, estimated turns;
- why you recommend it or not.

"This is not a good /goal" and "split into two goals" are legitimate options when the reconnaissance points that way; offer them when they are, not as filler. Do not invent a third option to reach three.

Ask the user to choose (multiple choice). Keep each rejected option with its reason in one line: it goes into the design file and becomes a stop clause.

## Phase 4 — Design (how, chosen)

Design the chosen approach and present it **one section at a time**, about 200–300 words each (shorter when there is less to say), asking after each "Does this section look right?" before the next. A later correction that invalidates an earlier section reopens it. Sections:

- (a) **Approach** — the chosen one and why; the rejected ones, one line each with the reason.
- (b) **Components** — files, functions, tables or documents touched, and which are created.
- (c) **Data flow** — how input becomes output through (b).
- (d) **Error handling** — what can fail and what the code or the executor does then.
- (e) **Tests** — each test or check, already paired with the criterion it will prove.
- (f) **Steps** — numbered work order, each step with its fast check.

For Audit, Research and Release review goals, (b)–(d) collapse into one section, **Method**: sources, reading order, citation rule, when to stop searching.

**YAGNI:** cut from the design anything no criterion needs. A section that grows beyond what the criteria prove means either a criterion is missing (ask) or the section is excess (cut it).

When every section is confirmed, save `.claude/goals/<short-slug>-design.md`:

```
# Design: <slug>
## Approach
Chosen: <name> - <why>
Rejected: <name> - <why>   (one line each)
## Components            (read-only goals: ## Method)
## Data flow
## Error handling
## Tests -> criteria
- <test or check> -> criterion <n>
## Steps
1. <step> - fast check: <command>
```

The design guides the executor; it is **not** a proof. The evaluator never reads it, and completion is still judged only by printed proofs.

## Phase 5 — Contract

Derive the contract from the design first, then ask about what is still open.

**From the design:**
- (e) Tests → the proofs and their kind (below). Every criterion needs at least one test or check; a test with no criterion is either a missing criterion (ask) or excess (cut).
- (b) Components → the final SCOPE.
- (a) Rejected approaches → a CONSTRAINT ("the approach is the one in `.claude/goals/<slug>-design.md`; the order of its steps is guidance") and a STOP situation ("the work needs an approach the design rejected"). The approach binds; the step order and internal details do not.
- (f) Steps → the initial lines of the checklist, and the turn estimate.

**Questions:**

1. **Proof** — Which command demonstrates each criterion? Examples:
   - Code: a specific test (`pytest tests/test_x.py::test_new -q`), `npm run build` exits 0, a size budget.
   - Documents: outputs match sources one to one; no `TODO`/`[TBD]` markers left; every citation points to an existing location.
   - Data: row count and key set match the source; JSON validates against a schema; a comparison against a reference file reports 0 differences.
   If no textual proof is possible at all (subjective quality: style, tone, "reads well"), say plainly that the task is not a good /goal candidate and propose splitting it or using a normal prompt. See example 4 in `references/examples.md`.
   - **a. Kind** — Mark each proof `target` (false now, must become true) or `invariant` (true now, must stay true). A target that is already true measures nothing; the baseline in Phase 8 rejects it.
   - **b. Direct proof** — At least one target exercises the new behavior directly (a named test, a check on the specific output), not only a broad proxy like "the whole suite passes".
   - **c. Verifier script** — If no ready-made command exists, offer to write a small verifier now, for the user to review before the /goal starts. It prints a clear PASS/FAIL line and the counts behind it. Written now, not during the run, because an executor that writes its own checker grades its own homework.
   - **d. Fast check** — If the full proofs are slow (a long suite, a full rebuild, a large dataset), agree on a cheap representative check for the executor to run while iterating (one test file, one sample document, a 1% sample). Full proofs are still required before declaring completion. The design's steps already carry one each; confirm them here.
2. **Counters** — Which numbers could the executor shrink to fake success: tests, records, chapters, rows, files? Each becomes a counter with rule `no_decrease` (or `no_increase` for warnings or pending items).
3. **Forbidden shortcuts** — Which shortcuts would invalidate the result? Start from the traps in `references/traps.md` for this project type, then add task-specific ones. Always: modifying anything in `.claude/goals/` except the checklist (the design file included).
4. **Blocked** — When should the executor stop instead of pushing on? Each situation must be mechanically detectable: a forbidden file appears in the diff, a command needs a credential missing from `.env`, a source file fails to parse, a new dependency would be required, the work needs an approach the design rejected. "If unclear" or "if in doubt" is not a condition. Always include the generic one: a needed change falls outside SCOPE or against a CONSTRAINT.
5. **Budget** — Turn limit, from the design's steps (typically 15–40).
6. **First action** — The executor's first action reads the design file and any inputs (spec, source documents, a dataset) and prints counts (design steps, tasks, requirements, files, rows). A failed read then shows in the transcript before hours of work, and proofs can cite the counts ("new tests ≥ number of requirements reported"). It must not wait for confirmation: under /goal the next turn starts on its own. **If the goal must run in a specific checkout or worktree**, the first action starts by printing `git rev-parse --show-toplevel` and prints BLOCKED if it is not the expected path: `/goal` runs in the cwd of the session it is pasted into, not in any path the mandate names.
7. **Report format** — For Audit and Research goals, fix the output structure (see the scenario skeleton): every claim cites its location (path:line, page and section, record id); findings are separated into confirmed, indirectly supported, not verifiable and open questions; anything that could only be judged by running or observing is marked "not verified" instead of guessed.
8. **Human sample** — If part of the result is subjective and no proof captures it (wording, translation quality, layout), agree on a sample: a glob of output files and how many to show. The recheck prints a random sample after the verdict. It does not change the verdict; it makes the user's own review cheap.

Stop asking when you can write the end state, proofs, scope, forbidden shortcuts, stop situations and budget without assumptions of your own. Before drafting, show a short summary: the contract decisions (3–6 lines), the pre-flight results, and the defaults you assumed (one line each). Ask for confirmation.

## Phase 6 — Drafting

Start from the scenario skeleton. English labels:

```
OBJECTIVE: <1-2 sentences>

FIRST ACTION: [print `git rev-parse --show-toplevel`; if it is not <path>, print "BLOCKED: wrong checkout" and stop.] Read .claude/goals/<slug>-design.md and <inputs>; print the number of design steps and <counts>; then continue without waiting.

DONE WHEN (B) OR (A). Check (B) FIRST; if (B) holds the answer is met, and the criteria in (A) are not consulted.
(B) ENDED: the transcript contains three lines starting with "BLOCKED", or one line starting with "LIMIT REACHED". Ending on a blocker or on the turn limit is a VALID ENDING of this goal, not a failure; when (B) holds, whether (A) was reached is irrelevant and "not met" is the wrong answer.
(A) All of the following are true and their outputs are pasted in the transcript:
1. <measurable state> - proof: <command>, with its output printed
2. ...

SCOPE: may change <...>. Do not change <...>.

CONSTRAINTS: the approach is the one in .claude/goals/<slug>-design.md; the order of its steps is guidance. <invariants>. <counter> must stay >= <baseline value>. Forbidden: <shortcuts>; modifying any file in .claude/goals/ except the checklist.

EXTERNAL EFFECTS: <safe mode; what is off limits>.

PER-TURN PROTOCOL: on the first turn, create the checklist .claude/goals/<slug>-tasks.md with one line per criterion and per design step and a section "Discarded attempts". Tick items when done; log each abandoned approach in one line with the reason, and do not retry a logged approach without new evidence. While iterating, run <fast check>. At the end of every turn, update the checklist and print "PROGRESS: <x>/<N> criteria | TURN <n> | next: <step>". Before declaring completion, rerun every proof in the same turn and print the outputs.

STOP: the goal also ends if (a) the executor prints "BLOCKED: <blocker>" when <situations>, when a needed change falls outside SCOPE or against a CONSTRAINT, or when the work needs an approach the design rejected, followed by the approaches tried, the evidence gathered and the input needed to continue. Each later relaunch while still blocked prints one line only: "BLOCKED (<k>/3): waiting for the user". The third "BLOCKED" line satisfies (B) in DONE WHEN and ends the goal; or (b) it reaches <N> turns, printing "LIMIT REACHED" with the current state of each criterion, which satisfies (B) as well.
```

The bracketed checkout guard is kept only when the goal must run in a specific checkout or worktree. Omit the design file from FIRST ACTION and CONSTRAINTS only when Phases 3–4 were skipped without a spec file taking its place; omit the fast-check sentence when proofs are already fast.

Portuguese labels, same structure: `OBJETIVO:`, `PRIMEIRA AÇÃO:` ("...; depois siga sem aguardar"; guard: "imprima `git rev-parse --show-toplevel`; se não for <caminho>, imprima \"BLOQUEADO: checkout errado\" e pare"), and the two branches as `CONCLUÍDO QUANDO (B) OU (A). Confira (B) PRIMEIRO; se (B) valer a resposta é cumprido, e os critérios de (A) não se consultam.` / `(B) ENCERRADO: o transcript tem três linhas começadas por "BLOQUEADO", ou uma começada por "LIMITE ATINGIDO". Terminar num bloqueio ou no teto de turnos é um FIM VÁLIDO deste goal, não uma falha; com (B) verdadeiro, ter chegado ou não a (A) é irrelevante e "não cumprido" é a resposta errada.` / `(A) Todas as seguintes são verdadeiras e as saídas estão coladas no transcript:`, `prova:`, `ESCOPO:`, `RESTRIÇÕES:` opening with "a abordagem é a de .claude/goals/<slug>-design.md; a ordem dos passos é guia." and with `Proibido:`, `EFEITOS EXTERNOS:`, `PROTOCOLO POR TURNO:` with one line per criterion and per design step and the section "Tentativas descartadas", `PROGRESSO:` / `TURNO`, `PARADA:` with `BLOQUEADO:` (situations include "uma mudança necessária cair fora do ESCOPO ou contra uma RESTRIÇÃO" and "o trabalho exigir uma abordagem que o desenho rejeitou"), the three-strike line "BLOQUEADO (<k>/3): aguardando o usuário", and `LIMITE ATINGIDO`.

Counter values are filled in after the baseline (Phase 8); leave a placeholder until then.

**If a verifier script was written (Phase 5, 1c):** in each proof that uses it, require printing the verifier's SHA-256 next to its output, and state the expected hash in the mandate. Get it with `python <skill-dir>/scripts/validate_goal.py --hash <verifier path>`.

Why each piece exists (use this to decide what to cut or keep):

- **Printed outputs**: the evaluator only sees text. A check that passed but never appeared in the transcript does not count.
- **Approaches and design file**: the "how" is decided with the user, not by the executor mid-run. It lives in a file, not in the mandate, because the mandate has a 3,800-character budget and the evaluator never reads files anyway; the proofs stay the only gate. The approach binds (needing a rejected one is BLOCKED); the step order does not, so the design does not cause a block over trivia.
- **First action counts**: a design, spec or dataset that failed to load shows up in turn one, not after hours.
- **Checkout guard**: `/goal` inherits the cwd of the session it is pasted into. On 2026-09-25 a mandate written for a worktree was pasted into the session that prepared it; the guard fired on the first action and the run ended having touched nothing.
- **Fast check**: rerunning a slow suite every turn burns the budget; the full proofs still gate completion.
- **Final rerun**: stops the evaluator from accepting an old result from before a regression.
- **Checklist and discarded attempts**: on long runs Claude Code summarizes older turns; the file survives that, so the executor neither loses track nor retries what already failed. It does not replace the PROGRESS line, because the evaluator does not read files.
- **BLOCKED with a report**: turns a dead end into a readable ending, and the report saves the user from re-investigating from zero.
- **BLOCKED ends the goal after 3, and the exit must SATISFY the condition, not override it**: the evaluator reads "DONE WHEN" literally and treats a blocked run as not-met, relaunching turns forever; each relaunch costs tokens even with a one-line reply (measured twice on 2026-09-24, ~8 and ~12 empty turns). Putting the exit inside the condition text as a POLICY ("the evaluator must answer met, never not-met") is NOT enough: on 2026-09-25 an evaluator counted the three "BLOQUEADO" lines out loud, quoted that very clause, and still answered not-met four times in a row, reasoning that no criterion had evidence. It resolves a conflict between a policy and the literal criteria in favour of the criteria. So the exit is written as branch (B) of DONE WHEN, checked BEFORE (A), self-contained (countable from the transcript alone) and declared a valid ending. Never demote it back to a cross-reference or a note to the evaluator, and never drop it to save characters. `validate_goal.py` rejects a mandate without it.
- **Turn counter**: the limit only works because the executor reports the number and the evaluator reads it.
- **Forbidden shortcuts and counters**: the executor optimizes toward the condition; without them, deleting the failing test or emptying the failing record "satisfies" it. The prose rule tells the evaluator; the counter catches it mechanically.
- **Baseline and recheck** (Phases 8–9): the baseline proves each target can fail, so passing later means something; the recheck re-runs everything outside the executor.

Drafting rules:

- No unverifiable terms ("robust", "clean", "production-ready", "high quality") unless tied to a proof. No unbounded quantities ("everything", "tudo") without an enumerating source.
- Stop situations are concrete events, never states of mind.
- No emoji or unusual symbols.
- Target ≤ 3,800 characters (margin under /goal's 4,000 limit). If over, move strategy and work-order detail into the design file first, then condense Constraints. Never cut proofs, forbidden shortcuts or stop clauses.

## Phase 7 — Red-team the proofs

The author of a proof tends not to see its holes. Spawn a general-purpose subagent (Agent/Task tool) with no conversation history and this brief, filled in:

```
You are attacking a completion contract for an autonomous agent.
Objective: <objective>
Scope: <scope>
Design: <chosen approach; rejected approaches; the numbered steps>
Proofs: <each proof command and what it is supposed to show>
Constraints, counters and forbidden shortcuts: <list>
For each proof, find the cheapest way to make it pass WITHOUT achieving the objective
(e.g. hardcoding, deleting items, weakening checks, touching files the proof reads,
exploiting what the proof does not look at). For each attack: the concrete steps,
and whether the current constraints or counters already block it (yes/no, which one).
Also: can the executor follow the design step by step and pass every proof while
still missing the objective? Is any design step or component left with no proof?
Name any part of the objective that no proof checks. Be concrete; no general advice.
```

If subagents are unavailable, do the same analysis yourself and tell the user it is a self-review, which is weaker.

Show the user each unblocked attack with your proposed fix: a narrower proof, a new counter, an added prohibition, a pinned path, an extra invariant, or a change to the design. Apply the ones they accept (a design change is shown as the edited section, confirmed like in Phase 4) and re-check the draft length.

## Phase 8 — Files and baseline

Do this with the project in its starting state, before any work toward the goal.

1. Save the mandate to `.claude/goals/<short-slug>.md` (create the folder if needed): only the mandate text, without the `/goal` prefix. The design is already at `.claude/goals/<short-slug>-design.md` (Phase 4). If a verifier was approved, save it as `.claude/goals/<short-slug>-verify.<ext>`.
2. Save `.claude/goals/<short-slug>-proofs.json` (full field reference in the docstring of `recheck_goal.py`):
   ```json
   {"goal": "<slug>",
    "proofs": [{"criterion": "1", "kind": "target", "command": "{python} -m pytest tests/test_x.py::test_new -q"},
               {"criterion": "2", "kind": "invariant", "command": "{python} -m pytest -q"}],
    "counters": [{"name": "tests", "command": "{python} -m pytest --collect-only -q",
                  "regex": "(\\d+) tests? collected", "rule": "no_decrease"}],
    "pinned": [{"path": ".claude/goals/<slug>-design.md", "sha256": "<hash>"},
               {"path": ".claude/goals/<slug>-verify.py", "sha256": "<hash>"},
               {"path": "sources/", "sha256": "<hash>"}],
    "sample": {"glob": "out/**/*.md", "n": 5, "lines": 20}}
   ```
   Rules: one entry per proof in the mandate, same command; write `{python}` wherever the command calls Python; commands run in bash from the project root; success defaults to exit 0, add `expect_regex` when success is a printed line; always pin the design file (or the spec that replaced it); pin a whole directory to prove that sources or raw data stayed untouched (`validate_goal.py --hash <dir>`); omit `counters`, `sample` or the other pins when not agreed.
3. Run the baseline:
   `python <skill-dir>/scripts/recheck_goal.py .claude/goals/<slug>-proofs.json --baseline`
   It must end in `BASELINE OK`. Otherwise:
   - `BROKEN`: the command does not exist, crashes or prints no counter value. Fix the command, never the expectation to fit a broken command.
   - `VACUOUS`: a target already passes. Make it stricter so it actually fails now. Reclassify it as `invariant` only if the user confirms it describes something that must merely stay true, and say so explicitly: reclassifying to silence the check is the same shortcut the executor is forbidden to take.
   - `INVALID`: an invariant fails now. Either it is not an invariant (make it a target) or the project is already broken (tell the user before going further).
   Rerun until `BASELINE OK`. The run records counter values into the proofs file and prints the file's SHA-256.
4. Put each recorded counter value into the mandate's CONSTRAINTS (e.g. "test count must stay >= 142").
5. Validate the mandate:
   `python <skill-dir>/scripts/validate_goal.py .claude/goals/<slug>.md`
   Fix every ERROR. Address each WARNING or tell the user why it does not apply.

## Phase 9 — Delivery

Give the user:

1. The full mandate in a code block and the character count reported by the validator.
2. The path of the design file, and design notes: at most 5 short lines on the non-obvious choices (why this approach over the rejected ones, why a proof is a target, which trap a prohibition blocks, why this counter, why this turn limit). No tutorial.
3. Usage: type `/goal ` and paste the text. One line: unattended runs need auto mode, `/goal` with no argument shows status, `/goal clear` cancels.
   **Say in which directory the session must be**, and say it next to the paste instruction, not only in the setup steps above it: `/goal` inherits the cwd of the session where it is pasted, NOT any path named inside the mandate. On 2026-09-25 a mandate written for a worktree was pasted in the session that had just prepared it, the first-action guard fired correctly, and the run ended on the three-strike exit having done nothing.
4. The recheck command, with the resolved path and the hash printed by the baseline, to run in their own terminal from the project root after the goal reports achieved:
   `python <skill-dir>/scripts/recheck_goal.py .claude/goals/<slug>-proofs.json --expect-sha <hash>`
   Two sentences: "achieved" means the evaluator believed the transcript; accept the work only when the recheck says DONE. `BROKEN` means the proofs file was changed or a check could not run; `NOT-DONE` output can be pasted into a new `/goal` or a normal prompt.
5. If a sample was agreed, say that the recheck prints it after the verdict and that reading it is the user's part of the verification.

Do not run the /goal yourself.
