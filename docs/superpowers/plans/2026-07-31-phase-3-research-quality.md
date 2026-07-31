# Phase 3 — Research Quality (Execution Plan)

> Instruksi untuk agent murah. Bahasa Indonesia, level "apa yang harus dicapai" — bukan "cara implementasi". Eksplorasi kode dulu, pilih solusi paling sederhana yang konsisten dengan arsitektur existing.

**Goal:** Perbaiki kualitas output riset pada 3 titik nyata yang terbukti bermasalah — prompt kotor, ekstraksi hasil yang rapuh, beban prompt berlebihan. Tanpa mengubah arsitektur.

**Global Constraints:**
- Tidak menambah dependency, tidak mengubah alur routing, tidak menambah kemampuan AI baru.
- Semua perbaikan dibuktikan lewat pengujian (jalankan alur asli, bukan simulasi hasil akhir).
- Tiap task: eksplorasi → implementasi paling sederhana → uji → seluruh test suite lulus → lanjut.
- Bekerja di branch terpisah dari `main` (PR baru, tidak di-merge tanpa tinjauan).

---

### Task 1: Bersihkan prompt dari sisa sintaks kode

**Tujuan:** Tidak ada teks sisa kode (literal `if ts else 0` dan sejenisnya) yang terkirim ke LLM. Nilai dirender benar dalam semua kondisi, termasuk saat sinyal screening tidak tersedia.

**Kriteria selesai:**
- Rendering prompt hasil screening bersih: confidence terformat benar; sinyal & alasan benar; tanpa sinyal → keluaran wajar, bukan sisa sintaks.
- Audit seluruh penyusun prompt (analisis, perbandingan, riset) — tidak ada sisa sintaks serupa di tempat lain.
- Pengujian rendering membuktikan prompt bersih, termasuk kasus tanpa sinyal.

### Task 2: Ekstraksi ringkasan & rekomendasi yang andal

**Tujuan:** Ringkasan eksekutif dan rekomendasi selalu terambil dari jawaban LLM apa pun format penanda yang umum (heading markdown, tebal, label sebaris) — tanpa menangkap bagian yang salah.

**Kriteria selesai:**
- Format jawaban LLM yang wajar → ringkasan & rekomendasi benar (termasuk format label sebaris yang sekarang gagal).
- Kata kunci di tengah kalimat (mis. "ringkasan" dalam konteks lain) tidak memicu penangkapan salah.
- Pengujian dengan beberapa variasi format membuktikan hal ini.

### Task 3: Batasi beban analisis di prompt laporan riset

**Tujuan:** Laporan riset menerima analisis per saham secukupnya, bukan teks penuh — mencegah prompt raksasa dan biaya token berlebih.

**Keputusan (sudah ditetapkan):** kepala + ekor — simpan bagian awal dan akhir analisis, buang bagian tengah. Bagian awal berisi ringkasan kondisi; bagian akhir berisi kesimpulan (dijamin oleh panduan analisis yang sudah ada). Ditandai jelas bahwa bagian tengah dipotong, supaya LLM tahu informasinya tidak lengkap.

**Kriteria selesai:**
- Setiap blok analisis di prompt laporan riset dibatasi secara konsisten sehingga ukuran prompt tetap terkendali tanpa menghilangkan konteks awal dan kesimpulan analisis.
- Pengujian membuktikan batas tersebut dan penanda pemotongan ada.

### Task 4: Verifikasi menyeluruh

**Kriteria selesai:**
- Seluruh test suite lulus, tidak ada regresi.
- Smoke test riset nyata: prompt laporan bersih, ringkasan ter-ekstrak benar, ukuran prompt terkendali.

---

**Di luar scope (sudah diputuskan):** perbaikan perintah `memory` CLI (task terpisah nanti), "reasoning" AI secara umum (sudah dijaga aturan data-only; tidak ada gap terverifikasi), ringkasan percakapan cerdas dengan AI (keputusan Phase 2 ditunda), personalisasi, fitur baru.
