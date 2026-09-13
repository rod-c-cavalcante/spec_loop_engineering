# SPEC 002 — Fortalecimento v4.0 (mecanismos financiados pela retrospectiva Forja)

> Feature de tooling: fortalece o próprio SpecLoop (`loop/`, `gates.sh`,
> `constitution.md` propostas, ADRs), não um produto de negócio. Origem:
> duas retrospectivas externas (`RETROSPECTIVA.md` e `RETROSPECTIVA-005-006.md`,
> features 001–006 de um projeto chamado Forja, mesma arquitetura SpecLoop)
> anexadas pelo humano em 2026-09-13. Ver comparação completa no plano de
> execução desta sessão.

## Contexto e motivação

O README e o `ARCHITECTURE.md §7` afirmam que "cada mecanismo do SpecLoop
nasce de uma falha real de produção". Duas retrospectivas novas, de um
projeto que usa a mesma arquitetura, chegaram depois da v3.0 e expõem gaps
reais: hábitos que essas retros consideram o mais valioso do processo
(mutation testing, ponto único de veredito) **não existem** neste template;
e um padrão de código que a própria retro nomeia como anti-padrão ("nunca
ler veredito por cano") **já está presente** em `loop/ralph.sh`.

## Escopo (in)

- Um script de mutation testing (`loop/mutar.py`) com restauração segura.
- Um ponto único de veredito (`loop/verificar.py`) que invalida a corrida se
  a árvore mudar durante a execução do gate.
- Correção do padrão de leitura de veredito por pipe em `loop/ralph.sh`.
- Quatro lints novos em `gates.sh`: `orm-migration-lint`,
  `infra-assertion-lint`, lint de CRLF em scripts, lint de seção
  "Pendências conhecidas" na spec ativa.
- Extensão do `preflight.sh`/`smoke.sh`: rebuild forçado quando o diff toca
  `Dockerfile`/`infra/**`; `prd-lint` cobrindo ordenação de histórias
  `risk:high` em features com mais de 10 histórias.
- Regra de teste de jornada visível (constituição) + seção correspondente no
  template de `spec.md`.
- Três ADRs propostos (`proposto`, não aceitos por este trabalho):
  endurecimento do Verifier, mutation testing obrigatório em `risk:high`,
  branch protection como código.
- Uma proposta de diff para `constitution.md`, apresentada para aceitação
  humana explícita — **não aplicada** como parte desta feature.
- Reforço documental no `PROMPT_VERIFY.md`: checklist do oráculo generalizado
  além de mocks, exigência de evidência do vermelho.

## Requisitos (EARS)

### RF-01 — Mutação restaura mesmo sob timeout (Unwanted behavior)
IF `loop/mutar.py` é interrompido (timeout, SIGTERM ou exceção) a qualquer
momento após aplicar uma mutação, THEN THE SYSTEM SHALL restaurar o arquivo
mutado a partir da cópia de backup própria do script — nunca via
`git checkout` — antes de encerrar o processo.

### RF-02 — Mutação sobrevivente é reportada, não descartada (Event-driven)
WHEN `loop/mutar.py` aplica uma mutação e a suíte no escopo indicado
continua verde, THE SYSTEM SHALL reportar a mutação como "sobrevivente" com
arquivo, linha e operador aplicado, e sair com código de saída ≠ 0.

### RF-03 — Veredito único cobre escopo antes do gate (Event-driven)
WHEN `loop/verificar.py` é chamado para uma história do `prd.json`,
THE SYSTEM SHALL primeiro conferir que o `e2eScope` declarado da história
tem cobertura de teste correspondente; se não houver, SHALL falhar
imediatamente sem rodar `gates.sh`.

### RF-04 — Veredito anulado por árvore mutada durante a corrida (Unwanted behavior)
IF o hash da árvore de trabalho ao final da execução de `gates.sh` difere do
hash capturado no início da chamada de `loop/verificar.py`, THEN THE SYSTEM
SHALL anular o veredito (saída ≠ 0, mensagem explícita), independente do
código de saída do `gates.sh`.

### RF-05 — Exit code do gate nunca passa por pipe (Unwanted behavior)
THE SYSTEM SHALL, em `loop/ralph.sh`, gravar a saída de `gates.sh` em
arquivo antes de qualquer transformação (`tail`, `md5sum`) e ler o código de
saída real de `gates.sh` diretamente — nunca do último comando de um pipe
que inclua `gates.sh`.

### RF-06 — Migração sem modelo ORM correspondente é reprovada (Unwanted behavior)
IF o diff da história toca um arquivo de migração de banco de dados sem
tocar também o(s) arquivo(s) de modelo ORM correspondente(s), THEN
THE SYSTEM SHALL reprovar o gate L0 (`orm-migration-lint`), a menos que a
história declare justificativa explícita (ver `plan.md`).

### RF-07 — Teste de infra que mede o insumo é reprovado (Unwanted behavior)
IF um arquivo de teste sob `*test*infra*`/`*test*compose*` faz assert sobre
o conteúdo bruto de um arquivo de configuração de infraestrutura (ex.:
`docker-compose.yml`) em vez da saída resolvida da ferramenta (ex.:
`docker compose config`), THEN THE SYSTEM SHALL reprovar o gate L0
(`infra-assertion-lint`).

### RF-08 — Script shell ou Python com CRLF é reprovado (Unwanted behavior)
IF um arquivo `*.sh` ou `*.py` versionado (rastreado ou novo) contém
terminador de linha CRLF, THE SYSTEM SHALL reprovar o gate L0, citando o
arquivo. Escopo ampliado de `*.sh` para incluir `*.py` durante esta mesma
sessão: o Verifier encontrou CRLF introduzido em `loop/tests/test_mutar.py`
por um script Python que escreveu sem `newline=""` — a armadilha não é
específica de shell.

### RF-09 — Mudança em Dockerfile/infra força rebuild completo (Event-driven)
WHEN o diff da história toca `Dockerfile*` ou qualquer caminho sob
`infra/**`, THE SYSTEM SHALL forçar rebuild completo (`--build`, sem
`SKIP_REBUILD`) no `smoke.sh`, independentemente do escopo declarado da
história.

### RF-10 — Feature com UI exige teste de jornada visível (Ubiquitous)
THE SYSTEM SHALL exigir, para toda feature cuja spec declare uma tela de
entrada de usuário, ao menos um teste E2E que navegue exclusivamente por
elementos visíveis (não por rota direta ou chamada de API) até a tela-alvo
descrita na seção "Jornada esperada" do `spec.md` da feature.

### RF-11 — Merge bloqueado sem os dois checks de gate (State-driven)
WHILE o repositório remoto tiver branch protection configurável via `gh` CLI,
THE SYSTEM SHALL fornecer um script versionado que a configura para exigir
`gates-l0` E `gates-l2` verdes antes de permitir merge em `main`.

### RF-12 — Feature grande sem risco cedo gera aviso bloqueante (Unwanted behavior)
IF uma feature tem mais de 10 histórias pendentes e nenhuma história
`risk:high` está entre as primeiras 30% (arredondado para cima) da ordem do
`prd.json`, THEN THE SYSTEM SHALL emitir aviso bloqueante no preflight
(`prd-lint`), com override consciente equivalente ao já existente.

### RF-13 — Spec sem seção de pendências conhecidas é reprovada (Unwanted behavior)
IF a spec ativa (`specPath` do `prd.json`) não contém a seção
`## Pendências conhecidas`, THEN THE SYSTEM SHALL reprovar o gate L0
(mesmo padrão do `lgpd-lint`/`adr-lint`).

### RF-14 — Checklist do Verifier cobre oráculo emprestado e evidência de vermelho (Ubiquitous)
THE SYSTEM SHALL declarar em `loop/PROMPT_VERIFY.md` dois itens adicionais de
checklist: (a) todo teste que afirma um código de erro/rejeição tem par que
muda só a precondição culpada e passa; (b) o Verifier pede evidência de que
o teste novo foi visto falhando antes da implementação (log ou histórico de
commit), reprovando se a evidência não existir e for solicitada.

## Out of scope (tão importante quanto o escopo)

- Reimplementar o Verifier como processo determinístico não-LLM.
- Lints para stacks além de Python/JS (ex.: Go, Rust, Java).
- Mutation testing como gate obrigatório em histórias `risk:normal`/`low`
  (só `risk:high`, para não inflar o tempo de loop — ver `plan.md`).
- Aplicar o diff de `constitution.md` ou aceitar os ADRs propostos — isso é
  decisão humana, fora do que esta feature executa.
- Resolver os gaps citados nas retros que são do projeto Forja em si
  (entregabilidade de e-mail, execução real em VPS) — não são deste template.
- Trocar o provedor de CI ou de hospedagem de Git.

## Pendências conhecidas

- O script de branch protection (RF-11) depende de `gh` CLI autenticado com
  permissão de admin no repositório remoto — não pode ser testado por gate
  local; fica documentado e com teste de "dry-run" (mostra o que faria).
- `infra-assertion-lint` (RF-07) e `orm-migration-lint` (RF-06) são
  heurísticas de regex sobre nomes de arquivo/padrões de código — como o
  `mock-lint` existente, têm falso-negativo possível; não substituem revisão
  do Verifier.
- RF-14(b) (evidência de vermelho) é reforço documental, não gate
  determinístico — a própria retrospectiva de origem reconhece que "não é
  mecanizável hoje" (RETROSPECTIVA-005-006.md, ação 10).
- `loop/mutar.py` existe e funciona, mas nenhum gate exige sua execução em
  histórias `risk:high` — a exigência (ADR-0006 proposto) é hoje de
  processo/Verifier, não mecanizada em `gates.sh`/`verificar.py`.

## Dados pessoais (LGPD)

- **Dados tocados**: nenhum. Esta feature altera tooling de desenvolvimento
  (`loop/`, `docs/`, `.specify/`) — não introduz coleta, log ou
  processamento de dado pessoal.
- **Base legal**: n/a. | **Retenção**: n/a.
- **Minimização**: n/a.

## Critérios de pronto (definition of done)

- [ ] Todos os RF acima cobertos por teste automatizado que passa
      (scripts Python testados com `pytest`; lints de `gates.sh` provados
      contra um caso real do defeito que motivou, antes de contar como
      concluídos — ver `plan.md`, seção Verificação)
- [ ] `./loop/gates.sh` retorna 0 rodando sobre o próprio `loop/` alterado
- [ ] Commits referenciam esta spec
- [ ] `state/progress.md` atualizado com aprendizados
- [ ] Os 3 ADRs propostos e o diff de `constitution.md` apresentados para
      decisão humana — não commitados como aceitos
