# SPEC 004 — Revisão antes do commit com correção automática

> Feature de tooling: altera o próprio SpecLoop (`loop/ralph.sh`, prompts).
> Origem: pedido do humano em 2026-10-07, na sequência da spec 003 — quando a
> revisão apontar correções, o loop deve devolvê-las ao Builder sozinho, antes
> de qualquer commit.

## Contexto e motivação

`ARCHITECTURE.md §3` já desenha o ciclo assim: o Verifier audita, "REPROVOU →
feedback → Builder corrige", e só depois vem o commit. O código nunca fez
isso: o Builder commita no fim da própria iteração, o Verifier só roda à mão
(`/verify`), e uma reprovação depende de um humano levar o recado de volta.
O resultado é commit de código reprovado e retrabalho manual.

## Escopo (in)

- `loop/ralph.sh` roda o Verifier depois dos gates verdes e antes do commit.
- Reprovação volta ao Builder por arquivo (`state/review.md`), sem humano.
- O commit passa a ser feito pelo loop, só depois da aprovação.
- Teto de retrabalho por história, com parada para humano.

## Requisitos (EARS)

### RF-01 — Verifier roda antes do commit (Event-driven)
WHEN uma história termina a iteração marcada `passes: true` com gates verdes
e seu `risk` é `high` ou está em `VERIFY_RISKS` (padrão: `high normal`),
THE SYSTEM SHALL executar o Verifier sobre o diff desde o commit em que a
história começou, informando a história e esse ponto fixo, antes de criar
qualquer commit.

### RF-02 — Aprovação gera o commit (Event-driven)
WHEN o Verifier emite `VEREDITO: APROVADO`, THE SYSTEM SHALL criar um commit
com todo o trabalho da história, usando a mensagem deixada pelo Builder em
`state/.commit_msg`, e remover `state/review.md`.

### RF-03 — Reprovação volta ao Builder sem commit (Event-driven)
WHEN o Verifier emite `VEREDITO: REPROVADO`, THE SYSTEM SHALL gravar a saída
do Verifier em `state/review.md`, reverter a história para `passes: false`,
não criar commit, e seguir para a próxima iteração.

### RF-04 — Teto de retrabalho para e chama humano (Unwanted behavior)
IF a mesma história é reprovada mais de `MAX_REWORK` vezes (padrão 2) na
mesma execução do loop, THEN THE SYSTEM SHALL encerrar com código 7, sem
commit, preservando `state/review.md`.

### RF-05 — Veredito ilegível não vira aprovação (Unwanted behavior)
IF a saída do Verifier não contém `VEREDITO: APROVADO` nem
`VEREDITO: REPROVADO`, THEN THE SYSTEM SHALL encerrar com código 8, sem commit.

### RF-06 — História fora do alcance do Verifier commita direto (State-driven)
WHILE o `risk` da história não é `high` nem está em `VERIFY_RISKS`, THE SYSTEM
SHALL criar o commit após os gates verdes sem executar o Verifier.

### RF-07 — Gates vermelhos nunca deixam história marcada pronta (Unwanted behavior)
IF a história está `passes: true` e os gates do loop falham, THEN THE SYSTEM
SHALL reverter a história para `passes: false`, sem commit e sem Verifier.

### RF-08 — Mensagem de commit sempre rastreável (Unwanted behavior)
IF `state/.commit_msg` não existe ou está vazio no momento do commit, THEN
THE SYSTEM SHALL usar uma mensagem que cita a história e `refs <specPath>`.

### RF-09 — Builder não commita e prioriza correções pendentes (Ubiquitous)
THE SYSTEM SHALL declarar em `loop/PROMPT_BUILD.md` que o Builder (a) deixa a
mensagem de commit em `state/.commit_msg` em vez de commitar e (b) quando
`state/review.md` existe, executa as AÇÕES dele antes de qualquer outra coisa.

## Out of scope (tão importante quanto o escopo)

- O Verifier consertar código (continua só aprovando ou reprovando).
- Encaminhar OBSERVAÇÕES não bloqueantes (smells, spec 003) ao Builder — só
  as AÇÕES de um REPROVADO voltam.
- Agentes conversando direto entre si: o canal é arquivo, mediado por
  `ralph.sh` (ARCHITECTURE.md D3).
- Push, PR ou merge automáticos (constituição §10).
- Remover o checkpoint humano e o bloqueio de `risk:high` (ADR-0007).
- Aceitar o ADR-0009 proposto por esta feature.
- Mudar o schema de `state/verdicts.csv` ou de `state/metrics.csv`.

## Pendências conhecidas

- RF-09 é texto de prompt: um Builder que commitar por conta própria não é
  impedido. O loop tolera (audita desde o commit de início da história), mas
  o código reprovado já estará commitado localmente.
- O veredito é lido da saída textual de um LLM; os testes usam agentes falsos.
  Nenhuma corrida com Claude real foi feita nesta feature.
- Saída com código 7 ou 8 deixa a árvore suja; retomar exige
  `ALLOW_DIRTY=1 ./loop/ralph.sh` (o preflight exige árvore limpa — ADR-0004).
- O contador de retrabalho vive na memória do processo: reiniciar o loop zera.
- Rodar o Verifier em histórias `normal` aumenta custo e latência por
  iteração (ARCHITECTURE.md D2); `VERIFY_RISKS=high` restringe.

## Dados pessoais (LGPD)

- **Dados tocados**: nenhum. Esta feature altera tooling de desenvolvimento
  (`loop/`, `docs/`) — não introduz coleta, log ou processamento de dado
  pessoal.
- **Base legal**: n/a. | **Retenção**: n/a.
- **Minimização**: n/a.

## Critérios de pronto (definition of done)

- [ ] RF-01 a RF-08 cobertos por teste em `loop/tests/test_ralph_revisao.py`,
      visto falhando antes da implementação
- [ ] `./loop/gates.sh` retorna 0
- [ ] ADR-0009 criado como `proposto` e indexado
- [ ] Commits referenciam esta spec
