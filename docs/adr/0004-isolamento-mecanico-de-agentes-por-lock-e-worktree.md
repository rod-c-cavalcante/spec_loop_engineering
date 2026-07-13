# ADR-0004 — Isolamento mecânico de agentes: lock por working tree + worktree para paralelismo

Status: aceito
Data: 2026-07-13
Decisores: tech lead (humano)
História/feature de origem: retrospectiva forja_platform §2.2 (perda real de trabalho, feature 006)

## Contexto
Um agente de retrofit rodando em paralelo com uma iteração ativa do ralph.sh
no MESMO working tree teve arquivos não commitados apagados pelo commit do
loop. A regra "use worktrees" já existia como texto (ARCHITECTURE.md §5) —
e texto não impede nada. Working tree é recurso mutável compartilhado sem lock.

## Decisão
Dois mecanismos, não recomendações: (1) `loop/ralph.sh` adquire lock exclusivo
(`state/loop.lock`, PID + timestamp) e o preflight aborta se houver lock vivo;
(2) o preflight exige working tree limpo (`git status --porcelain` vazio)
antes de qualquer loop. Paralelismo legítimo acontece exclusivamente via
`git worktree` (um tree por agente).

## Alternativas consideradas
- Manter como convenção documentada — rejeitada: já falhou de forma cara.
- Lock distribuído/daemon — rejeitada: complexidade sem ganho local (§9).

## Consequências
- (+) Colisão de agentes vira erro imediato e legível, não perda silenciosa.
- (−) Um lock obsoleto após crash exige limpeza (o preflight detecta PID morto
  e remove sozinho); ALLOW_DIRTY=1 existe como override consciente.
- Reversão: trivial (remover checagens) — mas exigiria novo ADR justificando.

## Verificação
`preflight.sh` itens 1 e 2; testável matando o loop e verificando remoção do
lock (trap EXIT) e simulando segundo loop concorrente (deve abortar com rc=10).
