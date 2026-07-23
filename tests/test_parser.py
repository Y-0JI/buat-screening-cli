from app.agent.parser import parse_intent, INTENT_ANALYZE, INTENT_SCREEN, INTENT_COMPARE, INTENT_HELP, INTENT_UNKNOWN


class TestParseIntent:
    def test_analyze_direct(self):
        intent, params = parse_intent("analisa BBCA")
        assert intent == INTENT_ANALYZE
        assert params["ticker"] == "BBCA"

    def test_analyze_natural(self):
        intent, params = parse_intent("Apakah BBCA layak dibeli?")
        assert intent == INTENT_ANALYZE
        assert params["ticker"] == "BBCA"

    def test_compare(self):
        intent, params = parse_intent("Bandingkan BBCA dan BBRI")
        assert intent == INTENT_COMPARE
        assert "BBCA" in params["tickers"]

    def test_screen_breakout(self):
        intent, params = parse_intent("Cari saham yang sedang breakout")
        assert intent == INTENT_SCREEN

    def test_help(self):
        intent, params = parse_intent("help")
        assert intent == INTENT_HELP

    def test_unknown(self):
        intent, params = parse_intent("lalala")
        assert intent == INTENT_UNKNOWN

    def test_top_gainers(self):
        intent, params = parse_intent("top gainers hari ini")
        assert intent == INTENT_SCREEN
        assert params["type"] == "top_gainers"
