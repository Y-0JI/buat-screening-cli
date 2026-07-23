# Screening CLI

AI-powered CLI for Indonesian stock screening and analysis.

## Requirements

- Python 3.12+

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Copy `.env.example` to `.env` and configure:

```
AI_API_KEY=your-api-key-here
AI_MODEL=openai/gpt-4o-mini
AI_BASE_URL=https://openrouter.ai/api/v1
LOG_LEVEL=INFO
```

Verify installation:

```bash
screening --help
```

## Usage

```bash
# Analysis
screening analyze BBCA
screening trend BBCA
screening score BBCA

# Comparison
screening compare BBCA BBRI
screening compare BBCA,BBRI

# Bulk screening
screening screen
screening screen --sector Financials
screening screen --limit 5

# Market overview
screening gainers
screening losers
screening sector Financials

# Stock universe
screening stocks
screening stocks bank

# Natural language
screening natural "analisa BBCA"
screening natural "bandingkan BBCA dan BBRI"
screening natural "cari saham breakout"

# Help
screening info
```

## Commands

| Command | Description |
|---------|-------------|
| `analyze <ticker>` | AI-powered stock analysis |
| `trend <ticker>` | Technical trend analysis |
| `score <ticker>` | Full screening score |
| `compare <t1> [t2]` | Compare stocks |
| `screen [opts]` | Bulk screening (--sector, --limit) |
| `gainers` | Top gainers today |
| `losers` | Top losers today |
| `sector <name>` | Screening by sector |
| `stocks [query]` | List/search stocks |
| `natural "<query>"` | Natural language query |
| `info` | Help |

## Test

```bash
python -m pytest tests/ -v
```

## Structure

```
app/
  cli/          CLI entrypoint & formatter
  agent/        AI agent (intent, summarization)
  parser/       Intent parsing
  router/       Tool orchestration
  tools/        Data providers (Yahoo Finance)
  indicators/   Technical indicators
  screeners/    Screening rules
  services/     OpenRouter, stock list
  config/       Settings (.env)
  models/       Pydantic models
  prompts/      AI prompt templates
  data/         Stock universe (951 IDX emiten)
  utils/        Logging etc
tests/
```

## Rules

- AI never calculates indicators
- Every feature includes tests
- Provider agnostic architecture
- See `guide/` for full documentation
