#!/usr/bin/env python3
"""
SpecLoop · metrics_report.py — painel unificado de métricas (v3.0)

4 famílias, cada velocidade pareada com um contrapeso de qualidade:
  A. HARNESS  qualidade da spec     FPSR, gaps Intent→Spec/Spec→Impl/Spec→Oráculo
  B. LOOP     execução              iterações/história, aprovação Verifier,
                                    retrabalho, autonomia, latência por gate
  C. FINOPS   economia              custo/feature, HDE, custo do retrabalho
  D. DORA     entrega               lead time (git), deploy freq (git),
                                    CFR e MTTR (manuais até haver telemetria)

Uso:
  python3 loop/metrics_report.py            # relatório humano no terminal
  python3 loop/metrics_report.py --md       # markdown p/ comentário de PR (CI)
  python3 loop/metrics_report.py --snapshot # acrescenta linha em metrics_history.csv

Fontes: state/metrics.csv (ralph.sh), state/verdicts.csv (Verifier),
state/progress.md (tags [gap:*]), git (DORA).

ANTI-GOODHART: este painel é termômetro, não meta. Nenhuma métrica isolada
vira OKR; leia sempre o par (ex.: FPSR alto + defeitos escapados altos =
specs frouxas ou gates fracos, não excelência).
"""
import csv, os, signal, subprocess, sys
try:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
except Exception:
    pass
from collections import defaultdict
from datetime import datetime, timezone

ROOT = os.path.join(os.path.dirname(__file__), "..")
M = lambda *p: os.path.join(ROOT, *p)
COST_IT = float(os.environ.get("COST_PER_ITERATION_BRL", "2.50"))
DEV_HOUR = float(os.environ.get("DEV_HOUR_BRL", "150"))
MD = "--md" in sys.argv
SNAP = "--snapshot" in sys.argv


def sh(cmd):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                              cwd=ROOT, timeout=15).stdout.strip()
    except Exception:
        return ""


def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ── B. LOOP + base p/ A e C ──────────────────────────────────────────────
rows = read_csv(M("state", "metrics.csv"))
stories, order = defaultdict(list), []
for r in rows:
    if r["story"] not in stories:
        order.append(r["story"])
    stories[r["story"]].append(r)

n_stories = len(order)
total_iters = len(rows)
total_secs = sum(int(r.get("duration_s") or 0) for r in rows)
fails = sum(1 for r in rows if r.get("gates") == "fail")
first_pass = sum(1 for s in order if stories[s][0].get("gates") == "pass")
fpsr = 100 * first_pass / n_stories if n_stories else 0
iters_avg = total_iters / n_stories if n_stories else 0
retrabalho_pct = 100 * fails / total_iters if total_iters else 0
breaker = sum(1 for r in rows if r.get("result") == "circuit_breaker")
blocked = sum(1 for r in rows if r.get("result") == "blocked")
autonomy = 100 * (1 - (breaker + blocked) / n_stories) if n_stories else 0
lat = defaultdict(list)
for r in rows:
    lat[r.get("level", "?")].append(int(r.get("duration_s") or 0))
lat_str = " · ".join(f"{k}:{sum(v)//len(v)//60}m{sum(v)//len(v)%60:02d}s"
                     for k, v in sorted(lat.items()) if v)

# ── Verifier ─────────────────────────────────────────────────────────────
verd = read_csv(M("state", "verdicts.csv"))
first_verdict = {}
for v in verd:
    first_verdict.setdefault(v["story"], v["verdict"])
v_total = len(first_verdict)
v_ok = sum(1 for x in first_verdict.values() if x.upper().startswith("APROV"))
verifier_rate = 100 * v_ok / v_total if v_total else None

# ── A. HARNESS: gaps taxonomizados ───────────────────────────────────────
gaps = {"intent-spec": 0, "spec-impl": 0, "spec-oraculo": 0}
prog = M("state", "progress.md")
if os.path.exists(prog):
    txt = open(prog, encoding="utf-8").read().lower()
    for k in gaps:
        gaps[k] = txt.count(f"[gap:{k}]")
# gaps são contados APENAS via tags [gap:*] no progress.md (fonte única —
# o Verifier escreve a tag lá ao reprovar; contar verdicts.csv duplicaria).

# ── C. FINOPS ────────────────────────────────────────────────────────────
cost_total = total_iters * COST_IT
cost_rework = fails * COST_IT
hde_min = (cost_total / DEV_HOUR) * 60 if DEV_HOUR else 0

# ── D. DORA (proxies via git; CFR/MTTR manuais) ──────────────────────────
first_commit = sh("git log main..HEAD --reverse --format=%ct | head -1") or \
               sh("git log master..HEAD --reverse --format=%ct | head -1")
lead_h = None
if first_commit.isdigit():
    lead_h = (datetime.now(timezone.utc).timestamp() - int(first_commit)) / 3600
merges = sh("git log main --merges --since=28.days --oneline | wc -l") or \
         sh("git log master --merges --since=28.days --oneline | wc -l")
deploy_wk = (int(merges) / 4) if merges.isdigit() else None

feature = "?"
try:
    import json
    feature = json.load(open(M("loop", "prd.json")))["feature"]
except Exception:
    pass

# ── SNAPSHOT acumulado (1 linha por feature/execução) ────────────────────
if SNAP:
    hist = M("state", "metrics_history.csv")
    new = not os.path.exists(hist)
    with open(hist, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["date", "feature", "stories", "iters", "fpsr_pct",
                        "verifier_first_ok_pct", "rework_pct", "autonomy_pct",
                        "gap_intent_spec", "gap_spec_impl", "gap_spec_oraculo",
                        "cost_brl", "hde_min", "lead_time_h", "deploys_per_week"])
        w.writerow([datetime.now().date(), feature, n_stories, total_iters,
                    round(fpsr, 1), round(verifier_rate, 1) if verifier_rate is not None else "",
                    round(retrabalho_pct, 1), round(autonomy, 1),
                    gaps["intent-spec"], gaps["spec-impl"], gaps["spec-oraculo"],
                    round(cost_total, 2), round(hde_min), 
                    round(lead_h, 1) if lead_h else "", deploy_wk or ""])

# ── SAÍDA ────────────────────────────────────────────────────────────────
fmt = (lambda x, suf="": ("–" if x is None else f"{x:.0f}{suf}"))
if MD:
    print(f"## 📊 SpecLoop · métricas da feature `{feature}`\n")
    print("| Família | Métrica | Valor | Contrapeso |")
    print("|---|---|---|---|")
    print(f"| A. Harness | First-Pass Success | {fpsr:.0f}% | gaps: I→S {gaps['intent-spec']} · S→I {gaps['spec-impl']} · S→O {gaps['spec-oraculo']} |")
    print(f"| B. Loop | Iterações/história | {iters_avg:.1f} | retrabalho {retrabalho_pct:.0f}% · autonomia {autonomy:.0f}% |")
    print(f"| B. Loop | Aprovação Verifier (1ª) | {fmt(verifier_rate,'%')} | circuit breaker {breaker} · blocked {blocked} |")
    print(f"| B. Loop | Latência por gate | {lat_str or '–'} | |")
    print(f"| C. FinOps | Custo da feature | R$ {cost_total:.2f} | retrabalho R$ {cost_rework:.2f} |")
    print(f"| C. FinOps | HDE | {hde_min:.0f} min-equiv. | premissas R$ {COST_IT}/iter · R$ {DEV_HOUR:.0f}/h |")
    print(f"| D. DORA | Lead time (1º commit→agora) | {fmt(lead_h,'h')} | CFR/MTTR: preencher c/ dados de produção |")
    print(f"| D. DORA | Deploys/semana (28d) | {fmt(deploy_wk)} | |")
    print("\n> Termômetro, não meta (Goodhart). Histórico: `state/metrics_history.csv`.")
else:
    print("═" * 64)
    print(f" SpecLoop · painel de métricas · feature {feature}")
    print("═" * 64)
    print(f" A. HARNESS   FPSR {fpsr:.0f}%  ·  gaps I→S:{gaps['intent-spec']}  S→I:{gaps['spec-impl']}  S→O:{gaps['spec-oraculo']}")
    print(f" B. LOOP      {iters_avg:.1f} iter/história · Verifier 1ª: {fmt(verifier_rate,'%')} · retrabalho {retrabalho_pct:.0f}%")
    print(f"              autonomia {autonomy:.0f}% · breaker {breaker} · blocked {blocked} · latência {lat_str or '–'}")
    print(f" C. FINOPS    R$ {cost_total:.2f} total (retrabalho R$ {cost_rework:.2f}) · HDE {hde_min:.0f} min-equiv.")
    print(f" D. DORA      lead time {fmt(lead_h,'h')} · deploys/sem {fmt(deploy_wk)} · CFR/MTTR: produção")
    print("─" * 64)
    print(" Leitura pareada (anti-Goodhart): FPSR alto + defeitos escapados altos")
    print(" = specs frouxas/gates fracos. Autonomia alta + retrabalho alto = loop")
    print(" girando à toa. Nenhuma métrica isolada vira meta.")
