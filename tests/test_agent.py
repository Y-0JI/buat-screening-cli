from unittest.mock import patch
from app.agent.core import analyze_with_ai, compare_with_ai, ask_llm


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
            mock_llm.return_value = "**Ringkasan** Bagus\n**Risiko** - Risiko1\n**Kesimpulan** Beli"
            result = analyze_with_ai("BBCA")
            assert result.summary == "Bagus"
            assert len(result.risks) == 1
            assert result.conclusion == "Beli"


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


def _mock_stock_data():
    from datetime import date
    from app.models.stock import HistoricalPrice, StockData, StockInfo
    return StockData(
        info=StockInfo(ticker="BBCA", name="Test Bank", sector="Finance", market_cap=1e12),
        history=[
            HistoricalPrice(date=date(2024, 1, i + 1), open=100.0, high=101.0, low=99.0, close=100.0 + i, volume=1_000_000)
            for i in range(30)
        ],
    )
