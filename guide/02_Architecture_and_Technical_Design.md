# Architecture & Technical Design

**Version:** 2.0 (merged & cleaned)

> Menggantikan `03_System_Architecture.md` dan `05_Technical_Design_Document.md`
> (isinya overlap ~90%, sekarang satu file). Dua perbaikan dari versi
> lama:
> 1. Layer **"Planner"** yang muncul di diagram lama dihapus — gak
>    pernah didefinisikan tanggung jawabnya di mana pun, dan
>    `04_AI_Agent_Specification.md` sudah menyatakan "decide tools"
>    adalah tugas Agent. Kalau nanti memang perlu planner terpisah
>    dari agent, tambahkan di sini DAN definisikan rule-nya di
>    AI Agent Specification — jangan cuma muncul di diagram.
> 2. Module list sekarang sinkron dengan folder structure (sebelumnya
>    TDD lupa menyebut `models/` dan `prompts/`).

------------------------------------------------------------------------

# 1. High Level Architecture

``` text
User
 │
 ▼
CLI
 │
 ▼
Command Parser
 │
 ▼
AI Agent          (memahami intent + memilih tool, lihat AI Agent Spec)
 │
 ▼
Tool Router
 ├── Yahoo Finance
 ├── Technical Indicator Engine
 ├── Screening Engine
 ├── Fundamental Engine (future)
 └── News Engine (future)
 │
 ▼
OpenRouter
 │
 ▼
Response Formatter
 │
 ▼
Terminal
```

## Layers

| Layer | Isi |
|---|---|
| Presentation | `cli/` |
| Agent | `agent/` (intent understanding, tool selection, summarization) |
| Business Logic | `indicators/`, `screeners/` |
| Data Access | `tools/`, `services/` |
| External Services | Yahoo Finance, OpenRouter |

------------------------------------------------------------------------

# 2. Technology Stack

## CLI / Runtime
- Python 3.12+

## AI
- OpenRouter API
- **MVP: 1 model default** (dipilih saat setup, via `.env`). Arsitektur
  tetap provider-agnostic (tool router tidak bergantung ke satu model
  tertentu), jadi menambah model lain (GPT/Gemini/DeepSeek/Qwen) di
  kemudian hari cukup ganti config — tidak perlu diintegrasikan &
  ditest semuanya sejak MVP.

## Data Source
- Yahoo Finance / yfinance

## CLI UI
- Rich

## Configuration
- `.env`

## Dependency Management
- uv (disarankan) atau pip

## Logging
- loguru

## Validation
- Pydantic

------------------------------------------------------------------------

# 3. Folder Structure

``` text
super-screening-ai/

app/
    cli/
    agent/          # intent, tool selection, summarization (termasuk yang dulu direncanakan masuk folder ai/ terpisah)
    tools/
    indicators/
    screeners/
    services/
    config/
    models/         # pydantic models
    prompts/        # prompt templates
    utils/

tests/
logs/
docs/

.env
README.md
```

> Folder `ai/` yang ada di draft lama dihapus — isinya (intent
> understanding, tool selection, ringkasan) sudah jadi tanggung jawab
> `agent/`, dua folder untuk hal yang sama cuma bikin bingung mau taruh
> file baru di mana.

------------------------------------------------------------------------

# 4. Standards

- Python 3.12+
- Type hints
- Pydantic models
- Loguru logging
- Rich UI
- Unit tests (satu per fitur, lihat catatan di Sprint Roadmap)
- `.env` configuration

------------------------------------------------------------------------

# 5. Engineering Principles

- Modular & SOLID
- Testable
- Provider agnostic (data source & AI model)
- Configuration driven
- Replaceable components — engine tidak boleh terikat ke CLI, lihat
  `01_PRD.md` §4 (Product Philosophy)
