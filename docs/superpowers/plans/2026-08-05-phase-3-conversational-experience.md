# Phase 3 — Conversational Experience (Execution Plan)

> Instruksi untuk agent murah. Bahasa Indonesia, level "apa yang harus dicapai" — bukan "cara implementasi". Eksplorasi kode dulu, pilih solusi paling sederhana yang konsisten dengan arsitektur existing.

**Goal:** Percakapan multi-turn konsisten di seluruh aplikasi. Satu **Conversation State** jadi satu-satunya sumber konteks follow-up — dipakai `natural` dan `chat`, tanpa sumber konteks lain. Lapisan baru, tidak merombak Phase 1/2.

**Global Constraints:**
- **Conversation State = satu abstraksi** — API `record`/`recent`/`clear`; detail penyimpanan (rolling `IMPORTANT_CONTEXT`) internal, tidak bocor ke pemanggil.
- **Simpan minimum** — hanya info yang dibutuhkan follow-up berikutnya (ticker aktif, workflow, query inti). Bukan hasil analisis, bukan riwayat percakapan. Tiap aksi sukses menggantikan state sebelumnya; state selalu = konteks saat ini, bukan gabungan percakapan.
- **Resolver rule-based** — hanya pola eksplisit, deterministik; bukan parser kedua, tanpa interpretasi bebas. Pola tak cocok → `None`, alur normal yang memutuskan.
- **Netral** — state tidak tahu pemanggil (natural/chat). Tak ada flag mode, tak ada perilaku beda per entry point.
- **Update hanya aksi sukses** — workflow gagal/batal → state lama dipertahankan apa adanya.
- Tanpa tipe memori, storage, atau dependency baru — reuse `IMPORTANT_CONTEXT` + `get_store()` yang sudah ada.
- Perilaku stabil Phase 1/2 tidak berubah (multi-clause, ambiguity, klarifikasi, follow-up compare lama tetap lolos).
- Tiap task: eksplorasi → implementasi → uji → seluruh suite lulus → lanjut. Branch terpisah + PR, tanpa merge tanpa tinjauan.

---

### Task 1: Conversation State (single source)

**Tujuan:** Satu mekanisme simpan+baca konteks percakapan yang bisa dipakai ulang semua entry point. Menggantikan peran `_last_research_context()` yang hanya baca RESEARCH_FINDING terakhir.

**Yang harus dikerjakan:**
- Satu entri rolling `IMPORTANT_CONTEXT` (source `conversation`) berisi konteks percakapan saat ini (ticker aktif, workflow, query inti). Di-overwrite tiap aksi sukses — bukan satu entri per turn, bukan riwayat penuh.
- API `record` (tulis/timpa, dipanggil hanya dari jalur sukses), `recent` (baca konteks saat ini). I/O internal lewat `get_store()`.
- Abstraksi netral: pemanggil hanya pakai API; natural & chat identik. State tidak menyimpan hasil analisis, tidak tahu pemanggil.

**Kriteria selesai:**
- Aksi sukses → entri rolling ter-update; invocation berikutnya (natural) / turn berikutnya (chat) membaca konteks yang sama.
- Bounded: satu entri, konten rolling. Tidak ada antrean panjang entri.
- Entri otomatis muncul di konteks LLM via mekanisme existing (tanpa ubah `serialize_for_prompt`).
- Sesi kosong / tanpa aksi sukses → tidak ada entri baru.
- Pengujian round-trip nyata (bukan mock hasil akhir).

### Task 2: Follow-up resolver penuh

**Tujuan:** Follow-up tidak cuma compare. Kasus jelas ter-resolve via aturan, dari konteks conversation state — multi-hop (2–3 follow-up beruntun), bukan cuma turn terakhir.

**Pola yang harus jalan (rule-based, bahasa natural):**
- `"bandingkan dengan X"` / `"vs X"` → lengkapi ticker dari konteks (perilaku lama dipertahankan).
- `"kalau X gimana?"` / `"gimana dengan X?"` / `"terus X?"` → analyze X.
- Pronoun/anchor: `"dia"`, `"itu"`, `"saham itu"`, `"yang tadi"` → ganti ke ticker dari konteks, lanjut alur parsing normal.
- Rangkaian: `analisa BBRI` → `kalau BBCA gimana?` → `bandingkan dengan BBNI` — tiap hop baca konteks terbaru, bukan konteks turn pertama.

**Kriteria selesai:**
- Setiap pola di atas → query lengkap benar, eksekusi berjalan seperti query normal.
- Tanpa konteks / pola tak cocok → `None`, query jalan apa adanya.
- Parser dan coordination lama tidak diubah untuk menyediakan pola ini (hanya extension pada resolver).
- Pengujian per pola + rangkaian multi-hop berturut.

### Task 3: Integrasi `natural`

**Tujuan:** Alur one-shot natural pakai conversation state sebagai sumber follow-up, menggantikan `_last_research_context()`.

**Yang harus dikerjakan:**
- Setelah action sukses → `record` konteks.
- `_try_followup` baca dari state baru, lalu resolver Task 2; behavior lama untuk compare tetap benar.

**Kriteria selesai:**
- Rangkaian lintas invocation: `natural "analisa BBRI"` → `natural "kalau BBCA gimana?"` → `natural "bandingkan dengan BBNI"`.
- Alur Phase 1/2 (multi-clause, ambiguity, klarifikasi, follow-up compare existing) tetap lulus tanpa perubahan perilaku.

### Task 4: Integrasi `chat`

**Tujuan:** Di mode chat, kasus follow-up jelas ter-resolve konsisten dengan `natural`; LLM tetap pemegang keputusan untuk hal lain.

**Yang harus dikerjakan:**
- Setiap turn: coba resolver Task 2 dulu. Ter-resolve → eksekusi workflow nyata (bukan LLM free tool), hasil direkam ke konteks secara konsisten.
- Tidak ter-resolve → LLM dipakai seperti sekarang (tool-calling bebas tetap jalan).
- Konteks LLM prompt tetap dari memory existing + conversation state, tidak menambah saluran konteks baru.

**Kriteria selesai:**
- Di chat, follow-up yang sama seperti di natural menghasilkan perilaku sejenis (konsisten, bukan duplikat jalur konteks).
- Pertanyaan bebas yang tidak cocok pola tetap ditangani LLM seperti sebelumnya.

### Task 5: Verifikasi menyeluruh

**Kriteria selesai:**
- Seluruh test suite lulus, tidak ada regresi.
- Smoke: rangkaian multi-turn 3-hop di natural DAN chat → hasil benar + entri rolling ter-update.
- Satu aksi gagal sengaja → state lama utuh (tidak ter-overwrite).
- Tidak ada sumber konteks ganda yang tersisa (satu conversation state).

---

**Deliverables:** 1 file conversation state baru (+ resolver), integrasi di `app/cli/main.py`, tests per Task.

**Di luar scope (sudah diputuskan):** riwayat percakapan penuh, memory jangka panjang / personalisasi, LLM planning & reasoning bebas, manajemen banyak sesi, watchlist, fitur baru. Evolusi riwayat penuh ditunda ke fase berikutnya.