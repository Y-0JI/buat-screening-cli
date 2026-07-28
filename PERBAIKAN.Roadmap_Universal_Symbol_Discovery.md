# PERBAIKAN.Roadmap_Universal_Symbol_Discovery — Universal Symbol Discovery: Sambungkan ke Alur Produksi

## Latar Belakang

Fase 1 sampai 6 dari roadmap "Universal Symbol Discovery" sudah selesai
dikerjakan dan digabung ke branch utama. Tapi hasil audit menunjukkan
seluruh sistem itu **belum benar-benar terpakai**. Perintah screening,
gainers, losers, dan sector masih mengambil daftar saham dari file
statis lama, bukan dari sistem discovery multi-provider yang baru
dibangun. Efeknya, tujuan utama roadmap — universe saham yang selalu
tersedia dan tidak bergantung pada satu sumber data — belum tercapai
meskipun semua fase "selesai" di atas kertas.

Dokumen ini berisi daftar perbaikan untuk menutup kesenjangan tersebut.
Kerjakan berurutan, satu perbaikan boleh selesai sebelum lanjut ke
berikutnya.

---

## Perbaikan 1 — Isi Implementasi Pengambilan Daftar Simbol yang Sebenarnya

**Masalah:** Kedua provider data (IDX dan Yahoo Finance) memiliki fungsi
untuk mengambil daftar simbol, tapi keduanya masih kosong / placeholder
dan tidak pernah benar-benar mengambil data dari sumbernya.

**Yang harus dilakukan:** Implementasikan pengambilan daftar simbol
nyata untuk masing-masing provider, sesuai kemampuan sumber data
masing-masing (misalnya IDX punya endpoint daftar emiten resmi, Yahoo
bisa dipakai untuk validasi/pelengkap, bukan sumber utama daftar
emiten IDX). Jika salah satu provider memang tidak punya cara
menyediakan daftar simbol secara wajar, itu boleh, tapi harus
didokumentasikan alasannya di kode, bukan dibiarkan kosong tanpa
penjelasan.

**Kriteria selesai (butuh bukti nyata):** Jalankan pengambilan daftar
simbol untuk tiap provider dan tunjukkan output log yang membuktikan
jumlah simbol yang benar-benar didapat lebih dari nol dan berisi kode
saham yang masuk akal (bukan list kosong, bukan data dummy).

---

## Perbaikan 2 — Jadikan Sistem Discovery sebagai Sumber Universe yang Sesungguhnya

**Masalah:** Perintah screening, gainers, losers, dan sector saat ini
membaca daftar saham dari file statis yang di-hardcode, sama sekali
tidak melewati sistem fallback multi-provider, penggabungan, atau
deduplikasi yang sudah dibangun di fase-fase sebelumnya. Sistem baru
itu jadi kode yang menganggur, tidak pernah dipanggil di jalur
produksi.

**Yang harus dilakukan:** Sambungkan sistem discovery multi-provider
(fallback antar-provider + penggabungan + deduplikasi + validasi +
normalisasi) sebagai sumber universe yang dipakai oleh semua perintah
screening. File statis boleh tetap dipertahankan sebagai lapisan cache
lokal (supaya aplikasi tetap bisa jalan walau semua provider gagal),
tapi bukan lagi sebagai satu-satunya sumber kebenaran.

**Kriteria selesai (butuh bukti nyata):** Tunjukkan log/transkrip
menjalankan salah satu perintah screening dari awal, yang membuktikan
proses tersebut benar-benar memanggil sistem discovery (bukan langsung
baca file statis), termasuk saat providernya sengaja dibuat gagal
untuk membuktikan fallback-nya jalan.

---

## Perbaikan 3 — Perkuat Proses Validasi Universe dengan Sistem Discovery

**Masalah:** Proses validasi universe saat ini hanya mengecek ulang
daftar ticker yang sudah ada memakai satu provider saja. Proses ini
tidak pernah menemukan emiten baru dan tidak memanfaatkan kemampuan
multi-provider yang sudah dibangun.

**Yang harus dilakukan:** Ubah proses validasi universe supaya turut
memanfaatkan hasil discovery dari semua provider yang tersedia,
sehingga emiten baru (misalnya IPO terbaru) bisa otomatis masuk ke
daftar, bukan cuma memvalidasi status hidup/mati dari daftar lama.

**Kriteria selesai (butuh bukti nyata):** Tunjukkan log hasil
menjalankan proses validasi universe yang membuktikan ada penambahan
emiten baru terdeteksi dari sumber selain daftar lama, atau bila
memang tidak ada emiten baru saat pengujian, tunjukkan log yang
membuktikan proses tetap benar-benar memanggil semua provider yang
tersedia untuk pengecekan.

---

## Perbaikan 4 — Perbaiki Bug Crash pada Retry Provider IDX

**Masalah:** Saat provider IDX gagal mengambil data dan mencoba
mekanisme percobaan ulang, terjadi crash karena ada referensi ke
fungsi jeda waktu yang belum tersedia di modul tersebut. Akibatnya,
mekanisme retry yang seharusnya menyelamatkan proses malah membuat
prosesnya gagal total.

**Yang harus dilakukan:** Perbaiki referensi yang hilang tersebut agar
mekanisme retry benar-benar berjalan sesuai rancangan.

**Kriteria selesai (butuh bukti nyata):** Tunjukkan log pengujian yang
sengaja memicu kegagalan provider IDX, dan buktikan proses retry
berjalan tanpa crash sampai selesai (baik akhirnya berhasil atau
akhirnya menyerah setelah percobaan habis — yang penting tidak crash).

---

## Perbaikan 5 — Perbaiki Klasifikasi Status pada Sistem Pemantauan Provider

**Masalah:** Sistem pemantauan kesehatan provider saat ini mencatat
SEMUA jenis kegagalan sebagai "rate limited", padahal penyebabnya bisa
bermacam-macam (koneksi putus, data rusak, bug internal, dan
sebagainya). Ini membuat laporan kesehatan provider menyesatkan dan
menyulitkan diagnosis masalah sebenarnya.

**Yang harus dilakukan:** Bedakan pencatatan status kegagalan sesuai
jenis penyebabnya yang sebenarnya, bukan digeneralisir jadi satu
kategori. Pemantauan ini sudah punya mekanisme klasifikasi jenis error
di provider lain (Yahoo Finance) yang bisa dijadikan acuan pola.

**Kriteria selesai (butuh bukti nyata):** Tunjukkan log pengujian
dengan beberapa jenis kegagalan berbeda yang sengaja dipicu, dan
buktikan laporan kesehatan provider mencatat kategori yang berbeda-
beda sesuai penyebabnya masing-masing, bukan semua masuk kategori yang
sama.

---

## Perbaikan 6 — Perbaiki Test yang Mengunci Perilaku Placeholder sebagai "Benar"

**Masalah:** Ada test otomatis yang saat ini menganggap daftar simbol
kosong dari provider sebagai hasil yang benar. Test semacam ini lolos
terus meskipun fiturnya belum benar-benar berfungsi, sehingga
menyembunyikan masalah alih-alih menangkapnya.

**Yang harus dilakukan:** Setelah Perbaikan 1 selesai, perbarui test
terkait supaya membuktikan sistem discovery benar-benar mengembalikan
data simbol yang valid dan masuk akal, bukan lagi memvalidasi bahwa
hasilnya kosong.

**Kriteria selesai (butuh bukti nyata):** Tunjukkan hasil test suite
lengkap berjalan (output pass/fail sungguhan, bukan klaim), dengan
test yang relevan sekarang memvalidasi data asli, bukan list kosong.

---

## Aturan Verifikasi Umum

Untuk setiap perbaikan di atas, laporan "sudah selesai" dari agent
**tidak cukup** tanpa bukti konkret berupa log, transkrip output, atau
hasil test yang benar-benar dijalankan. Klaim tanpa bukti dianggap
belum selesai dan harus diulang sampai buktinya bisa ditunjukkan.
