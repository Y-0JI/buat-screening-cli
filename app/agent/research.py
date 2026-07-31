from dataclasses import dataclass
from typing import Literal
from app.agent.core import analyze_with_ai, compare_with_ai, _load_prompt, _build_system_prompt
from app.router.engine import fetch_stock, bulk_screen, build_context
from app.services.llm import chat_completion
from app.services.stock_list import get_all
from app.parser.intent import detect_research_intent, ResearchIntent
from app.models.analysis import AIAnalysis


@dataclass
class ResearchReport:
    intent: ResearchIntent
    screening_results: list[dict] | None
    analyses: dict[str, AIAnalysis] | None
    comparison: dict | None
    data_quality: dict[str, list[str]]
    recommendations: list[str]
    executive_summary: str


def run_research(query: str) -> ResearchReport:
    intent = detect_research_intent(query)

    screening_results = None
    analyses = None
    comparison = None
    data_quality = {}

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
            from app.models.analysis import AIAnalysis
            analyses = {t: AIAnalysis(ticker=t, summary="Data tidak ditemukan", conclusion="Gagal mengambil data")}
            data_quality[t] = ["Data tidak ditemukan"]

    elif intent.type == "comparative":
        tickers = intent.tickers[:2]
        analyses = {}
        for t in tickers:
            data = fetch_stock(t)
            if data:
                ctx = build_context(data)
                data_quality[t] = ctx.get("data_caveats", [])
                analyses[t] = analyze_with_ai(t)
        comparison = compare_with_ai(tickers)

    elif intent.type == "analyze_only":
        t = intent.tickers[0] if intent.tickers else ""
        if t:
            data = fetch_stock(t)
            if data:
                ctx = build_context(data)
                data_quality[t] = ctx.get("data_caveats", [])
                analyses = {t: analyze_with_ai(t)}

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
        lines = llm_result.split("\n")
        in_summary = False
        in_recs = False
        for line in lines:
            ll = line.lower()
            if "ringkasan" in ll or "eksekutif" in ll or "summary" in ll:
                in_summary = True
                in_recs = False
                continue
            if "rekomendasi" in ll or "recommendation" in ll:
                in_recs = True
                in_summary = False
                continue
            if in_summary and line.strip():
                executive_summary += line.strip() + " "
            if in_recs and line.strip().startswith(("-", "•", "*", "1.", "2.", "3.", "4.", "5.")):
                recommendations.append(line.strip().lstrip("-•*123456789. "))

    if not executive_summary:
        executive_summary = "Laporan riset otomatis berdasarkan data terkini."
    if not recommendations:
        recommendations = ["Lakukan analisis manual lebih lanjut sebelum keputusan investasi."]

    return ResearchReport(
        intent=intent,
        screening_results=screening_results,
        analyses=analyses,
        comparison=comparison,
        data_quality=data_quality,
        recommendations=recommendations,
        executive_summary=executive_summary.strip(),
    )


def _render_report_prompt(template: str, intent: ResearchIntent, screening, analyses, comparison, data_quality) -> str:
    parts = []
    parts.append(f"QUERY: {intent.raw_query}")
    parts.append(f"INTENT: {intent.type}")

    if screening:
        parts.append("SCREENING RESULTS:")
        for r in screening[:10]:
            ts = r.get("top_signal")
            parts.append(f"- {r['ticker']} ({r.get('sector', '-')}): {ts.signal if ts else 'N/A'} ({ts.confidence:.0%} if ts else 0) - {ts.reason if ts else 'N/A'}")

    if analyses:
        parts.append("ANALYSES:")
        for ticker, a in analyses.items():
            parts.append(f"--- {ticker} ---")
            parts.append(a.summary)
            if ticker in data_quality:
                parts.append(f"DATA QUALITY: {', '.join(data_quality[ticker])}")

    if comparison:
        parts.append("COMPARISON:")
        parts.append(comparison.get("analysis", ""))

    return template.replace("{{context}}", "\n".join(parts))
