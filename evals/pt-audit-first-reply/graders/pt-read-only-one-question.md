---
type: llm
weight: 2
---

The user wrote in Portuguese and asked to audit the procedures in procedimentos/ (3 files) against
referencia/checklist.md (5 items). This is a read-only audit: nothing in procedimentos/ or referencia/
should change.

PASS if the final reply is written in Portuguese, treats the task as a read-only audit (it does not propose
editing procedimentos/ or referencia/), and asks the user at most one question, which comes with a
recommended answer.

FAIL if:
- the reply is mainly in English;
- it proposes changing, fixing or rewriting the audited procedures or the checklist as part of this goal;
- it asks two or more questions in this reply, or a question with no recommended answer;
- it delivers a finished /goal condition or mandate without asking anything.
