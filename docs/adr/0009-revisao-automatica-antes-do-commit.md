# ADR-0009 — Revisão automática antes do commit; o loop commita, não o Builder

Status: proposto
Data: 2026-10-07
Decisores: <pendente — humano decide aceitar/rejeitar>
História/feature de origem: specs/004-revisao-antes-do-commit (RF-01 a RF-09)

## Contexto
`ARCHITECTURE.md §3` desenha "Verifier reprovou → feedback → Builder corrige"
antes do commit, mas isso nunca foi código: o Builder commitava no fim da
iteração, o Verifier só rodava à mão (`/verify`) e uma reprovação dependia de
um humano levar o recado. Código reprovado já estava commitado quando alguém
olhava. A constituição §12 pede mecanismo onde o passo é determinístico.

## Decisão
`loop/ralph.sh` roda o Verifier depois dos gates verdes e antes de qualquer
commit, em histórias `risk:high` e nas de `VERIFY_RISKS` (padrão
`high normal`). APROVADO: o loop commita. REPROVADO: a saída vai para
`state/review.md`, a história volta a `passes: false` e o Builder corrige na
iteração seguinte; após `MAX_REWORK` reprovações o loop para (exit 7). O
Builder deixa de commitar e escreve a mensagem em `state/.commit_msg`.

## Alternativas consideradas
- Builder commita e o Verifier audita depois (commit de correção em seguida)
  — rejeitada: mantém código reprovado no histórico e o pedido foi corrigir
  antes do commit.
- Pedir no `PROMPT_BUILD.md` que o Builder chame o Verifier — rejeitada: é
  texto, e o autor escolheria quando ser auditado (constituição §11/§12).
- Subagentes conversando direto — rejeitada: contraria D3 (monolítico); o
  canal por arquivo preserva o contexto limpo por iteração (D1).
- Verifier em toda história, inclusive `low` — rejeitada: custo sem retorno
  demonstrado (mesmo argumento do ADR-0007).

## Consequências
- (+) Nenhum commit do loop contém código que o Verifier reprovou; a
  correção não depende de humano no caminho comum.
- (+) O bloqueio do ADR-0007 (exit 6) deixa de ser o caso normal em
  `risk:high`: o Verifier chamado pelo loop registra o veredito em
  `state/verdicts.csv`; o exit 6 fica como rede de segurança.
- (−) Estende o Verifier a histórias `normal`, que o ADR-0007 (proposto)
  havia deixado de fora por custo; `VERIFY_RISKS=high` restaura aquele alcance.
- (−) O loop pode parar com árvore suja (exit 7/8); retomar exige
  `ALLOW_DIRTY=1`, override previsto no ADR-0004.
- (−) O veredito vem de texto de LLM; saída sem veredito para o loop (exit 8)
  em vez de aprovar.
- Reversão: remover o bloco 6 de `ralph.sh` e devolver o passo de commit ao
  `PROMPT_BUILD.md`; exige novo ADR.

## Verificação
`loop/tests/test_ralph_revisao.py` roda o `ralph.sh` real com Builder e
Verifier falsos: prova que a auditoria vê o HEAD anterior e a árvore suja,
que REPROVADO não gera commit e reverte `passes`, e os códigos 7 e 8.
