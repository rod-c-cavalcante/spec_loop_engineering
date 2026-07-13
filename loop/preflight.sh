#!/usr/bin/env bash
# =============================================================================
# SpecLoop · preflight.sh — pré-condições mecânicas antes de qualquer loop
# Origem: retrospectiva forja_platform §2.2 (colisão de agentes na feature 006;
# feature.json obsoleto sobrescrevendo plan.md da 008) e §2.4 (porta ocupada).
# Lição-mestra: lição determinística vira código, não texto.
#
# Uso:  ./loop/preflight.sh            (ralph.sh chama automaticamente)
# Overrides conscientes (use sabendo o porquê):
#   ALLOW_DIRTY=1        pula checagem de working tree limpo
#   OVERRIDE_MERGED=1    permite escrever em specs/ de feature já mesclada
#   PRD_LINT_ACK=1       reconhece warnings de histórias "gordas"
#   CHECK_PORTS="5173 8000"  portas do host a checar (vazio = pula)
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")/.."
PRD="loop/prd.json"
LOCK="state/loop.lock"
FAIL=0

echo "── preflight ──"

# 1) LOCK DE AGENTE — dois agentes no mesmo working tree é impossibilidade, não regra
if [[ -f "$LOCK" ]]; then
  LOCK_PID=$(cut -d: -f1 "$LOCK" 2>/dev/null || echo "")
  if [[ -n "$LOCK_PID" ]] && kill -0 "$LOCK_PID" 2>/dev/null; then
    echo "✖ preflight: outro loop ATIVO neste working tree (PID $LOCK_PID, ver $LOCK)."
    echo "  Para paralelismo, use git worktree (ARCHITECTURE.md §5). Nunca o mesmo tree."
    exit 10
  fi
  echo "  ⚠ lock obsoleto (processo morto) — removendo."
  rm -f "$LOCK"
fi

# 2) WORKING TREE LIMPO — commit do loop sobrescrevendo trabalho alheio foi
#    exatamente a perda real da feature 006.
if [[ -z "${ALLOW_DIRTY:-}" ]] && [[ -n "$(git status --porcelain 2>/dev/null)" ]]; then
  echo "✖ preflight: working tree sujo. Commite, stashe ou descarte antes do loop."
  git status --short | head -10
  echo "  (override consciente: ALLOW_DIRTY=1)"
  FAIL=1
fi

# 3) CONSISTÊNCIA TRIPLA — feature.json ↔ branch git ↔ prd.json
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "?")
PRD_FEATURE=$(jq -r '.feature // "?"' "$PRD" 2>/dev/null || echo "?")
PRD_BRANCH=$(jq -r '.branchName // ""' "$PRD" 2>/dev/null || echo "")
if [[ -f .specify/feature.json ]]; then
  SPECIFY_FEATURE=$(jq -r '.feature // .FEATURE // "?"' .specify/feature.json 2>/dev/null || echo "?")
  if [[ "$SPECIFY_FEATURE" != "?" && "$SPECIFY_FEATURE" != "$PRD_FEATURE" ]]; then
    echo "✖ preflight: .specify/feature.json aponta '$SPECIFY_FEATURE' mas prd.json aponta '$PRD_FEATURE'."
    echo "  Foi EXATAMENTE assim que um template sobrescreveu o plan.md de feature mesclada."
    FAIL=1
  fi
fi
if [[ -n "$PRD_BRANCH" && "$BRANCH" != "$PRD_BRANCH" ]]; then
  echo "✖ preflight: branch atual '$BRANCH' ≠ branchName do prd.json '$PRD_BRANCH'."
  FAIL=1
fi

# 4) MERGED-GUARD — specs de feature já mesclada em main são artefato histórico
MAIN=$(git rev-parse --verify main >/dev/null 2>&1 && echo main || echo master)
if [[ -z "${OVERRIDE_MERGED:-}" && -n "$PRD_BRANCH" ]] \
   && git rev-parse --verify "$PRD_BRANCH" >/dev/null 2>&1 \
   && git branch --merged "$MAIN" 2>/dev/null | grep -qx "[* ]*$PRD_BRANCH"; then
  echo "✖ preflight: a branch '$PRD_BRANCH' JÁ está mesclada em $MAIN."
  echo "  Escrever em specs/$PRD_FEATURE agora corromperia artefato histórico."
  echo "  (override consciente: OVERRIDE_MERGED=1)"
  FAIL=1
fi

# 5) PORTAS DO HOST — 1h de debug de CSS por processo órfão vira 1 mensagem
for p in ${CHECK_PORTS:-}; do
  if (exec 3<>"/dev/tcp/127.0.0.1/$p") 2>/dev/null; then
    exec 3>&- 3<&- || true
    echo "  ⚠ porta $p OCUPADA no host — se não for o compose deste projeto,"
    echo "    há processo órfão mascarando seu ambiente (mate-o antes de debugar)."
  fi
done

# 6) PRD-LINT — histórias "gordas" (backend E frontend juntos) = raio de falha grande
API_RX='(endpoint|/api/|POST |GET |PATCH |DELETE |rota)'
FE_RX='(página|pagina|page|componente|component|tela|frontend|\.tsx|\.vue)'
FAT=$(jq -r '.userStories[] | select(.passes == false) | select(.id != "S-RELEASE") | "\(.id)\t\(.acceptance)"' "$PRD" 2>/dev/null \
  | grep -iE "$API_RX" | grep -icE "$FE_RX" || true)
if [[ "${FAT:-0}" -gt 0 && -z "${PRD_LINT_ACK:-}" ]]; then
  echo "  ⚠ prd-lint: $FAT história(s) misturando backend E frontend no mesmo acceptance."
  echo "    Fatia fina (1 endpoint OU 1 página) falha menos e corrige mais barato."
  echo "    Se for intencional, siga com PRD_LINT_ACK=1."
fi

if [[ $FAIL -ne 0 ]]; then
  echo "══ PREFLIGHT: BLOQUEADO ══"
  exit 11
fi
echo "══ PREFLIGHT: OK (branch=$BRANCH, feature=$PRD_FEATURE) ══"
