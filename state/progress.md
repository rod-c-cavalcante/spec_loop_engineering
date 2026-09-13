# Progress log do loop

> Memória de aprendizado entre iterações. O Builder lê este arquivo ANTES de
> agir e acrescenta 2–5 linhas ao final de cada iteração. Denso, não verboso.
> Faça expurgo humano quando passar de ~150 linhas (memória que cresce sem
> revisão acumula vieses e decisões obsoletas).

## Formato de cada entrada
## Iteração <data ISO> — <id da história>
- Fez: ...
- Descobriu: ... (armadilhas, convenções implícitas, decisões)
- Gap registrado: (se houver) tag padronizada gap:intent-spec, gap:spec-impl
  ou gap:spec-oraculo ENTRE COLCHETES + 1 linha (o painel conta as tags)

## Iteração 2026-09-13 — T-006/T-007 (specs/002-fortalecimento-v4)
- Fez: implementou `infra-assertion-lint` e `crlf-lint` em `gates.sh`.
- Descobriu: `git grep` (sem `--untracked`) NÃO enxerga arquivo novo ainda não
  commitado — um teste de infra recém-escrito pelo Builder na MESMA iteração
  passaria batido pelo lint até o commit. Descoberto plantando o defeito real
  antes de confiar no lint (mesmo hábito que a retro pede). O mock-lint
  existente tem a mesma limitação, não corrigido aqui (fora do escopo desta
  história) — candidato a registrar de novo se reaparecer.
- Descoberta 2: `grep -q $'\r' arquivo` NÃO detecta CRLF neste ambiente
  (Windows/Git Bash MSYS) — o próprio grep abre o arquivo em modo texto e o
  SO strippa o `\r` antes do padrão ver o byte. `grep -U` (modo binário)
  resolve e é no-op inofensivo em grep GNU/Linux. Isto é literalmente a
  mesma classe de armadilha texto↔binário que motivou o crlf-lint
  (RETROSPECTIVA-005-006.md §3.4) — reapareceu na hora de implementar o
  próprio lint que devia pegá-la.
- [gap:spec-oraculo] lint que não pega o caso motivador na primeira tentativa
  é o mesmo padrão "gate que não roda mas diz ok" da retro — só não virou
  falso-verde aqui porque cada lint foi verificado plantando o defeito real
  ANTES de contar como concluído (plan.md de specs/002, seção Verificação).

## Iteração 2026-09-13 — T-013 (specs/002-fortalecimento-v4, risk:high)
- Fez: endureceu `ralph.sh` para bloquear (exit 6) história `risk:high`
  marcada `passes:true` sem veredito `APROVADO` em `state/verdicts.csv`.
- Descobriu: `SKIP_VERIFIER=1` citado em `ARCHITECTURE.md` nunca existiu
  como checagem real em nenhum script — o Verifier nunca foi mecanicamente
  exigido para nada. A proposta original (RF-04) era "impedir que
  SKIP_VERIFIER=1 funcione em risk:high"; a implementação real e mais forte
  foi "exigir veredito registrado", que cobre o mesmo problema sem depender
  de uma variável que não fazia nada.
- Gap registrado: [gap:intent-spec] nenhum Verifier independente auditou
  esta própria mudança nesta sessão — o mesmo agente implementou, testou e
  documentou T-013. É exatamente o padrão que a retro (RETROSPECTIVA-005-006.md
  §4.3) aponta como causa de 4 de 5 falsos-verdes. Recomendado rodar /verify
  sobre este diff antes de confiar nele, especialmente por ser risk:high.

## Iteração 2026-09-13 — /verify sobre specs/002-fortalecimento-v4 (working tree)
- Fez: rodou o Verifier (loop/PROMPT_VERIFY.md) sobre o diff não commitado.
  Primeiro veredito: REPROVADO em T-002 e T-003 (state/verdicts.csv).
- Descobriu: [gap:spec-oraculo] `mutate_negacao` em `mutar.py` engolia o ')'
  de chamadas de função aninhadas (`if is_valid(x):` → `if not (is_valid(x):`,
  SyntaxError) — e o teste que EXERCITAVA exatamente esse caso só checava
  substring, não sintaxe, então passava verde com a mutação quebrada. É o
  mesmo "teste que não pode falhar" que a própria feature 002 existe para
  prevenir, encontrado na ferramenta de mutation testing dela mesma.
- Descoberta 2: [gap:spec-impl] `verificar.py::_scope_has_coverage` usava
  `git grep` sem `--untracked` — mesmo bug já corrigido em `gates.sh`
  (infra-assertion-lint) nesta sessão, mas não replicado aqui. Quebrava o
  caso normal de uso: verificar.py chamado no mesmo iteração em que o
  Builder acabou de escrever o teste, ainda não commitado.
- Corrigido: regex de `mutate_negacao` reescrita (greedy até o último
  delimitador, não non-greedy + rstrip); `--untracked` adicionado; 4 testes
  de regressão novos (incluindo `ast.parse` para validar sintaxe, não só
  substring). Segundo veredito: APROVADO (state/verdicts.csv). 26/26 testes
  verdes, gates.sh --level 0 verde.
- Lição: "achado plantado manualmente antes de contar como pronto" (o
  próprio critério de verificação do plan.md desta feature) pegou os 4
  lints de gates.sh, mas eu não apliquei o MESMO rigor aos scripts Python
  (mutar.py/verificar.py) — só rodei os testes que eu mesmo escrevi. O
  Verifier independente (ainda que sendo eu, num papel separado) achou o
  que a revisão do próprio autor não achou. Reforça constitution §11/
  checklist do Verifier: quem escreve o teste não deveria ser o único a
  julgar se ele prova algo.
- Descoberta 3, ao preparar o commit: `git add` avisou que
  `loop/tests/test_mutar.py` tinha CRLF (170/170 linhas) — introduzido por
  um `open(p, "w", encoding="utf-8").write(s)` em Python SEM `newline=""`
  usado horas antes para renomear uma variável. Ninguém pegou porque
  crlf-lint (RF-08) só cobria `*.sh`. Corrigido: arquivo normalizado para
  LF, crlf-lint estendido para `*.py` também, RF-08 atualizado no spec.md
  para refletir o escopo real. [gap:spec-oraculo] terceira vez na mesma
  sessão que a armadilha texto↔binário aparece — a primeira (crlf-lint em
  si, `grep -U`) e a segunda (git grep --untracked) já tinham sido
  corrigidas; esta terceira só foi pega porque `git add` avisa por padrão,
  não porque algum gate meu a pegou primeiro. Vale registrar: "achado
  plantado antes de contar como pronto" também deveria valer para os
  PRÓPRIOS arquivos da história, não só para o caso de exemplo sintético.

## Iteração 2026-09-13 — CI 100% quebrada desde o primeiro commit (achado externo)
- Fez: investigou https://github.com/rod-c-cavalcante/spec_loop_engineering/actions/runs/34759206761
  (reportado pelo usuário) e as duas corridas anteriores — as 3 corridas de
  CI que já existiram falharam de forma idêntica: `./loop/gates.sh: Permission
  denied` (exit 126) no primeiro passo do job Gates L0.
- Descobriu: [gap:spec-impl] TODOS os `*.sh` do repo (gates.sh, ralph.sh,
  preflight.sh, smoke.sh, setup-branch-protection.sh, githooks/pre-commit)
  estavam `100644` no índice do git — nunca tiveram o bit de execução
  registrado, desde o commit inicial do projeto (antes desta sessão).
  `docs/DEVOPS.md` promete "CI roda os MESMOS gates" (zero drift); na
  prática nunca rodou nenhum, porque `ci.yml` chama `./loop/gates.sh`
  (exige +x), e localmente eu sempre rodei via `bash ./loop/gates.sh`
  (explicitando o interpretador, que não exige +x) — exatamente o tipo de
  divergência "passou na minha máquina, quebrou no CI" que a própria
  constituição/README descrevem como razão de ser do L2. `core.filemode=false`
  neste Windows fazia qualquer `chmod` local nunca chegar no índice do git.
- Corrigido: `git update-index --chmod=+x` nos 8 scripts; novo
  `exec-bit-lint` em `gates.sh` reprova qualquer `*.sh` tracked sem o bit
  `100755` — verificado plantando a regressão exata (derrubando o bit de
  `ralph.sh`) antes de contar como pronto. 3 falhas idênticas é bem além do
  "2x" que a constitution §12 exige para promover a mecanismo.
