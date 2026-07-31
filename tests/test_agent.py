import os
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


def test_compare_caveats_in_prompt():
    with patch("app.agent.core.fetch_stock") as mock_fetch:
        mock_fetch.return_value = _mock_stock_data(days=30)
        with patch("app.agent.core.chat_completion") as mock_llm:
            mock_llm.return_value = "BBCA vs BBRI."
            compare_with_ai(["BBCA", "BBRI"])
            user_msg = mock_llm.call_args.args[0][1]["content"]
            assert "Keterbatasan Data:" in user_msg


def test_research_no_ai_when_all_data_failed():
    with patch("app.agent.research.fetch_stock") as mock_fetch:
        mock_fetch.return_value = None
        with patch("app.agent.research.chat_completion") as mock_llm:
            report = run_research("analisa XYZY")
            assert report.failed == ["XYZY"]
            assert report.analyses is None
            mock_llm.assert_not_called()


def test_research_unsupported_query_no_ai():
    with patch("app.agent.research.chat_completion") as mock_llm:
        report = run_research("gainers")
        assert report.intent.type == "unsupported"
        mock_llm.assert_not_called()


def test_research_compare_partial_sends_all_tickers():
    with patch("app.agent.research.fetch_stock") as mock_fetch:
        mock_fetch.side_effect = lambda t: _mock_stock_data() if t == "BBCA" else None
        with patch("app.agent.core.fetch_stock") as mock_core_fetch:
            mock_core_fetch.side_effect = lambda t: _mock_stock_data() if t == "BBCA" else None
            with patch("app.agent.core.chat_completion") as mock_llm_core:
                mock_llm_core.return_value = "BBCA stabil."
                with patch("app.agent.research.chat_completion") as mock_llm:
                    mock_llm.return_value = "Ringkasan Eksekutif: ok\nRekomendasi:\n1. hold"
                    with patch("app.agent.research.compare_with_ai") as mock_compare:
                        mock_compare.return_value = {"type": "comparison", "analysis": "x"}
                        report = run_research("bandingkan BBCA dan BBRI")
                        assert report.failed == ["BBRI"]
                        mock_compare.assert_called_once_with(["BBCA", "BBRI"])


def test_research_saves_summary_to_memory():
    import tempfile
    from app.memory import MemoryStore
    from app.memory.models import MemoryType
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    store = MemoryStore(path=path)
    with patch("app.agent.research.get_store", return_value=store):
        with patch("app.agent.research.fetch_stock") as mock_fetch:
            mock_fetch.return_value = _mock_stock_data()
            with patch("app.agent.research.analyze_with_ai") as mock_analyze:
                mock_analyze.return_value = AIAnalysis(ticker="BBCA", summary="Ringkasan tes")
                with patch("app.agent.research.chat_completion") as mock_llm:
                    mock_llm.return_value = "Ringkasan Eksekutif: BBCA bagus\nRekomendasi:\n1. hold"
                    run_research("analisa BBCA")
    entries = [e for e in store.get_all() if e.type == MemoryType.RESEARCH_FINDING and e.source == "research"]
    assert entries, "riset sukses harus menyimpan entri memori"
    assert "Riset single_stock" in entries[0].content


def test_research_failed_no_memory_entry():
    import tempfile
    from app.memory import MemoryStore
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    store = MemoryStore(path=path)
    with patch("app.agent.research.get_store", return_value=store):
        with patch("app.agent.research.fetch_stock") as mock_fetch:
            mock_fetch.return_value = None
            with patch("app.agent.research.chat_completion") as mock_llm:
                run_research("analisa XYZY")
                mock_llm.assert_not_called()
    assert store.count() == 0


def test_screening_prompt_rendered_cleanly():
    from app.agent.research import _render_report_prompt
    from app.parser.intent import ResearchIntent
    from app.screeners.engine import ScreeningResult
    scr = [
        {"ticker": "BBCA", "sector": "Financials", "top_signal": ScreeningResult(ticker="BBCA", signal="BUY", confidence=0.85, reason="harga di atas EMA20"), "max_confidence": 0.85},
        {"ticker": "BBRI", "sector": "Financials", "top_signal": None, "max_confidence": 0},
    ]
    prompt = _render_report_prompt("{{context}}", ResearchIntent("sector_theme", [], None, "q"), scr, None, None, {})
    assert "if ts else" not in prompt
    assert "- BBCA (Financials): BUY (85%) - harga di atas EMA20" in prompt
    assert "- BBRI (Financials): N/A" in prompt


def test_extract_sections_variants():
    from app.agent.research import _extract_sections
    variants = [
        ("# Ringkasan Eksekutif\nBBCA kuat.\n# Rekomendasi\n1. hold\n2. beli", "BBCA kuat.", ["hold", "beli"]),
        ("## Kesimpulan\nBBCA layak.\n## Rekomendasi:\n- hold", "BBCA layak.", ["hold"]),
        ("Ringkasan Eksekutif: BBCA bagus\nRekomendasi:\n1. hold", "BBCA bagus", ["hold"]),
        ("**Ringkasan Eksekutif:** BBCA solid\n**Rekomendasi:** hold dan watchlist", "BBCA solid", ["hold dan watchlist"]),
    ]
    for text, expected_summary, expected_recs in variants:
        s = _extract_sections(text)
        assert s["summary"] == expected_summary, text
        assert s["recommendations"] == expected_recs, text


def test_extract_sections_no_false_positive():
    from app.agent.research import _extract_sections
    s = _extract_sections("kalimat biasa dengan kata ringkasan di tengah.\n## Rekomendasi\n1. hold")
    assert s["summary"] == "", "kata kunci di tengah kalimat tidak boleh memicu section"
    assert s["recommendations"] == ["hold"]


def test_trim_analysis_keeps_head_and_tail():
    from app.agent.research import _trim_analysis
    long = "A" * 400 + "B" * 1000 + "C" * 400
    trimmed = _trim_analysis(long)
    assert len(trimmed) <= 840, "blok analisis harus dibatasi secara konsisten"
    assert trimmed.startswith("A" * 400) and trimmed.endswith("C" * 400), "kepala dan ekor harus utuh"
    assert "dipotong" in trimmed, "harus ada penanda pemotongan"
    assert _trim_analysis("pendek") == "pendek"


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
