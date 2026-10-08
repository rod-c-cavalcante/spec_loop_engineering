"""Testes de loop/ralph.sh — prova RF-01 a RF-08 (specs/004-revisao-antes-do-commit).

Roda o ralph.sh REAL num repositório git temporário. Só é falso o que está na
fronteira do sistema: o LLM (Builder e Verifier, scripts que obedecem a uma
fila de vereditos) e os gates do produto (stub com exit code controlado).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

LOOP_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = LOOP_DIR.parent
BASH = shutil.which("bash")

pytestmark = pytest.mark.skipif(
    BASH is None or shutil.which("jq") is None, reason="ralph.sh exige bash e jq"
)

FAKE_BUILDER = r"""#!/usr/bin/env bash
cat > /dev/null
echo x >> "$CTL/builder_calls"
[[ -f state/review.md ]] && cp state/review.md "$CTL/review_seen_by_builder"
echo "linha $(wc -l < "$CTL/builder_calls")" >> work.txt
id=$(jq -r '[.userStories[] | select(.passes == false)][0].id // "none"' loop/prd.json | tr -d '\r')
[[ "$id" == "none" ]] && exit 0
jq --arg id "$id" '(.userStories[] | select(.id==$id) | .passes) = true' loop/prd.json | tr -d '\r' > loop/prd.json.tmp
mv loop/prd.json.tmp loop/prd.json
[[ -n "${NO_MSG:-}" ]] || echo "feat(x): $id pronto, refs specs/x/spec.md" > state/.commit_msg
"""

FAKE_VERIFIER = r"""#!/usr/bin/env bash
cat > "$CTL/verifier_stdin"
echo x >> "$CTL/verifier_calls"
git rev-parse HEAD >> "$CTL/head_at_verify"
git status --porcelain > "$CTL/status_at_verify"
story=$(sed -n 's/^STORY=//p' "$CTL/verifier_stdin" | tr -d '\r')
v=$(head -n1 "$CTL/queue")
sed -i 1d "$CTL/queue"
if [[ -z "$v" ]]; then echo "nao consegui concluir a auditoria"; exit 0; fi
echo "VEREDITO: $v"
if [[ "$v" == "REPROVADO" ]]; then
  echo "AÇÕES (só se REPROVADO):"
  echo "- corrija o campo X em work.txt"
fi
echo "2026-01-01T00:00:00,$story,$v," >> state/verdicts.csv
"""

FAKE_GATES = r"""#!/usr/bin/env bash
exit "$(cat "$CTL/gates_rc" 2>/dev/null || echo 0)"
"""


def _git(repo: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *args],
        cwd=repo, capture_output=True, text=True, check=True,
    )
    return out.stdout.strip()


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="")
    os.chmod(path, 0o755)


class Loop:
    def __init__(self, tmp_path: Path, risk: str):
        self.repo = tmp_path / "repo"
        self.ctl = tmp_path / "ctl"
        self.bin = tmp_path / "bin"
        self.ctl.mkdir(parents=True)
        _write(self.bin / "builder.sh", FAKE_BUILDER)
        _write(self.bin / "verifier.sh", FAKE_VERIFIER)
        _write(self.repo / "loop" / "gates.sh", FAKE_GATES)
        _write(self.repo / "loop" / "PROMPT_BUILD.md", "builder\n")
        _write(self.repo / "loop" / "PROMPT_VERIFY.md", "verifier\n")
        shutil.copy(LOOP_DIR / "ralph.sh", self.repo / "loop" / "ralph.sh")
        shutil.copy(REPO_ROOT / ".gitignore", self.repo / ".gitignore")
        prd = {
            "feature": "teste", "specPath": "specs/x/spec.md",
            "userStories": [{"id": "T-001", "title": "t", "passes": False, "risk": risk}],
        }
        _write(self.repo / "loop" / "prd.json", json.dumps(prd, indent=2) + "\n")
        _write(self.repo / "state" / "verdicts.csv", "timestamp,story,verdict,gap\n")
        _git(self.repo, "init", "-q")
        _git(self.repo, "add", "-A")
        _git(self.repo, "commit", "-q", "-m", "base")
        self.base = _git(self.repo, "rev-parse", "HEAD")

    def run(self, queue: list[str], **env: str) -> subprocess.CompletedProcess:
        (self.ctl / "queue").write_text("".join(v + "\n" for v in queue), encoding="utf-8", newline="")
        full_env = {
            **os.environ,
            "CTL": self.ctl.as_posix(),
            "AGENT_CMD": f"bash {(self.bin / 'builder.sh').as_posix()}",
            "VERIFY_CMD": f"bash {(self.bin / 'verifier.sh').as_posix()}",
            "SKIP_PREFLIGHT": "1", "NO_CHECKPOINT": "1", "MAX_ITERATIONS": "6",
            "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
            "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
            **env,
        }
        return subprocess.run(
            [BASH, "loop/ralph.sh"], cwd=self.repo, env=full_env,
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )

    def calls(self, who: str) -> int:
        f = self.ctl / f"{who}_calls"
        return len(f.read_text().splitlines()) if f.exists() else 0

    def commits(self) -> int:
        return int(_git(self.repo, "rev-list", "--count", f"{self.base}..HEAD"))

    def passes(self) -> bool:
        prd = json.loads((self.repo / "loop" / "prd.json").read_text(encoding="utf-8"))
        return prd["userStories"][0]["passes"]

    def review(self) -> Path:
        return self.repo / "state" / "review.md"


@pytest.fixture
def loop(tmp_path: Path) -> Loop:
    return Loop(tmp_path, risk="normal")


# ── RF-01 + RF-02 ────────────────────────────────────────────────────────

def test_aprovado_verifier_roda_antes_do_commit_e_loop_commita(loop):
    r = loop.run(["APROVADO"])
    assert r.returncode == 0, r.stdout + r.stderr
    # no momento da auditoria ainda não havia commit e o trabalho estava na árvore
    assert (loop.ctl / "head_at_verify").read_text().split() == [loop.base]
    assert "work.txt" in (loop.ctl / "status_at_verify").read_text()
    stdin = (loop.ctl / "verifier_stdin").read_text(encoding="utf-8")
    assert "STORY=T-001" in stdin
    assert f"BASE={loop.base}" in stdin
    assert loop.commits() == 1
    assert _git(loop.repo, "log", "-1", "--format=%s") == "feat(x): T-001 pronto, refs specs/x/spec.md"
    assert "work.txt" in _git(loop.repo, "show", "--name-only", "--format=", "HEAD")
    assert _git(loop.repo, "status", "--porcelain") == ""
    assert not loop.review().exists()


# ── RF-03 ────────────────────────────────────────────────────────────────

def test_reprovado_volta_ao_builder_sem_commit_e_depois_commita(loop):
    r = loop.run(["REPROVADO", "APROVADO"])
    assert r.returncode == 0, r.stdout + r.stderr
    assert loop.calls("builder") == 2
    assert loop.calls("verifier") == 2
    # as duas auditorias viram o mesmo HEAD: nada foi commitado entre elas
    assert (loop.ctl / "head_at_verify").read_text().split() == [loop.base, loop.base]
    seen = (loop.ctl / "review_seen_by_builder").read_text(encoding="utf-8")
    assert "T-001" in seen
    assert "corrija o campo X em work.txt" in seen
    assert loop.commits() == 1
    assert loop.passes() is True
    assert not loop.review().exists()


# ── RF-04 ────────────────────────────────────────────────────────────────

def test_teto_de_retrabalho_sai_com_7_sem_commit(loop):
    r = loop.run(["REPROVADO", "REPROVADO", "REPROVADO", "APROVADO"], MAX_REWORK="2")
    assert r.returncode == 7, r.stdout + r.stderr
    assert loop.calls("builder") == 3
    assert loop.commits() == 0
    assert loop.passes() is False
    assert loop.review().exists()
    # o loop reescreveu o prd.json (passes revertido) sem trocar o fim de linha
    assert b"\r" not in (loop.repo / "loop" / "prd.json").read_bytes()


# ── RF-05 ────────────────────────────────────────────────────────────────

def test_veredito_ilegivel_sai_com_8_sem_commit(loop):
    r = loop.run([])
    assert r.returncode == 8, r.stdout + r.stderr
    assert loop.calls("verifier") == 1
    assert loop.commits() == 0


# ── RF-06 ────────────────────────────────────────────────────────────────

def test_risk_low_commita_sem_verifier(tmp_path):
    loop = Loop(tmp_path, risk="low")
    r = loop.run([])
    assert r.returncode == 0, r.stdout + r.stderr
    assert loop.calls("verifier") == 0
    assert loop.commits() == 1


def test_verify_risks_restrito_dispensa_normal_mas_nunca_high(tmp_path):
    normal = Loop(tmp_path / "n", risk="normal")
    assert normal.run([], VERIFY_RISKS="high").returncode == 0
    assert normal.calls("verifier") == 0

    high = Loop(tmp_path / "h", risk="high")
    assert high.run(["APROVADO"], VERIFY_RISKS="").returncode == 0
    assert high.calls("verifier") == 1
    assert high.commits() == 1


# ── RF-07 ────────────────────────────────────────────────────────────────

def test_gates_vermelhos_revertem_passes_sem_commit_nem_verifier(loop):
    (loop.ctl / "gates_rc").write_text("1")
    r = loop.run(["APROVADO"], MAX_ITERATIONS="1")
    assert r.returncode == 1, r.stdout + r.stderr
    assert loop.passes() is False
    assert loop.calls("verifier") == 0
    assert loop.commits() == 0


# ── RF-08 ────────────────────────────────────────────────────────────────

def test_sem_mensagem_do_builder_commit_ainda_referencia_a_spec(loop):
    r = loop.run(["APROVADO"], NO_MSG="1")
    assert r.returncode == 0, r.stdout + r.stderr
    subject = _git(loop.repo, "log", "-1", "--format=%s")
    assert "T-001" in subject
    assert "refs specs/x/spec.md" in subject
