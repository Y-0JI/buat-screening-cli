# Phase 3 Fix — Review PR #202 (Execution Plan)

**Latar:** 3 poin review PR #202.

### Poin 1 — Follow-up rusak habis riset penuh
- Root cause: `parse_full("riset bbca")` → research, params cuma `text`; `_record_turn` research simpan `tickers=[]`; resolver early-return `not state.tickers`.
- Fix:
  - Resolver: gate `not state.tickers` dilepas dari semua cabang. `analyze-other` ("kalau X gimana?") jalan tanpa anchor; `compare-one` + pronoun tetap butuh anchor.
  - `_record_turn` research: ekstrak ticker dari query via universe suffix-match (helper `extract_tickers` di `conversation.py`). "riset bbca" → `BBCA`; "riset bank" → kosong.
  - Test baru: `natural "riset bbca"` → state ticker `BBCA` → `"vs bbri"` → compare BBCA+BBRI.

### Poin 2 — Dua mekanisme follow-up; hapus yang mati
- `coordination.py`: hapus `resolve_followup`, `_FOLLOWUP_COMPARE`, `_extract_context_ticker`, `_CONTEXT_TICKER_SOURCE`, `_canonical_ticker` + import tak terpakai.
- `conversation.py`: pindahkan `_canonical_ticker`.
- `main.py`: hapus `_last_research_context`, buang `resolve_followup` + `MemoryEntry` dari import, perbaiki docstring `_try_followup` stale.
- Test: hapus 4 test `resolve_followup` (test_coordination.py); 3 test `_last_research_context` (test_cli.py).
- Bukti: grep zero-reference.

### Poin 3 — Pronoun + ticker pendek konsisten
- Jalur pronoun: setelah substitusi, kanonikali tiap token `\w{2,5}` via universe — sama seperti compare/analyze-other.
- Test baru: `"bandingkan dia dengan bri"` → `"bandingkan BBCA dengan BBRI"`.

### Verifikasi wajib
- (a) riset → follow-up singkat terbaca; (b) satu mekanisme (grep proof); (c) pronoun canon.
- Full suite dari nol, tampilkan jumlah lulus.
- Push ke `feat/phase3-conversational-experience` (PR #202), tanpa merge.