# Worked examples

Four complete runs, condensed. Use them to calibrate: how much to ask, how far Approaches and Design go, how specific proofs get, what goes into `proofs.json`, and when not to render at all. Hashes and baseline numbers are illustrative.

## Contents
1. Change, Python (English): detailed request, two questions, full design
2. Audit, documents (Portuguese): read-only, method-only design, citation checker, pinned sources
3. Batch, data (English): per-item procedure, counters and key-set checks
4. Vague request: push back instead of rendering

---

## 1. Change, Python

**Request**: "Add retry with exponential backoff to `fetch_invoice` in `billing/client.py`; 3 attempts; only on timeouts and 5xx."

**Reconnaissance**: Python, pytest (`tests/`, 212 tests collected), mypy configured, clean tree. Scenario: Change.

**Questions asked** (everything else was settled by the request or given a default):
1. "Should 429 (rate limited) also retry? Recommended: yes, it is transient like 5xx." → yes.

**Approaches** (Phase 3, one message, recommended first):
- A. Hand-written loop inside `fetch_invoice` (recommended): 20 lines, no dependency, the retry rule sits next to the call it guards. Proofs: a direct test file. About 15 turns.
- B. A `@retry` decorator in `billing/retry.py`, reused later by other calls: one more file in SCOPE and a second test file for the decorator itself. About 20 turns. Not worth it for one call site (YAGNI).
- C. The `tenacity` library: least code, but adds a dependency and its own semantics to test around.
→ User chose A. Rejected: B (one call site, YAGNI), C (new dependency).

**Design** (Phase 4, presented section by section; saved file, excerpt):
```text
# Design: invoice-retry
## Approach
Chosen: hand-written loop in fetch_invoice - one call site, no dependency
Rejected: decorator in billing/retry.py - YAGNI for one call site
Rejected: tenacity - new dependency
## Components
billing/client.py (fetch_invoice); new tests/billing/test_retry.py
## Error handling
after the 3rd failure, re-raise the last exception unchanged
## Tests -> criteria
- test_retries_on_timeout_5xx_429 -> 1
- test_no_retry_on_other_4xx -> 2
## Steps
1. write both tests (they fail) - fast check: pytest tests/billing/test_retry.py -q
2. add the loop with injectable sleep - fast check: same
3. mypy and full suite - fast check: python -m mypy billing/
```

**Assumed defaults** (listed in the summary): delays 0.5s/1s/2s, tests mock the transport and never sleep for real, no changes outside `billing/`.

**Mandate**
```text
OBJECTIVE: Add retry with exponential backoff to fetch_invoice in billing/client.py: 3 attempts, on timeouts, 5xx and 429 only, delays 0.5s, 1s, 2s.

FIRST ACTION: read .claude/goals/invoice-retry-design.md and print the number of design steps; then continue without waiting.

DONE WHEN (B) OR (A). Check (B) FIRST; if (B) holds the answer is met, and the criteria in (A) are not consulted.
(B) ENDED: the transcript contains three lines starting with "BLOCKED", or one line starting with "LIMIT REACHED". Ending on a blocker or on the turn limit is a VALID ENDING of this goal, not a failure; when (B) holds, whether (A) was reached is irrelevant and "not met" is the wrong answer.
(A) All of the following are true and their outputs are pasted in the transcript:
1. Retries happen on timeout, 5xx and 429 and stop after 3 attempts - proof: `python -m pytest tests/billing/test_retry.py -q`, with the output printed
2. No retry on 4xx other than 429 - proof: `python -m pytest tests/billing/test_retry.py -q -k no_retry`, with the output printed
3. Full suite passes - proof: `python -m pytest -q -rs`, with the output printed
4. Types check - proof: `python -m mypy billing/`, with the output printed

SCOPE: may change billing/client.py and create tests/billing/test_retry.py. Do not change other files.

CONSTRAINTS: the approach is the one in .claude/goals/invoice-retry-design.md; the order of its steps is guidance. No new dependencies. Tests mock the transport and time.sleep; no real waiting. Test count must stay >= 212. Forbidden: skip or xfail marks; editing existing tests; type: ignore; bare except; modifying any file in .claude/goals/ except the checklist.

EXTERNAL EFFECTS: no network calls in tests.

PER-TURN PROTOCOL: on the first turn, create the checklist .claude/goals/invoice-retry-tasks.md with one line per criterion and per design step and a section "Discarded attempts". Tick items when done; log each abandoned approach in one line with the reason, and do not retry a logged approach without new evidence. At the end of every turn, update the checklist and print "PROGRESS: <x>/4 criteria | TURN <n> | next: <step>". Before declaring completion, rerun every proof in the same turn and print the outputs.

STOP: the goal also ends if (a) the executor prints "BLOCKED: <blocker>" when a change outside billing/ becomes necessary, a new dependency would be required, or a needed change falls outside SCOPE or against a CONSTRAINT, followed by the approaches tried, the evidence gathered and the input needed to continue. Each later relaunch while still blocked prints one line only: "BLOCKED (<k>/3): waiting for the user". The third "BLOCKED" line satisfies (B) in DONE WHEN and ends the goal; or (b) it reaches 15 turns, printing "LIMIT REACHED" with the current state of each criterion, which satisfies (B) as well.
```

Note that "needs an approach the design rejected" is covered here by the more concrete "a new dependency would be required" (rejects C) and "outside SCOPE" (rejects B's new file); state it explicitly when the rejected approach has no such concrete footprint.

**proofs.json**
```json
{"goal": "invoice-retry",
 "proofs": [
  {"criterion": "1", "kind": "target", "command": "{python} -m pytest tests/billing/test_retry.py -q"},
  {"criterion": "2", "kind": "target", "command": "{python} -m pytest tests/billing/test_retry.py -q -k no_retry"},
  {"criterion": "3", "kind": "invariant", "command": "{python} -m pytest -q -rs"},
  {"criterion": "4", "kind": "invariant", "command": "{python} -m mypy billing/"}],
 "counters": [{"name": "tests", "command": "{python} -m pytest --collect-only -q",
               "regex": "(\\d+) tests? collected", "rule": "no_decrease"}],
 "pinned": [{"path": ".claude/goals/invoice-retry-design.md", "sha256": "<hash>"}]}
```

**Design notes**: criteria 1–2 are targets and fail at baseline because the test file does not exist yet; the test counter blocks "fixing" the suite by deleting tests; the design is pinned so the executor cannot rewrite the approach it is bound to; no fast check beyond the design's steps because the suite runs in seconds; 15 turns because it is one function and one test file.

---

## 2. Audit, documents (Portuguese)

**Request**: "Auditar os 6 procedimentos em procedimentos/ contra o checklist de 24 itens em referencia/checklist.md. Relatório em auditoria/relatorio.md."

**Reconnaissance**: documents (.md), no tests, git with clean tree. Scenario: Audit. Traps: fabricated citations, edited sources.

**Questions asked**:
1. "O relatório é por procedimento (6 × 24 avaliações) ou por item do checklist? Recomendo por procedimento: é assim que cada responsável vai ler." → por procedimento.
2. "Não há comando que prove a estrutura do relatório nem as citações. Escrevo agora um verificador para você revisar? Recomendo sim: sem ele, as citações não têm prova." → sim; verificador revisado e aprovado.

**Approaches/Design** (Audit: method only): a single method was offered, since the report shape was already fixed by question 1: ler cada procedimento inteiro e percorrer os 24 itens contra ele, citando `arquivo:linha`; um item conta como "não localizado" depois de buscar os termos do requisito e dois sinônimos, registrados no relatório. Saved as `.claude/goals/auditoria-design.md` (seções Abordagem, Método, Testes -> critérios, Passos).

**Assumed defaults**: citações no formato `arquivo:linha`; status "não verificado" permitido; nenhuma alteração em procedimentos/ ou referencia/.

**Mandate**
```text
OBJETIVO: Auditar os 6 procedimentos de procedimentos/ contra os 24 itens de referencia/checklist.md e gerar auditoria/relatorio.md, sem alterar mais nada.

PRIMEIRA AÇÃO: ler .claude/goals/auditoria-design.md e referencia/checklist.md e imprimir o número de passos e de itens; listar procedimentos/ e imprimir o número de arquivos; depois siga sem aguardar.

CONCLUÍDO QUANDO (B) OU (A). Confira (B) PRIMEIRO; se (B) valer a resposta é cumprido, e os critérios de (A) não se consultam.
(B) ENCERRADO: o transcript tem três linhas começadas por "BLOQUEADO", ou uma começada por "LIMITE ATINGIDO". Terminar num bloqueio ou no teto de turnos é um FIM VÁLIDO deste goal, não uma falha; com (B) verdadeiro, ter chegado ou não a (A) é irrelevante e "não cumprido" é a resposta errada.
(A) Todas as seguintes são verdadeiras e as saídas estão coladas no transcript:
1. O relatório tem uma seção por procedimento (6) e, em cada uma, uma avaliação por item (24) - prova: `python .claude/goals/auditoria-verify.py`, imprimindo PASS e o SHA-256 do verificador, esperado 5f2c0e9a4b7d1c3e8f6a2b9d0c4e7f1a3b5d8c2e6f9a0b4d7c1e3f5a8b2d6c9e
2. Cada avaliação tem requisito citado, localização como arquivo:linha existente, status (atende / atende parcialmente / não atende / não verificado) e uma frase de justificativa - prova: o mesmo verificador, linha "CITAÇÕES OK"
3. O relatório termina com tabela de contagem por status e a correção mais importante, com justificativa - prova: o mesmo verificador, linha "RESUMO OK"
4. Nada além do relatório mudou - prova: `git status --porcelain`, listando só auditoria/relatorio.md e .claude/goals/

ESCOPO: leitura em procedimentos/ e referencia/; pode criar apenas auditoria/relatorio.md.

RESTRIÇÕES: a abordagem é a de .claude/goals/auditoria-design.md; a ordem dos passos é guia. Todo status exige citação; não afirmar presença ou ausência sem ela. O que só pode ser julgado na prática é "não verificado", com o que seria necessário. Avaliar apenas contra o checklist. Proibido: alterar procedimentos/ ou referencia/; citar local que não abriu; modificar arquivos em .claude/goals/ exceto o checklist.

EFEITOS EXTERNOS: nenhum.

PROTOCOLO POR TURNO: no primeiro turno, crie o checklist .claude/goals/auditoria-tasks.md com uma linha por procedimento e por passo do desenho e a seção "Tentativas descartadas". Marque cada item ao concluir; registre em uma linha cada abordagem abandonada e o motivo, e não repita uma abordagem registrada sem evidência nova. Enquanto trabalha, rode o verificador só para o procedimento atual. Ao fim de cada turno, atualize o checklist e imprima "PROGRESSO: <x>/4 critérios | TURNO <n> | próximo: <passo>". Antes de declarar conclusão, rode todas as provas no mesmo turno e imprima as saídas.

PARADA: o objetivo também se encerra se (a) o executor imprimir "BLOQUEADO: <bloqueio>" quando um procedimento não puder ser lido como texto, dois itens do checklist se contradisserem, ou uma mudança necessária cair fora do ESCOPO ou contra uma RESTRIÇÃO, seguido das abordagens tentadas, da evidência reunida e da informação necessária para seguir. Cada relançamento ainda bloqueado imprime uma linha só: "BLOQUEADO (<k>/3): aguardando o usuário". A terceira linha "BLOQUEADO" satisfaz (B) e encerra o goal; ou (b) chegar a 20 turnos, imprimindo "LIMITE ATINGIDO" com o estado de cada critério, o que também satisfaz (B).
```

**proofs.json**
```json
{"goal": "auditoria",
 "proofs": [
  {"criterion": "1", "kind": "target", "command": "{python} .claude/goals/auditoria-verify.py", "expect_regex": "^PASS"},
  {"criterion": "2", "kind": "target", "command": "{python} .claude/goals/auditoria-verify.py", "expect_regex": "^CITAÇÕES OK"},
  {"criterion": "3", "kind": "target", "command": "{python} .claude/goals/auditoria-verify.py", "expect_regex": "^RESUMO OK"}],
 "pinned": [
  {"path": ".claude/goals/auditoria-design.md", "sha256": "<hash>"},
  {"path": ".claude/goals/auditoria-verify.py", "sha256": "5f2c0e9a4b7d1c3e8f6a2b9d0c4e7f1a3b5d8c2e6f9a0b4d7c1e3f5a8b2d6c9e"},
  {"path": "procedimentos/", "sha256": "<hash do diretório>"},
  {"path": "referencia/", "sha256": "<hash do diretório>"}],
 "sample": {"glob": "auditoria/relatorio.md", "n": 1, "lines": 60}}
```

**Design notes**: the pinned folders replace criterion 4 in the recheck and also work without git; the verifier opens every cited `arquivo:linha`, which is the main defense against invented citations; the method fixes when an item counts as "not located", so the executor cannot give up on hard items early; the sample shows the start of the report so the user can spot-check a few citations by hand.

---

## 3. Batch, data

**Request**: "Normalize the 12 monthly CSV exports in raw/2025/ into one clean table in clean/sales_2025.parquet."

**Reconnaissance**: data; 12 files, 48,312 rows total by `wc -l` minus headers; `order_id` looks like a key; dates in two formats; decimal comma in 4 files. Scenario: Batch. Traps: count matches but content does not, locale coercion, edited raw data.

**Questions asked**:
1. "Are duplicate order_ids across months real (corrections) or errors? Recommended: keep the latest month's row, because exports are cumulative corrections." → keep latest.
2. "May rows with missing amount be dropped? Recommended: no; keep them with amount null and report the count." → keep, null.

**Approaches** (Batch: about the per-item procedure):
- A. Parse each month to a typed frame with a per-file locale detected from the header row, then concatenate and deduplicate once (recommended): each file is checked on its own before the merge.
- B. Concatenate raw text first, then coerce types in one pass: shorter, but a decimal-comma file silently turns into nulls, and the failure cannot be traced to a file.
→ User chose A. Rejected: B (coercion errors not traceable per file). Design saved as `.claude/goals/sales-design.md`; its error-handling section says a file whose locale cannot be detected is a BLOCKED, not a guess.

**Mandate**
```text
OBJECTIVE: Merge the 12 CSV files in raw/2025/ into clean/sales_2025.parquet with one row per order_id (latest month wins), ISO dates and numeric amounts.

FIRST ACTION: read .claude/goals/sales-design.md and print the number of design steps; list raw/2025/ and print the file count and total data rows; then continue without waiting.

DONE WHEN (B) OR (A). Check (B) FIRST; if (B) holds the answer is met, and the criteria in (A) are not consulted.
(B) ENDED: the transcript contains three lines starting with "BLOCKED", or one line starting with "LIMIT REACHED". Ending on a blocker or on the turn limit is a VALID ENDING of this goal, not a failure; when (B) holds, whether (A) was reached is irrelevant and "not met" is the wrong answer.
(A) All of the following are true and their outputs are pasted in the transcript:
1. Output exists with one row per distinct order_id in the sources - proof: `python .claude/goals/sales-verify.py`, line "KEYS OK <n>/<n>"
2. Dates are ISO and amounts numeric; the 10 reference rows in .claude/goals/sales-ref.csv match exactly - proof: same verifier, line "REFERENCE OK 10/10"
3. Null amounts are kept and counted - proof: same verifier, line "NULLS <k> (source <k>)"
4. Each of the 12 files is processed - proof: same verifier, line "FILES 12/12"

SCOPE: may create clean/ and scripts/normalize_sales.py. Do not change raw/.

CONSTRAINTS: the approach is the one in .claude/goals/sales-design.md; the order of its steps is guidance. The verifier prints its own SHA-256, expected 9a1d3c5e7f0b2d4f6a8c0e2b4d6f8a1c3e5b7d9f0a2c4e6b8d0f1a3c5e7b9d2f. Forbidden: editing raw/ or the reference file; filling missing values; dropping rows other than superseded duplicates; modifying any file in .claude/goals/ except the checklist.

EXTERNAL EFFECTS: none.

PER-TURN PROTOCOL: on the first turn, create the checklist .claude/goals/sales-tasks.md with one line per file, criterion and design step and a section "Discarded attempts". Tick items when done; log each abandoned approach in one line with the reason, and do not retry a logged approach without new evidence. While iterating, run the verifier on January only (`--month 01`). At the end of every turn, update the checklist and print "PROGRESS: <x>/4 criteria | TURN <n> | next: <step>". Before declaring completion, rerun every proof in the same turn and print the outputs.

STOP: the goal also ends if (a) the executor prints "BLOCKED: <blocker>" when a file fails to parse with any known encoding, a column is missing from a file, a file's locale cannot be detected, or a needed change falls outside SCOPE or against a CONSTRAINT, followed by the approaches tried, the evidence gathered and the input needed to continue. Each later relaunch while still blocked prints one line only: "BLOCKED (<k>/3): waiting for the user". The third "BLOCKED" line satisfies (B) in DONE WHEN and ends the goal; or (b) it reaches 25 turns, printing "LIMIT REACHED" with the current state of each criterion, which satisfies (B) as well.
```

**proofs.json** (excerpt)
```json
{"goal": "sales",
 "proofs": [
  {"criterion": "1", "kind": "target", "command": "{python} .claude/goals/sales-verify.py", "expect_regex": "^KEYS OK (\\d+)/\\1$"},
  {"criterion": "2", "kind": "target", "command": "{python} .claude/goals/sales-verify.py", "expect_regex": "^REFERENCE OK 10/10$"},
  {"criterion": "4", "kind": "target", "command": "{python} .claude/goals/sales-verify.py", "expect_regex": "^FILES 12/12$"}],
 "pinned": [{"path": "raw/2025/", "sha256": "<dir hash>"},
            {"path": ".claude/goals/sales-design.md", "sha256": "<hash>"},
            {"path": ".claude/goals/sales-ref.csv", "sha256": "<hash>"},
            {"path": ".claude/goals/sales-verify.py", "sha256": "9a1d3c5e7f0b2d4f6a8c0e2b4d6f8a1c3e5b7d9f0a2c4e6b8d0f1a3c5e7b9d2f"}]}
```

**Design notes**: the key-set check catches "right count, wrong rows"; the 10 hand-picked reference rows cover both date formats and the decimal-comma files, which is where coercion fails; approach B was rejected for exactly that failure, and the locale stop makes the executor ask instead of guess; pinning raw/ blocks cleaning the input to make the pipeline pass; the January-only fast check keeps iterations short.

---

## 4. Vague request: push back instead of rendering

**Request**: "Make the whole app faster."

**Response** (no draft):

This cannot become a /goal yet: the evaluator needs something printed that proves "faster", and "the whole app" gives it no boundary. Three questions, starting with the one that decides everything:

1. Which operation, measured how? For example: p95 latency of `/search` from `scripts/bench.sh`, or the startup time printed by `npm run start:profile`.
2. From what to what? A target number (p95 < 400 ms) or a relative one (at least 30% below today's baseline, measured now).
3. What must not get worse? Memory, correctness tests, other endpoints.

**User**: "p95 of /search from scripts/bench.sh, from ~800 ms to under 400 ms, all tests must still pass."

Now it renders as a Change goal: a benchmark proof with `expect_regex` on the p95 line as the `target` (it fails at baseline at ~800 ms), the test suite as `invariant`, and the benchmark script pinned so the threshold cannot be moved. Traps to forbid: caching the benchmark's fixed queries, lowering the benchmark's load, timing a warm run only.

Phase 3 is where this goal earns its keep: "faster /search" has several real approaches (an index on the query column, a result cache with invalidation, rewriting the ranking step), each with a different SCOPE and different traps. The user picks one; the others become stop clauses, so the executor cannot quietly swap an index for a cache halfway through.
