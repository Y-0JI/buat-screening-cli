import os
import tempfile
from datetime import date, timedelta
from unittest.mock import patch

from typer.testing import CliRunner
from app.cli.main import app
from app.models.stock import HistoricalPrice, StockInfo, StockData
from app.router import engine
from app.models.symbol import SymbolInfo
from app.services.watchlist import create as wl_create, add_symbol as wl_add, reset_data
from app.storage import set_test_backend
from app.storage.local import LocalJsonStorage

runner = CliRunner()


def _make_mock_data(ticker: str, name: str, sector: str, days: int = 60) -> StockData:
    base_prices = {"BBCA": 10000, "BBRI": 5000}
    base = base_prices.get(ticker, 5000)
    return StockData(
        info=StockInfo(ticker=ticker, name=name, sector=sector, market_cap=base * 1_000_000, currency="IDR"),
        history=[
            HistoricalPrice(
                date=date.today() - timedelta(days=days - i),
                open=base + i * 10,
                high=base + i * 10 + 50,
                low=base + i * 10 - 50,
                close=base + i * 10,
                volume=1_000_000 + i * 1000,
            )
            for i in range(days)
        ],
    )


MOCK_DATA = {
    "BBCA": _make_mock_data("BBCA", "PT Bank Central Asia Tbk.", "Financials"),
    "BBRI": _make_mock_data("BBRI", "PT Bank Rakyat Indonesia Tbk.", "Financials"),
}


def _mock_fetch(ticker, *args, **kwargs):
    return MOCK_DATA.get(ticker.upper())


@patch.object(engine.provider, "fetch", side_effect=_mock_fetch)
def test_analyze_command(mock_fetch):
    result = runner.invoke(app, ["analyze", "BBCA"])
    assert result.exit_code == 0


@patch.object(engine.provider, "fetch", side_effect=_mock_fetch)
def test_trend_command(mock_fetch):
    result = runner.invoke(app, ["trend", "BBCA"])
    assert result.exit_code == 0


@patch.object(engine.provider, "fetch", side_effect=_mock_fetch)
def test_score_command(mock_fetch):
    result = runner.invoke(app, ["score", "BBCA"])
    assert result.exit_code == 0


def test_info_command():
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0


@patch.object(engine.provider, "fetch", side_effect=_mock_fetch)
def test_compare_comma(mock_fetch):
    result = runner.invoke(app, ["compare", "BBCA,BBRI"])
    assert result.exit_code == 0
    assert "Perbandingan" in result.output


@patch.object(engine.provider, "fetch", side_effect=_mock_fetch)
def test_compare_space(mock_fetch):
    result = runner.invoke(app, ["compare", "BBCA", "BBRI"])
    assert result.exit_code == 0


@patch.object(engine.provider, "fetch", side_effect=_mock_fetch)
@patch("app.cli.main.get_discovered_tickers", return_value=[
    SymbolInfo(ticker="BBCA", name="PT Bank Central Asia Tbk.", sector="Financials"),
    SymbolInfo(ticker="BBRI", name="PT Bank Rakyat Indonesia Tbk.", sector="Financials"),
])
def test_screen_command(mock_stocks, mock_fetch):
    result = runner.invoke(app, ["screen", "--limit", "3"])
    assert result.exit_code == 0


@patch.object(engine.provider, "fetch", side_effect=_mock_fetch)
@patch("app.cli.main.get_discovered_tickers", return_value=[
    SymbolInfo(ticker="BBCA", name="PT Bank Central Asia Tbk.", sector="Financials"),
    SymbolInfo(ticker="BBRI", name="PT Bank Rakyat Indonesia Tbk.", sector="Financials"),
])
def test_gainers_command(mock_stocks, mock_fetch):
    result = runner.invoke(app, ["gainers"])
    assert result.exit_code == 0


@patch.object(engine.provider, "fetch", side_effect=_mock_fetch)
@patch("app.cli.main.get_discovered_tickers", return_value=[
    SymbolInfo(ticker="BBCA", name="PT Bank Central Asia Tbk.", sector="Financials"),
    SymbolInfo(ticker="BBRI", name="PT Bank Rakyat Indonesia Tbk.", sector="Financials"),
])
def test_losers_command(mock_stocks, mock_fetch):
    result = runner.invoke(app, ["losers"])
    assert result.exit_code == 0


@patch.object(engine.provider, "fetch", side_effect=_mock_fetch)
@patch("app.cli.main.get_discovered_tickers", return_value=[
    SymbolInfo(ticker="BBCA", name="PT Bank Central Asia Tbk.", sector="Financials"),
    SymbolInfo(ticker="BBRI", name="PT Bank Rakyat Indonesia Tbk.", sector="Financials"),
])
def test_sector_command(mock_stocks, mock_fetch):
    result = runner.invoke(app, ["sector", "Financials"])
    assert result.exit_code == 0


def test_stocks_command():
    result = runner.invoke(app, ["stocks"])
    assert result.exit_code == 0


@patch.object(engine.provider, "fetch", side_effect=_mock_fetch)
def test_natural_analyze(mock_fetch):
    result = runner.invoke(app, ["natural", "analisa BBCA"])
    assert result.exit_code in (0, 1)


@patch.object(engine.provider, "fetch", side_effect=_mock_fetch)
def test_natural_compare(mock_fetch):
    result = runner.invoke(app, ["natural", "bandingkan BBCA dan BBRI"])
    assert result.exit_code in (0, 1)


def test_natural_help():
    result = runner.invoke(app, ["natural", "info"])
    assert result.exit_code == 0


def test_natural_unknown():
    result = runner.invoke(app, ["natural", "lalala"])
    assert result.exit_code == 0


@patch.object(engine.provider, "fetch")
def test_natural_ambiguity_no_fetch(mock_fetch):
    with patch("app.cli.main.get_all", return_value=[
        {"ticker": "BBCA", "name": "Bank Central Asia Tbk."},
        {"ticker": "BBRI", "name": "Bank Rakyat Indonesia Tbk."},
    ]):
        result = runner.invoke(app, ["natural", "bandingkan xyz dan abc"])
    assert result.exit_code == 0, "ambigu harus batal dengan pesan, bukan error"
    mock_fetch.assert_not_called(), "ambigu tidak boleh memicu fetch"


@patch.object(engine.provider, "fetch")
def test_research_ambiguity_no_fetch(mock_fetch):
    with patch("app.cli.main.get_all", return_value=[
        {"ticker": "BBCA", "name": "Bank Central Asia Tbk."},
        {"ticker": "BBRI", "name": "Bank Rakyat Indonesia Tbk."},
    ]):
        result = runner.invoke(app, ["research", "bandingkan xyz dan abc"])
    assert result.exit_code == 0
    mock_fetch.assert_not_called()


def test_resolve_ambiguity_menu():
    from app.cli.main import _resolve_ambiguity
    with patch("sys.stdin.isatty", return_value=True), patch("app.cli.main.console.input", return_value="2"):
        assert _resolve_ambiguity(["BBCA", "BBRI", "BMRI"]) == "BBRI"
    with patch("sys.stdin.isatty", return_value=True), patch("app.cli.main.console.input", return_value="9"):
        assert _resolve_ambiguity(["BBCA"]) is None, "nomor di luar rentang = batal"
    with patch("sys.stdin.isatty", return_value=False):
        assert _resolve_ambiguity(["BBCA"]) is None, "non-TTY tidak boleh prompt"
    assert _resolve_ambiguity([]) is None


def test_substitute_ticker_keeps_query_structure():
    from app.cli.main import _substitute_ticker
    assert _substitute_ticker("bandingkan bca dan telekomunikasi", ["telekomunikasi"], "MTEL") == "bandingkan bca dan MTEL"
    assert _substitute_ticker("Analisa Telekomunikasi", ["telekomunikasi"], "MTEL") == "Analisa MTEL", "case-insensitive"
    assert _substitute_ticker("bandingkan bca dan xyz", ["xyz"], "BBRI") == "bandingkan bca dan BBRI"
    assert _substitute_ticker("bandingkan bca dan xyz", ["abc"], "BBRI") == "bandingkan bca dan xyz", "token tak ada = no-op"


@patch("app.agent.core.chat_completion", return_value="Perbandingan: BBCA vs MTEL")
@patch.object(engine.provider, "fetch", side_effect=_mock_fetch)
def test_natural_ambiguity_compare_keeps_intent(mock_fetch, mock_llm):
    with patch("app.cli.main._resolve_ambiguity_flow", return_value="MTEL"), patch("app.cli.main.get_all", return_value=[
        {"ticker": "BBCA", "name": "Bank Central Asia Tbk."},
        {"ticker": "MTEL", "name": "Mitra Telekomunikasi Indonesia Tbk."},
    ]):
        result = runner.invoke(app, ["natural", "bandingkan bca dan telekomunikasi"])
    called = [c.args[0] for c in mock_fetch.call_args_list]
    assert "BCA" in called and "MTEL" in called, "maksud compare harus dipertahankan, bukan analyze tunggal"


@patch("app.agent.research.chat_completion")
@patch("app.agent.core.chat_completion")
@patch.object(engine.provider, "fetch", side_effect=_mock_fetch)
def test_research_ambiguity_compare_keeps_intent(mock_fetch, mock_llm_core, mock_llm_research):
    with patch("app.cli.main._resolve_ambiguity_flow", return_value="MTEL"), patch("app.cli.main.get_all", return_value=[
        {"ticker": "BBCA", "name": "Bank Central Asia Tbk."},
        {"ticker": "MTEL", "name": "Mitra Telekomunikasi Indonesia Tbk."},
    ]):
        result = runner.invoke(app, ["research", "bandingkan bca dan telekomunikasi"])
    called = [c.args[0] for c in mock_fetch.call_args_list]
    assert "BCA" in called and "MTEL" in called, "riset comparative harus dipertahankan, bukan analyze tunggal"


def test_analyze_invalid_ticker():
    result = runner.invoke(app, ["analyze", "ABCDEFGHIJK"])
    assert result.exit_code != 0


def test_trend_invalid_ticker():
    result = runner.invoke(app, ["trend", ""])
    assert result.exit_code != 0


def test_score_invalid_ticker():
    result = runner.invoke(app, ["score", "ABCDEFGHIJK"])
    assert result.exit_code != 0


def test_compare_invalid_ticker():
    result = runner.invoke(app, ["compare", "BBCA", "ABCDEFGHIJK"])
    assert result.exit_code != 0


def _mock_fetch_partial_fail(ticker, *args, **kwargs):
    return MOCK_DATA.get(ticker.upper()) if ticker.upper() != "BBRI" else None


@patch("app.agent.research.chat_completion")
@patch("app.agent.core.chat_completion")
@patch.object(engine.provider, "fetch", side_effect=_mock_fetch)
def test_research_invalid_ticker_ambiguity_no_ai(mock_fetch, mock_llm_core, mock_llm_research):
    """Ticker tidak dikenal di universe -> ambigu, batal dengan pesan, tanpa fetch/LLM."""
    result = runner.invoke(app, ["research", "analisa XYZY"])
    assert result.exit_code == 0
    mock_llm_core.assert_not_called()
    mock_llm_research.assert_not_called()
    mock_fetch.assert_not_called()


@patch("app.agent.research.chat_completion", return_value="Ringkasan Eksekutif: ok\nRekomendasi:\n1. hold")
@patch("app.agent.core.chat_completion", return_value="BBCA stabil.")
@patch.object(engine.provider, "fetch", side_effect=_mock_fetch_partial_fail)
def test_research_compare_partial_failure_renders(mock_fetch, mock_llm_core, mock_llm_research):
    result = runner.invoke(app, ["research", "bandingkan BBCA dan BBRI"])
    assert result.exit_code == 0
    assert "BBRI" in result.output


def test_research_unsupported_query():
    result = runner.invoke(app, ["research", "gainers"])
    assert result.exit_code == 0
    assert "bukan permintaan riset" in result.output


def test_chat_saves_last_exchanges_to_memory():
    from app.memory import MemoryStore
    from app.memory.models import MemoryType
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    store = MemoryStore(path=path)
    questions = [f"pertanyaan {i}" for i in range(1, 6)]
    with patch("app.cli.main.get_store", return_value=store):
        with patch("app.cli.main.ask_llm", return_value="jawaban AI") as mock_llm:
            result = runner.invoke(app, ["chat"], input="\n".join(questions) + "\nexit\n")
    assert result.exit_code == 0
    assert mock_llm.call_count == 5, "penyimpanan memori tidak boleh memicu panggilan AI tambahan"
    entries = [e for e in store.get_all() if e.type == MemoryType.IMPORTANT_CONTEXT and e.source == "chat"]
    assert len(entries) == 1, "satu sesi chat harus menghasilkan tepat satu entri memori"
    content = entries[0].content
    assert "pertanyaan 3" in content and "pertanyaan 4" in content and "pertanyaan 5" in content, "3 pertanyaan-jawaban terakhir harus tersimpan"
    assert "jawaban AI" in content
    assert "pertanyaan 2" not in content, "batas ekor: Q&A ke-4 dari akhir harus terpotong"
    assert "pertanyaan 1" not in content, "hanya ekor percakapan yang boleh tersimpan, bukan seluruh riwayat"


def test_chat_no_reply_means_no_memory():
    from app.memory import MemoryStore
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    store = MemoryStore(path=path)
    with patch("app.cli.main.get_store", return_value=store):
        with patch("app.cli.main.ask_llm", return_value=None) as mock_llm:
            result = runner.invoke(app, ["chat"], input="halo\napa kabar\nexit\n")
    assert result.exit_code == 0
    assert mock_llm.call_count == 2, "AI gagal merespon, percakapan tidak terbentuk"
    assert store.count() == 0, "percakapan tanpa isi tidak boleh membuat entri memori"


def test_chat_empty_no_memory():
    from app.memory import MemoryStore
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    store = MemoryStore(path=path)
    with patch("app.cli.main.get_store", return_value=store):
        with patch("app.cli.main.ask_llm") as mock_llm:
            result = runner.invoke(app, ["chat"], input="exit\n")
    assert result.exit_code == 0
    mock_llm.assert_not_called()
    assert store.count() == 0


def _setup_wl_backend():
    fd, path = tempfile.mkstemp(suffix=".json", prefix="watchlist_cli_test_")
    os.close(fd)
    set_test_backend(LocalJsonStorage(path=path))
    reset_data()


def _teardown_wl_backend():
    set_test_backend(None)


def test_watchlist_show_by_name():
    _setup_wl_backend()
    w = wl_create("Saham Saya")
    wl_add(w.id, "BBCA")
    result = runner.invoke(app, ["watchlist", "show", "Saham Saya"])
    assert result.exit_code == 0
    assert "Saham Saya" in result.stdout
    assert "BBCA" in result.stdout
    _teardown_wl_backend()


def test_watchlist_show_nonexistent_name():
    _setup_wl_backend()
    wl_create("Saham Saya")
    result = runner.invoke(app, ["watchlist", "show", "TidakAda"])
    assert result.exit_code == 0
    assert "tidak ditemukan" in result.stdout.lower()
    _teardown_wl_backend()
