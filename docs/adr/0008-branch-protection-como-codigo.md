# ADR-0008 — Branch protection como código, não como recomendação em texto

Status: proposto
Data: 2026-09-13
Decisores: <pendente — humano decide aceitar/rejeitar>
História/feature de origem: specs/002-fortalecimento-v4 (RF-11), T-014

## Contexto
`docs/DEVOPS.md` já recomendava branch protection exigindo `gates-l0` +
`gates-l2`, mas como texto — nada no repositório configurava isso. Uma
retrospectiva externa registra a consequência concreta desse tipo de regra
não-mecanizada: um PR foi mesclado 90 segundos depois de aberto, com o gate
L2 ainda rodando (RETROSPECTIVA.md §3.3). A mesma retro mostra que a regra
"não mesclar antes do L2 fechar" sustentou quando seguida manualmente à
risca (RETROSPECTIVA-005-006.md §2.4) — mas "seguida à risca" é humano, não
mecanismo; a constituição §12 (lição determinística vira código, não texto)
se aplica diretamente aqui.

## Decisão
`scripts/setup-branch-protection.sh` (specs/002-fortalecimento-v4) usa `gh`
CLI para configurar branch protection em `main`/`master` exigindo os checks
`gates-l0` e `gates-l2` (nomes dos jobs em `.github/workflows/ci.yml`) antes
de permitir merge. Roda manualmente (1x por repositório, ou de novo se
resetada) — não é chamado por nenhum gate automático, pois depende de
credencial de admin no GitHub que o loop não deveria ter.

## Alternativas consideradas
- Deixar como recomendação em `docs/DEVOPS.md` — rejeitada: já era a
  situação anterior e não preveniu o incidente documentado.
- Automatizar via workflow do GitHub Actions que se autoconfigura — rejeitada
  nesta v4: exigiria token com permissão administrativa armazenado em
  secret do repositório, superfície de risco maior que um script rodado
  manualmente por humano com sua própria sessão `gh auth`.

## Consequências
- (+) "Não mesclar antes do L2 fechar" deixa de depender só de disciplina
  humana — o GitHub recusa o merge mecanicamente.
- (−) Setup inicial manual por repositório; não testável por gate local
  (depende de acesso ao remoto) — ver "Pendências conhecidas" em
  `specs/002-fortalecimento-v4/spec.md`.
- Reversão: remover a branch protection via GitHub UI ou `gh api -X DELETE`;
  não afeta nenhum código do loop.

## Verificação
`./scripts/setup-branch-protection.sh --dry-run` deve imprimir a chamada
`gh api` e o payload sem tocar o remoto, saindo com código 0. Verificação
real (fora de gate): após rodar sem `--dry-run`, abrir um PR de teste e
confirmar que o botão de merge fica bloqueado até `gates-l0` e `gates-l2`
reportarem sucesso.
