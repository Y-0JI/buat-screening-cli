# Phase 6 — Composite Render Screen Implementation Plan

> **Untuk agentic workers:** implementasi dari `docs/13.Roadmap_TUI_Search_First_Composite_View.md`,
> Phase 6 saja. Bahasa instruksi high-level — agent baca anchor file dulu, ikuti kontrak.
> Step berformat checkbox (`- [ ]`).

**Goal:** Layar TUI baru yang merender hasil composite (Phase 5) sebagai beberapa blok dalam satu layar:
quote, stats, signal screening, narrative AI. Per-blok graceful degradation; narasi AI terpisah
visual dari data terstruktur.

**Konteks:** Backend Phase 5 sudah jadi (`app/router/composite.py` + CLI `composite <ticker>` + `--json`).
Phase 6 = lapisan render Textual saja. Phase 7 (search-first landing) tidak di sini.

## Global Constraints

- **Layout: stacked vertical** (scroll antar blok, bukan tabbed) — keputusan user.
- SMC block LUAR scope (sudah diputuskan Phase 5).
- Block composite persis 4: `quote`, `stats`, `signal`, `narrative`.
- **Terminate wajib**: layar yang spawn proses harus `terminate_process` saat cancel mid-proses —
  revisi khusus atas bug terulang 2x sebelumnya (chat; table/report). PERSIS dgn pola
  `app/tui/screens/report.py:64-71` dan `table.py:38-44`: `proc` PASTI diterminate di `finally` block
  dalam `@work` coroutine, dan Textual membatalkan worker saat screen unmount — sehingga exit/batal
  tengah jalan menghentikan spawn.

- JSON contract dari CLI `composite <ticker> --json` (`app/router/composite.py`):
  ```json
  {
    "ticker": "BBCA",
    "name": "Bank BCA",
    "blocks": {
      "quote":      {"status": "available", "data": {"price": 9500.0, "change": "+1.23%", "name": "...", "sector": "..."}},
      "stats":      {"status": "available", "data": {"indicators": "...", "per": 22.5, ...}},
      "signal":     {"status": "available", "data": {"signals": [{"signal": "BUY", "reason": "...", "confidence": 0.8}]}},
      "narrative":  {"status": "unavailable" | "available" | "partial", "data": {"summary": "..."}, "error": "..."}
    }
  }
  ```
  `status`="partial" khusus stats (financials gagal tp indicators lokal ada).
- Test TUI existing di env ini mungkin pre-existing gagal (async) — handle via baseline
  comparison (Task 0 / Task 5). Jangan menghilangkan test lama.
- `pytest` runner. Commit per task.

---

## Task 0 — Baseline Test (SEBELUM implementasi apa pun)

**Why:** Klaim "test pre-existing gagal" tidak valid tanpa bukti dua angka. Ini snapshot awal.

- [ ] **Step 1:** Jalankan seluruh suite:
      `pytest -q --tb=short` → export/catatan list:
      `pytest --tb=no -q 2>&1 | tail -40 > docs/superpowers/plans/2026-08-08-baseline-phase6.txt`
- [ ] **Step 2:** Catat: jumlah total, jumlah failed, **list nama masing-masing test**.
  Perhatikan mana yang gagal BENDITAS: `tests/test_tui*.py` (async env?) dan `tests/test_json_output.py` (network?).
- [ ] **Step 3:** Simpan snapshot → commit `docs: baseline test Phase 6` (jangan digabung dgn kode).

---

## Task 1 — Registrasi Feature + dispatcher

**Files:**
- Modif: `app/tui/registry.py` (FEATURES)
- Modif: `app/tui/app.py` (`_result_screen`)

**Interfaces:**
- Consumes: `CompositeViewScreen(feature: Feature, argv: list[str], executor: Executor)` (Task 2)
- Produces: FEATURES berisi `Feature("composite", title=..., description=..., group="Analysis",
  command=["composite", "<TICKER>"], args=_TICKER, view="composite")`; `app._result_screen`
  handle `view == "composite"`.

- [ ] **Step 1:** Tambah feature `composite` ke `FEATURES` (`app/tui/registry.py:41`) — ikuti pola `analyze`.
      Kunci: arrow `== "composite"` menentukan screen mana dipakai.
- [ ] **Step 2:** `app/tui/app.py` — tambah branch `if feature.view == "composite": return CompositeViewScreen(feature, argv, self._executor)` di `_result_screen`.
- [ ] **Step 3:** import screen; cek open_feature/submit_feature jalan (dashboard → form ticker → screen composite).
- [ ] **Step 4 (verifikasi manual build):** `python -c "from app.tui.app import ScreeningApp; print('ok')"`.

---

## Task 2 — CompositeViewScreen

**Files:**
- Create: `app/tui/screens/composite.py`

**Interfaces:**
- Consumes: `Executor` (`app/tui/executor.py`), `terminate_process`, `_flatten` (dari `app/tui/screens/report.py:27`),
  JSON schema dari CLI `composite --json`.
- Produces: `CompositeViewScreen(Screen)` dengan compose → quote panel, stats table, signal table,
  narrative panel; escape/b → back.

**Wajib / critical — terminate benar:**
- [ ] **Step 1:** Dari `_load` (`@work(exclusive=True)`):
```python
proc = self._executor.run(self._argv + ["--json"])
try:
    out, _err = await asyncio.to_thread(proc.communicate)
finally:
    terminate_process(proc)
```
- [ ] **Step 2:** parse `out` JSON. Render sesuai block schema.
- [ ] **Step 3:** Per-block renderData:
  - `quote` status available → Panel: name, sector, price, change.
  - `stats` status "available"|"partial" → DataTable label/nilai: `indicators` + ratio (per/pbv/der/roe/npm/roa) — nilai tersedia saja.
    Kalau `partial`: tambah note konsult (⚠ sebagian tidak tersedia).
  - `signal` → DataTable: signal/reason/confidence.
  - `narrative` status "available" → Static text dalam `Panel` dengan **border_style="blue"** — pisah visual dari data terkelompok.
  - Block status unavailable → `Static` "⚠ {quote/stats/signal/narrative}: data tidak tersedia" (masih tampil, tidak gagal seluruh screen).
- [ ] **Step 4:** `action_back` → `self.app.pop_screen()`; bindings `escape`/`b` (pola screen lain).

---

## Task 3 — Test render

**Files:** `tests/test_tui_flow.py` — tambah case (gaya existing `_JsonExecutor`, `test_report_viewer_renders_sections`).

- [ ]**Step 1:** `_JsonExecutor` mock payload 4 blok available.
- [ ] **Step 2:** buka feature composite via form → assert layar jadi CompositeViewScreen; assert widget render quote stats signal narrative teksnya ada.
- [ ] **Step 3:** mock payload narrative unavailable → assert placeholder narrative tampil; quote/stats/signal normal.
- [ ] **Step 4:** jalankan `pytest tests/test_tui_flow.py -k composite -q` → pass (atau fail = list EARLIER).

---

## Task 4b — Test terminate mid-proses (Khusus, diminta user)

**Files:** `tests/test_tui_flow.py`

Buat test (mirip `test_cancel_mid_process_terminates_fast` line 440) khusus `CompositeViewScreen`:
- [ ]**Step 1:** `_SlowSleepExecutor` javan `Popen(["sleep","30"])` dengan stdout/stderr PIPE; simpan proc list.
- [ ] **Step 2:** buka composite screen via `push_screen(CompositeViewScreen(feature, ["composite","BBCA"], slow))`,
  `await pilot.pause()`, lalu `pilot.press("escape")` — screen ditutup saat worker still running.
- [ ] **Step 3:** assert `slow.procs[0].poll() is not None` (proses TERMATI) + elapsed < 5s.
  Ini BUKAN berasumsi ikut pola — test ini memVerifikasi terminate sungguhan jalan.
- [ ] **Step 4:** klaim masukkan ke result: proses tidak nyangkut background.

---

## Task 5 — Post re-run & bandingkan

- [ ]**Step 1:** run new baseline:
      `pytest --tb=no -q 2>&1 | tail -40 > tests/superpowers/...` — SAME capture seperti Task 0.
- [ ] **Step 2:** diff kedua file: jumlah fail harus ≤ baseline **DAN** set test yang tadinya lulus TIDAK ada yang jadi fail baru.
   Kalau ada fail baru → perbaiki tanpa menutup yang lama.
- [ ] **Step 3:** update file baseline comment — note deviation.

---

## Order & commit

1. Task 0 (baseline) → commit docs baseline
2. Task 1 → commit
3. Task 2 → commit
4. Task 3+4 → commit
5. Komit bersama, run test, Task 5 compare, PR → branch main, no merge.

## Skip (YAGNI)
- Phase 7 search-first landing — luar scope.
- Tabbed navigation — dipilih stacked saat mockup.
- Render interaktif tambahan (filter dalam layar) — nanti.
- Unit test untuk helpers `_flatten` — sudah dtest di existing.