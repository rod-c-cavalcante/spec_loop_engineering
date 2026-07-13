#!/usr/bin/env bash
# =============================================================================
# SpecLoop · ralph.sh v2.0 — loop com preflight, lock, autonomia graduada
# por risco e gates estratificados.
#
# Uso:
#   ./loop/ralph.sh                # roda o loop
#   ./loop/ralph.sh --dry-run      # mostra o plano sem chamar o agente
#
# Variáveis:
#   MAX_ITERATIONS=10      teto absoluto de voltas
#   MAX_SAME_FAILURE=3     falhas idênticas seguidas antes de parar
#   ITERATION_TIMEOUT=1200 segundos por iteração
#   AGENT_CMD="claude -p"  comando do agente (Claude Code headless)
#   SKIP_PREFLIGHT=1       pula o preflight (não recomendado)
#   NO_CHECKPOINT=1        não para após história risk=high (não recomendado)
#
# Autonomia graduada (campo "risk" por história no prd.json):
#   high   → executa a história e PARA para checkpoint humano (auth,
#            permissões, deleção, pagamento — onde os bugs graves moram)
#   normal → encadeia histórias normalmente (default)
#   low    → encadeia; Verifier dispensável (polish, docs)
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")/.."

MAX_ITERATIONS="${MAX_ITERATIONS:-10}"
MAX_SAME_FAILURE="${MAX_SAME_FAILURE:-3}"
ITERATION_TIMEOUT="${ITERATION_TIMEOUT:-1200}"
AGENT_CMD="${AGENT_CMD:-claude -p --dangerously-skip-permissions --output-format text}"
PRD="loop/prd.json"
PROGRESS="state/progress.md"
METRICS="state/metrics.csv"
LOCK="state/loop.lock"
DRY_RUN=0
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=1

command -v jq >/dev/null || { echo "ERRO: jq não instalado"; exit 1; }
[[ -f "$PRD" ]] || { echo "ERRO: $PRD não encontrado"; exit 1; }
mkdir -p state
[[ -f "$METRICS" ]] || echo "timestamp,iteration,story,risk,level,duration_s,gates,result" > "$METRICS"
[[ -f "$PROGRESS" ]] || echo "# Progress log do loop" > "$PROGRESS"

pending()     { jq -r '[.userStories[] | select(.passes == false)] | length' "$PRD"; }
next_story()  { jq -r '[.userStories[] | select(.passes == false)][0].id // "none"' "$PRD"; }
story_field() { jq -r --arg id "$1" --arg f "$2" '.userStories[] | select(.id==$id) | .[$f] // ""' "$PRD"; }

echo "══════════════════════════════════════════════════"
echo " SpecLoop v2 · $(jq -r '.feature' "$PRD")"
echo " Pendentes: $(pending) | Teto: $MAX_ITERATIONS iterações"
echo "══════════════════════════════════════════════════"

if [[ $DRY_RUN -eq 1 ]]; then
  echo "[dry-run] Ordem de execução (id · risk · e2eScope):"
  jq -r '.userStories[] | select(.passes == false) | "  → \(.id) · \(.risk // "normal") · \(.e2eScope // "-") — \(.title)"' "$PRD"
  exit 0
fi

# ── PREFLIGHT + LOCK ─────────────────────────────────────────────────────
[[ -z "${SKIP_PREFLIGHT:-}" ]] && ./loop/preflight.sh
echo "$$:$(date -Is)" > "$LOCK"
trap 'rm -f "$LOCK"' EXIT INT TERM

LAST_FAILURE=""
SAME_FAILURE_COUNT=0

for (( i=1; i<=MAX_ITERATIONS; i++ )); do
  [[ $(pending) -eq 0 ]] && { echo "✔ Backlog completo antes da iteração $i."; break; }
  STORY=$(next_story)
  RISK=$(story_field "$STORY" "risk"); RISK="${RISK:-normal}"
  SCOPE=$(story_field "$STORY" "e2eScope")

  # Nível de gate: S-RELEASE = L2 (E2E completo + smoke); demais = L1 seletivo
  if [[ "$STORY" == "S-RELEASE" ]]; then LEVEL=2; else LEVEL=1; fi

  echo ""
  echo "── Iteração $i/$MAX_ITERATIONS · $STORY · risk=$RISK · gate=L$LEVEL${SCOPE:+ · scope=$SCOPE} ──"
  START=$(date +%s)

  # 1) BUILDER — contexto limpo por iteração
  set +e
  OUTPUT=$(timeout "$ITERATION_TIMEOUT" bash -c "cat loop/PROMPT_BUILD.md | $AGENT_CMD" 2>&1)
  AGENT_RC=$?
  set -e
  [[ $AGENT_RC -eq 124 ]] && echo "⚠ Iteração excedeu ${ITERATION_TIMEOUT}s (timeout)."

  # 2) GATES — estratificados: a prova no nível certo
  set +e
  if [[ -n "$SCOPE" ]]; then
    ./loop/gates.sh --level "$LEVEL" --scope "$SCOPE"
  else
    ./loop/gates.sh --level "$LEVEL"
  fi
  GATES_RC=$?
  set -e

  DURATION=$(( $(date +%s) - START ))
  GATES_LABEL=$([[ $GATES_RC -eq 0 ]] && echo "pass" || echo "fail")

  # 3) CIRCUIT BREAKER — mesma falha repetida = parar e chamar humano
  if [[ $GATES_RC -ne 0 ]]; then
    FAILURE_SIG=$(./loop/gates.sh --level "$LEVEL" ${SCOPE:+--scope "$SCOPE"} 2>&1 | tail -3 | md5sum | cut -d' ' -f1 || true)
    if [[ "$FAILURE_SIG" == "$LAST_FAILURE" ]]; then
      SAME_FAILURE_COUNT=$((SAME_FAILURE_COUNT+1))
    else
      SAME_FAILURE_COUNT=1; LAST_FAILURE="$FAILURE_SIG"
    fi
    if [[ $SAME_FAILURE_COUNT -ge $MAX_SAME_FAILURE ]]; then
      echo "$(date -Is),$i,$STORY,$RISK,L$LEVEL,$DURATION,$GATES_LABEL,circuit_breaker" >> "$METRICS"
      echo "✖ CIRCUIT BREAKER: mesma falha ${MAX_SAME_FAILURE}x. Intervenha:"
      echo "  gates: ./loop/gates.sh --level $LEVEL ${SCOPE:+--scope $SCOPE} · log: tail -20 $PROGRESS"
      echo "  Recuperação correta: ler as asserções que falharam e corrigir a MESMA"
      echo "  história cirurgicamente — não descartar trabalho, não pular história."
      exit 2
    fi
  else
    SAME_FAILURE_COUNT=0; LAST_FAILURE=""
  fi

  # 4) TELEMETRIA
  RESULT="in_progress"
  grep -q "<promise>COMPLETE</promise>" <<<"$OUTPUT" && RESULT="complete_claimed"
  grep -q "<promise>BLOCKED" <<<"$OUTPUT" && RESULT="blocked"
  echo "$(date -Is),$i,$STORY,$RISK,L$LEVEL,$DURATION,$GATES_LABEL,$RESULT" >> "$METRICS"
  echo "   gates=$GATES_LABEL · ${DURATION}s · pendentes=$(pending)"

  # 5) BLOQUEIO — o agente pediu humano
  if [[ "$RESULT" == "blocked" ]]; then
    echo "⚠ Agente reportou bloqueio:"
    grep -o "<promise>BLOCKED[^<]*" <<<"$OUTPUT" || true
    exit 3
  fi

  # 6) CHECKPOINT DE RISCO — história high concluída para o loop p/ revisão
  STORY_DONE=$(jq -r --arg id "$STORY" '.userStories[] | select(.id==$id) | .passes' "$PRD")
  if [[ "$RISK" == "high" && "$STORY_DONE" == "true" && $GATES_RC -eq 0 && -z "${NO_CHECKPOINT:-}" ]]; then
    echo ""
    echo "⏸ CHECKPOINT: história risk=high '$STORY' concluída com gates verdes."
    echo "  Auth/permissões/deleção concentram os bugs graves — revise ANTES de seguir:"
    echo "    git show HEAD   ·   /verify (auditoria do Verifier)"
    echo "  Para continuar o backlog: ./loop/ralph.sh"
    exit 5
  fi

  # 7) CONDIÇÃO DUPLA DE SAÍDA — promise E gates E backlog zerado
  if [[ "$RESULT" == "complete_claimed" && $GATES_RC -eq 0 && $(pending) -eq 0 ]]; then
    echo ""
    echo "✔✔ COMPLETO: promise + gates verdes + backlog zerado."
    echo "   Revise: git log --oneline · cat $PROGRESS"
    exit 0
  fi
done

if [[ $(pending) -gt 0 ]]; then
  echo ""
  echo "⏸ Teto de $MAX_ITERATIONS iterações com $(pending) pendente(s)."
  exit 1
fi
echo "✔ Loop encerrado com backlog completo."
