# SPEC 001 — API de tarefas (feature de exemplo)

> Feature de exemplo para demonstrar o formato. Substitua pela sua primeira
> feature real mantendo a estrutura: contexto → escopo → requisitos EARS →
> out of scope → critérios de pronto.

## Contexto e motivação

Precisamos de uma API REST mínima de tarefas (todos) para servir de esqueleto
do produto e de cobaia do loop. Ela valida o pipeline completo:
spec → prd.json → loop → gates → commit rastreável.

## Escopo (in)

- CRUD de tarefas em memória (sem banco nesta feature)
- Validação de entrada e códigos de erro consistentes
- Testes automatizados cobrindo todos os critérios EARS abaixo

## Requisitos (EARS)

### RF-01 — Criar tarefa (Event-driven)
WHEN o cliente envia `POST /todos` com corpo `{ "title": "<string não vazia>" }`,
THE SYSTEM SHALL criar a tarefa com `id` único, `done: false`, e responder
`201` com a tarefa criada.

### RF-02 — Rejeitar título ausente (Unwanted behavior)
IF o corpo de `POST /todos` não contém `title` ou `title` é string vazia,
THEN THE SYSTEM SHALL responder `422` com corpo `{ "error": "title_required" }`
e não criar nada.

### RF-03 — Listar tarefas (Ubiquitous)
THE SYSTEM SHALL responder `GET /todos` com `200` e um array JSON de todas as
tarefas, em ordem de criação.

### RF-04 — Concluir tarefa (Event-driven)
WHEN o cliente envia `PATCH /todos/{id}` com `{ "done": true }` e a tarefa existe,
THE SYSTEM SHALL atualizar `done` e responder `200` com a tarefa atualizada.

### RF-05 — Tarefa inexistente (Unwanted behavior)
IF `PATCH /todos/{id}` ou `DELETE /todos/{id}` referenciam id inexistente,
THEN THE SYSTEM SHALL responder `404` com `{ "error": "not_found" }`.

## Out of scope (tão importante quanto o escopo)

- Autenticação e autorização
- Persistência em banco (feature 002)
- Paginação, filtros, ordenação customizada
- Frontend

## Critérios de pronto (definition of done)

- [ ] Todos os RF acima cobertos por testes automatizados que passam
- [ ] `./loop/gates.sh` retorna 0
- [ ] Commits referenciam esta spec
- [ ] `state/progress.md` atualizado com aprendizados
