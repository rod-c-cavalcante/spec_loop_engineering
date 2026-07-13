# DevOps no SpecLoop — o loop é o pipeline

Princípio central: **uma única fonte de verdade de "pronto"**. O `gates.sh`
que o loop roda localmente é EXATAMENTE o que a CI roda no PR
(`.github/workflows/ci.yml`). Zero drift entre "passou na minha máquina" e
"passou no PR" — porque é o mesmo script.

## As práticas, camada por camada

**Commit → PR (local)**
- Trunk-based com branches curtas: 1 feature = 1 branch = 1 worktree = 1 loop.
  Branch que vive mais de poucos dias é sinal de fatia grossa (prd-lint).
- Hook de pre-commit roda gates L0 em commits HUMANOS (o loop já se auto-verifica):
  `git config core.hooksPath githooks` (1x por clone).
- Commits atômicos rastreáveis (`refs specs/NNN/spec.md`) — o git log É a
  documentação de auditoria.

**PR → main (CI)**
- CI roda gates L0 em todo push (rápido, feedback em minutos) e L2 no PR
  (E2E completo + smoke com rebuild limpo — o que pegou os bugs graves reais).
- O painel de métricas comenta no PR automaticamente (4 famílias + snapshot
  acumulado em `state/metrics_history.csv`) — a decisão de merge vê custo,
  qualidade e DORA no mesmo lugar.
- Branch protection recomendada: exigir gates-l0 + gates-l2 verdes; proibir
  push direto em main; o merge é sempre decisão humana (constituição §10).

**main → produção (CD)**
- Deploy automatizado a partir de main (deploy = merge → Deployment Frequency
  do painel vira métrica real, não proxy).
- 12-Factor como base: config por variável de ambiente (nunca no repo —
  constituição §6), paridade dev/prod via Docker (o rebuild limpo do smoke.sh
  existe exatamente para provar essa paridade), logs como fluxo de eventos
  (sem PII — constituição §13).
- Rollback barato > deploy perfeito: prefira feature flags e migrações
  retrocompatíveis a janelas de deploy heroicas.

**Produção → backlog (o loop de fora)**
- Incidente vira: classificação de gap (intent-spec | spec-impl | spec-oraculo)
  + item no backlog + se determinístico, mecanismo (constituição §12).
- CFR e MTTR (DORA) saem daqui — preencha no painel quando houver telemetria.

## DORA no contexto de Loop Engineering (leitura honesta)

Loop Engineering automatiza codificação e verificação — a HIPÓTESE é que Lead
Time for Changes e Deployment Frequency melhorem drasticamente (iterações
quase diárias com alta confiabilidade). O painel existe para PROVAR a hipótese
com números, não para assumi-la. Contrapeso obrigatório: se Lead Time cai mas
Change Failure Rate sobe, você só transferiu o custo para produção — leia
sempre o par (docs/FINOPS.md, anti-Goodhart).
