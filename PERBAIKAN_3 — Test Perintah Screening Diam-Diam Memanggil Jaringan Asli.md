# PERBAIKAN_3 — Test Perintah Screening Diam-Diam Memanggil Jaringan Asli

## Latar Belakang

Setelah PERBAIKAN_23 selesai dan diverifikasi, seluruh test suite
dijalankan penuh dan hasilnya "105 passed" — kelihatannya semua aman.
Tapi begitu dicek waktu eksekusinya, empat test untuk perintah
screening (yang mewakili perintah screen, gainers, losers, dan sector)
masing-masing memakan waktu sekitar 36 detik, jauh di atas test lain
yang biasanya di bawah satu detik.

Setelah ditelusuri, penyebabnya adalah: keempat test itu masih meniru
(mock) fungsi lama yang dulu dipakai untuk mengambil daftar ticker.
Padahal setelah PERBAIKAN_23, perintah-perintah tersebut sudah beralih
memakai fungsi discovery yang baru. Karena target tiruannya salah
sasaran, tiruan itu tidak berpengaruh apa-apa, dan test-nya diam-diam
menjalankan proses discovery yang sesungguhnya — termasuk kemungkinan
mencoba menghubungi sumber data asli lewat jaringan.

Ini masalah yang sama persis seperti sebelumnya (test yang mengunci
perilaku lama sebagai "benar" tanpa disadari) tapi kali ini ke arah
sebaliknya: test-nya jadi diam-diam menguji sesuatu yang tidak
seharusnya diuji lewat jaringan asli, bukan lewat data tiruan. Kalau
dibiarkan, ini bikin proses testing jadi lambat, tidak bisa diandalkan
(bisa gagal random tergantung kondisi jaringan), dan berpotensi
memicu masalah pembatasan akses ke sumber data yang sudah berkali-kali
diperbaiki sebelumnya di proyek ini.

---

## Perbaikan 1 — Perbaiki Target Tiruan pada Test Perintah Screening

**Masalah:** Empat test yang mewakili perintah-perintah screening
utama masih meniru fungsi lama yang sudah tidak lagi dipakai oleh
perintah-perintah tersebut, sehingga tiruan itu tidak berfungsi dan
proses aslinya (termasuk kemungkinan koneksi ke jaringan) tetap
berjalan saat pengujian.

**Yang harus dilakukan:** Perbarui keempat test tersebut supaya meniru
fungsi yang sekarang benar-benar dipakai untuk mengambil daftar ticker
pada alur discovery yang baru, bukan lagi fungsi lama. Pastikan hasil
tiruannya tetap memberikan data contoh yang wajar seperti sebelumnya,
supaya pengujian tetap bisa memverifikasi perilaku perintahnya dengan
benar.

**Kriteria selesai (butuh bukti nyata):** Jalankan ulang test-test
tersebut dan tunjukkan waktu eksekusinya sekarang jauh lebih cepat
(di bawah satu detik per test, sebanding dengan test lain yang sudah
benar). Tambahan bukti lain: jalankan test-test itu dalam kondisi
tanpa akses jaringan sama sekali, dan buktikan test tetap lolos —
ini membuktikan tidak ada lagi panggilan ke sumber data asli yang
terjadi selama pengujian.

---

## Perbaikan 2 — Periksa Kemungkinan Masalah Serupa di Tempat Lain

**Masalah:** Kejadian di Perbaikan 1 kemungkinan bukan satu-satunya.
Setelah ada perubahan pada fungsi yang dipanggil oleh kode utama
(seperti pada PERBAIKAN_23), ada risiko test lain di proyek ini juga
masih meniru fungsi lama yang sudah tidak dipakai lagi, tanpa
disadari.

**Yang harus dilakukan:** Telusuri seluruh test suite untuk memastikan
setiap tiruan (mock) benar-benar menyasar fungsi yang masih dipakai
oleh kode yang diuji saat ini. Perbaiki bila ditemukan kejadian serupa.

**Kriteria selesai (butuh bukti nyata):** Tunjukkan hasil test suite
lengkap berjalan, dengan waktu eksekusi total yang wajar (bukan
didominasi beberapa test yang tiba-tiba lambat), sebagai bukti tidak
ada lagi tiruan yang salah sasaran di seluruh proyek.

---

## Aturan Verifikasi Umum

Untuk kedua perbaikan di atas, laporan "sudah selesai" dari agent
**tidak cukup** tanpa bukti konkret berupa log waktu eksekusi test
yang sebenarnya, dan hasil pengujian tanpa akses jaringan sebagai
bukti tambahan. Jumlah test yang lolos saja ("X passed") tidak cukup
untuk membuktikan test tersebut benar-benar menguji hal yang tepat.
