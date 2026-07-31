from app.parser.intent import parse, detect_research_intent, INTENT_ANALYZE, INTENT_SCREEN, INTENT_COMPARE, INTENT_HELP, INTENT_UNKNOWN, INTENT_GAINERS, INTENT_LOSERS, INTENT_STOCKS


class TestParse:
    def test_analyze_direct(self):
        intent, params = parse("analisa BBCA")
        assert intent == INTENT_ANALYZE
        assert params["ticker"] == "BBCA"

    def test_analyze_natural(self):
        intent, params = parse("Apakah BBCA layak dibeli?")
        assert intent == INTENT_ANALYZE
        assert params["ticker"] == "BBCA"

    def test_compare(self):
        intent, params = parse("Bandingkan BBCA dan BBRI")
        assert intent == INTENT_COMPARE
        assert "BBCA" in params["tickers"]

    def test_compare_vs_between_tickers(self):
        intent, params = parse("BBCA vs BBRI")
        assert intent == INTENT_COMPARE
        assert params["tickers"] == "BBCA,BBRI"

    def test_compare_verb_with_vs(self):
        intent, params = parse("bandingkan BBCA vs BBRI")
        assert intent == INTENT_COMPARE
        assert params["tickers"] == "BBCA,BBRI"

    def test_screen_breakout(self):
        intent, params = parse("Cari saham yang sedang breakout")
        assert intent == INTENT_SCREEN

    def test_gainers(self):
        intent, params = parse("top gainers")
        assert intent == INTENT_GAINERS

    def test_losers(self):
        intent, params = parse("top losers")
        assert intent == INTENT_LOSERS

    def test_stocks(self):
        intent, params = parse("daftar saham")
        assert intent == INTENT_STOCKS

    def test_help(self):
        intent, params = parse("help")
        assert intent == INTENT_HELP

    def test_unknown(self):
        intent, params = parse("lalala")
        assert intent == INTENT_UNKNOWN


class TestDetectResearchIntent:
    def test_consistency_with_parse(self):
        cases = [
            ("analisa BBCA", "single_stock", ["BBCA"], None),
            ("bandingkan BBCA dan BBRI", "comparative", ["BBCA", "BBRI"], None),
            ("BBCA vs BBRI", "comparative", ["BBCA", "BBRI"], None),
            ("cari saham breakout", "sector_theme", [], None),
            ("sektor bank", "sector_theme", [], "bank"),
            ("riset sektor financials", "sector_theme", [], "financials"),
            ("gainers", "unsupported", [], None),
            ("losers", "unsupported", [], None),
            ("stocks", "unsupported", [], None),
            ("help", "unsupported", [], None),
            ("lalala", "unsupported", [], None),
        ]
        for q, itype, tickers, sector in cases:
            r = detect_research_intent(q)
            assert r.type == itype, q
            assert r.tickers == tickers, q
            assert r.sector == sector, q
