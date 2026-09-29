---
description: Portuguese read-only audit, full flow with every decision delegated to the skill's recommended answers. Same gates as pipeline-change-en, plus Portuguese labels and the audited folders pinned by hash. Conformance case; run with --ablation none.
tags: [pipeline, pt]
runs: 1
max_turns: 80
timeout_seconds: 2400
allowed_tools: [Read, Glob, Grep, Skill, Agent, TodoWrite, Bash, Write, Edit]
expected_outcome: Design and proofs files in .claude/goals/, probably a verifier there too; BASELINE OK with procedimentos/ and referencia/ pinned; RESULT OK; a Portuguese mandate with CONCLUÍDO QUANDO (B) OU (A), (B) ENCERRADO and PARADA; a recheck command with --expect-sha. Nothing written in procedimentos/, referencia/ or auditoria/.
---

/goal-composer:goal-composer auditar os 3 procedimentos de procedimentos/ contra os 5 itens de referencia/checklist.md e gerar o relatório em auditoria/relatorio.md.

Não vou poder responder perguntas nesta sessão. Em cada pergunta adote a sua resposta recomendada, aceite cada seção do desenho e o resumo antes da redação como você os propuser, e siga pelo red-team, pelo baseline, pela validação e pela entrega. Liste os padrões que adotou.
