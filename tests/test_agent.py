from unittest.mock import patch
from app.agent.core import analyze_with_ai, compare_with_ai, ask_llm
from app.agent.research import run_research
from app.models.analysis import AIAnalysis


def test_analyze_with_ai_no_data():
    with patch("app.agent.core.fetch_stock") as mock:
        mock.return_value = None
        result = analyze_with_ai("INVALID")
        assert "tidak ditemukan" in result.summary.lower()


def test_analyze_with_ai_fallback_no_llm():
    with patch("app.agent.core.fetch_stock") as mock_fetch:
        mock_data = _mock_stock_data()
        mock_fetch.return_value = mock_data
        with patch("app.agent.core.chat_completion") as mock_llm:
            mock_llm.return_value = None
            result = analyze_with_ai("BBCA")
            assert "tidak tersedia" in result.summary.lower()
            assert result.raw_data is not None


def test_analyze_with_ai_with_llm():
    with patch("app.agent.core.fetch_stock") as mock_fetch:
        mock_data = _mock_stock_data()
        mock_fetch.return_value = mock_data
        with patch("app.agent.core.chat_completion") as mock_llm:
            mock_llm.return_value = "BBCA menunjukkan tren positif dengan RSI di 65. Risiko utama adalah tekanan jual asing. Kesimpulan: hold."
            result = analyze_with_ai("BBCA")
            assert "tren positif" in result.summary
            assert "hold" in result.summary.lower()


def test_compare_with_ai():
    with patch("app.agent.core.fetch_stock") as mock_fetch:
        mock_data = _mock_stock_data()
        mock_fetch.return_value = mock_data
        with patch("app.agent.core.chat_completion") as mock_llm:
            mock_llm.return_value = "BBCA lebih baik dari BBRI"
            result = compare_with_ai(["BBCA", "BBRI"])
            assert result["type"] == "comparison"
            assert "BBCA" in result["analysis"]


@patch("app.agent.core.chat_completion")
def test_ask_llm_no_api_key(mock_llm):
    mock_llm.return_value = None
    result = ask_llm("test query")
    assert result is None


@patch("app.agent.core.chat_completion")
def test_ask_llm_with_context(mock_llm):
    mock_llm.return_value = "BBCA golden cross."
    result = ask_llm("Apa sinyal?", context="BBCA: Golden Cross")
    assert result is not None
    mock_llm.assert_called_once()


def _assert_no_memory_placeholder(messages):
    assert not any("{{MEMORY}}" in m.get("content", "") for m in messages)


def test_analyze_memory_injected():
    with patch("app.agent.core.fetch_stock") as mock_fetch:
        mock_fetch.return_value = _mock_stock_data()
        with patch("app.agent.core.chat_completion") as mock_llm:
            mock_llm.return_value = "BBCA ok."
            analyze_with_ai("BBCA")
            _assert_no_memory_placeholder(mock_llm.call_args.args[0])


def test_compare_memory_injected():
    with patch("app.agent.core.fetch_stock") as mock_fetch:
        mock_fetch.return_value = _mock_stock_data()
        with patch("app.agent.core.chat_completion") as mock_llm:
            mock_llm.return_value = "BBCA vs BBRI."
            compare_with_ai(["BBCA", "BBRI"])
            _assert_no_memory_placeholder(mock_llm.call_args.args[0])


@patch("app.agent.core.chat_completion")
def test_ask_llm_memory_injected(mock_llm):
    mock_llm.return_value = "jawaban"
    ask_llm("test")
    _assert_no_memory_placeholder(mock_llm.call_args.args[0])


def test_research_memory_injected():
    with patch("app.agent.research.fetch_stock") as mock_fetch:
        mock_fetch.return_value = _mock_stock_data()
        with patch("app.agent.research.analyze_with_ai") as mock_analyze:
            mock_analyze.return_value = AIAnalysis(ticker="BBCA", summary="Ringkasan tes")
            with patch("app.agent.research.chat_completion") as mock_llm:
                mock_llm.return_value = "Ringkasan Eksekutif: tes\nRekomendasi:\n1. hold"
                run_research("analisa BBCA")
                _assert_no_memory_placeholder(mock_llm.call_args.args[0])


def test_analyze_caveats_rendered_cleanly():
    with patch("app.agent.core.fetch_stock") as mock_fetch:
        mock_fetch.return_value = _mock_stock_data()
        with patch("app.agent.core.chat_completion") as mock_llm:
            mock_llm.return_value = "BBCA ok."
            analyze_with_ai("BBCA")
            user_msg = mock_llm.call_args.args[0][1]["content"]
            assert "Keterbatasan Data:" in user_msg
            assert "- " in user_msg
            assert "{%" not in user_msg


def test_analyze_caveats_default_when_none():
    with patch("app.agent.core.fetch_stock") as mock_fetch:
        mock_fetch.return_value = _mock_stock_data(days=250)
        with patch("app.agent.core.chat_completion") as mock_llm:
            mock_llm.return_value = "BBCA ok."
            analyze_with_ai("BBCA")
            user_msg = mock_llm.call_args.args[0][1]["content"]
            assert "Tidak ada keterbatasan" in user_msg


def _mock_stock_data(days: int = 30):
    from datetime import date, timedelta
    from app.models.stock import HistoricalPrice, StockData, StockInfo
    base = date.today() - timedelta(days=days)
    return StockData(
        info=StockInfo(ticker="BBCA", name="Test Bank", sector="Finance", market_cap=1e12),
        history=[
            HistoricalPrice(date=base + timedelta(days=i), open=100.0, high=101.0, low=99.0, close=100.0 + i, volume=1_000_000)
            for i in range(days)
        ],
    )
