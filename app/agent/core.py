from app.parser.intent import INTENT_ANALYZE, INTENT_SCREEN, INTENT_COMPARE, INTENT_HELP, INTENT_UNKNOWN
from app.router.engine import fetch_stock, run_screening
from app.services.openrouter import chat_completion


def load_system_prompt() -> str:
    with open("app/prompts/system.md") as f:
        return f.read()


def process(intent: str, params: dict) -> dict:
    if intent == INTENT_ANALYZE:
        data = fetch_stock(params["ticker"])
        return {"type": "analyze", "ticker": params["ticker"], "data": data}

    if intent == INTENT_COMPARE:
        tickers = [t.strip() for t in params["tickers"].split(",")]
        results = []
        for t in tickers:
            data = fetch_stock(t)
            results.append({"ticker": t, "data": data})
        return {"type": "compare", "results": results}

    if intent == INTENT_SCREEN:
        return {"type": "screen", "params": params}

    if intent == INTENT_HELP:
        return {"type": "help"}

    return {"type": "unknown", "query": params.get("text", "")}


def ask_llm(user_query: str, context: str = "") -> str | None:
    system_prompt = load_system_prompt()
    messages: list[dict] = [
        {"role": "system", "content": system_prompt},
    ]
    if context:
        messages.append({"role": "user", "content": f"Context:\n{context}\n\nQuestion: {user_query}"})
    else:
        messages.append({"role": "user", "content": user_query})
    return chat_completion(messages)
