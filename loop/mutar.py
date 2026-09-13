#!/usr/bin/env python3
"""SpecLoop · mutar.py — mutation testing pontual (specs/002-fortalecimento-v4).

Origem: RETROSPECTIVA.md §2.1 ("a mutação não valida o código, valida o
teste") e RETROSPECTIVA-005-006.md §2.3 — nas duas retros, mutation testing
foi o hábito que mais mudou decisões: revelou repetidamente suíte verde que
não provava nada. Este template não tinha mecanismo nenhum para isso.

Aplica UMA mutação pontual (uma linha, um operador), roda o gate no escopo
indicado, reporta se a mutação foi morta (gate reprovou — bom, o teste
pegou) ou sobreviveu (gate passou — achado: o teste não prova o que diz
provar, constitution futura regra "mutação que não mata é achado", nunca
anedota). SEMPRE restaura o arquivo mutado a partir do backup em memória
próprio deste script — nunca via `git checkout` (RETROSPECTIVA.md §3.5: um
`git checkout --` para desfazer mutação apagou implementação não commitada
de outra história). A restauração roda em `finally` e também em handler de
SIGTERM/SIGINT, para sobreviver a timeout externo (RETROSPECTIVA-005-006.md
§5, ação 6: "cumprida, com susto" — um timeout deixou arquivo mutado, foi
restaurado à mão).

Uso:
    python3 loop/mutar.py --file src/todos/router.js --line 42 \
        --operator negacao [--scope @todos-mutacao] [--level 1] [--timeout 120]

Operadores:
    negacao     nega a condição de um `if`/`while` (envolve com `not (...)`
                em Python, `!(...)` em outras linguagens de chaves)
    relacional  troca um operador relacional pelo seu "quase-oposto"
                (< → >=, > → <=, <= → >, >= → <, == → !=, != → ==)
    await       remove a primeira ocorrência de `await ` na linha — a classe
                de bug que motivou o mock-lint (constitution §11)

Códigos de saída:
    0  mutação MORTA (o gate reprovou — o teste prova o que diz provar)
    1  mutação SOBREVIVEU (achado: gate passou com o código quebrado)
    2  erro de uso (arquivo/linha inválidos, operador não aplicável)
"""
from __future__ import annotations

import argparse
import re
import signal
import subprocess
import sys
from pathlib import Path
from types import FrameType

REPO_ROOT = Path(__file__).resolve().parent.parent

RELATIONAL_SWAPS = [
    ("<=", ">"), (">=", "<"), ("==", "!="), ("!=", "=="), ("<", ">="), (">", "<="),
]


class MutationNotApplicable(Exception):
    pass


def mutate_negacao(line: str) -> str:
    """Nega a condição de um if/while.

    Achado do Verifier (specs/002-fortalecimento-v4): a versão anterior usava
    `.+?` não-guloso + `\\)?` opcional + `rstrip(":) \\t")` para extrair a
    condição — e engolia o parêntese de fechamento de chamadas de função
    aninhadas (`if is_valid(x):` virava `if not (is_valid(x):`, inválido).
    Corrigido com `.*` GULOSO até o ÚLTIMO delimitador relevante (":" em
    Python, o ")" que fecha o "if (" em linguagens de chave) — greedy
    backtracking naturalmente inclui parênteses internos na condição.
    """
    body = line[:-1] if line.endswith("\n") else line
    newline = line[len(body):]

    m = re.match(r"^(\s*)(if|while)\b\s+(.*):(\s*(?:#.*)?)$", body)
    if m:
        indent, keyword, cond, tail = m.group(1), m.group(2), m.group(3), m.group(4)
        return f"{indent}{keyword} not ({cond}):{tail}{newline}"

    m = re.match(r"^(\s*)(if|while)\b\s*\((.*)\)(\s*\{?\s*)$", body)
    if m:
        indent, keyword, cond, tail = m.group(1), m.group(2), m.group(3), m.group(4)
        return f"{indent}{keyword} (!({cond})){tail}{newline}"

    raise MutationNotApplicable("linha não parece condição if/while reconhecível")


def mutate_relacional(line: str) -> str:
    for op, swapped in RELATIONAL_SWAPS:
        idx = line.find(op)
        if idx == -1:
            continue
        # evita casar "<=" quando o operador candidato é "<" etc.
        if op in ("<", ">") and line[idx : idx + 2] in ("<=", ">="):
            continue
        return line[:idx] + swapped + line[idx + len(op) :]
    raise MutationNotApplicable("nenhum operador relacional encontrado na linha")


def mutate_await(line: str) -> str:
    if "await " not in line:
        raise MutationNotApplicable("linha não contém 'await '")
    return line.replace("await ", "", 1)


OPERATORS = {"negacao": mutate_negacao, "relacional": mutate_relacional, "await": mutate_await}


class RestoreOnExit:
    """Garante restauração do arquivo mutado mesmo sob SIGTERM/SIGINT."""

    def __init__(self, path: Path, original: str):
        self.path = path
        self.original = original
        self._restored = False
        self._prev_handlers: dict[int, object] = {}

    def __enter__(self):
        for sig in (signal.SIGTERM, signal.SIGINT):
            self._prev_handlers[sig] = signal.getsignal(sig)
            signal.signal(sig, self._on_signal)
        return self

    def _on_signal(self, signum: int, frame: FrameType | None) -> None:
        self.restore()
        sys.exit(128 + signum)

    def restore(self) -> None:
        if self._restored:
            return
        self.path.write_text(self.original, encoding="utf-8", newline="")
        self._restored = True

    def __exit__(self, exc_type, exc, tb) -> None:
        self.restore()
        for sig, handler in self._prev_handlers.items():
            signal.signal(sig, handler)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--file", required=True, help="Caminho do arquivo-alvo, relativo ao repo")
    parser.add_argument("--line", type=int, required=True, help="Linha 1-indexed a mutar")
    parser.add_argument("--operator", required=True, choices=sorted(OPERATORS))
    parser.add_argument("--scope", default="", help="e2eScope a passar para gates.sh")
    parser.add_argument("--level", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=300, help="segundos antes de matar o gate (default 300)")
    args = parser.parse_args()

    target = (REPO_ROOT / args.file).resolve()
    if not target.is_file():
        print(f"✖ mutar: arquivo não encontrado: {args.file}", file=sys.stderr)
        return 2

    original = target.read_text(encoding="utf-8")
    lines = original.splitlines(keepends=True)
    if not (1 <= args.line <= len(lines)):
        print(f"✖ mutar: linha {args.line} fora do arquivo ({len(lines)} linhas)", file=sys.stderr)
        return 2

    try:
        mutated_line = OPERATORS[args.operator](lines[args.line - 1])
    except MutationNotApplicable as exc:
        print(f"✖ mutar: operador '{args.operator}' não aplicável à linha {args.line}: {exc}", file=sys.stderr)
        return 2

    with RestoreOnExit(target, original):
        lines[args.line - 1] = mutated_line
        target.write_text("".join(lines), encoding="utf-8", newline="")
        print(f"▶ mutar: {args.file}:{args.line} · operador={args.operator}")
        print(f"  original : {original.splitlines()[args.line - 1]}")
        print(f"  mutado   : {mutated_line.rstrip(chr(10))}")

        gate_cmd = ["./loop/gates.sh", "--level", str(args.level)]
        if args.scope:
            gate_cmd += ["--scope", args.scope]
        try:
            result = subprocess.run(gate_cmd, cwd=REPO_ROOT, timeout=args.timeout)
            gates_rc = result.returncode
        except subprocess.TimeoutExpired:
            print(f"✖ mutar: gate excedeu {args.timeout}s — abortando mutação (restauração garantida no finally)")
            return 2

    if gates_rc != 0:
        print(f"✔ mutar: mutação MORTA em {args.file}:{args.line} — o teste prova o que diz provar.")
        return 0

    print(f"⚠ mutar: mutação SOBREVIVEU em {args.file}:{args.line} ({args.operator}) — "
          f"achado, não anedota: vire correção de teste na mesma história "
          f"(RETROSPECTIVA.md §4, ação 2).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
