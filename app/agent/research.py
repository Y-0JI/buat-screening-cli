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
from app.models.research import (
    REASON_NEWS_UNAVAILABLE,
    REASON_NO_MARKET_CONTEXT,
    REPORT_SECTION_LABELS,
    REPORT_SECTIONS,
    ResearchData,
    ResearchSection,
    SectionStatus,
)
from app.agent.enrichment import (
    compute_confidence,
    compute_price_position,
    compute_technical_context,
    compute_volatility,
    enrich_financials,
)
from app.tools import get_provider

_financials_cache: dict[str, dict] = {}


def _get_financials(ticker: str) -> dict:
    """Lazy financial statements, cached for the whole process (session)."""
    if ticker not in _financials_cache:
        _financials_cache[ticker] = get_provider().fetch_financials(ticker)
    return _financials_cache[ticker]


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
    ai_failed: bool = False


def build_score_context(rd: ResearchData, analyses: dict[str, AIAnalysis] | None) -> dict:
    """Structured numbers only — no sentences, no duplicate of AI output."""
    ctx = {}
    for ticker, a in (analyses or {}).items():
        slot: dict = {}
        tech = rd.sections["technical"].data.get(ticker, {})
        if tech.get("key_metrics"):
            slot["indicators"] = tech["key_metrics"]
        mi = rd.sections["market_intelligence"].data.get(ticker, {})
        if mi.get("analyst_sentiment"):
            slot["analyst_sentiment"] = mi["analyst_sentiment"]
        if mi.get("technical_context"):
            slot["technical_context"] = mi["technical_context"]
        if slot:
            ctx[ticker] = slot
    return ctx


def enrich_investment_conclusion(rd: ResearchData, intent_type: str, analyses: dict[str, AIAnalysis] | None) -> None:
    """Platform-computed confidence + structured score context into the contract."""
    conf = compute_confidence(intent_type, rd.sections)
    ctx = build_score_context(rd, analyses)
    if not ctx and conf["confidence_score"] == 0.0:
        return
    rd.sections["investment_conclusion"] = ResearchSection(
        source="derived(platform)",
        status=SectionStatus.AVAILABLE,
        data={"confidence": conf, "score_context": ctx},
    )


def _mark_available(sections: dict[str, ResearchSection], key: str, source: str = "yfinance.info") -> dict:
    if sections[key].status == SectionStatus.MISSING:
        sections[key] = ResearchSection(source=source, status=SectionStatus.AVAILABLE)
    return sections[key].data


def enrich_market_intelligence(rd: ResearchData, analyses: dict[str, AIAnalysis] | None) -> None:
    """Market Intelligence container: market context (real data only), analyst sentiment,
    technical context (numbers only), news availability. Deterministic."""
    for ticker, a in (analyses or {}).items():
        if not (a.raw_data and a.raw_data.history):
            continue
        info = a.raw_data.info
        fund = info.fundamentals or {}
        slot: dict = {}

        if rd.sections["market"].status == SectionStatus.AVAILABLE:
            slot["market_context"] = {"available": True, "source": "screening"}
        else:
            slot["market_context"] = {"available": False, "reason": REASON_NO_MARKET_CONTEXT}

        analyst = {}
        for k, label in (
            ("recommendationKey", "recommendation_key"),
            ("recommendationMean", "recommendation_mean"),
            ("targetMeanPrice", "target_mean"),
            ("targetHighPrice", "target_high"),
            ("targetLowPrice", "target_low"),
        ):
            if fund.get(k) is not None:
                analyst[label] = fund[k]
        if analyst:
            slot["analyst_sentiment"] = analyst

        tech = compute_technical_context(a.raw_data.history, fund.get("52WeekChange"))
        if tech:
            slot["technical_context"] = tech

        slot["news_availability"] = {"status": "unavailable", "reason": REASON_NEWS_UNAVAILABLE}

        if slot:
            rd.sections["market_intelligence"] = ResearchSection(
                source="yfinance.info; derived(price_history)",
                status=SectionStatus.PARTIAL,
                reason=REASON_NEWS_UNAVAILABLE,
                data={ticker: slot},
            )


def enrich_research_data(rd: ResearchData, analyses: dict[str, AIAnalysis] | None) -> None:
    """Platform enrichment phase: derived metrics into the contract. Deterministic."""
    for ticker, a in (analyses or {}).items():
        if not (a.raw_data and a.raw_data.history):
            continue
        hist = a.raw_data.history
        info = a.raw_data.info
        price = hist[-1].close

        price_data = _mark_available(rd.sections, "price", source="yfinance.info")
        price_data.setdefault(ticker, {})
        fund = info.fundamentals or {}
        price_data[ticker].update(compute_price_position(price, fund.get("fiftyTwoWeekHigh"), fund.get("fiftyTwoWeekLow")))

        vol = compute_volatility([p.close for p in hist])
        if vol is not None:
            risk_data = _mark_available(rd.sections, "risk", source="derived(price_history)")
            risk_data.setdefault(ticker, {})["volatility_annual_pct"] = vol

        raw = _get_financials(ticker)
        if raw:
            metrics = enrich_financials(raw)
            if metrics:
                fin_data = _mark_available(rd.sections, "financial", source="yfinance.financials")
                fin_data[ticker] = metrics
            else:
                rd.sections["financial"] = ResearchSection(
                    source="yfinance.financials",
                    status=SectionStatus.PARTIAL,
                    reason=REASON_FINANCIALS_UNAVAILABLE,
                    data=rd.sections["financial"].data,
                )


def build_research_data(intent: ResearchIntent, screening_results, analyses, comparison, data_quality) -> ResearchData:
    """Normalize research outputs into the provider-independent ResearchData contract."""
    sections = {key: ResearchSection() for key in REPORT_SECTIONS}
    dq = data_quality or {}

    if screening_results:
        sections["market"] = ResearchSection(
            source="screening", status=SectionStatus.AVAILABLE, data={"results": screening_results[:15]}
        )

    if comparison and comparison.get("analysis"):
        comp = _mark_available(sections, "comparison", source="ai")
        comp["analysis"] = _trim_analysis(comparison.get("analysis", ""))

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
            if a.summary:
                technical[ticker]["analysis"] = _trim_analysis(a.summary)
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

    research_data = build_research_data(intent, screening_results, analyses, comparison, data_quality)
    enrich_research_data(research_data, analyses)
    enrich_market_intelligence(research_data, analyses)
    enrich_investment_conclusion(research_data, intent.type, analyses)

    user_prompt = build_report_prompt(research_data)
    system_prompt = _build_system_prompt()
    llm_result = chat_completion([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ], temperature=0)

    ai_failed = False
    executive_summary = ""
    recommendations = []
    if llm_result:
        sections = _extract_sections(llm_result)
        executive_summary = sections["summary"]
        recommendations = sections["recommendations"]
    else:
        ai_failed = True

    if not executive_summary:
        executive_summary = "Laporan riset otomatis berdasarkan data terkini."
    if not recommendations:
        recommendations = ["Lakukan analisis manual lebih lanjut sebelum keputusan investasi."]

    if llm_result:
        topic = intent.sector or query.strip()[:50]
        get_store().add_or_update(
            MemoryType.RESEARCH_FINDING,
            f"Laporan riset ({intent.type}) '{query[:60]}':\n{llm_result}",
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
        ai_failed=ai_failed,
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


def _fmt_num(v) -> str:
    if isinstance(v, (int, float)):
        if abs(v) >= 1e12:
            return f"{v / 1e12:.1f}T"
        if abs(v) >= 1e9:
            return f"{v / 1e9:.1f}B"
        if abs(v) >= 1e6:
            return f"{v / 1e6:.1f}M"
        return f"{v:.2f}"
    return str(v)


def _fmt_metric(v) -> str:
    if not isinstance(v, dict):
        return _fmt_num(v)
    latest = v.get("latest")
    if latest is None:
        return ""
    s = _fmt_num(latest)
    yoy = v.get("yoy_pct")
    if yoy is not None:
        s += f" ({yoy:+.1f}% YoY)"
    return s


def _serialize_financial(data: dict) -> list[str]:
    lines = []
    for ticker, metrics in data.items():
        parts = []
        for label, key in (
            ("Pendapatan", "revenue"),
            ("Laba bersih", "net_income"),
            ("Utang", "total_debt"),
            ("Kas", "cash"),
            ("Ekuitas", "equity"),
            ("Arus kas operasi", "operating_cash_flow"),
            ("FCF", "free_cash_flow"),
        ):
            s = _fmt_metric(metrics.get(key))
            if s:
                parts.append(f"{label} {s}")
        if parts:
            lines.append(f"- {ticker}: " + "; ".join(parts))
    return lines


def _serialize_conclusion(data: dict) -> list[str]:
    lines = []
    conf = data.get("confidence", {})
    lines.append(f"- confidence_level: {conf.get('confidence_level')} (skor {conf.get('confidence_score')})")
    for label, reducer in (("pengurang", "missing_sections"), ("sebagian", "partial_sections")):
        items = conf.get(reducer) or {}
        if items:
            lines.append(f"- {label}: " + ", ".join(f"{k} ({r})" if r else k for k, r in items.items()))
    for ticker, ctx in (data.get("score_context") or {}).items():
        bits = []
        ind = ctx.get("indicators")
        if ind:
            bits.append(", ".join(f"{k}={v}" for k, v in ind.items()))
        analyst = ctx.get("analyst_sentiment")
        if analyst:
            mean = analyst.get("recommendation_mean")
            target = analyst.get("target_mean")
            bits.append("analis " + analyst.get("recommendation_key", "n/a") + (f" ({mean})" if mean is not None else "") + (f", target {target}" if target is not None else ""))
        tech = ctx.get("technical_context")
        if tech:
            vals = []
            for key in ("vs_sma20_pct", "vs_sma50_pct", "week52_change_pct"):
                if tech.get(key) is not None:
                    vals.append(f"{key}={tech[key]}")
            if vals:
                bits.append("teknikal: " + ", ".join(vals))
        if bits:
            lines.append(f"- {ticker}: " + "; ".join(bits))
    return lines


def _serialize_market_intelligence(data: dict) -> list[str]:
    lines = []
    for ticker, slot in data.items():
        parts = []
        ctx = slot.get("market_context")
        if ctx and ctx.get("available"):
            parts.append("konteks pasar tersedia (screening)")
        analyst = slot.get("analyst_sentiment")
        if analyst:
            mean = analyst.get("recommendation_mean")
            target = analyst.get("target_mean")
            parts.append(f"analis {analyst.get('recommendation_key', 'n/a')}" + (f" ({mean})" if mean is not None else "") + (f", target {target}" if target is not None else ""))
        tech = slot.get("technical_context")
        if tech:
            bits = []
            if tech.get("vs_sma20_pct") is not None:
                bits.append(f"+{tech['vs_sma20_pct']}% vs SMA20" if tech["vs_sma20_pct"] >= 0 else f"{tech['vs_sma20_pct']}% vs SMA20")
            if tech.get("vs_sma50_pct") is not None:
                bits.append(f"{tech['vs_sma50_pct']:+}% vs SMA50")
            if tech.get("week52_change_pct") is not None:
                bits.append(f"52w {tech['week52_change_pct']:+.1f}%")
            if bits:
                parts.append("teknikal: " + ", ".join(bits))
        news = slot.get("news_availability", {})
        if news.get("status") == "unavailable":
            parts.append(f"berita: tidak tersedia ({news.get('reason', '')})")
        if parts:
            lines.append(f"- {ticker}: " + "; ".join(parts))
    return lines


def _serialize_section_data(data: dict) -> list[str]:
    out = []
    for key, val in data.items():
        if isinstance(val, dict):
            parts = ", ".join(f"{k}={v}" for k, v in val.items() if v is not None)
            out.append(f"- {key}: {parts}")
        elif isinstance(val, list):
            out.append(f"- {key}: " + "; ".join(str(x) for x in val))
        else:
            out.append(f"- {key}: {val}")
    return out


def serialize_research_data(rd: ResearchData) -> str:
    """Deterministic, token-thin serialization: available/partial sections only."""
    lines = ["## Ringkasan Eksekutif"]
    for key in REPORT_SECTIONS:
        if key == "executive_summary":
            continue
        sec = rd.sections[key]
        if sec.status == SectionStatus.MISSING:
            continue
        lines.append(f"## {REPORT_SECTION_LABELS.get(key, key.replace('_', ' ').title())}")
        if key == "market":
            results = sec.data.get("results", [])
            top = ", ".join(
                f"{r['ticker']} {r.get('top_signal').signal if r.get('top_signal') else 'N/A'}"
                for r in results[:5]
            )
            lines.append(f"- {len(results)} kandidat; top: {top}")
        elif key == "financial":
            lines.extend(_serialize_financial(sec.data))
        elif key == "market_intelligence":
            lines.extend(_serialize_market_intelligence(sec.data))
        elif key == "investment_conclusion":
            lines.extend(_serialize_conclusion(sec.data))
        else:
            lines.extend(_serialize_section_data(sec.data))
    lines.append("## Rekomendasi")
    return "\n".join(lines)


def build_report_prompt(rd: ResearchData) -> str:
    """Prompt Builder: ResearchData -> AI message. Deterministic per input."""
    template = _load_prompt("research.md")
    return template.replace("{{data}}", serialize_research_data(rd))
