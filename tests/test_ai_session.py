import os
import pty
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch

from app.cli.main import _ai_session, app
from app.router import engine
from typer.testing import CliRunner
from tests.test_cli import MOCK_DATA, _mock_fetch, runner


def _fresh_store():
    from app.memory import MemoryStore
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    return MemoryStore(path=path)


def _patch_store(store):
    return patch("app.cli.main.get_store", return_value=store), \
           patch("app.cli.conversation.get_store", return_value=store), \
           patch("app.agent.core.get_store", return_value=store)


# --- Task 1: entry non-interaktif tetap help ---

@patch("app.agent.core.chat_completion", return_value="BBCA stabil.")
@patch.object(engine.provider, "fetch", side_effect=_mock_fetch)
def test_noargs_nontty_shows_help(mock_fetch, mock_llm_core):
    result = runner.invoke(app, [])
    assert result.exit_code in (0, 2)
    assert "Usage" in result.output, "non-TTY no-args harus menampilkan help"
    assert not mock_fetch.called, "non-TTY tidak boleh masuk sesi AI"


@patch.object(engine.provider, "fetch", side_effect=_mock_fetch)
def test_help_flag_never_opens_session(mock_fetch):
    with patch("app.cli.main.console.input") as mock_input:
        result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output
    assert not mock_input.called, "--help tidak boleh masuk sesi AI"


# --- Task 2: sesi AI unified (loop langsung, tanpa entry typer) ---

@patch("app.agent.core.chat_completion", return_value="BBCA stabil.")
@patch.object(engine.provider, "fetch", side_effect=_mock_fetch)
def test_session_analyze_and_saves_trace(mock_fetch, mock_llm_core):
    store = _fresh_store()
    p1, p2, p3 = _patch_store(store)
    with p1, p2, p3, patch("app.cli.main.console.input", side_effect=["analisa bbca", "exit"]):
        _ai_session()
    called = [c.args[0] for c in mock_fetch.call_args_list]
    assert "BBCA" in called, "sesi harus memproses pertanyaan lewat pipeline natural"
    assert any(e.source == "chat" for e in store.get_all()), "jejak percakapan tersimpan di memori"


@patch("app.agent.core.chat_completion", return_value="BBCA stabil.")
@patch.object(engine.provider, "fetch", side_effect=_mock_fetch)
def test_session_multiturn_followup(mock_fetch, mock_llm_core):
    store = _fresh_store()
    p1, p2, p3 = _patch_store(store)
    with p1, p2, p3, patch("app.cli.main.console.input", side_effect=["analisa bbca", "vs bri", "exit"]):
        _ai_session()
    called = [c.args[0] for c in mock_fetch.call_args_list]
    assert called.index("BBCA") < called.index("BBRI"), \
        "follow-up 'vs bri' di sesi harus ter-resolve dari konteks turn sebelumnya"


@patch.object(engine.provider, "fetch", side_effect=_mock_fetch)
def test_session_empty_no_memory_entry(mock_fetch):
    store = _fresh_store()
    p1, p2, p3 = _patch_store(store)
    with p1, p2, p3, patch("app.cli.main.console.input", side_effect=["exit"]):
        _ai_session()
    assert not any(e.source == "chat" for e in store.get_all()), "sesi kosong tanpa entri memori"


# --- Smoke: entry TTY via pty (perilaku nyata, bukan CliRunner) ---

def _run_in_pty(script: list[str], timeout: float = 30.0) -> tuple[int, str]:
    master, slave = pty.openpty()
    env = dict(os.environ)
    env["PYTHONUNBUFFERED"] = "1"
    proc = subprocess.Popen(script, stdin=slave, stdout=slave, stderr=slave, env=env, close_fds=True)
    os.close(slave)
    out = b""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            chunk = os.read(master, 4096)
        except OSError:
            break
        if not chunk:
            break
        out += chunk
        if b"Screening AI" in out:
            os.write(master, b"exit\n")
        if b"exit" in out.lower() and proc.poll() is not None:
            break
        if b"Ketik 'exit'" in out:
            os.write(master, b"exit\n")
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    os.close(master)
    return proc.returncode, out.decode(errors="replace")


def test_smoke_pty_noargs_opens_ai_session():
    code, out = _run_in_pty([sys.executable, "-m", "app.cli.main"])
    assert code == 0, f"exit {code}; output: {out[:400]}"
    assert "Screening AI" in out, "TTY no-args harus membuka sesi AI (banner tampil)"


def test_smoke_nontty_noargs_shows_help():
    proc = subprocess.run(
        [sys.executable, "-m", "app.cli.main"],
        input=b"", capture_output=True, timeout=30,
    )
    assert proc.returncode in (0, 2)
    assert b"Usage" in proc.stdout, "non-TTY no-args harus menampilkan help"
