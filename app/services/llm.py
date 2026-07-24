import os
import httpx
from loguru import logger
from app.config.settings import settings


def chat_completion(messages: list[dict], model: str | None = None) -> str | None:
    api_key = settings.ai_api_key or os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        logger.warning("AI_API_KEY tidak dikonfigurasi")
        return None

    base_url = settings.ai_base_url or os.getenv("AI_BASE_URL", "")
    if not base_url:
        logger.warning("AI_BASE_URL tidak dikonfigurasi")
        return None

    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    model_name = model or settings.ai_model or os.getenv("OPENROUTER_MODEL", "")
    payload = {
        "model": model_name,
        "messages": messages,
        "stream": False,
    }

    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as e:
        logger.error(f"AI HTTP {e.response.status_code}: {e.response.text[:200]}")
    except httpx.TimeoutException:
        logger.warning("AI request timeout setelah 30s")
    except Exception as e:
        logger.warning(f"AI request error: {e}")
    return None
