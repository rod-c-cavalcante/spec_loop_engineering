# ADR-0002 — Erros como texto plano

Status: substituído por ADR-0003
Data: 2026-07-09
Decisores: tech lead (humano)
História/feature de origem: T-003 (primeira versão)

## Contexto
Na primeira iteração da API, respostas de erro eram string simples
(ex.: `"title is required"`), o mínimo para o teste passar.

## Decisão
Erros HTTP respondem corpo em texto plano com mensagem legível.

## Alternativas consideradas
- JSON estruturado — adiada por "simplicidade primeiro" (leitura equivocada:
  simplicidade não é ausência de contrato).

## Consequências
- (+) Implementação trivial.
- (−) Clientes fazem parsing frágil de strings; mensagens viram contrato
  acidental; i18n impossível. Motivou a substituição — ver ADR-0003.
