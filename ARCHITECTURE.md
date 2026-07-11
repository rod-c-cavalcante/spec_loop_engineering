# ARCHITECTURE.md — Arquitetura proposta do SpecLoop

## 1. Visão geral

O SpecLoop implementa o padrão **"spec como árbitro, loop como motor"**:

- A **spec** (Camada 1) é a única fonte da verdade sobre o que "pronto" significa.
- O **loop** (Camada 2) é quem consulta o árbitro repetidamente, sem você no meio.
- O **estado** (Camada 3) vive fora do contexto do modelo — em git e arquivos —
  para que o loop sobreviva a estouros de janela de contexto e a reinícios.

A tese central: o gargalo da IA em produção não é o modelo, é a **articulação de
intenção** (Intent Harness) e a **verificação** (backpressure). O SpecLoop
industrializa os dois.

## 2. Camada 1 — Intent Harness (compatível com GitHub Spec Kit)

### Por que o Spec Kit como base — e por que não só ele

**Veredito: o Spec Kit É a base ideal para a Camada 1, mas não cobre as Camadas 2 e 3.**

O que o Spec Kit resolve muito bem:
- Workflow maduro: `/speckit.constitution → specify → clarify → plan → tasks → implement → converge`
- Padrão de mercado (117k stars, 30+ agentes suportados) — zero vendor lock-in
- Templates prontos, sistema de extensões/presets/bundles para customização
- `/speckit.converge` reconcilia codebase × spec (essencial em brownfield)

O que o Spec Kit NÃO resolve (e o SpecLoop adiciona):

| Lacuna | Consequência sem o SpecLoop | Solução SpecLoop |
|---|---|---|
| `/speckit.implement` é one-shot interativo | Você fica no teclado; "pronto" é declarado, não provado | `loop/ralph.sh` itera até os gates passarem |
| Sem estado entre sessões | Contexto estoura em features grandes | git + `state/progress.md` + contexto limpo/iteração |
| Sem verificação obrigatória | Agente declara sucesso com testes quebrados | `gates.sh` (backpressure) + agente Verifier |
| Sem travas de custo | Loop infinito = fatura infinita | MAX_ITERATIONS, timeout, circuit breaker |
| Sem métricas | "Quanto a IA economizou?" vira chute | `state/metrics.csv` → HDE |

Conclusão prática: **instale o Spec Kit por cima do SpecLoop** (`specify init .
--force --integration claude`). Os dois foram desenhados para as mesmas
convenções (`.specify/memory/constitution.md`, `specs/NNN-feature/`). O Spec Kit
gera os artefatos; o SpecLoop os executa em loop.

### Artefatos e seus papéis

| Artefato | Papel | Memória |
|---|---|---|
| `constitution.md` | Regras inegociáveis (5–10, verificáveis) | Long-term |
| `spec.md` | O quê/por quê, requisitos em **EARS** | Mid-term (vida da feature) |
| `plan.md` | Decisões técnicas, stack, contratos | Mid-term |
| `tasks.md` | Decomposição com dependências e marcadores [P] de paralelismo | Mid-term |
| `prd.json` | `tasks.md` traduzido para máquina (`passes: true/false`) | Fonte do loop |
| `docs/adr/` | Decisões arquiteturais (contexto + alternativas + consequências); imutáveis, substituíveis | Long-term |

**EARS obrigatório nos critérios de aceite.** Os cinco padrões (Ubiquitous,
Event-driven, State-driven, Unwanted behavior, Optional) reduzem ambiguidade e
melhoram drasticamente o first-pass success. Exemplo:

> WHEN o usuário envia POST /todos sem o campo `title`,
> THE SYSTEM SHALL responder 422 com corpo `{ "error": "title_required" }`.

Um critério EARS bem escrito é um teste esperando para nascer — e é exatamente
isso que o Builder faz com ele (TDAD: testes primeiro, implementação depois).

## 3. Camada 2 — Loop Runtime (padrão Ralph, endurecido)

### O ciclo de uma iteração

```
┌──────────────────────────────────────────────────────────┐
│ ITERAÇÃO N (contexto 100% limpo)                         │
│                                                          │
│ 1. ralph.sh injeta PROMPT_BUILD.md no Claude Code        │
│ 2. Builder lê: prd.json → primeira história passes=false │
│    + spec.md da feature + constitution.md + progress.md  │
│ 3. Builder escreve testes que falham (TDAD)              │
│ 4. Builder implementa a MENOR mudança coerente           │
│ 5. Builder roda ./loop/gates.sh                          │
│    ├─ FALHOU → corrige e repete (dentro da iteração)     │
│    └─ PASSOU → segue                                     │
│ 6. Verifier (subagente) audita diff × critérios EARS     │
│    ├─ REPROVOU → feedback → Builder corrige              │
│    └─ APROVOU → segue                                    │
│ 7. Marca passes=true no prd.json                         │
│ 8. Registra aprendizado em state/progress.md             │
│ 9. Commit atômico: "feat(x): ... refs specs/NNN/spec.md" │
│ 10. Todas passes=true? → <promise>COMPLETE</promise>     │
└──────────────────────────────────────────────────────────┘
        │ contexto descartado; estado fica em git+arquivos
        ▼
  ITERAÇÃO N+1 (novo contexto limpo lê o estado e continua)
```

### Decisões de projeto e trade-offs

**D1 — Contexto limpo por iteração (não sessão contínua).**
Sessões longas degradam ("context rot"). O SpecLoop descarta o contexto a cada
iteração e reconstrói o mínimo necessário a partir do estado externo. Trade-off:
custo de re-leitura por iteração; mitigado mantendo specs curtas (1–3 páginas)
e `progress.md` como resumo denso, não log verboso.

**D2 — Verificação em duas camadas: determinística + agêntica.**
`gates.sh` (lint, typecheck, testes, build) é barato, objetivo e roda sempre.
O Verifier (LLM-as-judge com `PROMPT_VERIFY.md`) audita o que gates não pegam:
aderência aos critérios EARS, escopo do diff, violações da constituição.
Trade-off: o Verifier adiciona latência e custo por iteração — vale quando
qualidade importa mais que velocidade (produção). Para spikes, desligue com
`SKIP_VERIFIER=1`.

**D3 — Uma história por iteração (monolítico, não multi-agente).**
Agentes não-determinísticos conversando entre si é complexidade prematura.
O SpecLoop é deliberadamente monolítico: um processo, uma história por volta.
Paralelismo acontece na camada de infraestrutura (worktrees), não na de agentes.

**D4 — "Pronto" = promise + gates, nunca só promise.**
O loop só encerra quando o Builder emite `<promise>COMPLETE</promise>` E o
`gates.sh` retorna 0 E todas as histórias têm `passes: true`. Condição dupla
evita o modo de falha clássico: o agente declara vitória com testes quebrados.

**D5 — Travas (circuit breaker).**
- `MAX_ITERATIONS` (default 10): teto absoluto de voltas.
- `MAX_SAME_FAILURE` (default 3): se o mesmo gate falha 3x seguidas, o loop
  para e pede humano — repetir a mesma abordagem que falha é desperdício.
- `ITERATION_TIMEOUT` (default 20min): mata iterações penduradas.

### ADRs — a memória do "porquê"

O loop tem contexto limpo por iteração (D1); sem memória de decisões, o Builder
tende a re-decidir o já decidido. Os ADRs (`docs/adr/`) fecham esse buraco:
o Builder lê o índice (progressive disclosure — títulos + status), segue ADRs
`aceito`s sem rediscutir, propõe novos (status `proposto`) e bloqueia em
conflito; o Verifier reprova diffs que contradigam ADR aceito; o `gates.sh`
valida o formato (adr-lint). Cadeia de promoção: `progress.md` → ADR →
constituição. ADR é para decisão cara de reverter ou transversal a features —
decisão local de feature mora no `plan.md`.

## 4. Camada 3 — Estado & telemetria

- **git é a memória primária.** Commits atômicos por história, mensagem
  referenciando a spec (`refs specs/001-x/spec.md`) → rastreabilidade total.
- **`state/progress.md` é a memória de aprendizado.** Cada iteração acrescenta
  2–5 linhas: o que fez, o que descobriu, armadilhas do codebase. A iteração
  seguinte lê isso antes de agir. Faça expurgo quando passar de ~150 linhas.
- **`state/metrics.csv` é a memória econômica.** `iteração, história, tokens,
  duração, resultado`. HDE = custo tokens (R$) ÷ custo-hora dev (R$) →
  minutos-equivalentes. Três meses disso mudam a conversa sobre ROI.

## 5. Escalabilidade

### Paralelismo com git worktrees
```bash
git worktree add ../projeto-feat-002 -b feat/002-pagamentos
cd ../projeto-feat-002 && ./loop/ralph.sh   # loop independente, zero colisão
```
Cada worktree tem checkout próprio na sua branch; N loops rodam sobre o mesmo
repositório sem tocar nos arquivos uns dos outros. As tasks marcadas `[P]` no
`tasks.md` são as candidatas naturais a worktrees separados.

### Do time solo ao time grande
| Escala | Configuração |
|---|---|
| Solo / MVP | 1 loop, MAX_ITERATIONS=10, Verifier ligado |
| Time pequeno | 1 worktree por feature; PRs revisados por humano; CI roda gates de novo |
| Escala industrial | Loops em containers efêmeros (padrão "arquiteto persistente + devs efêmeros"); o SpecLoop é o protótipo local desse desenho |

### Loop de feedback do sistema (o loop de fora)
Todo bug em produção é classificado em `state/progress.md`:
- **Spec→Implementation gap**: a spec era clara, a implementação divergiu →
  fortaleça `gates.sh` e o `PROMPT_VERIFY.md`.
- **Intent→Spec gap**: a spec nasceu incompleta → melhore o `/speckit.clarify`
  e os templates de spec.
Em três meses, o padrão de gaps mostra onde investir. Esse é o loop que melhora
os loops — e é onde o valor composto mora.

## 6. O que este template NÃO é

- Não é um substituto para revisão humana de PR. É um gerador de PRs melhores.
- Não é multi-agente orquestrado. É um loop monolítico deliberado.
- Não é recomendado para tarefas triviais — uma sessão interativa é mais rápida
  e segura para mudanças de 10 minutos. Loop é para backlog, não para hotfix.
