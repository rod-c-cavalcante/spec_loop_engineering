# TASKS 003 — Verifier: padrões (smells) e ponto fixo

> Não substitui o `loop/prd.json` ativo (`001-exemplo-todo-api`).

- [ ] T-001 — `loop/diff_base.py` + `loop/tests/test_diff_base.py`
      (RF-01 a RF-05). Testes primeiro, vistos falhando.
      Depende de: — · risk: normal

- [ ] T-002 — `loop/PROMPT_VERIFY.md`: item "Padrões e smells", bloco
      `OBSERVAÇÕES`, insumo 5 via `diff_base.py`, contagem de regras
      (RF-06, RF-07).
      Depende de: T-001 · risk: normal

- [ ] T-003 — `.claude/commands/verify.md`: ref base opcional e recomendação
      de sessão nova (RF-08).
      Depende de: T-001 · risk: low

- [ ] T-004 — `ARCHITECTURE.md` (D2) e `README.md`: refletir o novo alcance.
      Depende de: T-002, T-003 · risk: low
