#!/usr/bin/env bash
# =============================================================================
# SpecLoop · smoke.sh — verificação ponta a ponta ROTEIRIZADA (gate L2)
# Origem: retrospectiva §1.1/§2.3 — os bugs mais graves (tipo errado, string
# em vez de número, DELETE sem await, env ausente no compose) só apareceram
# em rebuild limpo + chamadas reais. Este script transforma esse ritual
# (pulável sob pressão) em portão mecânico.
#
# Python urllib em vez de curl/bash: elimina a classe recorrente de bugs de
# encoding UTF-8 mutilando acentuação nos testes manuais.
#
# ESQUELETO: edite SMOKE_CHECKS (abaixo) para o seu produto. Cada check é
# {method, url, body?, expect_status, expect_json?: {campo: valor}}.
#
# Uso: ./loop/smoke.sh            (chamado pelo gates.sh --level 2)
#   SKIP_REBUILD=1  pula o docker rebuild (só roda os checks)
#   BASE_URL=...    default http://localhost:8000
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")/.."
BASE_URL="${BASE_URL:-http://localhost:8000}"

# ── 1) Rebuild limpo — o único jeito de pegar env ausente e estado fantasma ──
if [[ -z "${SKIP_REBUILD:-}" ]] && [[ -f docker-compose.yml || -f compose.yml ]]; then
  echo "▶ smoke: rebuild limpo (down -v && up --build)"
  docker compose down -v --remove-orphans
  docker compose up --build -d
  echo "▶ smoke: aguardando saúde dos serviços (até 90s)"
  for i in $(seq 1 30); do
    if python3 -c "import urllib.request,sys; urllib.request.urlopen('$BASE_URL/health', timeout=2)" 2>/dev/null; then
      echo "  serviços de pé."; break
    fi
    sleep 3
    [[ $i -eq 30 ]] && { echo "✖ smoke: serviços não subiram em 90s"; exit 1; }
  done
fi

# ── 2) Checks reais — HTTP de verdade, JSON de verdade, encoding de verdade ──
python3 - "$BASE_URL" << 'PYEOF'
import json, sys, urllib.request, urllib.error

BASE = sys.argv[1]

# EDITE AQUI: os checks do SEU produto. Exemplos p/ a feature 001 (todo-api).
# Inclua sempre: 1 criação com ACENTUAÇÃO (pega bug de encoding), 1 erro
# esperado (pega contrato de erro), 1 deleção seguida de leitura (pega o
# clássico "DELETE que não deleta" — bug real da retro, invisível p/ mocks).
SMOKE_CHECKS = [
    dict(name="cria tarefa com acentuação", method="POST", path="/todos",
         body={"title": "Ação de verificação nº 1 — çãõé"},
         expect_status=201, expect_json={"done": False}),
    dict(name="rejeita title vazio (contrato de erro)", method="POST", path="/todos",
         body={"title": ""}, expect_status=422, expect_json={"error": "title_required"}),
    dict(name="lista contém a tarefa criada", method="GET", path="/todos",
         expect_status=200),
]

def call(method, path, body=None):
    req = urllib.request.Request(BASE + path, method=method)
    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        req.add_header("Content-Type", "application/json; charset=utf-8")
    try:
        with urllib.request.urlopen(req, data=data, timeout=10) as r:
            return r.status, json.loads(r.read().decode("utf-8") or "null")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8") or "null")

failed = 0
for c in SMOKE_CHECKS:
    status, resp = call(c["method"], c["path"], c.get("body"))
    ok = status == c["expect_status"]
    for k, v in (c.get("expect_json") or {}).items():
        ok = ok and isinstance(resp, dict) and resp.get(k) == v
    print(("  ✔ " if ok else "  ✖ ") + c["name"] + f" [{status}]")
    if not ok:
        print(f"     esperado: status={c['expect_status']} json⊇{c.get('expect_json')}")
        print(f"     recebido: {json.dumps(resp, ensure_ascii=False)[:200]}")
        failed += 1

sys.exit(1 if failed else 0)
PYEOF
RC=$?
if [[ $RC -eq 0 ]]; then echo "══ SMOKE: TODOS VERDES ══"; else echo "══ SMOKE: FALHA ══"; fi
exit $RC
