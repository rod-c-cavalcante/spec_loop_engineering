#!/usr/bin/env bash
# =============================================================================
# SpecLoop · setup-branch-protection.sh — branch protection COMO CÓDIGO
# (specs/002-fortalecimento-v4, RF-11)
#
# Origem: PR mesclado 90s depois de aberto, com o gate L2 ainda rodando
# (RETROSPECTIVA.md §3.3, ação 4). A regra "não mesclar antes do L2 fechar"
# sustentou quando seguida à risca (RETROSPECTIVA-005-006.md §2.4) — mas até
# agora só existia como convenção documentada (docs/DEVOPS.md: "recomendada").
# Este script é a versão executável: exige os checks `gates-l0` e `gates-l2`
# (nomes dos jobs em .github/workflows/ci.yml) antes de permitir merge em
# main/master.
#
# Não roda em nenhum gate automaticamente — depende de `gh` CLI autenticado
# com permissão de admin no repositório remoto (fora do que o loop controla
# sozinho, ver plan.md de specs/002, seção Riscos). Rode manualmente 1x por
# repositório (ou de novo se branch protection for resetada).
#
# Uso:
#   ./scripts/setup-branch-protection.sh --dry-run   # mostra o que faria, não toca o remoto
#   ./scripts/setup-branch-protection.sh              # aplica de verdade (exige confirmação)
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")/.."

DRY_RUN=0
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=1

command -v gh >/dev/null || { echo "ERRO: gh CLI não instalado (https://cli.github.com)"; exit 1; }

MAIN=$(git rev-parse --verify main >/dev/null 2>&1 && echo main || echo master)
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "")
if [[ -z "$REPO" ]]; then
  echo "ERRO: não foi possível identificar o repositório remoto (gh repo view falhou)."
  echo "  Confirme 'gh auth status' e que o remote 'origin' aponta para o GitHub."
  exit 1
fi

PAYLOAD=$(cat <<JSON
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["gates-l0", "gates-l2"]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": null,
  "restrictions": null
}
JSON
)

echo "── setup-branch-protection ──"
echo "Repositório : $REPO"
echo "Branch      : $MAIN"
echo "Checks obrigatórios: gates-l0, gates-l2 (nomes dos jobs em .github/workflows/ci.yml)"
echo ""

if [[ $DRY_RUN -eq 1 ]]; then
  echo "[dry-run] Chamada que seria feita (nada foi alterado no remoto):"
  echo "  gh api -X PUT repos/$REPO/branches/$MAIN/protection --input -"
  echo "$PAYLOAD" | sed 's/^/    /'
  exit 0
fi

echo "Isto vai EXIGIR gates-l0 + gates-l2 verdes antes de qualquer merge em '$MAIN'."
echo "$PAYLOAD" | gh api -X PUT "repos/$REPO/branches/$MAIN/protection" --input -
echo "══ branch protection aplicada em $REPO:$MAIN ══"
