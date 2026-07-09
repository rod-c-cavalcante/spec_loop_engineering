# PLAN 001 — API de tarefas

> O plan traduz o QUÊ (spec) em COMO (decisões técnicas). Curto e decisivo.
> Este exemplo usa Node.js; troque pela sua stack — o loop é agnóstico.

## Stack e decisões

| Decisão | Escolha | Justificativa (2 linhas máx.) |
|---|---|---|
| Runtime | Node.js 20+ | Ubíquo, zero setup no ambiente do loop |
| Framework HTTP | Express 4 | Mínimo suficiente; sem opinião de arquitetura |
| Testes | Vitest + Supertest | Rápido, API compatível com Jest, testa HTTP de ponta a ponta |
| Armazenamento | Map em memória | Escopo da feature exclui banco (ver spec, out of scope) |

## Estrutura de arquivos

```
src/
├── app.js          # instância Express + rotas (exportada p/ testes)
├── server.js       # bootstrap (listen) — separado p/ testabilidade
└── todos/
    ├── router.js   # rotas /todos
    └── store.js    # Map em memória + geração de id
tests/
└── todos.test.js   # 1+ teste por critério EARS (RF-01..RF-05)
```

## Contratos

- Tarefa: `{ id: string, title: string, done: boolean, createdAt: ISO8601 }`
- Erros: sempre `{ "error": "<código_snake_case>" }` com o status HTTP da spec.

## Riscos e mitigação

- Ordem de criação em Map: garantida por inserção; testar explicitamente (RF-03).
- Id único: usar `crypto.randomUUID()` — sem dependência extra.
