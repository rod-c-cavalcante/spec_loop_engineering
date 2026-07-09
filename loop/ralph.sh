#!/usr/bin/env bash
# =============================================================================
# SpecLoop · ralph.sh — o loop que executa o backlog até completar
# Padrão Ralph endurecido: contexto limpo por iteração, gates obrigatórios,
# circuit breaker, timeout e telemetria.
#
# Uso:
#   ./loop/ralph.sh                # roda o loop
#   ./loop/ralph.sh --dry-run      # mostra o plano sem chamar o agente
#
# Variáveis (sobreponha via ambiente):
#   MAX_ITERATIONS=10      teto absoluto de voltas
#   MAX_SAME_FAILURE=3     falhas idênticas seguidas antes de parar
#   ITERATION_TIMEOUT=1200 segundos por iteração (20 min)
#   AGENT_CMD="claude -p"  comando do agente (Claude Code headless)
#   SKIP_VERIFIER=0        1 = pula a auditoria agêntica (só gates)
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")/.."   # sempre opera na raiz do projeto

MAX_ITERATIONS="${MAX_ITERATIONS:-10}"
MAX_SAME_FAILURE="${MAX_SAME_FAILURE:-3}"
ITERATION_TIMEOUT="${ITERATION_TIMEOUT:-1200}"
AGENT_CMD="${AGENT_CMD:-claude -p --dangerously-skip-permissions --output-format text}"
SKIP_VERIFIER="${SKIP_VERIFIER:-0}"
PRD="loop/prd.json"
PROGRESS="state/progress.md"
METRICS="state/metrics.csv"
DRY_RUN=0
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=1

command -v jq >/dev/null || { echo "ERRO: jq não instalado"; exit 1; }
[[ -f "$PRD" ]] || { echo "ERRO: $PRD não encontrado"; exit 1; }
mkdir -p state
[[ -f "$METRICS" ]] || echo "timestamp,iteration,story,duration_s,gates,result" > "$METRICS"
[[ -f "$PROGRESS" ]] || echo "# Progress log do loop" > "$PROGRESS"

pending() { jq -r '[.userStories[] | select(.passes == false)] | length' "$PRD"; }
next_story() { jq -r '[.userStories[] | select(.passes == false)][0].id // "none"' "$PRD"; }

echo "══════════════════════════════════════════════════"
echo " SpecLoop · $(jq -r '.feature' "$PRD")"
echo " Histórias pendentes: $(pending) | Teto: $MAX_ITERATIONS iterações"
echo "══════════════════════════════════════════════════"

if [[ $DRY_RUN -eq 1 ]]; then
  echo "[dry-run] Ordem de execução:"
  jq -r '.userStories[] | select(.passes == false) | "  → \(.id): \(.title)"' "$PRD"
  echo "[dry-run] Comando do agente: $AGENT_CMD < loop/PROMPT_BUILD.md"
  exit 0
fi

LAST_FAILURE=""
SAME_FAILURE_COUNT=0

for (( i=1; i<=MAX_ITERATIONS; i++ )); do
  [[ $(pending) -eq 0 ]] && { echo "✔ Backlog completo antes da iteração $i."; break; }
  STORY=$(next_story)
  echo ""
  echo "── Iteração $i/$MAX_ITERATIONS · história $STORY ──"
  START=$(date +%s)

  # 1) BUILDER — contexto limpo: o prompt é injetado do zero a cada volta
  set +e
  OUTPUT=$(timeout "$ITERATION_TIMEOUT" bash -c "cat loop/PROMPT_BUILD.md | $AGENT_CMD" 2>&1)
  AGENT_RC=$?
  set -e
  [[ $AGENT_RC -eq 124 ]] && echo "⚠ Iteração excedeu ${ITERATION_TIMEOUT}s (timeout)."

  # 2) GATES — a prova, não a alegação
  set +e
  ./loop/gates.sh
  GATES_RC=$?
  set -e

  DURATION=$(( $(date +%s) - START ))
  GATES_LABEL=$([[ $GATES_RC -eq 0 ]] && echo "pass" || echo "fail")

  # 3) CIRCUIT BREAKER — mesma falha repetida = parar e chamar humano
  if [[ $GATES_RC -ne 0 ]]; then
    FAILURE_SIG=$(./loop/gates.sh 2>&1 | tail -3 | md5sum | cut -d' ' -f1 || true)
    if [[ "$FAILURE_SIG" == "$LAST_FAILURE" ]]; then
      SAME_FAILURE_COUNT=$((SAME_FAILURE_COUNT+1))
    else
      SAME_FAILURE_COUNT=1; LAST_FAILURE="$FAILURE_SIG"
    fi
    if [[ $SAME_FAILURE_COUNT -ge $MAX_SAME_FAILURE ]]; then
      echo "timestamp=$(date -Is),iteration=$i,story=$STORY" >> state/circuit-breaker.log
      echo "$(date -Is),$i,$STORY,$DURATION,$GATES_LABEL,circuit_breaker" >> "$METRICS"
      echo "✖ CIRCUIT BREAKER: mesma falha ${MAX_SAME_FAILURE}x seguidas."
      echo "  Repetir a abordagem que falha é desperdício. Intervenha:"
      echo "  1. Leia a falha:   ./loop/gates.sh"
      echo "  2. Leia o log:     tail -20 $PROGRESS"
      echo "  3. Diagnóstico:    gap Spec→Impl (melhore gates/verifier) ou"
      echo "                     Intent→Spec (clarifique a spec) — registre."
      exit 2
    fi
  else
    SAME_FAILURE_COUNT=0; LAST_FAILURE=""
  fi

  # 4) TELEMETRIA
  RESULT="in_progress"
  grep -q "<promise>COMPLETE</promise>" <<<"$OUTPUT" && RESULT="complete_claimed"
  grep -q "<promise>BLOCKED" <<<"$OUTPUT" && RESULT="blocked"
  echo "$(date -Is),$i,$STORY,$DURATION,$GATES_LABEL,$RESULT" >> "$METRICS"
  echo "   gates=$GATES_LABEL · ${DURATION}s · pendentes=$(pending)"

  # 5) BLOQUEIO — o agente pediu humano
  if [[ "$RESULT" == "blocked" ]]; then
    echo "⚠ Agente reportou bloqueio:"
    grep -o "<promise>BLOCKED[^<]*" <<<"$OUTPUT" || true
    exit 3
  fi

  # 6) CONDIÇÃO DUPLA DE SAÍDA — promise E gates E backlog zerado
  if [[ "$RESULT" == "complete_claimed" && $GATES_RC -eq 0 && $(pending) -eq 0 ]]; then
    echo ""
    echo "✔✔ COMPLETO: promise emitida + gates verdes + backlog zerado."
    echo "   Revise: git log --oneline · cat $PROGRESS"
    exit 0
  fi
done

if [[ $(pending) -gt 0 ]]; then
  echo ""
  echo "⏸ Teto de $MAX_ITERATIONS iterações atingido com $(pending) história(s) pendente(s)."
  echo "  Revise o progresso e rode de novo, ou aumente MAX_ITERATIONS conscientemente."
  exit 1
fi
echo "✔ Loop encerrado com backlog completo."
