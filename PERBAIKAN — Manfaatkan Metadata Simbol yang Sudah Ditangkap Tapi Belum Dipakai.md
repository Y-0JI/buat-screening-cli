# PERBAIKAN — Manfaatkan Metadata Simbol yang Sudah Ditangkap Tapi Belum Dipakai

## Latar Belakang

Proses discovery yang sekarang sudah menangkap informasi tambahan
untuk setiap simbol saham — bukan cuma kode tickernya, tapi juga nama
perusahaan dan sektor industrinya. Sayangnya informasi ini kebanyakan
langsung dibuang begitu proses discovery selesai, hanya kode tickernya
saja yang dipakai lanjut.

Ini bukan cuma soal sayang data — ada satu perintah yang jadi boros
waktu gara-gara ini. Perintah untuk mencari saham berdasarkan sektor
tertentu saat ini bekerja dengan cara yang tidak efisien: dia
memproses SEMUA saham yang ada dulu (proses yang berat dan lama),
baru setelah itu membuang hasil yang sektornya tidak cocok. Padahal
kalau informasi sektor sudah ada sejak awal, seharusnya bisa dipakai
untuk menyaring dulu saham mana saja yang termasuk sektor yang dicari,
baru diproses lebih lanjut hanya saham-saham yang relevan saja.

---

## Perbaikan 1 — Saring Berdasarkan Sektor Sebelum Memproses, Bukan Sesudah

**Masalah:** Perintah pencarian saham berdasarkan sektor saat ini
memproses seluruh saham yang ada terlebih dahulu (proses yang berat
dan memakan waktu lama), baru kemudian membuang hasil yang sektornya
tidak sesuai. Ini sangat tidak efisien, karena sebagian besar hasil
yang diproses dengan susah payah akhirnya dibuang begitu saja.

**Yang harus dilakukan:** Ubah urutan prosesnya. Manfaatkan informasi
sektor yang sudah didapat sejak proses awal pengambilan daftar saham,
untuk menyaring dulu saham mana saja yang termasuk sektor yang dicari.
Setelah itu, baru proses yang berat (pengambilan data harga dan
sejenisnya) dijalankan hanya untuk saham-saham yang sudah tersaring
tersebut, bukan untuk seluruh saham yang ada.

**Kriteria selesai (butuh bukti nyata):** Jalankan perintah pencarian
berdasarkan sektor sebelum dan sesudah perbaikan, lalu tunjukkan
perbandingan waktu eksekusinya. Harus terlihat jelas waktu yang
dibutuhkan jauh lebih cepat setelah perbaikan, karena yang diproses
sekarang hanya saham-saham yang relevan saja, bukan semuanya.

---

## Perbaikan 2 — Tampilkan Nama Perusahaan pada Hasil Screening

**Masalah:** Hasil dari perintah-perintah screening saat ini hanya
menampilkan kode ticker saham (misalnya kode empat huruf), tanpa nama
perusahaannya. Ini menyulitkan pengguna yang tidak hafal semua kode
ticker untuk mengenali saham apa yang dimaksud.

**Yang harus dilakukan:** Tampilkan juga nama perusahaan di samping
kode ticker pada hasil perintah-perintah screening, memanfaatkan
informasi nama yang sudah didapat dari proses discovery. Kalau nama
perusahaan untuk suatu ticker tidak tersedia, tampilkan saja kode
tickernya seperti biasa, jangan sampai perintahnya gagal karena
informasi ini tidak ada.

**Kriteria selesai (butuh bukti nyata):** Jalankan salah satu perintah
screening setelah perbaikan, dan tunjukkan hasilnya sekarang
menampilkan nama perusahaan di samping kode ticker, bukan cuma kode
tickernya saja.

---

## Aturan Verifikasi Umum

Untuk kedua perbaikan di atas, laporan "sudah selesai" dari agent
**tidak cukup** tanpa bukti konkret berupa hasil eksekusi perintah
yang benar-benar dijalankan (termasuk perbandingan waktu untuk
Perbaikan 1), bukan sekadar klaim bahwa perubahan sudah dilakukan.
