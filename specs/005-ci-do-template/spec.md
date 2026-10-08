# SPEC 005 — CI do próprio template: smoke sem produto e testes do loop

> Feature de tooling. Origem: corrida de CI do PR #2 (run 37705960750, job
> "Gates L2"), analisada a pedido do humano em 2026-10-07.

## Contexto e motivação

O job Gates L2 do PR #2 falhou em `smoke(rebuild+HTTP real)` com
`Connection refused`. A causa não é a v5.0: o repositório é um template sem
produto (sem `docker-compose.yml`, `package.json`, `requirements.txt` ou
`pyproject.toml`), e o `smoke.sh` faz chamadas HTTP a `localhost:8000` mesmo
assim. O PR #1 (2026-09-13) falhou do mesmo jeito e registrou isso como
esperado. Consequência: nenhum PR do próprio template consegue ficar verde,
o que inviabiliza a branch protection do ADR-0008.

A mesma corrida mostrou um falso-verde: o gate `loop-tests` não aparece em
nenhum dos dois jobs. O runner não tem `pytest`, e `gates.sh` pula o gate em
silêncio — os testes de `loop/tests/` nunca rodaram em CI.

## Escopo (in)

- `smoke.sh` reconhece "repositório sem produto" e declara o smoke não
  aplicável, de forma visível.
- `gates.sh` reprova quando `loop/tests/` existe e não há `pytest`.
- `ci.yml` instala `pytest` nos jobs L0 e L2.

## Requisitos (EARS)

### RF-01 — Smoke não aplicável em repositório sem produto (State-driven)
WHILE o repositório não tem `docker-compose.yml`, `compose.yml`,
`package.json`, `pyproject.toml` nem `requirements.txt` na raiz, e `BASE_URL`
não foi definida por quem chamou, THE SYSTEM SHALL encerrar `loop/smoke.sh`
com código 0 e uma mensagem dizendo que não há produto a provar, sem fazer
chamadas HTTP.

### RF-02 — Com produto, o smoke continua obrigatório (Unwanted behavior)
IF qualquer um desses arquivos existe, ou `BASE_URL` foi definida, ou
`SMOKE_REQUIRED=1`, THEN THE SYSTEM SHALL executar os checks HTTP e falhar
quando o serviço não responde.

### RF-03 — Testes do loop sem pytest reprovam o gate (Unwanted behavior)
IF `loop/tests/` existe e nenhum `pytest` está disponível, THEN THE SYSTEM
SHALL reprovar `gates.sh` com mensagem dizendo como instalar, em vez de pular
o gate.

### RF-04 — CI roda os testes do loop (Ubiquitous)
THE SYSTEM SHALL instalar `pytest` nos jobs `gates-l0` e `gates-l2` de
`.github/workflows/ci.yml`, de modo que o gate `loop-tests` execute neles.

## Out of scope (tão importante quanto o escopo)

- Implementar o produto de exemplo (`specs/001-exemplo-todo-api`).
- Mudar os checks HTTP do `smoke.sh` ou o rebuild de containers.
- Aceitar o ADR-0008 ou configurar branch protection.

## Pendências conhecidas

- RF-01 troca um vermelho permanente por um "não aplicável": um produto que
  não use nenhum dos cinco arquivos-marcadores e não defina `BASE_URL` teria
  o smoke pulado. `SMOKE_REQUIRED=1` fecha essa brecha, mas é opt-in.
- RF-03 não tem teste automatizado (exigiria simular ambiente sem Python);
  foi verificado à mão e pela própria corrida de CI.
- RF-04 só se prova na CI real.

## Dados pessoais (LGPD)

- **Dados tocados**: nenhum. Esta feature altera tooling de desenvolvimento
  e CI — não introduz coleta, log ou processamento de dado pessoal.
- **Base legal**: n/a. | **Retenção**: n/a.
- **Minimização**: n/a.

## Critérios de pronto (definition of done)

- [ ] RF-01 e RF-02 cobertos por teste em `loop/tests/test_smoke.py`, visto
      falhando antes da implementação
- [ ] `./loop/gates.sh --level 2` retorna 0 neste repositório
- [ ] Corrida de CI do PR mostra `loop-tests` executando e L2 verde
- [ ] Commits referenciam esta spec
