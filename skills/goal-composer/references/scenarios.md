# Scenario skeletons

Pick one in Phase 1 and start the draft from it in Phase 6. Skeletons are in English; write the mandate in the user's language with the matching labels. Placeholders are in `<angle brackets>`. Each skeleton lists only what is specific to the scenario. Always added from the SKILL.md template, verbatim: the DONE WHEN header with branch (B), the design-file sentence in FIRST ACTION and CONSTRAINTS, the PER-TURN PROTOCOL and the STOP block (with the three-strike line). The skeletons show only branch (A) of DONE WHEN; never paste a skeleton without (B).

Each scenario also says how deep Phases 3 (Approaches) and 4 (Design) go, and which stop situations to add. Every scenario gets the generic stop "a needed change falls outside SCOPE or against a CONSTRAINT"; every scenario with a design also gets "the work needs an approach the design rejected".

Use one scenario per goal. If the task mixes two (fix and then document), propose two goals.

## Contents
- Change: implement, fix or refactor within a bounded area
- Batch: N similar items from an enumerable source
- Audit: read-only comparison of a subject against a reference
- Research: read-only investigation producing a findings report
- Release review: read-only verdict on whether something is ready

---

## Change

**Fits when** the changes stay within one subsystem or a short list of files, and the "after" state is concrete (a behavior, a passing test, a produced file).

```
OBJECTIVE: <action> so that <concrete after state>.

FIRST ACTION: read .claude/goals/<slug>-design.md [and <spec paths>]; print the number of design steps [and of tasks and requirements found]; then continue without waiting.

DONE WHEN (B) OR (A). <header and branch (B) verbatim from the SKILL.md template>
(A) All of the following are true and their outputs are pasted in the transcript:
1. <new behavior> - proof: <specific test or check>, output printed
2. New tests for <behavior> exist and pass - proof: <test command for the new file>; new test count >= <number of requirements>
3. Existing suite still passes - proof: <full test command>, output printed
4. Build / type check passes - proof: <command>, output printed
5. Final summary lists each changed file with lines added and removed - proof: `git diff --stat`, output printed

SCOPE: may change <files or folders>. Do not change <neighbor subsystems>, public API in <file>.

CONSTRAINTS: no new dependencies. Test count must stay >= <baseline>. Forbidden: <traps for this project type>; editing existing tests to make them pass.
```

**Stop situations**: a change outside SCOPE becomes necessary; a new dependency is required; two requirements in the spec contradict each other (escalate, do not pick one); an existing test fails for a reason outside SCOPE.

**proofs.json**: criteria 1–2 `target`, 3–4 `invariant`; counter on tests (`no_decrease`). The direct proof (2b) is criterion 1 or 2.

**Approaches/Design**: full. Typical alternatives: change in place vs. a new module or wrapper; library vs. hand-written; one pass vs. a preparatory refactor first (often a separate goal). Design has all six sections; (e) must name the new tests criterion by criterion.

**Budget**: one or two files, 10–20 turns; three or more files, 20–35. Above that, split.

---

## Batch

**Fits when** the task is "do the same thing N times" and N comes from an enumerable source: a list file, an issue query, a folder, a spreadsheet column.

```
OBJECTIVE: <action> for the <N> <items> listed in <source>.

FIRST ACTION: read .claude/goals/<slug>-design.md and <source>; print the number of design steps, the number of items and their identifiers; then continue without waiting.

DONE WHEN (B) OR (A). <header and branch (B) verbatim from the SKILL.md template>
(A) All of the following are true and their outputs are pasted in the transcript:
1. Every item in <source> is done - proof: <verifier> prints one line per item (id, status) and "PASS <N>/<N>"
2. Each item has its own <commit / output file / record> - proof: <command listing them>, count = <N>
3. <invariant checks: suite, build, schema> - proof: <command>
4. Final summary is a table: item id | what was done | files touched | check result

SCOPE: per item, only <files related to that item>. Items outside <source> are not touched.

CONSTRAINTS: the item list comes only from <source>; do not add, merge or drop items. Forbidden: marking an item done without its check passing; skipping an item silently.
```

**Stop situations**: an item turns out not to exist or not to be reproducible (log it as skipped with the reason and continue only if the user allowed skips); an item requires a breaking change; the source changes during the run (items added or closed by someone else).

**proofs.json**: criterion 1 `target` with `expect_regex` on the PASS line; counter on items done (`no_decrease`) and, when relevant, on items in the source (`no_decrease`, so none are deleted). A `sample` of finished items is cheap and catches systematic errors.

**Approaches/Design**: full, but about the per-item procedure, not the items. Typical alternatives: one generic procedure vs. grouping items by kind; item order (riskiest first vs. source order); one commit per item vs. one per group. Design (c) is the per-item procedure, (d) says what happens to an item that fails, (f) the order.

**Budget**: roughly 1–3 turns per item plus 5. Above 40 turns, split the list.

---

## Audit

**Fits when** something must be checked against a reference (a spec, a checklist, a regulation, a design, a README) and the output is a report, not changes. Also fits document audits: policies, technical reports, contracts against a required-content list.

```
OBJECTIVE: audit <subject> against <reference> and produce <report path>; change nothing else.

FIRST ACTION: read .claude/goals/<slug>-design.md (the method) and <reference>; print the number of items to audit; list <subject> files and print their count; then continue without waiting.

DONE WHEN (B) OR (A). <header and branch (B) verbatim from the SKILL.md template>
(A) All of the following are true and their outputs are pasted in the transcript:
1. <report path> has one section per reference item (<N> sections) - proof: <verifier> prints the section count and PASS
2. Each section has: (a) the requirement quoted from <reference>, (b) where it is met, cited as <path:line / page and section>, (c) status: met / partially met / not met / not verified, with one sentence of reason, (d) up to <k> risks - proof: <verifier> checks the fields and that every cited location exists
3. The report ends with a summary table (status counts) and the single most important fix, with one sentence of reason
4. Nothing but the report changed - proof: <pinned subject folder in the recheck>; `git status --porcelain` lists only <report path> and .claude/goals/

SCOPE: read-only on <subject> and <reference>; may create only <report path>.

CONSTRAINTS: every status needs a citation; do not claim presence or absence without one. Anything that can only be judged by running, measuring or observing is marked "not verified" with what would be needed. Evaluate only against <reference>; do not add criteria of your own. Forbidden: editing <subject> or <reference>.
```

**Stop situations**: a subject file cannot be parsed (encrypted, scanned image without text, proprietary format); two parts of the reference contradict each other; a reference item cannot be located in the subject after searching (list the terms searched, mark it, and continue; stop only if more than <k> items end this way).

**proofs.json**: criteria 1–2 `target` (the report does not exist yet); pin the subject and reference folders; `sample` of 3–5 report sections for the user to check citations by hand. The citation checker (2c) is the core proof: fabricated citations are the main trap.

**Approaches/Design**: method only. Typical alternatives: walk the reference item by item vs. walk the subject section by section and map back. Design = (a) + Method (reading order, citation rule, when an item counts as "not located") + (e) + (f).

**Budget**: about 1 turn per 3–5 reference items plus 5.

---

## Research

**Fits when** the goal is to find out: how a system works, why something happens, what the options are, what is undocumented. Nothing is changed except the report.

```
OBJECTIVE: find out <question> in <sources> and write <report path>; change no sources.

DONE WHEN (B) OR (A). <header and branch (B) verbatim from the SKILL.md template>
(A) All of the following are true and their outputs are pasted in the transcript:
1. <report path> answers each of these questions: <q1>, <q2>, <q3> - proof: <verifier> prints one line per question with the section found
2. Every finding cites its location (<path:line / page / URL / record id>) - proof: <verifier> checks that cited locations exist
3. Findings are separated into: confirmed (direct evidence cited), indirectly supported (inference, with the reasoning), not verifiable (what would be needed), open questions
4. At least <m> items of <specific kind, e.g. undocumented behaviors> are listed, each with a citation
5. Nothing but the report changed - proof: pinned sources; `git status --porcelain`

SCOPE: read-only on <sources>; may create only <report path>.

CONSTRAINTS: no commands that change the environment (installs, builds, migrations). Do not present an inference as confirmed. Forbidden: citing a location without opening it.
```

**Stop situations**: a source needs a tool or credential not available; two sources contradict each other on a fact the question depends on (report both, stop only if it blocks every remaining question).

**proofs.json**: criteria 1–4 `target`; pinned sources; `sample` of findings. Numbers in criterion 4 must be ones the user is confident exist; otherwise drop the criterion rather than invite padding.

**Approaches/Design**: method only. Typical alternatives: read the code first vs. the data first vs. the documentation first; breadth-first survey vs. one question at a time. Design = (a) + Method (sources, order, when to stop searching a question) + (e) + (f).

**Budget**: 10–25 turns. Research runs long on reading, not writing.

---

## Release review

**Fits when** the output is a verdict on one or more candidates (branches, pull requests, document versions, datasets) and nothing is merged, pushed or changed.

```
OBJECTIVE: decide whether each of <candidates> is ready for <target>; do not merge, push or change anything.

DONE WHEN (B) OR (A). <header and branch (B) verbatim from the SKILL.md template>
(A) All of the following are true and their outputs are pasted in the transcript:
1. One report per candidate, <path pattern>, each with: diff size (files, lines), risk per changed file (low / medium / high, one-line reason), test results (command and exit code), missing items (up to 5), verdict - proof: <verifier> checks the fields in every report
2. Verdict is exactly one of: ready / needs work / blocked, with at most 3 blockers
3. Verdicts are based on running the checks, not on commit messages or descriptions - proof: each report includes the printed test output
4. Final summary table compares all candidates

SCOPE: read-only on <candidates>; may create only the report files.

CONSTRAINTS: each candidate is reviewed independently. Forbidden: git push, merge, rebase, force-push; editing any candidate.
```

**Stop situations**: a candidate diff exceeds <size> lines (out of range for automated review, hand to a human); running the checks needs credentials or services not available; a candidate changes during the review (new commits or force-push).

**proofs.json**: criterion 1 `target`; pin or record each candidate's commit hash in the first action and compare at the end; invariant that the target branch did not move.

**Approaches/Design**: method only, often a single one; do not invent a second. Design = Method (which checks run on every candidate, in what order, what makes a verdict "blocked") + (e) + (f).

**Budget**: 5–10 turns per candidate.
