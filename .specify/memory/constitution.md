# Constitution — regras inegociáveis do projeto

> Compatível com GitHub Spec Kit (`/speckit.constitution` edita este arquivo).
> Mantenha entre 5 e 10 regras. Toda regra deve ser VERIFICÁVEL — se um agente
> (ou os gates) não consegue checar, é aspiração, não regra. Edite as regras de
> exemplo abaixo para o seu contexto.

## Princípios

1. **Spec antes de código.** Nenhuma implementação sem `spec.md` aprovado com
   critérios de aceite em EARS. Violação: PR rejeitado.

2. **Testes antes de implementação (TDAD).** Cada critério EARS gera ao menos
   um teste automatizado que falha antes da implementação e passa depois.

3. **Gates são inegociáveis.** `./loop/gates.sh` verde é pré-condição para
   qualquer commit de feature. Testes não podem ser removidos ou enfraquecidos
   para passar.

4. **Menor mudança coerente.** Cada commit resolve exatamente uma história.
   Diffs que tocam arquivos fora do escopo da história são reprovados pelo
   Verifier.

5. **Rastreabilidade total.** Toda mensagem de commit referencia a spec:
   `refs specs/NNN-nome/spec.md`. Todo bug em produção é classificado como
   gap Intent→Spec ou Spec→Implementação em `state/progress.md`.

6. **Sem segredos no repositório.** Credenciais só via variáveis de ambiente.
   O loop nunca roda com credenciais de produção.

7. **Dependências justificadas.** Nova dependência exige 2 linhas de
   justificativa no `plan.md` da feature (o que resolve, por que não fazer na mão).

8. **Specs curtas.** 1 a 3 páginas por feature. Passou disso, a feature é
   grande demais — divida.

9. **Simplicidade primeiro.** Sem abstrações especulativas ("vamos precisar
   depois"). Três repetições reais antes de generalizar.

10. **Humano decide o merge.** O loop produz commits locais e evidências;
    push, PR e merge são sempre decisões humanas.

## Governança

- Mudanças nesta constituição exigem edição humana explícita (agentes não editam).
- Em conflito entre constituição e spec, a constituição vence e a spec é corrigida.
- Revisão trimestral: regras que nunca bloquearam nada são candidatas a remoção.
- Decisões arquiteturais transversais ou caras de reverter exigem ADR em
  `docs/adr/` (agentes propõem; humanos aceitam, descontinuam e substituem).

## Regras adicionadas na v2.0 (origem: retrospectiva de produção)

11. **Mock só na fronteira do sistema.** APIs externas, e-mail e pagamento
    podem ser mocados; dependências internas (banco, sessão, filas) testam
    contra implementação real ou fake de alta fidelidade. `MagicMock` em alvo
    async é reprovado pelo gate (mock-lint) — o Builder não pode ser o único
    autor do próprio oráculo.

12. **Lição determinística vira código, não texto.** Todo gotcha reproduzível
    registrado 2x no progress.md deve ser promovido a mecanismo (preflight,
    gate, hook ou script) no expurgo seguinte. Só lição de julgamento
    permanece como documentação (ADR/constituição).

13. **Privacy by design (LGPD, Art. 46 §2º).** Toda spec contém a seção
    "## Dados pessoais (LGPD)" (dados tocados ou "nenhum", base legal,
    retenção, minimização) — validada pelo lgpd-lint. Dado pessoal em log é
    reprovação. Deleção de dados pessoais é sempre `risk: high`. Dados
    sensíveis (Art. 11) exigem humano/DPO antes do loop.
