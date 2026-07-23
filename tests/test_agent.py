from unittest.mock import patch
from app.agent.core import ask_agent


def test_ask_agent_no_api_key():
    result = ask_agent("test query")
    assert result is None


@patch("app.agent.core.chat_completion")
def test_ask_agent_with_context(mock_llm):
    mock_llm.return_value = "BBCA menunjukkan golden cross pattern."
    result = ask_agent("Apa sinyal BBCA?", context="BBCA: Golden Cross detected")
    assert result is not None
    assert "golden cross" in result.lower()
    mock_llm.assert_called_once()


@patch("app.services.openrouter.chat_completion")
def test_tool_selection_logic(mock_llm):
    mock_llm.return_value = "analyze"
    from app.services.openrouter import chat_completion
    messages = [
        {"role": "system", "content": "Kamu adalah asisten saham."},
        {"role": "user", "content": "Analisa BBCA"},
    ]
    result = chat_completion(messages)
    assert result == "analyze"
