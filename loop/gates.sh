#!/usr/bin/env bash
# =============================================================================
# SpecLoop · gates.sh — backpressure determinístico
# "Pronto" é uma alegação; gates são a prova. Retorna 0 só se TUDO passar.
# Auto-detecta a stack; adicione/edite gates para o seu projeto.
# =============================================================================
set -uo pipefail
cd "$(dirname "$0")/.."

FAILED=0
run_gate() {
  local name="$1"; shift
  echo "▶ gate: $name"
  if "$@"; then
    echo "  ✔ $name"
  else
    echo "  ✖ $name FALHOU"
    FAILED=1
  fi
}

# ── Node.js ──────────────────────────────────────────────────────────────
if [[ -f package.json ]]; then
  if jq -e '.scripts.lint' package.json >/dev/null 2>&1; then
    run_gate "lint" npm run --silent lint
  fi
  if jq -e '.scripts.typecheck' package.json >/dev/null 2>&1; then
    run_gate "typecheck" npm run --silent typecheck
  fi
  if jq -e '.scripts.test' package.json >/dev/null 2>&1; then
    run_gate "test" npm test --silent -- --run
  fi
  if jq -e '.scripts.build' package.json >/dev/null 2>&1; then
    run_gate "build" npm run --silent build
  fi
fi

# ── Python ───────────────────────────────────────────────────────────────
if [[ -f pyproject.toml || -f requirements.txt ]]; then
  command -v ruff   >/dev/null && run_gate "ruff"   ruff check .
  command -v pytest >/dev/null && run_gate "pytest" pytest -q
fi

# ── Gates universais ─────────────────────────────────────────────────────
# Segredos óbvios em staged/working tree (barato e salva vidas)
if git grep -nE "(api[_-]?key|secret|password)\s*=\s*['\"][A-Za-z0-9]{16,}" -- ':!loop/gates.sh' >/dev/null 2>&1; then
  echo "  ✖ possível segredo hardcoded encontrado (constitution §6)"
  FAILED=1
fi

# ── ADR lint ─────────────────────────────────────────────────────────────
# Todo ADR precisa de Status válido; ADRs propostos não bloqueiam, mas avisam.
if ls docs/adr/[0-9][0-9][0-9][0-9]-*.md >/dev/null 2>&1; then
  for adr in docs/adr/[0-9][0-9][0-9][0-9]-*.md; do
    if ! grep -qE "^Status: (proposto|aceito|descontinuado|substituído por ADR-[0-9]{4})" "$adr"; then
      echo "  ✖ adr-lint: $adr sem Status válido (proposto|aceito|descontinuado|substituído por ADR-NNNN)"
      FAILED=1
    fi
  done
  PROPOSED=$(grep -l "^Status: proposto" docs/adr/[0-9][0-9][0-9][0-9]-*.md 2>/dev/null | wc -l)
  [[ $PROPOSED -gt 0 ]] && echo "  ⚠ adr-lint: $PROPOSED ADR(s) com status 'proposto' aguardando decisão humana"
fi

# ── Resultado ────────────────────────────────────────────────────────────
if [[ $FAILED -eq 0 ]]; then
  echo "══ GATES: TODOS VERDES ══"
  exit 0
else
  echo "══ GATES: FALHA — a história NÃO está pronta ══"
  exit 1
fi
