# SpecLoop — Projeto-modelo: SDD + Loop Engineering para Claude Code

> **A spec é o árbitro. O loop é o motor. Você é o engenheiro que projeta os dois.**

SpecLoop é um template de projeto para Claude Code que une as duas disciplinas mais
importantes do desenvolvimento com IA em 2026:

1. **Spec-Driven Development (SDD)** — a intenção vira artefato versionado
   (`constitution.md` → `spec.md` → `plan.md` → `tasks.md`), no padrão do
   [GitHub Spec Kit](https://github.com/github/spec-kit).
2. **Loop Engineering** — em vez de você fazer prompt tarefa por tarefa, um loop
   autônomo (padrão Ralph) executa o backlog história por história, com contexto
   limpo a cada iteração, verificação obrigatória e estado persistido em git.

O resultado: você escreve a spec, aperta o play e revisa PRs — não conversas.

---

## Arquitetura em 3 camadas

```
┌─────────────────────────────────────────────────────────────┐
│  CAMADA 1 · INTENT HARNESS (compatível com Spec Kit)        │
│  .specify/memory/constitution.md   ← regras inegociáveis    │
│  specs/NNN-feature/spec.md         ← o QUÊ e POR QUÊ (EARS) │
│  specs/NNN-feature/plan.md         ← o COMO técnico         │
│  specs/NNN-feature/tasks.md        ← decomposição executável│
│  loop/prd.json                     ← backlog p/ máquina     │
│  docs/adr/                         ← decisões (o "porquê")  │
├─────────────────────────────────────────────────────────────┤
│  CAMADA 2 · LOOP RUNTIME (padrão Ralph)                     │
│  loop/ralph.sh          ← o loop: builder → gates → verifier│
│  loop/PROMPT_BUILD.md   ← alma do agente Builder            │
│  loop/PROMPT_VERIFY.md  ← alma do agente Verifier           │
│  loop/gates.sh          ← backpressure: lint, test, build   │
├─────────────────────────────────────────────────────────────┤
│  CAMADA 3 · ESTADO & TELEMETRIA                             │
│  git (commits atômicos)  ← memória durável do progresso     │
│  state/progress.md       ← aprendizados entre iterações     │
│  state/metrics.csv       ← tokens/iteração → HDE            │
└─────────────────────────────────────────────────────────────┘
```

Leia `ARCHITECTURE.md` para o detalhamento completo (decisões, trade-offs,
escalabilidade com git worktrees e o loop de feedback Intent→Spec / Spec→Impl).

---

## Quickstart (10 minutos)

### Passo 0 — Pré-requisitos
- [Claude Code](https://docs.claude.com/en/docs/claude-code) instalado e autenticado
- `git`, `jq` e `bash`
- (Opcional, recomendado) [Spec Kit CLI](https://github.com/github/spec-kit):
  `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git`

### Passo 1 — Clonar este template
```bash
cp -r specloop meu-projeto && cd meu-projeto && git init && git add -A && git commit -m "chore: bootstrap SpecLoop"
```

### Passo 2 — (Opcional) Integrar o Spec Kit por cima
```bash
specify init . --force --integration claude
```
Isso instala os slash commands `/speckit.*` no `.claude/commands/`. O SpecLoop foi
desenhado para conviver com eles: a `constitution.md` fica no mesmo lugar
(`.specify/memory/`) e o diretório `specs/NNN-feature/` segue a mesma convenção.

### Passo 3 — Escrever a constituição
Abra o Claude Code e rode:
```
/speckit.constitution   (se instalou o Spec Kit)
```
Ou edite manualmente `.specify/memory/constitution.md` — já vem com 10 regras
de exemplo comentadas. **Regra de ouro: 5 a 10 regras, todas verificáveis.**

### Passo 4 — Especificar a primeira feature
```
/speckit.specify  →  /speckit.clarify  →  /speckit.plan  →  /speckit.tasks
```
Ou copie `specs/001-exemplo-todo-api/` como referência de formato (EARS incluso).
Depois, transcreva as histórias para `loop/prd.json` (cada história = um item
com `id`, `title`, `acceptance` e `passes: false`).

### Passo 5 — Rodar o loop
```bash
./loop/ralph.sh            # roda até completar ou atingir MAX_ITERATIONS
./loop/ralph.sh --dry-run  # mostra o que faria, sem chamar o agente
```

### Passo 6 — Revisar
```bash
git log --oneline          # commits atômicos por história
cat state/progress.md      # o que o loop aprendeu
cat loop/prd.json | jq '.userStories[] | {id, passes}'
```

---

## Os 5 blocos do loop (e onde cada um mora)

| Bloco | Função | Arquivo |
|---|---|---|
| 1. Fonte de trabalho | O que fazer a seguir | `loop/prd.json` (derivado de `specs/`) |
| 2. Executor | Quem faz | Claude Code via `loop/PROMPT_BUILD.md` |
| 3. Verificador | "Pronto" significa algo | `loop/gates.sh` + `loop/PROMPT_VERIFY.md` |
| 4. Estado | Memória fora do contexto | git + `state/progress.md` |
| 5. Travas | Não explodir custo/risco | `MAX_ITERATIONS`, timeout, circuit breaker no `ralph.sh` |

---

## Regras de segurança (leia antes de rodar sem supervisão)

1. **Nunca** rode o loop com credenciais de produção no ambiente.
2. Comece com `MAX_ITERATIONS=5` e aumente conforme a confiança.
3. O loop só encerra com sucesso quando o Builder emite `<promise>COMPLETE</promise>`
   **e** todos os gates passam — "pronto" é uma alegação; os gates são a prova.
4. Revise TODO commit. Dívida de compreensão cresce mais rápido que o código.
5. Um bug que passou pelos gates é feedback sobre o sistema: registre em
   `state/progress.md` se foi gap Spec→Implementação (melhore os gates) ou
   Intent→Spec (melhore a spec/clarify).

## Escalando (quando uma feature virar dez)

- **Paralelismo**: uma feature = uma branch = um `git worktree`. Rode um
  `ralph.sh` por worktree; os arquivos nunca colidem. Ver `ARCHITECTURE.md §5`.
- **Brownfield**: use `/speckit.converge` para reconciliar codebase × spec e
  gerar as tasks restantes — ele é, na prática, uma iteração de loop manual.
- **Métricas**: `state/metrics.csv` acumula tokens por iteração. HDE =
  custo em tokens (R$) ÷ custo/hora do dev (R$) → minutos-equivalentes.

## Estrutura de diretórios

```
specloop/
├── README.md                        ← você está aqui
├── ARCHITECTURE.md                  ← arquitetura detalhada e decisões
├── CLAUDE.md                        ← memória do Claude Code (leia!)
├── .specify/memory/constitution.md  ← regras inegociáveis
├── specs/001-exemplo-todo-api/      ← feature de exemplo (spec/plan/tasks)
├── docs/adr/                        ← ADRs: template, índice e 3 exemplos
├── loop/
│   ├── ralph.sh                     ← o loop
│   ├── gates.sh                     ← verificação determinística
│   ├── PROMPT_BUILD.md              ← agente Builder
│   ├── PROMPT_VERIFY.md             ← agente Verifier
│   └── prd.json                     ← backlog executável
├── .claude/commands/                ← slash commands utilitários
└── state/                           ← progress.md + metrics.csv
```

---

## ADRs — a memória do "porquê" (docs/adr/)

Um **Architecture Decision Record (ADR)** captura UMA decisão arquitetural
significativa no momento em que foi tomada: contexto, decisão, alternativas
rejeitadas e consequências aceitas. Formato proposto por Michael Nygard (2011);
o template deste projeto segue o estilo **MADR** compacto.

Por que o SpecLoop precisa disso: o loop roda com **contexto limpo por
iteração** (força do padrão Ralph), então o Builder acorda amnésico — e um
agente sem memória de decisões tende a *re-decidir* o já decidido (ex.: trocar
o store em memória por SQLite na iteração 14 porque "parece melhor"). O ADR é
a casa permanente dessas decisões.

Regras de operação (detalhes em `docs/adr/README.md`):

- **Imutável**: ADR aceito nunca é editado — cria-se um novo que o substitui
  (`Status: substituído por ADR-NNNN`). A trilha histórica é o valor.
- **Ciclo de vida**: `proposto → aceito → (descontinuado | substituído)`.
  **Agentes propõem; humanos aceitam** (governança na constitution).
- **Hierarquia**: ADR aceito fica abaixo da constituição e acima da spec.
  Conflito spec × ADR → o loop BLOQUEIA e chama humano.
- **Calibragem**: ADR só para decisão **cara de reverter ou transversal a
  features** (stack, contratos, persistência, padrões de erro). Decisão local
  de feature mora no `plan.md`; nome de variável não gera ADR.
- **Integração no loop**: o Builder lê o índice antes de agir (progressive
  disclosure), o Verifier reprova diff que contradiz ADR aceito, e o
  `gates.sh` valida o formato (`adr-lint`) e avisa sobre ADRs pendentes.
- **Promoção da memória**: `state/progress.md` (tático) → destila → `docs/adr/`
  (decisões) → promove → `constitution.md` (só regra universal verificável).
  Expurgo é destilação, não deleção.

Exemplos incluídos: ADR-0001 (aceito), ADR-0002 (substituído) e ADR-0003
(aceito, substitui o 0002) — leia os três em sequência para ver o ciclo completo.

---

## Referências bibliográficas (ABNT NBR 6023)

COBUSGREYLING. **loop-engineering: practical patterns, starters & CLI tools for loop engineering with AI coding agents**. GitHub, [*S. l.*], 2026. Disponível em: https://github.com/cobusgreyling/loop-engineering. Acesso em: 11 jul. 2026.

GITHUB. **spec-kit: toolkit to help you get started with Spec-Driven Development**. GitHub, [*S. l.*], 2026. Disponível em: https://github.com/github/spec-kit. Acesso em: 11 jul. 2026.

HUNTLEY, Geoffrey. **Everything is a ralph loop**. [*S. l.*], 17 jan. 2026. Disponível em: https://ghuntley.com/loop/. Acesso em: 11 jul. 2026.

HUNTLEY, Geoffrey. **Ralph Wiggum as a "software engineer"**. [*S. l.*], 14 jul. 2025. Disponível em: https://ghuntley.com/ralph/. Acesso em: 11 jul. 2026.

KILO. **What is loop engineering? AI feedback loops**. [*S. l.*], 2026. Disponível em: https://kilo.ai/articles/what-is-loop-engineering. Acesso em: 11 jul. 2026.

LANGCHAIN. **The art of loop engineering**. [*S. l.*], jun. 2026. Disponível em: https://www.langchain.com/blog/the-art-of-loop-engineering. Acesso em: 11 jul. 2026.

MADR. **Markdown Architectural Decision Records**. [*S. l.*], [2018-2026]. Disponível em: https://adr.github.io/madr/. Acesso em: 11 jul. 2026.

MIKEYOBRIEN. **ralph-orchestrator: an improved implementation of the Ralph Wiggum technique for autonomous AI agent orchestration**. GitHub, [*S. l.*], 2026. Disponível em: https://github.com/mikeyobrien/ralph-orchestrator. Acesso em: 11 jul. 2026.

MINDSTUDIO. **What is loop engineering? The new meta for AI coding agents**. [*S. l.*], jun. 2026. Disponível em: https://www.mindstudio.ai/blog/what-is-loop-engineering-ai-coding-agents. Acesso em: 11 jul. 2026.

NYGARD, Michael. **Documenting architecture decisions**. Cognitect Blog, [*S. l.*], 15 nov. 2011. Disponível em: https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions. Acesso em: 11 jul. 2026.

OSMANI, Addy. **Loop engineering**. O'Reilly Radar, [*S. l.*], jun. 2026. Disponível em: https://www.oreilly.com/radar/loop-engineering/. Acesso em: 11 jul. 2026.

SNARKTANK. **ralph: an autonomous AI agent loop that runs repeatedly until all PRD items are complete**. GitHub, [*S. l.*], 2026. Disponível em: https://github.com/snarktank/ralph. Acesso em: 11 jul. 2026.

TOSEA.AI. **What is loop engineering? A complete guide from prompt to harness engineering (2026)**. [*S. l.*], jun. 2026. Disponível em: https://tosea.ai/blog/loop-engineering-ai-agents-complete-guide-2026. Acesso em: 11 jul. 2026.

VERCEL LABS. **ralph-loop-agent: continuous autonomy for the AI SDK**. GitHub, [*S. l.*], 2026. Disponível em: https://github.com/vercel-labs/ralph-loop-agent. Acesso em: 11 jul. 2026.

WATERS, John K. **Loop engineering emerges as developers put AI coding agents on repeat**. ADTmag, [*S. l.*], 1 jul. 2026. Disponível em: https://adtmag.com/articles/2026/07/01/loop-engineering-emerges-as-developers-put-ai-coding-agents-on-repeat.aspx. Acesso em: 11 jul. 2026.
