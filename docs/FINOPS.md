# FinOps no SpecLoop — a economia do loop

FinOps em três fases (FinOps Foundation): **informar** (visibilidade de
custo), **otimizar** (reduzir desperdício), **operar** (decidir com números).
No SpecLoop as três já têm mecanismo:

## 1. Informar — visibilidade por desenho
- Toda iteração gera linha em `state/metrics.csv` (história, risco, nível de
  gate, duração, resultado). Nada de custo invisível.
- `python3 loop/metrics_report.py` consolida: custo por feature, custo do
  RETRABALHO (iterações fail — o desperdício nº 1), HDE.
- Snapshot acumulado por feature em `state/metrics_history.csv` + comentário
  automático no PR: o custo chega onde a decisão acontece.

## 2. Otimizar — as alavancas, por ordem de impacto
1. **Retrabalho** (iterações fail): quase sempre gap Intent→Spec. Spec melhor
   é a otimização FinOps mais barata que existe.
2. **Latência de gate**: a estratificação L0/L1/L2 já cortou ~60% do tempo de
   parede; vigie a coluna de latência do painel para o L1 não engordar.
3. **Fatia fina**: história gorda que falha custa 2 iterações longas;
   duas histórias finas custam 2 curtas — e falham menos (prd-lint).
4. **Modelo certo por tarefa**: histórias risk:low/polish toleram modelos mais
   baratos (`AGENT_CMD` é configurável por execução).
5. **Autonomia graduada**: checkpoint humano só em risk:high — tempo de gente
   é o recurso mais caro do sistema; gaste-o onde o risco justifica.

## 3. Operar — unit economics e governança
- **HDE (Horas-Dev Equivalentes)** = custo do loop ÷ custo-hora do dev.
  É o número que fecha a conversa de ROI com quem paga a conta:
  "a feature 009 custou R$ 42 = 17 min-equivalentes; manual seriam ~2 dias."
- **Calibração mensal**: ajuste `COST_PER_ITERATION_BRL` com a fatura real da
  API 1x/mês. A precisão do HDE é a credibilidade do relatório.
- **Orçamento por feature**: MAX_ITERATIONS × custo/iteração é o teto natural;
  o circuit breaker é, na prática, um mecanismo FinOps (corta gasto repetitivo
  sem progresso).
- **Anti-Goodhart**: métrica é termômetro, não meta. Custo baixo com FPSR
  baixo e defeitos escapados = você economizou no lugar errado. Leia pares.
