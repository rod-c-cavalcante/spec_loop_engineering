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

*Baseado nos padrões: GitHub Spec Kit (SDD), Ralph loop de Geoffrey Huntley
(loop engineering), Builder/Verifier (SDD com dois agentes) e nos 3 loops de
Andrew Ng (código agêntico, feedback do dev, feedback externo).*
