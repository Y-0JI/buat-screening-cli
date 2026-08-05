import os
import tempfile
from unittest.mock import patch

from typer.testing import CliRunner

from app.cli import conversation
from app.cli.conversation import ConversationState, recent, record, resolve_followup
from app.cli.main import app
from app.router import engine
from tests.test_cli import MOCK_DATA, _mock_fetch, runner


def _fresh_store():
    from app.memory import MemoryStore
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    return MemoryStore(path=path)


def _state(workflow="analyze", tickers=("BBRI",), query="analisa bbri"):
    return ConversationState(workflow=workflow, tickers=tickers, query=query)


# --- Task 1: conversation state round-trip ---

def test_record_recent_roundtrip():
    store = _fresh_store()
    with patch("app.cli.conversation.get_store", return_value=store):
        assert recent() is None, "tanpa aksi -> tanpa state"
        record("analyze", ["BBRI"], "analisa bbri")
        s = recent()
        assert s is not None and s.workflow == "analyze" and s.tickers == ("BBRI",) and s.query == "analisa bbri"


def test_record_overwrites_previous_state():
    store = _fresh_store()
    with patch("app.cli.conversation.get_store", return_value=store):
        record("analyze", ["BBRI"], "analisa bbri")
        record("compare", ["BBRI", "BBCA"], "bandingkan bbri dan bbca")
        entries = [e for e in store.get_all() if e.source == "conversation"]
        assert len(entries) == 1, "satu entri rolling, bukan menumpuk"
        s = recent()
        assert s.workflow == "compare" and s.tickers == ("BBRI", "BBCA")


# --- Task 2: resolver per pola ---

def test_resolve_compare_one():
    assert resolve_followup("bandingkan dengan bbca", _state(), None) == "bandingkan BBRI dan BBCA"
    assert resolve_followup("bandingkan bbca", _state(), None) == "bandingkan BBRI dan BBCA"
    assert resolve_followup("vs bbca", _state(), None) == "bandingkan BBRI dan BBCA"


def test_resolve_analyze_other():
    for q in ("kalau bbca gimana?", "kalau bbca", "gimana dengan bbca?", "bagaimana dengan bbca?", "terus bbca?"):
        assert resolve_followup(q, _state(), None) == "analisa BBCA", q


def test_resolve_pronoun():
    assert resolve_followup("bandingkan dia dengan bbni", _state(), None) == "bandingkan BBRI dengan bbni"
    assert resolve_followup("bandingkan saham itu dengan bbni", _state(), None) == "bandingkan BBRI dengan bbni"
    assert resolve_followup("kalau dia gimana?", _state(), None) == "analisa BBRI"


def test_resolve_no_context_or_pattern():
    assert resolve_followup("bandingkan dengan bbca", None, None) is None
    assert resolve_followup("analisa bbca", _state(), None) is None, "query jelas bukan follow-up"
    assert resolve_followup("bandingkan bca dan bri", _state(), None) is None, "compare 2 ticker tak perlu konteks"
    assert resolve_followup("apa itu dividen", _state(), None) is None, "pronoun tanpa pola follow-up tidak disentuh"


def test_resolve_multi_hop_sequence():
    store = _fresh_store()
    with patch("app.cli.conversation.get_store", return_value=store):
        record("analyze", ["BBRI"], "analisa bbri")
        s = recent()
        r1 = resolve_followup("kalau bbca gimana?", s, None)
        assert r1 == "analisa BBCA"
        record("analyze", ["BBCA"], r1)
        r2 = resolve_followup("bandingkan dengan bbni", recent(), None)
        assert r2 == "bandingkan BBCA dan BBNI", "hop berikutnya pakai konteks terbaru, bukan turn pertama"


# --- Task 3: integrasi natural (lintas invocation) ---

@patch("app.agent.core.chat_completion", return_value="BBRI stabil.")
@patch.object(engine.provider, "fetch", side_effect=_mock_fetch)
def test_natural_multi_turn_sequence(mock_fetch, mock_llm_core):
    store = _fresh_store()
    with patch("app.cli.main.get_store", return_value=store), patch("app.agent.core.get_store", return_value=store):
        r1 = runner.invoke(app, ["natural", "analisa bbri"])
        r2 = runner.invoke(app, ["natural", "kalau bbca gimana?"])
        r3 = runner.invoke(app, ["natural", "bandingkan dengan bbni"])
    called = [c.args[0] for c in mock_fetch.call_args_list]
    assert r1.exit_code == 0 and r2.exit_code == 0 and r3.exit_code == 0
    assert "BBRI" in called and "BBCA" in called and "BBNI" in called
    assert called.index("BBCA") > called.index("BBRI")
    assert called.index("BBNI") > called.index("BBCA")


@patch.object(engine.provider, "fetch", side_effect=_mock_fetch)
def test_failed_action_keeps_previous_state(mock_fetch):
    store = _fresh_store()
    with patch("app.cli.conversation.get_store", return_value=store), patch("app.cli.main.get_store", return_value=store):
        record("analyze", ["BBRI"], "analisa bbri")
        r = runner.invoke(app, ["natural", "analisa tickerTIDAKADA"])
        s = recent()
    assert r.exit_code in (0, 1)
    assert s is not None and s.tickers == ("BBRI",), "aksi gagal/batal -> state lama utuh"


# --- Task 4: integrasi chat ---

@patch("app.agent.core.chat_completion", return_value="BBCA stabil.")
@patch.object(engine.provider, "fetch", side_effect=_mock_fetch)
def test_chat_resolves_followup_consistently(mock_fetch, mock_llm_core):
    store = _fresh_store()
    with patch("app.cli.main.get_store", return_value=store), patch("app.cli.conversation.get_store", return_value=store), patch("app.agent.core.get_store", return_value=store):
        record("analyze", ["BBCA"], "analisa bbca")
        inputs = ["vs bri", "exit"]
        with patch("app.cli.main.console.input", side_effect=inputs):
            result = runner.invoke(app, ["chat"])
    called = [c.args[0] for c in mock_fetch.call_args_list]
    assert result.exit_code == 0
    assert "BBCA" in called and "BBRI" in called, "follow-up di chat ter-resolve konsisten dengan natural"
