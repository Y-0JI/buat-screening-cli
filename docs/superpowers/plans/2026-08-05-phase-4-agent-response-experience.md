# Phase 4 — Agent Response Experience (Execution Plan)

> Instruksi untuk agent murah. Bahasa Indonesia, level "apa yang harus dicapai" — bukan "cara implementasi". Eksplorasi kode dulu, pilih solusi paling sederhana yang konsisten dengan arsitektur existing.

**Objective:** Jawaban AI (analyze, compare, research, chat, natural) konsisten, terstruktur, detail sesuai konteks, dan diakhiri rekomendasi/langkah berikutnya saat relevan — di seluruh entry point, tanpa ubah parser/orchestrator/conversation state/workflow Phase 1–3.

**Scope:** Lapisan respons AI saja — prompt + panduan bersama. Presenter/renderer dan struktur report existing tidak dirombak. Tanpa kemampuan riset/reasoning baru.

**Global Constraints:**
- Satu Response Guideline reusable — bukan template per workflow.
- Guideline ditaruh di `system.md` (semua alur AI sudah melewatinya via `_build_system_prompt`); prompt spesifik (analysis/comparison/research) mengikuti, tanpa salinan aturan berbeda-beda.
- Perilaku stabil fase sebelumnya tidak berubah — Phase 4 hanya mengubah cara penyampaian hasil.
- Tanpa dependency baru. Tiap task: eksplorasi → implementasi → uji → seluruh suite lulus → lanjut. Branch + PR, tanpa merge tanpa tinjauan.
- **Prinsip tambahan (disepakati saat review):**
  1. Guideline ringkas — hanya prinsip umum yang dipakai bersama, bukan prompt panjang.
  2. Struktur respons vs gaya bahasa dibedakan jelas, bisa berkembang terpisah.
  3. Struktur konsisten, tapi hanya bagian yang relevan dengan pertanyaan — tidak memaksa semua jawaban memiliki bagian yang sama.
  4. Rekomendasi/langkah berikutnya hanya saat benar-benar membantu — tidak untuk pertanyaan definisi/penjelasan sederhana.
  5. Output yang sudah terstruktur (tabel screening, laporan riset) → respons AI melengkapi dengan insight, bukan mengulang isi output.

---

### Task 1: Response Guideline (shared)

**Tujuan:** Satu pedoman respons yang dipakai semua workflow.

**Yang harus dikerjakan:**
- File `app/prompts/response_guideline.md`: dua bagian yang jelas terpisah —
  - **Struktur respons**: ringkasan → isi utama (fakta vs interpretasi jelas) → keterbatasan jika ada → rekomendasi/langkah berikutnya jika relevan. Hanya bagian yang relevan yang muncul; jangan memaksa semua bagian pada tiap jawaban.
  - **Gaya bahasa**: Indonesia natural, kalimat pendek, bullet untuk daftar; variasi di tingkat kata, bukan struktur.
- `system.md` memuat guideline (embed/referensikan) — otomatis diwarisi analyze/compare/chat/riset.
- Hapus instruksi yang bertentangan: "Variasikan struktur — jangan pakai template sama" di `system.md` dan `analysis.md` → ganti dengan "struktur konsisten, variasi bahasa".
- Audit `comparison.md` dan `research.md`: tidak ada instruksi struktur bebas yang bertentangan; bila ada, selaraskan.

**Kriteria selesai:**
- Guideline ada dan ringkas; semua prompt LLM memuat prinsip yang sama.
- Tidak ada instruksi kontradiktif tersisa di folder prompts.
- Pengujian: render tiap prompt → berisi aturan guideline, bebas baris "variasikan struktur".

### Task 2: Tingkat detail sesuai konteks

**Tujuan:** Jawaban singkat untuk pertanyaan singkat, mendalam saat diminta riset/detail.

**Yang harus dikerjakan:**
- Guideline memuat aturan depth switch eksplisit: analyze cepat (tanpa qualifier riset) → poin utama saja; permintaan detail/riset → pembahasan mendalam; chat → sesuaikan panjang turn.
- `analysis.md` memakai aturan ini (bukan instruksi terpisah yang berbeda makna).

**Kriteria selesai:**
- Prompt analyze cepat dan research berisi panduan depth yang jelas dan tidak saling bertentangan.
- Pengujian render prompt membuktikan kedua jalur memuat aturan yang konsisten.

### Task 3: Rekomendasi & langkah berikutnya

**Tujuan:** Jawaban keputusan berakhir dengan rekomendasi yang actionable; non-keputusan menawarkan langkah lanjut.

**Yang harus dikerjakan:**
- Guideline mendefinisikan format rekomendasi konsisten: keputusan (beli/tahan/jual/amati) + alasan berbasis data + catatan risiko/keterbatasan. Rekomendasi hanya muncul saat pertanyaan keputusan/analisis; pertanyaan definisi/penjelasan sederhana tidak dipaksa.
- Bila rekomendasi tidak relevan → akhiri dengan langkah berikutnya yang bisa dilakukan pengguna (mis. "bandingkan dengan BBCA") hanya jika membantu.
- `analysis.md`, `comparison.md`, `research.md` (bagian AI) mengikuti format ini; bagian investasi pada riset report selaras bahasanya tanpa rombak struktur.
- Jalur chat/fallback LLM (`ask_llm`): pertanyaan keputusan → rekomendasi; pertanyaan umum → jawaban + tawaran lanjut opsional.

**Kriteria selesai:**
- Semua prompt yang menghasilkan kesimpulan memuat aturan rekomendasi/langkah berikutnya + syarat kemunculannya.
- Pengujian render prompt + smoke chat (LLM-mocked) membuktikan instruksi terkirim.

### Task 4: Konsistensi seluruh entry point + verifikasi

**Tujuan:** Buktikan semua entry point memakai panduan yang sama, tanpa regresi.

**Yang harus dikerjakan:**
- Audit alur teks AI: analyze, compare, research, chat, natural fallback, dan teks hasil tool (`_run_tool`) — semua tunduk pada guideline.
- Output data-driven (screen table, laporan riset sections) tidak diubah — sudah terstruktur; pastikan instruksi AI tidak menyuruh mengulang output (prinsip 5: AI menambah insight, bukan menyalin tabel).
- `research.md` dicek: AI menulis insight/interpretasi per bagian, tidak menyalin ulang data mentah.

**Kriteria selesai:**
- Seluruh suite lulus, tanpa regresi.
- Smoke: satu analyze, satu compare, satu chat (LLM-mocked) → prompt memuat guideline + instruksi lama yang bertentangan tidak ada.
- Bukti hasil test eksplisit dilampirkan di PR (output pytest lengkap + contoh render prompt), bukan hanya jumlah.

---

**Deliverables:** `app/prompts/response_guideline.md` (baru), pembaruan `system.md`/`analysis.md`/`comparison.md`/`research.md`, tests render prompt, PR ke `main` tanpa merge.

**Out of scope (diputuskan):** presenter/renderer, rombak section report riset, parser/orchestrator/conversation state/workflow Phase 1–3, kemampuan riset baru, LLM planning, memory/personalisasi, perubahan kontrak Conversation State.

**File:** `docs/superpowers/plans/2026-08-05-phase-4-agent-response-experience.md`
