# Phase 1 Lanjutan — Tuntaskan Konsistensi Alur Riset (Execution Plan)

> Instruksi untuk agent murah. Bahasa Indonesia, level "apa yang harus dicapai" — bukan "cara implementasi". Eksplorasi kode dulu, pilih solusi paling sederhana yang konsisten dengan arsitektur existing.

**Goal:** Tuntaskan 4 hal yang tersisa dari Phase 1 konsistensi alur riset (follow-up review PR Phase 1).

**Global Constraints:**
- Tidak bangun ulang yang sudah berfungsi.
- Tidak mengubah perilaku routing yang sudah benar di luar perbaikan yang diminta.
- Tidak menambah dependency.
- Tiap task: eksplorasi → implementasi paling sederhana → uji → seluruh test suite lulus → lanjut.
- Bekerja di branch terpisah dari `main` (PR baru, terpisah dari PR Phase 1 yang masih terbuka).

---

### Task 1: Satu mekanisme pemahaman query

**Tujuan:** Dua mekanisme pemahaman query yang berjalan terpisah disatukan. Mekanisme riset memanfaatkan hasil mekanisme yang sudah ada lebih dulu — bukan menduplikasi logika sendiri.

**Pemetaan tipe — keputusan eksplisit (wajib diikuti, jangan diganti-ganti):**

Query yang lewat jalur riset dipetakan dari hasil pemahaman query yang sudah ada sebagai berikut:

| Kategori hasil pemahaman query | Jadi tipe riset | Catatan |
|---|---|---|
| analisis satu saham | riset satu saham | |
| perbandingan | riset perbandingan | |
| screening (dengan sektor) | riset berbasis sektor + filter sektor | perilaku hari ini dipertahankan |
| screening (tanpa sektor) | riset berbasis sektor tanpa filter | perilaku hari ini dipertahankan |
| riset umum | riset berbasis sektor tanpa filter | perilaku hari ini dipertahankan |
| gainers / losers / daftar saham / bantuan / tidak dikenali | **DITOLAK** — hasil riset kosong + pesan penjelas singkat ("query ini bukan permintaan riset"), tanpa memanggil AI, tanpa screening massal | keputusan baru, alasan: memanggil AI & screening 951 saham untuk query "help"/"gainers" adalah kerja sia-sia — sejalan dengan Task 2 |

**Catatan dead literal:** ada dua tipe riset yang tidak pernah dihasilkan oleh mekanisme apa pun (mati / tidak terpakai). Setelah unifikasi, periksa apakah keduanya masih mati. Kalau masih: biarkan apa adanya, jangan diaktifkan, jangan dihapus — di luar scope. Cukup pastikan pemetaan di atas tidak menggunakannya.

**Perbaikan yang harus terjadi saat penyatuan:**
- "bandingkan BBCA dan BBRI" → kedua ticker benar (hari ini "DAN" kebaca ticker).
- "BBCA vs BBRI" → kedua ticker benar (hari ini ticker pertama hilang).
- "sektor bank", "cari saham breakout" → dibaca sebagai permintaan sektor/screening (hari ini kebaca saham "BANK"/"CARI").

**Kriteria selesai:**
- Query yang sama dikirim lewat kedua jalur masuk menghasilkan interpretasi sama persis.
- Ada test konsistensi yang membuktikan ini untuk kumpulan query representatif (perbandingan, analisis satu saham, sektor, gainers, bantuan, riset umum) — termasuk kasus salah di atas dan kasus "ditolak" di jalur riset.

### Task 2: Hentikan panggilan AI saat semua data gagal

**Tujuan:** Ketika permintaan riset gagal mengambil data sama sekali (satu saham, atau kedua saham pada perbandingan), sistem berhenti sebelum memanggil AI — bukan memanggil AI untuk laporan kosong yang hasilnya toh dibuang.

**Kriteria selesai:**
- Alur riset mengembalikan laporan kosong bertanda kegagalan segera setelah data gagal total, sebelum panggilan AI penyusun laporan.
- CLI menampilkan pesan kegagalan langsung + exit code non-nol.
- Riset sektor yang hasilnya kosong tanpa kegagalan data tidak berubah perilakunya.
- Test menjalankan alur riset yang sesungguhnya dengan data gagal di-mock di sumbernya → terbukti panggilan AI tidak terjadi.

### Task 3: Tes yang membuktikan, bukan mensimulasikan

**Tujuan:** Tes yang sekarang menyuntikkan hasil riset palsu dari luar diganti dengan tes yang menjalankan alur aslinya.

**Kriteria selesai:**
- Tes skenario kegagalan menjalankan fungsi alur riset sungguhan (kegagalan data di-mock di sumber data), bukan menyuntik hasil akhir palsu.
- Tes CLI kegagalan juga menjalankan alur asli.
- Tidak ada lagi tes kegagalan riset yang menyuntikkan hasil akhir palsu dari luar.

### Task 4: Perbandingan parsial — keputusan eksplisit

**Keputusan:** Saham yang gagal di tahap analisis awal tetap dikirim ke tahap perbandingan — tahap itu memiliki penanganan kegagalan datanya sendiri, jadi tidak perlu mekanisme baru: saham yang gagal dicoba ulang di sana, dan kalau tetap gagal, kegagalannya tercatat di hasil perbandingan dan di catatan laporan.

**Kriteria selesai:**
- Satu saham gagal, satu sukses → laporan tetap tampil lengkap; saham gagal dicoba di tahap perbandingan; kegagalan tercatat di laporan.
- Kedua saham gagal → berperilaku sesuai Task 2 (tanpa panggilan AI).
- Ada test yang membuktikan kedua skenario lewat alur riset sesungguhnya.

### Task 5: Verifikasi menyeluruh

**Kriteria selesai:**
- Seluruh test suite lulus, tidak ada regresi.
- Smoke test manual alur riset & perbandingan berjalan normal.

---

**Di luar scope:** kualitas jawaban LLM (Phase 3), conversation continuity (Phase 2), fitur baru.
