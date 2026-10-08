# TASKS 004 — Revisão antes do commit com correção automática

> Não substitui o `loop/prd.json` ativo (`001-exemplo-todo-api`).

- [ ] T-001 — `loop/tests/test_ralph_revisao.py` + `loop/ralph.sh`: Verifier
      antes do commit, commit pelo loop, reprovação volta ao Builder, teto de
      retrabalho, veredito ilegível (RF-01 a RF-08). Testes primeiro.
      Depende de: — · risk: high (altera quem commita)

- [ ] T-002 — `loop/PROMPT_BUILD.md` e `loop/PROMPT_VERIFY.md`: Builder não
      commita e prioriza `state/review.md`; Verifier lê STORY/BASE (RF-09).
      Depende de: T-001 · risk: normal

- [ ] T-003 — ADR-0009 `proposto` + índice; `.gitignore`; `CLAUDE.md`,
      `ARCHITECTURE.md` e `README.md` refletem o novo protocolo.
      Depende de: T-001 · risk: low
