# ADRs — Architecture Decision Records

> Memória de longo prazo das decisões arquiteturais. Um ADR captura UMA decisão
> significativa: contexto, alternativas e consequências. ADRs são IMUTÁVEIS —
> nunca edite um ADR aceito; crie um novo que o substitui.

## Índice (mantenha atualizado — é o que o Builder lê primeiro)

| # | Título | Status |
|---|--------|--------|
| [0001](0001-persistencia-em-memoria-no-mvp.md) | Persistência em memória no MVP | aceito |
| [0002](0002-erros-como-texto-plano.md) | Erros como texto plano | substituído por ADR-0003 |
| [0003](0003-contrato-de-erro-json-padronizado.md) | Contrato de erro JSON padronizado | aceito |
| [0004](0004-isolamento-mecanico-de-agentes-por-lock-e-worktree.md) | Isolamento mecânico de agentes (lock + worktree) | aceito |
| [0005](0005-protecao-de-artefatos-de-features-mescladas.md) | Proteção de artefatos de features mescladas | aceito |
| [0006](0006-mutation-testing-obrigatorio-risk-high.md) | Mutation testing obrigatório em risk:high | proposto |
| [0007](0007-verifier-obrigatorio-em-risk-high.md) | Veredito do Verifier obrigatório para fechar história risk:high | proposto |
| [0008](0008-branch-protection-como-codigo.md) | Branch protection como código | proposto |

## Quando criar um ADR (calibragem — não burocratize)

CRIE um ADR quando a decisão é **cara de reverter ou atravessa features**:
- Escolha de stack, framework, biblioteca estrutural
- Contratos (formato de erro, versionamento de API, esquema de eventos)
- Estratégia de persistência, autenticação, observabilidade
- Padrões transversais (como tratamos datas, dinheiro, i18n)

NÃO crie ADR para: nome de variável, estrutura interna de um módulo,
decisão que vale só para uma feature (isso é o `plan.md`).

## Ciclo de vida

`proposto` → `aceito` → (`descontinuado` | `substituído por ADR-NNNN`)

- **Agentes podem PROPOR** ADRs (status `proposto`), nunca aceitar.
- **Humanos aceitam, descontinuam e substituem.** (constitution — governança)
- Ao substituir: novo ADR referencia o antigo; o antigo ganha o status
  `substituído por ADR-NNNN` (única edição permitida em ADR aceito).

## Caminho de promoção da memória

`state/progress.md` (tático, expurgo frequente)
  → destila para → `docs/adr/` (decisões, permanente)
    → promove para → `constitution.md` (só se virar regra universal verificável)

## Como os agentes usam (progressive disclosure)

1. Builder lê ESTE índice (barato: títulos + status).
2. Carrega o ADR completo só se relevante à história atual.
3. Diff que contraria ADR `aceito` → Builder bloqueia; Verifier reprova.
