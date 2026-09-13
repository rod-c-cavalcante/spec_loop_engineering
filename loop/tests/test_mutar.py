"""Testes de loop/mutar.py — prova RF-01 e RF-02 (specs/002-fortalecimento-v4).

Carrega mutar.py por caminho (não é pacote instalado) e usa um arquivo de
fixture isolado em loop/tests/fixtures/ para nunca mutar o próprio código do
template (mitigação descrita em plan.md, seção Riscos).
"""
from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

MODULE_PATH = Path(__file__).resolve().parent.parent / "mutar.py"
spec = importlib.util.spec_from_file_location("mutar", MODULE_PATH)
mutar = importlib.util.module_from_spec(spec)
sys.modules["mutar"] = mutar
spec.loader.exec_module(mutar)

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample_target.py"


# ── operadores puros (sem tocar disco) ──────────────────────────────────────

def test_mutate_negacao_python():
    result = mutar.mutate_negacao("    if is_valid(x):\n")
    assert "not (" in result
    assert result.endswith(":\n")


def test_mutate_negacao_sem_condicao_levanta():
    with pytest.raises(mutar.MutationNotApplicable):
        mutar.mutate_negacao("    return 42\n")


def test_mutate_negacao_com_chamada_de_funcao_produz_python_valido():
    """Regressão do achado do Verifier (specs/002-fortalecimento-v4): a
    versão anterior engolia o ')' de chamadas de função aninhadas e
    produzia SyntaxError — sem que nenhum teste percebesse, porque só se
    checava substring. Este teste valida SINTAXE, não substring."""
    result = mutar.mutate_negacao("    if is_valid(x):\n")
    assert result.count("(") == result.count(")")
    ast.parse(f"def f(x):\n{result}        pass\n")


def test_mutate_negacao_com_chamada_de_metodo_encadeada():
    result = mutar.mutate_negacao("    if self.is_ready(a, b):\n")
    assert result.count("(") == result.count(")")
    ast.parse(f"def f(self, a, b):\n{result}        pass\n")


def test_mutate_negacao_clike_com_chamada_de_funcao_aninhada():
    """Mesma regressão, branch C-like (JS/TS/Java) — sem teste algum antes."""
    result = mutar.mutate_negacao("    if (isValid(x)) {\n")
    assert result.count("(") == result.count(")")
    assert result.rstrip("\n").endswith("{")


def test_mutate_relacional_troca_menor_que():
    result = mutar.mutate_relacional("    if idade < 18:\n")
    assert "idade >= 18" in result


def test_mutate_relacional_nao_confunde_com_lte():
    # "<=" não deve ser tratado como "<" isolado
    result = mutar.mutate_relacional("    if nota <= 7:\n")
    assert "nota > 7" in result


def test_mutate_relacional_sem_operador_levanta():
    with pytest.raises(mutar.MutationNotApplicable):
        mutar.mutate_relacional("    return nome\n")


def test_mutate_await_remove_primeira_ocorrencia():
    result = mutar.mutate_await("    resultado = await session.delete(obj)\n")
    assert "await " not in result
    assert "session.delete(obj)" in result


def test_mutate_await_sem_await_levanta():
    with pytest.raises(mutar.MutationNotApplicable):
        mutar.mutate_await("    session.delete(obj)\n")


# ── restauração garantida (RF-01) ───────────────────────────────────────────

def test_restore_on_exit_restaura_ao_sair_normalmente(tmp_path):
    target = tmp_path / "alvo.py"
    original = "if a < b:\n    pass\n"
    target.write_text(original, encoding="utf-8")

    with mutar.RestoreOnExit(target, original):
        target.write_text("if a >= b:\n    pass\n", encoding="utf-8")
        assert target.read_text(encoding="utf-8") != original

    assert target.read_text(encoding="utf-8") == original


def test_restore_on_exit_restaura_em_sinal_simulado(tmp_path):
    """Simula o timeout/SIGTERM que deixou arquivo mutado na retro original
    (RETROSPECTIVA-005-006.md §5, ação 6) — chama o handler de sinal
    diretamente em vez de enviar um sinal real de SO (portável e determinístico
    em CI/Windows)."""
    target = tmp_path / "alvo.py"
    original = "if a < b:\n    pass\n"
    target.write_text(original, encoding="utf-8")

    guard = mutar.RestoreOnExit(target, original)
    guard.__enter__()
    target.write_text("MUTADO\n", encoding="utf-8")
    assert target.read_text(encoding="utf-8") == "MUTADO\n"

    with pytest.raises(SystemExit):
        guard._on_signal(15, None)  # SIGTERM

    assert target.read_text(encoding="utf-8") == original


# ── fluxo completo via main() com gate mockado ──────────────────────────────

def _fixture_original() -> str:
    return FIXTURE.read_text(encoding="utf-8")


def test_main_mutacao_morta_gate_reprova(monkeypatch):
    original = _fixture_original()
    lines = original.splitlines()
    target_line = next(i for i, line in enumerate(lines, start=1) if "if " in line and ":" in line)

    monkeypatch.setattr(mutar.subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=1))
    argv = ["mutar.py", "--file", str(FIXTURE.relative_to(mutar.REPO_ROOT)),
            "--line", str(target_line), "--operator", "negacao"]
    monkeypatch.setattr(sys, "argv", argv)

    rc = mutar.main()

    assert rc == 0  # mutação morta
    assert FIXTURE.read_text(encoding="utf-8") == original  # restaurado


def test_main_mutacao_sobrevive_gate_aprova(monkeypatch):
    original = _fixture_original()
    lines = original.splitlines()
    target_line = next(i for i, line in enumerate(lines, start=1) if "if " in line and ":" in line)

    monkeypatch.setattr(mutar.subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=0))
    argv = ["mutar.py", "--file", str(FIXTURE.relative_to(mutar.REPO_ROOT)),
            "--line", str(target_line), "--operator", "negacao"]
    monkeypatch.setattr(sys, "argv", argv)

    rc = mutar.main()

    assert rc == 1  # mutação sobreviveu: achado
    assert FIXTURE.read_text(encoding="utf-8") == original  # restaurado de qualquer forma


def test_main_operador_nao_aplicavel_retorna_2(monkeypatch):
    original = _fixture_original()
    argv = ["mutar.py", "--file", str(FIXTURE.relative_to(mutar.REPO_ROOT)),
            "--line", "1", "--operator", "await"]
    monkeypatch.setattr(sys, "argv", argv)

    rc = mutar.main()

    assert rc == 2
    assert FIXTURE.read_text(encoding="utf-8") == original
