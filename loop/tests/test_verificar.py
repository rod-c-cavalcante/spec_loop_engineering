"""Testes de loop/verificar.py — prova RF-03 e RF-04 (specs/002-fortalecimento-v4).

Todas as chamadas reais a git/gates.sh são mockadas: este teste prova o
COMPORTAMENTO do wrapper (escopo checado antes do gate, árvore comparada
antes/depois), não o resultado de uma corrida real de gate.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

MODULE_PATH = Path(__file__).resolve().parent.parent / "verificar.py"
spec = importlib.util.spec_from_file_location("verificar", MODULE_PATH)
verificar = importlib.util.module_from_spec(spec)
sys.modules["verificar"] = verificar
spec.loader.exec_module(verificar)


def _write_prd(tmp_path: Path, story: dict) -> Path:
    prd = {"feature": "teste", "userStories": [story]}
    path = tmp_path / "prd.json"
    path.write_text(json.dumps(prd), encoding="utf-8")
    return path


# ── _load_story ──────────────────────────────────────────────────────────

def test_load_story_encontra_por_id(tmp_path):
    prd_path = _write_prd(tmp_path, {"id": "T-001", "passes": False})
    story = verificar._load_story(prd_path, "T-001")
    assert story["id"] == "T-001"


def test_load_story_inexistente_sai_com_10(tmp_path):
    prd_path = _write_prd(tmp_path, {"id": "T-001", "passes": False})
    with pytest.raises(SystemExit) as exc:
        verificar._load_story(prd_path, "T-999")
    assert exc.value.code == 10


def test_load_story_prd_ausente_sai_com_10(tmp_path):
    with pytest.raises(SystemExit) as exc:
        verificar._load_story(tmp_path / "nao-existe.json", "T-001")
    assert exc.value.code == 10


# ── _scope_has_coverage ──────────────────────────────────────────────────

def test_scope_vazio_sempre_tem_cobertura():
    assert verificar._scope_has_coverage("") is True


def test_scope_com_match_tem_cobertura(monkeypatch):
    monkeypatch.setattr(verificar, "_run", lambda cmd: SimpleNamespace(returncode=0, stdout="tests/foo.test.js\n"))
    assert verificar._scope_has_coverage("@algo") is True


def test_scope_sem_match_nao_tem_cobertura(monkeypatch):
    monkeypatch.setattr(verificar, "_run", lambda cmd: SimpleNamespace(returncode=1, stdout=""))
    assert verificar._scope_has_coverage("@inexistente") is False


def test_scope_encontra_arquivo_de_teste_nao_commitado():
    """Regressão do achado do Verifier (specs/002-fortalecimento-v4): git grep
    SEM --untracked não via arquivo de teste recém-criado, ainda não
    commitado — exatamente o caso normal de uso (Builder escreve o teste na
    mesma iteração antes de chamar verificar.py). Usa git de verdade (não
    mocka _run) porque é precisamente o comportamento do git que estava
    quebrado."""
    tag = "@regressao-untracked-99887766"
    target = verificar.REPO_ROOT / "loop" / "tests" / "_tmp_untracked_scope_test.py"
    assert not target.exists(), "arquivo de fixture não deveria pré-existir"
    try:
        target.write_text(f"# {tag}\ndef test_x():\n    assert True\n", encoding="utf-8")
        assert verificar._scope_has_coverage(tag) is True
    finally:
        target.unlink(missing_ok=True)


# ── main(): RF-03 — falha rápido sem rodar o gate ────────────────────────

def test_main_escopo_sem_cobertura_nao_roda_gate(tmp_path, monkeypatch):
    prd_path = _write_prd(tmp_path, {"id": "T-001", "passes": False, "e2eScope": "@sem-teste"})
    calls = []

    def fake_run(cmd):
        calls.append(cmd)
        if cmd[:2] == ["git", "grep"]:
            return SimpleNamespace(returncode=1, stdout="")
        raise AssertionError(f"gate não deveria ser chamado, mas foi: {cmd}")

    monkeypatch.setattr(verificar, "_run", fake_run)
    monkeypatch.setattr(sys, "argv", ["verificar.py", "--story", "T-001", "--prd", str(prd_path)])

    rc = verificar.main()

    assert rc == 8
    assert not any(str(c[0]).endswith("gates.sh") for c in calls if c)


# ── main(): RF-04 — árvore mudou durante a execução do gate ─────────────

def test_main_arvore_mudou_anula_veredito(tmp_path, monkeypatch):
    prd_path = _write_prd(tmp_path, {"id": "T-002", "passes": False})
    signatures = iter(["hash-antes", "hash-depois"])

    monkeypatch.setattr(verificar, "_tree_signature", lambda: next(signatures))
    monkeypatch.setattr(verificar, "_run", lambda cmd: SimpleNamespace(returncode=0, stdout="", stderr=""))
    monkeypatch.setattr(sys, "argv", ["verificar.py", "--story", "T-002", "--prd", str(prd_path)])

    rc = verificar.main()

    assert rc == 9


def test_main_arvore_estavel_gate_verde_retorna_0(tmp_path, monkeypatch):
    prd_path = _write_prd(tmp_path, {"id": "T-002", "passes": False})

    monkeypatch.setattr(verificar, "_tree_signature", lambda: "hash-estavel")
    monkeypatch.setattr(verificar, "_run", lambda cmd: SimpleNamespace(returncode=0, stdout="", stderr=""))
    monkeypatch.setattr(sys, "argv", ["verificar.py", "--story", "T-002", "--prd", str(prd_path)])

    assert verificar.main() == 0


def test_main_arvore_estavel_gate_falha_retorna_1(tmp_path, monkeypatch):
    prd_path = _write_prd(tmp_path, {"id": "T-002", "passes": False})

    monkeypatch.setattr(verificar, "_tree_signature", lambda: "hash-estavel")
    monkeypatch.setattr(verificar, "_run", lambda cmd: SimpleNamespace(returncode=1, stdout="", stderr=""))
    monkeypatch.setattr(sys, "argv", ["verificar.py", "--story", "T-002", "--prd", str(prd_path)])

    assert verificar.main() == 1
