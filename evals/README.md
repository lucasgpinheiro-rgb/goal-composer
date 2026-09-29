# Evals

Eval suite for `claude plugin eval` (Claude Code v2.1.269 or later). Every run and every judge call is a real model call billed to your Claude account.

## Cases

**interview** (4 cases, single reply, scored with and without the plugin)

| Case | Passes when |
| --- | --- |
| `vague-request-pushback` | "make the whole app faster" gets questions about the operation, measure and target, not a mandate |
| `grep-only-easy-out` | a grep-only success check is flagged as satisfiable by deleting the callers and paired with the project's unittest suite |
| `recon-before-asking` | the reply shows facts read from the project and asks at most one question, with a recommended answer, that the project cannot answer |
| `pt-audit-first-reply` | a Portuguese audit request gets a Portuguese, read-only first reply with at most one question and a recommended answer |

**pipeline** (2 cases, full flow, conformance only)

| Case | Passes when |
| --- | --- |
| `pipeline-change-en` | with every decision delegated to the skill's recommendations: design and proofs files exist, a red-team subagent ran, the transcript shows `VERDICT: BASELINE OK` and `RESULT: OK`, the mandate has the `(B) ENDED` branch, the recheck command carries a 64-hex hash, and nothing was written outside `.claude/goals/` |
| `pipeline-audit-pt` | the same for a Portuguese read-only audit, plus Portuguese labels and `procedimentos/` pinned by hash |

Each case builds its own small project with `scaffold.sh` (Python standard library only, clean git tree).

## Run

From the repository root, on Linux, macOS or WSL2 (native Windows has no sandbox for the Bash grants the pipeline cases need; on Linux, first install the sandbox dependencies listed in the Claude Code sandboxing documentation). Python 3.10 or later.

```
claude plugin eval . --tag interview --scaffold --judge-model sonnet --max-cost-usd 5
claude plugin eval . --tag pipeline --ablation none --scaffold --allow-tools Bash Write Edit --runs 1 --max-cost-usd 10
```

The cost ceilings are placeholders; adjust them. The interview group is 4 cases × 3 runs × 2 arms = 24 short runs plus judge calls. The pipeline group is 2 long runs (up to 80 turns each, with a subagent). To iterate on one case cheaply: `claude plugin eval . --case <name> --runs 1 --ablation none --scaffold`.

`--judge-model sonnet` is recommended because the rubrics ask the judge to count questions and tell a question from a decision; a small judge is more likely to misread them.

## How to read the results

- **Interview Δ** is the with-plugin score minus the no-plugin score for the same prompt. The skill is slash-only, so every prompt starts with `/goal-composer:goal-composer`. Without the plugin, Claude Code does not reject that unknown command locally (checked with v2.1.284: it goes on to call the model), so the no-plugin arm is answering the same request without the skill.
- **`skill-fired`** is an indicator, not part of the score: it passes when the skill's text appears in the run's trace.
- **Pipeline cases** delegate every decision in the prompt ("take your recommended answer at every question"). That is not the intended interactive use; they test whether the skill's own gates (red-team, baseline, validator) pass when it reaches them, which a single-reply case cannot.

## Known traps

- **unittest targets.** The pipeline fixture uses unittest. Before goal-composer 1.0.1, `recheck_goal.py` reported a target for a test module that did not exist yet as `BROKEN` ("No module named"), and `discover -p test_x.py` as `VACUOUS` on Python 3.10 and 3.11 ("Ran 0 tests ... OK", exit 0). Since 1.0.1 a missing project module is an ordinary failure and a run with 0 tests never passes, so both forms fail at baseline as a target should. A missing tool or package, such as pytest not installed, is still `BROKEN`.
- **Home directory.** Sandboxed Bash cannot read your home directory. If a pipeline transcript shows the skill failing to open `recheck_goal.py` or `validate_goal.py`, run the suite from a clone outside your home directory.
- **Graders are the author's.** A high score says the skill does what these rubrics ask, not that the rubrics capture everything that matters.
