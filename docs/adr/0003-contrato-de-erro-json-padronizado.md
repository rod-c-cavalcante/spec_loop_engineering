# ADR-0003 — Contrato de erro JSON padronizado

Status: aceito
Data: 2026-07-10
Decisores: tech lead (humano)
História/feature de origem: T-004 / specs/001-exemplo-todo-api/spec.md (RF-02, RF-05)

## Contexto
ADR-0002 gerou parsing frágil de mensagens no cliente. A spec 001 já exige
códigos de erro estáveis (`title_required`, `not_found`). Clientes precisam de
um contrato que não quebre quando o texto da mensagem mudar.

## Decisão
Toda resposta de erro HTTP tem corpo `{ "error": "<codigo_snake_case>" }`,
com o código estável documentado na spec da feature. Substitui o ADR-0002.

## Alternativas consideradas
- RFC 7807 (application/problem+json) — rejeitada por ora: mais campos do que
  o produto consome; candidata natural a ADR futuro se surgirem múltiplos clientes.
- Manter texto plano — rejeitada: contrato acidental (ver consequências do ADR-0002).

## Consequências
- (+) Clientes fazem switch por código, não parsing de string; i18n livre no front.
- (−) Um campo a mais em toda resposta de erro; migração dos testes antigos.
- Reversão: barata enquanto houver um único cliente; cara depois — por isso ADR.

## Verificação
Testes de integração asseguram o shape `{error}` em RF-02 e RF-05;
Verifier reprova erro novo sem código snake_case documentado na spec.
