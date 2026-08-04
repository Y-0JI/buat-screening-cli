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
    with patch("app.agent.research.get_provider") as mock_provider:
        mock_provider.return_value.fetch_financials.return_value = _RAW_FIN
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
        with patch("app.agent.research.get_provider") as mock_provider:
            mock_provider.return_value.fetch_financials.return_value = _RAW_FIN
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
    with patch("app.agent.research.get_provider") as mock_provider:
        mock_provider.return_value.fetch_financials.return_value = _RAW_FIN
        with patch("app.agent.research.get_store", return_value=store):
            with patch("app.agent.research.fetch_stock") as mock_fetch:
                mock_fetch.return_value = _mock_stock_data()
                with patch("app.agent.research.analyze_with_ai") as mock_analyze:
                    mock_analyze.return_value = AIAnalysis(ticker="BBCA", summary="Ringkasan tes")
                    with patch("app.agent.research.chat_completion") as mock_llm:
                        mock_llm.return_value = "Ringkasan Eksekutif: BBCA bagus\nRekomendasi:\n1. hold"
                        run_research("analisa BBCA")
    entries = [e for e in store.get_all() if e.type == MemoryType.RESEARCH_FINDING and e.source.startswith("research:")]
    assert entries, "riset sukses harus menyimpan entri memori"
    assert "Laporan riset (single_stock)" in entries[0].content


def test_compare_two_pairs_both_in_memory():
    import tempfile
    from app.memory import MemoryStore
    from app.memory.models import MemoryType
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    store = MemoryStore(path=path)
    with patch("app.agent.core.get_store", return_value=store):
        with patch("app.agent.core.fetch_stock") as mock_fetch:
            mock_fetch.return_value = _mock_stock_data()
            with patch("app.agent.core.chat_completion") as mock_llm:
                mock_llm.return_value = "hasil A"
                compare_with_ai(["BBCA", "BBRI"])
                mock_llm.return_value = "hasil B"
                compare_with_ai(["TLKM", "ASII"])
    entries = [e for e in store.get_all() if e.type == MemoryType.RESEARCH_FINDING and e.source.startswith("compare:")]
    assert len(entries) == 2, "dua perbandingan beda topik harus dua entri, bukan saling menimpa"


def test_research_two_topics_both_in_memory():
    import tempfile
    from app.memory import MemoryStore
    from app.memory.models import MemoryType
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    store = MemoryStore(path=path)
    for q in ("riset sektor financials", "riset sektor energy"):
        with patch("app.agent.research.get_store", return_value=store):
            with patch("app.agent.research.get_all", return_value=[{"ticker": "BBCA", "sector": "Financials"}]):
                with patch("app.agent.research.bulk_screen", return_value=([], [], [])):
                    with patch("app.agent.research.chat_completion") as mock_llm:
                        mock_llm.return_value = "Ringkasan Eksekutif: ok\nRekomendasi:\n1. hold"
                        run_research(q)
    entries = [e for e in store.get_all() if e.type == MemoryType.RESEARCH_FINDING and e.source.startswith("research:")]
    assert len(entries) == 2, "dua riset beda topik harus dua entri, bukan saling menimpa"


def test_build_research_data_fills_sections():
    from app.agent.research import build_research_data
    from app.models.research import SectionStatus
    from app.parser.intent import ResearchIntent
    a = AIAnalysis(
        ticker="BBCA", summary="ok",
        key_metrics={"RSI": "53.8"},
        raw_data=_mock_stock_data(),
        screening_results=None,
    )
    a.raw_data.info.fundamentals = {"trailingPE": 13.4, "returnOnEquity": 0.22, "dividendYield": 5.63, "priceToBook": 3.0}
    rd = build_research_data(ResearchIntent("single_stock", ["BBCA"], None, "q"), None, {"BBCA": a}, None, {"BBCA": ["Data lama"]})
    assert rd.schema_version == 1
    assert rd.sections["company"].status == SectionStatus.AVAILABLE
    assert rd.sections["company"].data["BBCA"]["sector"] == "Finance"
    assert rd.sections["price"].data["BBCA"]["price"] == a.raw_data.history[-1].close
    assert rd.sections["fundamental"].data["BBCA"]["trailingPE"] == 13.4
    assert rd.sections["valuation"].data["BBCA"]["priceToBook"] == 3.0
    assert rd.sections["dividend"].data["BBCA"]["dividendYield"] == 5.63
    assert rd.sections["risk"].data["BBCA"]["caveats"] == ["Data lama"]
    assert rd.sections["financial"].status == SectionStatus.MISSING
    assert rd.sections["market_intelligence"].status == SectionStatus.MISSING
    assert rd.symbol == "BBCA"


def test_build_research_data_immutable():
    from dataclasses import FrozenInstanceError
    from app.agent.research import build_research_data
    from app.parser.intent import ResearchIntent
    rd = build_research_data(ResearchIntent("single_stock", ["BBCA"], None, "q"), None, None, None, {})
    try:
        rd.symbol = "XX"
        assert False, "ResearchData harus read-only setelah normalisasi"
    except FrozenInstanceError:
        pass


def test_extract_fundamentals_filters_placeholders():
    from app.tools.yahoo_finance import _extract_fundamentals
    out = _extract_fundamentals({"trailingPE": 13.4, "beta": 0.0, "profitMargins": 0.0, "totalDebt": 0, "recommendationKey": "strong_buy", "missing": None})
    assert out == {"trailingPE": 13.4, "recommendationKey": "strong_buy"}


def test_research_ai_failure_falls_back_and_keeps_research_data():
    import tempfile
    from app.memory import MemoryStore
    from app.models.research import SectionStatus
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    store = MemoryStore(path=path)
    with patch("app.agent.research.get_provider") as mock_provider:
        mock_provider.return_value.fetch_financials.return_value = _RAW_FIN
        with patch("app.agent.research.get_store", return_value=store):
            with patch("app.agent.research.fetch_stock") as mock_fetch:
                mock_fetch.return_value = _mock_stock_data()
                with patch("app.agent.research.analyze_with_ai") as mock_analyze:
                    mock_analyze.return_value = AIAnalysis(ticker="BBCA", summary="Ringkasan tes", raw_data=_mock_stock_data())
                    with patch("app.agent.research.chat_completion") as mock_llm:
                        mock_llm.return_value = None
                        report = run_research("analisa BBCA")
    assert report.ai_failed is True
    assert report.research_data is not None, "ResearchData harus tetap tersimpan walau AI gagal"
    assert report.research_data.sections["company"].status == SectionStatus.AVAILABLE
    assert "otomatis" in report.executive_summary
    assert store.count() == 0, "AI gagal tidak boleh menyimpan laporan"


_RAW_FIN = {
    "financials": {
        "2025-12-31": {"Total Revenue": 1.1e14, "Net Income Common Stockholders": 5.8e13},
        "2024-12-31": {"Total Revenue": 1.0e14},
    },
    "balance_sheet": {
        "2025-12-31": {"Total Debt": 5.2e13, "Cash And Cash Equivalents": 7.8e13, "Stockholders Equity": 2.5e14}
    },
    "cashflow": {"2025-12-31": {"Free Cash Flow": 3.0e13}},
}


def _rd_with_data(fundamentals=None, raw_fin=None):
    from app.agent.enrichment import enrich_financials
    from app.agent.research import _financials_cache, build_research_data, enrich_research_data, enrich_market_intelligence
    from app.parser.intent import ResearchIntent
    _financials_cache.clear()
    a = AIAnalysis(ticker="BBCA", summary="ok", key_metrics={"RSI": "53.8"}, raw_data=_mock_stock_data(), screening_results=None)
    a.raw_data.info.fundamentals = fundamentals or {
        "fiftyTwoWeekHigh": 9000.0, "fiftyTwoWeekLow": 5000.0, "52WeekChange": -0.238,
        "recommendationKey": "strong_buy", "recommendationMean": 1.38, "targetMeanPrice": 8074.84,
    }
    rd = build_research_data(ResearchIntent("single_stock", ["BBCA"], None, "q"), None, {"BBCA": a}, None, {})
    with patch("app.agent.research.get_provider") as mock_provider:
        mock_provider.return_value.fetch_financials.return_value = raw_fin if raw_fin is not None else _RAW_FIN
        enrich_research_data(rd, {"BBCA": a})
    enrich_market_intelligence(rd, {"BBCA": a})
    _financials_cache.clear()
    return rd


def test_enrich_financials_deterministic_and_normalized():
    from app.agent.enrichment import enrich_financials
    m1 = enrich_financials(_RAW_FIN)
    m2 = enrich_financials(_RAW_FIN)
    assert m1 == m2, "enrichment harus deterministik"
    assert m1["revenue"] == {"latest": 110000000000000.0, "yoy_pct": 10.0}
    assert set(m1) == {"revenue", "net_income", "total_debt", "cash", "equity", "free_cash_flow"}


def test_enrich_price_position_and_volatility():
    from app.agent.research import build_report_prompt
    close = _mock_stock_data().history[-1].close
    rd = _rd_with_data()
    price = rd.sections["price"].data["BBCA"]
    assert price["week52_high"] == 9000.0 and price["week52_low"] == 5000.0
    assert abs(price["pct_from_high"] - ((close - 9000.0) / 9000.0 * 100)) < 0.01
    assert abs(price["pct_from_low"] - ((close - 5000.0) / 5000.0 * 100)) < 0.01
    assert isinstance(rd.sections["risk"].data["BBCA"]["volatility_annual_pct"], float)


def test_research_data_holds_metrics_not_raw_statements():
    rd = _rd_with_data()
    fin = rd.sections["financial"].data["BBCA"]
    assert "financials" not in fin and "balance_sheet" not in fin and "cashflow" not in fin
    assert fin["revenue"]["latest"] == 110000000000000.0
    assert rd.sections["financial"].source == "yfinance.financials"


def test_report_prompt_has_formatted_financial_no_raw():
    from app.agent.research import build_report_prompt
    rd = _rd_with_data()
    prompt = build_report_prompt(rd)
    assert "## Financial Analysis" in prompt, "section baru harus ikut schema tanpa ubah builder"
    assert "Pendapatan 110.0T (+10.0% YoY)" in prompt
    assert "Total Revenue" not in prompt and "Free Cash Flow" not in prompt, "raw statement tidak boleh masuk prompt"


def test_financial_fetch_cached_per_session():
    from app.agent.research import _financials_cache, _get_financials
    _financials_cache.clear()
    with patch("app.agent.research.get_provider") as mock_provider:
        mock_provider.return_value.fetch_financials.return_value = _RAW_FIN
        _get_financials("BBCA")
        _get_financials("BBCA")
        assert mock_provider.return_value.fetch_financials.call_count == 1, "fetch keuangan harus sekali per sesi"
    _financials_cache.clear()


def test_market_intelligence_container_single_stock():
    from app.models.research import REASON_NO_MARKET_CONTEXT, REASON_NEWS_UNAVAILABLE, SectionStatus
    rd = _rd_with_data()
    mi = rd.sections["market_intelligence"]
    slot = mi.data["BBCA"]
    assert mi.status == SectionStatus.PARTIAL
    assert mi.reason == REASON_NEWS_UNAVAILABLE
    assert "derived(price_history)" in mi.source and "yfinance.info" in mi.source
    assert slot["market_context"] == {"available": False, "reason": REASON_NO_MARKET_CONTEXT}, \
        "konteks pasar tidak boleh diinferensikan dari satu saham"
    assert slot["analyst_sentiment"]["recommendation_key"] == "strong_buy"
    assert slot["analyst_sentiment"]["target_mean"] == 8074.84
    assert slot["technical_context"]["week52_change_pct"] == -23.8
    assert slot["news_availability"] == {"status": "unavailable", "reason": REASON_NEWS_UNAVAILABLE}
    assert "bullish" not in str(slot["technical_context"]).lower(), "interpretasi bukan bagian kontrak"


def test_market_context_only_from_real_market_data():
    from app.agent.research import build_research_data, enrich_market_intelligence
    from app.parser.intent import ResearchIntent
    from app.screeners.engine import ScreeningResult
    a = AIAnalysis(ticker="BBCA", summary="ok", key_metrics={}, raw_data=_mock_stock_data(), screening_results=None)
    scr = [{"ticker": "BBCA", "sector": "Financials", "top_signal": ScreeningResult(ticker="BBCA", signal="BUY", confidence=0.85, reason="x"), "max_confidence": 0.85}]
    rd = build_research_data(ResearchIntent("sector_theme", [], "financials", "q"), scr, {"BBCA": a}, None, {})
    enrich_market_intelligence(rd, {"BBCA": a})
    assert rd.sections["market_intelligence"].data["BBCA"]["market_context"]["available"] is True


def test_market_intelligence_in_prompt_concise():
    from app.agent.research import build_report_prompt
    rd = _rd_with_data()
    prompt = build_report_prompt(rd)
    assert "## Market Intelligence" in prompt
    assert "analis strong_buy (1.38), target 8074.84" in prompt
    assert "berita: tidak tersedia (news_unavailable)" in prompt
    assert "analyst_sentiment" not in prompt, "key internal tidak boleh bocor ke prompt"


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


def test_report_prompt_rendered_cleanly():
    from app.agent.research import build_report_prompt, build_research_data
    from app.parser.intent import ResearchIntent
    from app.screeners.engine import ScreeningResult
    scr = [
        {"ticker": "BBCA", "sector": "Financials", "top_signal": ScreeningResult(ticker="BBCA", signal="BUY", confidence=0.85, reason="harga di atas EMA20"), "max_confidence": 0.85},
        {"ticker": "BBRI", "sector": "Financials", "top_signal": None, "max_confidence": 0},
    ]
    rd = build_research_data(ResearchIntent("sector_theme", [], None, "q"), scr, None, None, {})
    prompt = build_report_prompt(rd)
    assert "{{" not in prompt and "if ts else" not in prompt
    assert "## Market Overview" in prompt
    assert "2 kandidat" in prompt
    assert "financial" not in prompt.lower().replace("## ", ""), "section missing tidak boleh masuk input AI"
    assert "## Ringkasan Eksekutif" in prompt and "## Rekomendasi" in prompt


def test_report_prompt_deterministic_and_skip_missing():
    from app.agent.research import build_report_prompt, build_research_data
    from app.parser.intent import ResearchIntent
    rd = build_research_data(ResearchIntent("single_stock", ["BBCA"], None, "q"), None, None, None, {})
    p1 = build_report_prompt(rd)
    p2 = build_report_prompt(rd)
    assert p1 == p2, "input ResearchData sama -> prompt harus identik"
    assert "## Financial" not in p1 and "## Market Intelligence" not in p1, "section missing tidak boleh dikirim ke AI"


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
