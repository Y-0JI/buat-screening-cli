from app.services.openrouter import chat_completion


def load_system_prompt() -> str:
    with open("app/prompts/system.md") as f:
        return f.read()


def ask_agent(user_query: str, context: str = "") -> str | None:
    system_prompt = load_system_prompt()
    messages: list[dict] = [
        {"role": "system", "content": system_prompt},
    ]
    if context:
        messages.append({"role": "user", "content": f"Context:\n{context}\n\nQuestion: {user_query}"})
    else:
        messages.append({"role": "user", "content": user_query})
    return chat_completion(messages)
