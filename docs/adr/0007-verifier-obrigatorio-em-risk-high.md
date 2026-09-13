# ADR-0007 — Veredito do Verifier obrigatório para fechar história risk:high

Status: proposto
Data: 2026-09-13
Decisores: <pendente — humano decide aceitar/rejeitar>
História/feature de origem: specs/002-fortalecimento-v4 (RF-04), T-013

## Contexto
`ARCHITECTURE.md §7` (D2) já descrevia o Verifier como segunda camada de
verificação, mas nenhum script exigia sua execução — `SKIP_VERIFIER=1` era
citado como override sem nenhuma checagem correspondente em código; na
prática, o Verifier nunca era mecanicamente exigido para nenhuma história.
Uma retrospectiva externa (RETROSPECTIVA-005-006.md §4.3) mostra o custo
concreto: num período sem auditoria independente, 4 dos 5 falsos-verdes
encontrados eram testes que o próprio autor escreveu e validou — "um
revisor que não escreveu o código pergunta 'isso pode falhar?' antes de
perguntar 'isso passou?'".

## Decisão
`loop/ralph.sh` passa a bloquear (exit 6, distinto do checkpoint informativo
exit 5) o avanço do loop quando uma história `risk:high` está marcada
`passes: true` com gates verdes mas **sem** linha `APROVADO` correspondente
em `state/verdicts.csv`. Essa checagem já está implementada no código desta
sessão (não é pulável por `NO_CHECKPOINT=1`, que só afeta a pausa
informativa, não a exigência do veredito).

## Alternativas consideradas
- Manter como recomendação em `ARCHITECTURE.md` — rejeitada: já era a
  situação anterior e não preveniu os 4 falsos-verdes documentados.
- Exigir Verifier em toda história (não só `risk:high`) — rejeitada por ora:
  custo de latência/token por iteração (D2, ARCHITECTURE.md) em histórias de
  baixo risco não teve o mesmo retorno demonstrado nas retros; revisar se
  a régua trimestral (constituição, governança) mostrar padrão diferente.

## Consequências
- (+) O caso mais caro de auditoria pulada (risco alto, sem segunda opinião)
  fica mecanicamente impossível de passar despercebido pelo loop.
- (−) Loop pode ficar bloqueado esperando execução manual do Verifier
  (`/verify`) — trade-off aceito: é exatamente o ponto de checkpoint humano
  que a constituição já previa para `risk:high`.
- Reversão: reverter o bloco de `ralph.sh` que lê `state/verdicts.csv`;
  trivial, mas exige novo ADR justificando (mesma régua do ADR-0004).

## Verificação
Simular: marcar história `risk:high` como `passes:true` sem linha em
`state/verdicts.csv`, rodar `ralph.sh`, confirmar `exit 6` e mensagem citando
`/verify`. Depois registrar `APROVADO` em `verdicts.csv` para a mesma
história e confirmar que o loop segue para o checkpoint normal (`exit 5`,
ou passa direto com `NO_CHECKPOINT=1`).
