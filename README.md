# SpecLoop v4.0 — SDD + Loop Engineering para Claude Code

> **A spec é o árbitro. O loop é o motor. Os gates são a prova.
> Você é o engenheiro que projeta os três.**

Template de projeto e material didático que une **Spec-Driven Development**
(GitHub Spec Kit), **Loop Engineering** (padrão Ralph endurecido por produção),
**DevOps** (CI = os mesmos gates), **FinOps** (custo visível por desenho) e
**LGPD** (privacy by design como gate, não como cartaz).

**Para quem é**: estudantes de engenharia com IA (trilha de aprendizado
abaixo) e fábricas de software (padrões de governança, métricas e compliance
prontos para operar em escala).

---

## Índice

1. [A ideia em 60 segundos](#a-ideia-em-60-segundos)
2. [Arquitetura em 3 camadas](#arquitetura-em-3-camadas)
3. [Quickstart](#quickstart-10-minutos)
4. [Trilha de aprendizado (estudantes)](#trilha-de-aprendizado)
5. [O loop em detalhe](#os-5-blocos-do-loop)
6. [ADRs — a memória do "porquê"](#adrs--a-memória-do-porquê-docsadr)
7. [Novidades v4.0](#novidades-v40)
8. [Painel de métricas (4 famílias)](#painel-de-métricas)
9. [DevOps · FinOps · LGPD](#devops--finops--lgpd)
10. [Segurança e escala](#regras-de-segurança)
11. [FAQ](#faq)
12. [Glossário](#glossário)
13. [Referências (ABNT)](#referências-bibliográficas-abnt-nbr-6023)

---

## A ideia em 60 segundos

No **prompt engineering**, você dirige o carro: cada curva exige sua mão no
volante. No **loop engineering**, você projeta o piloto automático e o painel:
define o destino (**spec** com critérios EARS), os sensores (**gates**:
testes, lint, build), o critério de chegada (**verificação** determinística +
agêntica) e as travas (**limites** de iteração, custo e risco). Um loop
(`ralph.sh`) executa o backlog história por história, com contexto limpo a
cada iteração e memória em git + arquivos — e você revisa PRs, não conversas.

O que diferencia este template: **cada mecanismo foi financiado por uma falha
real de produção** — duas retrospectivas, 14 features no total
(`ARCHITECTURE.md §7`). Nada aqui é especulação; é cicatriz transformada em
código. A v4.0 acrescenta mutation testing, veredito único e um Verifier que
deixou de ser pulável em histórias de risco — ver [Novidades v4.0](#novidades-v40).

## Arquitetura em 3 camadas

```
┌─────────────────────────────────────────────────────────────┐
│  CAMADA 1 · INTENT HARNESS (compatível com Spec Kit)        │
│  .specify/memory/constitution.md   ← 13 regras verificáveis │
│  specs/NNN-feature/spec.md         ← o QUÊ (EARS) + LGPD    │
│  specs/NNN-feature/plan.md         ← o COMO técnico         │
│  docs/adr/                         ← decisões (o PORQUÊ)    │
│  loop/prd.json                     ← backlog p/ máquina     │
├─────────────────────────────────────────────────────────────┤
│  CAMADA 2 · LOOP RUNTIME (padrão Ralph endurecido)          │
│  loop/preflight.sh  ← lock, tree limpo, consistência        │
│  loop/ralph.sh      ← o loop: risk, checkpoint, breaker     │
│  loop/gates.sh      ← prova estratificada L0/L1/L2          │
│  loop/verificar.py  ← veredito único, anula se árvore mudar │
│  loop/mutar.py      ← mutation testing pontual (risk:high)  │
│  loop/smoke.sh      ← rebuild limpo + HTTP real (L2)        │
│  loop/PROMPT_*.md   ← almas dos agentes Builder e Verifier  │
├─────────────────────────────────────────────────────────────┤
│  CAMADA 3 · ESTADO, MÉTRICAS & ENTREGA                      │
│  git + state/progress.md           ← memória durável        │
│  state/metrics*.csv + verdicts.csv ← painel de 4 famílias   │
│  .github/workflows/ci.yml          ← CI = os mesmos gates   │
│  loop/metrics_report.py            ← comenta o painel no PR │
└─────────────────────────────────────────────────────────────┘
```

Detalhamento completo, decisões e trade-offs: **`ARCHITECTURE.md`**.

## Quickstart (10 minutos)

```bash
# 0. Pré-requisitos: Claude Code autenticado, git, jq, python3, bash
# 1. Clonar e inicializar
cp -r specloop meu-projeto && cd meu-projeto
git init && git add -A && git commit -m "chore: bootstrap SpecLoop v4"
git config core.hooksPath githooks          # gates L0 em todo commit humano

# 2. (Recomendado) Spec Kit por cima — mesmas convenções, zero conflito
specify init . --force --integration claude # instala /speckit.* no Claude Code

# 3. Escrever a constituição e a primeira spec
#    /speckit.constitution → /speckit.specify → clarify → plan → tasks
#    (ou copie o formato de specs/001-exemplo-todo-api — EARS + seção LGPD)
#    Transcreva as tasks para loop/prd.json (id, acceptance, risk, e2eScope)

# 4. Rodar
./loop/ralph.sh --dry-run   # plano: id · risk · e2eScope, sem executar
./loop/ralph.sh             # preflight → loop → gates L1 → S-RELEASE (L2)

# 5. Revisar e medir
git log --oneline && cat state/progress.md
python3 loop/metrics_report.py             # painel das 4 famílias
```

O loop **para sozinho** em três situações desenhadas: história `risk: high`
concluída (checkpoint humano), mesma falha 3x (circuit breaker) e bloqueio
reportado pelo agente. Parar é feature, não bug.

## Trilha de aprendizado

Para estudantes — cada nível destrava o seguinte:

- **Nível 0 · Leitor** — leia `README` + `ARCHITECTURE.md`; rode
  `./loop/ralph.sh --dry-run` e explique o plano para alguém.
- **Nível 1 · Especificador** — escreva UMA spec real com 5 requisitos EARS e
  a seção LGPD; passe no lgpd-lint. (A habilidade mais valiosa da era dos
  agentes é articular intenção verificável.)
- **Nível 2 · Operador de loop** — rode o loop na sua spec; sobreviva a um
  circuit breaker lendo as asserções e corrigindo cirurgicamente; leia o
  painel e explique seu FPSR.
- **Nível 3 · Engenheiro de harness** — provoque os 3 gaps de propósito
  (spec ambígua, gate fraco, mock mentiroso) e conserte cada um no lugar
  certo; escreva seu primeiro ADR.
- **Nível 4 · Fábrica** — 2 features em paralelo com git worktrees; branch
  protection + CI; apresente o `metrics_history.csv` como um gerente de
  engenharia apresentaria.

## Os 5 blocos do loop

| Bloco | Função | Arquivo |
|---|---|---|
| 1. Fonte de trabalho | O que fazer a seguir | `loop/prd.json` (de `specs/`) |
| 2. Executor | Quem faz | Claude Code via `loop/PROMPT_BUILD.md` |
| 3. Verificador | "Pronto" é prova, não alegação | `gates.sh` L0/L1/L2 + `smoke.sh` + Verifier |
| 4. Estado | Memória fora do contexto | git + `state/progress.md` + ADRs |
| 5. Travas | Custo/risco sob controle | preflight, MAX_ITERATIONS, breaker, checkpoint por risco |

Uma iteração = contexto limpo → lê estado → 1 história → TDAD → menor mudança
→ gates → registra → commit atômico → morre. O estado sobrevive; o contexto não.

## ADRs — a memória do "porquê" (docs/adr/)

O Builder acorda amnésico a cada iteração (por design) — sem memória de
decisões, ele re-decide o já decidido. ADRs (formato Nygard/MADR) são a casa
permanente: imutáveis (substitui-se, não se edita), com ciclo
`proposto → aceito → substituído` onde **agentes propõem e humanos aceitam**.
ADR aceito fica acima da spec na hierarquia; conflito → loop bloqueia.
Calibragem: só decisão **cara de reverter ou transversal** (o resto é plan.md).
Leia os exemplos 0001–0005 (dois nasceram de incidentes reais de produção).

Caminho de promoção da memória: `progress.md` → destila → **ADR** (julgamento)
ou **código** (lição determinística, §12) → promove → **constituição** (regra
universal). Expurgo é destilação, não deleção.

## Novidades v4.0

Uma segunda rodada de retrospectivas de produção (mais 6 features, mesmo
padrão de arquitetura) motivou `specs/002-fortalecimento-v4/` — comparação
achado a achado contra este template, mecanismo por mecanismo, com auditoria
independente (`/verify`) rodada sobre o diff antes do commit. Mesma regra da
v2: mecanismo, não recomendação; e na dúvida entre documentar e automatizar,
automatize (`ARCHITECTURE.md §7`).

| Melhoria | O que faz | Por quê (achado da retrospectiva) |
|---|---|---|
| `loop/mutar.py` | Mutation testing pontual — nega condição, troca operador relacional, remove `await`; restauração garantida por `try/finally`, **nunca** `git checkout` | 9 mutações em produção externa revelaram 3x suíte verde que não provava nada; um `git checkout` para desfazer mutação já tinha apagado trabalho não commitado numa retro anterior |
| `loop/verificar.py` | Ponto único de veredito: checa cobertura do `e2eScope` **antes** de gastar o gate; anula o veredito se a árvore mudar durante a execução | "Gate impossível de fechar" — um artefato de teste mudando a árvore em pleno L2 custou ~40min de corrida perdida num período real de produção |
| Fix em `ralph.sh` | Exit code do gate nunca mais passa por um pipe (saída vai para arquivo antes de qualquer `tail`/`md5sum`) | Leitura de veredito por cano perdeu o exit code real — o gate tinha reprovado e a leitura dizia zero |
| 4 lints novos em `gates.sh` | `orm-migration-lint`, `infra-assertion-lint`, `crlf-lint` (cobre `.sh` e `.py`), `pendencias-lint` — cada um verificado plantando o defeito real antes de contar como pronto | Divergência ORM↔banco 2x; teste de infra medindo o YAML escrito em vez da saída de `docker compose config`; escrita de arquivo por script convertendo quebra de linha em byte literal — passou verde na 4ª vez |
| Verifier obrigatório em `risk:high` | `ralph.sh` bloqueia (exit 6) história de risco marcada pronta sem veredito `APROVADO` registrado em `state/verdicts.csv` — não pulável por `NO_CHECKPOINT` | Um período inteiro sem auditoria independente teve 4 de 5 falsos-verdes vindos de teste que o próprio autor escreveu e validou |
| `prd-lint` de ordenação por risco | `preflight.sh` bloqueia feature com >10 histórias pendentes sem `risk:high` nos primeiros 30% da ordem do `prd.json` | Feature de 18 histórias adiou o checkpoint humano até perto do fim |
| `scripts/setup-branch-protection.sh` | Branch protection **como código** (`gh` CLI, com `--dry-run`) exigindo `gates-l0` + `gates-l2` antes do merge | PR mesclado 90s depois de aberto, com o L2 ainda rodando — a regra manual só sustentou quando seguida à risca |
| Rebuild forçado por infra | `smoke.sh` ignora `SKIP_REBUILD` quando o diff toca `Dockerfile*`/`infra/**` | `--force-recreate` não reconstrói imagem; 3 rodadas de teste testaram uma imagem velha sem avisar |

**Pendente de decisão humana** — agentes propõem, nunca aceitam: os ADRs
`docs/adr/0006-0008` (status `proposto`) e o diff de constituição em
`specs/002-fortalecimento-v4/proposta-constituicao.md`. Nada disso foi
aplicado automaticamente.

A própria auditoria (`/verify`) desta rodada é o melhor exemplo de por que o
Verifier existe: encontrou 2 defeitos reais antes do commit — uma mutação
que produzia código sintaticamente inválido sem que nenhum teste percebesse
(o teste só checava substring, não sintaxe — gap Spec→Oráculo) e um
`git grep` que não enxergava arquivo de teste ainda não commitado (gap
Spec→Implementação). Os dois ganharam teste de regressão antes do push —
ver `state/verdicts.csv` e `state/progress.md`.

Detalhes completos: `ARCHITECTURE.md` (seção "Candidatos v4.0") e
`specs/002-fortalecimento-v4/{spec,plan,tasks}.md`.

## Painel de métricas

`python3 loop/metrics_report.py` (terminal) · `--md` (PR) · `--snapshot`
(acumula em `state/metrics_history.csv`). A CI comenta o painel em todo PR.

| Família | Mede | Métricas | Contrapeso (anti-Goodhart) |
|---|---|---|---|
| **A. Harness** | qualidade da spec | First-Pass Success Rate; gaps Intent→Spec / Spec→Impl / Spec→Oráculo | FPSR alto + defeitos escapados = gates fracos |
| **B. Loop** | execução | iterações/história; aprovação do Verifier (1ª); retrabalho; autonomia; latência L0/L1/L2 | autonomia alta + retrabalho alto = loop girando à toa |
| **C. FinOps** | economia | custo/feature; custo do retrabalho; HDE (min-equivalentes) | custo baixo + FPSR baixo = economia no lugar errado |
| **D. DORA** | entrega | lead time (git); deploys/semana (git); CFR e MTTR (produção) | lead time menor + CFR maior = custo transferido p/ produção |

Regra de leitura: **termômetro, não meta** (Lei de Goodhart). Nenhuma métrica
isolada vira OKR; decisões usam o par métrica+contrapeso e a tendência no
histórico acumulado.

## DevOps · FinOps · LGPD

- **DevOps (`docs/DEVOPS.md`)** — trunk-based com 1 feature = 1 worktree = 1
  loop; hook de pre-commit; **CI rodando os mesmos gates** (L0 em push, L2 em
  PR — fonte única de "pronto"); branch protection; 12-Factor; deploy = merge;
  incidentes retornam como gaps classificados.
- **FinOps (`docs/FINOPS.md`)** — informar (custo por iteração no CSV),
  otimizar (retrabalho > latência de gate > fatia fina > modelo por risco),
  operar (HDE como unit economics; calibração mensal; circuit breaker como
  mecanismo de orçamento).
- **LGPD (`docs/LGPD.md`)** — privacy by design mecânico: toda spec declara
  `## Dados pessoais (LGPD)` (dados, base legal, retenção, minimização) e o
  **lgpd-lint bloqueia** spec sem análise; PII em log é reprovação do
  Verifier; deleção de dados é sempre `risk: high`; dado sensível (Art. 11)
  → BLOCKED até humano/DPO. A rastreabilidade do SDD vira insumo de RIPD.

## Regras de segurança

1. Nunca rode o loop com credenciais de produção. 2. Comece com
`MAX_ITERATIONS=5`. 3. "Pronto" = promise **E** gates **E** backlog zerado.
4. Revise TODO commit — dívida de compreensão cresce mais rápido que código.
5. Todo bug é feedback: classifique o gap (`[gap:intent-spec]`,
`[gap:spec-impl]`, `[gap:spec-oraculo]`) e conserte o SISTEMA, não só o bug.
6. Paralelismo SÓ via `git worktree` (o preflight torna a colisão impossível
— ADR-0004). 7. Overrides (`ALLOW_DIRTY`, `OVERRIDE_MERGED`, `NO_CHECKPOINT`)
existem para serem usados conscientemente e raramente.

## FAQ

**O loop travou no circuit breaker. E agora?** Leia as asserções que falharam
(`./loop/gates.sh --level 1 --scope @tag`), corrija a MESMA história
cirurgicamente, rode de novo. Não descarte trabalho, não pule história.

**Posso usar outro agente que não o Claude Code?** Sim — `AGENT_CMD` é
configurável; os prompts são markdown puro.

**Por que minha história não roda?** Dependência (`dependsOn`) pendente, ou o
preflight bloqueou (leia a mensagem — ela cita o incidente que a justifica).

**gates.sh verde basta para dar merge?** Não. S-RELEASE (L2 + smoke) verde +
Verifier APROVADO + revisão humana. As 4 provas estão no template de PR. Em
histórias `risk:high`, o Verifier APROVADO deixou de ser recomendação na
v4.0: `ralph.sh` bloqueia (exit 6) sem veredito registrado em
`state/verdicts.csv` — ver [Novidades v4.0](#novidades-v40).

**Specs dão trabalho. Vale a pena?** FPSR responde com números: spec ruim =
FPSR baixo = retrabalho pago em tokens e tempo. A spec é a otimização FinOps
mais barata do sistema.

**Preciso do Spec Kit?** Não, mas ajuda: os slash commands `/speckit.*`
automatizam constitution→specify→plan→tasks e o SpecLoop consome o resultado.

## Glossário

**EARS** formato de requisito verificável (WHEN/IF...THE SYSTEM SHALL) ·
**FPSR** % de histórias verdes na 1ª iteração · **Gap Intent→Spec** a spec
não capturou a intenção · **Gap Spec→Impl** o código divergiu da spec ·
**Gap Spec→Oráculo** os testes não representam a spec (mock que confirma o
bug) · **Gates L0/L1/L2** prova rápida / seletiva / de release · **HDE**
horas-dev equivalentes (custo do loop ÷ custo-hora) · **Harness** o arnês de
intenção (constituição+specs+ADRs) · **Ralph** padrão de loop com contexto
limpo e estado em git · **S-RELEASE** história sintética que prova a feature
inteira (L2) · **TDAD** teste falha antes, passa depois · **Verifier** agente
auditor que aprova/reprova com evidências · **Worktree** checkout paralelo do
mesmo repo (1 por agente).

## Referências bibliográficas (ABNT NBR 6023)

BRASIL. **Lei nº 13.709, de 14 de agosto de 2018 (Lei Geral de Proteção de Dados Pessoais — LGPD)**. Brasília, DF: Presidência da República, 2018. Disponível em: https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm. Acesso em: 13 jul. 2026.

COBUSGREYLING. **loop-engineering: practical patterns, starters & CLI tools for loop engineering with AI coding agents**. GitHub, [*S. l.*], 2026. Disponível em: https://github.com/cobusgreyling/loop-engineering. Acesso em: 11 jul. 2026.

DORA. **DORA research: metrics for software delivery performance**. [*S. l.*], 2026. Disponível em: https://dora.dev. Acesso em: 13 jul. 2026.

FINOPS FOUNDATION. **What is FinOps?** [*S. l.*], 2026. Disponível em: https://www.finops.org/introduction/what-is-finops/. Acesso em: 13 jul. 2026.

FORSGREN, Nicole; HUMBLE, Jez; KIM, Gene. **Accelerate: the science of lean software and DevOps**. Portland: IT Revolution Press, 2018.

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

WATERS, John K. **Loop engineering emerges as developers put AI coding agents on repeat**. ADTmag, [*S. l.*], 1 jul. 2026. Disponível em: https://adtmag.com/articles/2026/07/01/loop-engineering-emerges-as-developers-put-ai-coding-agents-on-repeat.aspx. Acesso em: 13 jul. 2026.

WIGGINS, Adam. **The twelve-factor app**. [*S. l.*], 2017. Disponível em: https://12factor.net/pt_br/. Acesso em: 13 jul. 2026.
