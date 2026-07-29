# Sprint Roadmap

**Version:** 2.0 (merged & cleaned)

> Perbaikan dari versi lama: `05_Technical_Design_Document.md` /
> `07_AGENTS.md` mewajibkan *"every feature must include tests"*, tapi
> roadmap lama numpuk semua testing di Sprint 8. Itu kontradiksi —
> kalau testing wajib per-fitur, testing gak boleh nunggu 7 sprint dulu
> baru dikerjakan. Sekarang testing jadi Definition of Done tiap
> sprint, dan Sprint 8 diganti jadi polish + dokumentasi final.

------------------------------------------------------------------------

## Sprint 1 — Project Setup
- Project setup
- CLI
- Config
- Logging
- **DoD:** unit test untuk config loader & CLI entrypoint

## Sprint 2 — Data Layer
- Yahoo Finance Tool
- Data models
- **DoD:** unit test untuk Yahoo Finance Tool (mock response)

## Sprint 3 — Indicator Engine
- Indicator Engine (SMA, EMA, RSI, MACD, ATR, Bollinger, ADX, Stochastic)
- **DoD:** unit test per indikator terhadap nilai referensi yang diketahui

## Sprint 4 — Screening Engine
- Screening Engine (Golden Cross, Breakout, Trend, Volume, RSI, EMA Rules)
- **DoD:** unit test per rule screening

## Sprint 5 — AI Agent
- AI Agent
- OpenRouter integration
- **DoD:** test tool-selection logic (mock LLM response)

## Sprint 6 — Natural Language Commands
- Natural language commands
- **DoD:** test parsing intent dari beberapa contoh kalimat natural language

## Sprint 7 — Formatter & Reports
- Formatter
- Reports
- **DoD:** test output formatting (snapshot/golden file)

## Sprint 8 — Polish & Documentation
- Integration test end-to-end (CLI → Agent → Tool → Formatter)
- Final documentation update
- Bug fixing dari hasil integration test
