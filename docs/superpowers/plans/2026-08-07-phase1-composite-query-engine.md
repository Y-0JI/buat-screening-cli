# Phase 5 — Composite Query Engine Implementation Plan

> **Untuk agentic workers:** implementasi dari `docs/13.Roadmap_TUI_Search_First_Composite_View.md`,
> Phase 5 saja. Bahasa instruksi high-level — agent baca file sumber dulu, lalu ikuti kontrak.
> Step berformat checkbox (`- [ ]`).

**Goal:** Satu query ticker memicu beberapa fungsi existing (quote, statistik, screening signal, narasi AI) sekaligus dan mengembalikan satu hasil teragregasi per-blok.

**Architecture:** Backend orchestration murni, tanpa render baru. Komposit result jadi input Phase 6 (render screen). Entry CLI = command baru `composite <ticker>`, `natural()` TIDAK diubah.

**Tech Stack:** Python 3.12, stdlib `concurrent.futures`, dataclasses, rich (render CLI), pydantic (tidak dipakai baru).

## Global Constraints

- Data layer dipakai as-is: `fetch_stock`, `build_context`, `run_screening`, `provider.fetch_financials`, `analyze_with_ai`. Tidak ada implementasi ulang engine/pembuat anyar.
- **SMC signal LUAR scope** — tidak ada engine SMC di kode, dan dihapus dari kontrak sampai engine-nya ada.
- Konkurensi: **maksimal 2 worker** paralel (rate-limit cooldown tanpa lock, aman di 2 — `app/tools/yahoo_finance.py:14`).
- `natural()` tetap satu-klausa. Command `composite` berdiri sendiri.
- Block composite persis: `quote`, `stats`, `signal`, `narrative` (satu kata, tanpa spasi).
- JSON contract via `app/cli/json_output.py` (`sanitize`/`dump`).
- Rendering CLI pakai rich + pola `RichPresenter` yang sudah ada. **Stats (rasio fundamental) Wajib muncul di mode non-json juga.**
- Gaya commit ikuti: `git log --oneline -10`.

---

## Anchor kode (bacaan wajib sebelum mulai)

| Fungsi | Lokasi | Kontrak |
|---|---|---|
| `fetch_stock(ticker)` → `StockData \| None` | `app/router/engine.py:15` | fetch tunggal, cache ProviderCache |
| `build_context(data)` → dict (price, change, indicators, name, sector, screening, data_caveats) | `app/router/engine.py:63` | lokal, tanpa network |
| `run_screening(data)` → `list[ScreeningResult]` | `app/router/engine.py:59` | lokal |
| `ScreeningResult(ticker, signal, reason, confidence)` | `app/screeners/engine.py:6` | — |
| `provider.fetch_financials(ticker)` → dict (mentah) | `app/tools/__init__.py:97` | network, cache 168j |
| `enrich_financials(raw, price, info_fundamentals)` → dict rasio (per/der/roa/roe/npm/pbv...) | `app/agent/enrichment.py:118` | lokal, normalize |
| `analyze_with_ai(ticker)` → `AIAnalysis(summary)` | `app/agent/core.py:41` | LLM narrative |
| `_deep_merge_first_wins(dst, src)` — pola merge leaf-level first-wins | `app/tools/__init__.py:15` | **RUJUKAN merge stats** |
| `validate_symbol` / `normalize` | `app/validation` | dipakai command lain |
| `sanitize`/`dump` | `app/cli/json_output.py:14` | JSON output |
| `RichPresenter.stock_header` / `Table` / `Panel` / `_print_screening_results` | `app/presenters/rich_presenter.py` | reuse render |

Gaya test: `tests/test_router.py` (mock di modul `app.router.composite.*`). Runner: `pytest`.

---

## Task 1 — Contract composite

**Files:**
- Create: `app/router/composite.py`

Dataclass (`dataclasses`):
- `CompositeBlock`:
  - `status: str` — `"available"` | `"unavailable"`
  - `data: dict` — default `field(default_factory=dict)`
  - `error: str | None` — default `None`
- `CompositeResult`:
  - `ticker: str`
  - `name: str`
  - `blocks: dict[str, CompositeBlock]` — default `field(default_factory=dict)`
  - `created_at: str` — default `datetime.now(timezone.utc).isoformat()`

Helper (module-private):
- `_ok(data: dict)` → `CompositeBlock(status="available", data=data)`
- `_fail(error: str)` → `CompositeBlock(status="unavailable", data={}, error=error)`

`data` untuk tiap blok:
- `quote`: `{"price": float, "change": str, "name": str, "sector": str}`
- `stats`: `{"indicators": str}` + hasil rasio fundamental (merge first-wins)
- `signal`: `list[dict]` — per item `{"signal", "reason", "confidence"}`
- `narrative`: `{"summary": str}`

- [ ] **Step 1:** Buat `app/router/composite.py` berisi kedua dataclass + helper `_ok`/`_fail`.
- [ ] **Step 2:** File tanpa indent err; import jalan:
      `python -c "from app.router.composite import CompositeBlock, CompositeResult"`

## Task 2 — Orchestrator `build_composite(ticker)`

**File:** modifikasi `app/agent/composite.py` (tambah fungsi + import)

Flow:
1. `t = normalize(ticker)`; init `result = CompositeResult(ticker=t, name="")`.
2. `data = fetch_stock(t)`.
   - `data is None` → tiap blok dari `_fail("Data tidak ditemukan")`, `name=""`, return.
3. `ctx = build_context(data)`:
   - `result.name = ctx["name"]`
   - blok `quote` = `_ok({... price/change/name/sector})`
4. Blok lokal (no thread):
   - `signal` = `_ok([...])` dari `run_screening(data)`.
   - Section awal `stats` = `{"indicators": ctx["indicators"]}`.
5. Blok network independen — **paralel `ThreadPoolExecutor(max_workers=2)`**:
   - `analyze_with_ai(ticker)` → `narrative`. **Bungkus try/except sendiri** — exception di dalam thread tidak boleh bocor ke aggregate. Gagal → `_fail(...)` narrative; blok lain tetap jalan.
   - `provider.fetch_financials(ticker)` → `raw`; jika `raw` terisi → `ratio = enrich_financials(raw, price, data.info.fundamentals)` → **merge ke `stats` dengan aturan first-wins** (karang rujuk `app/tools/__init__.py:15`, tulis helper `_merge_first_wins(dst, src)` module-private). Jangan replace `dst`, dan tidak memakai `dict.update()`.
6. Agregasi ke `result.blocks`; return.

**Kontrak (untuk Task 3):** `build_composite(ticker: str) -> CompositeResult`. Selalu 4 key `blocks`; setiap blok : `available` atau `unavailable`.

- [ ] **Step 1: tulis fungsi + helper merge.**
- [ ] **Step 2: Unit-verifikasi happy path via mock test (Task 4).**

---

## Task 3 — CLI command `composite`

**File:** modif `app/cli/main.py`

Tambahkan `@app.command()`:
```
def composite(
    Ticker: str = typer.Argument(help="Kode saham"),
    json: bool = typer.Option(False, "--json", help="Output JSON terstruktur"),
)
```
- Validasi `validate_symbol` → error exit bila invalid (pola `analyze`/`score`).
- `t = normalize(ticker)`.
- `console.status(...)` → `r = build_composite(t)`.
- **`--json`:** `print(jo.dump(r))` — `sanitize` harusnya serbu dataclass auto.
- **non-`--json` render:** (wajib tampil) —
  - header: `r.name` + ticker, modal `rich.Panel` biar seperti `_p.analysis`.
  - blok `quote`: harga + perubahan.
  - blok `stats`: baris-sendiri — `indicators` DAN tiap ratio fundamental (per/der/roa/roe/npm/pbv) nilai yang ada. **Sudah pasti muncul, bukan cuma JSON.**
  - blok `signal`: table sama `_print_screening_results`.
  - blok `narrative`: text LLM, Panel terpisah dengan border beda — AI-generated jelas terpisah dari data terstruktur.
  - blok `unavailable` → baris `[yellow]⚠ {...data tidak tersedia}[/]` (per-blok, bukan gagalize semua).
  - command `exit code 1` hanya jika blok `quote` unavailable (data inti kosong); selainnya 0.
- `natural()` dan command lain JANGAN diubah.

- [ ] **Step 1: Manjalankan/tambahkan command.**
- [ ] **Step 2 (manual):** `screening composite BBCA --json` → 4 key; `screening composite BBCA` → semua blok tampil termasuk stats.
- [ ] **Edit if needed — jangan biarkan rendering netral.**

---

## Task 4 — Tests

**File baru:** `tests/test_composite.py` (gaya `tests/test_router.py`).

Helper `_mock_stock(price, prev)` (copy dari `tests/test_router.py:7`) + `_recent_cache`.

Patch titik module composite, contoh:
- `patch("app.router.composite.fetch_stock")`
- `patch("app.router.composite.build_context")`
- `patch("app.router.composite.run_screening")`
- `patch("app.router.composite.analyze_with_ai")`
- `patch("app.router.composite.provider")` (untuk `fetch_financials`)

Unit case (4):
1. **happy path** — mock lengkap: 4 blok `available`, `narrative.summary` terpampang, `stats` memuat `indicators` + ratio fundamental.
2. **fetch gagal** — `fetch_stock` → `None` → all 4 blok `unavailable`.
3. **stats fetching gagal** — `provider.fetch_financials` raise `Exception` → blok `stats` `unavailable` + `error`, `signal`, `quote`, `narrative` tetap `available`.
4. **narrative (AI) gagal** (khusus, jangan campu dgn 3): `analyze_with_ai` raise `Exception` → blok `narrative` `unavailable` + `error`, SUBTIME `quote`, `stats`, `signal` tetap `available`.

- [ ] **Run:** `pytest tests/test_composite.py -v` → 4 pass.
- [ ] **Run:** seluruh suite `pytest` masih hijau (jangan ada regresi).

---

## Order kerja & commit

1. Task 1 (model) → commit
2. Task 2 (orchestrator) → commit
3. Task 3 (CLI) → commit
4. Task 4(s) → commit
SesuStatus: komit per task, terse akan disusun lalu dibuatkan PR ke branch main — tidak di-merge sampai direview manual.

## Skip (YAGNI)

- Blok SMC — dihapus sampai engine ada.
- Render composite TUI — Phase 6, 7 dari dok lain. Blok blok di-skip.
- Skema `schema_version`/pydantic model — dataclass cukup.