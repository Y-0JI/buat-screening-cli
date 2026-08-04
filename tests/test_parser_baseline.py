"""Regression baseline: snapshot parse() SEBELUM Phase 1 Intent Understanding.

Query di sini TIDAK boleh berubah hasilnya kecuali sengaja diubah — kalau berubah
tanpa alasan, itu regresi. Perubahan perilaku yang disengaja dicatat di PR.
"""

from app.parser.intent import parse


BASELINE = [
    ("analisa BBCA", ("analyze", {"ticker": "BBCA"})),
    ("Apakah BBCA layak dibeli?", ("analyze", {"ticker": "BBCA"})),
    ("analisa jkon", ("analyze", {"ticker": "JKON"})),
    ("analisa fundamental jkon", ("analyze", {"ticker": "JKON"})),
    ("analisa teknikal bbca", ("analyze", {"ticker": "BBCA"})),
    ("cek lengkap adro", ("analyze", {"ticker": "ADRO"})),
    ("fundamental bbni", ("analyze", {"ticker": "BBNI"})),
    ("trend BBCA", ("analyze", {"ticker": "BBCA"})),
    ("score BBCA", ("analyze", {"ticker": "BBCA"})),
    ("BBCA", ("analyze", {"ticker": "BBCA"})),
    ("saham BBCA", ("analyze", {"ticker": "BBCA"})),
    ("kondisi bbca", ("analyze", {"ticker": "BBCA"})),
    ("Bandingkan BBCA dan BBRI", ("compare", {"tickers": "BBCA,BBRI"})),
    ("BBCA vs BBRI", ("compare", {"tickers": "BBCA,BBRI"})),
    ("bandingkan BBCA vs BBRI", ("compare", {"tickers": "BBCA,BBRI"})),
    ("perbandingan bbca dan bbri", ("compare", {"tickers": "BBCA,BBRI"})),
    ("top gainers", ("gainers", {})),
    ("saham naik", ("gainers", {})),
    ("paling naik", ("gainers", {})),
    ("top losers", ("losers", {})),
    ("saham turun", ("losers", {})),
    ("Cari saham yang sedang breakout", ("screen", {"type": "all"})),
    ("sektor bank", ("screen", {"type": "sector", "sector": "bank"})),
    ("saham apa", ("screen", {"type": "all"})),
    ("cari saham", ("screen", {"type": "all"})),
    ("rekomendasi saham", ("screen", {"type": "all"})),
    ("riset sektor financials", ("research", {"text": "riset sektor financials"})),
    ("riset bbca", ("research", {"text": "riset bbca"})),
    ("research bbca", ("research", {"text": "research bbca"})),
    ("daftar saham", ("stocks", {})),
    ("list saham", ("stocks", {})),
    ("emiten", ("stocks", {})),
    ("help", ("help", {})),
    ("bantuan", ("help", {})),
    ("menu", ("help", {})),
    ("tolong", ("help", {})),
    ("lalala", ("unknown", {"text": "lalala"})),
    ("analisa dulu jkon sekarang", ("unknown", {"text": "analisa dulu jkon sekarang"})),
    ("makan siang", ("unknown", {"text": "makan siang"})),
]


def test_baseline_parse_results():
    for query, expected in BASELINE:
        assert parse(query) == expected, f"regresi parse: {query!r}"
