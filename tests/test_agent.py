from unittest.mock import patch
from app.agent.core import process, ask_llm


def test_process_analyze():
    with patch("app.agent.core.fetch_stock") as mock_fetch:
        mock_fetch.return_value = "mock_data"
        result = process("analyze", {"ticker": "BBCA"})
        assert result["type"] == "analyze"
        assert result["ticker"] == "BBCA"
        assert result["data"] == "mock_data"


def test_process_compare():
    with patch("app.agent.core.fetch_stock") as mock_fetch:
        mock_fetch.return_value = "mock_data"
        result = process("compare", {"tickers": "BBCA,BBRI"})
        assert result["type"] == "compare"
        assert len(result["results"]) == 2


def test_process_screen():
    result = process("screen", {"type": "all"})
    assert result["type"] == "screen"


def test_process_help():
    result = process("help", {})
    assert result["type"] == "help"


def test_process_unknown():
    result = process("unknown", {"text": "lalala"})
    assert result["type"] == "unknown"


def test_ask_llm_no_api_key():
    result = ask_llm("test query")
    assert result is None


@patch("app.agent.core.chat_completion")
def test_ask_llm_with_context(mock_llm):
    mock_llm.return_value = "BBCA menunjukkan golden cross pattern."
    result = ask_llm("Apa sinyal BBCA?", context="BBCA: Golden Cross detected")
    assert result is not None
    assert "golden cross" in result.lower()
    mock_llm.assert_called_once()
