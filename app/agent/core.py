import re
from app.router.engine import fetch_stock, build_context, run_screening, bulk_screen, bulk_gainers, bulk_losers
from app.models.analysis import AIAnalysis
from app.services.llm import chat_completion
from app.services.stock_list import search


def _load_prompt(name: str) -> str:
    try:
        with open(f"app/prompts/{name}") as f:
            return f.read()
    except FileNotFoundError:
        with open("app/prompts/system.md") as f:
            return f.read()


def _render_template(template: str, **kwargs) -> str:
    for key, val in kwargs.items():
        template = template.replace("{{" + key + "}}", str(val))
    return template


def analyze_with_ai(ticker: str) -> AIAnalysis:
    data = fetch_stock(ticker)
    if not data:
        return AIAnalysis(ticker=ticker.upper(), summary="Data tidak ditemukan", conclusion="Gagal mengambil data")

    ctx = build_context(data)
    prompt = _load_prompt("analysis.md")
    filled = _render_template(prompt, **ctx)

    llm_result = chat_completion([
        {"role": "system", "content": "Kamu adalah asisten riset saham Indonesia."},
        {"role": "user", "content": filled},
    ])

    if llm_result:
        return AIAnalysis(
            ticker=ticker.upper(),
            summary=llm_result,
            key_metrics=_extract_metrics(ctx["indicators"]),
            raw_data=data,
        )

    return AIAnalysis(
        ticker=ticker.upper(),
        summary="Analisis AI tidak tersedia (periksa konfigurasi AI di .env)",
        key_metrics={"indikator": ctx["indicators"]},
        risks=[],
        conclusion="Aktifkan AI API key di file .env untuk analisis AI.",
        raw_data=data,
        screening_results=None,
    )


def compare_with_ai(tickers: list[str]) -> dict:
    results = []
    failed = []
    for t in tickers:
        data = fetch_stock(t)
        if data:
            ctx = build_context(data)
            results.append(ctx)
        else:
            failed.append(t)

    if not results:
        return {"type": "error", "message": f"Data tidak ditemukan: {', '.join(failed)}"}

    prompt_template = _load_prompt("comparison.md")
    stocks_text = "\n".join(
        f"- {r['ticker']}: Harga {r['price']}, Perubahan {r['change']}, Indikator {r['indicators']}, Screening {r['screening']}"
        for r in results
    )
    filled = prompt_template.replace("{{stocks}}", stocks_text)

    llm_result = chat_completion([
        {"role": "system", "content": "Kamu adalah asisten riset saham Indonesia."},
        {"role": "user", "content": filled},
    ])

    analysis = llm_result or "Analisis AI tidak tersedia (periksa konfigurasi AI di .env)"
    if failed:
        analysis += f"\n\n⚠ Tidak dapat memuat data: {', '.join(failed)}"

    return {
        "type": "comparison",
        "tickers": tickers,
        "analysis": analysis,
        "data": {r["ticker"]: {"price": r["price"], "change": r["change"], "indicators": r["indicators"]} for r in results},
    }


def ask_llm(user_query: str, context: str = "") -> str | None:
    system_prompt = _load_prompt("system.md")
    messages = [{"role": "system", "content": system_prompt}]
    if context:
        messages.append({"role": "user", "content": f"Context:\n{context}\n\nQuestion: {user_query}"})
    else:
        messages.append({"role": "user", "content": user_query})

    resp = chat_completion(messages)
    if not resp:
        return None

    tool_match = re.search(r'\[TOOL:\s*(\w+)\s*(.*?)\]', resp, re.DOTALL)
    if not tool_match:
        return resp

    tool_name = tool_match.group(1).lower()
    tool_args = tool_match.group(2).strip().split()
    tool_result = _run_tool(tool_name, tool_args)
    if tool_result is None:
        return resp

    messages.append({"role": "assistant", "content": resp})
    messages.append({"role": "user", "content": f"Tool result:\n{tool_result}\n\nJelaskan hasil ini ke pengguna dengan bahasa natural."})
    return chat_completion(messages) or resp


def _run_tool(name: str, args: list[str]) -> str | None:
    if name == "analyze":
        ticker = args[0].upper() if args else ""
        if not ticker:
            return None
        data = fetch_stock(ticker)
        if not data:
            return f"Data untuk {ticker} tidak ditemukan."
        ctx = build_context(data)
        return (
            f"Ticker: {ctx['ticker']}\n"
            f"Nama: {ctx['name']}\n"
            f"Sektor: {ctx['sector']}\n"
            f"Harga: {ctx['price']}\n"
            f"Perubahan: {ctx['change']}\n"
            f"Indikator: {ctx['indicators']}\n"
            f"Screening: {ctx['screening']}"
        )

    if name == "compare":
        if len(args) < 2:
            return None
        tickers = [a.upper() for a in args[:2]]
        parts = []
        for t in tickers:
            data = fetch_stock(t)
            if not data:
                parts.append(f"{t}: Data tidak ditemukan.")
            else:
                ctx = build_context(data)
                parts.append(f"- {ctx['ticker']}: Harga {ctx['price']}, Perubahan {ctx['change']}, Indikator {ctx['indicators']}, Screening {ctx['screening']}")
        return "\n".join(parts)

    if name == "screen":
        from app.services.stock_list import get_all
        tickers = [s["ticker"] for s in get_all()]
        results = bulk_screen(tickers)
        sector_filter = args[0] if args else None
        if sector_filter:
            results = [r for r in results if r.get("sector") and sector_filter.lower() in r["sector"].lower()]
        if not results:
            return "Tidak ada sinyal screening ditemukan."
        lines = ["Hasil screening:"]
        for r in results[:10]:
            ts = r["top_signal"]
            lines.append(f"- {r['ticker']} ({r.get('sector', '-')}): {ts.signal} ({ts.confidence:.0%}) - {ts.reason}")
        return "\n".join(lines)

    if name == "gainers":
        from app.services.stock_list import get_all
        tickers = [s["ticker"] for s in get_all()]
        results = bulk_gainers(tickers)
        if not results:
            return "Tidak ada data gainers."
        lines = ["Top gainers:"]
        for r in results[:10]:
            lines.append(f"- {r['ticker']}: {r['price']:,.0f} ({r['change']:+.2f}%)")
        return "\n".join(lines)

    if name == "losers":
        from app.services.stock_list import get_all
        tickers = [s["ticker"] for s in get_all()]
        results = bulk_losers(tickers)
        if not results:
            return "Tidak ada data losers."
        lines = ["Top losers:"]
        for r in results[:10]:
            lines.append(f"- {r['ticker']}: {r['price']:,.0f} ({r['change']:+.2f}%)")
        return "\n".join(lines)

    if name == "search":
        query = " ".join(args) if args else ""
        results = search(query)
        if not results:
            return f"Tidak ditemukan saham untuk '{query}'."
        lines = [f"Ditemukan {len(results)} saham:"]
        for s in results[:10]:
            lines.append(f"- {s['ticker']}: {s['name']}")
        return "\n".join(lines)

    return None


def _extract_metrics(indicators_str: str) -> dict[str, str | float]:
    metrics: dict[str, str | float] = {}
    for part in indicators_str.split("|"):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            metrics[k.strip()] = v.strip()
    return metrics
