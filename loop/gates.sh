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
# loop-tests — mutar.py/verificar.py (specs/002-fortalecimento-v4) têm testes
# próprios em loop/tests/; roda sempre, independente de o produto da feature
# ativa ser Python (não depende de pyproject.toml/requirements.txt na raiz,
# que pertencem ao produto, não ao template). Resolve pytest via `python -m`
# quando o binário não está no PATH (comum em ambiente Windows/Git Bash).
if [[ -d loop/tests ]]; then
  PYTEST_CMD=""
  if command -v pytest >/dev/null 2>&1; then
    PYTEST_CMD="pytest"
  elif command -v python3 >/dev/null 2>&1 && python3 -m pytest --version >/dev/null 2>&1; then
    PYTEST_CMD="python3 -m pytest"
  elif command -v python >/dev/null 2>&1 && python -m pytest --version >/dev/null 2>&1; then
    PYTEST_CMD="python -m pytest"
  fi
  [[ -n "$PYTEST_CMD" ]] && run_gate "loop-tests" $PYTEST_CMD -q loop/tests
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
  # pendencias-lint — o que segue sem prova precisa ficar dito, não implícito
  # (RETROSPECTIVA-005-006.md §8 / specs/002-fortalecimento-v4 RF-13).
  if ! grep -q "^## Pendências conhecidas" "$SPEC_PATH"; then
    echo "  ✖ pendencias-lint: $SPEC_PATH sem a seção '## Pendências conhecidas' (specs/002-fortalecimento-v4 RF-13)"
    FAILED=1
  fi
fi

# ── Arquivos tocados no diff atual (uncommitted + novos) ────────────────
# Base para orm-migration-lint e infra-assertion-lint: olhar o que MUDOU,
# não o repositório inteiro — mesmo recorte que o Builder está prestes a
# commitar.
CHANGED_FILES=$( { git diff --name-only HEAD 2>/dev/null; git ls-files --others --exclude-standard 2>/dev/null; } | sort -u)

# orm-migration-lint — migração sem o modelo ORM correspondente no mesmo
# diff é exatamente a divergência ORM↔banco que se repetiu 2x na retro
# (RETROSPECTIVA.md §3.2, ação 3): coluna/restrição só na migração, o ORM
# "mentia" em silêncio para quem lê só o modelo.
MIGRATION_CHANGED=$(echo "$CHANGED_FILES" | grep -E '(^|/)(migrations?|alembic/versions)/.+\.(py|sql|js|ts)$|(^|/)db/migrate/.+\.rb$' || true)
if [[ -n "$MIGRATION_CHANGED" && -z "${ORM_LINT_ACK:-}" ]]; then
  MODEL_CHANGED=$(echo "$CHANGED_FILES" | grep -E '(^|/)models?\.py$|(^|/)models?/.+\.py$|(^|/)schema\.prisma$|(^|/)entit(y|ies)/.+\.(py|ts)$' || true)
  if [[ -z "$MODEL_CHANGED" ]]; then
    echo "  ✖ orm-migration-lint: migração tocada sem modelo ORM correspondente no mesmo diff (constitution proposta, RF-06):"
    echo "$MIGRATION_CHANGED" | sed 's/^/      /'
    echo "    Se for intencional (ex.: migração de dado, não de schema), reconheça com ORM_LINT_ACK=1."
    FAILED=1
  fi
fi

# infra-assertion-lint — teste que mede o INSUMO (o YAML escrito) em vez da
# SAÍDA da ferramenta ficou verde com bug real presente: 'ports: []' no
# arquivo, o Compose concatena e as portas continuavam publicadas
# (RETROSPECTIVA-005-006.md §3.1 nº2, ação 9).
INFRA_TEST_FILES=$(git grep --untracked -lE '(docker-compose\.ya?ml|compose\.ya?ml)' -- '*test*infra*' '*infra*test*' '*test*compose*' '*compose*test*' 2>/dev/null || true)
if [[ -n "$INFRA_TEST_FILES" ]]; then
  for f in $INFRA_TEST_FILES; do
    if ! grep -qE 'compose[[:space:]]+config' "$f"; then
      echo "  ✖ infra-assertion-lint: $f parece medir o arquivo de config bruto, não a saída resolvida de 'docker compose config' (RF-07)"
      FAILED=1
    fi
  done
fi

# crlf-lint — escrita de arquivo por script converteu quebra de linha em
# byte literal 4x na retro; a 4ª vez passou verde (RETROSPECTIVA-005-006.md
# §3.4, ação 12). Cobre *.sh (shebang quebra) E *.py — achado do Verifier
# nesta própria sessão: um `open(p, "w").write(...)` sem `newline=""` no
# Windows introduziu CRLF em um dos testes desta feature, sem nenhum gate
# pegando (crlf-lint só cobria .sh na primeira versão). A armadilha não é
# específica de shell; é de "escrita de arquivo por script", como o nome
# do achado já diz.
CRLF_FILES=""
while IFS= read -r f; do
  [[ -f "$f" ]] || continue
  # -U: lê em modo binário — sem ela, grep no Git Bash/MSYS (Windows) abre em
  # modo texto e o próprio SO já stripa o \r antes do grep ver o byte (o
  # mesmo tipo de armadilha texto↔binário da retro, §3.4). No-op inofensivo
  # em grep GNU/Linux (arquivo já chega sem tradução).
  grep -Uq $'\r' "$f" 2>/dev/null && CRLF_FILES+="$f "
done < <({ git ls-files '*.sh' '*.py' 2>/dev/null; git ls-files --others --exclude-standard '*.sh' '*.py' 2>/dev/null; } | sort -u)
if [[ -n "$CRLF_FILES" ]]; then
  echo "  ✖ crlf-lint: script(s) shell com terminador CRLF (RF-08): $CRLF_FILES"
  FAILED=1
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
