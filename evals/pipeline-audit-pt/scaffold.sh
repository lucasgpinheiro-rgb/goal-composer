#!/usr/bin/env bash
# Three short work procedures and a five-item checklist, in Portuguese. Read-only audit fixture.
set -euo pipefail
mkdir -p procedimentos referencia
cat > referencia/checklist.md <<'MD'
# Checklist de procedimentos operacionais

1. Define objetivo e campo de aplicação.
2. Lista os riscos da atividade.
3. Indica os EPIs obrigatórios.
4. Descreve a sequência de execução em passos numerados.
5. Nomeia o responsável pela liberação da atividade.
MD
cat > procedimentos/trabalho-em-altura.md <<'MD'
# PO-01 Trabalho em altura

Objetivo: estabelecer regras para atividades acima de 2 m do nível inferior, em todas as unidades.

Riscos: queda de pessoas, queda de materiais, choque elétrico em redes próximas.

EPIs: cinto tipo paraquedista com talabarte duplo, capacete com jugular, calçado de segurança.

Execução:
1. Emitir a permissão de trabalho.
2. Inspecionar o cinto e os pontos de ancoragem.
3. Isolar a área abaixo da atividade.
4. Executar o serviço mantendo sempre um talabarte conectado.

Liberação: supervisor de manutenção.
MD
cat > procedimentos/bloqueio-e-etiquetagem.md <<'MD'
# PO-02 Bloqueio e etiquetagem

Objetivo: impedir a energização acidental de máquinas durante manutenção.

Riscos: choque elétrico, prensamento, liberação de energia residual.

Execução:
1. Comunicar os operadores afetados.
2. Desligar a máquina pelo comando normal.
3. Aplicar cadeado e etiqueta em cada fonte de energia.
4. Testar a ausência de energia antes de iniciar.
MD
cat > procedimentos/espaco-confinado.md <<'MD'
# PO-03 Espaço confinado

Objetivo: orientar a entrada em tanques e galerias.

EPIs: detector multigás, máscara autônoma quando indicado, cinto com linha de resgate.

A entrada ocorre após medição da atmosfera, com vigia do lado de fora durante todo o trabalho.

Liberação: supervisor de entrada.
MD
git init -q && git add -A && git -c user.name=eval -c user.email=eval@example.com commit -qm "procedimentos"
