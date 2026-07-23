# Screening CLI

AI-powered CLI for Indonesian stock screening and analysis.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Copy `.env.example` to `.env` and set your OpenRouter API key:

```
OPENROUTER_API_KEY=sk-or-v1-your-key
OPENROUTER_MODEL=openai/gpt-4o-mini
LOG_LEVEL=INFO
```

## Usage

```bash
# Command mode
screening analyze BBCA
screening compare BBCA,BBRI
screening screen
screening help

# Natural language
screening natural "analisa BBCA"
screening natural "bandingkan BBCA dan BBRI"
screening natural "cari saham breakout"
```

## Test

```bash
python -m pytest tests/ -v
```

## Structure

```
app/
  cli/          CLI entrypoint & formatter
  agent/        Intent parser & AI agent
  tools/        Data sources (Yahoo Finance)
  indicators/   Technical indicators
  screeners/    Screening rules
  services/     External services (OpenRouter)
  config/       Settings (.env)
  models/       Pydantic models
  prompts/      AI prompt templates
  utils/        Logging etc
tests/
```

## Rules

- AI never calculates indicators
- Every feature includes tests
- Provider agnostic architecture
- See `guide/` for full documentation
