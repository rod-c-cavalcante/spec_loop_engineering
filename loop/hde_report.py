#!/usr/bin/env python3
"""
SpecLoop · hde_report.py — relatório FinOps do loop (HDE: Horas-Dev Equivalentes)

Lê state/metrics.csv e responde a pergunta que fecha a conversa de ROI:
"quanto custou esta feature em dinheiro e em minutos-equivalentes de dev?"

Uso:
  python3 loop/hde_report.py
  COST_PER_ITERATION_BRL=2.50 DEV_HOUR_BRL=150 python3 loop/hde_report.py

Variáveis:
  COST_PER_ITERATION_BRL  custo médio por iteração em R$ (calibre com a fatura
                          da API ou o relatório de custo do Claude Code; um
                          chute honesto vale mais do que nenhum número)
  DEV_HOUR_BRL            custo-hora do dev (salário+encargos / horas úteis)

Interpretação: HDE = custo total do loop ÷ custo-hora do dev, em minutos.
Ex.: loop custou R$ 30 e a hora-dev custa R$ 150 → HDE = 12 min-equivalentes.
Se o mesmo trabalho manual levaria 6 h, a alavancagem é 30x. Três meses desse
número por feature mudam a conversa sobre orçamento de IA na fábrica.
"""
import csv, os, sys
from collections import defaultdict

METRICS = os.path.join(os.path.dirname(__file__), "..", "state", "metrics.csv")
COST_IT = float(os.environ.get("COST_PER_ITERATION_BRL", "2.50"))
DEV_HOUR = float(os.environ.get("DEV_HOUR_BRL", "150"))

if not os.path.exists(METRICS):
    sys.exit("state/metrics.csv não existe ainda — rode o loop primeiro.")

rows = list(csv.DictReader(open(METRICS, encoding="utf-8")))
if not rows:
    sys.exit("metrics.csv vazio — rode o loop primeiro.")

by_story = defaultdict(lambda: {"iters": 0, "secs": 0, "fails": 0})
for r in rows:
    s = by_story[r["story"]]
    s["iters"] += 1
    s["secs"] += int(r.get("duration_s") or 0)
    if r.get("gates") == "fail":
        s["fails"] += 1

total_iters = sum(s["iters"] for s in by_story.values())
total_secs = sum(s["secs"] for s in by_story.values())
total_cost = total_iters * COST_IT
hde_min = (total_cost / DEV_HOUR) * 60

print("═" * 62)
print(" SpecLoop · Relatório FinOps (HDE)")
print(f" Premissas: R$ {COST_IT:.2f}/iteração · R$ {DEV_HOUR:.0f}/hora-dev")
print("═" * 62)
print(f" {'história':<14}{'iterações':>10}{'falhas':>8}{'parede':>10}{'custo R$':>10}")
for story, s in sorted(by_story.items()):
    print(f" {story:<14}{s['iters']:>10}{s['fails']:>8}{s['secs']//60:>8}m {s['iters']*COST_IT:>9.2f}")
print("─" * 62)
print(f" TOTAL: {total_iters} iterações · {total_secs//60} min de parede · R$ {total_cost:.2f}")
print(f" HDE:   {hde_min:.0f} minutos-equivalentes de dev")
print()
print(" Leituras acionáveis:")
worst = max(by_story.items(), key=lambda kv: kv[1]["fails"], default=None)
if worst and worst[1]["fails"] > 1:
    print(f" · '{worst[0]}' concentrou {worst[1]['fails']} falhas de gate —")
    print("   candidata a fatia mais fina ou spec mais clara (gap Intent→Spec?).")
retry = [k for k, v in by_story.items() if v["iters"] > 2]
if retry:
    print(f" · Histórias com 3+ iterações: {', '.join(retry)} — o retrabalho é o")
    print("   maior custo FinOps do loop; ataque a causa, não o sintoma.")
print(" · Calibre COST_PER_ITERATION_BRL com a fatura real 1x/mês; a precisão")
print("   do HDE é a credibilidade do relatório.")
