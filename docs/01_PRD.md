# Product Requirements Document (PRD)

# Super IDX AI CLI Screener

**Version:** 2.0 (merged & cleaned)
**Status:** Draft

> Catatan: dokumen ini menggantikan `01_PRD_v1_Engineering.md` dan
> `02_PRD_v2_Engineering.md` (v2 dihapus karena isinya duplikat v1 tanpa
> informasi baru). Detail arsitektur, tech stack, dan struktur folder
> dipindah ke `02_Architecture_and_Technical_Design.md` supaya cuma ada
> satu sumber kebenaran untuk hal teknis — sebelumnya info yang sama
> ditulis ulang di 3 file berbeda dan mulai gak sinkron satu sama lain.

------------------------------------------------------------------------

# 1. Project Vision

Membangun sebuah **AI-powered CLI (Command Line Interface)** untuk
melakukan screening dan analisis saham Indonesia secara interaktif
menggunakan bahasa alami (Natural Language).

Aplikasi ini bertindak sebagai **AI Research Assistant** yang mampu
memahami pertanyaan pengguna, mengambil data yang diperlukan secara
otomatis, melakukan perhitungan indikator, lalu memberikan analisis yang
mudah dipahami.

Target utama bukan sekadar menampilkan data, tetapi membantu pengguna
melakukan riset saham dengan lebih cepat.

------------------------------------------------------------------------

# 2. Project Goals

Membuat AI Assistant yang mampu:

-   Memahami pertanyaan pengguna
-   Mengambil data saham IDX
-   Melakukan screening otomatis
-   Menghitung indikator teknikal
-   Melakukan scoring
-   Memberikan ringkasan analisis
-   Menjelaskan alasan hasil screening

Semua dilakukan melalui Terminal (CLI).

------------------------------------------------------------------------

# 3. Target User

-   Investor pemula
-   Swing Trader
-   Position Trader
-   Investor jangka panjang
-   Pengguna yang nyaman menggunakan terminal

------------------------------------------------------------------------

# 4. Product Philosophy

**Engine terlebih dahulu, UI belakangan.**

CLI menjadi fondasi utama. Engine yang dibangun harus dapat digunakan
kembali untuk:

-   Web
-   Desktop App
-   Telegram Bot
-   Discord Bot
-   REST API
-   Mobile App

Tanpa menulis ulang logika bisnis.

------------------------------------------------------------------------

# 5. MVP Scope

Versi pertama berfokus pada:

-   CLI
-   Yahoo Finance
-   AI Analysis
-   Screening
-   Technical Indicators

Belum mencakup:

-   Trading
-   Broker Integration
-   Portfolio Management
-   Backtesting
-   Web Dashboard

------------------------------------------------------------------------

# 6. Core Modules (fungsional)

Deskripsi *apa yang dikerjakan* tiap modul. Pemetaan ke folder/file ada
di dokumen Architecture.

## AI Agent
- Memahami intent
- Memilih tool
- Menggabungkan hasil
- Menghasilkan jawaban

## Yahoo Finance Tool
- Harga
- OHLCV
- Volume
- Market Cap
- Historical Data

## Technical Indicator Engine
- SMA, EMA, RSI, MACD, ATR, Bollinger Band, ADX, Stochastic

## Screening Engine
- Golden Cross
- Breakout
- Trend
- Volume
- RSI
- EMA Rules

## AI Analysis Engine
AI hanya menginterpretasikan hasil. Perhitungan indikator dilakukan oleh
Python — **AI tidak pernah menghitung indikator sendiri** (lihat
`04_AI_Agent_Specification.md` dan `05_AGENTS.md`).

------------------------------------------------------------------------

# 7. AI Workflow (functional flow)

```
User → AI memahami intent → Memilih tool → Mengambil data Yahoo Finance
→ Menghitung indikator → Melakukan screening → Mengirim hasil ke AI
→ AI membuat ringkasan → Terminal
```

Diagram teknis (layer, komponen) ada di
`02_Architecture_and_Technical_Design.md`.

------------------------------------------------------------------------

# 8. Example Commands

``` bash
analyze BBCA
screen
compare BBCA BBRI
top gainers
top losers
sector bank
trend BBCA
score BBCA
help
```

Natural language:

``` text
Apakah BBCA layak dibeli?
Bandingkan BBCA dan BBRI.
Cari saham yang sedang breakout.
Ringkas kondisi IHSG hari ini.
```

------------------------------------------------------------------------

# 9. AI Responsibilities

**AI:**
- Memahami pertanyaan
- Memilih tool
- Menjelaskan hasil
- Membuat ringkasan

**Python:**
- Menghitung indikator
- Screening
- Pengolahan data

------------------------------------------------------------------------

# 10. Roadmap

## v2
- News Analysis
- Fundamental Analysis
- Financial Statement Summary

## v3
- Portfolio Analysis
- Dividend Analysis
- Alert System
- Export PDF/Excel

## v4
- REST API
- Web Dashboard
- Mobile Client

------------------------------------------------------------------------

# 11. Non Functional Requirements

- Startup CLI cepat
- Logging jelas
- Error handling baik
- Linux-first
- Konfigurasi melalui `.env`
- Cocok untuk laptop spesifikasi rendah

------------------------------------------------------------------------

# 12. Success Criteria

MVP berhasil jika pengguna dapat:

1. Menjalankan CLI.
2. Bertanya dengan bahasa alami.
3. AI memahami intent.
4. Data diambil dari Yahoo Finance.
5. Indikator dihitung.
6. AI menghasilkan analisis.
7. Hasil tampil rapi di terminal.

Engine harus dapat digunakan kembali oleh web, desktop, maupun API tanpa
mengubah logika inti.
