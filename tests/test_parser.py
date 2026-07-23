from app.parser.intent import parse, INTENT_ANALYZE, INTENT_SCREEN, INTENT_COMPARE, INTENT_HELP, INTENT_UNKNOWN, INTENT_GAINERS, INTENT_LOSERS, INTENT_STOCKS


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
