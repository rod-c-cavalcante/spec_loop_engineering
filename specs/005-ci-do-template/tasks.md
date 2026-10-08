# TASKS 005 — CI do próprio template

> Não substitui o `loop/prd.json` ativo (`001-exemplo-todo-api`).

- [ ] T-001 — `loop/tests/test_smoke.py` + `loop/smoke.sh`: smoke não
      aplicável sem produto; obrigatório com produto (RF-01, RF-02).
      Depende de: — · risk: normal

- [ ] T-002 — `loop/gates.sh` reprova `loop/tests/` sem pytest;
      `.github/workflows/ci.yml` instala pytest em L0 e L2 (RF-03, RF-04).
      Depende de: — · risk: normal
