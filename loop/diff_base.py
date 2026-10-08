#!/usr/bin/env python3
"""SpecLoop · diff_base.py — ponto fixo do Verifier (specs/003-verifier-padroes).

Entrega o diff que o Verifier audita: do ref base até a árvore de trabalho
(todos os commits depois do ref + mudanças não commitadas). `git show HEAD`
só via o último commit — história com commit de correção após um REPROVADO
ficava parcialmente fora da auditoria.

Falha ANTES da auditoria quando não há o que auditar: ref digitado errado ou
diff vazio viram erro legível aqui, não um veredito sobre nada.

Uso:
    python3 loop/diff_base.py [--base <ref>]      # padrão: HEAD~1

Saída: diff em stdout; avisos em stderr (arquivos não rastreados não aparecem
em `git diff` — são listados para o Verifier ler direto).

Códigos de saída:
    0  há diff a auditar
    2  ref base não resolve para um commit
    3  nada a auditar (sem diff e sem arquivo não rastreado)
"""
from __future__ import annotations

import argparse
import subprocess
import sys

BASE_PADRAO = "HEAD~1"


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], capture_output=True)


def _resolve(ref: str) -> str | None:
    r = _git("rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
    return r.stdout.decode().strip() if r.returncode == 0 else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", default=BASE_PADRAO)
    args = parser.parse_args(argv)

    # stderr em UTF-8 mesmo com pipe no Windows (cp1252 não codifica "✖").
    sys.stderr.reconfigure(encoding="utf-8")

    sha = _resolve(args.base)
    if sha is None:
        print(f"✖ diff_base: ref '{args.base}' não resolve para um commit", file=sys.stderr)
        return 2

    diff = _git("diff", sha).stdout
    untracked = _git("ls-files", "--others", "--exclude-standard").stdout.decode("utf-8", "replace").split("\n")
    untracked = [f for f in untracked if f]

    if not diff and not untracked:
        print(f"✖ diff_base: nada a auditar entre '{args.base}' e a árvore de trabalho", file=sys.stderr)
        return 3

    if untracked:
        print("⚠ diff_base: arquivos não rastreados (fora do diff — leia direto):", file=sys.stderr)
        for f in untracked:
            print(f"    {f}", file=sys.stderr)

    # bytes direto: o diff pode conter qualquer encoding dos arquivos do repo.
    sys.stdout.buffer.write(diff)
    return 0


if __name__ == "__main__":
    sys.exit(main())
