from app.parser.intent import parse, parse_full, detect_research_intent, INTENT_ANALYZE, INTENT_SCREEN, INTENT_COMPARE, INTENT_HELP, INTENT_UNKNOWN, INTENT_GAINERS, INTENT_LOSERS, INTENT_STOCKS


class TestParse:
    def test_analyze_direct(self):
        intent, params = parse("analisa BBCA")
        assert intent == INTENT_ANALYZE
        assert params["ticker"] == "BBCA"

    def test_analyze_natural(self):
        intent, params = parse("Apakah BBCA layak dibeli?")
        assert intent == INTENT_ANALYZE
        assert params["ticker"] == "BBCA"

    def test_analyze_qualifier_fundamental(self):
        intent, params = parse("analisa fundamental jkon")
        assert intent == INTENT_ANALYZE
        assert params["ticker"] == "JKON"

    def test_analyze_qualifier_teknikal(self):
        intent, params = parse("analisa teknikal bbca")
        assert intent == INTENT_ANALYZE
        assert params["ticker"] == "BBCA"

    def test_analyze_qualifier_lengkap(self):
        intent, params = parse("cek lengkap adro")
        assert intent == INTENT_ANALYZE
        assert params["ticker"] == "ADRO"

    def test_analyze_qualifier_leading(self):
        intent, params = parse("fundamental bbni")
        assert intent == INTENT_ANALYZE
        assert params["ticker"] == "BBNI"

    def test_analyze_single_word_regression(self):
        intent, params = parse("analisa jkon")
        assert intent == INTENT_ANALYZE
        assert params["ticker"] == "JKON"

    def test_analyze_no_midword_capture(self):
        intent, params = parse("analisa dulu jkon sekarang")
        assert intent == INTENT_UNKNOWN

    def test_analyze_valid_ticker_after_noise(self):
        intent, params = parse("analisa fundamental dari saham tlkm")
        assert intent == INTENT_ANALYZE
        assert params["ticker"] == "TLKM"

    def test_analyze_new_expressions(self):
        cases = [
            ("kenapa bca turun", "BCA"),
            ("bca bagus nggak", "BCA"),
            ("kelayakan bca", "BCA"),
            ("mau beli bca", "BCA"),
            ("nasib bca", "BCA"),
            ("berita bca", "BCA"),
        ]
        for q, ticker in cases:
            intent, params = parse(q)
            assert intent == INTENT_ANALYZE, q
            assert params["ticker"] == ticker, q

    def test_gainers_new_variant(self):
        intent, params = parse("saham apa yang naik terus")
        assert intent == INTENT_GAINERS

    def test_compare_lebih_baik(self):
        intent, params = parse("mana yang lebih baik bca atau bri")
        assert intent == INTENT_COMPARE
        assert params["tickers"] == "BCA,BRI"

    def test_saham_sector_fallback(self):
        intent, params = parse("saham energi")
        assert intent == INTENT_SCREEN
        assert params == {"type": "sector", "sector": "energi"}

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


class TestParseFull:
    _U = [
        {"ticker": "BBCA", "name": "Bank Central Asia Tbk."},
        {"ticker": "BBRI", "name": "Bank Rakyat Indonesia Tbk."},
        {"ticker": "TLKM", "name": "Telkom Indonesia (Persero) Tbk."},
        {"ticker": "MTEL", "name": "Mitra Telekomunikasi Indonesia Tbk."},
    ]

    def test_backward_compat_parse_tuple(self):
        result = parse_full("analisa BBCA", self._U)
        assert parse("analisa BBCA") == (result.intent, result.params)

    def test_confidence_levels(self):
        assert parse_full("analisa BBCA", self._U).confidence == "high"
        assert parse_full("analisa BBCA").confidence == "medium", "tanpa universe tidak bisa high"
        assert parse_full("BBCA", self._U).confidence == "low", "single-word fallback = low"
        assert parse_full("lalala", self._U).confidence == "low"
        assert parse_full("saham apa", self._U).confidence == "medium"

    def test_ambiguous_result(self):
        r = parse_full("analisa xyz", self._U)
        assert r.ambiguity.ambiguous is True
        assert r.confidence == "low"
        r2 = parse_full("analisa BBCA", self._U)
        assert r2.ambiguity.ambiguous is False

    def test_saham_sector_reinterpret_with_universe(self):
        r = parse_full("saham BBCA", self._U)
        assert r.intent == INTENT_ANALYZE, "ticker valid di universe tetap analyze"
        assert r.params == {"ticker": "BBCA"}
        r2 = parse_full("saham energi", self._U)
        assert r2.intent == INTENT_SCREEN
        assert r2.params == {"type": "sector", "sector": "energi"}


class TestDetectResearchIntent:
    def test_consistency_with_parse(self):
        cases = [
            ("analisa BBCA", "single_stock", ["BBCA"], None),
            ("analisa fundamental jkon", "single_stock", ["JKON"], None),
            ("fundamental bbni", "single_stock", ["BBNI"], None),
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
