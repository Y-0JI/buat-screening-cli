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


## Multiple Data Provider Strategy

Untuk menjaga arsitektur tetap modular dan provider agnostic, sistem
dirancang agar dapat menggunakan lebih dari satu data provider melalui
tool abstraction.

### Current Provider

- Yahoo Finance / yfinance

### Future Provider

- IDX API
- Additional providers apabila diperlukan di masa mendatang.

### Design Principles

- AI Agent tidak berkomunikasi langsung dengan data provider.
- Seluruh akses data dilakukan melalui tool abstraction.
- Penambahan provider baru tidak boleh mengubah business logic maupun AI Agent.
- AI dapat menggunakan satu atau beberapa provider sesuai kebutuhan analisis.
- Setiap provider harus memiliki antarmuka yang konsisten agar mudah dipertukarkan.

### Expected Benefits

- Meningkatkan ketersediaan data.
- Memungkinkan penggunaan data resmi maupun data pelengkap.
- Mengurangi ketergantungan terhadap satu provider.
- Mempermudah ekspansi engine di masa depan tanpa mengubah arsitektur utama.

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
    cli/            # CLI entrypoint & formatter
    agent/          # intent, tool selection, summarization
    parser/         # intent parsing layer
    router/         # tool orchestration layer
    tools/          # data provider abstraction
    indicators/     # technical indicator calculations
    screeners/      # screening rules engine
    services/       # external services (OpenRouter, stock list)
    config/         # settings (.env)
    models/         # pydantic models (stock, analysis)
    prompts/        # AI prompt templates
    data/           # static data (stock universe)
    utils/          # logging, helpers

tests/              # unit + integration tests
logs/               # runtime logs
docs/
guide/              # project documentation

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
