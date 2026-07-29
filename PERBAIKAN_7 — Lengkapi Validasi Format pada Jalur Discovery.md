# PERBAIKAN_7 — Lengkapi Validasi Format pada Jalur Discovery

## Latar Belakang

Setelah ditelusuri ulang, roadmap Universal Symbol Discovery sudah
berjalan baik di hampir semua bagian — multi-provider, fallback,
penggabungan, penghapusan duplikat, pemantauan kesehatan provider, dan
arsitektur yang bisa dikembangkan, semuanya sudah terbukti jalan.

Tapi ada satu bagian yang belum lengkap: validasi format simbol.
Validasi format saat ini hanya diterapkan saat seseorang meminta data
untuk satu ticker tertentu secara langsung (misalnya lewat perintah
CLI). Validasi ini belum diterapkan pada daftar simbol yang didapat
dari proses discovery (pengambilan daftar simbol dari provider).

Saat ini, proses penggabungan hasil discovery hanya membuang entri yang
kosong, tapi tidak memeriksa apakah format simbolnya benar-benar valid.
Kalau suatu saat ada provider yang mengembalikan data simbol dengan
format aneh atau rusak (bukan kosong, tapi juga bukan format ticker
yang wajar), itu akan tetap lolos masuk ke daftar universe yang dipakai
untuk screening.

---

## Perbaikan 1 — Terapkan Validasi Format Simbol pada Hasil Discovery

**Masalah:** Simbol yang didapat dari proses discovery multi-provider
tidak diperiksa format keabsahannya sebelum digabung dan disimpan
sebagai daftar universe. Yang diperiksa cuma apakah simbolnya kosong
atau tidak, bukan apakah formatnya benar.

**Yang harus dilakukan:** Terapkan pemeriksaan format simbol yang sudah
ada di proyek ini (yang sekarang cuma dipakai untuk validasi ticker
tunggal) juga pada proses penggabungan hasil discovery, sebelum daftar
tersebut disimpan ke cache atau dipakai sebagai universe. Simbol yang
formatnya tidak valid harus dibuang, sama seperti simbol yang kosong.

**Kriteria selesai (butuh bukti nyata):** Buat percobaan dengan data
simbol contoh yang sengaja berisi campuran format valid dan tidak
valid (misalnya simbol dengan karakter aneh atau terlalu panjang), lalu
jalankan proses discovery-nya dan tunjukkan hasilnya membuktikan hanya
simbol dengan format valid yang lolos masuk ke daftar akhir.

---

## Aturan Verifikasi Umum

Laporan "sudah selesai" dari agent **tidak cukup** tanpa bukti konkret
berupa hasil percobaan yang benar-benar dijalankan, membuktikan simbol
dengan format tidak valid benar-benar dibuang dari daftar akhir.
