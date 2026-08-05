# Phase 5 — AI-first CLI Experience (Execution Plan)

> Instruksi untuk agent murah. Bahasa Indonesia, level "apa yang harus dicapai" — bukan "cara implementasi". Eksplorasi kode dulu, pilih solusi paling sederhana yang konsisten dengan arsitektur existing.

**Objective:** `screening` tanpa argumen (TTY) langsung membuka sesi AI interaktif — natural language jadi default. CLI commands tetap utuh untuk automation. Reuse seluruh kemampuan fase 1–4, tanpa duplikasi workflow.

**Scope:** Entry experience saja: perilaku no-args + sesi AI unified. Tanpa TUI, tanpa command baru, tanpa ubah parser/orchestration/conversation state/response generation/research workflow.

**Global Constraints:**
- **AI session = lapisan entry, bukan workflow baru.** Seluruh kemampuan berasal dari pipeline existing (`natural` → follow-up → routing → ambiguity → multi-clause → fallback LLM). Tidak ada logika routing baru.
- Sesi AI hanya mengatur siklus interaksi (input → proses → output). Seluruh keputusan tetap di parser, orchestration, conversation state, dan workflow fase sebelumnya.
- **Perilaku interaktif vs non-interaktif terpisah jelas**: TTY + tanpa argumen → sesi AI; non-TTY (pipe/CI/script) → help seperti sekarang, automation tidak berubah.
- **Sesi ringan**: tanpa layout/panel/komponen visual terminal — itu domain roadmap TUI.
- **Satu titik masuk AI**: tidak menambah subcommand baru; entry point aplikasi = entry AI. `_reroute_unknown_to_natural` dan `_KNOWN_COMMANDS` tidak diubah.
- **Dokumentasi jelas**: Phase 5 hanya mengubah cara masuk ke AI, bukan menambah kemampuan AI baru.
- Tanpa dependency baru. Tiap task: eksplorasi → implementasi → uji → seluruh suite lulus → lanjut. Branch + PR, tanpa merge tanpa tinjauan.

---

### Task 1: Entry AI-first (no-args)

**Tujuan:** `screening` di TTY tanpa argumen → sesi AI langsung; non-TTY → help.

**Yang harus dikerjakan:**
- Di callback utama: hanya jika `sys.argv` tanpa argumen apa pun (termasuk flag) DAN stdin TTY → jalankan sesi AI lalu selesai. Selain itu perilaku lama tetap (help di non-TTY, command existing tidak tersentuh).
- Header sesi minimal (1–2 baris identitas + hint `exit`), prompt `> ` — tanpa dekorasi berlebih.

**Kriteria selesai:**
- TTY no-args → prompt AI muncul, langsung bisa tanya.
- Non-TTY no-args → help tampil, tidak menggantung menunggu input.
- `--help` dan semua command dengan argumen berperilaku identik dengan sebelumnya.

### Task 2: Sesi AI unified

**Tujuan:** Satu sesi yang memakai semua kemampuan AI fase 1–4 tanpa duplikasi.

**Yang harus dikerjakan:**
- Loop sesi: baca input → `exit`/`quit`/`keluar` berhenti → selain itu jalankan pipeline `natural` yang sudah ada.
- Akhir sesi: simpan jejak pertanyaan ke memori (pola chat tail existing, source `chat`) — kontinuitas antar sesi tetap lewat memori Phase 2/3. Sesi tanpa isi → tanpa entri baru.

**Kriteria selesai:**
- Di sesi: `analisa bbca` → analyze struktur; `kalau bbca gimana?` → follow-up ter-resolve; pertanyaan bebas → LLM.
- Rangkaian multi-turn lintas keluar-masuk aplikasi tetap terbaca (state Phase 3).
- Tidak ada jalur routing baru yang diduplikasi.

### Task 3: Verifikasi menyeluruh

**Kriteria selesai:**
- Test TTY no-args → sesi: `analisa bbca` → fetch jalan → `exit` → exit 0; jejak memori tersimpan.
- Test non-TTY no-args → output help, tanpa hang.
- Test sesi multi-turn: `analisa bbca` → `vs bri` → compare BBCA+BBRI.
- Seluruh test suite dari nol hijau (bukti output pytest lengkap di PR), tidak ada regresi command existing.

---

**Deliverables:** `app/cli/main.py` (entry + sesi), tests baru, plan doc, `docs/11.Roadmap_AI_Agent_Interaction.md` diperbarui ke versi updated (Phase 5 = AI-first CLI Experience; hapus duplikat `11.Roadmap_AI_Agent_Interaction_updated.md` di root).

**Out of scope (diputuskan):** TUI, desktop/web, command baru, reasoning baru, perubahan parser/orchestration/conversation state/response generation, research workflow baru, perubahan perilaku non-TTY.

**File:** `docs/superpowers/plans/2026-08-05-phase-5-ai-first-cli.md`
