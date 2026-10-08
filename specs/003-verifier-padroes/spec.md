# SPEC 003 — Verifier: eixo de padrões (smells) e ponto fixo de diff

> Feature de tooling: altera o próprio SpecLoop (`loop/`, `.claude/commands/`),
> não um produto de negócio. Origem: análise do skill `code-review` de
> mattpocock/skills (docs/engineering/code-review.md), pedida pelo humano em
> 2026-10-07. O skill NÃO é instalado; três ideias dele são absorvidas.

## Contexto e motivação

O skill revisa um diff em dois eixos (Standards e Spec) a partir de um ponto
fixo. O eixo Spec já é coberto, com mais rigor, pelo `loop/PROMPT_VERIFY.md`.
A comparação expôs três lacunas reais do Verifier:

1. Nenhum item do checklist olha manutenibilidade. A constituição §4 (menor
   mudança) e §9 (sem abstração especulativa) só são alcançadas pelo item 4
   genérico ("alguma regra violada?").
2. O Verifier audita só `git show HEAD`. História com mais de um commit, ou
   com commit de correção após um REPROVADO, fica parcialmente fora da
   auditoria.
3. `/verify` roda na sessão corrente; se for a do Builder, perde-se a
   independência que motivou o ADR-0007.

## Escopo (in)

- Um script (`loop/diff_base.py`) que resolve o ponto fixo e entrega o diff
  auditável, falhando cedo quando o ref não existe ou não há nada a auditar.
- Novo item "Padrões e smells" no checklist do `loop/PROMPT_VERIFY.md`, com
  bloco `OBSERVAÇÕES` no formato de saída.
- `/verify` aceita um ref base opcional e recomenda sessão nova.
- Correção da contagem de regras da constituição citada no checklist (10 → 13).

## Requisitos (EARS)

### RF-01 — Ref base inexistente falha antes da auditoria (Unwanted behavior)
IF o ref base passado a `loop/diff_base.py` não resolve para um commit, THEN
THE SYSTEM SHALL sair com código 2 e mensagem citando o ref, sem emitir diff.

### RF-02 — Nada a auditar falha antes da auditoria (Unwanted behavior)
IF não há diferença entre o ref base e a árvore de trabalho e não há arquivo
não rastreado, THEN THE SYSTEM SHALL sair com código 3 e mensagem explícita.

### RF-03 — Diff cobre do ponto fixo até a árvore de trabalho (Event-driven)
WHEN `loop/diff_base.py --base <ref>` é chamado com um ref válido, THE SYSTEM
SHALL emitir em stdout o diff de `<ref>` até a árvore de trabalho (todos os
commits posteriores ao ref mais mudanças não commitadas) e sair com código 0.

### RF-04 — Arquivo não rastreado é anunciado, não omitido (Event-driven)
WHEN existem arquivos não rastreados (fora do `.gitignore`), THE SYSTEM SHALL
listá-los em stderr, pois não aparecem no diff.

### RF-05 — Base padrão preserva o comportamento atual (Ubiquitous)
THE SYSTEM SHALL usar `HEAD~1` como base quando `--base` é omitido.

### RF-06 — Checklist do Verifier cobre padrões e smells (Ubiquitous)
THE SYSTEM SHALL declarar em `loop/PROMPT_VERIFY.md` um item de checklist
"Padrões e smells" que: (a) lista os doze smells de referência; (b) exige que
cada achado cite a regra violada ou o trecho do diff; (c) classifica achado
como OBSERVAÇÃO não bloqueante, exceto quando corresponde à constituição §4 ou
§9, caso em que reprova; (d) só conta duplicação a partir da terceira
ocorrência real (constituição §9).

### RF-07 — Veredito continua único (Ubiquitous)
THE SYSTEM SHALL manter um único `VEREDITO: APROVADO | REPROVADO` por auditoria
e o formato atual de `state/verdicts.csv`; observações não geram linha própria.

### RF-08 — `/verify` aceita ponto fixo (Event-driven)
WHEN `/verify <ref>` é invocado, THE SYSTEM SHALL auditar o diff produzido por
`loop/diff_base.py --base <ref>`; sem argumento, usa a base padrão.

## Out of scope (tão importante quanto o escopo)

- Instalar o skill `code-review` ou qualquer outro de mattpocock/skills
  (`implement`, `pr`, `retro`): colidem com o `/code-review` nativo, com o
  Builder e com a constituição §10.
- Subagentes por eixo (ARCHITECTURE.md D3: monolítico, não multi-agente).
- Gate determinístico de smells em `gates.sh` (smell é julgamento —
  constituição §12 mantém julgamento como texto).
- Tornar o Verifier obrigatório fora de `risk:high` (ADR-0007, alternativas).
- Mudar o schema de `state/verdicts.csv` ou o bloqueio de `loop/ralph.sh`.
- Aceitar, editar ou substituir ADRs.

## Pendências conhecidas

- RF-06 e RF-07 são reforço documental do prompt, sem teste automatizado —
  mesmo tratamento do RF-14 da spec 002. A prova é uma auditoria `/verify`
  real sobre um diff com smell plantado.
- RF-08 depende de o agente seguir o comando; o que é mecânico (RF-01 a RF-05)
  está no script e testado.
- A recomendação de sessão nova para `/verify` é texto: nada impede rodá-lo na
  sessão do Builder.
- `loop/ralph.sh` ainda sugere `git show HEAD` no checkpoint; não alterado
  aqui (fora do escopo desta história).

## Dados pessoais (LGPD)

- **Dados tocados**: nenhum. Esta feature altera tooling de desenvolvimento
  (`loop/`, `.claude/`, `docs`) — não introduz coleta, log ou processamento
  de dado pessoal.
- **Base legal**: n/a. | **Retenção**: n/a.
- **Minimização**: n/a.

## Critérios de pronto (definition of done)

- [ ] RF-01 a RF-05 cobertos por teste em `loop/tests/test_diff_base.py`,
      visto falhando antes da implementação
- [ ] `./loop/gates.sh` retorna 0
- [ ] `state/verdicts.csv` e `loop/metrics_report.py` inalterados
- [ ] Commits referenciam esta spec
