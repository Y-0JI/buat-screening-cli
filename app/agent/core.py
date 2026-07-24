from app.router.engine import fetch_stock, build_context
from app.models.analysis import AIAnalysis
from app.services.llm import chat_completion


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
            summary=_extract_section(llm_result, "Ringkasan"),
            key_metrics=_extract_metrics(ctx["indicators"]),
            risks=_extract_list(llm_result, "Risiko"),
            conclusion=_extract_section(llm_result, "Kesimpulan"),
            raw_data=data,
        )

    return AIAnalysis(
        ticker=ticker.upper(),
        summary="Analisis AI tidak tersedia (periksa konfigurasi API key)",
        key_metrics={"indikator": ctx["indicators"]},
        risks=[],
        conclusion="Aktifkan OpenRouter API key untuk analisis AI.",
        raw_data=data,
        screening_results=None,
    )


def compare_with_ai(tickers: list[str]) -> dict:
    results = []
    for t in tickers:
        data = fetch_stock(t)
        if data:
            ctx = build_context(data)
            results.append(ctx)

    if not results:
        return {"type": "error", "message": "Data tidak ditemukan"}

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

    return {
        "type": "comparison",
        "tickers": tickers,
        "analysis": llm_result or "Analisis AI tidak tersedia",
        "data": {r["ticker"]: {"price": r["price"], "change": r["change"], "indicators": r["indicators"]} for r in results},
    }


def ask_llm(user_query: str, context: str = "") -> str | None:
    messages: list[dict] = [
        {"role": "system", "content": _load_prompt("system.md")},
    ]
    if context:
        messages.append({"role": "user", "content": f"Context:\n{context}\n\nQuestion: {user_query}"})
    else:
        messages.append({"role": "user", "content": user_query})
    return chat_completion(messages)


def _extract_section(text: str, section: str) -> str:
    pattern = f"**{section}**"
    if pattern not in text:
        return text
    after = text.split(pattern, 1)[1].strip()
    for s in ["Ringkasan", "Metrik", "Risiko", "Kesimpulan"]:
        if s != section and f"**{s}**" in after:
            return after.split(f"**{s}**")[0].strip()
    return after


def _extract_metrics(indicators_str: str) -> dict[str, str | float]:
    metrics: dict[str, str | float] = {}
    for part in indicators_str.split("|"):
        part = part.strip()
        if "=" in part:
            k, v = part.split("=", 1)
            metrics[k.strip()] = v.strip()
    return metrics


def _extract_list(text: str, section: str) -> list[str]:
    pattern = f"**{section}**"
    if pattern not in text:
        return []
    after = text.split(pattern, 1)[1].strip()
    next_section = None
    for s in ["Ringkasan", "Metrik", "Risiko", "Kesimpulan"]:
        if s != section and f"**{s}**" in after:
            next_section = after.split(f"**{s}**")[0]
            break
    content = (next_section or after)
    items = []
    for line in content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("-") or stripped.startswith("*"):
            items.append(stripped.lstrip("-* ").strip())
    return items
