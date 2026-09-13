# Proposta de diff — `.specify/memory/constitution.md` (v4.0)

> **Não aplicado.** Por regra da própria constituição ("Mudanças nesta
> constituição exigem edição humana explícita — agentes não editam"), este
> documento é uma PROPOSTA de diff para sua leitura e decisão. Aplique
> manualmente (ou peça explicitamente) se aceitar — total ou parcialmente.
> Origem: specs/002-fortalecimento-v4, mecanismos que a spec classifica como
> "regra universal verificável" (item 6 do caminho de promoção em CLAUDE.md),
> não decisão de julgamento local (essas viraram ADR-0006/0007/0008).

## Diff proposto

Adicionar ao final de `.specify/memory/constitution.md`, como nova seção
depois de "Regras adicionadas na v2.0":

```diff
+## Regras propostas na v4.0 (origem: retrospectivas Forja, features 001-006)
+
+14. **Auditoria independente é condição de saída, não recomendação, em
+    risk:high.** Uma história `risk:high` só conta como concluída com
+    veredito `APROVADO` do Verifier registrado em `state/verdicts.csv`
+    (`loop/ralph.sh` bloqueia com exit 6 sem isso — ver ADR-0007). Nasce de
+    um período inteiro sem auditoria independente em que 4 de 5
+    falsos-verdes encontrados eram testes que o próprio autor escreveu e
+    validou.
+
+15. **Toda feature com entrada de UI prova o caminho até a tela, não só a
+    tela.** A spec declara a jornada esperada; ao menos um teste E2E chega
+    ao destino navegando por elementos VISÍVEIS (não rota direta/API). Um
+    caminho sem esse teste deixou 2 CTAs mortos por duas features inteiras,
+    com 136 testes verdes que não notaram.
+
+16. **Feature grande adianta o risco.** Acima de 10 histórias pendentes,
+    ao menos uma `risk:high` precisa estar entre os primeiros 30% da ordem
+    do `prd.json` (preflight bloqueia com prd-lint de ordenação, override
+    consciente `RISK_ORDER_ACK=1`). Nasce de uma feature de 18 histórias
+    que adiou o checkpoint humano até perto do fim.
```

## Por que estas três, e não as outras da spec 002

A spec `002-fortalecimento-v4` cobre 14 requisitos; só estes três viram
proposta de constituição porque são os que atendem ao critério do próprio
`docs/adr/README.md` ("regra universal verificável", não decisão de
julgamento local ou detalhe de implementação):

| Mecanismo da spec 002 | Por que NÃO virou regra de constituição |
|---|---|
| `mutar.py` obrigatório em risk:high (RF-01/02) | Decisão de trade-off custo×benefício, cara de reverter — é ADR (ADR-0006), não regra inegociável |
| `orm-migration-lint`, `infra-assertion-lint`, `crlf-lint` (RF-06/07/08) | Heurísticas de gate com falso-negativo aceito — mecanismo, não princípio; já documentado em `gates.sh` e nas "Pendências conhecidas" da spec |
| `verificar.py` (RF-03/04) | Ferramenta/wrapper, não regra de conduta — o comportamento que importa (árvore não pode mudar durante o gate) já é implícito em "gates são inegociáveis" (princípio 3) |
| Branch protection como código (RF-11) | Configuração de infraestrutura externa (GitHub), não regra que um agente deste repo possa verificar sozinho — é ADR (ADR-0008) |
| Evidência de vermelho (RF-14b) | A própria retro de origem diz que "não é mecanizável hoje" — documentação no `PROMPT_VERIFY.md`, não regra verificável por gate |

## Se aceitar parcialmente

As três regras propostas são independentes entre si — aceitar só a 14 (a
mais diretamente ligada a um falso-verde documentado, RETROSPECTIVA-005-006.md
§4.3) sem as demais é uma divisão razoável, já que o mecanismo de código
correspondente (`ralph.sh` T-013) já está implementado e não depende das
outras duas.
