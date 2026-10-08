# PLAN 005 — CI do próprio template

> Stack: bash (`smoke.sh`, `gates.sh`), YAML do GitHub Actions, pytest.

## Stack e decisões

| Decisão | Escolha | Justificativa (2 linhas máx.) |
|---|---|---|
| Como detectar "sem produto" | Ausência dos 5 arquivos-marcadores que `gates.sh`/`smoke.sh` já usam + `BASE_URL` não definida | Determinístico e sem configuração; reusa os mesmos sinais que já decidem quais gates rodam |
| Resultado sem produto | Exit 0 com aviso `⚠ smoke: N/A` | O gate não pode provar o que não existe; vermelho permanente ensina a ignorar o L2 |
| Escape | `SMOKE_REQUIRED=1` força os checks | Produto fora dos marcadores não fica sem smoke por acidente |
| pytest ausente | `gates.sh` reprova | Gate pulado em silêncio é falso-verde (constituição §3) |
| pytest na CI | `actions/setup-python@v5` + `pip install pytest` incondicionais | O Python do sistema no runner recusa `pip install` (PEP 668) |
| Dependências | `pytest` só na CI (já era exigido pelos testes de `loop/tests/`) | Nenhuma dependência nova de produto (constituição §7) |

## Estrutura de arquivos

```
loop/smoke.sh               # editado: RF-01, RF-02
loop/gates.sh               # editado: RF-03
loop/tests/test_smoke.py    # novo
.github/workflows/ci.yml    # editado: RF-04
```

## Verificação

- `python -m pytest -q loop/tests/test_smoke.py`
- `./loop/gates.sh --level 2` local e a corrida de CI do PR #2.
