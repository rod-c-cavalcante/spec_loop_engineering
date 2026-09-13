# PLAN 002 — Fortalecimento v4.0

> Traduz o QUÊ (spec 002) em COMO. Esta feature altera o próprio template,
> então "stack" aqui é: bash (gates existentes) + Python 3 (consistente com
> `loop/metrics_report.py` e `loop/hde_report.py`, que já usam só stdlib).

## Stack e decisões

| Decisão | Escolha | Justificativa (2 linhas máx.) |
|---|---|---|
| Linguagem dos scripts novos | Python 3, só stdlib | Consistente com `metrics_report.py`/`hde_report.py`; evita dependência nova (constitution §7) |
| Estratégia de mutação (`mutar.py`) | 3 operadores mínimos: negação de condição (`if x` → `if not x`), troca de relacional (`<`→`>=` etc.), remoção de `await` | Cobre as classes de bug citadas nas retros (DELETE sem await, condição de corrida, comparação errada) sem construir um framework completo de mutation testing |
| Restauração de mutação | Backup em memória do conteúdo original antes de escrever; `try/finally` (Python) garante restauração mesmo com `SIGTERM`/timeout externo | Resposta direta ao "susto" da retro (RETROSPECTIVA-005-006.md §5, ação 6: timeout deixou arquivo mutado) — nunca usar `git checkout` (RETROSPECTIVA.md §3.5) |
| Detecção de árvore mutada (`verificar.py`) | `git diff --stat` (ou hash de `git status --porcelain` + `git diff`) antes/depois da chamada a `gates.sh` | Já existe precedente: `preflight.sh` usa `git status --porcelain` para "tree limpo"; reaproveita o mesmo primitivo git em vez de inventar novo |
| Detecção de arquivos tocados (lints novos) | `git diff --name-only` contra a branch base (mesmo padrão do `mock-lint`/`adr-lint`/`lgpd-lint` já em `gates.sh`, que usam `git grep`) | Zero dependência nova; mesma superfície de comando que os gates existentes já usam |
| Onde os lints novos entram | Dentro da seção "Gates universais" de `gates.sh` (L0), ao lado de `mock-lint`/`lgpd-lint`/`adr-lint` | Mantém um único arquivo como fonte de verdade dos gates determinísticos (docs/DEVOPS.md: "uma única fonte de verdade de pronto") |
| Escopo do mutation testing | Só histórias `risk:high` (via novo campo opcional `mutationRequired: true`/implícito quando `risk:high`), não 100% do código | Retro (RETROSPECTIVA-005-006.md §2.2) mostra que suíte lenta gera pressão para burlar disciplina; mutation testing é caro — aplicar onde bug grave concentra (mesma lógica do campo `risk` existente) |

## Estrutura de arquivos

```
loop/
├── mutar.py              # novo: mutation testing pontual com restauração segura
├── verificar.py           # novo: ponto único de veredito (wrapper de gates.sh)
├── ralph.sh                # editado: RF-05 (fix do pipe no circuit breaker)
├── gates.sh                # editado: 4 lints novos (RF-06..RF-08, RF-13)
├── preflight.sh             # editado: RF-12 (prd-lint de ordenação por risco)
├── smoke.sh                 # editado: RF-09 (rebuild forçado por Dockerfile/infra)
├── PROMPT_VERIFY.md         # editado: RF-14 (checklist generalizado)
└── tests/
    ├── test_mutar.py       # pytest: prova RF-01, RF-02
    └── test_verificar.py    # pytest: prova RF-03, RF-04

scripts/
└── setup-branch-protection.sh   # novo: RF-11, usa gh CLI, suporta --dry-run

docs/adr/
├── 0006-mutation-testing-obrigatorio-risk-high.md      # proposto
├── 0007-verifier-obrigatorio-em-risk-high.md            # proposto
└── 0008-branch-protection-como-codigo.md                # proposto

specs/002-fortalecimento-v4/
├── proposta-constituicao.md   # diff proposto para constitution.md (não aplicado)
└── (este spec.md, plan.md, tasks.md)
```

## Contratos

- `loop/mutar.py --file <path> --line <N> --operator <negacao|relacional|await> [--scope <e2eScope>] [--timeout <s>]`
  → exit 0 = mutação morta (teste pegou); exit 1 = mutação sobreviveu (achado,
  vira correção de teste, constitution futura regra "mutação que não mata é
  achado"); exit 2 = erro de uso/arquivo não encontrado. Sempre restaura o
  arquivo antes de sair, em qualquer um dos três casos.
- `loop/verificar.py --story <ID> [--level 0|1|2]` → propaga o exit code de
  `gates.sh`, exceto quando a árvore mudou durante a corrida (força exit 9,
  código reservado e documentado no próprio script) ou quando o `e2eScope`
  declarado não bate com nenhum teste (exit 8).
- `scripts/setup-branch-protection.sh [--dry-run]` → sem `--dry-run`, chama
  `gh api` para exigir os checks `gates-l0` e `gates-l2`; com `--dry-run`,
  imprime a chamada que faria e sai 0 sem tocar o remoto.

## Riscos e mitigação

- `mutar.py`/`verificar.py` mexem em arquivos do próprio `loop/` que os
  gates dependem — testar primeiro em cópia isolada (`tests/fixtures/`) antes
  de rodar contra o `loop/` real, para não travar o próprio gate que os prova.
- RF-11 (branch protection) não é testável por gate local — mitigação:
  `--dry-run` obrigatório no critério de pronto dessa história, e o script
  fica documentado em `docs/DEVOPS.md` como passo manual de setup por repo.
- Lints novos (RF-06/07/08/13) são heurísticas — risco de falso-negativo
  aceito e documentado na spec ("Pendências conhecidas"), mesmo padrão do
  `mock-lint` existente.
