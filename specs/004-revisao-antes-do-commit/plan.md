# PLAN 004 — Revisão antes do commit com correção automática

> Traduz o QUÊ (spec 004) em COMO. Stack: bash (`loop/ralph.sh`) + pytest
> (stdlib) para os testes; nenhuma dependência nova (constituição §7).

## Stack e decisões

| Decisão | Escolha | Justificativa (2 linhas máx.) |
|---|---|---|
| Quem commita | `ralph.sh`, depois do APROVADO | Único jeito mecânico de garantir "revisão antes do commit"; pedir ao Builder seria texto (constituição §12) |
| Canal Verifier → Builder | Arquivo `state/review.md` | Estado em arquivo, contexto limpo por iteração (D1); sem agente falando com agente (D3) |
| Como ler o veredito | `grep` de `VEREDITO: APROVADO\|REPROVADO` na saída gravada em arquivo | Mesmo cuidado do RF-05 da spec 002: nunca ler resultado por pipe; ausência de veredito para o loop |
| Ponto fixo da auditoria | `HEAD` no início da história, guardado pelo loop | Cobre todas as rodadas de retrabalho e tolera Builder que commitou; reusa `loop/diff_base.py` (spec 003) |
| Alcance | `risk:high` sempre + `VERIFY_RISKS` (padrão `high normal`) | `low` segue dispensado (cabeçalho do `ralph.sh`); custo fica ajustável por variável |
| Teto de retrabalho | `MAX_REWORK=2`, exit 7 | Mesmo espírito do circuit breaker: parar e chamar humano em vez de girar |
| Arquivos transitórios | `.gitignore` ganha lock, saídas e `review.md` | O loop passa a usar `git add -A`; sem isso commitaria lixo de execução |
| ADR | ADR-0009 `proposto` | Muda quem commita e o protocolo do loop — transversal |

## Estrutura de arquivos

```
loop/
├── ralph.sh               # editado: RF-01..RF-08
├── PROMPT_BUILD.md        # editado: RF-09
├── PROMPT_VERIFY.md       # editado: lê STORY/BASE injetados pelo loop
└── tests/
    └── test_ralph_revisao.py   # ralph.sh real + Builder/Verifier/gates falsos
.gitignore                 # editado: transitórios de state/
docs/adr/0009-…md          # novo, proposto (+ índice)
CLAUDE.md, ARCHITECTURE.md, README.md   # protocolo do loop atualizado
```

## Contratos

- Variáveis novas de `ralph.sh`: `VERIFY_CMD` (padrão = `AGENT_CMD`),
  `VERIFY_RISKS` (padrão `high normal`), `MAX_REWORK` (padrão 2).
- Códigos de saída novos: 7 = teto de retrabalho; 8 = veredito ilegível.
- O loop anexa ao `PROMPT_VERIFY.md` as linhas `STORY=<id>` e `BASE=<sha>`.
- `state/review.md`: cabeçalho com história e tentativa + saída do Verifier.
- `state/.commit_msg`: uma mensagem de commit, escrita pelo Builder.

## Verificação

- `python -m pytest -q loop/tests/test_ralph_revisao.py`: roda o `ralph.sh`
  real num repositório git temporário; só o LLM (Builder/Verifier) e os gates
  do produto são falsos — fronteira do sistema (constituição §11).
- `./loop/gates.sh` verde.
- Pendente (manual): uma corrida real com Claude em história de exemplo.
