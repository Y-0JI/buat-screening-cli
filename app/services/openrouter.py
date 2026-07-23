import httpx
from loguru import logger
from app.config.settings import settings


def chat_completion(messages: list[dict], model: str | None = None) -> str | None:
    if not settings.openrouter_api_key:
        logger.warning("OPENROUTER_API_KEY tidak dikonfigurasi")
        return None

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model or settings.openrouter_model,
        "messages": messages,
    }

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as e:
        logger.error(f"OpenRouter HTTP {e.response.status_code}: {e.response.text[:200]}")
    except httpx.TimeoutException:
        logger.warning("OpenRouter timeout setelah 30s")
    except Exception as e:
        logger.warning(f"OpenRouter error: {e}")
    return None
