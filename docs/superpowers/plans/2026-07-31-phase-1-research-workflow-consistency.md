# Phase 1 — Research Workflow Consistency Execution Plan

> Instruksi untuk agent murah. Bahasa Indonesia, level "apa yang harus dicapai" — bukan "cara implementasi". Sebelum mulai tiap task, eksplorasi dulu area kode yang relevan, lalu pilih solusi paling sederhana yang konsisten dengan arsitektur existing.

**Goal:** Alur riset konsisten di semua cara memulai riset: perintah `analyze`, `compare`, `research`, bahasa natural, dan chat.

**Scope:** Hanya perbaikan konsistensi alur riset. Tidak ada fitur baru, tidak ada refactor di luar yang diperlukan untuk tiap task.

**Global Constraints:**
- Tidak mengubah routing bahasa natural yang sudah ada (`natural "analisa BBCA"` tetap analisis singkat, bukan riset penuh).
- Tidak menambah dependency baru.
- Bahasa UI dan prompt: Indonesia, konsisten dengan yang sudah ada.
- Tiap task: eksplorasi → implementasi paling sederhana → uji → seluruh test suite tetap lulus → lanjut.
- Bekerja di branch terpisah, bukan langsung di `main`.

---

### Task 1: Memori AI terpakai di semua jalur riset

**Tujuan:** Semua jalur yang memanggil AI (analisis, perbandingan, riset penuh, chat) menyuntikkan memori pengguna dengan cara yang sama. Saat ini ada jalur riset penuh yang mengirim placeholder memori yang tidak pernah diisi ke LLM.

**Kriteria selesai:**
- Tidak ada placeholder memori mentah yang lolos ke LLM di jalur mana pun.
- Jalur yang tadinya tidak menyuntikkan memori kini menyuntikkannya, dengan format yang sama seperti jalur lain.
- Ada pengujian yang membuktikan hal ini untuk semua jalur AI.

### Task 2: Keterbatasan data tersaji benar di prompt analisis

**Tujuan:** Catatan keterbatasan data (riwayat pendek, indikator hilang, data basi) sampai ke LLM sebagai teks yang jelas, bukan sebagai sintaks template yang tidak diproses atau representasi data mentah.

**Kriteria selesai:**
- Output analisis per saham menyertakan keterbatasan data dalam bentuk terbaca.
- Tidak ada sisa sintaks template (misal `{% ... %}`) di prompt yang terkirim.
- Ada pengujian yang membuktikan prompt analisis mengandung keterbatasan data dengan format benar.

### Task 3: Keterbatasan data masuk ke perbandingan

**Tujuan:** Perbandingan antar saham menyertakan keterbatasan data per saham, konsisten dengan analisis per saham. Saat ini data itu sudah dihitung tapi tidak diteruskan.

**Kriteria selesai:**
- Prompt perbandingan berisi keterbatasan data untuk setiap saham yang dibandingkan (format sama dengan Task 2).
- Ada pengujian yang membuktikannya.

### Task 4: Tampilan perbandingan konsisten dengan format lain

**Tujuan:** Hasil perbandingan ditampilkan dengan gaya yang sama seperti hasil analisis dan laporan riset (komponen presentasi yang sama), bukan teks mentah yang dicetak langsung.

**Kriteria selesai:**
- Perbandingan dari perintah `compare` tampil dengan format/panel yang sama seperti perbandingan di laporan riset.
- Tidak ada duplikasi logika presentasi untuk konten yang sama.
- Ada pengujian CLI yang membuktikan hasil perbandingan tampil dengan format baru.

### Task 5: Kegagalan data pada riset satu saham berperilaku konsisten

**Tujuan:** Saat data saham gagal diambil, riset satu saham berperilaku sama dengan perintah analisis: pesan error jelas dan proses berhenti dengan kode non-nol. Riset multi-saham tetap toleran parsial (menampilkan yang berhasil, mencatat yang gagal).

**Kriteria selesai:**
- Riset satu saham dengan data gagal → error + exit code non-nol.
- Riset multi-saham dengan sebagian gagal → laporan tetap tampil dengan catatan kegagalan.
- Ada pengujian CLI untuk kedua kasus.

### Task 6: Verifikasi menyeluruh

**Tujuan:** Memastikan tidak ada regresi.

**Kriteria selesai:**
- Seluruh test suite lulus.
- Smoke test manual untuk perbandingan menunjukkan format baru benar-benar tampil.

---

**Di luar scope:** conversation continuity (Phase 2), kualitas jawaban LLM (Phase 3), routing intent bahasa natural, fitur baru apa pun.
