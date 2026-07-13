# ADR-0005 — Proteção de artefatos de features já mescladas + consistência tripla

Status: aceito
Data: 2026-07-13
Decisores: tech lead (humano)
História/feature de origem: retrospectiva forja_platform §2.2 (quase-incidente: template sobrescreveu specs/008/plan.md)

## Contexto
`setup-plan.ps1` rodou com `.specify/feature.json` apontando para a feature
anterior (008) e sobrescreveu o plan.md de uma feature JÁ MESCLADA com um
template em branco. Detecção foi sorte (git status manual). Specs de features
mescladas são registro histórico — corrompê-las quebra a rastreabilidade que
é o ativo central do SDD.

## Decisão
O preflight valida consistência tripla (`.specify/feature.json` ↔ branch git
atual ↔ `feature`/`branchName` do prd.json) e bloqueia escrita em `specs/NNN-*`
cuja branch já está mesclada na principal (merged-guard), salvo
`OVERRIDE_MERGED=1` explícito.

## Alternativas consideradas
- Confiar na atualização manual do feature.json — rejeitada: foi a causa raiz.
- Tornar specs/ mescladas read-only no filesystem — rejeitada: quebra correções
  legítimas de typo e não funciona uniformemente entre SOs.

## Consequências
- (+) A classe inteira "ferramenta certa, alvo errado" morre no preflight.
- (−) Correções legítimas em spec histórica exigem override consciente (bom:
  vira ato deliberado e auditável).
- Reversão: remover itens 3-4 do preflight; exigiria ADR substituto.

## Verificação
`preflight.sh` itens 3 e 4; testável apontando feature.json para feature
divergente (deve abortar com rc=11).
