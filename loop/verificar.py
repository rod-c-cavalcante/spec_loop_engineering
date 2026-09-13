#!/usr/bin/env python3
"""SpecLoop · verificar.py — ponto único de veredito (specs/002-fortalecimento-v4).

Wrapper único em volta de `gates.sh`. Duas garantias que `ralph.sh` chamando
`gates.sh` direto não dava:

  1. Cobertura de escopo é checada ANTES de gastar o gate (RF-03): se a
     história declara `e2eScope` e nenhum arquivo de teste referencia essa
     tag, falha rápido em vez de rodar a suíte inteira para nada.
  2. O veredito é ANULADO se a árvore de trabalho mudou durante a execução
     do gate (RF-04) — origem: RETROSPECTIVA-005-006.md §3.1 nº5 e §3.5,
     "gate impossível de fechar" / "editei a árvore durante o gate". Um
     artefato de teste versionado (ou qualquer edição concorrente) que muda
     a árvore no meio da corrida invalida a prova, mesmo que gates.sh tenha
     retornado 0.

Nunca leia o veredito deste script por um pipe que descarte `$?` — é
exatamente o anti-padrão que motivou o fix em ralph.sh (RF-05). Redirecione
para arquivo e leia o exit code direto, ou capture `$?` logo após a chamada.

Uso:
    python3 loop/verificar.py --story T-003 [--level 1] [--prd loop/prd.json]

Códigos de saída:
    0  gate passou e árvore estável
    1  gate reprovou (mesmo código que gates.sh retornaria)
    8  e2eScope declarado sem cobertura de teste correspondente
    9  árvore de trabalho mudou durante a execução do gate — veredito anulado
   10  erro de uso (história não encontrada, prd.json ausente, etc.)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True, **kwargs)


def _load_story(prd_path: Path, story_id: str) -> dict:
    if not prd_path.is_file():
        print(f"✖ verificar: {prd_path} não encontrado", file=sys.stderr)
        sys.exit(10)
    data = json.loads(prd_path.read_text(encoding="utf-8"))
    for story in data.get("userStories", []):
        if story.get("id") == story_id:
            return story
    print(f"✖ verificar: história '{story_id}' não existe em {prd_path}", file=sys.stderr)
    sys.exit(10)


def _scope_has_coverage(scope: str) -> bool:
    """RF-03: existe pelo menos um arquivo de teste que referencia a tag.

    --untracked é obrigatório: sem ele, git grep não enxerga um arquivo de
    teste recém-escrito e ainda não commitado — exatamente o caso normal de
    uso (o Builder escreve o teste na MESMA iteração antes de chamar este
    script). Achado do Verifier em specs/002-fortalecimento-v4 (reproduzido:
    tag presente só em arquivo untracked não era encontrada sem esta flag).
    """
    if not scope:
        return True
    result = _run(["git", "grep", "--untracked", "-l", "-F", scope, "--", "*test*", "*spec*"])
    return result.returncode == 0 and bool(result.stdout.strip())


def _tree_signature() -> str:
    """Hash do estado da árvore: conteúdo modificado + lista de status.

    Mesmos primitivos git que preflight.sh já usa para "tree limpo"
    (git status --porcelain) — aqui comparados antes/depois em vez de só
    checados uma vez, e reforçados com o diff de conteúdo (git diff HEAD)
    para pegar edição em arquivo que já estava sujo antes de começar.
    """
    status = _run(["git", "status", "--porcelain"]).stdout
    diff = _run(["git", "diff", "HEAD"]).stdout
    h = hashlib.sha256()
    h.update(status.encode("utf-8", "replace"))
    h.update(diff.encode("utf-8", "replace"))
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--story", required=True, help="ID da história em prd.json (ex.: T-003, S-RELEASE)")
    parser.add_argument("--prd", default="loop/prd.json", help="Caminho do prd.json (default: loop/prd.json)")
    parser.add_argument("--level", type=int, default=None, help="Nível do gate (default: 2 p/ S-RELEASE, senão 1)")
    args = parser.parse_args()

    prd_path = REPO_ROOT / args.prd
    story = _load_story(prd_path, args.story)
    scope = story.get("e2eScope", "")
    level = args.level if args.level is not None else (2 if args.story == "S-RELEASE" else 1)

    if scope and not _scope_has_coverage(scope):
        print(f"✖ verificar: e2eScope '{scope}' declarado na história '{args.story}' "
              f"sem nenhum arquivo de teste que o referencie — gate NÃO executado.")
        return 8

    before = _tree_signature()

    gate_cmd = ["./loop/gates.sh", "--level", str(level)]
    if scope:
        gate_cmd += ["--scope", scope]
    gate_result = _run(gate_cmd)
    print(gate_result.stdout, end="")
    print(gate_result.stderr, end="", file=sys.stderr)
    gates_rc = gate_result.returncode

    after = _tree_signature()

    if before != after:
        print(f"✖ verificar: a árvore de trabalho mudou durante a execução do gate "
              f"(história '{args.story}') — veredito ANULADO independente do resultado do "
              f"gates.sh (rc={gates_rc}). Rode de novo sobre árvore estável.")
        return 9

    return 0 if gates_rc == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
