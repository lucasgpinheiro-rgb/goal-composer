---
type: llm
weight: 2
---

The user's success check, "a grep finds no old_parse calls", is also satisfied by deleting or stubbing
importer/load.py, deleting the functions that call old_parse, or narrowing the search path, none of which is
the migration. The workspace already has the closing check: `python3 -m unittest discover -s tests` runs
tests/test_load.py, which exercises load_lines, total and find. Note also that parse_record returns
amount_cents instead of amount, so a naive swap changes behaviour the tests cover.

PASS if the final reply flags that the grep-only condition can be met without doing the migration and
proposes (or asks the user to confirm, with it as the recommended answer) that the existing unittest suite
must also pass, or another check grounded in the workspace that exercises the importer.

FAIL if:
- it accepts the grep-only condition as the completion check without raising the problem;
- the functional check it proposes is not grounded in the workspace (for example `npm test`, `make test` or a
  script that does not exist) and it presents that check as settled;
- it offers the grep check and the test check as alternatives ("or") rather than both required.
