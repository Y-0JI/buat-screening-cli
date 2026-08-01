from dataclasses import dataclass, field
from typing import Literal
from app.agent.core import analyze_with_ai, compare_with_ai, _load_prompt, _build_system_prompt
from app.router.engine import fetch_stock, bulk_screen, build_context
from app.services.llm import chat_completion
from app.services.stock_list import get_all
from app.parser.intent import detect_research_intent, ResearchIntent
from app.memory import get_store
from app.memory.models import MemoryType
from app.models.analysis import AIAnalysis
from app.models.research import REPORT_SECTIONS, ResearchData, ResearchSection, SectionStatus


@dataclass
class ResearchReport:
    intent: ResearchIntent
    screening_results: list[dict] | None
    analyses: dict[str, AIAnalysis] | None
    comparison: dict | None
    data_quality: dict[str, list[str]]
    recommendations: list[str]
    executive_summary: str
    failed: list[str] = field(default_factory=list)
    research_data: ResearchData | None = None


def _mark_available(sections: dict[str, ResearchSection], key: str, source: str = "yahoo") -> dict:
    if sections[key].status == SectionStatus.MISSING:
        sections[key] = ResearchSection(source=source, status=SectionStatus.AVAILABLE)
    return sections[key].data


def build_research_data(intent: ResearchIntent, screening_results, analyses, data_quality) -> ResearchData:
    """Normalize research outputs into the provider-independent ResearchData contract."""
    sections = {key: ResearchSection() for key in REPORT_SECTIONS}
    dq = data_quality or {}

    if screening_results:
        sections["market"] = ResearchSection(
            source="screening", status=SectionStatus.AVAILABLE, data={"results": screening_results[:15]}
        )

    for ticker, a in (analyses or {}).items():
        info = a.raw_data.info if a.raw_data else None
        if info:
            company = _mark_available(sections, "company")
            company[ticker] = {
                "name": info.name,
                "sector": info.sector,
                "industry": info.industry,
                "exchange": info.exchange,
                "market_cap": info.market_cap,
                "currency": info.currency,
            }
            fund = info.fundamentals
            if fund:
                fundamental = _mark_available(sections, "fundamental")
                fundamental[ticker] = {
                    k: fund[k] for k in ("trailingPE", "forwardPE", "returnOnEquity", "profitMargins", "operatingMargins", "bookValue", "beta") if k in fund
                }
                valuation = _mark_available(sections, "valuation")
                valuation[ticker] = {
                    k: fund[k] for k in ("priceToBook", "pegRatio", "enterpriseToRevenue", "targetMeanPrice", "targetHighPrice", "targetLowPrice") if k in fund
                }
                growth = _mark_available(sections, "growth")
                growth[ticker] = {
                    k: fund[k] for k in ("revenueGrowth", "earningsGrowth", "earningsQuarterlyGrowth") if k in fund
                }
                dividend = _mark_available(sections, "dividend")
                dividend[ticker] = {
                    k: fund[k] for k in ("dividendYield", "dividendRate", "payoutRatio", "trailingAnnualDividendYield") if k in fund
                }
        if a.raw_data and a.raw_data.history:
            hist = a.raw_data.history
            prev = hist[-2].close if len(hist) > 1 else hist[-1].close
            change = ((hist[-1].close - prev) / prev * 100) if prev else 0.0
            price = _mark_available(sections, "price")
            price[ticker] = {"price": hist[-1].close, "change_pct": round(change, 2), "volume": hist[-1].volume}
            technical = _mark_available(sections, "technical")
            technical[ticker] = {"key_metrics": a.key_metrics}
            if a.screening_results:
                technical[ticker]["signals"] = [s.signal for s in a.screening_results]
            if dq.get(ticker):
                risk = _mark_available(sections, "risk")
                risk[ticker] = {"caveats": dq[ticker]}

    return ResearchData(symbol=",".join(intent.tickers) if intent.tickers else "", sections=sections)


def run_research(query: str) -> ResearchReport:
    intent = detect_research_intent(query)

    screening_results = None
    analyses = None
    comparison = None
    data_quality = {}
    failed = []
    research_data = None

    if intent.type == "unsupported":
        return ResearchReport(intent, None, None, None, {}, [], "Query ini bukan permintaan riset.", [])

    if intent.type == "sector_theme":
        all_tickers = [s["ticker"] for s in get_all()]
        results, _invalid, _failed = bulk_screen(all_tickers)
        if intent.sector:
            results = [r for r in results if r.get("sector") and intent.sector.lower() in r["sector"].lower()]
        top = [r for r in results if r.get("max_confidence", 0) >= 0.7][:5]
        screening_results = results
        if top:
            analyses = {}
            for r in top:
                t = r["ticker"]
                data = fetch_stock(t)
                if data:
                    ctx = build_context(data)
                    data_quality[t] = ctx.get("data_caveats", [])
                    analyses[t] = analyze_with_ai(t)
            if len(analyses) > 1:
                comparison = compare_with_ai(list(analyses.keys()))

    elif intent.type == "single_stock":
        t = intent.tickers[0]
        data = fetch_stock(t)
        if data:
            ctx = build_context(data)
            data_quality[t] = ctx.get("data_caveats", [])
            analyses = {t: analyze_with_ai(t)}
        else:
            failed = [t]

    elif intent.type == "comparative":
        tickers = intent.tickers[:2]
        analyses = {}
        for t in tickers:
            data = fetch_stock(t)
            if data:
                ctx = build_context(data)
                data_quality[t] = ctx.get("data_caveats", [])
                analyses[t] = analyze_with_ai(t)
        if len(analyses) < len(tickers):
            failed = [t for t in tickers if t not in analyses]
        if analyses:
            comparison = compare_with_ai(tickers)

    elif intent.type == "analyze_only":
        t = intent.tickers[0] if intent.tickers else ""
        if t:
            data = fetch_stock(t)
            if data:
                ctx = build_context(data)
                data_quality[t] = ctx.get("data_caveats", [])
                analyses = {t: analyze_with_ai(t)}

    if failed and not analyses and not screening_results:
        return ResearchReport(intent, None, None, None, data_quality, [], "Laporan riset otomatis berdasarkan data terkini.", failed)

    research_data = build_research_data(intent, screening_results, analyses, data_quality)

    prompt = _load_prompt("research.md")
    filled = _render_report_prompt(prompt, intent, screening_results, analyses, comparison, data_quality)
    system_prompt = _build_system_prompt()
    llm_result = chat_completion([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": filled},
    ], temperature=0)

    executive_summary = ""
    recommendations = []
    if llm_result:
        sections = _extract_sections(llm_result)
        executive_summary = sections["summary"]
        recommendations = sections["recommendations"]

    if not executive_summary:
        executive_summary = "Laporan riset otomatis berdasarkan data terkini."
    if not recommendations:
        recommendations = ["Lakukan analisis manual lebih lanjut sebelum keputusan investasi."]

    if llm_result:
        recs = "; ".join(recommendations[:3])
        topic = intent.sector or query.strip()[:50]
        get_store().add_or_update(
            MemoryType.RESEARCH_FINDING,
            f"Riset {intent.type} '{query[:50]}': {executive_summary.strip()[:150]} Rekomendasi: {recs[:150]}",
            source=f"research:{intent.type}:{topic}",
        )

    return ResearchReport(
        intent=intent,
        screening_results=screening_results,
        analyses=analyses,
        comparison=comparison,
        data_quality=data_quality,
        recommendations=recommendations,
        executive_summary=executive_summary.strip(),
        failed=failed,
        research_data=research_data,
    )


_SUMMARY_LABELS = ("ringkasan eksekutif", "ringkasan", "eksekutif", "kesimpulan", "rangkuman", "conclusion", "summary")
_RECS_LABELS = ("rekomendasi", "recommendation", "recommendations")


def _normalize_line(line: str) -> str:
    return line.strip().lstrip("#").strip().strip("*").strip().lower()


def _match_section(line: str) -> tuple[str, str] | None:
    norm = _normalize_line(line)
    for section, labels in (("summary", _SUMMARY_LABELS), ("recs", _RECS_LABELS)):
        for label in labels:
            if norm == label:
                return section, ""
            if norm.startswith(label + ":"):
                return section, line.split(":", 1)[1].strip().lstrip("*#").strip()
    return None


def _extract_sections(text: str) -> dict[str, str | list[str]]:
    summary_parts = []
    recommendations = []
    current = None
    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            continue
        section = _match_section(line)
        if section:
            current, inline = section
            if inline:
                if current == "summary":
                    summary_parts.append(inline)
                else:
                    recommendations.append(inline.lstrip("-•*123456789. "))
            continue
        if current == "summary":
            summary_parts.append(line)
        elif current == "recs" and line.startswith(("-", "•", "1.", "2.", "3.", "4.", "5.")):
            recommendations.append(line.lstrip("-•*123456789. "))
    return {"summary": " ".join(summary_parts).strip(), "recommendations": recommendations}


def _trim_analysis(text: str, limit: int = 800) -> str:
    if len(text) <= limit:
        return text
    half = limit // 2
    return f"{text[:half]}\n[... bagian tengah dipotong ...]\n{text[-half:]}"


def _render_report_prompt(template: str, intent: ResearchIntent, screening, analyses, comparison, data_quality) -> str:
    parts = []
    parts.append(f"QUERY: {intent.raw_query}")
    parts.append(f"INTENT: {intent.type}")

    if screening:
        parts.append("SCREENING RESULTS:")
        for r in screening[:10]:
            ts = r.get("top_signal")
            if ts:
                parts.append(f"- {r['ticker']} ({r.get('sector', '-')}): {ts.signal} ({ts.confidence:.0%}) - {ts.reason}")
            else:
                parts.append(f"- {r['ticker']} ({r.get('sector', '-')}): N/A")

    if analyses:
        parts.append("ANALYSES:")
        for ticker, a in analyses.items():
            parts.append(f"--- {ticker} ---")
            parts.append(_trim_analysis(a.summary))
            if ticker in data_quality:
                parts.append(f"DATA QUALITY: {', '.join(data_quality[ticker])}")

    if comparison:
        parts.append("COMPARISON:")
        parts.append(comparison.get("analysis", ""))

    return template.replace("{{context}}", "\n".join(parts))
