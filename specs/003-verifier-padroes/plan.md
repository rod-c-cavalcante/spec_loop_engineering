# PLAN 003 — Verifier: padrões (smells) e ponto fixo

> Traduz o QUÊ (spec 003) em COMO. Stack: Python 3 só stdlib (igual a
> `loop/mutar.py` e `loop/verificar.py`) + edição de prompts em Markdown.

## Stack e decisões

| Decisão | Escolha | Justificativa (2 linhas máx.) |
|---|---|---|
| Onde mora a validação do ponto fixo | Script `loop/diff_base.py`, não instrução no prompt | Ref inválido e diff vazio são determinísticos — constituição §12 pede código, não texto |
| Alcance do diff | `git diff <base>` (base → árvore de trabalho) | Cobre vários commits e trabalho não commitado; o `/verify` já foi usado sobre diff não commitado (progress.md, 2026-09-13) |
| Arquivos não rastreados | Listados em stderr; contam como "há o que auditar" | `git diff` não os mostra; omitir em silêncio recriaria a lacuna que a spec fecha |
| Smells: bloqueio ou observação | Observação, exceto se cair em §4 ou §9 | Mantém o veredito único exigido por `ralph.sh` (ADR-0007 proposto) sem criar regra nova de reprovação |
| Um agente ou dois | Um Verifier, um item novo no checklist | ARCHITECTURE.md D3; evita dobrar o custo já ponderado em D2 |
| Dependências novas | Nenhuma | Constituição §7 |
| ADR | Nenhum | Mudança de checklist, como o RF-14 da spec 002; não é transversal nem cara de reverter |

## Estrutura de arquivos

```
loop/
├── diff_base.py            # novo: RF-01..RF-05
├── PROMPT_VERIFY.md        # editado: RF-06, RF-07, insumo 5, "10 regras" → 13
└── tests/
    └── test_diff_base.py   # pytest com repositório git real em tmp_path
.claude/commands/verify.md  # editado: RF-08
ARCHITECTURE.md             # editado: D2 cita o novo alcance do Verifier
README.md                   # editado: menção ao ponto fixo do /verify
```

## Contratos

- `loop/diff_base.py [--base <ref>]` → stdout: diff; stderr: avisos.
  exit 0 = há diff; exit 2 = ref não resolve; exit 3 = nada a auditar.

## Verificação

- `python -m pytest -q loop/tests/test_diff_base.py` (git real, sem mock).
- `./loop/gates.sh` verde.
- Manual: `/verify HEAD~1` em sessão nova sobre um diff com abstração
  especulativa plantada deve sair REPROVADO citando §9; com nome ruim apenas,
  APROVADO com OBSERVAÇÕES.
