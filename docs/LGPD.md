# LGPD no SpecLoop — privacy by design como mecanismo, não como cartaz

A Lei nº 13.709/2018 (LGPD) exige, no Art. 46 §2º, que a proteção de dados
seja observada **desde a concepção** (privacy by design). No SpecLoop isso não
é um documento na gaveta: é uma seção obrigatória da spec, validada por gate.

## O mecanismo (3 peças)

1. **Toda spec declara** a seção `## Dados pessoais (LGPD)` com quatro
   respostas: *quais dados pessoais a feature toca* (ou "nenhum"), *base legal*
   (Art. 7º — consentimento, contrato, legítimo interesse etc.), *retenção*
   (por quanto tempo e por quê) e *minimização* (por que não dá para coletar
   menos). Feature que não toca dado pessoal escreve "nenhum" — a declaração
   negativa também é informação auditável.
2. **`gates.sh` (lgpd-lint)** reprova o loop se a spec da feature ativa não
   contém a seção — a spec não avança para código sem a análise feita.
3. **Verifier audita**: dado pessoal em log é reprovação (vazamento por
   observabilidade é a violação mais comum e mais boba); dado coletado além
   do declarado na spec é reprovação (minimização, Art. 6º III).

## O mapa mínimo que estudante e fábrica precisam saber

- **Princípios (Art. 6º)**: finalidade, adequação, necessidade (minimização),
  transparência, segurança, prevenção, não discriminação, responsabilização.
  A seção da spec operacionaliza finalidade + necessidade.
- **Bases legais (Art. 7º)**: toda coleta precisa de UMA base declarada.
  "Porque é útil" não é base legal.
- **Direitos do titular (Art. 18)**: acesso, correção, anonimização,
  portabilidade, eliminação. Traduza em requisitos EARS quando a feature
  tocar dados pessoais (ex.: "WHEN o titular solicita eliminação, THE SYSTEM
  SHALL..."). Deleção de dados é sempre `risk: high` no prd.json.
- **Dados sensíveis (Art. 11)** — saúde, biometria, origem racial, religião,
  vida sexual, política: tratamento restrito; se a feature tocar, pare e
  envolva humano/DPO ANTES do loop (o Builder deve emitir BLOCKED).
- **RIPD/DPIA (Art. 38)**: para tratamento de alto risco, o Relatório de
  Impacto é exigível pela ANPD. A seção LGPD das specs, acumulada, é 80% do
  insumo do relatório — rastreabilidade do SDD virando compliance de graça.
- **Incidentes (Art. 48)**: vazamento com risco relevante deve ser comunicado
  à ANPD e aos titulares. Tenha o runbook ANTES do incidente.

## Armadilhas clássicas (e onde o SpecLoop as pega)

| Armadilha | Onde é pega |
|---|---|
| CPF/e-mail em log de debug | Verifier + heurística do gate (warning) |
| Coletar "para o futuro" | Seção LGPD (minimização) + Verifier (escopo) |
| Dado real em ambiente de teste | smoke.sh usa dados sintéticos por desenho |
| DELETE que não deleta (Art. 18 VI!) | O check "deleção seguida de leitura" do smoke |
| Retenção infinita por omissão | Campo retenção obrigatório na seção da spec |

*Nota: este documento é material didático de engenharia, não aconselhamento
jurídico. Fábricas de software: envolvam o DPO/jurídico na constituição.*
