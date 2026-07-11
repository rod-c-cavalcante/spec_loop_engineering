# ADR-0001 — Persistência em memória no MVP

Status: aceito
Data: 2026-07-10
Decisores: tech lead (humano)
História/feature de origem: T-002 / specs/001-exemplo-todo-api/spec.md

## Contexto
O MVP precisa validar o pipeline completo do loop (spec → prd → gates → commit)
com custo zero de infra. Volume esperado: < 100 tarefas por sessão. A spec 001
declara persistência em banco explicitamente fora de escopo.

## Decisão
Usaremos um Map em memória atrás de uma interface de store
(`src/todos/store.js`). Nenhum código fora do store conhece o mecanismo
de armazenamento.

## Alternativas consideradas
- SQLite — rejeitada: setup e dependência extras sem ganho no escopo do MVP.
- Postgres — rejeitada: infra prematura (constitution §9, simplicidade primeiro).

## Consequências
- (+) Zero setup; testes rápidos e determinísticos; loop roda em qualquer máquina.
- (−) Dados voláteis entre execuções — aceitável no MVP, inaceitável na feature 002.
- Reversão: trocar a implementação do store mantendo a interface; exigirá
  novo ADR que substitui este quando a feature de persistência entrar.

## Verificação
Verifier reprova diffs que acessem armazenamento fora de `src/todos/store.js`
ou adicionem driver de banco sem ADR substituto (gate: grep por `sqlite|pg|mongoose`).
