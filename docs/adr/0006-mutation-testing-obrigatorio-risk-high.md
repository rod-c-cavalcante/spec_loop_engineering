# ADR-0006 — Mutation testing obrigatório em histórias risk:high

Status: proposto
Data: 2026-09-13
Decisores: <pendente — humano decide aceitar/rejeitar>
História/feature de origem: specs/002-fortalecimento-v4 (RF-01, RF-02), T-003/T-004

## Contexto
Duas retrospectivas externas de um projeto com a mesma arquitetura
(RETROSPECTIVA.md §2.1; RETROSPECTIVA-005-006.md §2.3) apontam mutation
testing como o hábito que mais mudou decisões: 9 mutações, 3 revelaram
suíte verde que não provava nada — incluindo uma proteção contra fixação de
sessão no login. Este template não tinha nenhum mecanismo equivalente.
Mutation testing é caro (cada mutação roda o gate inteiro no escopo); rodar
em 100% do código inflaria o tempo de loop, que já foi gargalo documentado
(ARCHITECTURE.md §7, "10-22 min/iteração").

## Decisão
`loop/mutar.py` (specs/002-fortalecimento-v4) fica disponível como
ferramenta; propomos que seu uso passe de opcional a **obrigatório em
histórias `risk:high`**: pelo menos uma mutação aplicada e reportada
(morta ou sobrevivente) antes da história ser marcada `passes: true`.
Histórias `normal`/`low` continuam sem essa exigência.

## Alternativas consideradas
- Mutation testing em 100% das histórias — rejeitada: custo de tempo por
  iteração não se paga fora de onde o bug grave concentra (mesma lógica já
  aceita para o campo `risk` existente).
- Ferramenta de mutation testing de terceiros (ex.: `mutmut`, `stryker`) —
  rejeitada nesta v4: dependência nova sem justificativa ainda validada
  (constitution §7); `mutar.py` cobre os 3 operadores que motivaram as
  retros (negação, relacional, `await`) sem dependência externa.

## Consequências
- (+) Acrescenta prova de que o teste de uma história de risco realmente
  discrimina — não só que passa.
- (−) Aumenta o tempo de loop em histórias `risk:high`, que já param para
  checkpoint humano (custo aceito onde já se paga o custo de revisão).
- Reversão: remover a linha de `tasks.md`/critério de pronto que exige
  mutação; `mutar.py` continua utilizável como ferramenta opcional.

## Verificação (opcional, recomendado)
`gates.sh`/`verificar.py` poderiam checar, em histórias `risk:high`, se há
registro de execução de `mutar.py` em `state/progress.md` ou `metrics.csv`
— não implementado nesta v4 (ver "Pendências conhecidas" de specs/002); a
exigência hoje é de processo (Verifier audita), não de gate determinístico.
