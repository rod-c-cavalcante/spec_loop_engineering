"""Testes de loop/diff_base.py — prova RF-01 a RF-05 (specs/003-verifier-padroes).

Sem mock: cada teste monta um repositório git real em tmp_path e roda o
script como processo, do jeito que o Verifier o chama.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "diff_base.py"


def _git(repo: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *args],
        cwd=repo, capture_output=True, text=True, check=True,
    )
    return out.stdout.strip()


def _commit(repo: Path, name: str, content: str) -> str:
    (repo / name).write_text(content, encoding="utf-8", newline="")
    _git(repo, "add", name)
    _git(repo, "commit", "-q", "-m", f"add {name}")
    return _git(repo, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    _git(tmp_path, "init", "-q")
    _commit(tmp_path, "a.txt", "primeiro\n")
    _commit(tmp_path, "b.txt", "segundo\n")
    _commit(tmp_path, "c.txt", "terceiro\n")
    return tmp_path


def _run(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=repo, capture_output=True, text=True, encoding="utf-8",
    )


# ── RF-01 ────────────────────────────────────────────────────────────────

def test_ref_inexistente_sai_com_2_sem_diff(repo):
    r = _run(repo, "--base", "branch-que-nao-existe")
    assert r.returncode == 2
    assert "branch-que-nao-existe" in r.stderr
    assert r.stdout == ""


# ── RF-02 ────────────────────────────────────────────────────────────────

def test_sem_diferenca_sai_com_3(repo):
    r = _run(repo, "--base", "HEAD")
    assert r.returncode == 3
    assert r.stdout == ""
    assert r.stderr.strip() != ""


# ── RF-03 ────────────────────────────────────────────────────────────────

def test_base_antiga_cobre_todos_os_commits_posteriores(repo):
    primeiro = _git(repo, "rev-list", "--max-parents=0", "HEAD")
    r = _run(repo, "--base", primeiro)
    assert r.returncode == 0
    assert "+segundo" in r.stdout
    assert "+terceiro" in r.stdout
    assert "+primeiro" not in r.stdout


def test_mudanca_nao_commitada_entra_no_diff(repo):
    (repo / "a.txt").write_text("primeiro\neditado\n", encoding="utf-8", newline="")
    r = _run(repo, "--base", "HEAD")
    assert r.returncode == 0
    assert "+editado" in r.stdout


# ── RF-04 ────────────────────────────────────────────────────────────────

def test_arquivo_nao_rastreado_e_anunciado_e_conta_como_trabalho(repo):
    (repo / "novo.txt").write_text("x\n", encoding="utf-8", newline="")
    r = _run(repo, "--base", "HEAD")
    assert r.returncode == 0
    assert "novo.txt" in r.stderr


def test_sem_nao_rastreados_stderr_fica_limpo(repo):
    r = _run(repo, "--base", "HEAD~1")
    assert r.returncode == 0
    assert r.stderr == ""


# ── RF-05 ────────────────────────────────────────────────────────────────

def test_base_padrao_e_o_commit_anterior(repo):
    r = _run(repo)
    assert r.returncode == 0
    assert "+terceiro" in r.stdout
    assert "+segundo" not in r.stdout
