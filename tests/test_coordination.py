from app.cli.coordination import (
    ExecutionContext,
    RESEARCH_QUALIFIERS,
    resolve_followup,
    route_intent,
    split_clauses,
)
from app.parser.intent import parse_full

_U = [
    {"ticker": "BBCA", "name": "Bank Central Asia Tbk."},
    {"ticker": "BBRI", "name": "Bank Rakyat Indonesia Tbk."},
]

_CTX = "Laporan riset (single_stock) 'analisa BBCA':\nBBCA kuat."


def test_split_clauses_single_source():
    assert split_clauses("bandingkan bca dan bri tapi riset sektor bank") == ["bandingkan bca dan bri", "riset sektor bank"]
    assert split_clauses("analisa bca lalu cari saham breakout kemudian riset bbri") == ["analisa bca", "cari saham breakout", "riset bbri"]
    assert split_clauses("analisa bbca") == ["analisa bbca"]
    assert split_clauses("saham apa yang naik terus") == ["saham apa yang naik"], \
        "raw split: 'terus' dipecah; orchestration tetap aman (detect_multi_intent butuh >=2 klausa non-kosong)"


def test_route_intent_qualifier_to_research():
    assert route_intent(parse_full("analisa fundamental bbni", _U), "analisa fundamental bbni") == "research"
    assert route_intent(parse_full("analisa teknikal bbca", _U), "analisa teknikal bbca") == "research"
    assert route_intent(parse_full("laporan bbca", _U), "laporan bbca") == "research"
    assert route_intent(parse_full("riset bbca", _U), "riset bbca") == "research"
    assert route_intent(parse_full("analisa bbca", _U), "analisa bbca") == "analyze", "polos tetap analyze cepat"
    assert route_intent(parse_full("bandingkan bca dan bri", _U), "bandingkan bca dan bri") == "compare"
    assert "fundamental" in RESEARCH_QUALIFIERS and "lengkap" in RESEARCH_QUALIFIERS


def test_resolve_followup_compare():
    assert resolve_followup("bandingkan dengan bbri", parse_full("bandingkan dengan bbri", _U), _CTX) == "bandingkan BBCA dan BBRI"
    assert resolve_followup("vs bbri", parse_full("vs bbri", _U), _CTX) == "bandingkan BBCA dan BBRI"
    assert resolve_followup("bandingkan bbri", parse_full("bandingkan bbri", _U), _CTX) == "bandingkan BBCA dan BBRI"


def test_resolve_followup_pure_no_context():
    assert resolve_followup("bandingkan dengan bbri", parse_full("bandingkan dengan bbri", _U), None) is None
    assert resolve_followup("bandingkan dengan bbri", parse_full("bandingkan dengan bbri", _U), "") is None
    assert resolve_followup("analisa bbca", parse_full("analisa bbca", _U), _CTX) is None, "query jelas bukan follow-up"
    assert resolve_followup("bandingkan bca dan bri", parse_full("bandingkan bca dan bri", _U), _CTX) is None, "compare 2 ticker tak perlu konteks"


def test_execution_context_data_carrier():
    r = parse_full("analisa bbca", _U)
    ctx = ExecutionContext(query="analisa bbca", parse_result=r, last_context=_CTX, workflow="analyze")
    assert ctx.query == "analisa bbca"
    assert ctx.workflow == "analyze"
    assert ctx.parse_result.intent == "analyze"
