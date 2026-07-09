# CLAUDE.md — Memória do projeto (SpecLoop)

Este repositório segue **Spec-Driven Development + Loop Engineering**.
Você (Claude Code) opera sob as regras abaixo em TODA sessão, interativa ou em loop.

## Hierarquia de autoridade (em conflito, vence o de cima)
1. `.specify/memory/constitution.md` — regras inegociáveis
2. `specs/<feature-ativa>/spec.md` — critérios de aceite (EARS)
3. `specs/<feature-ativa>/plan.md` — decisões técnicas
4. Este arquivo — convenções operacionais
5. Instruções ad-hoc do usuário na sessão

## Workflow obrigatório
- NUNCA implemente sem spec. Se não existir `specs/NNN-*/spec.md` para o pedido,
  proponha criar a spec primeiro (ou rode `/speckit.specify` se disponível).
- Uma história por vez. A MENOR mudança coerente que satisfaça o critério EARS.
- TDAD: escreva primeiro os testes que falham, depois a implementação.
- Antes de declarar qualquer tarefa concluída, rode `./loop/gates.sh`.
  Se falhar, NÃO está concluída — corrija e rode de novo.
- Commits atômicos com referência à spec:
  `feat(todos): valida title obrigatório, refs specs/001-exemplo-todo-api/spec.md`

## Protocolo do loop (quando executado via loop/ralph.sh)
- Sua fonte de trabalho é `loop/prd.json`. Pegue a PRIMEIRA história com
  `passes: false`. Ignore as demais nesta iteração.
- Leia `state/progress.md` ANTES de agir — contém aprendizados das iterações
  anteriores. Não repita erros já documentados.
- Ao concluir a história: marque `passes: true` no prd.json, acrescente 2–5
  linhas de aprendizado em `state/progress.md`, faça o commit.
- Se TODAS as histórias tiverem `passes: true` e `gates.sh` retornar 0,
  emita exatamente: `<promise>COMPLETE</promise>`
- Se estiver bloqueado (dependência externa, ambiguidade na spec), emita
  `<promise>BLOCKED: <motivo em 1 linha></promise>` — nunca invente.

## Convenções do codebase
- Estrutura de feature: `specs/NNN-nome-curto/{spec.md, plan.md, tasks.md}`
- Specs curtas: 1–3 páginas. Acima disso, divida a feature.
- "Out of scope" é tão importante quanto o escopo — sempre presente na spec.
- Não adicione dependências sem justificar no plan.md da feature.
- Não toque em arquivos fora do escopo da história atual.

## O que você NUNCA faz
- Declarar sucesso sem gates verdes (a promise sem prova é o anti-padrão nº 1).
- Editar `constitution.md` sem instrução humana explícita.
- Fazer push. O loop commita local; push e PR são decisões humanas.
- Remover ou afrouxar testes para "fazer passar".
