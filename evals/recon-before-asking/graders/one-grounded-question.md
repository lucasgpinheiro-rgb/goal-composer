---
type: llm
weight: 2
---

The workspace is a small Python CLI: reports/cli.py defines `report` (argparse, optional --region) and prints
a text table from reports/data.py; tests use unittest (`python3 -m unittest discover -s tests`). The request,
"add a --csv option to the report command", leaves open things the project cannot answer, such as which
columns and formats the CSV uses, whether it goes to stdout or a file, and whether --region still applies.

PASS if the final reply shows it inspected the project (it states at least one concrete fact from it, such as
unittest, reports/cli.py, argparse or the existing --region option) and asks the user at most one question,
that question comes with a recommended answer, and it concerns something the project does not answer.

FAIL if:
- it asks the user something the project already answers (which test framework, how to run the tests,
  where the report command lives, what language the project uses);
- it asks two or more questions in this reply;
- it asks a question without giving a recommended answer;
- it delivers a finished /goal condition or mandate without asking anything.
