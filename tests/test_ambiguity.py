from app.parser.ambiguity import (
    AmbiguityResult,
    detect_ambiguity,
    detect_company_candidates,
    detect_invalid_ticker,
    detect_multi_intent,
    params_tickers,
)

_U = [
    {"ticker": "BBCA", "name": "Bank Central Asia Tbk."},
    {"ticker": "BBRI", "name": "Bank Rakyat Indonesia Tbk."},
    {"ticker": "TLKM", "name": "Telkom Indonesia (Persero) Tbk."},
    {"ticker": "MTEL", "name": "Mitra Telekomunikasi Indonesia Tbk."},
    {"ticker": "LRNA", "name": "Eka Sari Lorena Transport Tbk."},
    {"ticker": "ROTI", "name": "Nippon Indosari Corpindo Tbk."},
]


def test_params_tickers():
    assert params_tickers({"ticker": "BBCA"}) == ["BBCA"]
    assert params_tickers({"tickers": "BBCA,BBRI"}) == ["BBCA", "BBRI"]
    assert params_tickers({}) == []


def test_detect_invalid_ticker():
    assert detect_invalid_ticker("analyze", {"ticker": "BBCA"}, _U) == []
    assert detect_invalid_ticker("analyze", {"ticker": "bca"}, _U) == [], "huruf kecil 'bca' -> BBCA (akhiran)"
    assert detect_invalid_ticker("analyze", {"ticker": "xyz"}, _U) == ["xyz"]
    assert detect_invalid_ticker("compare", {"tickers": "BBCA,ZZZ"}, _U) == ["ZZZ"]
    assert detect_invalid_ticker("analyze", {"ticker": "xyz"}, None) == [], "tanpa universe tidak menilai"


def test_detect_multi_intent_requires_clause_separator():
    assert detect_multi_intent("bandingkan bca dan bri tapi riset sektor bank", _U) is True
    assert detect_multi_intent("analisa bca lalu cari saham breakout", _U) is True
    assert detect_multi_intent("analisa bbca", _U) is False
    assert detect_multi_intent("bandingkan bca dan bri", _U) is False
    assert detect_multi_intent("lalala", _U) is False
    assert detect_multi_intent("analisa kondisi breakout BCA", _U) is False, "dua kata kunci satu kalimat = satu maksud"
    assert detect_multi_intent("cari saham breakout dan analisa bca", _U) is False, "'dan' bukan pemisah klausa"
    assert detect_multi_intent("bandingkan a dan b lalu bandingkan c dan d", _U) is False, "dua klausa satu kategori = bukan multi"
    assert detect_multi_intent("saham apa yang naik terus", _U) is False, "'terus' di tengah frasa bukan pemisah"


def test_detect_company_candidates_token_based():
    assert detect_company_candidates("telekomunikasi", _U) == ["MTEL"]
    assert detect_company_candidates("bank", _U) == ["BBCA", "BBRI"]
    assert detect_company_candidates("sari", _U) == ["LRNA"], "token utuh di Eka Sari Lorena"
    assert detect_company_candidates("xyz", _U) == []
    assert detect_company_candidates("", _U) == []
    assert detect_company_candidates("bank", None) == []
    assert detect_company_candidates("sa", _U) == [], "kata <3 huruf tidak dinilai"
    assert "ROTI" not in detect_company_candidates("sari", _U), "'sari' jangan nyangkut ke Indosari (substring)"


def test_detect_ambiguity_orchestrator():
    r = detect_ambiguity("bandingkan xyz dan abc", "compare", {"tickers": "XYZ,ABC"}, _U)
    assert r == AmbiguityResult(True, "invalid_ticker", [], ["xyz", "abc"])
    r = detect_ambiguity("bandingkan bca dan telekomunikasi", "compare", {"tickers": "BCA,TELE"}, _U)
    assert r == AmbiguityResult(True, "invalid_ticker", ["MTEL"], ["telekomunikasi"]), "potongan 'tele' harus di-expand ke kata utuh"
    r = detect_ambiguity("bandingkan bca dan bri tapi riset sektor bank", "compare", {"tickers": "BCA,BRI"}, _U)
    assert r.ambiguous is True and r.reason == "multi_intent"
    r = detect_ambiguity("telekomunikasi", "unknown", {"text": "telekomunikasi"}, _U)
    assert r == AmbiguityResult(True, "company_candidate", ["MTEL"], ["telekomunikasi"])
    r = detect_ambiguity("analisa BBCA", "analyze", {"ticker": "BBCA"}, _U)
    assert r.ambiguous is False
    r = detect_ambiguity("bandingkan xyz dan abc", "compare", {"tickers": "XYZ,ABC"}, None)
    assert r.ambiguous is False, "tanpa universe: cuma multi-intent yang bisa jadi ambigu"
