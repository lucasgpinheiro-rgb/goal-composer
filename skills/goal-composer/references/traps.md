# False-completion traps by project type

Ways an executor can make proofs pass while the work is not done, often without meaning to. In Phase 5 (question 3, forbidden shortcuts), turn each trap that applies into a prohibition, a stricter proof flag, a counter or a pinned path. Read only the sections that match the project.

## Contents
- General (always)
- Node / TypeScript
- Python
- Go
- Rust
- JVM and .NET
- Browser automation (Playwright, Selenium, Puppeteer)
- Documents
- Data and spreadsheets

## General (always)

- **Edited checker**: the verifier, test fixtures, reference files or expected outputs are changed to match the output. Pin them.
- **Stale output**: a result printed before a later change is presented as current. The final rerun and the recheck cover this.
- **Filtered run**: the proof command gets narrowed (a path, `-k`, `--grep`, a subset) so failing parts do not run. Keep proof commands literal in the mandate and in `proofs.json`.
- **Local-only state**: success depends on an environment variable, a cache or a file outside the repository. The recheck from a clean shell exposes it.
- **Catch-all error handling**: `except Exception: pass`, empty `catch {}` or `|| true` swallow the failure the proof should detect. Forbid adding them in scope.

## Node / TypeScript

- `.skip`, `xit`, `describe.skip` count as passing; `.only` silently disables every other test in the file. Forbid both; counter on the number of tests executed.
- `--passWithNoTests` makes an empty run exit 0. Never allow it in proof commands.
- Jest with babel or `isolatedModules` strips types: tests pass while `tsc` fails. Add `npx tsc --noEmit` as a proof when TypeScript is involved.
- Snapshot updates (`-u`, `--updateSnapshot`) rewrite the expectation to match the output. Forbid them; pin `__snapshots__/` if it matters.
- Build or transpile caches (`node_modules/.cache`, `.next`, `dist`) can serve old code. Clear them inside the proof command when relevant.
- Monorepos: `npm test` may run one workspace only. Name the workspace or use the workspace flag explicitly.
- `// @ts-ignore`, `@ts-expect-error`, `any` and `eslint-disable` silence the type checker or linter. Forbid new ones in scope.

## Python

- `@pytest.mark.skip`, `skipif`, `xfail` count as not failing. Forbid adding them; `-rs` in the proof prints skip reasons.
- No tests collected exits 5 in pytest, which is a failure; but a `-k` filter or a wrong path can still collect far fewer tests than intended. Counter on collected tests.
- Tests may import an installed copy of the package (site-packages) instead of the source being edited. Prefer `{python} -m pytest` from the root with an editable install, or check `pkg.__file__` in the first action.
- `# type: ignore`, `# noqa`, `cast(Any, ...)` silence mypy or ruff. Forbid new ones in scope; run mypy as a proof if types matter.
- Autouse fixtures or `conftest.py` mocks can hollow out what a test exercises. Pin `conftest.py` if the goal does not need to change it.
- Floating-point or date comparisons loosened to make a test pass (`approx` with a huge tolerance). Forbid changing tolerances in existing tests.

## Go

- `go test` caches results and prints `(cached)`: use `-count=1` in proofs.
- `t.Skip` passes silently. Forbid adding it; `-v` shows skips.
- Build tags can exclude the files under test. Name the tags in the proof if the project uses them.
- `//nolint` silences linters. Forbid new ones in scope.

## Rust

- `#[ignore]` tests do not run by default. Forbid adding it.
- `cargo test` runs default features only; code behind other features is not compiled. Add `--all-features` or the specific feature to the proof.
- `#[allow(...)]` silences warnings and clippy. Forbid new ones in scope; `cargo clippy -- -D warnings` as a proof if lint matters.

## JVM and .NET

- `@Disabled` / `@Ignore` (JUnit), `[Ignore]` / `Skip=` (xUnit, NUnit) pass silently. Forbid adding them.
- `-DskipTests`, `-Dmaven.test.skip` or a narrowed surefire filter skip the suite. Keep proof commands literal.
- Incremental build output can be stale; use `clean` in the final proof.

## Browser automation (Playwright, Selenium, Puppeteer)

- Retries (`retries` in the config, `--retries`) hide flaky failures. Run proofs with retries set to 0.
- Fixed sleeps (`waitForTimeout`, `time.sleep`) make a run pass by timing luck. Forbid adding them; require waiting on a condition.
- Selectors that match the wrong element (first match, loose text) make assertions pass on the wrong thing. Require a screenshot or the matched element's text in the output for the direct proof.
- Route mocking or recorded responses (`page.route`, HAR playback) can mean the real flow never ran. State whether mocks are allowed and where.
- Headless and headed browsers can behave differently. Name the mode in the proof.
- External effects: automation against production can submit, send or sign for real. Default to a test environment or a dry-run flag, and list irreversible actions under EXTERNAL EFFECTS.

## Documents

- **Stub outputs**: the right number of files exists but some are empty or a few lines long. Check a minimum length per file in the verifier (words or lines), not only the count.
- **Placeholders**: `TODO`, `[TBD]`, `XXX`, `lorem ipsum`, "to be completed" left in the output. The verifier searches for them; case-insensitive.
- **Untranslated or copied passages**: in translation or rewriting, paragraphs remain in the source language or identical to the source. The verifier compares against the source (exact-match ratio) or checks for common source-language words.
- **Fabricated citations**: references to pages, sections, file lines or records that do not exist. The verifier checks that each cited location exists and is in range.
- **Broken structure**: headings, numbering, table of contents or cross-references not updated. Check that every entry in the index exists and vice versa.
- **Encoding damage**: mojibake such as `Ã§`, `Ã£`, `Â`, or replacement characters `�`. Search for them in the verifier.
- **Edited sources**: the source documents were changed to fit the output. Pin the source folder.

## Data and spreadsheets

- **Count matches, content does not**: the row count equals the source while rows were dropped and duplicates added. Check key uniqueness and that the key set equals the source key set.
- **Silent defaults**: missing values filled with 0, empty strings or a default date so validation passes. Count nulls or defaults before and after; forbid imputation unless agreed.
- **Type and locale coercion**: dates swapped between day/month, decimal comma versus point (`1.234,56` vs `1,234.56`), leading zeros stripped from IDs or codes. Check a few known values explicitly in the verifier.
- **Self-comparison**: the output is compared against itself or against a file the executor produced, instead of an independent reference. Pin the reference.
- **Spreadsheet cached values**: libraries such as openpyxl return the cached result of formulas, which can be stale or empty for files never opened in Excel. Recalculate or check formulas separately when formulas are part of the output.
- **Truncation**: exports cut at a row limit, a page size or an API pagination boundary. Compare totals against the source system's own count.
- **Edited raw data**: the input was cleaned in place to make the pipeline pass. Pin the raw data folder.
