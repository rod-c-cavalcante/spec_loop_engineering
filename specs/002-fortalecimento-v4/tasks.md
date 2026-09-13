# TASKS 002 — Fortalecimento v4.0

> Decomposição executável. Cada task vira uma história em um `prd.json`
> próprio desta feature (não substitui o `loop/prd.json` ativo de
> `001-exemplo-todo-api` — ver nota em `spec.md`/decisão de escopo da sessão).
> `[P]` = paralelizável. Ordem respeita risco e dependência: bug isolado →
> ponto único de veredito → mutation testing → lints independentes →
> endurecimento do Verifier (risco) → governança externa (branch protection).

- [ ] T-001 — Fix RF-05: `loop/ralph.sh` grava saída de `gates.sh` em arquivo
      temporário antes de qualquer pipe; assinatura do circuit breaker deriva
      do arquivo, exit code real lido direto. Teste: simular falha e checar
      que `GATES_RC` != 0 mesmo com pipe subsequente.
      Depende de: — · risk: normal

- [ ] T-002 — `loop/verificar.py`: wrapper de `gates.sh` com checagem de
      cobertura de `e2eScope` (RF-03) e hash de árvore antes/depois (RF-04).
      Testes próprios em `loop/tests/test_verificar.py`.
      Depende de: — · risk: normal

- [ ] T-003 — `loop/mutar.py`: operador de negação de condição + restauração
      via `try/finally` a partir de backup em memória (RF-01, RF-02, só este
      operador nesta história — fatia fina). Teste: matar o processo a meio
      da corrida (SIGTERM) e confirmar arquivo restaurado.
      Depende de: — · risk: normal

- [ ] T-004 — `loop/mutar.py`: operadores de troca de relacional e remoção
      de `await`. [P] (independente de T-003 após a estrutura base existir).
      Depende de: T-003 · risk: normal

- [ ] T-005 — `gates.sh`: `orm-migration-lint` (RF-06). [P]
      Depende de: — · risk: normal

- [ ] T-006 — `gates.sh`: `infra-assertion-lint` (RF-07). [P]
      Depende de: — · risk: normal

- [ ] T-007 — `gates.sh`: lint de CRLF em `*.sh` (RF-08). [P]
      Depende de: — · risk: normal

- [ ] T-008 — `gates.sh`: lint de seção "Pendências conhecidas" (RF-13),
      mesmo padrão do `lgpd-lint`. [P]
      Depende de: — · risk: normal

- [ ] T-009 — `smoke.sh`/`preflight.sh`: rebuild forçado quando diff toca
      `Dockerfile*`/`infra/**` (RF-09).
      Depende de: — · risk: normal

- [ ] T-010 — Regra de jornada visível: seção "Jornada esperada" no padrão
      de `spec.md` (documentar convenção) + verificação manual descrita no
      `PROMPT_VERIFY.md` (RF-10). Sem gate determinístico nesta v4 — E2E de
      navegação real depende de framework de UI que este template não fixa.
      Depende de: — · risk: normal

- [ ] T-011 — `preflight.sh`: `prd-lint` de ordenação de `risk:high` em
      features >10 histórias (RF-12).
      Depende de: — · risk: normal

- [ ] T-012 — `PROMPT_VERIFY.md`: checklist generalizado de oráculo emprestado
      + exigência de evidência de vermelho (RF-14).
      Depende de: — · risk: normal

- [ ] T-013 — Endurecer o Verifier: `ralph.sh` reprova história `risk:high`
      marcada `passes:true` sem veredito `APROVADO` correspondente em
      `state/verdicts.csv`; `SKIP_VERIFIER=1` passa a ser ignorado quando
      `risk:high`. Concentra o risco real da mudança (altera o critério de
      saída do loop) — checkpoint humano obrigatório após.
      Depende de: T-002 · risk: high

- [ ] T-014 — `scripts/setup-branch-protection.sh` com `--dry-run` (RF-11) +
      atualização de `docs/DEVOPS.md` (branch protection deixa de ser só
      "recomendada" em texto, ganha script versionado).
      Depende de: — · risk: normal

- [ ] T-015 — ADRs propostos (0006, 0007, 0008) + `proposta-constituicao.md`
      + atualização do índice `docs/adr/README.md` e da tabela
      `ARCHITECTURE.md §7`. Documentação, sem código — fecha o rastro da v4.
      Depende de: T-001..T-014 · risk: normal

- [ ] S-RELEASE — Verificação de release: `./loop/gates.sh --level 2` verde
      rodando sobre o `loop/` alterado; `loop/tests/` (pytest) verde;
      confirma que os 4 lints novos pegam um exemplo real do defeito que os
      motivou (ver plan.md, Verificação) antes de contar como concluídos.
      Depende de: T-001..T-015 · risk: high
