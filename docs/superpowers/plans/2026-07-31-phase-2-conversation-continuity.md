# Phase 2 — Conversation Continuity (Execution Plan)

> Instruksi untuk agent murah. Bahasa Indonesia, level "apa yang harus dicapai" — bukan "cara implementasi". Eksplorasi kode dulu, pilih solusi paling sederhana yang konsisten dengan arsitektur existing.

**Goal:** Riset dan percakapan membangun di atas interaksi sebelumnya — konteks riset penuh tersimpan, percakapan berlanjut antar sesi. Tanpa bangun sistem baru.

**Global Constraints:**
- Manfaatkan penyimpanan memori yang sudah ada — jangan buat storage baru.
- Tidak menambah dependency.
- Tiap task: eksplorasi → implementasi paling sederhana → uji → seluruh test suite lulus → lanjut.
- Bekerja di branch terpisah dari `main` (PR baru, tidak di-merge tanpa tinjauan).

---

### Task 1: Ringkasan riset tersimpan ke memori

**Tujuan:** Laporan riset penuh (ringkasan eksekutif, rekomendasi, jenis riset) disimpan ke memori saat selesai dibuat, sehingga riset berikutnya bisa memanfaatkannya. Sekarang hanya analisis per-ticker yang tersimpan; riset gabungan/sektor tidak.

**Yang harus dikerjakan:**
- Saat laporan riset berhasil disusun, simpan satu entri memori berisi: jenis riset, topik/ticker, inti ringkasan eksekutif, dan rekomendasi — sebagai satu kesatuan.
- Gunakan tipe memori temuan riset yang sudah ada, supaya muncul di konteks AI permintaan berikutnya lewat mekanisme yang sudah berjalan.
- Laporan yang gagal total (tanpa data) tidak menghasilkan entri.

**Kriteria selesai:**
- Riset selesai → entri memori baru terbentuk dan terlihat di konteks AI berikutnya.
- Riset gagal total → tidak ada entri baru.
- Ada pengujian untuk kedua kasus (jalankan alur riset sesungguhnya, bukan simulasi hasil akhir).

### Task 2: Percakapan chat berlanjut antar sesi

**Tujuan:** Saat sesi chat berakhir, jejak percakapan tersimpan ke memori sehingga sesi berikutnya mendapat konteks percakapan sebelumnya. Sekarang percakapan hilang begitu sesi keluar.

**Keputusan (sudah ditetapkan):** simpan tanpa AI — potongan beberapa pertanyaan-jawaban terakhir secara verbatim (terpotong wajar), gratis dan deterministik. Tidak meringkas dengan AI.

**Yang harus dikerjakan:**
- Keluar dari sesi chat → satu entri memori berisi jejak beberapa pertanyaan-jawaban terakhir.
- Entri muncul di konteks AI permintaan berikutnya (tidak perlu mekanisme baru — pakai yang sudah ada).
- Percakapan kosong (langsung keluar tanpa isi) tidak menghasilkan entri.

**Kriteria selesai:**
- Sesi chat berisi percakapan → keluar → entri memori baru terbentuk.
- Sesi chat kosong → keluar → tidak ada entri baru.
- Ada pengujian untuk kedua kasus.

### Task 3: Verifikasi menyeluruh

**Kriteria selesai:**
- Seluruh test suite lulus, tidak ada regresi.
- Smoke test: satu riset → cek entri memori baru; satu sesi chat singkat → cek entri konteks baru.

---

**Di luar scope (sudah diputuskan):** ringkasan percakapan cerdas pakai AI (nanti di fase kualitas, kalau perlu), jalur mengisi preferensi pengguna (tipe memori itu dibiarkan nganggur), kualitas jawaban LLM (Phase 3 roadmap riset), pengorganisasian pengetahuan memori, fitur baru.
