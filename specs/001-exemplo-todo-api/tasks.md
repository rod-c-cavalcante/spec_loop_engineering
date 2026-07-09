# TASKS 001 — API de tarefas

> Decomposição executável. Cada task vira uma história no `loop/prd.json`.
> `[P]` = paralelizável (candidata a worktree separado quando houver escala).
> Ordem respeita dependências: infra → store → rotas → validações.

- [ ] T-001 — Bootstrap do projeto Node (package.json, vitest, supertest,
      `src/app.js` vazio respondendo 404 padrão, `gates.sh` verde no vazio).
      Depende de: —
- [ ] T-002 — Store em memória (`src/todos/store.js`): create/list/get/update/
      delete + id UUID + ordem de inserção. Testes unitários do store.
      Depende de: T-001
- [ ] T-003 — RF-01 + RF-03: POST /todos e GET /todos com testes de integração.
      Depende de: T-002
- [ ] T-004 — RF-02: validação de title (422 + error code). [P]
      Depende de: T-003
- [ ] T-005 — RF-04 + RF-05: PATCH /todos/{id}, 404 para inexistente. [P]
      Depende de: T-003
