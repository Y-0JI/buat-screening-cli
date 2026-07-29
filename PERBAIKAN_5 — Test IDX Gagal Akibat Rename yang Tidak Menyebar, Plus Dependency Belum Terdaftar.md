# PERBAIKAN_5 — Test IDX Gagal Akibat Rename yang Tidak Menyebar, Plus Dependency Belum Terdaftar

## Latar Belakang

Setelah perbaikan pola koneksi ke IDX selesai (ganti pendekatan supaya
tidak terdeteksi sebagai bot), sebenarnya bagian intinya sudah berhasil
— provider IDX sekarang benar-benar bisa mengambil data dari sumbernya.
Tapi ada efek samping: nama variabel internal yang menyimpan koneksi ke
IDX berubah saat perbaikan itu dilakukan, dan sejumlah test yang masih
mengacu ke nama lama tidak ikut diperbarui.

Akibatnya, saat test suite dijalankan penuh, ada beberapa test yang
gagal total, dan satu test lain gagal secara diam-diam dengan cara yang
lebih berbahaya: karena mengacu ke nama variabel yang sudah tidak ada,
tiruan data (mock) yang seharusnya dipakai jadi tidak berfungsi, dan
tanpa disadari test tersebut malah mencoba menghubungi IDX yang
sesungguhnya lewat jaringan saat pengujian berjalan.

Selain itu, ditemukan juga bahwa library baru yang dipakai untuk
menyamar sebagai browser (bagian dari perbaikan koneksi IDX) belum
didaftarkan secara resmi sebagai kebutuhan proyek. Saat ini library itu
kebetulan ikut terpasang karena jadi bawaan dari library lain yang
sudah ada, bukan karena didaftarkan sendiri. Ini beresiko kalau suatu
saat library lain itu berubah dan tidak lagi butuh library tersebut —
proyek ini bisa tiba-tiba error saat dijalankan tanpa peringatan
sebelumnya.

---

## Perbaikan 1 — Samakan Semua Test dengan Nama Variabel Internal yang Baru

**Masalah:** Beberapa test masih mengacu ke nama variabel internal lama
pada provider IDX yang sudah diganti namanya saat perbaikan koneksi
sebelumnya. Karena tidak disamakan, sebagian test gagal total, dan satu
test lainnya gagal secara diam-diam karena tiruan datanya jadi tidak
berpengaruh sama sekali, membuat test itu tanpa sengaja mencoba
menghubungi IDX sungguhan saat pengujian.

**Yang harus dilakukan:** Telusuri seluruh test yang berhubungan
dengan provider IDX, dan pastikan semuanya mengacu ke nama variabel
internal yang sekarang benar-benar dipakai oleh kodenya, bukan nama
lama yang sudah tidak berlaku.

**Kriteria selesai (butuh bukti nyata):** Jalankan seluruh test suite
dan tunjukkan hasilnya semua lolos tanpa ada yang gagal. Perhatikan
juga waktu eksekusinya — pastikan tidak ada test yang tiba-tiba lambat
dibanding test lain, karena itu tanda ada test yang diam-diam
menghubungi jaringan asli alih-alih memakai data tiruan.

---

## Perbaikan 2 — Daftarkan Library Penyamaran Browser Secara Resmi

**Masalah:** Library yang dipakai untuk membuat permintaan ke IDX
terlihat seperti browser sungguhan belum didaftarkan sebagai kebutuhan
resmi proyek ini. Saat ini library tersebut kebetulan ikut terpasang
karena menjadi bawaan dari library lain yang sudah dipakai proyek,
bukan karena benar-benar didaftarkan sendiri. Kalau suatu saat library
lain itu berubah, proyek ini bisa tiba-tiba gagal dijalankan tanpa
peringatan.

**Yang harus dilakukan:** Tambahkan library tersebut secara eksplisit
ke daftar kebutuhan resmi proyek, supaya keberadaannya tidak lagi
bergantung secara kebetulan pada library lain.

**Kriteria selesai (butuh bukti nyata):** Tunjukkan bagian konfigurasi
proyek yang membuktikan library tersebut sekarang terdaftar secara
eksplisit, dan lakukan instalasi ulang proyek dari awal (bukan
memakai lingkungan yang sudah ada sebelumnya) untuk membuktikan
semuanya tetap terpasang dengan benar tanpa mengandalkan library lain.

---

## Aturan Verifikasi Umum

Untuk kedua perbaikan di atas, laporan "sudah selesai" dari agent
**tidak cukup** tanpa bukti konkret berupa log hasil test suite yang
benar-benar dijalankan dan bukti instalasi ulang proyek dari awal.
Jumlah test yang lolos saja tidak cukup — harus dipastikan tidak ada
test yang gagal maupun yang lolos secara tidak wajar (misalnya karena
diam-diam menghubungi jaringan asli).
