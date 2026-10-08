"""Testes de loop/smoke.sh — prova RF-01 e RF-02 (specs/005-ci-do-template).

Roda o smoke.sh real num diretório temporário. A URL usada nos casos "com
produto" aponta para uma porta sem serviço: o smoke tem de falhar ali.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

LOOP_DIR = Path(__file__).resolve().parent.parent
BASH = shutil.which("bash")
SEM_SERVICO = "http://127.0.0.1:9"

pytestmark = pytest.mark.skipif(BASH is None, reason="smoke.sh exige bash")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / "loop").mkdir()
    shutil.copy(LOOP_DIR / "smoke.sh", tmp_path / "loop" / "smoke.sh")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    return tmp_path


def _run(repo: Path, **env: str) -> subprocess.CompletedProcess:
    base_env = {k: v for k, v in os.environ.items() if k not in ("BASE_URL", "SMOKE_REQUIRED")}
    return subprocess.run(
        [BASH, "loop/smoke.sh"], cwd=repo, env={**base_env, **env},
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )


# ── RF-01 ────────────────────────────────────────────────────────────────

def test_sem_produto_smoke_nao_se_aplica_e_avisa(repo):
    r = _run(repo)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "sem produto" in r.stdout
    assert "Traceback" not in r.stderr


# ── RF-02 (par discriminante: muda só a precondição) ─────────────────────

@pytest.mark.parametrize("marcador", ["package.json", "requirements.txt", "pyproject.toml"])
def test_com_marcador_de_produto_smoke_roda_e_falha_sem_servico(repo, marcador):
    (repo / marcador).write_text("{}\n", encoding="utf-8")
    r = _run(repo, BASE_URL=SEM_SERVICO)
    assert r.returncode != 0


def test_base_url_definida_torna_o_smoke_obrigatorio(repo):
    r = _run(repo, BASE_URL=SEM_SERVICO)
    assert r.returncode != 0
    assert "sem produto" not in r.stdout


def test_smoke_required_forca_os_checks_mesmo_sem_marcador(repo):
    r = _run(repo, SMOKE_REQUIRED="1")
    assert r.returncode != 0
    assert "sem produto" not in r.stdout
