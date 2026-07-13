#!/usr/bin/env bash
# =============================================================================
# SpecLoop · gates.sh — backpressure ESTRATIFICADO (v2.0)
# "Pronto" é uma alegação; gates são a prova. Retorna 0 só se TUDO passar.
#
# Camadas (origem: retrospectiva §2.1 — 10-22 min/iteração era o gargalo):
#   L0  rápido    lint, typecheck, unit/contract + gates universais   (segundos)
#   L1  seletivo  L0 + E2E filtrado pelo escopo da história            (~1-3 min)
#   L2  release   L0 + E2E COMPLETO + smoke.sh (rebuild limpo + HTTP real)
#
# Uso:
#   ./loop/gates.sh                         # L1 sem filtro (compat.)
#   ./loop/gates.sh --level 0
#   ./loop/gates.sh --level 1 --scope "@equipe"
#   ./loop/gates.sh --level 2               # história S-RELEASE
# =============================================================================
set -uo pipefail
cd "$(dirname "$0")/.."

LEVEL=1; SCOPE=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --level) LEVEL="$2"; shift 2;;
    --scope) SCOPE="$2"; shift 2;;
    *) shift;;
  esac
done

FAILED=0
run_gate() {
  local name="$1"; shift
  echo "▶ gate: $name"
  if "$@"; then echo "  ✔ $name"; else echo "  ✖ $name FALHOU"; FAILED=1; fi
}

# ═══ L0 — SEMPRE: rápido e determinístico ═══════════════════════════════
if [[ -f package.json ]]; then
  jq -e '.scripts.lint'      package.json >/dev/null 2>&1 && run_gate "lint"      npm run --silent lint
  jq -e '.scripts.typecheck' package.json >/dev/null 2>&1 && run_gate "typecheck" npm run --silent typecheck
  # Convenção: "test:unit" = rápido (unit+contract); "test" = tudo. Adapte.
  if jq -e '.scripts["test:unit"]' package.json >/dev/null 2>&1; then
    run_gate "unit" npm run --silent test:unit -- --run
  elif jq -e '.scripts.test' package.json >/dev/null 2>&1 && [[ $LEVEL -eq 0 ]]; then
    run_gate "test" npm test --silent -- --run
  fi
fi
if [[ -f pyproject.toml || -f requirements.txt ]]; then
  command -v ruff   >/dev/null && run_gate "ruff" ruff check .
  # Convenção: marque E2E com @pytest.mark.e2e; L0 roda só o resto. Adapte.
  command -v pytest >/dev/null && run_gate "pytest-unit" pytest -q -m "not e2e"
fi

# ── Gates universais ─────────────────────────────────────────────────────
if git grep -nE "(api[_-]?key|secret|password)\s*=\s*['\"][A-Za-z0-9]{16,}" -- ':!loop/gates.sh' >/dev/null 2>&1; then
  echo "  ✖ possível segredo hardcoded (constitution §6)"; FAILED=1
fi

# mock-lint — o problema do oráculo (retro §2.3): MagicMock em alvo async
# só REFORÇA o bug (o await ausente do DELETE passou 'verde' assim).
ASYNC_TARGETS='(AsyncSession|AsyncClient|AsyncEngine|aiohttp|asyncpg)'
if git grep -nE "MagicMock\([^)]*\)" -- '*test*' '*spec*' 2>/dev/null | grep -E "$ASYNC_TARGETS" >/dev/null 2>&1; then
  echo "  ✖ mock-lint: MagicMock aplicado a alvo async — use AsyncMock (constitution §11)"
  git grep -nE "MagicMock" -- '*test*' | grep -E "$ASYNC_TARGETS" | head -3
  FAILED=1
fi

# lgpd-lint — privacy by design mecânico: a spec da feature ativa DECLARA
# a análise de dados pessoais (docs/LGPD.md). "nenhum" também é declaração.
SPEC_PATH=$(jq -r '.specPath // ""' loop/prd.json 2>/dev/null || echo "")
if [[ -n "$SPEC_PATH" && -f "$SPEC_PATH" ]]; then
  if ! grep -q "^## Dados pessoais (LGPD)" "$SPEC_PATH"; then
    echo "  ✖ lgpd-lint: $SPEC_PATH sem a seção '## Dados pessoais (LGPD)' (constitution §13)"
    FAILED=1
  fi
fi
# heurística de PII em log (warning, não bloqueio — revisão é do Verifier)
if git grep -inE "(logger\.|logging\.|console\.log|print\().*(cpf|rg\b|senha|password|e-?mail|telefone)" -- 'src/*' 'apps/*' 2>/dev/null | head -3 | grep -q .; then
  echo "  ⚠ lgpd: possível dado pessoal em log — confirme mascaramento (Verifier audita)"
fi

# adr-lint
if ls docs/adr/[0-9][0-9][0-9][0-9]-*.md >/dev/null 2>&1; then
  for adr in docs/adr/[0-9][0-9][0-9][0-9]-*.md; do
    if ! grep -qE "^Status: (proposto|aceito|descontinuado|substituído por ADR-[0-9]{4})" "$adr"; then
      echo "  ✖ adr-lint: $adr sem Status válido"; FAILED=1
    fi
  done
  PROPOSED=$(grep -l "^Status: proposto" docs/adr/[0-9][0-9][0-9][0-9]-*.md 2>/dev/null | wc -l)
  [[ $PROPOSED -gt 0 ]] && echo "  ⚠ adr-lint: $PROPOSED ADR(s) 'proposto' aguardando decisão humana"
fi

# ═══ L1 — E2E SELETIVO (escopo da história) ═════════════════════════════
if [[ $LEVEL -ge 1 ]]; then
  if [[ -f package.json ]] && jq -e '.scripts["test:e2e"]' package.json >/dev/null 2>&1; then
    if [[ -n "$SCOPE" ]]; then
      run_gate "e2e($SCOPE)" npm run --silent test:e2e -- --grep "$SCOPE"
    elif [[ $LEVEL -eq 1 ]]; then
      echo "  ⚠ L1 sem --scope: rodando E2E completo (marque histórias com e2eScope no prd.json)"
      run_gate "e2e(full)" npm run --silent test:e2e
    fi
  fi
  if [[ -f pyproject.toml || -f requirements.txt ]] && command -v pytest >/dev/null; then
    if [[ -n "$SCOPE" ]]; then
      run_gate "pytest-e2e($SCOPE)" pytest -q -m e2e -k "$SCOPE"
    fi
  fi
fi

# ═══ L2 — RELEASE: E2E completo + smoke real ════════════════════════════
if [[ $LEVEL -ge 2 ]]; then
  if [[ -f package.json ]] && jq -e '.scripts["test:e2e"]' package.json >/dev/null 2>&1; then
    run_gate "e2e(FULL)" npm run --silent test:e2e
  fi
  if [[ -f pyproject.toml || -f requirements.txt ]] && command -v pytest >/dev/null; then
    run_gate "pytest-e2e(FULL)" pytest -q -m e2e
  fi
  run_gate "smoke(rebuild+HTTP real)" ./loop/smoke.sh
fi

if [[ $FAILED -eq 0 ]]; then
  echo "══ GATES L$LEVEL: TODOS VERDES ══"; exit 0
else
  echo "══ GATES L$LEVEL: FALHA — NÃO está pronto ══"; exit 1
fi
