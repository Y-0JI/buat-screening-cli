# AI Provider Migration — Design Spec

## Objective

Replace the current provider-specific AI integration (OpenRouter) with a provider-agnostic configuration, using 9Router as the default AI provider. All existing AI functionality and CLI behavior must remain unchanged.

## Scope

- Migrate to provider-agnostic config via env vars: `AI_API_KEY`, `AI_MODEL`, `AI_BASE_URL`
- Rename `app/services/openrouter.py` to `app/services/llm.py` with generic OpenAI-compatible client
- Update `app/config/settings.py` with generic field names
- Update `app/agent/core.py` import
- Update `.env.example`, `README.md`
- Update tests
- No new AI features, no prompt changes, no architectural redesign

## Design

### 1. Configuration (`app/config/settings.py`)

```python
class Settings(BaseSettings):
    ai_api_key: str = ""
    ai_model: str = ""
    ai_base_url: str = ""
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
```

Backward compatibility: old `OPENROUTER_API_KEY` / `OPENROUTER_MODEL` env vars no longer read by Settings directly. Users update `.env` to new names. Minimal breaking change — one-time rename.

### 2. LLM Client (`app/services/llm.py`)

Rename existing `app/services/openrouter.py` to `app/services/llm.py`. Replace hardcoded OpenRouter URL with `settings.ai_base_url`. Construct endpoint as `{base_url}/chat/completions`. Same function signature `chat_completion(messages, model?)`, same error handling. No classes, no protocols.

### 3. Import Updates

- `app/agent/core.py`: `from app.services.openrouter` → `from app.services.llm`

No other files import the client directly.

### 4. File Changes

| Action | File |
|--------|------|
| Rename | `app/services/openrouter.py` → `app/services/llm.py` |
| Edit | `app/config/settings.py` |
| Edit | `app/agent/core.py` |
| Edit | `.env.example` |
| Edit | `README.md` |
| Edit | `tests/test_config.py` |
| No change needed | `tests/test_agent.py` (mocks `app.agent.core.chat_completion` — same function name, import chain resolves correctly) |

### 5. `.env.example`

```
AI_API_KEY=sk-or-v1-...
AI_MODEL=openai/gpt-4o-mini
AI_BASE_URL=https://openrouter.ai/api/v1
LOG_LEVEL=INFO
```

### 6. Test Updates

- `tests/test_config.py`: Update field name assertions from `openrouter_api_key` → `ai_api_key`, `openrouter_model` → `ai_model`
- `tests/test_agent.py`: No changes needed — mocks target `app.agent.core.chat_completion` remains valid

### 7. Out of Scope

- No new AI features
- No prompt changes
- No architectural redesign
- No additional provider abstraction layers

## Verification

- All existing tests pass
- `screening analyze BBCA`, `screening compare BBCA BBRI`, `screening natural "test"` continue working
- Config reads new env var names correctly
